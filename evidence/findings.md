# Findings

The public record is organized around a simple question:

> **What did the evidence allow us to conclude — and what did it refuse to let us say?**

The findings below are deliberately narrow. They describe the tested data, task and computational protocol. They are not claims about Organoid Intelligence as a whole.

## Finding 01 — Aggregate representations did not beat simple baselines

The first predictive experiment asked whether simple neural summaries could predict an explicit experiment-level performance variable from the public goal-directed-learning artifact. The analysis used 32 complete experiments from 16 organoids and five-fold `GroupKFold` splits held out by organoid. The median and mean baselines were compared with firing-rate and network/connectivity summaries.

| Model | MAE | RMSE | Interpretation |
|---|---:|---:|---|
| Median baseline | **24.24** | **55.87** | Best typical error in the tested setup |
| Mean baseline | 30.53 | 55.93 | Simple reference |
| Network summary | 46.93 | 70.05 | Worse than both simple baselines |
| Firing-rate summary | 53.05 | 83.02 | Positive rank signal, poor calibrated prediction |

The firing-rate model produced a descriptive Spearman association of `rho = 0.359` with an empirical permutation value of `p = 0.018`, but its predictive errors were worse than both baselines and its R² was negative. The appropriate conclusion is therefore not that neural activity contains no information. It is that these aggregate summaries, this target, this sample and this estimator did not produce better calibrated out-of-fold predictions.

**What this ruled out:** treating a small rank association as evidence of a useful performance decoder.
**What remains open:** richer temporal representations, better-specified targets and independent data with aligned labels.

The experiment used processed data derived from a public Zenodo record associated with the 2026 goal-directed-learning paper.[1] [2]

## Finding 02 — Temporal structure carried incremental predictive information

The lack of aligned labels changed the task. Instead of manufacturing a condition classifier, the investigation moved to a label-free next-window prediction problem: predict the population firing rate in the next 100 ms from the recent history of a session.

Simple burst/backbone state features were derived strictly from the training portion of each session. Under time-blocked evaluation with a five-window gap, the combined representation improved over population-rate lags alone in the pooled test.

| Model | MAE (Hz) | RMSE (Hz) | R² |
|---|---:|---:|---:|
| Ridge, rate only | 35.945 | 114.939 | 0.346 |
| Ridge, burst/backbone only | 34.866 | 107.053 | 0.433 |
| **Ridge, combined** | **33.263** | **104.054** | **0.464** |

The direction was reproduced on HO2, HO3 and a digest-distinct HO4 asset. In the three-session synthesis, the combined representation improved MAE, RMSE and R² relative to rate-only in each tested session. This is a **qualified label-free predictive result**.

> **The strongest defensible wording is:** simple temporal features provided incremental short-horizon predictive information in the tested sessions.

**What this does not show:** learning, biological memory, intelligence, condition decoding, performance decoding, cross-organoid transfer or a biological mechanism. The target is another neural activity statistic, not a biological condition or behavioral performance label.

The temporal data branch was built from open NWB material in DANDI:001603.[3]

## Finding 03 — Replication exposed a provenance problem

The attempt to examine repeated assets revealed a distinction between file-level uniqueness and representation-level independence. Selected pairs had different whole-file SHA-256 values, but the audited neural arrays were exactly equal, including `spike_times`, ragged indices and `t_spk_mat`. Fresh PyNWB, direct `h5py` access and a second minimal analysis agreed with the equality.

The remaining whole-file differences were localized to six metadata datasets and related attributes, including keywords, file creation date, experimenter, related publications, session start time and timestamp reference time.

| Level | Observed result | What it supports | What it does not support |
|---|---|---|---|
| Whole file | Different digests | Files are byte-distinct | Neural recordings are independent |
| Targeted neural arrays | Exact equality in inspected pairs | Representation-level equality | Biological stability |
| Metadata and object identity | Localized differences | Curation/header/provenance transformation is plausible | The upstream cause is resolved |

The correct interpretation is a **provenance contradiction**, not a biological stability result. The remaining question is how the upstream source or conversion process produced equal neural payloads with session-specific metadata differences.

**What changed:** the replication branch stopped being a simple confirmation exercise and became a source-lineage investigation.

The public archive’s asset catalog and source context are available through DANDI and the associated publication record.[3] [4]

## Finding 04 — The experiment changed the question

The original plan was tempted by condition or performance decoding. The data did not support that cleanly: the public metadata and inspected NWB objects did not expose an aligned condition or performance label for the neural windows. Subject identity and file naming cannot be used as substitutes for an experimental label.

The investigation therefore pivoted to a label-free question:

> **Can recent neural structure predict the next observed neural state without inventing labels?**

This pivot is not a retreat from the scientific question. It is the scientific result of respecting the data boundary. The dataset determines which claim is testable; the investigator does not get to manufacture the missing variable.

**What this changed:** the project moved from a potentially overinterpreted supervised task to an executable temporal task with explicit leakage controls and narrower conclusions.

## Why these findings matter together

Taken separately, each result is modest. Taken together, they form a useful research record:

1. Aggregate summaries did not provide a robust shortcut to experiment-level performance prediction.
2. Temporal structure added a narrow predictive signal when the task was aligned with the data actually available.
3. Replication forced a provenance audit instead of allowing file-level uniqueness to stand in for biological independence.
4. The research question changed because the evidence boundary changed.

This is not a finished theory of organoid intelligence. It is a demonstration of how a research program can become more precise by allowing negative results, missing labels and contradictions to change the next move.

## Status of this record

These findings are public summaries of bounded computational investigations. They should be read together with [What we ruled out](what-we-ruled-out.md), [What we cannot claim](../docs/limitations.md), the [research map](../docs/research-map.md) and the [source register](sources.md).

## References

[1]: https://doi.org/10.1016/j.celrep.2026.116984 "Goal-directed learning in cortical organoids"
[2]: https://zenodo.org/records/17684862 "Goal-Directed Learning in Cortical Organoids — Experimental Data and Code"
[3]: https://dandiarchive.org/dandiset/001603/draft "DANDI:001603 — public draft dataset record"
[4]: https://github.com/braingeneers/Protosequences "Protosequences source repository"
