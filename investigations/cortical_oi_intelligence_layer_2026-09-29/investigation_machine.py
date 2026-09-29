#!/usr/bin/env python3
"""
Investigation Machine for Real Cortical Cloud Data
===================================================
A complete autonomous investigation system that:
1. Characterizes real neural data
2. Detects regimes and transitions
3. Identifies stimulation responses
4. Generates and tests hypotheses
5. Tracks contradictions
6. Evolves ResearchState
6. Preserves full provenance

Principle: THE DATA DETERMINES THE QUESTION.
THE QUESTION DOES NOT MANUFACTURE THE DATA.
"""

import sys, json, os, h5py, msgpack, time
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
import uuid

# Add our modules to path
sys.path.insert(0, "/home/vinicius")
from cortical_oi_integration import CorticalOIController, CorticalIntegrationConfig, BurstAnalyzer, ResearchState
from cortical_cloud_bridge import CorticalCloudBridge, RealDataExperimentRunner, SpikeEvent, StimEvent

class HypothesisStatus(Enum):
    PENDING = "pending"
    TESTING = "testing"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"

@dataclass
class Hypothesis:
    """Scientific hypothesis with prediction and falsification criteria"""
    id: str
    question: str
    prediction: str  # What we expect to observe if true
    falsification_criterion: str  # What would falsify it
    status: HypothesisStatus = HypothesisStatus.PENDING
    evidence: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tested_at: Optional[str] = None
    confidence: float = 0.0  # 0-1

@dataclass
class ContradictionRecord:
    """Record of a contradiction between prediction and observation"""
    timestamp: str
    expected: str
    observed: str
    context: str
    severity: str

@dataclass
class InvestigationSession:
    """Complete investigation session record"""
    session_id: str
    recording_path: str
    start_time: str
    metadata: Dict
    hypotheses: List[Hypothesis] = field(default_factory=list)
    observations: List[Dict] = field(default_factory=list)
    contradictions: List[ContradictionRecord] = field(default_factory=list)
    research_state_snapshots: List[Dict] = field(default_factory=list)
    provenance: List[Dict] = field(default_factory=list)
    end_time: Optional[str] = None
    status: str = "active"

class InvestigationMachine:
    """
    Autonomous investigation machine for real Cortical Cloud data.
    
    Does NOT pre-determine discoveries.
    Lets the data drive the questions.
    """
    
    def __init__(self, bridge: CorticalCloudBridge, output_dir: str = "./investigation_output"):
        self.bridge = bridge
        self.runner = RealDataExperimentRunner(bridge)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = InvestigationSession(
            session_id=f"invest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            recording_path=str(bridge.recording_path),
            start_time=datetime.now().isoformat(),
            metadata=asdict(bridge.metadata) if bridge.metadata else {}
        )
        
        self.research_state = ResearchState(
            active_question="Characterize neural dynamics in this recording",
            hypothesis="The recording contains structured neural activity with detectable bursts and state transitions",
            contradictions_total=0,
            contradiction_log=[],
            burst_predictions_made=0,
            burst_predictions_confirmed=0,
            burst_predictions_failed=0,
            next_question="",
            last_update_tick=0,
            total_bursts_observed=0,
            experiment_start_time=datetime.now().isoformat(),
            session_id=self.session.session_id
        )
        
        # Analysis components
        self.burst_analyzer = None
        self._init_analyzers()
        
        print(f"🔬 Investigation Machine initialized: {self.session.session_id}")
        print(f"   Recording: {bridge.metadata.file_path if bridge.metadata else 'unknown'}")
        print(f"   Output: {self.output_dir}")
    
    def _init_analyzers(self):
        """Initialize analysis components"""
        config = CorticalIntegrationConfig(
            burst_min_spikes=3,
            burst_max_isi_ms=15.0,
            prediction_window_ms=50.0
        )
        self.burst_analyzer = BurstAnalyzer(config)
        
        # Store config in research state
        self.research_state.burst_analyzer_config = {
            'burst_min_spikes': config.burst_min_spikes,
            'burst_max_isi_ms': config.burst_max_isi_ms,
            'prediction_window_ms': config.prediction_window_ms
        }
    
    def _log_provenance(self, step: str, inputs: List[str], outputs: List[str], 
                       parameters: Dict, code_version: str = "1.0"):
        """Log full provenance for each step"""
        prov = {
            "step_id": f"{step}_{len(self.session.provenance)}",
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "inputs": inputs,
            "outputs": outputs,
            "parameters": parameters,
            "code_version": code_version,
            "environment": {
                "python": sys.version.split()[0],
                "platform": sys.platform
            }
        }
        self.session.provenance.append(prov)
    
    def _snapshot_research_state(self, trigger: str):
        """Snapshot research state for traceability"""
        snapshot = {
            "trigger": trigger,
            "timestamp": datetime.now().isoformat(),
            "current_question": self.research_state.active_question,
            "hypotheses_count": len(self.session.hypotheses),
            "evidence_count": len(self.session.observations),
            "contradiction_count": len(self.research_state.contradiction_log),
            "next_questions": self.research_state.next_question if self.research_state.next_question else []
        }
        self.session.research_state_snapshots.append(snapshot)
    
    # ===== PHASE 1: CHARACTERIZATION =====
    
    def characterize(self) -> Dict:
        """Phase 1: Comprehensive data characterization"""
        print("\n" + "="*60)
        print("PHASE 1: DATA CHARACTERIZATION")
        print("="*60)
        
        results = self.runner.run_full_characterization()
        
        # Log provenance
        self._log_provenance(
            step="characterize",
            inputs=[self.session.recording_path],
            outputs=["burst_characterization", "stim_response", "state_transitions"],
            parameters={"window_ms": 100, "step_ms": 50}
        )
        
        # Update research state with observations
        self._add_observation("recording_metadata", asdict(self.bridge.metadata) if self.bridge.metadata else {})
        self._add_observation("burst_characterization", results.get("burst_characterization", {}))
        self._add_observation("stim_response", results.get("stim_response", {}))
        self._add_observation("state_transitions", results.get("state_transitions", {}))
        
        # Generate initial hypotheses from data
        self._generate_hypotheses_from_characterization(results)
        
        self._snapshot_research_state("post_characterization")
        return results
    
    def _generate_hypotheses_from_characterization(self, results: Dict):
        """Generate hypotheses based on characterization results"""
        hypotheses = []
        
        # From burst characterization
        burst_char = results.get("burst_characterization", {})
        if burst_char.get("total_bursts", 0) > 0:
            mean_rate = burst_char.get("mean_burst_rate_hz", 0)
            hypotheses.append(Hypothesis(
                id=f"hyp_burst_rate_{len(self.session.hypotheses)}",
                question=f"Is the baseline burst rate stable around {mean_rate:.2f} Hz?",
                prediction="Burst rate will remain within 2 std of mean across recording",
                falsification_criterion="Burst rate changes by > 2 std from baseline in any 10s window"
            ))
            
            mean_spikes = burst_char.get("mean_spikes_per_burst", 0)
            hypotheses.append(Hypothesis(
                id=f"hyp_burst_size_{len(self.session.hypotheses)}",
                question=f"Do bursts consistently contain ~{mean_spikes:.1f} spikes?",
                prediction="Burst spike counts follow narrow distribution around mean",
                falsification_criterion="Burst spike count distribution is bimodal or has CV > 0.5"
            ))
        
        # From state transitions
        state_trans = results.get("state_transitions", {})
        transitions = state_trans.get("transitions", [])
        if transitions:
            hypotheses.append(Hypothesis(
                id=f"hyp_state_transitions_{len(self.session.hypotheses)}",
                question="Do detected state transitions correspond to meaningful neural regime changes?",
                prediction="Transitions correlate with changes in burst patterns or network synchrony",
                falsification_criterion="Transitions are uncorrelated with any other neural features"
            ))
        
        # From stimulation response (if applicable)
        stim_resp = results.get("stim_response", {})
        if stim_resp.get("stim_response_ratio", 0) > 1.5:
            hypotheses.append(Hypothesis(
                id=f"hyp_stim_excitation_{len(self.session.hypotheses)}",
                question="Does stimulation consistently increase neural activity?",
                prediction="Post-stimulus spike count > pre-stimulus in >70% of stim events",
                falsification_criterion="Post-stimulus spike count <= pre-stimulus in >50% of events"
            ))
        elif stim_resp.get("stim_response_ratio", 0) < 0.5:
            hypotheses.append(Hypothesis(
                id=f"hyp_stim_suppression_{len(self.session.hypotheses)}",
                question="Does stimulation consistently suppress neural activity?",
                prediction="Post-stimulus spike count < pre-stimulus in >70% of stim events",
                falsification_criterion="Post-stimulus spike count >= pre-stimulus in >50% of events"
            ))
        
        # Add hypotheses to session and research state
        for h in hypotheses:
            self.session.hypotheses.append(h)
            # ResearchState has hypothesis field (single string), track multiple in session
        
        print(f"  Generated {len(hypotheses)} initial hypotheses from characterization")
        for h in hypotheses:
            print(f"    - {h.id}: {h.question}")
    
    def _add_observation(self, obs_type: str, data: Any):
        """Add observation to session and research state"""
        obs = {
            "type": obs_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.session.observations.append(obs)
        # ResearchState doesn't have evidence_log, just track in session
    
    # ===== PHASE 2: HYPOTHESIS TESTING =====
    
    def test_hypothesis(self, hypothesis_id: str) -> Dict:
        """Test a specific hypothesis against the data"""
        print(f"\n--- Testing Hypothesis: {hypothesis_id} ---")
        
        # Find hypothesis
        hyp = None
        for h in self.session.hypotheses:
            if h.id == hypothesis_id:
                hyp = h
                break
        
        if not hyp:
            return {"error": f"Hypothesis {hypothesis_id} not found"}
        
        hyp.status = HypothesisStatus.TESTING
        hyp.tested_at = datetime.now().isoformat()
        
        # Route to appropriate test based on hypothesis type
        if "burst_rate" in hypothesis_id:
            result = self._test_burst_rate_stability(hyp)
        elif "burst_size" in hypothesis_id:
            result = self._test_burst_size_distribution(hyp)
        elif "state_transitions" in hypothesis_id:
            result = self._test_state_transition_meaning(hyp)
        elif "stim_excitation" in hypothesis_id:
            result = self._test_stim_excitation(hyp)
        elif "stim_suppression" in hypothesis_id:
            result = self._test_stim_suppression(hyp)
        else:
            result = {"status": "inconclusive", "reason": "No test implemented for this hypothesis type"}
        
        # Update hypothesis
        hyp.status = HypothesisStatus(result.get("status", "inconclusive"))
        hyp.evidence.append(result)
        hyp.confidence = result.get("confidence", 0.0)
        
        # Update research state - it only has single hypothesis field
        # Track multiple hypotheses in session only
        
        # Check for contradictions
        self._check_contradictions(hyp, result)
        
        self._log_provenance(
            step=f"test_hypothesis_{hypothesis_id}",
            inputs=[self.session.recording_path],
            outputs=[f"hypothesis_result_{hypothesis_id}"],
            parameters={"hypothesis": hyp.question}
        )
        
        self._snapshot_research_state(f"tested_{hypothesis_id}")
        
        print(f"  Result: {hyp.status.value} (confidence: {hyp.confidence:.2f})")
        return result
    
    def _test_burst_rate_stability(self, hyp: Hypothesis) -> Dict:
        """Test if burst rate is stable across recording"""
        burst_char = self.session.observations[1]["data"] if len(self.session.observations) > 1 else {}
        if burst_char.get("total_bursts", 0) == 0:
            return {"status": "inconclusive", "confidence": 0.0, "reason": "No bursts detected"}
        
        # Get bursts across full recording
        bursts = self.bridge.detect_bursts_in_window(window_ms=100.0, step_ms=50.0)
        if not bursts:
            return {"status": "inconclusive", "confidence": 0.0, "reason": "No bursts in windowed analysis"}
        
        # Compute burst rate per 10s window
        window_duration = 10_000_000  # 10s in microseconds
        rates = []
        current_window_start = self.bridge.metadata.start_timestamp
        window_bursts = 0
        
        for b in sorted(bursts, key=lambda x: x['timestamp']):
            ts = b['timestamp']
            if ts >= current_window_start + window_duration:
                rates.append(window_bursts / 10.0)  # per second
                current_window_start = ts
                window_bursts = 1
            else:
                window_bursts += 1
        
        if window_bursts > 0:
            rates.append(window_bursts / 10.0)
        
        if len(rates) < 2:
            return {"status": "inconclusive", "confidence": 0.0, "reason": "Insufficient windows"}
        
        mean_rate = np.mean(rates)
        std_rate = np.std(rates)
        cv = std_rate / mean_rate if mean_rate > 0 else 0
        
        # Falsification: any window > 2 std from mean
        falsified = any(abs(r - mean_rate) > 2 * std_rate for r in rates)
        
        return {
            "status": "falsified" if falsified else "supported",
            "confidence": 1.0 - min(cv, 1.0),
            "mean_rate_hz": mean_rate,
            "std_rate_hz": std_rate,
            "cv": cv,
            "window_rates": rates,
            "falsified": falsified
        }
    
    def _test_burst_size_distribution(self, hyp: Hypothesis) -> Dict:
        """Test if burst sizes follow narrow distribution"""
        bursts = self.bridge.detect_bursts_in_window(window_ms=100.0, step_ms=50.0)
        if not bursts:
            return {"status": "inconclusive", "confidence": 0.0}
        
        spike_counts = [b['spike_count'] for b in bursts]
        mean_spikes = np.mean(spike_counts)
        std_spikes = np.std(spike_counts)
        cv = std_spikes / mean_spikes if mean_spikes > 0 else 0
        
        # Falsification: CV > 0.5
        falsified = cv > 0.5
        
        return {
            "status": "falsified" if falsified else "supported",
            "confidence": max(0, 1.0 - cv * 2),
            "mean_spikes": mean_spikes,
            "std_spikes": std_spikes,
            "cv": cv,
            "spike_counts": spike_counts[:50],  # limit output
            "falsified": falsified
        }
    
    def _test_state_transition_meaning(self, hyp: Hypothesis) -> Dict:
        """Test if state transitions correlate with neural features"""
        # Get transitions from characterization
        state_trans = self.session.observations[3]["data"] if len(self.session.observations) > 3 else {}
        transitions = state_trans.get("transitions", [])
        
        if not transitions:
            return {"status": "inconclusive", "confidence": 0.0, "reason": "No transitions detected"}
        
        # Get features around each transition
        features = self.bridge.compute_basic_features(window_ms=500.0, step_ms=250.0)
        
        correlations = []
        for t in transitions:
            t_idx = t.get('window_idx', 0)
            if 0 < t_idx < len(features) - 1:
                before = features[max(0, t_idx-2):t_idx]
                after = features[t_idx+1:min(len(features), t_idx+3)]
                
                if before and after:
                    before_rates = [f['mean_rate_hz'] for f in before]
                    after_rates = [f['mean_rate_hz'] for f in after]
                    if before_rates and after_rates:
                        change = np.mean(after_rates) - np.mean(before_rates)
                        correlations.append(change)
        
        if not correlations:
            return {"status": "inconclusive", "confidence": 0.0}
        
        # Check if transitions correspond to rate changes
        significant_changes = sum(1 for c in correlations if abs(c) > 0.5)
        support_ratio = significant_changes / len(correlations)
        
        return {
            "status": "supported" if support_ratio > 0.5 else "falsified",
            "confidence": support_ratio,
            "total_transitions": len(transitions),
            "correlated_transitions": significant_changes,
            "mean_change": np.mean(correlations) if correlations else 0,
            "support_ratio": support_ratio
        }
    
    def _test_stim_excitation(self, hyp: Hypothesis) -> Dict:
        """Test if stimulation excites"""
        if not self.bridge.metadata.has_stims:
            return {"status": "inconclusive", "confidence": 0.0}
        
        stims = self.bridge.get_stims()
        if not stims:
            return {"status": "inconclusive", "confidence": 0.0}
        
        pre_window = 50000
        post_window = 100000
        
        excited = 0
        total = min(100, len(stims))
        
        for stim in stims[:total]:
            pre = len(self.bridge.get_spikes(stim.timestamp - pre_window, stim.timestamp))
            post = len(self.bridge.get_spikes(stim.timestamp, stim.timestamp + post_window))
            if post > pre:
                excited += 1
        
        ratio = excited / total if total > 0 else 0
        falsified = ratio <= 0.5
        
        return {
            "status": "falsified" if falsified else "supported",
            "confidence": abs(ratio - 0.5) * 2,
            "excited_count": excited,
            "total_tested": total,
            "ratio": ratio
        }
    
    def _test_stim_suppression(self, hyp: Hypothesis) -> Dict:
        """Test if stimulation suppresses"""
        if not self.bridge.metadata.has_stims:
            return {"status": "inconclusive", "confidence": 0.0}
        
        stims = self.bridge.get_stims()
        if not stims:
            return {"status": "inconclusive", "confidence": 0.0}
        
        pre_window = 50000
        post_window = 100000
        
        suppressed = 0
        total = min(100, len(stims))
        
        for stim in stims[:total]:
            pre = len(self.bridge.get_spikes(stim.timestamp - pre_window, stim.timestamp))
            post = len(self.bridge.get_spikes(stim.timestamp, stim.timestamp + post_window))
            if post < pre:
                suppressed += 1
        
        ratio = suppressed / total if total > 0 else 0
        falsified = ratio <= 0.5
        
        return {
            "status": "falsified" if falsified else "supported",
            "confidence": abs(ratio - 0.5) * 2,
            "suppressed_count": suppressed,
            "total_tested": total,
            "ratio": ratio
        }
    
    def _check_contradictions(self, hyp: Hypothesis, result: Dict):
        """Check for contradictions between hypothesis prediction and evidence"""
        # Simple contradiction: prediction was specific but evidence contradicts
        if hyp.status == HypothesisStatus.FALSIFIED:
            contradiction = {
                "timestamp": datetime.now().isoformat(),
                "expected": hyp.prediction,
                "observed": str(result),
                "context": f"Hypothesis test: {hyp.question}",
                "severity": "high" if hyp.confidence > 0.7 else "medium"
            }
            self.session.contradictions.append(contradiction)
            self.research_state.contradiction_log.append(contradiction)
            print(f"  ⚠️ CONTRADICTION DETECTED: {contradiction['context']}")
    
    def test_all_hypotheses(self) -> List[Dict]:
        """Test all pending hypotheses"""
        print("\n" + "="*60)
        print("PHASE 2: HYPOTHESIS TESTING")
        print("="*60)
        
        results = []
        for hyp in self.session.hypotheses:
            if hyp.status == HypothesisStatus.PENDING:
                result = self.test_hypothesis(hyp.id)
                results.append(result)
        
        return results
    
    # ===== PHASE 3: DISCOVERY-DRIVEN EXPLORATION =====
    
    def discover_patterns(self) -> Dict:
        """Phase 3: Let the data reveal patterns without pre-specified hypotheses"""
        print("\n" + "="*60)
        print("PHASE 3: DISCOVERY-DRIVEN EXPLORATION")
        print("="*60)
        
        discoveries = {}
        
        # 1. Temporal clustering analysis
        discoveries["temporal_clustering"] = self._analyze_temporal_clustering()
        
        # 2. Channel correlation structure
        discoveries["channel_correlations"] = self._analyze_channel_correlations()
        
        # 3. Stimulation artifact characterization (if stim present)
        if self.bridge.metadata.has_stims:
            discoveries["stim_artifacts"] = self._analyze_stim_artifacts()
        
        # 4. Burst network structure (multi-channel bursts)
        discoveries["burst_networks"] = self._analyze_burst_networks()
        
        # 5. Anomaly detection
        discoveries["anomalies"] = self._detect_anomalies()
        
        # Log provenance
        self._log_provenance(
            step="discover_patterns",
            inputs=[self.session.recording_path],
            outputs=list(discoveries.keys()),
            parameters={}
        )
        
        self._snapshot_research_state("post_discovery")
        
        # Generate new questions from discoveries
        self._generate_questions_from_discoveries(discoveries)
        
        return discoveries
    
    def _analyze_temporal_clustering(self) -> Dict:
        """Analyze if spikes/bursts cluster in time beyond Poisson expectation"""
        spikes = self.bridge.get_spikes()
        if len(spikes) < 10:
            return {"message": "Insufficient spikes"}
        
        # ISI distribution
        timestamps = sorted([s.timestamp for s in spikes])
        isis = np.diff(timestamps)
        
        # Compare to exponential (Poisson)
        mean_isi = np.mean(isis)
        cv_isi = np.std(isis) / mean_isi if mean_isi > 0 else 0
        
        # Poisson has CV=1; CV<1 = regular, CV>1 = bursting
        regime = "poisson" if 0.8 < cv_isi < 1.2 else ("regular" if cv_isi <= 0.8 else "bursting")
        
        return {
            "mean_isi_us": mean_isi,
            "cv_isi": cv_isi,
            "regime": regime,
            "isi_stats": {
                "min": np.min(isis),
                "max": np.max(isis),
                "median": np.median(isis)
            }
        }
    
    def _analyze_channel_correlations(self) -> Dict:
        """Analyze cross-channel correlations"""
        spikes = self.bridge.get_spikes()
        if len(spikes) < 10:
            return {"message": "Insufficient spikes"}
        
        # Bin spikes into 10ms bins per channel
        bin_us = 10000
        start_ts = self.bridge.metadata.start_timestamp
        end_ts = self.bridge.metadata.end_timestamp
        n_bins = int((end_ts - start_ts) / bin_us) + 1
        
        n_channels = self.bridge.metadata.channel_count
        binned = np.zeros((n_channels, n_bins))
        
        for s in spikes:
            ch = s.channel
            bin_idx = (s.timestamp - start_ts) // bin_us
            if 0 <= ch < n_channels and 0 <= bin_idx < n_bins:
                binned[ch, bin_idx] += 1
        
        # Compute pairwise correlations (sample subset for speed)
        active_channels = [i for i in range(n_channels) if np.sum(binned[i]) > 10]
        if len(active_channels) < 2:
            return {"message": "Insufficient active channels"}
        
        # Sample up to 20 channels
        sample_chs = active_channels[:min(20, len(active_channels))]
        corr_matrix = np.corrcoef(binned[sample_chs])
        
        # Mean off-diagonal correlation
        mask = ~np.eye(len(sample_chs), dtype=bool)
        mean_corr = np.mean(corr_matrix[mask])
        max_corr = np.max(corr_matrix[mask])
        
        return {
            "active_channels": len(active_channels),
            "analyzed_channels": len(sample_chs),
            "mean_correlation": float(mean_corr),
            "max_correlation": float(max_corr),
            "correlation_distribution": {
                "mean": float(np.mean(corr_matrix[mask])),
                "std": float(np.std(corr_matrix[mask])),
                "min": float(np.min(corr_matrix[mask])),
                "max": float(np.max(corr_matrix[mask]))
            }
        }
    
    def _analyze_stim_artifacts(self) -> Dict:
        """Characterize stimulation artifacts in recordings"""
        stims = self.bridge.get_stims()
        if not stims:
            return {"message": "No stims"}
        
        # Look at raw samples around first few stims
        artifacts = []
        for stim in stims[:5]:
            # Get samples around stim
            frame_idx = int((stim.timestamp - self.bridge.metadata.start_timestamp) / 
                          (1e6 / self.bridge.metadata.sampling_frequency))
            
            window_frames = 100  # ~4ms at 25kHz
            start_frame = max(0, frame_idx - window_frames)
            end_frame = min(self.bridge.metadata.duration_frames, frame_idx + window_frames)
            
            samples = self.bridge.get_samples(start_frame, end_frame - start_frame)
            if len(samples) > 0:
                # Check for large deflections on stimulated channel
                ch = stim.channel
                if ch < samples.shape[1]:
                    ch_signal = samples[:, ch]
                    peak = np.max(np.abs(ch_signal))
                    baseline = np.median(np.abs(ch_signal))
                    artifacts.append({
                        "stim_timestamp": stim.timestamp,
                        "channel": ch,
                        "peak_amplitude": float(peak),
                        "baseline_amplitude": float(baseline),
                        "artifact_ratio": float(peak / baseline) if baseline > 0 else 0
                    })
        
        return {
            "artifacts_analyzed": len(artifacts),
            "artifacts": artifacts,
            "mean_artifact_ratio": np.mean([a['artifact_ratio'] for a in artifacts]) if artifacts else 0
        }
    
    def _analyze_burst_networks(self) -> Dict:
        """Analyze multi-channel burst synchronization"""
        bursts = self.bridge.detect_bursts_in_window(window_ms=50.0, step_ms=25.0)
        if not bursts:
            return {"message": "No bursts detected"}
        
        # Group bursts by time proximity (within 5ms = network burst)
        network_bursts = []
        for b in sorted(bursts, key=lambda x: x['timestamp']):
            if network_bursts and b['timestamp'] - network_bursts[-1]['channels'][-1]['timestamp'] < 5000:
                # Add to existing network burst
                network_bursts[-1]['channels'].append({'channel': b['channels'][0], 'timestamp': b['timestamp']})
            else:
                network_bursts.append({
                    'timestamp': b['timestamp'],
                    'channels': [{'channel': b['channels'][0], 'timestamp': b['timestamp']}]
                })
        
        # Filter for true multi-channel
        multi_channel = [nb for nb in network_bursts if len(set(c['channel'] for c in nb['channels'])) > 1]
        
        return {
            "total_detected_bursts": len(bursts),
            "network_bursts": len(network_bursts),
            "multi_channel_bursts": len(multi_channel),
            "sync_ratio": len(multi_channel) / len(network_bursts) if network_bursts else 0,
            "max_channels_in_burst": max(len(set(c['channel'] for c in nb['channels'])) for nb in network_bursts) if network_bursts else 0
        }
    
    def _detect_anomalies(self) -> Dict:
        """Detect anomalous periods in the recording"""
        features = self.bridge.compute_basic_features(window_ms=1000.0, step_ms=500.0)
        if len(features) < 20:
            return {"message": "Insufficient data for anomaly detection"}
        
        rates = [f['mean_rate_hz'] for f in features]
        active_chs = [f['active_channels'] for f in features]
        
        # Z-score based anomaly detection
        rate_mean, rate_std = np.mean(rates), np.std(rates)
        ch_mean, ch_std = np.mean(active_chs), np.std(active_chs)
        
        anomalies = []
        for i, f in enumerate(features):
            rate_z = abs(f['mean_rate_hz'] - rate_mean) / rate_std if rate_std > 0 else 0
            ch_z = abs(f['active_channels'] - ch_mean) / ch_std if ch_std > 0 else 0
            
            if rate_z > 3 or ch_z > 3:
                anomalies.append({
                    "window_idx": i,
                    "timestamp": f['window_start'],
                    "rate_z": rate_z,
                    "ch_z": ch_z,
                    "rate": f['mean_rate_hz'],
                    "active_channels": f['active_channels']
                })
        
        return {
            "total_windows": len(features),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[:10],  # limit output
            "rate_stats": {"mean": float(rate_mean), "std": float(rate_std)},
            "channel_stats": {"mean": float(ch_mean), "std": float(ch_std)}
        }
    
    def _generate_questions_from_discoveries(self, discoveries: Dict):
        """Generate new questions from discoveries (data-driven)"""
        new_questions = []
        
        # From temporal clustering
        tc = discoveries.get("temporal_clustering", {})
        if tc.get("regime") == "bursting":
            new_questions.append("What drives the bursting regime? Network connectivity? Intrinsic properties?")
        elif tc.get("regime") == "regular":
            new_questions.append("Is the regular firing due to pacemaker neurons or network inhibition?")
        
        # From channel correlations
        cc = discoveries.get("channel_correlations", {})
        if cc.get("mean_correlation", 0) > 0.1:
            new_questions.append(f"Channels show significant correlation (r={cc['mean_correlation']:.3f}). What is the network structure?")
        
        # From burst networks
        bn = discoveries.get("burst_networks", {})
        if bn.get("multi_channel_bursts", 0) > 0:
            new_questions.append(f"Multi-channel bursts detected ({bn['multi_channel_bursts']}). Are these synfire chains or population bursts?")
        
        # From anomalies
        anom = discoveries.get("anomalies", {})
        if anom.get("anomalies_detected", 0) > 0:
            new_questions.append(f"Found {anom['anomalies_detected']} anomalous periods. What triggers these regime changes?")
        
        # From stimulation artifacts
        sa = discoveries.get("stim_artifacts", {})
        if sa.get("artifacts_analyzed", 0) > 0:
            ratio = sa.get("mean_artifact_ratio", 0)
            if ratio > 10:
                new_questions.append(f"Large stimulation artifacts (ratio={ratio:.1f}). How to reject artifacts in real-time?")
        
        self.research_state.next_questions = new_questions
        self.session.hypotheses.extend([
            Hypothesis(
                id=f"hyp_discovery_{len(self.session.hypotheses)}_{i}",
                question=q,
                prediction="To be determined by further investigation",
                falsification_criterion="To be defined when hypothesis is formalized"
            )
            for i, q in enumerate(new_questions)
        ])
        
        print(f"  Generated {len(new_questions)} new questions from discoveries:")
        for q in new_questions:
            print(f"    - {q}")
    
    # ===== PHASE 4: CLOSED-LOOP EXPERIMENT DESIGN =====
    
    def design_next_experiment(self) -> Dict:
        """Phase 4: Design next experiment based on current ResearchState"""
        print("\n" + "="*60)
        print("PHASE 4: EXPERIMENT DESIGN (for real Cloud execution)")
        print("="*60)
        
        # This would run on real Cortical Cloud with live stimulation
        # For now, we design the protocol
        
        if not self.research_state.next_questions:
            return {"message": "No questions to pursue"}
        
        # Pick highest priority question
        question = self.research_state.next_questions[0]
        
        # Design experiment based on question type
        if "burst" in question.lower():
            design = self._design_burst_experiment(question)
        elif "correlation" in question.lower() or "network" in question.lower():
            design = self._design_network_experiment(question)
        elif "stimulation" in question.lower() or "artifact" in question.lower():
            design = self._design_stim_experiment(question)
        elif "anomal" in question.lower() or "regime" in question.lower():
            design = self._design_regime_experiment(question)
        else:
            design = self._design_generic_experiment(question)
        
        design["target_question"] = question
        design["designed_at"] = datetime.now().isoformat()
        design["session_id"] = self.session.session_id
        
        # Log provenance
        self._log_provenance(
            step="design_experiment",
            inputs=[self.session.recording_path],
            outputs=["experiment_design"],
            parameters={"question": question}
        )
        
        print(f"  Designed experiment for: {question}")
        print(f"  Protocol: {design.get('protocol', 'N/A')}")
        
        return design
    
    def _design_burst_experiment(self, question: str) -> Dict:
        """Design experiment to investigate bursting"""
        return {
            "protocol": "burst_characterization_with_stim",
            "stimulation": {
                "channels": list(range(min(8, self.bridge.metadata.channel_count))),
                "current_ua": 10,
                "pulse_width_us": 200,
                "train_count": 5,
                "inter_pulse_interval_us": 5000
            },
            "measurement": "burst rate, size, network synchrony pre/post stimulation",
            "duration_s": 120,
            "phases": ["baseline_30s", "stim_30s", "post_30s", "recovery_30s"]
        }
    
    def _design_network_experiment(self, question: str) -> Dict:
        """Design experiment to probe network structure"""
        return {
            "protocol": "connectivity_mapping",
            "stimulation": {
                "channels": list(range(min(16, self.bridge.metadata.channel_count))),
                "current_ua": 5,
                "pulse_width_us": 100,
                "train_count": 1,
                "pattern": "sequential_single_channel"
            },
            "measurement": "post-stimulus response latency and amplitude per channel",
            "duration_s": 180,
            "phases": ["baseline_30s", "mapping_120s", "recovery_30s"]
        }
    
    def _design_stim_experiment(self, question: str) -> Dict:
        """Design experiment for stimulation optimization"""
        return {
            "protocol": "stim_parameter_optimization",
            "stimulation": {
                "channels": list(range(min(8, self.bridge.metadata.channel_count))),
                "parameter_space": {
                    "current_ua": [1, 5, 10, 20, 50],
                    "pulse_width_us": [100, 200, 500, 1000],
                    "train_count": [1, 3, 5, 10]
                },
                "method": "bayesian_optimization",
                "objective": "minimize_burst_rate"
            },
            "measurement": "burst rate vs stimulation parameters",
            "duration_s": 600,
            "phases": ["baseline_60s", "bo_optimization_480s", "recovery_60s"]
        }
    
    def _design_regime_experiment(self, question: str) -> Dict:
        """Design experiment to probe regime transitions"""
        return {
            "protocol": "regime_perturbation",
            "stimulation": {
                "channels": list(range(min(16, self.bridge.metadata.channel_count))),
                "current_ua": 20,
                "pulse_width_us": 200,
                "train_count": 10,
                "trigger": "anomaly_detection"  # Stimulate when anomaly detected
            },
            "measurement": "time to return to baseline, trajectory of recovery",
            "duration_s": 300,
            "phases": ["baseline_60s", "perturbation_180s", "recovery_60s"]
        }
    
    def _design_generic_experiment(self, question: str) -> Dict:
        """Generic experiment design"""
        return {
            "protocol": "observation_only",
            "stimulation": None,
            "measurement": "comprehensive characterization",
            "duration_s": 120,
            "phases": ["extended_observation_120s"]
        }
    
    # ===== SAVE AND EXPORT =====
    
    def save_session(self, filename: Optional[str] = None) -> str:
        """Save complete investigation session"""
        if filename is None:
            filename = f"{self.session.session_id}.json"
        
        filepath = self.output_dir / filename
        
        # Convert to serializable format
        def convert(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            elif hasattr(obj, '__dict__'):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            return obj
        
        session_data = convert({
            "session": self.session.__dict__,
            "research_state": self.research_state.__dict__
        })
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"\n💾 Session saved to: {filepath}")
        return str(filepath)
    
    def export_for_cloud_execution(self, design: Dict) -> Dict:
        """Export experiment design in format for Cortical Cloud execution"""
        return {
            "experiment_id": f"exp_{self.session.session_id}_{datetime.now().strftime('%H%M%S')}",
            "session_id": self.session.session_id,
            "recording_metadata": asdict(self.bridge.metadata) if self.bridge.metadata else {},
            "protocol": design,
            "analysis_pipeline": {
                "burst_detection": {
                    "min_spikes": 3,
                    "max_isi_ms": 15.0
                },
                "features": ["burst_rate", "burst_size", "inter_burst_interval", 
                           "channel_synchrony", "stim_response"],
                "output_format": "hdf5_with_data_streams"
            },
            "success_criteria": {
                "min_recording_quality": "SNR > 3",
                "min_stim_delivery": "95%",
                "data_completeness": "100%"
            }
        }
    
    def run_full_investigation(self) -> Dict:
        """Run complete investigation pipeline"""
        print("="*60)
        print(f"STARTING FULL INVESTIGATION: {self.session.session_id}")
        print("="*60)
        
        # Phase 1: Characterize
        self.characterize()
        
        # Phase 2: Test hypotheses
        self.test_all_hypotheses()
        
        # Phase 3: Discover patterns
        discoveries = self.discover_patterns()
        
        # Phase 4: Design next experiment
        experiment_design = self.design_next_experiment()
        
        # Phase 5: Prepare for Cloud execution
        cloud_export = self.export_for_cloud_execution(experiment_design)
        
        # Finalize
        self.session.end_time = datetime.now().isoformat()
        self.session.status = "completed"
        
        # Save everything
        self.save_session()
        
        # Save cloud-ready design
        cloud_path = self.output_dir / f"{self.session.session_id}_cloud_experiment.json"
        with open(cloud_path, 'w') as f:
            json.dump(cloud_export, f, indent=2, default=str)
        
        print("\n" + "="*60)
        print("INVESTIGATION COMPLETE")
        print("="*60)
        print(f"  Session: {self.session.session_id}")
        print(f"  Hypotheses tested: {len([h for h in self.session.hypotheses if h.status != HypothesisStatus.PENDING])}")
        print(f"  Contradictions found: {len(self.session.contradictions)}")
        print(f"  New questions generated: {len(self.research_state.next_questions)}")
        print(f"  Cloud experiment design: {cloud_path}")
        
        return {
            "session_id": self.session.session_id,
            "hypotheses_tested": len([h for h in self.session.hypotheses if h.status != HypothesisStatus.PENDING]),
            "hypotheses_supported": len([h for h in self.session.hypotheses if h.status == HypothesisStatus.SUPPORTED]),
            "hypotheses_falsified": len([h for h in self.session.hypotheses if h.status == HypothesisStatus.FALSIFIED]),
            "contradictions": len(self.session.contradictions),
            "next_questions": self.research_state.next_questions,
            "cloud_experiment_design": str(cloud_path)
        }


def investigate_recording(recording_path: str, output_dir: str = "./investigation_output") -> Dict:
    """High-level function to run investigation on a recording"""
    with CorticalCloudBridge(recording_path) as bridge:
        machine = InvestigationMachine(bridge, output_dir)
        return machine.run_full_investigation()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Investigation Machine for Cortical Cloud Data")
    parser.add_argument("recording", help="Path to HDF5 recording")
    parser.add_argument("--output", help="Output directory", default="./investigation_output")
    
    args = parser.parse_args()
    
    result = investigate_recording(args.recording, args.output)
    print(json.dumps(result, indent=2, default=str))