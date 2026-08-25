# Public boundary

This repository is intentionally public. It is a research record, not a mirror of the private OI laboratory.

## Public by design

The public repository may contain:

- findings that can be stated without exposing operational machinery;
- aggregate metrics and bounded computational results;
- public papers, dataset records and official source links;
- conceptual descriptions of the research-state model;
- a small declarative example of the synthetic Sandbox;
- limitations, contradictions and methodological pivots;
- documentation, schemas and examples authored for this public record.

## Private by design

The following must remain in the private laboratory:

- operational ASIE code, state, frontier, cycles and internal scoring;
- private prompts, orchestration and agent-specific execution details;
- raw or restricted biological data, credentials, tokens and acquisition paths;
- unpublished experiment runners, intermediate artifacts and local caches;
- full internal traces, seed ledgers or artifacts that reconstruct the private workflow;
- strategic decisions or hypotheses whose disclosure would expose the laboratory’s research position;
- third-party material that cannot be redistributed under a compatible license.

## Review before every publication

Before opening a pull request or pushing an update, ask:

1. Does this file expose a secret, credential, raw asset or private operational path?
2. Does it allow a reader to reconstruct the private ASIE workflow?
3. Does it make a stronger scientific claim than its source and task support?
4. Does it include third-party material whose license has not been checked?
5. Does the README and research map explain the status and limitation of the new result?

If the answer to any of the first four questions is yes or uncertain, the file does not belong in the public repository.

## Relationship to the private laboratory

The private `OI-Organoids-Intelligence` repository remains the execution and working environment. This repository publishes selected conclusions and methods at a higher level of abstraction. Public content may be inspired by private work, but it must be rewritten so that it stands alone and does not reference private paths or hidden state.
