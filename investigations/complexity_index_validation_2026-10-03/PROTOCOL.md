# Protocol (written 2026-10-03 before any PCIst value was computed)
Data: Farnes et al. Dryad 10.5061/dryad.j9kd51c9q (CC0), TMS-EEG evoked, n=10, rec 31=wake, 32=ketamine (open-label, within-subject).
Code: renzocom/PCIst commit ed7d853 (GPL-3.0), published TMS defaults: baseline (-400,-50) ms, response (0,300), k=1.2, min_snr=1.1, max_var=99, n_steps=100.
Split by whole subject, deterministic: sort IDs; discovery = even positions (0,2,4,6,8), held-out = odd (1,3,5,7,9).
Parameters are FIXED to published defaults; nothing is tuned on any subject. Discovery subjects are used only to choose which stress tests to report; held-out subjects get only the pre-set defaults.
Primary readout: within-subject delta PCIst (ketamine - wake), paired Wilcoxon, effect size, and per-subject direction. n=5/5 split is underpowered: this is exploratory, not definitive validation. LOSO also reported as exploratory.
Stress tests (only what preprocessed data allows): baseline window, response window, min_snr, max_var, channel subsets (random 50%), trial subsampling (to min count), k.
Not claimed: no consciousness classification, no human threshold applied to organoids, non-significant != equivalent (report CI of paired difference).

## Addendum (before spontaneous LZ computed)
Spontaneous: per-file epochs (EEGLAB, preprocessed, after ICA). Files sorted by recording number: first two = wake, last two = ketamine; eyes open/closed from filename. Same subject split. Metric: Lempel-Ziv complexity (LZ76) per channel on signal binarised at the median of the analytic amplitude... fixed: binarise raw signal by median of the epoch/channel (primary), normalised by LZ of the time-shuffled sequence; averaged over channels then epochs. Secondary: analytic-amplitude binarisation. Delta ket-wake per subject, per eye condition, Wilcoxon + bootstrap CI. No tuning.

## Bajwa ds005620 addendum (written before download/measurement)
Source: OpenNeuro ds005620 v1.0.0 (README says CC-BY-4.0, OpenNeuro metadata says CC0 - treat as CC-BY). 20 analysed (sub-1037 excluded in participants.tsv).
Recorte: sorted analysed IDs, every 2nd (idx 0,2,4..): 1010,1017,1024,1036,1046,1055,1060,1062,1067,1071. Split alternating: discovery 1010,1024,1046,1060,1067; held-out 1017,1036,1055,1062,1071.
Contrast: awake eyes-closed rest vs sedation rest run-1 (labelled by awakening order, not by report). Metric: single-channel-style LZc as in Farnes (median binarisation, normalised by shuffle), 0.5-40 Hz, resampled to 250 Hz, 8-s epochs (2000 samples), first 20 epochs, mean over channels subset EEG-only. Paired within subject: sedation - awake; expect decrease (published). Experience vs no-experience: NOT tested - per-awakening labels are not in BIDS events nor in the authors' repo.
Bajwa second attempt (declared after attempt 1 showed no awake>sedation drop; same split, same metric): sedation window = the 200 s ending 60 s before the end of sed rest run-1 (to approximate the paper's window ending 1 min before awakening); awake window unchanged except awake crop is also its last 200 s ending 60 s before end. Attempt 1 results remain reported.

## Farnes LZ stress tests (declared before running, 2026-10-03 ~14:30)
Same files/split/metric as primary. Variants: (a) binarisation by mean instead of median; (b) odd-index channels instead of even; (c) first 8 epochs only; (d) unnormalised LZ (raw complexity count). Report delta ket-wake per eye condition, n, CI, direction. No tuning of the primary.
