# 18 — Local Learning Selector Design (R2)

Scope: design of a local, non-LLM learned component that supports the selection method (files 15–17). It has no external AI API dependency. It is not a trading system, not a strategy optimizer, and does not decide trades. Claim IDs: `LRN-*`.

## 18.1 What the learner is allowed to do

The learner may supply only:
- `L`-class preferences (file 15 §15.3): which of several admissible candidates an annotated protocol would choose;
- abstention decisions (emit `UnresolvedState` with reason `OOD` or `EP` instead of a selection);
- estimates of the usefulness of selections, but only under objective C (§18.3) and as a separately reported property.

The learner may not:
- redefine any deterministic generator (SP-01 to SP-20 remain the authority for F and O properties);
- override a failed logical check (SP-07) or a failed source-fidelity check;
- create candidates that do not come from a generator;
- turn a learned preference into ICT doctrine. Learned outputs carry class `L` and are never presented as source-declared (`S`).

## 18.2 Inputs

Each training or inference example is a **frozen snapshot** taken at decision bar `t`:

- bars up to `t` (closed bars only), for each scale in use;
- candidate set with SP-01 to SP-17 outputs (factual and source-declared properties, with class labels);
- the task card identity (categorical);
- the representation identity and its parameters;
- the exclusion log;
- a learned-representation vector (optional; for example a TS2Vec-type encoder trained on bars only, TS2Vec, MIT-licensed open-source; see file 12 and claim OS-05 for scope). Such a vector is an unsupervised feature. It does not, by itself, encode ICT or any interpretation.

Snapshot rule: the snapshot is serialized before the selection is computed, so that the selection cannot influence the features or the labels. Any violation is a leak.

## 18.3 Objectives A–D (kept separate)

| Objective | Target | Evidence type | What success means | Failure it can hide |
|---|---|---|---|---|
| **A** Fidelity to a declared procedure | Output of a declared deterministic variant (e.g., one G-OB-P variant in file 05 §5.4a) on the same snapshot | Exact replication | Matches the declared procedure; no market claim | Learning an unstated rule and presenting it as the declared one. If A needs learning, the procedure is under-specified. |
| **B** Contextual coherence | Expert annotations of the candidate set under the pre-outcome snapshot: select / alternatives / none, with reason codes and free-text rationale | Human annotation (inter-annotator agreement reported) | Agreement with held-out annotators; calibrated abstention | Annotator bias; learning a house style. Requires agreement statistics and a disagreement set. |
| **C** Predictive usefulness | A forward outcome defined **before** training (e.g., a pre-declared forward statistic of the selected element relative to matched controls) | Causal, out-of-sample evaluation, purged and embargoed (file 12, AC-class sources) | Lift over matched controls on purged, time-blocked data | Overfitting to parameters; regime dependence; survivorship in the instrument universe |
| **D** Trading decisions | Not in scope. The owner's downstream decision logic is not part of this foundation. | — | — | — |

Separation rules:
1. Each objective has its own dataset, labels, metrics, and approval. A model trained for B may not be promoted on the basis of C, and vice versa.
2. C labels must never be used as B labels, and B annotations must not be made after seeing C outcomes for the same snapshot.
3. Objective A results must be reported as exact-match rates, not as accuracy on an unknown target.

## 18.4 Outputs

For each candidate: one of `select`, `alternative` (admissible but not preferred under the current objective), `reject` (with `X-*` code), or `abstain`. For each snapshot: the selection set (possibly more than one member), or an `UnresolvedState` (file 15 §15.7). Multiple selections are allowed; the learner must not force a single winner when the protocol says the situation is ambiguous.

Learner-specific reason codes: `EP` (no learned preference, or preference confidence not calibrated), `OOD`.

**No confidence percentages are reported.** Calibration may be assessed (e.g., reliability tables) and reported, but no universal probability threshold for "select" is given here. Each deployment must declare its abstention policy (SP-18), and that policy is evaluated by sensitivity analysis (SP-12).

## 18.5 Out-of-distribution handling

- A snapshot is OOD if its feature vector, instrument, scale, or regime lies outside the support of the validation data, as measured by a declared support check. The support check itself is an operational policy (SP-18) with no default value in this foundation.
- OOD snapshots are returned as `UnresolvedState` with code `OOD`. The learner is not run for these, or its output is discarded and logged.
- Support checks must be run on the same feature set the learner uses; a check on a different set is not evidence.

## 18.6 Validation design

- **Splits.** Time-blocked, with an embargo between blocks equal to the longest look-ahead used in any label (objective C). No random splits for any objective.
- **Regime and instrument stratification.** Report metrics per stratum; a stratum with insufficient cases is reported as insufficient, not averaged away.
- **Scale-shift test.** Train at one scale, test at another, and report the drop (a diagnostic of representation dependence).
- **Annotation agreement.** Report agreement between annotators on the same snapshots before any B metric is interpreted.
- **Matched controls for C.** Compare each selected element with controls matched on declared factual properties (e.g., scale, knowability status, containment label). Controls must be chosen before outcomes are seen.
- **Leakage audit.** Serialize-before-select check (§18.2) and replay consistency (SWS-04d) on a sample of snapshots.

## 18.7 Regression protocol (addresses F-05)

Learning updates can silently remove previously correct behavior. The following are required:

1. **Golden set.** A frozen set of canonical cases (file 19 cases W1–W10, plus the ICT-primary fixtures from SP-09/SP-10) with expected outputs. Any new model version must reproduce the golden set exactly for the deterministic parts and must either reproduce or log an approved change for the learned parts.
2. **Per-objective dashboards.** A, B, and C metrics tracked separately. An improvement on one objective may not be reported as a general improvement.
3. **Replay buffer.** Each retraining includes a fixed buffer of earlier annotated snapshots, so that previously learned distinctions are re-exposed. The buffer's composition is versioned.
4. **Shadow run.** A new version runs alongside the approved version on live snapshots without affecting outputs. Disagreements are reviewed before promotion.
5. **Abstention drift monitoring.** A rise or fall in abstention rate is a regression signal, reported even if accuracy looks stable.
6. **Authority order.** Deterministic procedures (SP-*) are authoritative for F and O properties and for logical checks. A learned output that conflicts with them is rejected and logged, not averaged.
7. **Versioning and rollback.** Every model, buffer, support check, and golden-set expectation is versioned. Rollback is always possible to the last approved version.
8. **Approval.** Promotion requires a recorded review of golden-set results, per-objective dashboards, and the shadow disagreement log. The approver is a named person, not the learner.

## 18.8 Learning-update limitations

- **Data drift.** Market regimes change; a learner validated in one regime may fail in another. Monitored through OOD checks and stratified metrics.
- **Label drift.** Annotator interpretations change over time. Handled by agreement re-measurement and by keeping the annotation guideline versioned.
- **Feedback loops.** If the system's own selections are shown to annotators or used as labels, the learner learns its own behavior. Prevented by the snapshot rule (§18.2) and by excluding system outputs from B labels.
- **Catastrophic forgetting.** Handled by the replay buffer and golden set (§18.7).
- **Non-stationary features.** Learned representation vectors can drift when retrained on new bars. Their version is part of the snapshot.
- **Small-sample strata.** Some contexts (rare scale combinations, rare regimes) will not have enough data. These are reported as insufficient and routed to `OOD` or `IC`.

## 18.9 What is implementable now versus what needs learning

Implementable from the design without learning: SP-01 to SP-20 (given parameter declarations), the unresolved-state emission, dependency-aware recomputation, the logical checks, the golden-set harness, and objective A as an exact-match harness.

Requires learning or empirical evaluation: objective B preferences (annotation campaign needed), objective C usefulness (causal evaluation with purged splits, data not yet collected), and any EP-coded choice (file 15 §15.7). See file 14, §14.8.

## 18.10 Claim statements (LRN)

- **LRN-01** Learning may supply `L`-class preferences and abstention; it may not redefine deterministic `F` or `O` properties.
- **LRN-02** Objectives A, B, and C are separate datasets, labels, metrics, and approvals.
- **LRN-03** Objective A measures replication of a declared procedure, not market truth.
- **LRN-04** Objective C requires outcomes defined before training, purged and embargoed time splits, and matched controls.
- **LRN-05** No universal probability threshold for selection is given; abstention policy is declared and sensitivity-tested.
- **LRN-06** The regression protocol (§18.7) is mandatory before any learned component is promoted.
