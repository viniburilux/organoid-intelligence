# Complexity-index validation on public human data (2026-10-03)

Exploratory validation of EEG complexity indices (PCIst, Lempel-Ziv) on public human datasets, following a protocol suggested by Andrea Lavazza. This is a validation exercise for the measures, not a claim about organoids and not a classification of consciousness.

## What was tested
- **Farnes et al. (ketamine)**, Dryad doi:10.5061/dryad.j9kd51c9q (CC0; mirror Zenodo 4245091). 10 subjects, wake vs ketamine, preprocessed TMS-EEG and spontaneous EEG.
- **Bajwa et al. (propofol)**, OpenNeuro ds005620 v1.0.0 (README says CC-BY-4.0, OpenNeuro metadata says CC0; treated as CC-BY). 20 analysed subjects; only a 10-subject slice was used.
- Protocol and split were written before measuring (`PROTOCOL.md`). Parameters were fixed to published defaults.

## Results (short)
- Farnes, evoked PCIst, ketamine minus wake: mean delta +0.67 (95% bootstrap CI -5.8 to +6.9), 7/10 up, Wilcoxon p=0.85. Held-out 5 subjects: +1.39 (CI -11.1 to 12.2). Robust to windows, SNR, k, channel subsets, trial counts. Consistent with the paper (evoked PCI did not differ).
- Farnes, spontaneous Lempel-Ziv: higher under ketamine with eyes closed (median binarisation +0.028, CI 0.013-0.043, 9/10 up; amplitude binarisation +0.050, 10/10 up). Eyes open with median binarisation: no effect. Held-out n=5 has direction but wide CIs. No multiple-comparison correction.
- Bajwa slice, awake vs sedation LZ: attempt 1 (first 200 s of sedation rest) showed no drop (-0.019, CI -0.051 to +0.009); this window probably includes light sedation. Attempt 2 (200 s ending 60 s before the end of the sedation rest recording, same subjects and metric, declared in `PROTOCOL.md` after attempt 1): delta -0.019 (CI -0.051 to +0.011), 6/10 down, p=0.32; held-out -0.041, 4/5 down. Still no clear drop. Both attempts use minimal preprocessing and a 1-in-3 channel subset, so this neither reproduces nor refutes the published decrease.

## Limits
- n=10 allows exploratory analysis only. A non-significant result is not equivalence; confidence intervals are wide.
- Data are preprocessed, so preprocessing cannot be stress-tested.
- LZ here is a plain LZ76 implementation, not the exact published pipeline. Absolute values are not comparable with the papers.
- Experience vs no-experience reports (Bajwa) are not tested: per-awakening labels were not found in the BIDS files or the authors' repository.
- No human threshold is transferred to organoids. Nothing here classifies consciousness.

## Files
`PROTOCOL.md` (pre-registered protocol and addenda), `run.py` (PCIst), `lz.py` (spontaneous LZ), `bajwa_lz.py` and `bajwa_lz_attempt2.py` (Bajwa slice), `results.json`, `lz_results.json`, `bajwa_results.json`, `bajwa_attempt2_results.json` (aggregates, rounded to 4 decimals).

## Code and licences
PCIst: Comolatti et al. 2019, https://github.com/renzocom/PCIst, commit ed7d853 (GPL-3.0). It is imported, not copied. Scripts here are original. Raw data are not included.

Scripts use absolute /tmp paths from the original run (data under /tmp/f and /tmp/w/bajwa); adjust before rerunning.
