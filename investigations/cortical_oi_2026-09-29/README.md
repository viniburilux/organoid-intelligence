# Cortical-OI Integration Investigation (2026-09-29)

This investigation explores the integration between Cortical Labs' CL SDK/Simulator 
and the Organoid Intelligence (OI) investigation infrastructure.

## Structure

- `scripts/` - Reproducible experiment code
- `archaeology/` - Prior art and opportunity matrix
- `experiments/` - Executed experiments with results
- `results/` - Summary outputs

## Experiments Executed (on CL Simulator)

### 1. Bayesian Optimization of Burst Suppression ✅
- **Objective**: Find stimulation parameters that minimize burst rate
- **Result**: 34.7% reduction (4.9 → 3.2 bursts/s)
- **Status**: Hypothesis supported
- **Key file**: `experiments/bo_burst_suppression/bo_state.json`
- **Recording**: `experiments/bo_burst_suppression/best_run.h5`

### 2. Burst-STDP Protocol (±10ms timing) ❌
- **Objective**: Test if spike-timing-dependent plasticity changes burst probability
- **Result**: All 3 hypotheses FALSIFIED
- **Status**: Simulator limitation confirmed (Poisson process has no plasticity)
- **Key file**: `experiments/burst_stdp/complete_results.json`
- **Recording**: `experiments/burst_stdp/control.h5`

### 3. Adaptive Feature-Based Stimulation ⚠️
- **Objective**: Test if burst-feature-scaled stimulation causes lasting plasticity
- **Result**: Marginal change (Δ -0.10 bursts/s)
- **Status**: Marginal; simulator lacks multi-channel network structure
- **Key file**: `experiments/adaptive_feature_stim/complete_results.json`
- **Recording**: `experiments/adaptive_feature_stim/run.h5`

## Key Findings

1. **BO optimization works** on the CL Simulator (parameter search valid)
2. **Simulator has no plasticity mechanisms** - Poisson process only
3. **Simulator has no multi-channel network structure** - single-channel bursts only
4. **Infrastructure validated** for closed-loop experimentation
5. **Real Cortical Cloud data required** for biological validation

## Reproducibility

All experiments run on Cortical Labs CL SDK Simulator (available via `pip install cl-sdk`).

```bash
pip install cl-sdk
python scripts/bo_burst_suppression.py
python scripts/burst_stdp_experiment.py
python scripts/adaptive_feature_experiment.py
```

## Next Steps

Access to Cortical Cloud real recordings for biological validation.

---

**Private Research Record**: Complete archaeological data, all HDF5 recordings, 
intermediate results, and subagent outputs are in the private repository.

**LuxMemory Links**: 
- Discovery: `cortical_oi_discovery_memory_link.json`
- Investigation: `cortical_oi_investigation_discovery_link.json`  
- Complete: `cortical_oi_complete_investigation_link.json`
