# 11 — Implementation Knowledge Contracts

These contracts describe what a future implementation must respect for each selection task. They are **knowledge specifications**, not code. Each contract separates:

- **[FACT-LOGIC]** — deterministic, implementable from observed data under a stated definition.
- **[JUDGMENT]** — contextual choice that must be learned, validated, or explicitly left as a set of alternatives.

No contract supplies numeric thresholds. Parameters are named and marked unresolved.

Common rules for all contracts:

1. Every output carries `knowable_bar` and the definition ID and parameters.
2. Outputs are **sets** of candidates with status; a single "best" output is only allowed as a *selector output* with the selector ID and the full candidate set retained.
3. Hindsight fields (`taken_later`, `held`, `respected`) exist only in a separate labeled table and never feed back into candidate generation at an earlier bar.
4. Competing outputs are never averaged silently.

---

## IC-01 — Movement segmentation (online)

- **Task identity:** identify the current movement state at bar t under a stated representation.
- **Required information:** closed bars up to t; scale identifier.
- **Candidate types:** change-point posterior over run length (causal); directional run labels (deterministic).
- **Temporal boundary:** only bars with close ≤ t. Forming bar excluded from confirmed state.
- **Supported contexts:** scale; instrument; session calendar (must be explicit).
- **Source-backed constraints:** a causal online method is available (OS-01). Offline methods (OS-02) must not be used in this contract's output (LL-03).
- **[FACT-LOGIC]:** run-length posterior and directional runs given the model/definition.
- **[JUDGMENT]:** the observation model and hazard; whether a change is a market event.
- **Legitimate alternatives:** multiple observation models; close-based vs range-based inputs.
- **Explicit unresolved states:** "no change detected," "change with low posterior," "model misspecified."
- **Dependencies:** none (root contract).
- **Invalidating evidence:** the output uses a bar with close > t; the output changes retroactively for the same t without a logged revision.
- **Requires empirical learning:** whether any state is predictive (target 5, file 07).

## IC-02 — Swing candidate generation

- **Task identity:** list all turning-point candidates under each swing family at each scale.
- **Required information:** closed bars; family and parameters (k, threshold, close vs wick).
- **Candidate types:** k-bar pivots, threshold-zigzag pivots, level-from-period extremes.
- **Temporal boundary:** each candidate has `occurrence_bar` and `knowable_bar`; a family-specific confirmation lag applies (e.g., k bars for k-bar pivots).
- **Supported contexts:** scale; calendar.
- **Source-backed constraints:** the ICT primary text read prefers higher-timeframe references for support/resistance (E, P1); it does not define a numeric swing rule (gap).
- **[FACT-LOGIC]:** given family and parameters, candidate set is deterministic.
- **[JUDGMENT]:** family and parameters; which candidates are "significant."
- **Legitimate alternatives:** all families above, at all scales.
- **Explicit unresolved states:** provisional, confirmed, invalidated.
- **Dependencies:** IC-01 (optional, for scale-state context).
- **Invalidating evidence:** a candidate's `knowable_bar` precedes data it uses; candidate set changes for past bars when new data arrives (repaint).
- **Requires empirical learning:** which families/parameters yield references that are useful for a given task (target 3/5).

## IC-03 — Swing selection by task

- **Task identity:** for a named task (T-REF-ENTRY, T-REF-INVALIDATION, T-REF-HTF-BIAS, T-LIQ-TARGET), select a subset of candidates from IC-02.
- **Required information:** IC-02 output; the task label; the selector definition.
- **Candidate types:** the same as IC-02, filtered.
- **Temporal boundary:** same as IC-02; selection at bar t uses only candidates with `knowable_bar ≤ t`.
- **Supported contexts:** task, scale, distance from current price (in units defined by the project), status.
- **Source-backed constraints:** the ICT Order Blocks lesson (P1) describes support/resistance references at higher timeframes and an invalidation-type stop at the block low; these support the task distinction but do not define a selector.
- **[FACT-LOGIC]:** filters by status, scale, and knowability.
- **[JUDGMENT]:** which candidate is relevant to the task; how many to keep; ranking.
- **Legitimate alternatives:** multiple selectors per task, each with an ID; no single "best" selector is justified.
- **Explicit unresolved states:** "no relevant candidate," "multiple equally plausible candidates."
- **Dependencies:** IC-02.
- **Invalidating evidence:** the same selector returns the same single candidate for all tasks (task-blindness), or a selected candidate's knowable time is after the decision time.
- **Requires empirical learning:** selector ranking; calibration of alternatives (target 3).

## IC-04 — Structure view construction

- **Task identity:** label the swing sequence into structural relations and define the current structural reference, for each (family, scale, break rule) combination.
- **Required information:** IC-02 candidates (confirmed only, per view), break rule.
- **Candidate types:** HH/HL/LH/LL pair labels; reference swing; trend label per view.
- **Temporal boundary:** a label is valid from its confirmation bar.
- **Supported contexts:** scale; family; break rule.
- **Source-backed constraints:** community break definitions are inconsistent (CF-02); the primary text read does not define BOS/MSS (GP-01).
- **[FACT-LOGIC]:** pair labels and reference assignment under explicit rules.
- **[JUDGMENT]:** which reference matters for the question; whether any break is meaningful.
- **Legitimate alternatives:** multiple views simultaneously (file 03 §3.8).
- **Explicit unresolved states:** "no structure change," "view A and view B disagree," "reference provisional."
- **Dependencies:** IC-02, IC-01.
- **Invalidating evidence:** a view's label changes without a new confirmed candidate; a label uses a forming bar.
- **Requires empirical learning:** whether any view predicts anything (target 5).

## IC-05 — Break event detection

- **Task identity:** detect when a bar breaks a specified structural reference, under a break rule.
- **Required information:** IC-04 reference; bar series.
- **Candidate types:** close-break event; wick-break event; reclaim event (close back on the original side).
- **Temporal boundary:** close-break knowable at the close of the breaking bar; wick-break knowable at the bar's close as well (intrabar timing unresolved, PM-07); reclaim knowable at its bar's close.
- **Supported contexts:** scale; reference; session if defined.
- **[FACT-LOGIC]:** the event occurs or does not under the rule.
- **[JUDGMENT]:** whether the event is structurally meaningful.
- **Legitimate alternatives:** close vs wick; with/without reclaim status.
- **Explicit unresolved states:** "break undetermined at scale" (if the break and reclaim occur in the same bar with unknown order).
- **Dependencies:** IC-04.
- **Invalidating evidence:** a break reported before the breaking bar closes under close rule.
- **Requires empirical learning:** the relationship between break types and subsequent movement (LL-03; CF-03). **The mission prohibits assuming "every break means reversal."**

## IC-06 — Liquidity candidate generation

- **Task identity:** list liquidity reference candidates under each family (individual extremes, equal-level clusters, prior period extremes, session extremes, round levels, range boundaries).
- **Required information:** closed bars; calendar and timezone; tolerance parameter for clusters; unit for round levels.
- **Candidate types:** as listed; each with side (buy-side above / sell-side below), level, knowable bar.
- **Temporal boundary:** prior period extremes knowable at period close; clusters knowable at the second member's confirmation; sessions at session close.
- **Supported contexts:** scale; calendar; tolerance; instrument.
- **Source-backed constraints:** BSL/SSL naming is community (S1). The primary FVG lesson uses "liquidity offered" for traded ranges (P1), a different referent (CASE-04).
- **[FACT-LOGIC]:** candidates and their taken status, given family and parameters.
- **[JUDGMENT]:** relevance; whether a candidate is a target; whether a cluster is meaningful.
- **Legitimate alternatives:** all families; wick vs close-based taken status.
- **Explicit unresolved states:** "taken (wick)," "taken (close)," "untaken," "tolerance-sensitive cluster."
- **Dependencies:** IC-02 (for swing-based), IC-03 (for selection).
- **Invalidating evidence:** the output states a cause ("stops here") as fact; a cluster's membership changes without a new bar.
- **Requires empirical learning:** whether any family's taken events differ from matched non-levels (HY-03, CF-05).

## IC-07 — Liquidity relevance evaluation

- **Task identity:** rank or annotate liquidity candidates for a task, without asserting hidden orders.
- **Required information:** IC-06 candidates with attributes (distance, scale, age, touches, taken status).
- **Candidate types:** annotated candidate sets; no single score.
- **Temporal boundary:** attributes computed from bars ≤ t.
- **[FACT-LOGIC]:** attribute computation.
- **[JUDGMENT]:** relevance.
- **Legitimate alternatives:** feature sets; per-task rules; learned ranking.
- **Explicit unresolved states:** "relevance unknown," "relevance conflicting across scales."
- **Dependencies:** IC-06.
- **Invalidating evidence:** a universal importance score is presented as ICT doctrine; relevance uses future taken status.
- **Requires empirical learning:** yes; no verified relevance function exists (UN-03, UN-07).

## IC-08 — Zone candidate generation

- **Task identity:** generate FVG and order-block candidates under each defined generator.
- **Required information:** closed bars; for G-OB-P a support/structure reference; for G-OB-C a displacement definition.
- **Candidate types:** G-FVG (three-candle imbalance), G-OB-P (lowest down-close with most range near reference), G-OB-C (last opposing candle before displacement).
- **Temporal boundary:** G-FVG knowable at third candle close; G-OB candidates knowable when the move that defines them is confirmed (and the reference is confirmed, for G-OB-P).
- **Supported contexts:** scale; reference; displacement definition.
- **Source-backed constraints:** ICT primary (P1) OB definition and FVG description; community definitions conflict (CF-01, CF-09).
- **[FACT-LOGIC]:** each generator's output given parameters.
- **[JUDGMENT]:** which generator is relevant; "near"; "displacement."
- **Legitimate alternatives:** both OB generators; both FVG readings; body vs wick boundaries.
- **Explicit unresolved states:** "G-OB-P produced no candidate (no reference near)," "candidate overlaps others."
- **Dependencies:** IC-02, IC-04.
- **Invalidating evidence:** a generator returns a candidate whose defining bars postdate the decision time; an FVG reported with no three-candle relation.
- **Requires empirical learning:** whether any generator's candidates differ in outcomes (UN-05, UN-06).

## IC-09 — Zone status tracking

- **Task identity:** maintain status history for each zone candidate.
- **Required information:** IC-08 candidates; subsequent bars.
- **Candidate types:** statuses: untested, touched, traded-through, closed-through, validated (per generator rule), expired (parameter).
- **Temporal boundary:** each transition has a bar and knowable time.
- **Source-backed constraints:** primary OB validation = later trade-through of the down candle's high (P1); invalidation-by-close is community (S1).
- **[FACT-LOGIC]:** status transitions under rules.
- **[JUDGMENT]:** which status matters for the task.
- **Legitimate alternatives:** trade-through vs close-based invalidation (both logged).
- **Explicit unresolved states:** "validated but close-invalidated," "expired (window choice)."
- **Dependencies:** IC-08.
- **Invalidating evidence:** a status changes without its defining bar; status history overwritten.
- **Requires empirical learning:** which status carries information (UN-06).

## IC-10 — Interpretation ledger

- **Task identity:** assemble competing interpretations for a question, each with supporting and contradicting observations, assumptions, and falsifiers.
- **Required information:** outputs of IC-03, IC-04, IC-07, IC-09 with their dependency IDs.
- **Candidate types:** interpretation objects (statement, evidence, assumptions, falsifiers, status).
- **Temporal boundary:** evidence ≤ t only.
- **Source-backed constraints:** none sufficient to rank interpretations (mission §9: no universal rules).
- **[FACT-LOGIC]:** evidence bookkeeping, shared-bar detection (overlap counts), dependency propagation.
- **[JUDGMENT]:** the statement set itself; presentation order.
- **Legitimate alternatives:** multiple interpretations simultaneously; no requirement to produce one.
- **Explicit unresolved states:** "unresolved," "competing equal-support," "weakened by new evidence."
- **Dependencies:** all upstream contracts.
- **Invalidating evidence:** two interpretations counted as independent when they share source bars; a single "confidence" percentage output; an interpretation with no falsifier.
- **Requires empirical learning:** whether ledger presentation improves decisions (not established; file 06 §6.17).

## IC-11 — Revision propagation

- **Task identity:** when new bars arrive, recompute statuses of dependent elements and log changes.
- **Required information:** dependency graph; new bars; revision log.
- **[FACT-LOGIC]:** recomputation and append-only logging.
- **[JUDGMENT]:** none in mechanics; interpretation revisions still require judgment.
- **Legitimate alternatives:** eager vs lazy recomputation.
- **Explicit unresolved states:** "revision pending" (for partial bars).
- **Invalidating evidence:** a logged output modified in place; missing revision entries.

## IC-12 — Causal snapshot and audit

- **Task identity:** reproduce any logged output using only data available at its decision time.
- **Required information:** bar store with close timestamps; code/definition versions; parameters.
- **[FACT-LOGIC]:** replay with truncated data; diff against logged outputs.
- **Invalidating evidence:** replay differs from log for a non-revision reason; any use of forming bars.
- **Priority:** this contract underpins every learning claim. Build it first.

## IC-13 — Learning targets and label protocols

- **Task identity:** train or evaluate selectors and representations under the six targets (file 07 §7.2).
- **Required information:** causal snapshots (IC-12); annotations with pre-outcome snapshot (file 07 §7.6); hindsight labels in a separate table; purged/embargoed splits.
- **[FACT-LOGIC]:** split generation, label-window computation, leakage checks.
- **[JUDGMENT]:** the label definition for "relevance"; annotator guidance.
- **Legitimate alternatives:** annotated relevance, outcome-based relevance (labeled hindsight), concept-fidelity tests.
- **Explicit unresolved states:** low annotator agreement; label ambiguity.
- **Invalidating evidence:** any feature computed from data after a sample's decision time; test-period parameter selection; reporting only the best configuration out of many.
- **Requires empirical learning:** all of target 3, 4, 5. Target 1 and 2 are deterministic tests.

---

## 11.14 Summary of what is implementable now versus what needs learning or evidence

| Area | Implementable now (FACT-LOGIC) | Requires learning or new evidence (JUDGMENT) |
|---|---|---|
| Movement | Bars, derived measures, causal change detection | Which movement scale matters for a task |
| Swings | Candidate families, knowability | Task-specific selection |
| Structure | Labels, break events under rules | Meaning of breaks |
| Liquidity | Candidate levels, taken status under rules | Relevance; whether levels attract price |
| Zones | G-FVG, G-OB-P, G-OB-C outputs; status | Which generator and status matter; "institutional" meaning (not a computable fact) |
| Reasoning | Ledgers, shared-bar detection, propagation | Which interpretation is right; ranking |
| Learning | Splitters, label protocols | Any predictive claim |

## 11.15 Evidence that would invalidate a claim in this foundation

- For any candidate-generation claim: a documented example where the generator's stated definition yields a different output than the definition states.
- For any "source says" claim: a verified primary text that contradicts the transcript reading (e.g., a different OB definition in the full lesson).
- For any structural or liquidity claim: a causal, out-of-sample study showing no difference between labeled elements and matched controls (would weaken, not prove absence of, usefulness).
- For any learning-protocol claim: a leakage test showing performance dependence on post-decision data.
