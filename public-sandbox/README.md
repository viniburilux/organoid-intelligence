# OI Sandbox — public edition

The OI Sandbox is a computational laboratory for testing closed-loop experiment interfaces in a synthetic environment.

Its public edition exposes the idea and the evidence boundary, not the private laboratory machinery. The core loop is:

```text
stimulus / action
      ↓
synthetic neural response
      ↓
observation / state
      ↓
transition memory
      ↓
objective and metrics
      ↓
next action
```

> **Synthetic control is not biological evidence.**

## What the sandbox can test

The sandbox can test whether a controller can execute a declared computational loop, preserve seeds, respond to perturbations, compare policies, retain transition information and produce metrics with explicit uncertainty.

The public record includes four conceptual stages:

| Stage | Public meaning |
|---|---|
| M1 | Closed-loop synthetic substrate with action, response, state and transition memory |
| M2 | Goal-directed control with perturbation and transfer phases |
| M2-D | Adversarial scenarios and component ablations |
| M2-E | An attempt to separate history access from the information needed for action selection |

## What M2-E showed

M2-E compared random, fixed, current-state-only, several adaptive history windows and an oracle in a synthetic two-dimensional task. It used eight scenarios, nine conditions, 64 seeds per scenario-condition cell and 4,608 trajectories.

The `current_state_only` condition differed from random by `+0.453` in `success_post`, with a paired bootstrap 95% interval of `[+0.274, +0.664]`. This repaired a specific M2-D confound: a no-history selector can still behave differently from random if it retains information that differentiates actions.

The result does **not** isolate a pure causal effect of history. The no-history policy used a fixed nominal model, while adaptive policies estimated transition models from recent samples. The comparison therefore changes both history access and policy class. The experiment remains an informative computational result with an explicit identifiability limit.

## Public contract example

The smallest public representation of a run can be expressed as:

```yaml
substrate: synthetic-2d
objective: reach-target-after-perturbation
policy: current-state-only
memory: none
perturbation: regime-change-with-state-retention
seeds: declared-and-paired
metrics:
  - success_post
  - recovery
  - transfer
status: computational-demonstration
biological_claim: false
```

This example is intentionally declarative. It demonstrates the boundary between a research protocol and an operational execution environment.

## What the sandbox does not claim

The sandbox does not establish intelligence, consciousness, biological learning, biological memory, organoid equivalence, generalization to living tissue or a universal benchmark. It is a way to make computational assumptions visible and testable before connecting to more complex substrates.

## What remains open

A cleaner memory experiment would use one shared action-scoring architecture and manipulate only access to a bounded transition buffer while holding current-state information, target, exploration and model class constant. That is a design opportunity, not a completed result.

## Related pages

Read the [findings](../evidence/findings.md), [limitations](../docs/limitations.md), [timeline](../docs/timeline.md) and [research map](../docs/research-map.md).
