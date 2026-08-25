# Organoid Intelligence

> **Investigated without shortcuts.**

An open research record exploring what evidence can — and cannot — support about learning, prediction, memory and intelligence in biological neural systems.

Organoid Intelligence is a field with extraordinary demonstrations, serious open questions and a high risk of interpretive overreach. This repository does not present a finished theory, a universal benchmark or a claim that synthetic control is biological intelligence. It records an evidence-driven investigation: what was tested, what failed, what survived, what contradicted the first interpretation and how the question changed when the data required it.

## What did the evidence allow us to conclude?

Four findings organize the public record:

| Finding | Result | Status |
|---|---|---|
| **01 — Aggregate representations** | Firing-rate and network summaries did not beat simple baselines for experiment-level performance prediction under organoid-held-out splits. | Negative result, qualified |
| **02 — Temporal structure** | Simple burst/backbone features added short-horizon predictive information beyond population-rate lags in the tested sessions. | Positive direction, bounded |
| **03 — Provenance** | Files with different whole-file digests contained exactly equal targeted neural arrays in selected repeated pairs. | Provenance contradiction |
| **04 — The question changed** | The absence of aligned condition labels forced a shift from supervised decoding to label-free temporal prediction. | Methodological pivot |

Read the [full findings record](evidence/findings.md) or enter through the [public research map](docs/research-map.md).

## What this project demonstrates today

The current public record demonstrates controlled computational experiments, leakage-aware evaluation, a narrow label-free temporal signal, replication attempts, provenance auditing, contradiction handling and a persistent research-state model presented here only as a public concept.

It does **not** currently demonstrate intelligence, consciousness, biological memory, general learning, decoding of experimental condition, independent biological longitudinal stability or equivalence between synthetic agents and organoids.

> **Synthetic control is not biological evidence.**

## Research, not a sanitized laboratory

This repository is intentionally built from scratch as a public record. It is not a mirror of the private laboratory `OI-Organoids-Intelligence`.

The public repository contains curated findings, interpretable summaries, source links, public-method descriptions, small synthetic examples and a public edition of the OI Sandbox. It does not contain operational ASIE state, private frontier decisions, raw or restricted data, acquisition credentials, unpublished experiment machinery, intermediate laboratory artifacts or the complete internal execution environment.

The private laboratory remains the place where the machine works. This repository is the place where the scientific record can be read.

## Explore the record

| Section | What you will find |
|---|---|
| [Findings](evidence/findings.md) | Four central discoveries, their evidence and their boundaries |
| [What we ruled out](evidence/what-we-ruled-out.md) | Results and interpretations the investigation does not carry forward |
| [What we cannot claim](docs/limitations.md) | A deliberately explicit claim boundary |
| [Research timeline](docs/timeline.md) | How each result changed the next question |
| [Research map](docs/research-map.md) | Investigation, result, status and next question in one view |
| [Public Sandbox](public-sandbox/README.md) | The synthetic closed-loop edition and its limits |
| [Evidence policy](docs/evidence-policy.md) | How public claims, sources and provenance are handled |

## The public research question

> **Can we investigate Organoid Intelligence without confusing evidence with hype?**

The answer is not a single score. It is a record of boundaries. A negative result can remove a tempting shortcut. A failed label branch can reveal what the data actually supports. A replication attempt can expose a provenance problem. A synthetic experiment can validate an interface without validating a biological interpretation.

## Current status

This is a **public research record**, not a completed benchmark release and not a biological claim. Several findings remain qualified and were produced under bounded datasets, tasks and computational protocols. The current public record is designed to be auditable and honest about those boundaries.

The private laboratory currently contains a richer operational state and additional artifacts. Their absence here is deliberate.

## Citation and sources

The record is grounded in public papers, archives and source repositories. Start with the [source register](evidence/sources.md), which links each public claim to its primary or official origin.

## License

Original documentation, public summaries, schemas and small examples are released under the [MIT License](LICENSE), unless a file states otherwise. Third-party papers, datasets, code, trademarks and source artifacts retain their own licenses and are not relicensed by this repository.

## Repository status

**Version:** public record v0.1
**Scope:** evidence, findings, limitations, timeline, research map and public synthetic sandbox
**Private boundary:** operational ASIE, internal state, raw/restricted data and unpublished laboratory machinery remain outside this repository
