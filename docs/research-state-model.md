# Public research-state model

A research program becomes easier to trust when it preserves not only conclusions, but also uncertainty, contradiction and the next question. The private laboratory implements a richer operational state system. This page publishes only the conceptual model.

## The public objects

| Object | Question it answers |
|---|---|
| **Knowledge** | What does the current record support? |
| **Question** | What remains unresolved or blocked? |
| **Hypothesis** | What falsifiable explanation or expectation is being carried forward? |
| **Evidence** | Which source or analysis supports the statement? |
| **Contradiction** | Which observations do not yet fit together? |
| **Unknown** | Which missing fact prevents a stronger conclusion? |
| **Frontier** | Which next move would most reduce uncertainty? |
| **Status** | Is the item supported, partial, open, blocked, rejected or unverified? |

## Minimal public record

```yaml
id: public-example-001
question: "Can recent neural structure predict the next observed neural state?"
hypothesis: "Simple temporal features may add information beyond population-rate lags."
evidence:
  - "Leakage-aware next-window prediction"
  - "Time-blocked evaluation"
status: qualified_positive
contradiction: "File-level uniqueness did not guarantee targeted-payload independence."
unknown: "Which upstream conversion or curation process produced the equal arrays?"
next_move: "Reconcile source provenance before making independence claims."
```

## Why this matters

The state model prevents a negative result from disappearing, a hypothesis from becoming a fact by repetition or a contradiction from being smoothed away in a later summary. It also makes it possible to resume a research program from the last defensible frontier rather than from memory alone.

## Privacy boundary

The public model does not expose the private ASIE queue, internal scoring, cycle logs, resource budgets, prompts, credentials, hidden hypotheses or operational state transitions. It is a conceptual and educational interface for evidence-aware research.

## Related pages

Read the [research map](research-map.md), [evidence policy](evidence-policy.md), [timeline](timeline.md) and [limitations](limitations.md).
