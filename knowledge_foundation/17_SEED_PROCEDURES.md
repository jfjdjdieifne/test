# 17 — Seed Procedures (R2)

Purpose: implementation-oriented contracts for the selection steps in files 15 and 16. Each procedure is a *seed*: a starting specification to be implemented, tested, and refined, not a settled market rule.

Depends on: `15` (property classes, exclusion and unresolved codes), `16` (task cards, priority items). Claim IDs: `SP-*`.

## 17.1 Required fields

Every procedure below states:

- **ID** and **Task** (which task card it serves)
- **Inputs** (typed; each input has its time of availability)
- **Steps** (deterministic; no step reads data after the decision bar)
- **Outputs** (selection, exclusion with reason, or unresolved state with code)
- **Provenance** (researcher `R`, ICT-primary `P1`, ICT-secondary `S`, academic `AC`, open-source `OS` — per file 12 — and property class per §15.3)
- **Counterexamples** (situations where the step is known or expected to misbehave)
- **Unresolved parameters** (named slots; no values)
- **Validation** (what must be shown before the procedure is trusted)

## 17.2 Procedure index

| ID | Name | Task | Provenance | Property class |
|---|---|---|---|---|
| SP-01 | Knowability gate | all | R | F |
| SP-02 | Task-scale compatibility table | T-S6, T-S1 | R (table is O) | O |
| SP-03 | Event binding by crossing | T-S2 | R | F |
| SP-04 | Falsifier binding | T-S5 | R | F given I |
| SP-05 | Containment / escape classification | T-S3, item 8 | R | F |
| SP-06 | Dominance filter | all | R | F |
| SP-07 | Logical consistency check | combinations | R | F |
| SP-08 | Entry-leg window | T-S3 | R | F |
| SP-09 | Order-block validation (trade-through) | OB tasks | P1 | S |
| SP-10 | Order-block stop reference | OB tasks | P1 | S |
| SP-11 | FVG three-candle geometry | FVG tasks | R (geometry), S (definition) | F / S |
| SP-12 | Sensitivity analysis protocol | all parameterized | R | O |
| SP-13 | Turning-point confirmation status | T-S1, item 9 | R | F |
| SP-14 | Leg construction | item 2 | R | F |
| SP-15 | Retracement base | T-S4 | R | O |
| SP-16 | Representation-dependence reporting | T-S6, item 10 | R | F |
| SP-17 | Liquidity taken status | liquidity tasks | S (community E*) for naming; R for definition | F |
| SP-18 | Declared policy registry | all | R | O |
| SP-19 | Unresolved-state emission | all | R | F |
| SP-20 | Revision propagation | all | R | F |

## 17.3 Procedures

### SP-01 Knowability gate
- **Task.** all.
- **Inputs.** Candidate `c` with `knowable_bar(c)`; decision bar `t`; `status(c, t)`.
- **Steps.** (1) If `knowable_bar(c) > t`, emit `X-KNOW`. (2) If `status(c, t)` is `provisional` and `Π_T` does not allow provisional use, emit `X-STATE`. (3) Otherwise pass.
- **Outputs.** Pass, or exclusion with code.
- **Provenance.** R. Principle: no selection may use information unavailable at `t`.
- **Counterexamples.** A confirmation rule that uses data from after the occurrence bar must set `knowable_bar` to the confirmation bar (SP-13). Forgetting this is the most common leak.
- **Unresolved parameters.** Whether provisional use is ever allowed (policy).
- **Validation.** Replay: recompute the selection from data truncated at `t`; results must match the stored output for every `t` in the test set.

### SP-02 Task-scale compatibility table
- **Task.** T-S6, T-S1.
- **Inputs.** Task card role; the table of allowed scale classes per role.
- **Steps.** Look up the role; allowed scales = table entry; other scales emit `X-SCALE`.
- **Outputs.** Allowed representation list.
- **Provenance.** The table is an O-class policy. Source support is S (ICT primary states higher-timeframe levels as support/resistance references; the text does not specify an entry-scale rule). Record both.
- **Counterexamples.** A role absent from the table; a higher-timeframe bar not yet closed.
- **Unresolved parameters.** Entries of the table for entry-timing roles (open, MP).
- **Validation.** Table is versioned; each change triggers SP-12 and SP-20.

### SP-03 Event binding by crossing
- **Task.** T-S2.
- **Inputs.** Closing price `C_b` of bar `b`; set `R_b` of confirmed references knowable ≤ `b`, each with view, side, and level.
- **Steps.** For each `r` in `R_b`: `r` is bound iff `C_b` is beyond `r.level` on the break side. Collect bound references. Empty → no event at these scales.
- **Outputs.** Binding set (may have several members; no ranking).
- **Provenance.** R. The "close" basis is a declared choice; a wick-based variant is an alternative (open).
- **Counterexamples.** Wick-only crossings (not bound under close basis); a crossing and reclaim within one bar.
- **Unresolved parameters.** Close vs wick basis; tie rule for `C_b = level`.
- **Validation.** Hand-checked fixtures including exact-equality and multi-view crossings.

### SP-04 Falsifier binding
- **Task.** T-S5.
- **Inputs.** Interpretation `I` written as a set of structural claims; each claim names a view and a reference role.
- **Steps.** For each claim, identify the reference whose close-based violation in the opposite direction contradicts it. If `I` has no reference-form claims, emit MP.
- **Outputs.** Falsifier set per interpretation.
- **Provenance.** R; the mapping from text to claims is an analyst act and must be recorded.
- **Counterexamples.** A descriptive word ("pullback", "impulse") with no reference form; a claim that could be falsified by two different references.
- **Unresolved parameters.** None beyond the wording of `I`.
- **Validation.** Each interpretation in file 19 has an explicit claim table.

### SP-05 Containment / escape classification
- **Task.** T-S3, item 8.
- **Inputs.** Coarse leg `c` (time interval `[t_c0, t_c1]`, price span `[p_lo, p_hi]`); fine leg `f` (interval, endpoints `e_1`, `e_2`).
- **Steps.** (1) If intervals do not overlap → `disjoint`. (2) If `[t_f0, t_f1] ⊂ [t_c0, t_c1]` and both endpoints lie within `[p_lo, p_hi]` → `contained`. (3) Otherwise → `escaping`.
- **Outputs.** Label; no relevance judgment.
- **Provenance.** R (geometry).
- **Counterexamples.** Boundary equality; fine legs that span coarse boundaries in time only.
- **Unresolved parameters.** Boundary tie rule (SWS-06).
- **Validation.** Property tests on synthetic intervals, including equal endpoints.

### SP-06 Dominance filter
- **Task.** all with a declared requirement list.
- **Inputs.** Candidates; required property list `q_1 … q_m` with boolean evaluation per candidate.
- **Steps.** Compute satisfied set `S(c)` for each candidate. Exclude `B` if there is `A` with `S(B) ⊊ S(A)` (`X-DOM`). Keep ties.
- **Outputs.** Survivors; excluded-with-reason.
- **Provenance.** R. No weights, no scores, no thresholds on counts.
- **Counterexamples.** Incomparable satisfaction sets (the common case); declared requirements that are themselves contested.
- **Unresolved parameters.** The requirement list itself (per task card).
- **Validation.** Confirm that no output depends on an ordering of the requirement list.

### SP-07 Logical consistency check
- **Task.** Combination pruning (file 15 §15.9).
- **Inputs.** A partial combination: an interpretation `I` with direction `d`, a current price `p_now`, a target reference, an invalidation reference, and entry legs.
- **Steps.** (1) Invalidation must lie on the opposite side of the current price from the target for direction `d`; otherwise `X-GEOM` (inconsistent). (2) An entry leg used for a zone must be `contained` in the leg whose structure it refines (SP-05); otherwise inconsistent. (3) If a required element is missing, not evaluable.
- **Outputs.** consistent / inconsistent / not-evaluable, with the failing clause.
- **Provenance.** R. These are logical requirements of the declared task cards, not claims about the market.
- **Counterexamples.** An interpretation whose target is not a price level; a combination where the invalidation and target coincide.
- **Unresolved parameters.** None.
- **Validation.** Each clause has a passing and a failing fixture.

### SP-08 Entry-leg window
- **Task.** T-S3.
- **Inputs.** Coarse leg (time interval); fine legs.
- **Steps.** A fine leg is in the window iff its interval lies inside the coarse leg's interval and it is knowable by the decision bar. Length of the window is not a parameter.
- **Outputs.** In-window set.
- **Provenance.** R.
- **Counterexamples.** Entries taken after the coarse leg has been broken (its window closes by SP-03 event, not by time).
- **Unresolved parameters.** None (window is structural, not temporal).
- **Validation.** Fixtures with entries before and after a break.

### SP-09 Order-block validation (trade-through)
- **Task.** OB validation tasks.
- **Inputs.** Candidate order-block candle `o` (bullish or bearish per the source's rule); later bars.
- **Steps.** Validated at the first later bar `v` whose high exceeds the high of `o` (bullish case, per the transcript's "later candle trades through its high" wording). Pre-validation status otherwise.
- **Outputs.** Validated bar `v`, or pre-validation status.
- **Provenance.** P1 (ICT primary, chunk 0 of the OB transcript; auto-caption, verified against the text read; see file 05 §5.4a). Class S.
- **Counterexamples.** Close-based trade-through (not stated in source); wick-only pierce that does not trade through the high.
- **Unresolved parameters.** Trade-through basis (wick vs close) — open choice P-V (file 05).
- **Validation.** Confirm the wording against all chunks before treating P1 wording as full doctrine; chunks 1–4 remain unread (file 14, §14.6).

### SP-10 Order-block stop reference
- **Task.** OB stop tasks.
- **Inputs.** Candidate order-block candle `o`.
- **Steps.** Stop reference = low of `o` in the bullish case (P1 wording: "the low of the bullish order block"). The source's 50% stop-raise reference uses "order block total range", which is undefined in the text.
- **Outputs.** Stop reference level; or unresolved (AI) for the 50% reference.
- **Provenance.** P1 (S class). The 50%-reference definition is UN-11 (file 10).
- **Counterexamples.** Candles with very small body range; definition of "total range".
- **Unresolved parameters.** UN-11 (total range), P-L/P-C (candle selection readings, file 05 §5.4a).
- **Validation.** As SP-09.

### SP-11 FVG three-candle geometry
- **Task.** FVG tasks.
- **Inputs.** Three consecutive closed candles `a, b, c`.
- **Steps.** Bullish gap: low(c) > high(a), with `b` as the middle candle. Bearish is symmetric. The gap span is `[high(a), low(c)]` (bullish). Optional lower-timeframe confirmation requires a definition of the "void" that the source's wording leaves open.
- **Outputs.** Gap candidate; LTF-confirmation status = unresolved (AI) unless defined.
- **Provenance.** Geometry R; source definition S (FVG lesson, chunk 0, auto-caption; verify before quoting).
- **Counterexamples.** Gaps caused by session breaks or data gaps; missing candles.
- **Unresolved parameters.** Void definition for LTF confirmation; data-gap handling policy.
- **Validation.** Fixtures with gap, no-gap, and data-gap cases.

### SP-12 Sensitivity analysis protocol
- **Task.** all parameterized procedures.
- **Inputs.** Procedure; declared parameter ranges (chosen by analyst, recorded).
- **Steps.** Run the procedure over a grid of declared values; record which outputs change. Report the set of parameter values for which the output changes, not an "optimal" value.
- **Outputs.** Sensitivity report.
- **Provenance.** R. Explicitly not parameter optimization against outcomes (see file 18, objective C constraints).
- **Counterexamples.** Grids chosen so as to hide sensitivity.
- **Unresolved parameters.** Grid bounds — these are analyst declarations, must be stated.
- **Validation.** The report must be reproducible from its declared grid.

### SP-13 Turning-point confirmation status
- **Task.** T-S1, item 9.
- **Inputs.** Candidate turning point with occurrence bar; confirmation rule of its family (F-K: right-window closed; F-T: reversal amount reached; F-C: closes-only variant).
- **Steps.** Status = `confirmed` at the first bar where the family's confirmation rule holds, `provisional` before that. `knowable_bar` = confirmation bar. Supersession per SWS-04c.
- **Outputs.** Status history; knowable bar.
- **Provenance.** R.
- **Counterexamples.** A confirmed point later superseded under a family that permits supersession after confirmation (declare which families permit this; default in this foundation: none, to be decided).
- **Unresolved parameters.** Family parameters (`k`, `τ`); whether confirmed points can be revised.
- **Validation.** Replay consistency (SWS-04d).

### SP-14 Leg construction
- **Task.** item 2.
- **Inputs.** Ordered confirmed or provisional points.
- **Steps.** Pair consecutive points of alternating side. Direction = from low to high (up) or high to low (down). `knowable_bar` = max of endpoints' knowable bars. Drop pairs of same side (not legs).
- **Outputs.** Leg list with status = min status of endpoints.
- **Provenance.** R.
- **Counterexamples.** Same-side consecutive points after supersession; gaps in the sequence.
- **Unresolved parameters.** None.
- **Validation.** Alternation property test.

### SP-15 Retracement base
- **Task.** T-S4.
- **Inputs.** Current price; legs of the view.
- **Steps.** Base = the most recent confirmed leg whose direction is opposite to the current retracement direction (operational rule; alternatives are open).
- **Outputs.** Base leg or unresolved (MP/IC).
- **Provenance.** O-class (researcher declaration).
- **Counterexamples.** Retracements that began before the most recent leg; multiple candidate bases.
- **Unresolved parameters.** Choice of base rule (O).
- **Validation.** Report the base under two declared rules; difference is a finding, not an error.

### SP-16 Representation-dependence reporting
- **Task.** T-S6, item 10.
- **Inputs.** Task; set of admissible representations.
- **Steps.** Run the task under each admissible representation. If outputs agree, report the agreement. If they differ, report each output with its representation ID and do not merge.
- **Outputs.** Per-representation outputs and an agreement flag.
- **Provenance.** R.
- **Counterexamples.** Agreement that is an artifact of shared inputs (report it as such).
- **Unresolved parameters.** The admissible set.
- **Validation.** Case W9 (file 19).

### SP-17 Liquidity taken status
- **Task.** Liquidity tasks.
- **Inputs.** A liquidity candidate level `L` on a side (buy-side above, sell-side below); bars after its occurrence.
- **Steps.** Taken-by-wick at bar `b` iff the high (buy-side) or low (sell-side) of `b` crosses `L`. Taken-by-close iff the close crosses `L`. Report both, separately.
- **Outputs.** Two flags with bar index of first occurrence; never a merged "taken".
- **Provenance.** R for definition. The naming of buy-side and sell-side liquidity follows secondary sources (E*, community; file 04 §4.7 caution). Primary ICT wording on liquidity locations is contested (CF-05, IC-06).
- **Counterexamples.** Wicks through levels with no close-back; equal-highs clusters where the level is undefined.
- **Unresolved parameters.** Cluster tolerance for "equal" levels (O).
- **Validation.** Fixtures for wick-only and close-based taking.

### SP-18 Declared policy registry
- **Task.** all.
- **Inputs.** Each policy name used in any `Π_T`, `X_T`, or procedure.
- **Steps.** Each entry records: policy ID; statement; value (or "unset"); reason it is a policy and not a fact; sensitivity report reference (SP-12); owner-approved status (not implied).
- **Outputs.** Registry (a table in the implementation).
- **Provenance.** R.
- **Counterexamples.** A policy presented in output without its registry ID.
- **Unresolved parameters.** All values; none are set here.
- **Validation.** Every output that uses a policy cites its registry ID.

### SP-19 Unresolved-state emission
- **Task.** all.
- **Inputs.** Survivor set after SP-06, `Π_T` check result.
- **Steps.** If survivors > 1 and no `Π_T` applies, emit unresolved with the set, the applicable reason code from file 15 §15.7, and the evidence needed to resolve it. If the survivor set is empty, emit exclusion summary and reason. Never pick silently.
- **Outputs.** Unresolved state object.
- **Provenance.** R.
- **Counterexamples.** A reason code that is wrong (e.g., MO used when the data exists); reviewers must check codes.
- **Unresolved parameters.** None.
- **Validation.** Every unresolved output passes the schema in file 19 §19.1.

### SP-20 Revision propagation
- **Task.** all.
- **Inputs.** Changed status or selection `s`; dependency graph (file 15 §15.8).
- **Steps.** Mark dependents; recompute in topological order; log before/after; never patch in place.
- **Outputs.** Revision log.
- **Provenance.** R.
- **Counterexamples.** Cycles in the dependency graph (should not exist by §15.10; a cycle is a defect).
- **Unresolved parameters.** None.
- **Validation.** Case W8 (file 19) includes a propagation log.
