# 04 — Continual Learning, Local Compute, First Implementation Specification (I, J, K)

## I. Continual learning

### I.1 Two modes

| Aspect | Historical mode | Live mode |
|---|---|---|
| Purpose | Train, validate and compare versions on past data under purged walk-forward | Apply a promoted version; observe drift; collect shadow outputs |
| Data | Frozen snapshots with known data hash | Closed bars as they arrive; snapshot per decision |
| Label arrival | Labels computed from the frozen history with their maturity recorded | Labels arrive after horizon; LS-SYN and LS-RULE are immediate, LS-ANN is asynchronous, LS-PERS and LS-OUT mature later |
| Updates | Batch retrain with replay (I.3) | Only the promotion gate changes the serving version; no online weight updates in stage 1 |
| Output | Model candidate with report | Interpretations with versions; shadow records |

**Stage 1 has no online learning.** Live mode serves a frozen version. Retraining is a historical-mode batch with a new version identifier.

### I.2 Versioned artifacts

Every model artifact is recorded with:
- `artifact_id`, `created_at`, `training_data_manifest_hash` (bars, labels, label sources and maturity cut-off);
- `feature_schema_version`, `generator_set_version`, `kernel_version`;
- `objective_id` (A–F), `hyperparameters` (as recorded, not tuned on the hold-out);
- the evaluation report hash, including all baselines;
- `parent_artifact_id` (lineage).

Artifacts are immutable. A rollback re-points the serving version; it does not overwrite.

### I.3 Replay

- **Golden set.** A frozen, hand-reviewed set of snapshots with LS-ANN and LS-RULE labels, never used for training. It is the regression gate.
- **Stratified replay buffer.** For each retrain, the training set includes a stratified sample from every generator family, scale and regime cluster seen so far, so that new data does not erase older families. Stratification keys are declared; their sizes are declared and reported. No numeric buffer size is recommended here.
- **Label replay.** Labels are retained with their source and maturity, so a relabelled cut-off can be reproduced.

### I.4 Drift

Drift is monitored on:
- feature distributions per generator and scale (declared divergence measure and reporting threshold, to be set by the owner — not set here);
- ensemble disagreement over time;
- the fraction of admissible sets that are empty or ambiguous (structural drift in the market or in the generators);
- agreement with LS-RULE on new snapshots (rule-fidelity drift).

A drift signal triggers review, not automatic retraining.

### I.5 Shadow evaluation

A candidate version runs beside the champion on live closed bars, writing its interpretations to a shadow table. Comparison uses only objectives that can be evaluated at the time: A–D, and E once horizons have matured. Shadow records are never used as training labels for the same snapshot.

### I.6 Promotion gate and rollback

States: `candidate → shadow → champion`, with `retired` and `rolled_back`.

Promotion requires all of the following:
1. Kernel contract tests and golden-set regression pass.
2. The candidate beats the declared baseline on its pre-registered objective, on held-out families or periods, by a margin **that the owner declares before the evaluation** (no margin is set in this document).
3. The candidate does not violate any constraint status that the champion satisfies.
4. Shadow evaluation over a declared period shows no unexplained divergence on the golden set.
5. Attribution and lineage are complete.

**No automatic deployment on recent profit.** A version cannot be promoted, and cannot be retained, because of a recent profitable period. Objective E must pass under the purged protocol; a single favourable period is recorded as an observation.

Rollback: re-point to the parent artifact; keep the failed artifact and its report.

### I.7 Catastrophic forgetting

Stage 1 uses replay (I.3) and full retraining, not weight regularisation. Elastic weight consolidation and similar regularisers add Fisher estimates and hyper-parameters with unclear benefit for a gradient-boosted ranker. Revisit only if a neural encoder is adopted and replay fails on the golden set.

### I.8 Avoiding self-training loops

- The system's own interpretations are never labels for the snapshot that produced them.
- Corrections by a reviewer are stored as LS-ANN with the reviewer's id and are labelled as corrections of the system output.
- Any label derived from a system output is tagged `derived_from_system` and excluded from training by default.

## J. Local compute feasibility

No benchmark numbers are given: none have been measured for this system. The following is structural reasoning from the component design.

- **Candidate generation and index updates:** per-bar work is bounded by active generator states and affected index neighbourhoods. Expected to run on a single CPU core for one instrument and a few timeframes; to be measured.
- **Unary scorer (gradient-boosted ranker):** tabular, CPU-only training and inference. Memory scales with rows × features; rows scale with snapshots × tasks × admissible candidates. Row counts must be estimated from the first synthetic run and reported.
- **Coherence:** exact enumeration cost is the product of domain sizes per component. It is bounded by a declared budget; memory and time are reported per run.
- **Synthetic generation:** cheap and parallelisable on CPU.
- **Optional encoder (stage 2+, e.g. TS2Vec-style):** CPU training is possible but slower; a GPU is optional. Decide only after the stage-1 baseline is measured.
- **Storage:** append-only event logs plus materialised views are sized by bars and candidate counts. Sizes must be measured on the owner's data, not estimated here.
- **Hardware specification:** unknown (see file 05 §Unknowns). The owner must state available CPU, RAM and storage before the first build is scheduled.

What must be reported on every run, so that feasibility is evidenced: wall-clock time per stage; peak memory; row counts; largest coherence component size and whether it was exact or approximate; number of `NOT_EXAMINED` entries.

## K. First implementation specification

### K.0 Scope

- Instrument: one, chosen by the owner. Timeframes: one fine and one coarse, chosen by the owner.
- Begin with price only: closed bars → candidates (swings, legs) → structural references. No FVG, no liquidity, no entry model in this build.
- Tasks in scope: **T-S1** (structural reference selection for a declared role), **T-S2** (binding of a reference to the leg that formed it), **T-S5** (falsifier: the level whose violation invalidates a declared structural reading). Role definitions come from the owner's declared task list; the names are the foundation's identifiers.
- Out of scope: trade decisions, profitability, order management, live execution, FVG, liquidity, entry models.

### K.1 Phases

**Phase 0 — kernel and contracts (no learning).**
- Bar store, candle semantics with `UNKNOWN` for ambiguous intrabar order, F-K and F-T generators with declared parameters, interval index, ledger, admissibility for T-S1/T-S2/T-S5.
- Contract tests (file 02 §H.3) all passing.
- Deterministic baseline output for each task: the declared rule. This is the reference that every later phase must beat or be replaced by.

**Phase 1 — synthetic ground truth (learning begins).**
- Generator: hierarchical random price process with declared families (for example: different turning-point density, noise levels, gaps, regime switches). Parameters declared, recorded, and sampled from declared ranges; the ranges are owner-declared.
- Labels: LS-SYN role per candidate.
- Model: gradient-boosted ranker (unary) for T-S1 and T-S5; abstention trained only on declared equivalence cases.
- Evaluation: family holdout; all baselines in file 03 §B; regret and top-1 agreement; attribution review for hidden thresholds.
- Gate: pre-registered margin over the declared baseline on held-out families. If not met, stop and report; do not tune on the hold-out.

**Phase 2 — rule fidelity and real-data review.**
- On real closed bars, the learner is compared with LS-RULE outputs (where a rule is the target, e.g. a declared fallback).
- LS-ANN: a written annotation protocol for T-S1 disputes on real snapshots, with at least two annotators and agreement recorded. Annotation protocol content is an owner decision.
- Outputs on real data are presented as interpretations with uncertainty fields. No profitability evaluation.

**Phase 3 — coherence (T-S1 + T-S2 + T-S5 jointly).**
- Factor graph within components; hard constraints exact; learned pairwise factor trained on LS-ANN coherence and LS-SYN hierarchy consistency.
- Budgets declared; `NOT_EXAMINED` recorded.
- Gate: independent per-task baseline comparison on coherence agreement and constraint violations (zero).

**Phase 4 — objective E (evaluation only, optional for this build).**
- Only after Phases 1–3 pass and a decision-policy owner exists for any use. Purged protocol; matched controls.

### K.2 Interfaces (logical, for the builder)

- `kernel.bars` — read/write by ingestion only.
- `kernel.generators.run(snapshot) → candidates[]` — deterministic.
- `kernel.index.query(time_window, price_range, kind) → candidates[]` — returns all.
- `ledger.admissible(task, snapshot) → entries[]` — exact.
- `learn.score(task, rows) → scores[], abstain[], attributions[]` — read-only; versioned.
- `coherence.solve(component, budget) → interpretations[], unexamined[]`.
- `registry.serve(task) → artifact_id` — only path to a learned version in live use.

### K.3 Acceptance criteria (what "done" means for each phase)

- Every interpretation has version identifiers, a constraint status, and its unexamined alternatives listed.
- Every candidate has a ledger status for every task.
- Contract tests pass; the golden set is unchanged except by a logged, reviewed addition.
- Every comparison against a baseline is reported with the baseline, its parameters and the held-out split.
- No output is described as correct, understood, or profitable. Outputs are described as interpretations under declared definitions.
- The learned component can be disabled and the system falls back to the declared rule with a visible flag.

### K.4 Fallback

If a learned component fails a gate, or its version is rolled back, the declared rule is served with `model_status = FALLBACK`. Failure to beat the baseline is an outcome, recorded in the report, and the learned scorer is archived.

### K.5 Explicitly not in this build

Trading logic; order sizing; live connectivity; LLM components; GNNs; reinforcement learning; FVG and liquidity tasks; universal thresholds; any use of profit as a label.
