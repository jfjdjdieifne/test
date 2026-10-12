# Learning Market-Analysis Intelligence — Architecture Research (AR-1)

Status: research and design only. **v2 (`v2/`) supersedes parts of this round; see `v2/00_DECISION_AND_CHALLENGE.md`.** No trading code, no strategy optimization, no live execution, no performance claims. Nothing here has been run on market data.

Relation to the knowledge foundation (`../knowledge_foundation/`): the foundation supplies definitions, provenance, selection contracts and the claim index. This directory decides how a future system should use those definitions, learn contextual selections, and be evaluated.

## Reading order

| File | Contents | Deliverables |
|---|---|---|
| [00_EXECUTIVE_DECISION.md](00_EXECUTIVE_DECISION.md) | Recommended architecture, comparison of serious options, rejections | A, B, O |
| [01_REFERENCES_AND_OPEN_SOURCE.md](01_REFERENCES_AND_OPEN_SOURCE.md) | Academic references and verified open-source candidates | C, D |
| [02_COMPONENTS_WORKFLOW_FOUNDATIONS.md](02_COMPONENTS_WORKFLOW_FOUNDATIONS.md) | Components, data structures, inference workflow, complexity, uncertainty, foundational mastery safeguards | E, F, H |
| [03_LEARNING_OBJECTIVES_AND_LABELS.md](03_LEARNING_OBJECTIVES_AND_LABELS.md) | Objectives A–F, label sources and maturity, label-free learning, teaching new concepts | G |
| [04_CONTINUAL_COMPUTE_FIRST_BUILD.md](04_CONTINUAL_COMPUTE_FIRST_BUILD.md) | Historical and live learning, local compute, first implementation specification | I, J, K |
| [05_CASES_PREMORTEM_HANDOFF.md](05_CASES_PREMORTEM_HANDOFF.md) | Worked failure cases, understanding tests, pre-mortem, unknowns, builder handoff | L, M, N |

## Conventions

- **Foundational** = deterministic, testable against a definition. Owned by the kernel; learned components cannot change it.
- **Declared policy** = an owner-chosen value or rule, labelled as such, sensitivity-tested. Never presented as market truth.
- **Learned** = a preference or score estimated from data under a named objective, with its own validation.
- **Source-supported** = traceable to a cited source with its grade (see the foundation's file 00).
- No universal numerical thresholds, confidence percentages or importance scores are introduced. Where a number appears in an example it is labelled illustrative and is not a recommendation.
- Claim-level citations: `[V]` verified in a session (abstract, repository metadata or page read); `[M]` bibliographic detail from memory, to be checked before publication.
