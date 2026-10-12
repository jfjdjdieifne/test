# 03 — Learning Objectives, Label Sources, Label-Free Learning, Teaching New Concepts (G)

Each objective states: unit, input, target, supervision, label maturity, loss, baseline, metrics, splits, leakage prevention, and failure analysis. No objective uses future profit as a label for structure or concept application.

## Label sources and maturity

| Source code | Description | Maturity | Can validate | Cannot validate |
|---|---|---|---|---|
| **LS-SYN** | Synthetic hierarchical price series with generator-known turning points and hierarchy | Exact (by construction) | Whether the algorithm recovers structure the generator produced, under declared generator families | Real-market correctness; that the generator resembles any market |
| **LS-RULE** | Output of a declared, versioned kernel rule on a snapshot | Exact relative to the rule | Fidelity of an approximation to the rule | That the rule is the right one |
| **LS-ANN** | Human annotation under a written protocol, with inter-annotator agreement recorded | Medium; subject to annotator bias | Coherence judgements, ambiguity, role plausibility | Ground truth; annotator agreement is not validity |
| **LS-PERS** | Persistence of a declared structural claim until its declared resolution (for example a reference not violated before the claim's resolution point) | Matures only after the claim's horizon | Internal consistency of a claim with its own declared resolution | Profitability; any claim that is circular with the rule that produced it (must be checked) |
| **LS-OUT** | Forward return or trade outcome | Matures after horizon; confounded | Predictive usefulness under objective E only | Concept application or structure correctness; never used for A–D |
| **LS-NONE** | No label | — | Structure and diagnostics only (clustering, stability, disagreement) | Any claim of correctness |

Every label record stores: `source_code`, `definition_version`, `maturity` (`provisional` / `matured`), `annotator_id?`, `generator_params_id?`, and the horizon used.

## A. Movement representation

- **Unit:** a series window at one representation scale.
- **Input:** bars up to the window end; representation parameters (declared).
- **Target:** LS-SYN turning-point set (for recovery), and LS-RULE for fidelity of the learned segmenter to F-K/F-T where a segmenter is learned.
- **Supervision:** synthetic ground truth; rule outputs.
- **Label maturity:** exact (synthetic); exact relative to rule.
- **Loss:** point-matching classification (each bar: turning / not turning at the scale), with a matching tolerance **declared in bars and reported with every result** (the tolerance is a policy; sensitivity sweep is reported, not optimised).
- **Baselines:** F-K and F-T as declared; PELT (offline, for comparison only); BOCPD (causal, for comparison only).
- **Metrics:** precision and recall of turning points under each declared tolerance; detection lag distribution (bars from turning point to confirmation); hierarchy-consistency rate (fine turning points inside coarse legs); behaviour under noise, gaps and regime changes (generator families held out).
- **Splits:** by generator family and by generator parameter region, not random bars.
- **Leakage prevention:** the window ends at the decision bar; a point is counted as detected only at its confirmation bar; offline methods (PELT) are scored under the same causal rule or labelled non-causal.
- **Failure analysis:** per family and per parameter region; confusion between noise and genuine turns; lag-inflated detections.

## B. Swing and reference selection

- **Unit:** (snapshot, task, admissible candidate set).
- **Input:** L1 features for each admissible candidate; the candidate's geometry and status.
- **Target:** for T-S1 (reference) — LS-SYN role under the generator; for fidelity — LS-RULE; for ambiguous or disputed cases — LS-ANN with an explicit `AMBIGUOUS` option.
- **Supervision:** synthetic first (stage 1), then rule-fidelity, then annotation (stage 2).
- **Label maturity:** exact (LS-SYN, LS-RULE); medium (LS-ANN).
- **Loss:** listwise softmax or LambdaRank over the admissible set, plus an abstention class trained only on LS-ANN ambiguity labels and on LS-SYN cases where two candidates are declared equivalent.
- **Baselines (all reported):** (a) declared rule; (b) uniform random over admissible set; (c) recency-only (declared, labelled as a policy); (d) nearest-by-scale rule (declared); (e) PELT/BOCPD-derived candidate with the same admissibility.
- **Metrics:** top-1 agreement with truth on LS-SYN held-out families; regret relative to the best admissible candidate under LS-SYN; agreement with LS-RULE; abstention quality against LS-ANN ambiguity labels; stability of selection under declared-parameter sensitivity sweeps.
- **Splits:** generator-family holdout; instrument and time holdout for real data; purged walk-forward for any LS-PERS-based evaluation (purge length = label horizon; embargo declared).
- **Leakage prevention:** admissibility enforces knowability; features are computed from the snapshot only; LS-SYN "truth" is never a feature; annotators see only the snapshot (not later bars) unless the annotation protocol explicitly asks about resolution.
- **Failure analysis:** top confusion pairs (which candidate was preferred over which); cases where the declared rule and the learner disagree; features with unexpectedly large attribution (possible hidden threshold); behaviour when the admissible set is empty.

## C. Linked-interpretation coherence

- **Unit:** joint configuration across linked tasks within one component.
- **Input:** the member candidates and their pairwise relations (containment, shared time window, crossing history).
- **Target:** hard constraints (exact, no labels needed); learned pairwise factor from LS-ANN coherence judgements and LS-SYN hierarchy consistency.
- **Supervision:** rules plus annotation.
- **Label maturity:** exact for constraints; medium for annotation.
- **Loss:** structured hinge (max-margin) on the pairwise factor; hard constraints are never softened.
- **Baselines:** independent per-task argmax (B alone) — shows whether coherence adds value; the declared rule's joint output.
- **Metrics:** constraint violations (must be zero); agreement with coherence annotations; propagation correctness (when a member is revised, the expected dependents are recomputed — a unit test, not a learned metric).
- **Splits:** by snapshot cluster and by family.
- **Leakage prevention:** the factor is trained only on snapshots whose annotation did not use later bars.
- **Failure analysis:** components that hit the budget; interpretations left in multiple alternatives; disagreements where the independent baseline was more coherent than the joint output.

## D. ICT concept fidelity

- **Unit:** (concept definition variant, snapshot).
- **Input:** kernel outputs for the concept's observables.
- **Target:** the concept's *declared* operational definition. Where the sources disagree, the output is `AMBIGUOUS` with the variants listed, not a chosen variant.
- **Supervision:** none for the rule itself; LS-RULE for implementation checks; LS-ANN for review of whether a variant matches a written definition.
- **Label maturity:** exact for implementation (differential tests against the definition); unresolved for doctrine.
- **Loss:** not applicable for the deterministic detector. A learned classifier is **not** used to decide concept presence. Learning may be used only to detect implementation drift (differential testing).
- **Baselines:** the implementation's own unit tests; independent re-implementation by a second builder.
- **Metrics:** exact-match on the concept's test cases (holds by construction for deterministic variants, so the meaningful metric is the coverage of those test cases); number of unresolved variant conflicts; review decisions recorded.
- **Splits:** not applicable; test case sets are hand-written and versioned.
- **Leakage prevention:** concept detection uses only closed bars at the decision time.
- **Failure analysis:** cases where two variants both match; cases where the source definitions changed.

## E. Predictive usefulness (evaluation only)

- **Unit:** (selected element, decision time, declared horizon, matched controls).
- **Input:** the element's features at decision time.
- **Target:** a forward statistic defined **before** training (for example a declared path measure), compared with matched controls drawn from the same snapshot distribution.
- **Supervision:** LS-OUT, used only as an evaluation target.
- **Label maturity:** matures after horizon; confounded.
- **Loss:** not trained here. Objective E is an evaluation objective; no model is fitted to it in stage 1.
- **Baselines:** matched random controls; declared rule; no-selection.
- **Metrics:** difference from matched controls with interval estimates; stability across regimes; multiple-trial adjustment (for example the probability of backtest overfitting or a deflated statistic, if the number of trials is tracked).
- **Splits:** purged walk-forward, purge = horizon, embargo declared; a final hold-out period untouched until the protocol is frozen.
- **Leakage prevention:** overlapping horizons are purged; features are snapshot-only; no selection rule is tuned on the hold-out.
- **Failure analysis:** effect concentrated in few periods; dependence on a single instrument; differences that vanish under matched controls.

## F. Trading decision quality (out of scope; gate only)

- **Status:** not part of this architecture's stages. Recorded so it is not built by accident.
- **Required before any work on it:** a written decision policy, a cost and slippage model, a risk policy, and objective E passing on an independent period. Each is an owner decision.
- **Label maturity:** outcome-based; hindsight-contaminated by the decision policy itself.
- **Rule:** outcomes from F must never be fed back as labels for A–D.

## Label-free learning

Label-free methods are permitted for **structure discovery and diagnostics only**. They never produce a label for correctness.

Permitted:
- Clustering or embedding of admissible candidates to detect near-duplicates and representation redundancy.
- Stability analysis: how often a candidate is selected across declared parameter sweeps.
- Disagreement analysis between generators (agreement counts).
- Drift detection on feature distributions (file 04).

Not permitted:
- Treating cluster membership as "correct wave" or "valid concept".
- Using reconstruction error or self-supervised loss as evidence of market understanding.
- Using any unlabeled metric to choose a promoted model.

## Teaching the system a new concept

A new concept enters in one of two distinct ways. They must not be confused.

**Route 1 — new operational definition (kernel change).**
1. Write a concept specification: name, observables, operational definition(s) with variants and their sources, scale, knowability rule, explicit ambiguities, and test cases (positive, negative, edge). Status `DECLARED`.
2. Implement the deterministic detector as a kernel generator with a version and hash.
3. Pass contract tests and the concept's test cases.
4. Register it as a candidate generator. Only then can tasks reference it.
5. Learned components are not retrained for this unless a task needs a new scorer; existing ones keep their versions.

**Route 2 — new contextual preference (learned selector).**
1. A task exists (declared role, admissibility rules, label sources).
2. Labels exist under the label sources above, with maturity recorded.
3. The unary scorer is retrained on the task's rows under the file 04 gate. Other tasks' scorers are not touched.

**Prevention of corruption of existing concepts:**
- A new concept cannot change an existing generator's parameters or outputs; it gets its own version and ID.
- Old interpretations keep their `depends_on`; they are not rewritten.
- Regression harness runs the old concept test set on every change.
- A new concept that overlaps an old one is recorded as a relation (`overlaps_with`, `subsumes`, `conflicts_with`) and not merged silently.
