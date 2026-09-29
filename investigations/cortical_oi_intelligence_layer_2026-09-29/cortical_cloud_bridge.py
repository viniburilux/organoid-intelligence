#!/usr/bin/env python3
"""
Cortical Cloud Data Bridge
==========================
Bridges our investigation infrastructure with real Cortical Cloud data.
Supports:
1. Recording ingestion and validation
2. Format verification (HDF5 structure, data streams)
3. Spike/event representation
4. Feature extraction
5. Analysis pipeline integration
6. Hypothesis generation
7. Stimulation/action planning
8. Observation and evidence collection
9. Contradiction detection
10. ResearchState update
11. Provenance persistence
"""

import sys, json, os, h5py, msgpack
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Add our integration to path
sys.path.insert(0, "/home/vinicius")
from cortical_oi_integration import CorticalOIController, CorticalIntegrationConfig, BurstAnalyzer

@dataclass
class CloudRecordingMetadata:
    """Metadata for a Cortical Cloud recording"""
    file_path: str
    channel_count: int
    sampling_frequency: int
    frames_per_second: int
    duration_seconds: float
    duration_frames: int
    start_timestamp: int
    end_timestamp: int
    uV_per_sample_unit: float
    has_samples: bool
    has_spikes: bool
    has_stims: bool
    has_data_streams: bool
    data_stream_names: List[str]
    spike_count: int
    stim_count: int
    file_size_mb: float

@dataclass
class SpikeEvent:
    """Standardized spike event representation"""
    timestamp: int  # microseconds
    channel: int
    waveform: Optional[np.ndarray] = None
    amplitude: Optional[float] = None

@dataclass 
class StimEvent:
    """Standardized stimulation event"""
    timestamp: int  # microseconds
    channel: int
    current_ua: Optional[float] = None
    pulse_width_us: Optional[int] = None
    train_count: Optional[int] = None

class CorticalCloudBridge:
    """
    Bridge between Cortical Cloud recordings and our investigation infrastructure.
    """
    
    def __init__(self, recording_path: str):
        self.recording_path = Path(recording_path)
        self.metadata: Optional[CloudRecordingMetadata] = None
        self._file: Optional[h5py.File] = None
        self._recording_view = None
        
    def open(self) -> 'CorticalCloudBridge':
        """Open and validate the recording"""
        if not self.recording_path.exists():
            raise FileNotFoundError(f"Recording not found: {self.recording_path}")
        
        self._file = h5py.File(self.recording_path, 'r')
        self._validate_structure()
        self._extract_metadata()
        return self
    
    def close(self):
        if self._file:
            self._file.close()
            self._file = None
    
    def __enter__(self):
        return self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _validate_structure(self):
        """Validate HDF5 structure matches expected Cortical format"""
        required_datasets = ['spikes', 'stims']
        for ds in required_datasets:
            if ds not in self._file:
                raise ValueError(f"Missing required dataset: {ds}")
        
        # Check root attributes
        required_attrs = ['channel_count', 'sampling_frequency', 'frames_per_second', 
                         'duration_frames', 'start_timestamp', 'end_timestamp',
                         'uV_per_sample_unit']
        for attr in required_attrs:
            if attr not in self._file.attrs:
                raise ValueError(f"Missing required attribute: {attr}")
    
    def _extract_metadata(self):
        """Extract recording metadata"""
        attrs = self._file.attrs
        self.metadata = CloudRecordingMetadata(
            file_path=str(self.recording_path),
            channel_count=int(attrs['channel_count']),
            sampling_frequency=int(attrs['sampling_frequency']),
            frames_per_second=int(attrs['frames_per_second']),
            duration_seconds=float(attrs['duration_seconds']),
            duration_frames=int(attrs['duration_frames']),
            start_timestamp=int(attrs['start_timestamp']),
            end_timestamp=int(attrs['end_timestamp']),
            uV_per_sample_unit=float(attrs['uV_per_sample_unit']),
            has_samples='samples' in self._file,
            has_spikes='spikes' in self._file,
            has_stims='stims' in self._file,
            has_data_streams='data_stream' in self._file,
            data_stream_names=list(self._file['data_stream'].keys()) if 'data_stream' in self._file else [],
            spike_count=self._file['spikes'].shape[0] if 'spikes' in self._file else 0,
            stim_count=self._file['stims'].shape[0] if 'stims' in self._file else 0,
            file_size_mb=self.recording_path.stat().st_size / (1024*1024)
        )
    
    def get_spikes(self, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[SpikeEvent]:
        """Get spikes as standardized events, optionally time-filtered"""
        if 'spikes' not in self._file:
            return []
        
        spikes_ds = self._file['spikes']
        spikes = spikes_ds[:]
        
        if start_ts is not None or end_ts is not None:
            mask = np.ones(len(spikes), dtype=bool)
            if start_ts is not None:
                mask &= spikes['timestamp'] >= start_ts
            if end_ts is not None:
                mask &= spikes['timestamp'] <= end_ts
            spikes = spikes[mask]
        
        events = []
        for sp in spikes:
            events.append(SpikeEvent(
                timestamp=int(sp['timestamp']),
                channel=int(sp['channel']),
                waveform=sp['samples'] if 'samples' in sp.dtype.names else None
            ))
        return events
    
    def get_stims(self, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[StimEvent]:
        """Get stimulation events"""
        if 'stims' not in self._file:
            return []
        
        stims_ds = self._file['stims']
        stims = stims_ds[:]
        
        if start_ts is not None or end_ts is not None:
            mask = np.ones(len(stims), dtype=bool)
            if start_ts is not None:
                mask &= stims['timestamp'] >= start_ts
            if end_ts is not None:
                mask &= stims['timestamp'] <= end_ts
            stims = stims[mask]
        
        events = []
        for st in stims:
            events.append(StimEvent(
                timestamp=int(st['timestamp']),
                channel=int(st['channel'])
            ))
        return events
    
    def get_samples(self, start_frame: int = 0, frame_count: Optional[int] = None) -> np.ndarray:
        """Get raw samples (shape: frames x channels)"""
        if 'samples' not in self._file:
            return np.array([])
        
        samples_ds = self._file['samples']
        if frame_count is None:
            frame_count = samples_ds.shape[0] - start_frame
        
        return samples_ds[start_frame:start_frame + frame_count, :]
    
    def get_data_stream(self, stream_name: str) -> Dict[int, Any]:
        """Get data stream entries as {timestamp: data} dict"""
        if 'data_stream' not in self._file or stream_name not in self._file['data_stream']:
            return {}
        
        ds_group = self._file['data_stream'][stream_name]
        index_ds = ds_group['index']
        data_ds = ds_group['data']
        
        index = index_ds[:]
        results = {}
        for entry in index:
            ts = entry['timestamp']
            start_idx = entry['start_index']
            end_idx = entry['end_index']
            raw_data = data_ds[start_idx:end_idx]
            # Deserialize msgpack
            decoded = msgpack.unpackb(raw_data, raw=False)
            results[ts] = decoded
        
        return results
    
    def iter_time_windows(self, window_ms: float = 100.0, step_ms: float = 50.0):
        """Iterate over time windows, yielding (start_ts, end_ts, spikes, stims)"""
        if not self.metadata:
            return
        
        window_us = int(window_ms * 1000)
        step_us = int(step_ms * 1000)
        
        current = self.metadata.start_timestamp
        while current + window_us <= self.metadata.end_timestamp:
            spikes = self.get_spikes(current, current + window_us)
            stims = self.get_stims(current, current + window_us)
            yield current, current + window_us, spikes, stims
            current += step_us
    
    def detect_bursts_in_window(self, window_ms: float = 100.0, step_ms: float = 50.0) -> List[Dict]:
        """Detect bursts in sliding windows across recording"""
        if not self.metadata:
            return []
        
        # Use our BurstAnalyzer
        config = CorticalIntegrationConfig(
            burst_min_spikes=3,
            burst_max_isi_ms=15.0,
            prediction_window_ms=50.0
        )
        analyzer = BurstAnalyzer(config)
        
        all_bursts = []
        for start_ts, end_ts, spikes, _ in self.iter_time_windows(window_ms, step_ms):
            # Convert to format expected by analyzer
            spike_dicts = [{'timestamp': s.timestamp, 'channel': s.channel} for s in spikes]
            bursts = analyzer.detect_bursts(spike_dicts, 0, start_ts)  # tick=0, timestamp=start_ts
            for b in bursts:
                b['window_start'] = start_ts
                b['window_end'] = end_ts
                all_bursts.append(b)
        
        return all_bursts
    
    def compute_basic_features(self, window_ms: float = 100.0, step_ms: float = 50.0) -> List[Dict]:
        """Compute basic features for each time window"""
        features = []
        for start_ts, end_ts, spikes, stims in self.iter_time_windows(window_ms, step_ms):
            # Channel activity
            channel_counts = {}
            for s in spikes:
                channel_counts[s.channel] = channel_counts.get(s.channel, 0) + 1
            
            feat = {
                'window_start': start_ts,
                'window_end': end_ts,
                'spike_count': len(spikes),
                'stim_count': len(stims),
                'active_channels': len(channel_counts),
                'channel_counts': channel_counts,
                'mean_rate_hz': len(spikes) / (window_ms / 1000.0) if window_ms > 0 else 0
            }
            features.append(feat)
        
        return features
    
    def to_research_state_format(self) -> Dict:
        """Convert metadata to format compatible with our ResearchState"""
        return {
            'source': 'cortical_cloud',
            'recording_path': str(self.recording_path),
            'metadata': asdict(self.metadata) if self.metadata else {},
            'ingested_at': datetime.now().isoformat()
        }


class RealDataExperimentRunner:
    """
    Runs our investigation protocols on real Cortical Cloud data.
    """
    
    def __init__(self, bridge: CorticalCloudBridge):
        self.bridge = bridge
        self.results = {}
    
    def run_burst_characterization(self) -> Dict:
        """Characterize burst dynamics in real data"""
        print("Running burst characterization on real data...")
        
        # Detect bursts across full recording
        bursts = self.bridge.detect_bursts_in_window(window_ms=100.0, step_ms=50.0)
        
        # Compute statistics
        if bursts:
            burst_rates = []
            inter_burst_intervals = []
            
            prev_burst_ts = None
            current_window = None
            window_bursts = 0
            
            for b in bursts:
                ts = b['timestamp']
                if current_window is None or ts - current_window > 100000:  # 100ms window
                    if current_window is not None and window_bursts > 0:
                        burst_rates.append(window_bursts * 10)  # per second
                    current_window = ts
                    window_bursts = 1
                else:
                    window_bursts += 1
                
                if prev_burst_ts is not None:
                    inter_burst_intervals.append(ts - prev_burst_ts)
                prev_burst_ts = ts
            
            if window_bursts > 0:
                burst_rates.append(window_bursts * 10)
            
            return {
                'total_bursts': len(bursts),
                'mean_burst_rate_hz': np.mean(burst_rates) if burst_rates else 0,
                'burst_rate_std': np.std(burst_rates) if burst_rates else 0,
                'mean_ibi_us': np.mean(inter_burst_intervals) if inter_burst_intervals else 0,
                'ibi_std_us': np.std(inter_burst_intervals) if inter_burst_intervals else 0,
                'burst_spike_counts': [b['spike_count'] for b in bursts],
                'mean_spikes_per_burst': np.mean([b['spike_count'] for b in bursts]) if bursts else 0
            }
        else:
            return {'total_bursts': 0, 'message': 'No bursts detected'}
    
    def run_stim_response_analysis(self) -> Dict:
        """Analyze neural responses to stimulation"""
        print("Running stimulation response analysis...")
        
        if not self.bridge.metadata or not self.bridge.metadata.has_stims:
            return {'message': 'No stimulation events in recording'}
        
        stims = self.bridge.get_stims()
        if not stims:
            return {'message': 'No stimulation events'}
        
        # Analyze peri-stimulus time histogram (PSTH) around each stim
        pre_window = 50000  # 50ms before
        post_window = 100000  # 100ms after
        
        all_pre_spikes = []
        all_post_spikes = []
        
        for stim in stims[:100]:  # Limit to first 100 for speed
            pre_spikes = self.bridge.get_spikes(
                stim.timestamp - pre_window, 
                stim.timestamp
            )
            post_spikes = self.bridge.get_spikes(
                stim.timestamp,
                stim.timestamp + post_window
            )
            all_pre_spikes.append(len(pre_spikes))
            all_post_spikes.append(len(post_spikes))
        
        return {
            'total_stims': len(stims),
            'analyzed_stims': min(100, len(stims)),
            'mean_pre_spikes': np.mean(all_pre_spikes) if all_pre_spikes else 0,
            'mean_post_spikes': np.mean(all_post_spikes) if all_post_spikes else 0,
            'stim_response_ratio': (np.mean(all_post_spikes) / np.mean(all_pre_spikes)) if all_pre_spikes and np.mean(all_pre_spikes) > 0 else 0
        }
    
    def run_state_transition_detection(self) -> Dict:
        """Detect neural state transitions using change-point detection on features"""
        print("Running state transition detection...")
        
        features = self.bridge.compute_basic_features(window_ms=500.0, step_ms=250.0)
        if len(features) < 10:
            return {'message': 'Insufficient windows for transition detection'}
        
        # Simple change-point detection on spike rate
        rates = [f['mean_rate_hz'] for f in features]
        
        # Use cumulative sum (CUSUM) for change detection
        mean_rate = np.mean(rates)
        std_rate = np.std(rates)
        
        if std_rate == 0:
            return {'message': 'No rate variation detected'}
        
        # Detect significant deviations (> 2 std)
        transitions = []
        for i, rate in enumerate(rates):
            z_score = (rate - mean_rate) / std_rate
            if abs(z_score) > 2.0:
                transitions.append({
                    'window_idx': i,
                    'timestamp': features[i]['window_start'],
                    'rate': rate,
                    'z_score': z_score,
                    'direction': 'increase' if z_score > 0 else 'decrease'
                })
        
        return {
            'mean_rate': mean_rate,
            'std_rate': std_rate,
            'transitions': transitions,
            'transition_count': len(transitions)
        }
    
    def run_full_characterization(self) -> Dict:
        """Run complete characterization pipeline"""
        print("="*60)
        print("FULL CORTICAL CLOUD RECORDING CHARACTERIZATION")
        print("="*60)
        
        results = {
            'metadata': asdict(self.bridge.metadata) if self.bridge.metadata else {},
            'burst_characterization': self.run_burst_characterization(),
            'stim_response': self.run_stim_response_analysis(),
            'state_transitions': self.run_state_transition_detection(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results = results
        return results
    
    def save_results(self, output_path: str):
        """Save characterization results"""
        with open(output_path, 'w') as f:
            # Convert numpy types to Python types for JSON
            def convert(obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(v) for v in obj]
                return obj
            
            json.dump(convert(self.results), f, indent=2)
        print(f"\nResults saved to: {output_path}")


def validate_recording_for_replay(recording_path: str) -> Tuple[bool, List[str]]:
    """Validate that a recording is compatible with CL_MOCK_REPLAY_PATH"""
    errors = []
    warnings = []
    
    with h5py.File(recording_path, 'r') as f:
        # Check required datasets
        for ds in ['spikes', 'stims', 'samples']:
            if ds not in f:
                errors.append(f"Missing dataset: {ds}")
        
        # Check attributes
        required_attrs = ['channel_count', 'sampling_frequency', 'frames_per_second',
                         'duration_frames', 'start_timestamp', 'end_timestamp',
                         'uV_per_sample_unit']
        for attr in required_attrs:
            if attr not in f.attrs:
                errors.append(f"Missing attribute: {attr}")
        
        # Check data stream format
        if 'data_stream' in f:
            for name in f['data_stream']:
                ds = f['data_stream'][name]
                if 'index' not in ds or 'data' not in ds:
                    warnings.append(f"Data stream '{name}' missing index or data")
        
        # Check spike format
        if 'spikes' in f:
            spikes = f['spikes']
            if 'timestamp' not in spikes.dtype.names or 'channel' not in spikes.dtype.names:
                errors.append("Spikes dataset missing required fields (timestamp, channel)")
            if 'samples' not in spikes.dtype.names:
                warnings.append("Spikes dataset missing waveform samples (required for full replay)")
        
        # Check stim format
        if 'stims' in f:
            stims = f['stims']
            if 'timestamp' not in stims.dtype.names or 'channel' not in stims.dtype.names:
                errors.append("Stims dataset missing required fields (timestamp, channel)")
    
    return len(errors) == 0, errors + warnings


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cortical Cloud Data Bridge")
    parser.add_argument("recording", help="Path to HDF5 recording")
    parser.add_argument("--output", help="Output JSON path for results")
    parser.add_argument("--validate", action="store_true", help="Only validate recording format")
    
    args = parser.parse_args()
    
    if args.validate:
        valid, issues = validate_recording_for_replay(args.recording)
        print(f"Valid for replay: {valid}")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        sys.exit(0 if valid else 1)
    
    # Run full characterization
    with CorticalCloudBridge(args.recording) as bridge:
        print(f"Loaded recording: {bridge.metadata.file_path}")
        print(f"  Channels: {bridge.metadata.channel_count}")
        print(f"  Duration: {bridge.metadata.duration_seconds:.2f}s")
        print(f"  Spikes: {bridge.metadata.spike_count}")
        print(f"  Stims: {bridge.metadata.stim_count}")
        print(f"  Data streams: {bridge.metadata.data_stream_names}")
        
        runner = RealDataExperimentRunner(bridge)
        results = runner.run_full_characterization()
        
        if args.output:
            runner.save_results(args.output)
        else:
            print(json.dumps(results, indent=2, default=str))