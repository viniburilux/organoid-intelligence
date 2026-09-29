#!/usr/bin/env python3
"""
Reusable Analysis Pipelines
===========================
Wrappers around SpikeInterface, Neo, Elephant, NWB for our investigation pipeline.
Implements REUSE > ADAPT > BUILD principle.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# ============================================================
# PIPELINE 1: NWB Conversion from Cortical HDF5
# ============================================================

def convert_cortical_hdf5_to_nwb(cortical_h5_path: str, nwb_output_path: str, 
                                  subject_id: str = "unknown",
                                  session_id: str = "session_001") -> bool:
    """
    Convert Cortical HDF5 recording to NWB format.
    REUSES: PyNWB, HDMF, h5py
    ADAPTS: Cortical HDF5 schema -> NWB schema
    """
    try:
        import h5py
        from pynwb import NWBFile, NWBHDF5IO
        from pynwb.ecephys import ElectricalSeries
        from pynwb.ogen import OptogeneticSeries
        from datetime import datetime
        from dateutil.tz import tzlocal
        import uuid
    except ImportError as e:
        print(f"Missing dependencies for NWB conversion: {e}")
        print("Install: pip install pynwb hdmf")
        return False
    
    with h5py.File(cortical_h5_path, 'r') as f:
        # Extract metadata
        attrs = f.attrs
        channel_count = int(attrs.get('channel_count', 64))
        sampling_freq = int(attrs.get('sampling_frequency', 25000))
        duration_sec = float(attrs.get('duration_seconds', 0))
        start_ts = int(attrs.get('start_timestamp', 0))
        
        # Create NWB file
        nwbfile = NWBFile(
            session_description=f"Cortical recording converted from {Path(cortical_h5_path).name}",
            identifier=str(uuid.uuid4()),
            session_start_time=datetime.fromtimestamp(start_ts / 1e6, tz=tzlocal()),
            experimenter=["Cortical Labs"],
            lab="Cortical Labs",
            institution="Cortical Labs",
            experiment_description="Converted from Cortical HDF5 format",
            session_id=session_id
        )
        
        # Add subject
        from pynwb.file import Subject
        nwbfile.subject = Subject(
            subject_id=subject_id,
            species="Human cortical organoid" if "organoid" in cortical_h5_path.lower() else "Rat cortical culture",
            description="Neural recording from MEA"
        )
        
        # Add device
        device = nwbfile.create_device(
            name="CL1 HD-MEA",
            description="Cortical Labs CL1 High-Density Microelectrode Array"
        )
        
        # Add electrode group
        egroup = nwbfile.create_electrode_group(
            name="cl1_mea",
            description="64-channel HD-MEA",
            device=device,
            location="cortical surface"
        )
        
        # Add electrodes
        for ch in range(channel_count):
            nwbfile.add_electrode(
                id=ch,
                x=0.0, y=0.0, z=0.0,  # Unknown positions
                imp=-1.0,
                location="cortical",
                filtering="bandpass 300-3000 Hz",
                group=egroup
            )
        
        # Add spike data if available
        if 'spikes' in f:
            spike_data = f['spikes'][:]
            if len(spike_data) > 0:
                # Group by channel
                for ch in range(channel_count):
                    ch_spikes = spike_data[spike_data['channel'] == ch]
                    if len(ch_spikes) > 0:
                        timestamps = ch_spikes['timestamp'] / 1e6  # Convert to seconds
                        nwbfile.add_unit(
                            id=ch,
                            spike_times=timestamps,
                            electrodes=[ch],
                            description=f"Spike times for channel {ch} from Cortical spike sorting"
                        )
        
        # Add stimulation data if available
        if 'stims' in f:
            stim_data = f['stims'][:]
            if len(stim_data) > 0:
                for i, stim in enumerate(stim_data):
                    nwbfile.add_stimulus(
                        OptogeneticSeries(
                            name=f"stim_{i}",
                            data=np.array([1]),  # Binary pulse
                            timestamps=np.array([stim['timestamp'] / 1e6]),
                            description=f"Electrical stimulation on channel {stim['channel']}"
                        )
                    )
        
        # Write NWB file
        with NWBHDF5IO(nwb_output_path, mode='w') as io:
            io.write(nwbfile)
        
        print(f"Successfully converted {cortical_h5_path} -> {nwb_output_path}")
        return True


# ============================================================
# PIPELINE 2: SpikeInterface Recording Extractor for Cortical HDF5
# ============================================================

class CorticalRecordingExtractor:
    """
    SpikeInterface-compatible RecordingExtractor for Cortical HDF5 files.
    REUSES: SpikeInterface BaseRecordingExtractor
    """
    
    def __init__(self, file_path: str):
        import h5py
        self._file_path = file_path
        self._file = h5py.File(file_path, 'r')
        
        attrs = self._file.attrs
        self._sampling_frequency = float(attrs.get('sampling_frequency', 25000))
        self._num_channels = int(attrs.get('channel_count', 64))
        self._dtype = self._file['samples'].dtype if 'samples' in self._file else np.int16
        self._num_frames = self._file['samples'].shape[0] if 'samples' in self._file else 0
        
        # Channel IDs
        self._channel_ids = list(range(self._num_channels))
    
    def get_channel_ids(self):
        return self._channel_ids
    
    def get_num_channels(self):
        return self._num_channels
    
    def get_sampling_frequency(self):
        return self._sampling_frequency
    
    def get_num_frames(self):
        return self._num_frames
    
    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        if channel_ids is None:
            channel_ids = self._channel_ids
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self._num_frames
        
        # Read from HDF5
        samples = self._file['samples'][start_frame:end_frame, channel_ids]
        return samples.astype(np.float32)
    
    def close(self):
        self._file.close()


# ============================================================
# PIPELINE 3: Elephant-based Analysis (REUSE)
# ============================================================

def elephant_burst_detection(spike_trains, sampling_rate=25000, 
                              min_spikes=3, max_isi_ms=15.0):
    """
    Detect bursts using Elephant's burst detection.
    REUSES: Elephant burst_detection
    """
    try:
        import elephant.spike_train_generation as stg
        import elephant.spike_train_analysis as sta
        from elephant.spike_train_dissimilarity import victor_purpura_dist
        import quantities as pq
        from neo import SpikeTrain
    except ImportError:
        print("Elephant/Neo not available. Install: pip install elephant neo quantities")
        return []
    
    # Convert to Neo SpikeTrains
    neo_trains = []
    for ch_id, spikes in spike_trains.items():
        if len(spikes) > 0:
            st = SpikeTrain(
                times=spikes * pq.s,
                t_stop=max(spikes) * pq.s if len(spikes) > 0 else 0 * pq.s,
                units=pq.s
            )
            neo_trains.append((ch_id, st))
    
    # Detect bursts using ISI method
    bursts_by_channel = {}
    for ch_id, st in neo_trains:
        if len(st) >= min_spikes:
            isi = np.diff(st.magnitude) * 1000  # Convert to ms
            burst_mask = isi <= max_isi_ms
            
            # Find consecutive bursts
            burst_starts = []
            in_burst = False
            for i, is_burst in enumerate(burst_mask):
                if is_burst and not in_burst:
                    burst_starts.append(i)
                    in_burst = True
                elif not is_burst:
                    in_burst = False
            
            bursts_by_channel[ch_id] = []
            for start_idx in burst_starts:
                end_idx = start_idx
                while end_idx < len(burst_mask) and burst_mask[end_idx]:
                    end_idx += 1
                if end_idx - start_idx + 1 >= min_spikes:
                    bursts_by_channel[ch_id].append({
                        'start_time': st[start_idx],
                        'end_time': st[end_idx],
                        'spike_count': end_idx - start_idx + 1,
                        'isi_values': isi[start_idx:end_idx]
                    })
    
    return bursts_by_channel


def elephant_cross_correlation(spike_trains, bin_size_ms=10.0, max_lag_ms=100.0):
    """
    Cross-channel correlation using Elephant.
    REUSES: Elephant cross_correlation_histogram
    """
    try:
        from elephant.spike_train_correlation import cross_correlation_histogram
        from neo import SpikeTrain
        import quantities as pq
    except ImportError:
        print("Elephant not available")
        return {}
    
    neo_trains = []
    for ch_id, spikes in spike_trains.items():
        if len(spikes) > 0:
            st = SpikeTrain(
                times=spikes * pq.s,
                t_stop=max(spikes) * pq.s if len(spikes) > 0 else 0 * pq.s
            )
            neo_trains.append((ch_id, st))
    
    results = {}
    for i, (ch1, st1) in enumerate(neo_trains):
        for j, (ch2, st2) in enumerate(neo_trains[i+1:], i+1):
            cch = cross_correlation_histogram(
                st1, st2,
                bin_size=bin_size_ms * pq.ms,
                max_lag=max_lag_ms * pq.ms
            )
            results[f"{ch1}_{ch2}"] = {
                'bin_edges': cch[1].magnitude,
                'counts': cch[0].magnitude,
                'peak_correlation': float(np.max(cch[0].magnitude)),
                'peak_lag_ms': float(cch[1][np.argmax(cch[0].magnitude)].magnitude)
            }
    
    return results


def elephant_change_point_detection(spike_trains, window_size=10000):
    """
    Detect state transitions using Elephant change point detection.
    REUSES: Elephant change_point_detection
    """
    try:
        from elephant.change_point_detection import change_point_detection
        from neo import SpikeTrain
        import quantities as pq
    except ImportError:
        print("Elephant change_point_detection not available")
        return {}
    
    results = {}
    for ch_id, spikes in spike_trains.items():
        if len(spikes) > 100:
            st = SpikeTrain(
                times=spikes * pq.s,
                t_stop=max(spikes) * pq.s
            )
            # Bin spike train
            binned = st.bin(window_size=window_size * pq.ms)
            # Change point detection
            cps = change_point_detection(binned)
            results[ch_id] = [float(cp) for cp in cps]
    
    return results


def elephant_synchrony_measures(spike_trains):
    """
    Compute synchrony measures (ISI-distance, SPIKE-distance).
    REUSES: Elephant synchrony
    """
    try:
        from elephant.spike_train_dissimilarity import isi_distance, spike_distance
        from neo import SpikeTrain
        import quantities as pq
    except ImportError:
        return {}
    
    neo_trains = []
    for ch_id, spikes in spike_trains.items():
        if len(spikes) > 0:
            st = SpikeTrain(
                times=spikes * pq.s,
                t_stop=max(spikes) * pq.s
            )
            neo_trains.append((ch_id, st))
    
    if len(neo_trains) < 2:
        return {}
    
    # Average pairwise ISI distance (lower = more synchronous)
    isi_dists = []
    spike_dists = []
    
    for i, (ch1, st1) in enumerate(neo_trains):
        for j, (ch2, st2) in enumerate(neo_trains[i+1:], i+1):
            isi_d = isi_distance(st1, st2)
            spike_d = spike_distance(st1, st2)
            isi_dists.append(float(np.mean(isi_d)))
            spike_dists.append(float(np.mean(spike_d)))
    
    return {
        'mean_isi_distance': np.mean(isi_dists) if isi_dists else None,
        'mean_spike_distance': np.mean(spike_dists) if spike_dists else None,
        'pairwise_isi': isi_dists,
        'pairwise_spike': spike_dists
    }


# ============================================================
# PIPELINE 4: DANDI/NWB Streaming Access
# ============================================================

def stream_dandi_nwb(dandiset_id: str, asset_id: Optional[str] = None, 
                      max_files: int = 5) -> List[Dict]:
    """
    Stream NWB files from DANDI archive.
    REUSES: dandi CLI / Python API, PyNWB
    """
    try:
        from dandi.dandiapi import DandiAPIClient
        from pynwb import NWBHDF5IO
    except ImportError:
        print("Install: pip install dandi pynwb")
        return []
    
    results = []
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id, 'draft')
        assets = list(dandiset.get_assets())
        
        if asset_id:
            assets = [a for a in assets if a.identifier == asset_id]
        
        for asset in assets[:max_files]:
            try:
                # Stream the file
                with asset.download() as f:
                    with NWBHDF5IO(f, mode='r', load_namespaces=True) as io:
                        nwbfile = io.read()
                        
                        # Extract basic info
                        info = {
                            'asset_id': asset.identifier,
                            'path': asset.path,
                            'session_id': nwbfile.session_id,
                            'subject_id': nwbfile.subject.subject_id if nwbfile.subject else None,
                            'electrodes': nwbfile.electrodes.to_dataframe() if nwbfile.electrodes else None,
                            'units': len(nwbfile.units) if nwbfile.units else 0,
                            'stimuli': list(nwbfile.stimulus.keys()) if nwbfile.stimulus else [],
                            'acquisition': list(nwbfile.acquisition.keys()),
                            'processing': list(nwbfile.processing.keys())
                        }
                        results.append(info)
            except Exception as e:
                results.append({'asset_id': asset.identifier, 'error': str(e)})
    
    return results


# ============================================================
# PIPELINE 5: Investigation Machine Integration Helpers
# ============================================================

def run_investigation_on_nwb(nwb_path: str, output_dir: str = "./investigation_output") -> Dict:
    """
    Run full Investigation Machine pipeline on NWB file.
    INTEGRATES: cortical_cloud_bridge + investigation_machine + Elephant/SpikeInterface
    """
    # This would be the main entry point
    # For now, return a template
    return {
        "nwb_path": nwb_path,
        "output_dir": output_dir,
        "status": "TEMPLATE - implement integration",
        "steps": [
            "1. Load NWB with PyNWB",
            "2. Extract spikes/stims to cortical_cloud_bridge format",
            "3. Run cortical_cloud_bridge characterization",
            "4. Run investigation_machine full pipeline",
            "5. Save results with provenance"
        ]
    }


# ============================================================
# PIPELINE 6: Cortical Simulator Experiment Runner
# ============================================================

def run_cortical_simulator_experiment(config: Dict, output_h5: str) -> bool:
    """
    Run experiment on CL Simulator with given configuration.
    REUSES: cl SDK, cortical_oi_integration
    """
    try:
        import cl
        from cortical_oi_integration import CorticalOIController, CorticalIntegrationConfig
    except ImportError:
        print("CL SDK or cortical_oi_integration not available")
        return False
    
    # Create config
    cortical_config = CorticalIntegrationConfig(
        ticks_per_second=config.get('ticks_per_second', 500),
        stop_after_seconds=config.get('stop_after_seconds', 30.0),
        burst_min_spikes=config.get('burst_min_spikes', 3),
        burst_max_isi_ms=config.get('burst_max_isi_ms', 15.0),
        prediction_window_ms=config.get('prediction_window_ms', 50.0),
        output_dir=Path(output_h5).parent,
        recording_suffix=Path(output_h5).stem
    )
    
    # Run experiment
    controller = CorticalOIController(cortical_config)
    controller.run_integration_experiment(output_h5)
    
    return True


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reusable Analysis Pipelines")
    parser.add_argument("--convert-to-nwb", help="Convert Cortical HDF5 to NWB")
    parser.add_argument("--output", help="Output path")
    parser.add_argument("--stream-dandi", help="Stream DANDI dandiset")
    
    args = parser.parse_args()
    
    if args.convert_to_nwb and args.output:
        convert_cortical_hdf5_to_nwb(args.convert_to_nwb, args.output)
    elif args.stream_dandi:
        results = stream_dandi_nwb(args.stream_dandi)
        for r in results:
            print(json.dumps(r, indent=2))
