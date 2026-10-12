# 05 — Worked Cases, Understanding Tests, Pre-mortem, Unknowns, Builder Handoff (L, M, N)

The numbers in the cases below are illustrative only. They are not market data, not recommendations, and not thresholds. They exist to show how the architecture behaves.

## Worked case 1 — the same bars, two representations, different references

Illustrative closes at bars 0–5: **100, 120, 110, 135, 125, 145.**

- **Representation F-K, pivot window of 1 bar (illustrative):** confirmed turning points at 100 (low), 120 (high), 110 (low), 135 (high), 125 (low), with 145 provisional. Five legs are visible.
- **Representation F-T, reversal size τ = 15 (illustrative, declared):** the 120→110 retracement (10) and 135→125 retracement (10) are below τ. No reversal is confirmed. The structure is a single up-leg from 100, currently extended to 145.

Consequences:

| Task | Under F-K | Under F-T (τ = 15) |
|---|---|---|
| T-S1 structural reference (uptrend) | last confirmed higher low = 125 | last confirmed low = 100 |
| T-S5 falsifier of "uptrend intact" | close below 125 | close below 100 |
| Interpretation of a close at 124 | breaks the 125 higher low; the reading is invalidated | does not reach 100; the reading is intact |

**What the architecture does:** both representations are candidate generators in the kernel. Each produces an interpretation with its own `depends_on`. The two interpretations are kept as alternatives (an MHT-style hypothesis set), not merged. A learned scorer may rank them for a task only inside the admissible set, and the ledger records the one not chosen. Neither is "the correct wave".

**What the architecture forbids:** choosing whichever representation gives the answer that matches a later move, and labelling the wave "correct" because price subsequently rose.

## Worked case 2 — liquidity levels: which crossing counts?

Illustrative set of reference levels: previous-day high, equal highs within a declared tolerance, intraday high, weekly high.

- The kernel computes which levels a bar's range crossed (interval index; all matches returned).
- A "sweep" requires a declared definition (for example: crossed, and closed back beyond within a declared number of bars). Until the owner declares the definition, the output is `AMBIGUOUS` and lists the variants.
- Levels not crossed are recorded as `NOT_EXAMINED` or `EXCLUDED(NOT_CROSSED)` in the ledger; they are not dropped.
- Hidden liquidity (levels not yet visible) is not inferred. It appears in the unknowns list, not in the output.

## Worked case 3 — FVG tasks separated by type

Three tasks, three different treatments:

1. **Formation of a span within a declared displacement** — deterministic. Requires a declared displacement definition; without it the task is blocked, not guessed.
2. **Current interaction (touched, partly filled, fully traded through)** — factual; kernel state machine; no learning.
3. **Entry-model preference (which span among several is preferred under a model)** — the model conditions are computed deterministically; the preference among admissible spans is learned only if labels exist (LS-ANN). Otherwise the ranked list is shown without a preference.

Nothing in this case uses a profit label. FVG profitability is not a task in this build.

## Worked case 4 — cascading error

A reference is revised when a bar confirms a new pivot that the F-K generator previously did not have. Steps:

1. The new candidate creates an event `superseded` linking the old reference.
2. The interpretation graph marks every interpretation whose `depends_on` includes the old reference.
3. Their admissible sets and ledger entries are recomputed; the revised entries are new events.
4. Downstream concepts (for example a liquidity reading that used the old reference as a level) are recomputed.
5. The change is logged with the cause (`kernel_version`, bar hash).

**Test:** a replayed sequence with a late-confirmed pivot must produce the same final interpretations as a fresh run, and the intermediate records must show the supersession.

## Worked case 5 — trade loss decomposition (diagnostic, not a learning label)

When a trading outcome is poor, the architecture requires the loss to be attributed to a stage before any component is changed:

| Stage | Evidence that would implicate it | Component |
|---|---|---|
| Data correctness | Gaps, duplicates, source disagreement | K1 |
| Candidate extraction | Generator misses or false candidates on LS-SYN or annotated cases | K3 |
| Information availability | Used data that was not knowable at the snapshot | K7, replay test |
| Contextual selection | Right candidates admissible, wrong one ranked; ledger shows alternatives | L2 |
| Concept application | Declared definition not met by the implementation | K4, differential tests |
| Interpretation | Constraint violations or incoherent member set | L3 |
| Predictive estimation | Objective E shows no effect against controls | evaluation |
| Trading decision | Out of scope here | — |

An outcome cannot by itself implicate a component. The attribution must come from a stage test. Updates are applied only to the implicated component, with an attribution record.

## Understanding tests (mastery probes)

The system is said to "understand" a concept only in the operational sense below. Each probe is a test, not a claim.

| Probe | Test design | Pass condition (declared in test) |
|---|---|---|
| Identify | Hand-labelled positive and negative snapshots | Matches the definition's test cases |
| Distinguish | Near-miss pairs (differ by one observable) | Outputs differ exactly where the definition says |
| Locate in context | Same concept in different structural contexts | Reference and binding are reported with alternatives |
| Apply consistently | Same snapshot recomputed from scratch versus incrementally by arrival-order replay | Identical final output; provisional status preserved in intermediate records |
| Explain relevance | Feature attribution and definition trace | Every output traces to kernel and feature inputs |
| Preserve alternatives | Ambiguous cases | Output lists variants, not one variant |
| Maintain dependencies | Revision cases (case 4) | Recomputed interpretations match a fresh run |
| Generalise | Held-out generator families and periods | Pre-registered comparison to baseline |
| Improve validly | Retrain under the gate | Gate passed; no profit-based promotion |

## L. Failure pre-mortem

Assume the project fails in twelve months. Likely causes, detection, smallest correction, and what stays unchanged.

1. **Labels are circular with the rule.** Learner reproduces the rule and is reported as an improvement. *Detect:* LS-RULE agreement high, LS-ANN disagreement unexamined. *Correct:* report fidelity separately; require a baseline comparison on LS-SYN and LS-ANN. *Unchanged:* kernel.
2. **Synthetic generator too easy or too like the rule.** Recovery is inflated. *Detect:* families where the declared rule is already perfect. *Correct:* add families with noise, gaps and regime changes; report per family. *Unchanged:* ledger and tests.
3. **Hidden thresholds in the ranker.** Learned cut points become de facto doctrine. *Detect:* attribution concentrates on a few scale features; sharp score steps. *Correct:* feature ablation; restrict features; export cut points for review. *Unchanged:* admissibility.
4. **Budget silently truncates search.** Unexamined candidates vanish. *Detect:* `NOT_EXAMINED` counts absent from reports. *Correct:* make the ledger a required output; fail the run if a candidate has no entry. *Unchanged:* generators.
5. **Lookahead leakage.** Features use bars confirmed after the snapshot. *Detect:* replay test with truncated history gives different outputs. *Correct:* enforce `confirmed_at_bar` in the index; add the replay test to R1. *Unchanged:* labels.
6. **Repeated pivot confirmation creates duplicate candidates.** Counts inflate. *Detect:* duplicate hashes with different provenance. *Correct:* canonical identity by bar span and kind. *Unchanged:* definitions.
7. **Definition drift.** A generator is "tuned" and no one notices. *Detect:* hash change without version bump. *Correct:* hash in the artifact and CI check. *Unchanged:* other generators.
8. **Abstention never used.** The system always picks, hiding ambiguity. *Detect:* abstention rate zero on LS-ANN ambiguity cases. *Correct:* review the declared ambiguity rule. *Unchanged:* scores.
9. **Coherence components too large.** Exact inference becomes infeasible. *Detect:* largest component size growing; `approximate` flags. *Correct:* tighten declared task scope; add hard constraints. *Unchanged:* unary scorer.
10. **Annotator drift or low agreement.** Labels become noise. *Detect:* agreement falls across sessions. *Correct:* protocol revision with versioned labels; re-annotate golden set. *Unchanged:* synthetic labels.
11. **Overfitting to the golden set through repeated review.** *Detect:* golden-set score rises while shadow agreement falls. *Correct:* rotate a held-out portion; log every golden-set access. *Unchanged:* training data.
12. **Live feedback loop.** Shadow or served outputs become labels. *Detect:* `derived_from_system` labels in training. *Correct:* exclusion by default; lineage check in the registry. *Unchanged:* protocol.
13. **Promotion on recent profit.** Pressure to deploy after a good period. *Detect:* promotion record lacks objective E report. *Correct:* hard gate in the registry. *Unchanged:* shadow mode.
14. **Scope creep to FVG and liquidity before swings are tested.** *Detect:* tasks registered before Phase 1 gate. *Correct:* registry refuses tasks without a passed predecessor. *Unchanged:* kernel.
15. **The owner's existing definitions conflict with the foundation.** *Detect:* differential test against the owner's definitions (requires inspection, see §Unknowns). *Correct:* record as variant conflicts; the owner decides. *Unchanged:* foundation definitions.

## M. Unknowns requiring inspection of the owner's project

These cannot be answered from this research. They require the owner to supply information or access to their own repository. This research did not inspect that repository and does not depend on it.

1. Language, runtime version and existing packaging of the owner's project.
2. Bar data sources, timezone convention, session definitions, handling of gaps and of holidays.
3. Available history depth and instruments.
4. Existing indicator and concept implementations: whether they encode trading rules, which parameters are hard-coded, and whether they are tested.
5. Whether any labelled data already exists (annotations, reviewed setups) and under what protocol.
6. Existing trade logs (only needed for the stage-gate of objective F, if ever).
7. Hardware available for local use: CPU, RAM, storage, GPU presence.
8. Licence and ownership constraints on any code or data the owner wants to reuse.
9. Whether the owner's definitions match the foundation's variants; the owner's decision on each conflict.
10. The audit attachment referenced in earlier work (not present in the workspace).
11. Declared values the owner must set: matching tolerances, ambiguity rule, feature measure and window, budgets, pre-registered margins, drift measures, stratification keys and sizes. None is set here.

## N. Builder-ready handoff

### N.1 Read first
`00_EXECUTIVE_DECISION.md` (decision and rejections), `02` §H (safeguards), `03` §B (swing objective), `04` §K (first build).

### N.2 Proposed layout (proposal; the builder may adapt)
```
kernel/        bars, candle semantics, generators, geometry, index   (no learning imports)
ledger/        candidates, admissibility, ledger, interpretations
tasks/         declared task definitions (versioned)
learn/         features, unary scorer, trainer, evaluator           (reads kernel, never writes it)
coherence/     factor components, budgeted inference                (phase 3)
registry/      artifacts, promotion gate, rollback
synth/         hierarchical generator with declared families          (LS-SYN)
tests/contract/ kernel contracts, replay test, ledger completeness
tests/golden/  frozen reviewed snapshots
reports/       evaluation reports with baselines and run metrics
```

### N.3 Order of work
1. Phase 0: kernel, contracts, declared-rule baseline. Stop if any contract test is missing.
2. Phase 1: synthetic generator; baseline comparisons; gate report.
3. Only if gate passed: Phase 2 annotation protocol and LS-RULE fidelity.
4. Phase 3 only after Phase 2 data exists.

### N.4 Non-negotiables
- No learned write to kernel tables; no label from future profit for structure or concept use.
- No top-k pruning without a ledger entry for every excluded candidate.
- No numeric default enters the system without owner declaration and sensitivity reporting.
- No LLM or external paid API in the runtime path.
- No promotion without the gate in `04` §I.6.
- Every output is an interpretation under declared definitions, with versions, status and alternatives.

### N.5 Acceptance for the research itself
- Every deliverable (A–O) is answered in one of these files: A, B, O in `00`; C, D in `01`; E, F, H in `02`; G in `03`; I, J, K in `04`; L, M, N and the understanding tests in `05`.
- Outstanding: the owner's repository has not been inspected; no benchmarks exist; no references were fetched in full text beyond the verified abstracts and metadata listed in `01`.
