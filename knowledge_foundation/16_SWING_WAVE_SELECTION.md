# 16 — Swing / Wave Selection (R2)

Depends on: `15_CONTEXTUAL_SELECTION_METHOD.md` (vocabulary, property classes, unresolved codes), `17_SEED_PROCEDURES.md` (procedure contracts), `19_SELECTION_CASES.md` (worked cases W1–W10). Claim IDs: `SWS-*`.

Terminology: "wave" here means a **leg of a declared representation** (an ordered pair of consecutive confirmed or provisional turning points). It does **not** mean an Elliott wave count, and no wave-count rule is used.

**Caveat on item lists.** The ten priority items (§16.1) and the task cards (§16.3) are the working mapping used in this round. Their exact wording must be cross-checked against the original request text before audit sign-off (see file 14, §14.6). The relation to file 06's baseline `T-*` tasks is: T-REF → T-S1, T-S5; T-REV → SP-20; T-BIAS → T-S6.

## 16.1 Priority items 1–10 (working mapping)

| Item | Question | Served by |
|---|---|---|
| 1 | Which turning points are knowable at decision bar `t` under each representation? | §16.2 layer L1, SP-01 |
| 2 | Which consecutive points form legs, with direction, endpoints, and knowability? | §16.2 layer L2 |
| 3 | What is the current structural reference for a view? | T-S1 |
| 4 | Which reference does a closed-bar break event bind to? | T-S2, SP-03 |
| 5 | What is the falsifier of a declared interpretation? | T-S5, SP-04 |
| 6 | From which leg is a current retracement measured? | T-S4 |
| 7 | Which fine leg times an entry relative to a coarse leg? | T-S3, SP-08 |
| 8 | Is a fine leg contained in, or escaping, a coarse leg? | SP-05 |
| 9 | How are provisional points handled, and when are they superseded? | SWS-04, SP-01 |
| 10 | Which scale answers a given question, and how does the answer depend on representation? | T-S6, SP-02 |

## 16.2 Representation layers

- **L1 turning-point candidates.** Three families are described abstractly; parameters are unspecified:
  - **F-K** k-bar pivot: a bar is a high (low) candidate if it is the extreme of a symmetric window of declared length. Knowable only after the window closes on the right. Parameter: window length `k` (declared policy, no default).
  - **F-T** threshold reversal: a new point is registered when price reverses from the current extreme by a declared amount. Parameter: amount `τ` (declared policy, no default; units must be declared, e.g., percent of price or ATR-multiple; no value is given here).
  - **F-C** closes-only variant: as F-K or F-T but using closing prices only. Parameter: as for the base family.
- **L2 legs.** Consecutive alternating points `(p_i, p_{i+1})`. Attributes: direction, price span, time interval, `knowable_bar = max(knowable(p_i), knowable(p_{i+1}))`.
- **L3 nesting.** Containment and escape relations between legs at different representation scales (SP-05).
- **L4 structure.** Labels over L2 under a declared view (e.g., "up-leg origin", "current leg"). Labels are view-relative.
- **L5 events.** Crossings and reclaims of L4 references by closed bars (SP-03).

## 16.3 Task cards

For each task: question · output · inputs · `H_T` · `X_T` · `C_T` · `Π_T` · procedure · unresolved outcomes · dependent conclusions.

### T-S1 Structural reference for a view

- **Question.** Which confirmed point is the reference that defines the current state of view `V`?
- **Output.** One reference (or unresolved set) with role `origin-of-current-leg` or `last-confirmed-extreme`, declared per view.
- **Inputs.** L2 legs of `V` at its declared scale, knowable by `t`.
- **`H_T`.** (1) confirmed status (provisional excluded unless `Π_T` allows, SWS-04); (2) knowable ≤ `t`; (3) belongs to `V`'s representation.
- **`X_T`.** `X-SCALE` for non-`V` candidates; `X-SUPER` for superseded points.
- **`C_T`.** Factual: `knowable_bar`, leg direction. Within-class only.
- **`Π_T`.** Declared, e.g., "origin of the most recent confirmed leg" for role `origin-of-current-leg`. This is an operational definition, not a market claim (SWS-02).
- **Procedure.** Filter, then apply `Π_T`. If the view has no confirmed leg, emit IC.
- **Unresolved outcomes.** IC (too little history); MP (no declared role for the question).
- **Dependent.** T-S5 falsifier, T-S4 base, zone context, liquidity "objective" labels.
- **Status of the policy.** `Π_T` is declared and unvalidated. It is not an ICT-source claim. Any use requires sensitivity analysis (SP-12) and a report of the main alternative rule.
- **Worked cases.** W1 (definite only conditional on the declared policy), W8 (reference relevance changes after a later event).

### T-S2 Event binding

- **Question.** Which references does a closed-bar event at bar `b` bind to?
- **Output.** Binding set, each member tagged with its view and direction.
- **Inputs.** Closing price of `b`; all confirmed references knowable ≤ `b` in every view in scope.
- **`H_T`.** Reference is crossed by the closing price of `b` on the break side; `knowable ≤ b`.
- **`X_T`.** `X-KNOW`, `X-SCALE` (only if the task card restricts the views).
- **`C_T`.** None needed when the binding set is a singleton. For a multi-member set, the output keeps all members; no ranking.
- **`Π_T`.** None by default (SP-03). A break-type policy (close vs wick) must be declared separately; it is an open choice recorded in file 10's open-question register.
- **Procedure.** Compute the crossed set; emit each member with its view. Empty set = no event at that scale.
- **Unresolved outcomes.** MP if the task requires a single view and several are crossed; AI if the source reading of "break" is needed and not declared.
- **Dependent.** Trend state of each view; falsifier evaluation; the reclaim check for later bars (a later close back across the reference is a separate event, not an edit of the first).
- **Worked cases.** W5 (competing references), W10 (singleton binding).

### T-S3 Entry-timing leg

- **Question.** Which fine-scale leg, if any, times an entry relative to a coarse structural leg?
- **Output.** A set of fine legs, each with containment label and completion status, or an unresolved set.
- **Inputs.** The selected coarse leg (from T-S1 or T-S4), fine-scale L2 legs in the same time window.
- **`H_T`.** (1) fine leg knowable ≤ decision bar; (2) contained in the coarse leg (SP-05 label `contained`); (3) completed (its second endpoint is confirmed).
- **`X_T`.** `X-KNOW`, `X-GEOM` (e.g., a fine leg whose direction is incompatible with the declared entry direction, if the task card declares one), `X-DOM`.
- **`C_T`.** Factual: endpoint prices, completion time, depth relative to the coarse leg's origin. Depth is a factual difference only; "deeper is better" is not a fact and needs `Π_T` or learning.
- **`Π_T`.** None by default. The choice between recency and depth is an open policy question (MP/EP).
- **Procedure.** Filter, apply dominance, then report survivors.
- **Unresolved outcomes.** MP or EP (typical). IC if no completed fine leg is contained yet.
- **Dependent.** Zone boundaries derived from the chosen leg; fine-scale liquidity below/above it.
- **Worked cases.** W2 (preserved ambiguity), W3 (task-changed reference).

### T-S4 Retracement base

- **Question.** From which leg is the current retracement measured?
- **Output.** One leg (or unresolved set).
- **Inputs.** Coarse L2 legs and the current price.
- **`H_T`.** The leg is the most recent confirmed leg of view `V` whose direction is opposite to the current retracement (factual given direction).
- **`X_T`.** `X-SCALE`, `X-SUPER`.
- **`Π_T`.** The "most recent opposite leg" rule is operational; state it.
- **Unresolved outcomes.** MP if the task uses a different base than the declared rule; IC.
- **Status of the rule.** "Most recent opposite leg" is a recency rule and is declared and unvalidated (SP-15). It is reported alongside its alternatives, not as a fact.
- **Dependent.** Any depth measure; zone-depth comparisons.

### T-S5 Falsifier of an interpretation

- **Question.** Which reference, if violated in a stated way, falsifies interpretation `I`?
- **Output.** One reference per interpretation, or the explicit statement that `I` has no structural falsifier and needs one written.
- **Inputs.** A written statement of `I` in terms of references, views, and direction.
- **`H_T`.** `I` is written in reference terms (if not, the output is MP and the procedure cannot run).
- **Procedure.** Map each structural claim of `I` to the reference it depends on; a claim "view V remains up" has falsifier = the reference whose close-based violation contradicts it (SP-04).
- **Unresolved outcomes.** MP (I not written in reference terms); AI (a source phrase such as "pullback" has no declared definition).
- **Dependent.** Invalidation levels; stop-side reference for zones.
- **Worked cases.** W3.

### T-S6 Scale for a question

- **Question.** Which representation scale answers question `Q`?
- **Output.** A scale class and a representation list, or unresolved.
- **Inputs.** Question `Q` written as a task card; available representations.
- **Procedure.** Map `Q`'s role to a scale class by declared table (SP-02). The table is operational policy (O). Record the representation dependence: rerun the same `Q` under each admissible representation and report whether the selection changes (W9).
- **Unresolved outcomes.** MP (no table entry); representation-dependent results are reported, not merged.
- **Dependent.** Everything downstream.
- **Worked cases.** W9.

## 16.4 Containment and escape (item 8)

- **Contained**: fine leg time interval inside coarse leg time interval and both endpoints inside coarse price span. Factual.
- **Escaping**: time overlap but at least one fine endpoint outside coarse span. Factual.
- **Disjoint**: no time overlap.

Interpretation: containment is nesting, not irrelevance. A contained leg can still time an entry (T-S3). An escaping leg is a factual event relative to the coarse leg and may be a break candidate (T-S2). Equality on boundaries (endpoint exactly equal to the span limit) needs a declared tie rule (open choice, SWS-06).

## 16.5 Provisional points (item 9)

A provisional point is a candidate whose confirmation condition is not yet met at decision bar `t`.

- **SWS-04a** Provisional points are not structural references by default. Using one requires `Π_T` to allow it, and the output must be tagged `provisional`.
- **SWS-04b** When the confirmation condition is met, the point becomes confirmed, and its `knowable_bar` is the confirmation bar (not its occurrence bar).
- **SWS-04c** A provisional same-side point is superseded (`X-SUPER`) if a more extreme same-side point occurs inside its confirmation window before confirmation. The superseded point stays in the record.
- **SWS-04d** Any output at time `t` must be identical when recomputed from data truncated at `t` (replay consistency). A difference means a leak.

## 16.6 Scale and representation dependence (item 10)

Results can differ across families and parameters. Two responses are allowed: (a) fix one representation as a declared design choice and report it; (b) keep several and report the disagreement. Merging representations into one structure without a declared rule is not allowed. Sensitivity analysis over declared parameters is a required validation step (file 17, SP-12), and its outcome is a fact about the system's behavior, not about the market.

## 16.7 Priority-item to procedure map (for implementation)

| Item | Procedure IDs in file 17 |
|---|---|
| 1 | SP-01 (knowability), SP-13 (confirmation status) |
| 2 | SP-14 (leg construction) |
| 3 | SP-02, SP-06, SP-07 |
| 4 | SP-03 |
| 5 | SP-04 |
| 6 | SP-15 |
| 7 | SP-05, SP-08, SP-06 |
| 8 | SP-05 |
| 9 | SP-13 |
| 10 | SP-02, SP-16 |

(All SP-* IDs above are defined in file 17; §17.2 of that file is the full index.)

## 16.8 Claim statements (SWS)

- **SWS-01** Swing/wave selection is representation-dependent; its outputs are valid only under a named representation.
- **SWS-02** The "origin of the most recent confirmed leg" rule is an operational definition (O), not a market fact.
- **SWS-03** Containment is a factual nesting relation; it does not by itself establish relevance.
- **SWS-04** Provisional points are excluded from structural references unless a declared policy allows them (see §16.5).
- **SWS-05** A break event binds to references by crossing; binding does not establish the event's significance.
- **SWS-06** Boundary-tie rules for containment are an open choice requiring declaration.
- **SWS-07** Recency vs depth for entry-timing legs is an open empirical or policy question (EP/MP).
- **SWS-08** Interpretations must be written in reference terms before any falsifier can be computed.

## 16.9 Dependent conclusions (K)

Changes in T-S1 propagate to T-S4, T-S5, zone context, and liquidity "objective" labels. Changes in T-S3 propagate to zone boundaries and fine-scale liquidity. Changes in T-S6 propagate to all. Propagation follows §15.8 and is always a recomputation, not an in-place patch.
