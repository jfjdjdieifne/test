# 05 — Fair Value Gaps, Order Blocks, and Zones

## 5.1 What these concepts represent

A **zone** is a price range attached to a time origin, used as a reference for future interaction. Three ICT-associated zone families are covered:

- **Fair value gap (FVG):** a price range left by a movement in which, per the ICT primary source read, one side of the market's liquidity is "offered" and the range is "typically confirmed with a liquidity void on the lower time frame charts" (P1 transcript, auto-caption quality uncertain). Community sources operationalize this as a three-candle imbalance.
- **Order block (OB):** a candle or candle cluster that ICT presents as the last (or lowest, see below) opposing candle before a move. The primary lesson defines it differently from most community sources (see §5.4).
- **Breaker block, mitigation block, rejection block, and other derivatives:** community-defined variants. Only the breaker block definition was read (S1). Mitigation block lessons exist in the primary ICT playlist (P2, title only).

Zones are **candidates**, not areas where orders were observed. A zone's label as "institutional" is an interpretation (E/F), not a measurement (see §5.9).

## 5.2 What is directly observable

- Candle OHLC and order (A).
- Three-candle relations: whether candle 1's high is below candle 3's low, or the reverse (B).
- Whether a later candle traded through a zone boundary (A/B).
- Whether a later candle closed beyond a zone boundary (A/B).

## 5.3 Fair value gap: definitions and operationalization

**ICT primary text (P1, FVG lesson, transcript read in part):** the transcript describes an FVG as "a range in price delivery where one side of the market liquidity is offered," and says that it is "typically confirmed with a liquidity void on the lower time frame charts in the same range of price," and that "in the same range of price price can actually gap to create a literal vacuum of trading thus posting an actual price gap." The lesson's example is described as using a daily chart. The transcript read contains a numeric fragment about the size of the range inside a down candle; because transcript numerals are artifact-prone, that figure is **not** reproduced or used as a market fact here.

**Community operationalization (S1, multiple sites, not individually verified):** a bullish FVG is a three-candle pattern in which candle 1's high is below candle 3's low; the gap is the space between them. Bearish is the mirror.

**Our operational definition (D):** `FVG_bull(t) := high[t-2] < low[t]`, gap = [high[t-2], low[t]]. Equivalent bearish mirror. Parameters: minimum gap size (unresolved; no verified value), whether gaps are required to be "unfilled" (a status), and whether the middle candle must be displacement-like (unresolved).

**What the operational definition does NOT establish:** that the gap was caused by institutional activity, that the gap will be "filled," that it is a support/resistance zone, or that it has any predictive value (CF-09). The mission prohibits "a price gap does not prove institutional activity." Apply the same rule to any gap detected in a continuous-trading series.

**Note on "gap":** in continuously traded markets, OHLC bars from one bar to the next usually do not show a true price gap; the three-candle imbalance is a pattern across bars, not a discontinuity in trading. Some markets (e.g., with session closures) do show gaps between sessions. The ICT primary lesson's example refers to a daily-chart range, so the relevant definition in that example is the imbalance, not a session gap. This distinction must be kept in implementation (scope note).

## 5.4 Order block: definitions compared

This is the central conflict in the zone family.

**ICT primary text read (P1, Order Blocks lesson, Dec 2016 content, transcript partially read):**

- "definition of a bullish order block is the lowest candle or price bar with a down close that has the most range between open to close and is near a support level"
- "validation of a bullish order block is when the high of the lowest down candle or price bar is traded through by a later formed candle or price bar"
- Entry: "when price trades higher away from the bullish order block and then returns to the bullish order block candle or price bar high" — described as a bullish entry technique.
- Risk: "the low of the bullish order block is the location of a relatively safe stop loss placement" and "just below the 50 percent of the order block total range … is also considered to be a good location to raise the stop loss."

One passage of the transcript is a recognition artifact (a phrase that does not fit its sentence). It is not used.

**Community definitions (S1, read as snippets or short pages):**

- "last opposing candle before a significant displacement move" (ictkillzone page, S1).
- "last down-close candle before an impulsive rally that breaks structure" (volity.io page, S1).
- Requires liquidity sweep before the displacement (ictkillzone, S1) — **not present in the primary text read**.
- Often requires FVG for confirmation (volity, S1) — **not present in the primary text read**.

**Conflicts (recorded, not merged):**

| Attribute | ICT primary (read) | Community (read) |
|---|---|---|
| Candidate candle | Lowest down-close candle within the relevant structure, with most range | Last opposing candle before move |
| Selection key | Lowest + most range | Last (temporal) |
| Context requirement | Near a support level (higher TF) | Break of structure / displacement |
| Sweep required | Not in text read | Required (one source) |
| FVG required | Not in text read | Preferred (one source) |
| Validation | Later candle trades through the high of the down candle | Often "unmitigated" = no close through zone (one source) |

Therefore a system that implements "last opposing candle" has not implemented the ICT primary definition, and vice versa. Both must be represented as distinct candidate generators (IC-05).

## 5.4a G-OB-P parameter register (round R2 — resolves F-04 as far as sources allow)

**Verified wording (P1, transcript re-read this round; auto-caption; opening section only; no timestamp):**

- Definition: "the lowest candle or price bar with a down close that has the most range between open to close and is near a support level."
- Validation: "the high of the lowest down candle or price bar is traded through by a later formed candle or price bar."
- Entry: "when price trades higher away from the bullish order block and then returns to the bullish order block candle or price bar high."
- Stop: "the low of the bullish order block is the location of a relatively safe stop loss placement"; "just below the 50 percent of the order block total range is also considered to be a good location to raise the stop loss."

**Body vs wick, as worded (refinement of §5.4):**

| Use in primary text | Wording | Reading | Status |
|---|---|---|---|
| Selection range ("most range") | "between open to close" | candle **body** | Verified wording |
| Validation level | "the high of" the candle | candle **high** (wick extreme) | Verified wording |
| Stop reference | "the low of the bullish order block" | candle **low** (wick extreme) | Verified wording |
| Stop-management reference | "50 percent of the order block total range" | "total range" is not defined in the text read; the most literal reading is high-to-low, but body-based is not excluded | **Ambiguous** (UN-11) |

The primary text therefore uses the body to *select* and the wick extremes to *validate* and *protect*. A generator that uses full range to select is not the primary definition.

**Parameter register.** Each parameter is either source-stated, source-ambiguous, or a declared operational policy. No numeric value is supplied.

| ID | Parameter | Status | Options | What the source does not settle |
|---|---|---|---|---|
| P-L | Meaning of "lowest" | Ambiguous | Reading L-low: bar with minimum low among qualifying bars. Reading L-base: bottom-most bar of a base cluster. Reading L-descriptive: "lowest" only describes the cluster; selection key is the body (below). | Which reading the source intends |
| P-C | How "lowest", "most range" and "near support" combine | Ambiguous | C-conjunctive: all clauses must hold for one bar (can be empty). C-prioritized: qualify by down close and nearness, then choose by one declared key. | Whether the clauses are a conjunction or a ranking. A conjunction can return nothing when the lowest bar is not the largest-body bar. |
| P-N | "Near support" | Undefined | Declared NEAR_POLICY. Options: (i) overlap of candle range with the reference band (no distance value needed, only the band); (ii) distance from a candle boundary to the reference, in a declared unit (value required, not market truth); (iii) distance in units of the candle's own range (value required). | Metric, unit, and magnitude |
| P-W | Window of "the move" that the candidate precedes | Undefined | Start: candle index. End: first of (validation bar), (opposite structure event, file 03), (declared maximum bars, policy). | The end condition and maximum length |
| P-R | Support reference | Partly stated | REF-OLD-LOW-HTF (old low on higher timeframe); REF-OLD-HIGH-RECLAIMED (old high price moved above recently). Both verbal (P1). | How the reference is confirmed and its expiry |
| P-V | Validation timing | Partly stated | Close-based (validated when a later bar closes beyond candle high) vs trade-through (any later bar's high exceeds candle high, P1 wording). Intrabar ordering undetermined at OHLC scale (PM-07). | Whether intrabar or close is intended |
| P-K | Invalidation | Not in primary text read | Community close-through (S1, separate rule). | Whether ICT invalidates by close |
| P-T | Multiplicity and ties | Not in source | Return all qualifying candidates, flag ties; never choose silently. | — |
| P-E | Empty result | Not in source | Return null with reason ("no down-close near reference in window"). Do not fall back to the nearest candle without an explicit fallback policy. | — |

**Consequence (answering F-04):** G-OB-P is not one generator. It is a family of readings. The implementation must expose the choices as variant IDs, for example `G-OB-P/L-low/C-prioritized/NEAR=overlap/V=trade-through`. Each variant is a separate candidate source. The ICT primary text does not justify choosing one variant over another, so no variant is labeled "the ICT order block."

**Symbolic illustration (hypothetical, no numbers).** Within one window there are three down-close bars: D1 is nearest to the reference and has a small body; D2 is farther and has the largest body; D3 has the lowest low but is not near the reference. C-conjunctive returns nothing. C-prioritized with key "largest body among near bars" returns D1 only if D1 is the only near bar; if D1 and D2 are both near, it returns D2. L-low with near-filter returns D1 or D2 depending on their lows. Four readings, four outputs, all consistent with the text read. That is the ambiguity, stated explicitly.

## 5.5 Movement origin and structural relation

Whatever definition is used, an OB or FVG candidate is linked to a **movement** that followed it. The relevant questions:

- Which leg (file 02) did the candidate precede?
- Did that leg break a structural reference (file 03)? If the primary definition's "near a support level" is adopted, the structural reference must be defined first.
- How much range did the subsequent leg cover relative to the candidate's own size? (D; unresolved parameter.)
- Did the subsequent movement break a reference before or after the candidate was formed? (Ordering matters; knowability.)

These relations define **origin quality features**. None has a verified universal threshold.

## 5.6 Candidate generation

**Candidate generator G-OB-P (ICT primary, D-rendered; R2):** a family of variants defined by the §5.4a register. Each variant is identified by its choices for P-L, P-C, P-N, P-W, P-R, P-V, P-E. No variant is authoritative. Example variant: `G-OB-P/L-low/C-prioritized/NEAR=overlap/V=trade-through`, which takes the qualifying down-close bars whose range overlaps the reference band, chooses the one with the lowest low, and validates on a later trade-through of its high. Its output is a candidate, not an ICT-endorsed block.

**Candidate generator G-OB-C (community, D-rendered):** for each displacement-like move, take the last opposing candle before it. Unresolved: displacement threshold, whether sweep is required.

**Candidate generator G-FVG:** as in §5.3.

Each generator must output all candidates, not one. "Which candidate is best" is not a generator property.

## 5.7 Alternatives and the "best zone" trap

The mission prohibits "choose the strongest FVG" and "choose the newest FVG" as universal rules. Accordingly:

- The newest FVG is one candidate; the largest is another; the one nearest current price is a third; the one that forms the boundary of a structural leg is a fourth. Each serves a different task.
- For order blocks, the lowest-with-most-range (ICT primary) and last-opposing (community) can select different candles in the same cluster. Both are legitimate labeled alternatives.
- Zones from different timeframes can overlap. Overlap is not a sum of evidence; it is an observation with its own status (see file 06 §6.6).

## 5.8 Zone status and invalidation

Status states to represent (D, sourced definitions differ):

- **Untested:** price has not returned to the zone.
- **Touched:** price entered the zone range.
- **Traded through:** price traded through a boundary.
- **Closed through:** a candle closed beyond a boundary (community "mitigation/invalidation" concept).
- **Expired:** a defined age or window passed (unresolved).

Each transition requires a bar and a knowability time. The ICT primary text read defines OB validation (trade-through of the down candle's high), not invalidation by close; the community definition of invalidation (close through) is an additional, separate rule.

## 5.9 What is interpretive

- Whether a zone is "institutional."
- Whether price "respecting" a zone demonstrates the presence of orders there.
- Whether a zone's origin movement is evidence of accumulation or distribution.

**Rule (F):** A zone that price reacted to is a zone that price reacted to. The reaction is observed; the cause is inferred. The mission's example applies: "A zone is institutional because price reacted there" is an unsupported claim.

## 5.10 Source evidence on zones

- ICT primary: defines OB and FVG procedurally (P1). The description is explicitly "candles, validation, entries, stops." It is a procedure, not a statistical result.
- No primary ICT source read in this session presents a measured success rate, sample, or out-of-sample test.
- No verified empirical study in this session tests FVG or OB predictive value (gap in 10; see 09 for what would be needed).

## 5.11 Examples where several zones are plausible

**Symbolic (hypothetical):** Two down candles precede a rally. The lower candle has more range; the upper candle is later and closer to the move's start. A third candle forms an FVG with the rally's first two candles.

- Primary-style OB candidate: the lower candle (lowest, most range), if near a support reference.
- Community-style OB candidate: the upper candle (last opposing).
- FVG candidate: the three-candle gap.
- If the lower candle was not near support, the primary-style generator yields nothing; the community generator still yields the upper candle. This is an explicit disagreement, not a bug.

## 5.12 Counterexamples

- **Hypothetical:** A last down candle before a rally is a tiny doji. The zone is nearly a price level; under a range-based rule its width is near zero.
- **Hypothetical:** A three-candle gap is created by one large spike candle. Gap is real under the definition, but the gap is a single-bar artifact of a thin liquidity event (a data-quality question as much as a market question).
- **Hypothetical:** A zone is traded through, then reclaimed, then traded through again. The zone's status depends on whether validation/invalidation uses the first trade-through or the close.

## 5.13 Alternatives that remain legitimate

- Primary vs community OB definitions.
- Body-based vs wick-based zone boundaries.
- Gap-based vs pattern-based FVG.
- Zones at multiple timeframes simultaneously.

## 5.14 Insufficient information

- Zone without its origin movement.
- Zone without a support/structure reference when the primary definition is used.
- Zone whose validation bar is still forming.
- FVG on a series with a missing bar (data quality) or with a session gap that is an artifact of session handling.

## 5.15 How new observations change interpretation

- Later bars can validate an OB candidate (trade-through of its high under the primary rule) or leave it unvalidated. Both states must be stored.
- A later close through a zone changes status under invalidation rules but not under trade-through-validation rules.
- A higher-timeframe bar can change the zone's context (support/structure) without changing its geometry.

## 5.16 Implications for a causal implementation

- `ZoneCandidate {family, generator_id, generator_params, origin_bars, boundaries, origin_direction, knowable_bar, validated_bar?, invalidated_bar?, status_history, linked_leg_id?, linked_structure_ref?}`.
- Keep G-OB-P and G-OB-C as separate generators with distinct IDs.
- Do not compute a single "zone score." Log features (range, distance, age, structural link) and leave the weighting to learning with explicit evaluation (file 07).
- Keep FVG and OB outputs separate even when they share candles; they share evidence (file 06 §6.5).
