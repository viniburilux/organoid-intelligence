#!/usr/bin/env python3
"""
Adaptive Feature-Based Stimulation Experiment
==============================================
Tests if adaptive stimulation scaled by burst features (spike count, synchrony) 
leads to lasting changes in network burst dynamics.

Protocol:
1. Record baseline burst rate (no stimulation) - 10s
2. Run closed-loop stimulation where stimulation intensity is scaled by burst feature:
   - Feature: spike count in detected burst
   - Stim amplitude = base_current * (burst_spike_count / reference_spike_count)
   - Train count scaled similarly
3. Record post-stimulation burst rate (no stimulation) - 10s
4. Compare pre vs post burst rates

Hypothesis: Adaptive stimulation based on burst features will produce lasting 
changes in burst rate after stimulation ends, indicating network plasticity.

Falsification: If burst rate returns to pre-stimulation levels immediately 
after stimulation ends, hypothesis is falsified (no lasting change).
"""

import sys, json, time, numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path("/home/vinicius")))
from cortical_oi_integration import CorticalOIController, CorticalIntegrationConfig

try:
    import cl
except ImportError:
    print("CL SDK not available")
    sys.exit(1)

class AdaptiveFeatureStimController(CorticalOIController):
    def __init__(self, config, base_current_ua=1.0, base_train_count=5, 
                 reference_spike_count=5, max_current_ua=5.0, max_train_count=10):
        super().__init__(config)
        self.base_current_ua = base_current_ua
        self.base_train_count = base_train_count
        self.reference_spike_count = reference_spike_count
        self.max_current_ua = max_current_ua
        self.max_train_count = max_train_count
        self.stimulation_channels = list(range(8))
        self.burst_count = 0
        self.phase = "baseline"  # baseline, stimulation, post
        self.phase_burst_counts = {"baseline": 0, "stimulation": 0, "post": 0}
        self.burst_features_log = []  # log burst features for analysis
        
    def run_integration_experiment(self):
        print(f"\n🧬 Starting Adaptive Feature Stim Experiment")
        print(f"   Base current: {self.base_current_ua} µA, Base train count: {self.base_train_count}")
        print(f"   Reference spike count: {self.reference_spike_count}")
        print(f"   Max current: {self.max_current_ua} µA, Max train count: {self.max_train_count}")
        print(f"   Phases: baseline(10s) -> adaptive_stim(10s) -> post(10s)\n")
        
        recording_path = None
        try:
            with cl.open() as neurons:
                print(f"📡 Connected to Cortical Simulator: {neurons}")
                
                # Create research state data stream
                research_ds = neurons.create_data_stream(
                    "research_state",
                    {
                        "experiment": "adaptive_feature_stimulation",
                        "hypothesis": "adaptive stim by burst features causes lasting plasticity",
                        "version": "1.0",
                        "integration_type": "cortical_cl_api_oi_sandbox"
                    }
                )
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
                recording_path = self.config.output_dir / f"{timestamp}_adaptive_feature_stim.h5"
                
                # Start recording with data streams
                recording = neurons.record(
                    file_suffix="_adaptive_feature_stim",
                    include_data_streams=True,
                    include_spikes=True,
                    include_stims=True,
                    include_raw_samples=True,
                )
                
                print(f"📼 Recording started: {recording.file['path']}")
                
                # Phase timing: 10s each = 5000 ticks each at 500Hz
                phase_duration_ticks = 5000
                total_ticks = phase_duration_ticks * 3
                
                tick_count = 0
                for tick in neurons.loop(
                    ticks_per_second=self.config.ticks_per_second,
                    stop_after_seconds=30.0,  # 30s total
                    ignore_jitter=True
                ):
                    tick_count = tick.iteration
                    
                    # Phase transitions
                    if tick_count == phase_duration_ticks:
                        self.phase = "stimulation"
                        print(f"\n🔄 Phase transition: BASELINE -> ADAPTIVE STIMULATION (tick {tick_count})")
                    elif tick_count == 2 * phase_duration_ticks:
                        self.phase = "post"
                        print(f"\n🔄 Phase transition: STIMULATION -> POST (tick {tick_count})")
                    
                    # Detect bursts using our analyzer
                    current_spikes = tick.analysis.spikes
                    
                    bursts = self.burst_analyzer.detect_bursts(current_spikes, tick_count, int(tick.timestamp))
                    
                    for burst in bursts:
                        self.burst_count += 1
                        self.phase_burst_counts[self.phase] += 1
                        
                        # Extract burst features
                        spike_count = burst["spike_count"]
                        channels = burst["channels"]
                        unique_channels = len(set(channels))
                        synchrony = unique_channels / max(1, spike_count)  # simple synchrony metric
                        
                        # Log burst features
                        self.burst_features_log.append({
                            "tick": tick_count,
                            "phase": self.phase,
                            "spike_count": spike_count,
                            "unique_channels": unique_channels,
                            "synchrony": synchrony,
                            "timestamp": burst["timestamp"]
                        })
                        
                        # Deliver adaptive stimulation if in stimulation phase
                        if self.phase == "stimulation":
                            self._deliver_adaptive_stimulation(burst, tick_count, neurons, 
                                                              spike_count, synchrony)
                        
                        # Log to research state periodically
                        if tick_count % 500 == 0:
                            research_ds.append(tick.timestamp, {
                                "phase": self.phase,
                                "tick": tick_count,
                                "total_bursts": self.burst_count,
                                "phase_bursts": self.phase_burst_counts.copy(),
                                "last_burst_features": {
                                    "spike_count": spike_count,
                                    "synchrony": synchrony
                                } if self.burst_features_log else None
                            })
                    
                    # Progress
                    if tick_count % 1000 == 0 and tick_count > 0:
                        print(f"   ⏱️  Tick {tick_count}/{total_ticks} | Phase: {self.phase} | Bursts: {self.burst_count} (baseline:{self.phase_burst_counts['baseline']}, stim:{self.phase_burst_counts['stimulation']}, post:{self.phase_burst_counts['post']})")
                
                # Final research state update
                research_ds.append(neurons.timestamp(), {
                    "phase": "complete",
                    "total_bursts": self.burst_count,
                    "phase_bursts": self.phase_burst_counts,
                    "baseline_rate": self.phase_burst_counts["baseline"] / 10.0,
                    "stim_rate": self.phase_burst_counts["stimulation"] / 10.0,
                    "post_rate": self.phase_burst_counts["post"] / 10.0,
                    "burst_features_log": self.burst_features_log
                })
                
        except Exception as e:
            print(f"❌ Error during experiment: {e}")
            raise
        
        print(f"\n✅ Experiment completed!")
        print(f"   Baseline (10s):  {self.phase_burst_counts['baseline']} bursts ({self.phase_burst_counts['baseline']/10:.2f} bursts/s)")
        print(f"   Stimulation (10s): {self.phase_burst_counts['stimulation']} bursts ({self.phase_burst_counts['stimulation']/10:.2f} bursts/s)")
        print(f"   Post (10s):      {self.phase_burst_counts['post']} bursts ({self.phase_burst_counts['post']/10:.2f} bursts/s)")
        
        return self.phase_burst_counts, self.burst_features_log, recording_path
    
    def _deliver_adaptive_stimulation(self, burst, tick_count, neurons, spike_count, synchrony):
        """Deliver stimulation scaled by burst features."""
        try:
            duration_us = 200
            
            # Scale current by spike count (more spikes = stronger stim)
            spike_ratio = spike_count / self.reference_spike_count
            current_ua = min(self.base_current_ua * spike_ratio, self.max_current_ua)
            
            # Scale train count by synchrony (more synchronous = more pulses)
            sync_ratio = max(0.5, min(synchrony * 2, 1.0))  # clamp 0.5-1.0
            train_count = max(1, int(self.base_train_count * sync_ratio))
            train_count = min(train_count, self.max_train_count)
            
            stim_design = cl.StimDesign(duration_us, -current_ua, duration_us, current_ua)
            
            for i in range(train_count):
                for ch in self.stimulation_channels:
                    neurons.stim(ch, stim_design)
            
            # Log stimulation event with adaptive parameters
            self.stim_log.append({
                "tick": tick_count,
                "timestamp": burst["timestamp"],
                "phase": self.phase,
                "burst_spike_count": spike_count,
                "burst_synchrony": synchrony,
                "adapted_current_ua": current_ua,
                "adapted_train_count": train_count,
                "channels": self.stimulation_channels.copy(),
                "pulse_width_us": duration_us
            })
            
        except Exception as e:
            print(f"   ⚠️  Warning: Failed to deliver stimulation: {e}")

def run_experiment():
    """Run the adaptive feature stimulation experiment."""
    print("="*70)
    print("ADAPTIVE FEATURE-BASED STIMULATION EXPERIMENT")
    print("Testing if burst-feature-scaled stim causes lasting plasticity")
    print("="*70)
    
    # Configuration
    config = CorticalIntegrationConfig(
        ticks_per_second=500,
        stop_after_seconds=30.0,  # 3 phases x 10s
        burst_min_spikes=3,
        burst_max_isi_ms=15.0,
        prediction_window_ms=50.0,
        research_state_update_interval_ticks=10,
        output_dir=Path(f"./adaptive_feature_results"),
        recording_suffix="_adaptive_feature_stim"
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    controller = AdaptiveFeatureStimController(
        config, 
        base_current_ua=1.0, 
        base_train_count=5,
        reference_spike_count=5,
        max_current_ua=5.0,
        max_train_count=10
    )
    phase_counts, burst_features, recording_path = controller.run_integration_experiment()
    
    # Analyze results
    print(f"\n{'='*70}")
    print("ADAPTIVE FEATURE STIMULATION RESULTS")
    print(f"{'='*70}")
    
    baseline_rate = phase_counts["baseline"] / 10.0
    stim_rate = phase_counts["stimulation"] / 10.0
    post_rate = phase_counts["post"] / 10.0
    delta_post_baseline = post_rate - baseline_rate
    
    print(f"Baseline (10s):  {phase_counts['baseline']} bursts ({baseline_rate:.2f} bursts/s)")
    print(f"Stimulation (10s): {phase_counts['stimulation']} bursts ({stim_rate:.2f} bursts/s)")
    print(f"Post (10s):      {phase_counts['post']} bursts ({post_rate:.2f} bursts/s)")
    print(f"Δ Post-Baseline:  {delta_post_baseline:+.2f} bursts/s")
    
    # Burst feature statistics during stimulation
    stim_features = [f for f in burst_features if f["phase"] == "stimulation"]
    if stim_features:
        avg_spike_count = np.mean([f["spike_count"] for f in stim_features])
        avg_synchrony = np.mean([f["synchrony"] for f in stim_features])
        print(f"\nBurst features during stimulation:")
        print(f"  Average spike count: {avg_spike_count:.2f}")
        print(f"  Average synchrony: {avg_synchrony:.2f}")
        print(f"  Number of stimulated bursts: {len(stim_features)}")
    
    # Hypothesis test
    print(f"\n--- HYPOTHESIS TEST ---")
    print(f"H: Adaptive stim causes lasting change (post ≠ baseline)")
    print(f"   Baseline rate: {baseline_rate:.2f}, Post rate: {post_rate:.2f}")
    print(f"   Change: {delta_post_baseline:+.2f} bursts/s")
    
    # Falsification: no lasting change = returns to baseline
    # Using a threshold: if |delta| < 0.1 bursts/s, consider no change
    threshold = 0.1
    if abs(delta_post_baseline) < threshold:
        print(f"❌ HYPOTHESIS FALSIFIED: |Δ| = {abs(delta_post_baseline):.2f} < {threshold} (no lasting change)")
        hypothesis_supported = False
        falsification = "Burst rate returned to baseline levels after stimulation ended"
    else:
        direction = "increase" if delta_post_baseline > 0 else "decrease"
        print(f"✅ HYPOTHESIS SUPPORTED: Lasting {direction} in burst rate detected")
        hypothesis_supported = True
        falsification = None
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "adaptive_feature_stimulation",
        "parameters": {
            "base_current_ua": controller.base_current_ua,
            "base_train_count": controller.base_train_count,
            "reference_spike_count": controller.reference_spike_count,
            "max_current_ua": controller.max_current_ua,
            "max_train_count": controller.max_train_count
        },
        "phase_counts": phase_counts,
        "rates": {
            "baseline": baseline_rate,
            "stimulation": stim_rate,
            "post": post_rate
        },
        "delta_post_baseline": delta_post_baseline,
        "hypothesis_supported": hypothesis_supported,
        "falsification": falsification,
        "burst_features_log": burst_features,
        "recording": str(recording_path)
    }
    
    output_path = Path("./adaptive_feature_results/complete_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Complete results saved to: {output_path}")
    print("\n🏁 Experiment complete!")
    
    return results

def main():
    run_experiment()

if __name__ == "__main__":
    main()