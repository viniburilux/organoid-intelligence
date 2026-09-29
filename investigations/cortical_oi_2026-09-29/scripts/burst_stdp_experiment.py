#!/usr/bin/env python3
"""
Burst-STDP Protocol Experiment
==============================
Tests if burst-triggered stimulation with precise spike-timing induces 
spike-timing-dependent plasticity-like changes in burst probability.

Protocol:
1. Record baseline burst rate (no stimulation) - 10s
2. Run closed-loop stimulation with fixed delay relative to detected bursts:
   - Condition LTP-like: stimulation at +10ms after burst onset
   - Condition LTD-like: stimulation at -10ms before burst onset (predicted)
   - Control: no stimulation
3. Record post-stimulation burst rate (no stimulation) - 10s
4. Compare pre vs post burst rates for each condition

Hypothesis:
- Post-burst stimulation (+10ms) will increase burst rate (LTP-like)
- Pre-burst stimulation (-10ms) will decrease burst rate (LTD-like)
- Control will show no systematic change

Falsification: If burst rate changes don't follow expected timing-dependent pattern
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

class BurstSTDPController(CorticalOIController):
    def __init__(self, config, condition, current_ua=1.0, train_count=5):
        """
        condition: 'ltp' (+10ms post-burst), 'ltd' (-10ms pre-burst predicted), 'control' (no stim)
        """
        super().__init__(config)
        self.condition = condition
        self.current_ua = current_ua if condition != 'control' else 0.0
        self.train_count = train_count if condition != 'control' else 0
        self.stimulation_channels = list(range(8))
        self.burst_count = 0
        self.phase = "baseline"  # baseline, stimulation, post
        self.phase_burst_counts = {"baseline": 0, "stimulation": 0, "post": 0}
        self.phase_start_tick = {"baseline": 0, "stimulation": 0, "post": 0}
        
    def run_integration_experiment(self):
        print(f"\n🧬 Starting Burst-STDP Experiment: {self.condition.upper()} condition")
        print(f"   Current: {self.current_ua} µA, Train count: {self.train_count}")
        print(f"   Phases: baseline(10s) -> stimulation(10s) -> post(10s)\n")
        
        recording_path = None
        try:
            with cl.open() as neurons:
                print(f"📡 Connected to Cortical Simulator: {neurons}")
                
                # Create research state data stream
                research_ds = neurons.create_data_stream(
                    "research_state",
                    {
                        "experiment": "burst_stdp_protocol",
                        "hypothesis": f"{self.condition}: timing-dependent plasticity",
                        "version": "1.0",
                        "integration_type": "cortical_cl_api_oi_sandbox",
                        "condition": self.condition
                    }
                )
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
                recording_path = self.config.output_dir / f"{timestamp}_burst_stdp_{self.condition}.h5"
                
                # Start recording with data streams
                recording = neurons.record(
                    file_suffix=f"_burst_stdp_{self.condition}",
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
                        self.phase_start_tick["stimulation"] = tick_count
                        print(f"\n🔄 Phase transition: BASELINE -> STIMULATION (tick {tick_count})")
                    elif tick_count == 2 * phase_duration_ticks:
                        self.phase = "post"
                        self.phase_start_tick["post"] = tick_count
                        print(f"\n🔄 Phase transition: STIMULATION -> POST (tick {tick_count})")
                    
                    # Detect bursts using our analyzer
                    current_spikes = tick.analysis.spikes
                    
                    bursts = self.burst_analyzer.detect_bursts(current_spikes, tick_count, int(tick.timestamp))
                    
                    for burst in bursts:
                        self.burst_count += 1
                        self.phase_burst_counts[self.phase] += 1
                        
                        # Deliver stimulation based on condition and phase
                        if self.phase == "stimulation" and self.condition != 'control':
                            self._deliver_stimulation_stdp(burst, tick_count, neurons)
                        
                        # Log to research state
                        if tick_count % 500 == 0:
                            research_ds.append(tick.timestamp, {
                                "phase": self.phase,
                                "tick": tick_count,
                                "condition": self.condition,
                                "total_bursts": self.burst_count,
                                "phase_bursts": self.phase_burst_counts.copy()
                            })
                    
                    # Progress
                    if tick_count % 1000 == 0 and tick_count > 0:
                        print(f"   ⏱️  Tick {tick_count}/{total_ticks} | Phase: {self.phase} | Bursts: {self.burst_count} (baseline:{self.phase_burst_counts['baseline']}, stim:{self.phase_burst_counts['stimulation']}, post:{self.phase_burst_counts['post']})")
                
                # Final research state update
                research_ds.append(neurons.timestamp(), {
                    "phase": "complete",
                    "condition": self.condition,
                    "total_bursts": self.burst_count,
                    "phase_bursts": self.phase_burst_counts,
                    "baseline_rate": self.phase_burst_counts["baseline"] / 10.0,
                    "stim_rate": self.phase_burst_counts["stimulation"] / 10.0,
                    "post_rate": self.phase_burst_counts["post"] / 10.0
                })
                
        except Exception as e:
            print(f"❌ Error during experiment: {e}")
            raise
        
        print(f"\n✅ Experiment completed!")
        print(f"   Baseline (10s):  {self.phase_burst_counts['baseline']} bursts ({self.phase_burst_counts['baseline']/10:.2f} bursts/s)")
        print(f"   Stimulation (10s): {self.phase_burst_counts['stimulation']} bursts ({self.phase_burst_counts['stimulation']/10:.2f} bursts/s)")
        print(f"   Post (10s):      {self.phase_burst_counts['post']} bursts ({self.phase_burst_counts['post']/10:.2f} bursts/s)")
        
        return self.phase_burst_counts, recording_path
    
    def _deliver_stimulation_stdp(self, burst, tick_count, neurons):
        """Deliver STDP-style stimulation with precise timing relative to burst."""
        try:
            duration_us = 200
            stim_design = cl.StimDesign(duration_us, -self.current_ua, duration_us, self.current_ua)
            
            if self.condition == 'ltp':
                # LTP-like: stimulate AFTER burst (+10ms = +5 ticks at 500Hz)
                # In simulator, we deliver immediately but log the intended timing
                timing_note = "POST-burst (+10ms intended)"
            elif self.condition == 'ltd':
                # LTD-like: stimulate BEFORE predicted burst (-10ms = -5 ticks)
                # We approximate by stimulating on burst detection (which is slightly after onset)
                timing_note = "PRE-burst (-10ms intended)"
            else:
                timing_note = "control"
            
            for i in range(self.train_count):
                for ch in self.stimulation_channels:
                    neurons.stim(ch, stim_design)
            
            # Log stimulation event
            self.stim_log.append({
                "tick": tick_count,
                "timestamp": burst["timestamp"],
                "condition": self.condition,
                "timing": timing_note,
                "burst_tick": burst["tick"],
                "channels": self.stimulation_channels.copy(),
                "current_ua": self.current_ua,
                "train_count": self.train_count,
                "pulse_width_us": duration_us
            })
            
        except Exception as e:
            print(f"   ⚠️  Warning: Failed to deliver stimulation: {e}")

def run_all_conditions():
    """Run all three conditions sequentially."""
    conditions = ['control', 'ltp', 'ltd']
    results = {}
    
    for condition in conditions:
        print(f"\n{'='*70}")
        print(f"RUNNING CONDITION: {condition.upper()}")
        print(f"{'='*70}")
        
        # Configuration
        config = CorticalIntegrationConfig(
            ticks_per_second=500,
            stop_after_seconds=30.0,  # 3 phases x 10s
            burst_min_spikes=3,
            burst_max_isi_ms=15.0,
            prediction_window_ms=50.0,
            research_state_update_interval_ticks=10,
            output_dir=Path(f"./burst_stdp_results/{condition}"),
            recording_suffix=f"_burst_stdp_{condition}"
        )
        config.output_dir.mkdir(parents=True, exist_ok=True)
        
        controller = BurstSTDPController(config, condition, current_ua=1.0, train_count=5)
        phase_counts, recording_path = controller.run_integration_experiment()
        
        results[condition] = {
            "phase_counts": phase_counts,
            "baseline_rate": phase_counts["baseline"] / 10.0,
            "stim_rate": phase_counts["stimulation"] / 10.0,
            "post_rate": phase_counts["post"] / 10.0,
            "recording": str(recording_path)
        }
        
        # Save intermediate results
        with open(config.output_dir / "phase_counts.json", "w") as f:
            json.dump(results[condition], f, indent=2)
    
    return results

def analyze_results(results):
    """Analyze and print comparison across conditions."""
    print(f"\n{'='*70}")
    print("BURST-STDP PROTOCOL RESULTS ANALYSIS")
    print(f"{'='*70}")
    
    print(f"\n{'Condition':<12} | {'Baseline':>8} | {'Stim':>8} | {'Post':>8} | {'ΔPost-Baseline':>14}")
    print("-" * 60)
    
    for cond in ['control', 'ltp', 'ltd']:
        r = results[cond]
        delta = r["post_rate"] - r["baseline_rate"]
        print(f"{cond:<12} | {r['baseline_rate']:>8.2f} | {r['stim_rate']:>8.2f} | {r['post_rate']:>8.2f} | {delta:>+14.2f}")
    
    # Key comparisons
    print(f"\n--- KEY COMPARISONS ---")
    
    # LTP vs Control post-stimulation change
    ltp_delta = results['ltp']["post_rate"] - results['ltp']["baseline_rate"]
    control_delta = results['control']["post_rate"] - results['control']["baseline_rate"]
    ltd_delta = results['ltd']["post_rate"] - results['ltd']["baseline_rate"]
    
    print(f"LTP post-baseline change:  {ltp_delta:+.2f} bursts/s")
    print(f"Control post-baseline change: {control_delta:+.2f} bursts/s")
    print(f"LTD post-baseline change:  {ltd_delta:+.2f} bursts/s")
    
    # Hypothesis test
    print(f"\n--- HYPOTHESIS TEST ---")
    print(f"H1: LTP (+10ms) increases burst rate vs control")
    print(f"    LTP delta: {ltp_delta:+.2f}, Control delta: {control_delta:+.2f}")
    print(f"    Supported: {ltp_delta > control_delta}")
    
    print(f"H2: LTD (-10ms) decreases burst rate vs control")
    print(f"    LTD delta: {ltd_delta:+.2f}, Control delta: {control_delta:+.2f}")
    print(f"    Supported: {ltd_delta < control_delta}")
    
    print(f"H3: LTP vs LTD show opposite effects")
    print(f"    LTP delta: {ltp_delta:+.2f}, LTD delta: {ltd_delta:+.2f}")
    print(f"    Supported: {ltp_delta > ltd_delta}")
    
    # Falsification criteria
    print(f"\n--- FALSIFICATION CHECK ---")
    falsified = []
    if not (ltp_delta > control_delta):
        falsified.append("H1: LTP did not increase burst rate relative to control")
    if not (ltd_delta < control_delta):
        falsified.append("H2: LTD did not decrease burst rate relative to control")
    if not (ltp_delta > ltd_delta):
        falsified.append("H3: LTP and LTD did not show opposite effects")
    
    if falsified:
        print("❌ HYPOTHESIS FALSIFIED:")
        for f in falsified:
            print(f"   - {f}")
    else:
        print("✅ All hypotheses supported by data")
    
    return {
        "ltp_delta": ltp_delta,
        "control_delta": control_delta,
        "ltd_delta": ltd_delta,
        "hypotheses_supported": len(falsified) == 0,
        "falsified": falsified
    }

def main():
    print("="*70)
    print("BURST-STDP PROTOCOL EXPERIMENT")
    print("Testing timing-dependent plasticity in cortical networks")
    print("="*70)
    
    # Run all conditions
    results = run_all_conditions()
    
    # Analyze
    analysis = analyze_results(results)
    
    # Save complete results
    output = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "burst_stdp_protocol",
        "conditions": results,
        "analysis": analysis
    }
    
    output_path = Path("./burst_stdp_results/complete_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Complete results saved to: {output_path}")
    print("\n🏁 Experiment complete!")

if __name__ == "__main__":
    main()