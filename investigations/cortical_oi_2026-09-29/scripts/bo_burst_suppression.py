#!/usr/bin/env python3
"""
Bayesian optimization of stimulation parameters to minimize burst rate.
Uses our closed-loop infrastructure as the objective function.
"""

import sys, subprocess, json, os, time, numpy as np
from pathlib import Path
# Try to import scikit-learn for Gaussian Process
try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C
except ImportError:
    print("scikit-learn not found, installing via pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C

# We'll also need scipy for the acquisition function optimization
from scipy.optimize import minimize
from scipy.stats import norm

# Import our existing infrastructure
sys.path.insert(0, str(Path("/home/vinicius")))
from cortical_oi_integration import CorticalOIController, CorticalIntegrationConfig

try:
    import cl
except ImportError:
    print("CL SDK not available")
    sys.exit(1)

from datetime import datetime

class BayesianOptimizationController:
    def __init__(self, param_bounds, n_initial=5):
        """
        param_bounds: list of tuples (min, max) for each parameter
        We'll optimize over two parameters: amplitude_ref (0 to 100) and train_count (1 to 10)
        Other parameters fixed: duration_us=200, interval_ms=10.0
        """
        self.param_bounds = np.array(param_bounds)
        self.dim = len(param_bounds)
        self.X = []  # observed parameters
        self.y = []  # observed burst rate (we want to minimize)
        self.n_initial = n_initial
        self.gp = GaussianProcessRegressor(
            kernel=C(1.0, (1e-3, 1e3)) * Matern(length_scale=1.0, length_scale_bounds=(1e-2, 1e2), nu=2.5) + WhiteKernel(noise_level=1, noise_level_bounds=(1e-10, 1e+1)),
            alpha=1e-6,
            n_restarts_optimizer=5,
            random_state=42
        )
        
    def _cl_rate_to_amplitude_uv(self, cl_rate):
        """Convert our reference amplitude (0-100) to actual amplitude in µA for stimulation.
        We'll map: cl_rate 0 -> 0.0 µA, cl_rate 100 -> 10.0 µA (so that our earlier 10 and 50 correspond to 1 and 5 µA).
        In our stimulation we used ±1.0 µA fixed. Let's instead make the amplitude control the current magnitude.
        We'll define: current_ua = cl_rate * 0.1  (so range 0 to 10 µA)
        """
        return cl_rate * 0.1  # returns current in µA

    def run_experiment(self, params):
        """Run a closed-loop experiment with given parameters and return burst rate (bursts per second).
        params: [amplitude_ref, train_count]
        amplitude_ref: 0-100 (will be converted to current_ua)
        train_count: 1-10 (integer)
        Fixed: duration_us=200, interval_ms=10.0, stimulation enabled if amplitude_ref>0
        """
        amplitude_ref, train_count = params
        amplitude_ref = float(amplitude_ref)
        train_count = int(round(train_count))
        # Convert amplitude_ref to current in µA
        current_ua = self._cl_rate_to_amplitude_uv(amplitude_ref)
        
        # Set up output directory for this run
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"./bo_run_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        # Configuration
        config = CorticalIntegrationConfig(
            ticks_per_second=500,
            stop_after_seconds=5.0,  # shorter duration for speed
            burst_min_spikes=2,
            burst_max_isi_ms=25.0,
            prediction_window_ms=50.0,
            research_state_update_interval_ticks=10,
            output_dir=output_dir,
            recording_suffix=f"_bo_amp{amplitude_ref:.1f}_tc{train_count}"
        )
        
        # We'll create a simple controller that runs the experiment and returns burst rate.
        
        class SimpleBOController(CorticalOIController):
            def __init__(self, config, current_ua, train_count):
                super().__init__(config)
                self.current_ua = current_ua
                self.train_count = train_count
                self.stimulation_enabled = (current_ua > 0.0)
                self.stimulation_channels = list(range(8))  # first 8 channels
                self.burst_count = 0
                
            def run_integration_experiment(self):
                print(f"\n🚀 Starting BO Experiment (current_ua={self.current_ua} µA, train_count={self.train_count})\n")
                recording_path = None
                try:
                    with cl.open() as neurons:
                        print(f"📡 Connected to Cortical Simulator: {neurons}")
                        
                        # Create research state data stream (we don't really need it for BO, but keep for consistency)
                        research_ds = neurons.create_data_stream(
                            "research_state",
                            {
                                "experiment": "bo_stimulation",
                                "hypothesis": "stimulation reduces burst rate",
                                "version": "1.0",
                                "integration_type": "cortical_cl_api_oi_sandbox"
                            }
                        )
                        
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
                        recording_path = self.config.output_dir / f"{timestamp}{self.config.recording_suffix}.h5"
                        
                        # Start recording with data streams
                        recording = neurons.record(
                            file_suffix=self.config.recording_suffix,
                            include_data_streams=True,
                            include_spikes=True,
                            include_stims=True,
                            include_raw_samples=True,
                        )
                        
                        print(f"📼 Recording started: {recording.file['path']}")
                        
                        tick_count = 0
                        for tick in neurons.loop(
                            ticks_per_second=self.config.ticks_per_second,
                            stop_after_seconds=self.config.stop_after_seconds,
                            ignore_jitter=True
                        ):
                            tick_count = tick.iteration
                            
                            # Detect bursts using our analyzer
                            # Pass spike objects directly (they have timestamp and channel attributes)
                            current_spikes = tick.analysis.spikes
                            
                            bursts = self.burst_analyzer.detect_bursts(current_spikes, tick_count, int(tick.timestamp))
                            
                            for burst in bursts:
                                self.burst_count += 1
                                # Deliver stimulation if enabled
                                if self.stimulation_enabled:
                                    self._deliver_stimulation(burst, tick_count, neurons)
                            
                            # Progress
                            if tick_count % 500 == 0 and tick_count > 0:
                                stop_tick = int(self.config.stop_after_seconds * self.config.ticks_per_second)
                                print(f"   ⏱️  Tick {tick_count}/{stop_tick} | Bursts: {self.burst_count}")
                        
                        # recording stops automatically
                    
                except Exception as e:
                    print(f"❌ Error during experiment: {e}")
                    raise
                
                print(f"\n✅ Experiment completed! Burst count: {self.burst_count}")
                burst_rate = self.burst_count / self.config.stop_after_seconds  # bursts per second
                return burst_rate, recording_path
            
            def _deliver_stimulation(self, burst, tick_count, neurons):
                """Deliver electrical stimulation via CL API using StimDesign."""
                try:
                    duration_us = 200  # fixed
                    stim_design = cl.StimDesign(duration_us, -self.current_ua, duration_us, self.current_ua)
                    for i in range(self.train_count):
                        for ch in self.stimulation_channels:  # first 8 channels
                            neurons.stim(ch, stim_design)
                except Exception as e:
                    print(f"   ⚠️  Warning: Failed to deliver stimulation: {e}")
        
        controller = SimpleBOController(config, current_ua, train_count)
        burst_rate, recording_path = controller.run_integration_experiment()
        return burst_rate

    def _expected_improvement(self, X, xi=0.01):
        """Expected improvement acquisition function."""
        mu, sigma = self.gp.predict(X, return_std=True)
        mu_sample_opt = np.min(self.y)

        with np.errstate(divide='warn'):
            imp = mu - mu_sample_opt - xi
            Z = imp / sigma
            ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma == 0.0] = 0.0
        return ei

    def _propose_location(self, acquisition_func):
        """Propose the next sampling point by optimizing the acquisition function."""
        X_seeds = np.random.uniform(self.param_bounds[:, 0], self.param_bounds[:, 1], size=(1000, self.dim))
        # Also add the observed points as seeds
        if len(self.X) > 0:
            X_seeds = np.vstack([X_seeds, np.array(self.X)])
        
        # Find the best acquisition value among seeds
        X_best = None
        acquisition_best = -np.inf
        for X_try in X_seeds:
            X_try = X_try.reshape(1, -1)
            acquisition = acquisition_func(X_try)
            if acquisition > acquisition_best:
                acquisition_best = acquisition
                X_best = X_try
        
        # Now optimize from the best seed found
        res = minimize(lambda x: -acquisition_func(x.reshape(1, -1)),
                       X_best.flatten(),
                       bounds=self.param_bounds,
                       method="L-BFGS-B")
        
        if res.success:
            return res.x
        else:
            # If optimization failed, return the best seed
            return X_best

    def suggest_next_location(self):
        """Suggest the next set of parameters to try."""
        if len(self.X) < self.n_initial:
            # We need to generate initial points randomly
            X_next = np.random.uniform(self.param_bounds[:, 0], self.param_bounds[:, 1], size=self.dim)
        else:
            # Fit the GP
            self.gp.fit(np.array(self.X), np.array(self.y))
            # Propose next point
            X_next = self._propose_location(self._expected_improvement)
        return X_next

    def observe(self, X, y):
        """Record an observation."""
        self.X.append(X.tolist() if isinstance(X, np.ndarray) else X)
        self.y.append(y.tolist() if isinstance(y, np.ndarray) else y)

def main():
    # Define parameter bounds: [amplitude_ref (0-100), train_count (1-10)]
    param_bounds = [(0, 100), (1, 10)]
    bo = BayesianOptimizationController(param_bounds, n_initial=5)
    
    n_iterations = 10  # total number of experiments to run
    print(f"Starting Bayesian optimization with {n_iterations} iterations.")
    print(f"Parameter bounds: amplitude_ref {param_bounds[0]}, train_count {param_bounds[1]}")
    
    for i in range(n_iterations):
        print(f"\n{'='*60}")
        print(f"Iteration {i+1}/{n_iterations}")
        print(f"{'='*60}")
        
        # Suggest next parameters
        params = bo.suggest_next_location()
        amplitude_ref, train_count = params
        print(f"Suggested parameters: amplitude_ref={amplitude_ref:.2f}, train_count={train_count:.2f}")
        
        # Run experiment
        try:
            burst_rate = bo.run_experiment(params)
            print(f"Observed burst rate: {burst_rate:.2f} bursts/s")
        except Exception as e:
            print(f"Experiment failed: {e}")
            # Assign a high burst rate to discourage this region
            burst_rate = 100.0
        
        # Observe the result
        bo.observe(params, burst_rate)
        print(f"Updated observations: {len(bo.X)} points")
        
        # Print current best
        if len(bo.y) > 0:
            best_idx = np.argmin(bo.y)
            best_params = bo.X[best_idx]
            best_burst = bo.y[best_idx]
            print(f"Current best: amplitude_ref={best_params[0]:.2f}, train_count={best_params[1]:.2f} -> burst rate={best_burst:.2f} bursts/s")
    
    # Final summary
    print(f"\n{'='*60}")
    print("Bayesian Optimization Complete")
    print(f"{'='*60}")
    if len(bo.y) > 0:
        best_idx = np.argmin(bo.y)
        best_params = bo.X[best_idx]
        best_burst = bo.y[best_idx]
        print(f"Best parameters found: amplitude_ref={best_params[0]:.2f}, train_count={best_params[1]:.2f}")
        print(f"Best burst rate: {best_burst:.2f} bursts/s")
        
        # Compare to baseline (from our earlier experiments, baseline burst rate was about 98 bursts in 20s = 4.9 bursts/s)
        baseline_burst_rate = 4.9  # from earlier experiment
        print(f"Baseline burst rate (from earlier experiment): {baseline_burst_rate:.2f} bursts/s")
        if best_burst < baseline_burst_rate:
            print(f"Improvement: {((baseline_burst_rate - best_burst) / baseline_burst_rate * 100):.1f}% reduction in burst rate")
        else:
            print(f"No improvement over baseline; burst rate increased by {((best_burst - baseline_burst_rate) / baseline_burst_rate * 100):.1f}%")
    else:
        print("No successful observations.")
    
    # Save the BO state
    state = {
        "X": bo.X,
        "y": bo.y,
        "param_bounds": param_bounds,
        "n_iterations": n_iterations
    }
    with open("bo_state.json", "w") as f:
        json.dump(state, f, indent=2)
    print("Saved BO state to bo_state.json")

if __name__ == "__main__":
    main()