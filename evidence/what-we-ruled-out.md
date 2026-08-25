# What we ruled out

A credible research record is not a collection of favorable outcomes. It also records the interpretations that were tested, weakened or rejected.

## Aggregate summaries are not a reliable performance shortcut

Firing-rate and network/connectivity summaries did not beat simple baselines for experiment-level performance prediction under organoid-held-out evaluation. The firing-rate model showed a rank association, but its calibrated predictive error was worse. The result does not support presenting aggregate activity summaries as a validated performance decoder.

## A missing label is not permission to invent one

The available DANDI metadata, sidecars and inspected NWB structures did not provide a condition or performance label aligned to the neural windows. Subject identity, timestamps and file names are not substitutes for an experimental label. The condition-supervised branch is therefore blocked in its current form.

## File-level uniqueness is not biological independence

Different SHA-256 values establish that files are byte-distinct. They do not establish independent recordings, independent neural content or longitudinal biological stability. In selected repeated pairs, the target neural arrays were exactly equal even though whole-file digests differed. Provenance must be resolved before such assets support an independence claim.

## A short-horizon predictor is not a learning system

Predicting the next neural activity window is a label-free computational task. A model that improves that prediction does not, by itself, demonstrate learning, memory, intelligence, consciousness or biological plasticity.

## Synthetic control is not organoid evidence

The OI Sandbox validates computational interfaces, trajectories, seeds, metrics, perturbations and policy comparisons in a synthetic environment. Its M2-E experiment separated a no-history information condition from random selection operationally, but it did not isolate a pure causal effect of memory. The Sandbox does not establish equivalence to living tissue.

## M2-E does not prove that more memory is better

The adaptive-window curve showed a descriptive increase across tested windows, but adjacent paired intervals did not establish a monotonic dose-response. The `current_state_only` and adaptive policies also used different model classes. The remaining claim is bounded to an operational policy comparison, not a general theory of biological or computational memory.

## The project is not a universal OI benchmark

The public record does not claim that a universal Organoid Intelligence benchmark already exists, nor that this repository is the first such benchmark. A versioned benchmark would require a task suite, shared execution contract, multiple validated substrates, fixed baselines, statistical rules and independent reproducibility.

## What remains after the exclusions

These exclusions do not make the project empty. They leave a narrower and more defensible record: a negative aggregate result, a qualified temporal signal, a provenance contradiction, an evidence-driven task pivot, a public model for research-state reasoning and a synthetic closed-loop laboratory whose limits are explicit.

## Related pages

Read the [findings](findings.md), [limitations](../docs/limitations.md), [timeline](../docs/timeline.md) and [research map](../docs/research-map.md).
