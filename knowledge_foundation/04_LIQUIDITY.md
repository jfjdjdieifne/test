# 04 — Liquidity

## 4.1 What the concept represents

In ICT-related sources, **liquidity** usually means clusters of resting orders (typically stop orders and breakout entries) assumed to sit at obvious price levels, and **liquidity pools** are the price levels where those orders are assumed to sit. Terms in use: buy-side liquidity (BSL, above highs), sell-side liquidity (SSL, below lows), equal highs/lows, "old highs/lows," prior day/week levels, sweeps and runs.

**Status of this concept in this foundation:** an **E-level claim about what ICT-community sources say**, plus a **D/F-level operationalization**. The existence of resting orders at these levels is an *assumption of the source*, not an observation in OHLC data. A level being "liquidity" is therefore a derived candidate, not a fact (mission §3: "A swing-derived level does not prove actual resting stop orders").

## 4.2 What is directly observable

- Prices of prior highs and lows (A/B).
- Whether later bars traded through those prices (A/B).
- Whether a bar closed beyond a level (A/B).
- The count of times price touched a level within a tolerance (B, tolerance is D).

## 4.3 What remains interpretive

- That any cluster of orders exists at a level.
- Who placed them and why.
- Whether taking the level "causes" a subsequent reversal.
- Whether the level is a *target* of the move (versus incidental).

## 4.4 How liquidity candidates are generated

Each family below is an operational definition (D) that produces candidates from observable price. Each has its own parameters.

| Family | Derivation | Knowability | Unresolved parameters |
|---|---|---|---|
| Individual swing extreme | Swing high/low from file 02 | When swing confirmed | Swing family |
| Equal highs/lows (cluster) | ≥ 2 extremes within a price tolerance | When the second extreme is confirmed | Tolerance (price or ATR-scaled), minimum count, time window |
| Prior period extremes | Prior day/week/month high/low | At period close | Calendar, timezone, session boundaries |
| Session extremes | High/low of a defined session window | At session close | Session definition (dependent on exchange hours and timezone) |
| Round or psychological levels | Price levels at multiples of a unit | Known in advance | Unit choice (no verified basis for specific units in this session) |
| Range boundaries | Extremes of a defined consolidation | When range definition confirmed | Range definition (interpretive) |

**Important:** none of these families is verified to be *the* liquidity. They are candidate sets. Their relevance must be evaluated per task (§4.6).

## 4.5 Individual levels, clusters, sessions and structural references differ

- **Individual levels** have one extreme. They are sensitive to a single print and to swing family choice.
- **Clusters (equal highs/lows)** combine multiple extremes. They depend on tolerance: a tolerance choice can create or erase a cluster. A cluster is not automatically stronger than a single level. This is a tolerance-dependent property.
- **Session levels** depend on how the session is defined. A session high can be a true extreme of the day but not of the surrounding structure.
- **Structural references** (file 03) define trends; their extremes may be liquidity candidates, but the structural role and the liquidity role are different questions.

## 4.6 Evaluating relevance without claiming hidden orders were observed

Candidate attributes that a future system can compute (B) and that may be relevant to an analyst (F/E):

- **Taken status:** has a later bar traded through the level? Did it close beyond it?
- **Distance:** price distance from current price in ATR or similar units (D).
- **Scale of origin:** which timeframe produced the level.
- **Path relevance:** is the level between current price and another candidate?
- **Age:** bars since creation (D).
- **Number of touches within tolerance** (D).

No combination of these is verified to predict outcomes. Any scoring rule is an unresolved learning target (file 07). The mission prohibits a universal importance score.

## 4.7 Sweeps and runs (definition conflicts)

ICT-related community sources define a **liquidity sweep** as price trading through a level and then reversing, sometimes requiring a close back on the other side (S1). A third-party liquidity-sweep page (S1: innercircletrader.net, a site whose official status was not verified) describes buy-side and sell-side sweeps, and distinguishes a "sweep" (reversal after taking liquidity) from a "run" (continuation). In the search-snippet text read, the sweep-versus-run label is assigned according to what happens next, and a close above or below the level is described as relevant. The full page was not read.

**Conflict CF-06:** definitions of sweep differ on (a) whether a wick-only trade-through counts, (b) whether a close back inside is required, (c) whether "run vs sweep" is determined by the subsequent move (hindsight). Option (c) is not knowable at the time of the trade-through and must be labeled hindsight.

Operational versions a system could implement (all D):
1. Wick-through: high > level. Knowable at the bar.
2. Close-back: high > level and close < level (for a buy-side level). Knowable at bar close.
3. Reversal-after-N: close-back plus a later move of defined size within N bars. Knowable only after N bars.

## 4.8 Examples where several liquidity readings are plausible

**Symbolic (hypothetical):** A current bullish bias with three candidate BSL levels above price: a daily prior high (untaken), a 4-hour equal-high cluster (formed by two touches), and a 1-hour swing high (taken once, then reclaimed).

- The daily high is untaken and possibly relevant as a target.
- The 4-hour cluster may be relevant but its status depends on the tolerance chosen.
- The 1-hour level may be a sweep candidate if taken again; it may also be simply a previous high inside an ongoing move.

The available information does not select one as "the" liquidity target without a task and a stated objective. Multiple readings must be retained.

## 4.9 Source-grounded examples

- ICT primary FVG lesson (P1, partial): the transcript describes a sequence of candles where price "offered" buy-side liquidity on a candle's low-to-close range, and then "the buy side liquidity had been offered on that range." Here "liquidity offered" refers to price already traded through a range within a candle's own movement. This is a different use of the word from the community "resting stop orders" usage (E). The two uses must not be merged.
- The ICT Order Blocks primary lesson (P1, partial) refers to using support/resistance on higher timeframes, but does not, in the text read, define liquidity pools as stop clusters. The stop-cluster interpretation is community (S1).

## 4.10 What the source evidence establishes

- Community sources consistently describe BSL above highs and SSL below lows (S1). This is a naming convention.
- The mechanism (stops clustering there, institutions targeting them) is asserted in community sources. No verified empirical study in this session confirmed that these levels attract price more than matched non-levels (CF-05, gap).
- Academic microstructure (file 09) addresses order flow and price impact, not stop-cluster targeting at chart levels. It does not validate the chart-level liquidity mechanism.

## 4.11 Counterexamples

- **Hypothetical:** An equal-high cluster formed from two touches within a tolerance that is nearly the typical bar range. The "cluster" is produced by noise. Treating it as a strong BSL is a tolerance artifact.
- **Hypothetical:** A prior-day high is taken in the first minutes of a session by a news-driven move that is unrelated to any level. The sweep label implies a stop-hunt mechanism that the data does not establish.
- **Hypothetical:** A level is "swept" by a wick, but the close stays inside the prior range. Under a close-back rule this is a sweep; under a wick-through rule it is also a sweep; under a reversal-after-N rule it is not until the reversal occurs. The label depends on the rule.

## 4.12 Alternatives that remain legitimate

- Wick-based and close-based definitions of taken/swept.
- Cluster versus individual level focus.
- Liquidity as "candidate targets" versus liquidity as "explanatory cause" (the latter is unsupported as an observation).

## 4.13 Insufficient information

- No volume or order-book data: cannot assess whether a level had any participation.
- No calendar and session definitions: session levels are undefined.
- Tolerance not stated: cluster labels are not reproducible.

## 4.14 How new observations change interpretation

- A new bar can take a level; its status changes from untaken to taken. Keep the history.
- A new cluster member can create a cluster that did not exist before.
- A later close back inside can change a sweep label under a close-back rule but not under a wick-through rule.

## 4.15 Implications for a causal implementation

- Output liquidity as `LiquidityCandidate {family, level, params, source_scale, knowable_bar, taken_bar?, close_back_bar?, tolerance}`.
- Do not output "liquidity above/below" as a boolean certainty.
- Never label a candidate with a cause ("stops here") unless the label is explicitly marked as a community assumption.
- Provide alternatives in the same output: the set of candidates, not the single "target."
