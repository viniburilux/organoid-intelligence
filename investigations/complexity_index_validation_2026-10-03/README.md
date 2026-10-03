# Complexity-index validation on public human data (2026-10-03)

Status: exploratory, n=10 per dataset. Not a claim about organoids, not a classification of consciousness.

## 1. The question (Andrea Lavazza)
Can the pipeline be extended from organoid data to a consciousness index? Proposed answer: treat it as a validation protocol for candidate indices, report an evidence profile (not conscious / non-conscious), start with a perturbational measure (PCI/PCIst) on independently characterised states in healthy subjects (wake, NREM, anaesthesia, ketamine as a dissociation test), control confounders (firing level, SNR/amplitude, active channels, perturbation intensity), and do not transfer a human threshold to organoids. He suggested public datasets for a first exercise: Farnes (ketamine) and Bajwa (propofol).

## 2. Infrastructure reused
- PCIst: Comolatti et al. 2019, https://github.com/renzocom/PCIst, commit ed7d853, GPL-3.0. Imported, not copied.
- Pre-registered protocol and subject-level split written before measuring (`PROTOCOL.md`), in the style of this repository's leakage-aware, held-out evaluation (see Finding 01).
- Authors' public pipeline for Bajwa (SugarLab/Anesthesia_PCI_Cont: EOG regression, AutoReject, ICA with ICLabel, pyconscious LZc, PCIst). Read, not yet run end to end.
- Data: Farnes et al., Dryad doi:10.5061/dryad.j9kd51c9q (CC0, mirror Zenodo 4245091); Bajwa et al., OpenNeuro ds005620 v1.0.0 (README says CC-BY-4.0, metadata says CC0; treated as CC-BY). Raw data are not included here.

## 3. New results
Farnes, evoked TMS-EEG, PCIst, ketamine minus wake (`results.json`):
- Mean delta +0.67 (95% bootstrap CI -5.8 to +6.9), 7/10 up, Wilcoxon p=0.85. Held-out 5 subjects: +1.39 (CI -11.1 to +12.2). Stable across windows, SNR, k, channel subsets and trial counts. Consistent with the paper (evoked PCI did not differ). Not equivalence: the CI is wide.

Farnes, spontaneous EEG, Lempel-Ziv (`lz_results.json`, `lz_stress_results.json`):
- Eyes closed: higher under ketamine. Median binarisation +0.028 (CI 0.013 to 0.043), 9/10 up, p=0.010; amplitude binarisation +0.050, 10/10 up. Stress variants (mean binarisation, odd channels, first 8 epochs) give the same direction: +0.024 to +0.028, 9/10 up, p 0.014 to 0.020; the unnormalised count also goes up (9/10, p=0.010) on its own scale. Held-out 5 subjects: direction kept, CIs include zero for the median variants.
- Eyes open, median binarisation: no effect (+0.004, CI -0.012 to 0.017), also across all stress variants. The effect depends on condition.
- No multiple-comparison correction.

Bajwa, 10 of 20 subjects, awake vs sedation LZ (`bajwa_results.json`, `bajwa_attempt2_results.json`):
- Attempt 1 (first 200 s of sedation rest): -0.019 (CI -0.051 to +0.009), 5/10 down. Attempt 2 (200 s ending 60 s before the end of the recording; declared in `PROTOCOL.md` after attempt 1): -0.019 (CI -0.051 to +0.011), 6/10 down, held-out -0.041, 4/5 down. No clear drop. Minimal preprocessing and 1-in-3 channels, so this neither reproduces nor refutes the published decrease.

Limits: n=10 allows exploratory analysis only; a non-significant result is not equivalence; Farnes data are preprocessed so preprocessing cannot be stress-tested; the LZ here is a plain LZ76 implementation, not the published pipeline, so absolute values are not comparable. Experience vs no-experience (Bajwa: 24 / 5 / 23 awakenings) is untested: per-awakening labels are not in the BIDS files or the authors' repository (their plotting script reads a local pcist.xlsx).

## 4. What this could open later
- Run the authors' pipeline on the Bajwa BIDS data (awake vs sedation, then TMS-EEG PCIst).
- Obtain per-awakening labels to separate experience, no experience and indeterminate. Contact with the authors is the owner's decision and has not happened.
- Only after a measure is characterised in humans: ask what, if anything, can be said about organoids, without transferring a human threshold.

## Files
`PROTOCOL.md` (protocol and addenda), `run.py` (PCIst), `lz.py`, `lz_stress.py` (spontaneous LZ), `bajwa_lz.py`, `bajwa_lz_attempt2.py`, and the aggregate `*_results.json` files (rounded to 4 decimals). Scripts use absolute /tmp paths from the original run; adjust before rerunning.
