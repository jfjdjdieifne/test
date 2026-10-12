# 19 — Worked Selection Cases (R2)

Purpose: show the method of files 15–17 applied to concrete states. These are **constructed fixtures**, not market observations. Levels are ordinal symbols (higher number = higher level); bar indices are labels. No case states a market price, a probability, or a trading outcome.

Case labels: W1–W10 and O1–O2 (this file); CASE-01 … CASE-08 (file 08) are a separate namespace. The earlier `CH-0n` labels are retired (file 13, §13.3). Cases are not claims and carry no claim IDs; the claims they illustrate are cited by their IDs (SWS-*, SP-*, LRN-*).

## 19.1 Unresolved-state schema

Every unresolved output has these fields:

| Field | Content |
|---|---|
| `state_id` | Unique identifier |
| `task` | Task card ID (e.g., T-S3) |
| `decision_bar` | Bar index `t` |
| `survivors` | Candidate IDs remaining, with representation IDs |
| `excluded` | Candidate ID + `X-*` code for each exclusion |
| `reason_code` | One of MO, MP, AI, IC, EP, OOD (file 15 §15.7) |
| `evidence_needed` | What would resolve it, typed by reason code |
| `policy_refs` | Registry IDs of any declared policies (SP-18) |
| `provenance` | Per-step class and source |
| `dependents_blocked` | Conclusions not computed because of this state |

## 19.2 Shared fixture dataset (used by W1–W10)

Coarse view **C** (representation family F-K, parameter `k` declared, unspecified here). Confirmed points, with `knowable_bar` in parentheses:

- `L_a` low, occurrence bar 10, level 10 (knowable 15)
- `H_a` high, bar 20, level 40 (knowable 25)
- `L_b` low, bar 30, level 20 (knowable 35)
- `H_b` high, bar 40, level 50 (knowable 45)

Coarse legs: Leg1 `L_a→H_a` (up), Leg2 `H_a→L_b` (down), Leg3 `L_b→H_b` (up).

Fine view **F** (a finer representation; points inside Leg3's time window):

| Fine leg | Direction | Occurrence | Endpoints (level) | Knowable |
|---|---|---|---|---|
| fA | up | 30→33 | 20→35 | 34 |
| fB | down | 33→36 | 35→25 | 38 |
| fC | up | 36→38 | 25→42 | 40 |
| fD | down | 38→39 | 42→22 | 41 |
| fE | up | 39→40 | 22→50 | 42 |

Decision bar for W1–W3, W6–W7, W9–W10 is `t = 52`. Current close at bar 52: level 30. Bars 53+ are added only in W5 and W8.

Note: fB's low (25) and fD's low (22) are both inside Leg3's price span [20, 50] and inside its time window [30, 40]. Both are `contained` by SP-05.

---

## W1 — Structural reference for the current leg (definite)

- **Priority item:** 3 · **Task:** T-S1 · **Class of result:** definite only conditional on view C and on the declared policy P-ORIGIN (unvalidated; not an ICT-source claim).
- **Observed state at t=52:** confirmed coarse points knowable ≤ 52: `L_a, H_a, L_b, H_b`. Last confirmed leg: Leg3 (`L_b→H_b`, up).
- **Question:** which confirmed point is the reference for the current state of view C?
- **Candidates:** `L_a`, `H_a`, `L_b`, `H_b`, all in view C. Fine points are excluded by `X-SCALE` (not in view C).
- **Hard requirements `H_T`:** confirmed; knowable ≤ t; in view C.
- **Policy `Π_T`:** role `origin-of-last-confirmed-leg` = origin of the most recent confirmed leg (SWS-02; O-class, registry entry required).
- **Exclusions:** `L_a`, `H_a`, `H_b` excluded under `X-POL` (not the origin of the last confirmed leg). `H_b` is the end of that leg, not the origin.
- **Result:** `L_b` (level 20). Justified selection: one survivor after `Π_T`.
- **Provenance:** `Π_T` is O-class (researcher declaration); no ICT source is cited for the choice of role.
- **Dependent conclusions:** T-S5 falsifier for "view C remains up" = `L_b`; T-S4 retracement base for coarse pullbacks (Leg3 is the last up-leg).
- **Sensitivity:** if view C is replaced by F-T with a declared amount, the last confirmed leg and its origin may change (see W9).

## W2 — Entry-timing leg with preserved ambiguity

- **Priority items:** 7, 8 · **Task:** T-S3 · **Class:** ambiguity preserved (MP/EP).
- **Question:** which completed fine leg, contained in the coarse up-leg Leg3, times a long continuation entry?
- **Step 1 (SP-05, containment):** fB and fD are both `contained` in Leg3. fA is contained too but is an up-leg. fC and fE are up-legs. All three are excluded under `X-POL`, by the declared task condition that a continuation-long entry uses completed down-legs inside the up-leg (O-class; registry entry required). Without that condition they would survive and the case would be broader.
- **Step 2 (SP-01, knowability at 52):** fB (38), fD (41) pass.
- **Step 3 (SP-08):** both inside the window.
- **Step 4 (SP-06, dominance):** both satisfy the same `H_T` set (completed, contained, down-leg, knowable). No strict superset relation. Neither dominates.
- **Survivors:** fB and fD. Their difference is factual (fD is deeper: low 22 vs 25; fD is more recent: knowable 41 vs 38). Whether depth or recency matters is not a fact. It is a policy or an empirical question.
- **Result:** unresolved, reason **MP** (if the task requires one) or **EP** (if a learned preference would be needed). Emit the unresolved schema (§19.1): survivors `[fB, fD]`, excluded `[fA, fC, fE: X-POL (continuation-entry condition)]`, `evidence_needed`: a declared recency-vs-depth policy with sensitivity analysis (SP-12) or annotated preference data (file 18, objective B).
- **Dependents blocked:** zone boundaries from fB vs fD; fine-scale sell-side liquidity below each.
- **Why this is not a silent pick:** choosing fD because it is deeper would embed a preference the source does not state.
- **Source note:** the ICT order-block transcript describes using "the lowest down candle" for selection (file 05, P-L/P-C). It does not decide this case: it governs order-block candle choice, not entry-timing leg choice across fine legs. This is an S-class limit, recorded as such.

## W3 — The same bars, a different task, a different reference (task change)

- **Priority item:** 5 (and 3, 7) · **Tasks:** T-S5 (falsifier) and T-S3 (entry timing).
- **Interpretations written in reference terms (SP-04):**
  - `I1` = "view C remains in an up-structure."
  - `I2` = "the current fine pullback has not yet resolved upward."
- **T-S5 for I1:** the falsifier is `L_b` (level 20). A close below it contradicts the higher-low structure of view C. Definite, given I1.
- **T-S5 for I2:** the falsifier is fD's low (level 22). A close below it contradicts the claim that the fine pullback has resolved in the stated place. Definite, given I2, but I2's wording is one analyst's translation of "pullback", and the translation is recorded.
- **T-S3 for the same bars:** unresolved between fB and fD (W2).
- **Contrast:**

| Task | Reference used | Status |
|---|---|---|
| T-S5 for I1 | `L_b` (level 20, coarse) | Definite given I1 |
| T-S5 for I2 | fD low (level 22, fine) | Definite given I2 |
| T-S3 | fB or fD | Unresolved (W2) |

- **Result:** changing the question changes the reference set. A reference chosen for "structure intact" is not reused for "entry timing" without a new selection.
- **Dependents:** invalidation for any zone built on I2 uses the fine reference; invalidation of I1 uses the coarse reference. They are not merged.

## W4 — A provisional point, confirmed later (branches)

- **Priority item:** 9 · **Task:** T-S1 · **Class:** IC at t, then branch-dependent.
- **Extension:** after H_b, a coarse down-leg confirms a low `L_c` (level 28, occurrence 48, knowable 56). A provisional high `H_p` (level 55) occurs at bar 60 and is confirmed at bar `60 + k` (k the declared family parameter; the value is not given).
- **Output at t = 59:** the last confirmed coarse leg is `H_b→L_c` (down). The origin of the current leg for T-S1 is `H_b`. `H_p` does not yet exist.
- **Output at t = 60 + k − 1:** `H_p` is provisional. Under SP-01 and SWS-04a it is excluded by `X-STATE` unless `Π_T` allows provisional use. Default output: the reference is `H_b`, tagged with status `last-confirmed`. Reason note: IC (the newest extreme is not yet confirmed).
- **Branch A (no higher high in the window):** `H_p` is confirmed at `60 + k`, knowable at that bar. From then on, T-S1 returns `H_p` as the new reference. The earlier output (`H_b` at `60 + k − 1`) stays in the log.
- **Branch B (higher high at bar 62, level 58):** `H_p` is superseded (`X-SUPER`, SWS-04c). The new candidate, with occurrence 62, is confirmed at `62 + k`. Until then, the output is again `H_b` with IC.
- **Replay check (SWS-04d):** recomputing from data truncated at `60 + k − 1` must reproduce the stored output. Any difference is a leak.
- **Provenance:** R (SP-13, SP-20).

## W5 — A break event with competing references

- **Priority item:** 4 · **Task:** T-S2 (binding) then a task-level question about reversal.
- **Extension:** bar 53 closes at level 19 (below `L_b` = 20, below fD's low = 22, below fB's low = 25).
- **Binding (SP-03, close basis):**
  - View C: `L_b` is crossed. Binding set = {`L_b`}. Singleton.
  - View F: fB low (25) and fD low (22) are both crossed. Binding set = {fB-low, fD-low}.
- **Step 2, task "does view C's up-structure break?"** Under the declared close basis, `L_b` is broken. Definite under that basis. The basis itself is an open choice (wick vs close; SP-03; the analogous trade-through choice is P-V in file 05 §5.4a).
- **Step 3, task "is there a trend reversal?"** The binding does not decide this: whether a close beyond one reference, without reclaim, constitutes reversal is an interpretive choice (AI). Emit unresolved, reason **AI**. Evidence needed: a source-faithful reading with a timestamp, or a declared reversal policy.
- **Dependents blocked:** any statement that "the trend has reversed" and any zone or target that depends on that statement. Propagation: the view-C state changes at bar 53 (SP-20), and all conclusions that depend on W1's `L_b` as the active up-structure are recomputed.
- **Note:** under the earlier decision bar `t = 52`, these binding results do not exist yet. Using them at 52 would be a leak (SP-01).

## W6 — Liquidity relevance depends on the structural reading

- **Priority items:** 3, 5 · **Task:** liquidity relevance (LQ), factual flags only.
- **Candidates at t = 53 (after W5):**

| Candidate | Side | Level | Taken by wick? | Taken by close? |
|---|---|---|---|---|
| `H_b` | buy-side | 50 | no | no |
| `H_a` | buy-side | 40 | yes (bar 40 high 50) | no |
| `L_a` | sell-side | 10 | no | no |
| `L_b` | sell-side | 20 | yes (bar 53 low 19) | yes (bar 53 close 19) |
| fD low | sell-side | 22 | yes | yes |

(Flags computed with SP-17. Taken-by-wick and taken-by-close are separate.)

- **Reading R-up (view C intact, W1):** the relevant "objective" above is `H_b` (untaken extreme of the current leg). Relevance set = {`H_b`}.
- **Reading R-down (view C broken, W5):** relevant objectives are sell-side levels below: `L_a` (untaken), with `L_b` and fD already taken.
- **Result:** the relevant set flips with the reading. Neither set is shown as "the" liquidity. Output: two conditional sets, reason **AI** for choosing between readings.
- **Source note:** the source ideas about buy-side and sell-side liquidity come from secondary sites (file 04 §4.7). Liquidity locations are contested (CF-05 / IC-06). This case uses the definition in SP-17, not a claim about where liquidity "is".

## W7 — Several fair-value gaps in different movement phases

- **Priority items:** 2, 8 · **Task:** zone candidate relevance for a long-continuation entry.
- **Candidates (SP-11 geometry):**
  - FVG1: bullish gap at bars 12–14, span [12, 14], below Leg3's price span. Traded through by bar 16 (low 9). 
  - FVG2: bullish gap at bars 31–33, span inside [20, 50], inside Leg3's time window.
  - FVG3: bearish gap at bars 41–43, inside the time window of the current retracement (after H_b), span inside [20, 50].
- **Factual exclusions (SP-05, SP-17):**
  - FVG1: excluded by two factual facts: its price span lies outside Leg3's span, and it is traded through by bar 16 (status `filled`). Recorded as `X-STATE` (status) and an outside-span note. The exclusion of filled gaps for entry tasks is itself a declared O-class policy, so the case also records it under `X-POL`.
  - FVG2: passes.
- **FVG3 under two readings:**
  - If the task card declares a direction-match policy (long-continuation uses bullish zones only): FVG3 is excluded under `X-POL`. Result: FVG2 definite, conditional on that policy.
  - If no such policy is declared: FVG3 survives. Result: unresolved, reason **MP**, survivors {FVG2, FVG3}.
- **Note on example policies:** the direction-match policy, the filled-gap exclusion, and the continuation-entry condition used in W2 and W7 are illustrative declarations. None is recommended, and each must be recorded in the policy registry (SP-18) before use.
- **Why the direction-match policy is not a fact:** FVG definitions (file 04, file 05) describe gap geometry and do not state which gap direction is relevant for which entry phase. Any such mapping is O-class.
- **Dependents blocked:** the zone used for the entry; invalidation derived from the zone's boundary.

## W8 — An older reference regains relevance after a later event

- **Priority items:** 3, 4 · **Task:** T-S1 for the new state, and dependents.
- **At t = 52:** `L_a` (level 10) excluded under `X-POL` from the "origin of current leg" role (W1).
- **Extension:** bar 53 breaks `L_b` (W5). View C's last confirmed leg is now a down-leg from `H_b`. Under the same `Π_T` ("origin of last confirmed leg"), the origin is now `H_b`.
- **Effect on `L_a`:** `L_a` is no longer excluded by the origin rule for the current role. Its role changes: it is the most recent confirmed sell-side extreme below the current close, so it is a candidate in the liquidity relevance set (W6, reading R-down).
- **Propagation log (SP-20), abbreviated:**
  1. Status of `L_b`: active structure → broken (bar 53).
  2. T-S1 result for view C: `L_b` → `H_b` (origin of last confirmed leg).
  3. T-S5 falsifier for I1: `L_b` → invalid (I1 is contradicted by the break; the interpretation's status changes, not its wording).
  4. Liquidity relevance set: recomputed under R-down.
  5. Zones dependent on W1's view-C state: recomputed; W7's FVG2 remains as a geometric fact but its relevance status changes with the task (not computed here).
- **Result:** a reference excluded earlier becomes relevant without changing its own data; the change comes from the later event and the declared policy.

## W9 — Two admissible representations, two answers

- **Priority item:** 10 · **Task:** T-S6 and T-S1.
- **Setup:** view C under F-K (declared `k`) and under F-T (declared amount `τ`). Both are admissible for the same role.
- **Outputs:**
  - Under F-K with the window in W1: confirmed points as in W1. `L_b` is the origin.
  - Under F-T with a declared `τ` larger than the decline from `H_a` to `L_b` (ordinal drop 20 in fixture units): the reversal that would confirm `L_b` does not register. The last confirmed low is `L_a`, and the origin of the current leg is `L_a`.
  - The value `τ` is illustrative. No parameter value is recommended.
- **Result:** two outputs with two representation IDs. Not merged. Reason **MP** (representation choice). Agreement is reported (SP-16) as "disagree".
- **Dependents blocked:** any downstream conclusion that uses the origin.

## W10 — Singleton binding (definite)

- **Priority items:** 4, 8 · **Task:** T-S2 for a fine-scale event.
- **Event:** bar 47 closes at level 24.
- **Binding (SP-03, close basis):**
  - Fine references knowable ≤ 47 on the downward side: fB low (25), fD low (22), `L_b` (20, in view C).
  - Crossed by close 24: fB low (24 < 25). Not fD (24 > 22). Not `L_b` (24 > 20).
  - Binding set = {fB low}. Singleton.
- **Result:** the event at bar 47 binds to fB low only. Definite under the close basis.
- **Consistency:** the event at 47 precedes decision bar 52 and is therefore available. The binding is a statement about bar 47 and does not depend on bar 52.
- **Note:** a singleton binding does not say the fine structure "broke". Interpretation of the event is a separate task (W5 pattern).

---

## O1 — Order-block candidate with an undefined stop reference (ICT primary, S-class)

- **Task:** OB candidate validation and stop reference.
- **Candidate:** a bearish-to-bullish candle selected by the source rule "lowest down-close candle near support" (file 05 §5.4a; P-L and P-C readings).
- **Validation (SP-09):** trade-through of the candle's high at a later bar. If present, validated at that bar. Outcome: validated (S-class, P1 wording, trade-through basis is open P-V).
- **Stop (SP-10):** candle low (P1 wording). Definite under P1.
- **50% reference:** "50 percent of the order block total range." The total range is undefined in the source (UN-11). Emit unresolved, reason **AI**. Evidence needed: a re-reading of the source with a timestamp, or a declared definition recorded as an O-class policy.
- **Candle selection:** the attachment of "lowest" is ambiguous (P-L, P-C). If several candles satisfy the rule, emit unresolved, reason **AI** (not MP, because the source rule itself is ambiguous).
- **Provenance:** P1 (auto-caption; wording verified against the text read; chunks 1–4 unread).

## O2 — FVG with a lower-timeframe confirmation condition (S-class, unresolved)

- **Task:** FVG candidate with optional LTF confirmation.
- **Geometry (SP-11):** the three-candle gap is definite (R).
- **LTF confirmation:** the source's wording about a lower-timeframe "void" is not defined in the text read. Status: unresolved, reason **AI**.
- **Result:** gap candidates are emitted with status `LTF-unconfirmed (AI)`. They are not treated as confirmed or rejected.
- **Provenance:** S (FVG lesson, chunk 0, auto-caption; verify before quoting).

---

## 19.3 Coverage matrix

| Case | Priority items | Task(s) | Result class |
|---|---|---|---|
| W1 | 3 | T-S1 | Definite (conditional on `Π_T`) |
| W2 | 7, 8 | T-S3 | Preserved ambiguity (MP/EP) |
| W3 | 3, 5, 7 | T-S5, T-S3 | Task change |
| W4 | 9 | T-S1 | IC, branch-dependent |
| W5 | 4 | T-S2 | Definite binding; AI for reversal |
| W6 | 3, 5 | LQ relevance | Conditional; AI |
| W7 | 2, 8 | Zone relevance | Definite for FVG2; MP for FVG3 |
| W8 | 3, 4 | T-S1, propagation | Role change after later event |
| W9 | 10 | T-S6, T-S1 | Representation dependence (MP) |
| W10 | 4, 8 | T-S2 | Definite singleton |
| O1 | — | OB validation/stop | S-class; AI for 50% reference |
| O2 | — | FVG LTF | S-class; AI |

Swing/wave full paths (observed → candidates → task → comparison → selection or unresolved → dependents): **W1, W2, W3** (plus W4 for the provisional case). Definite: W1, W5 (binding), W10. Preserved ambiguity: W2, W6, W7. Task change: W3, W8.

Dependency check for the cases: each case uses only data knowable by its decision bar, and each unresolved output has a reason code and evidence list (file 15 §15.7, §19.1).
