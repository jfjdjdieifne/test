# 08 — Applied Chart Cases

## 8.1 Scope and honesty statement

- No chart image or video frame was viewed. Chart cases here are drawn from **transcript text** of two primary ICT lessons (partial reads) and from **labeled hypotheticals** that use symbolic labels (no numbers). Nothing here is a verified market example.
- No timestamps are verified. Where a case would normally cite a timestamp, it says `timestamp: not verified`.
- Transcript artifacts are noted; the numbers read from transcripts are not used.

## 8.2 Case format

Each case states: source and grade · declared task · scale(s) · observables · candidate set · what each candidate implies · what the source establishes · knowability at the decision point · what remains unresolved.

---

### Case CH-01 — Fair value gap as a range with an offered side (ICT FVG lesson)

- **Source:** ICT Mentorship Core Content – Month 04 – ICT Fair Value Gaps FVG (YouTube `FgacYSN9QEo`). Uploaded 2022-09-10; description says the content is from December 2016. Grade P1 (partial transcript). Timestamp: not verified.
- **Declared task (as read):** explain what an FVG is and how it relates to a range of price trading.
- **Scale:** daily chart example (EUR/USD per transcript).
- **Observables (per transcript):** a down candle with a gap-like range relative to neighboring candles; wick and close characteristics of the candle to the left; the range traded by the down candle.
- **Source's reasoning as read:** the transcript states the range is one where "one side of the market liquidity is offered," and that the gap is "typically confirmed with a liquidity void on the lower time frame." It also argues that price in the example had already "traded up into" part of the range, so the source's attention shifts to other boundaries of the range.
- **Candidate set:** (i) the three-candle gap as the FVG; (ii) the sub-range that the source says was already "offered"; (iii) the candle's low-to-close range; (iv) the lower-timeframe void the source says confirms it.
- **What the source establishes:** a teaching procedure for identifying a range with a particular boundary logic. The source relies on the notion that a boundary has already been traded, which is a question of observed price path.
- **What the source does not establish:** that the gap was caused by institutional orders; a numeric gap threshold; any statistical outcome; the lower-timeframe void's definition beyond the sentence quoted.
- **Knowability:** the three-candle gap is knowable once the third candle closes. The "offered" status of a boundary depends on subsequent price traded within the range and must be tagged with its bar.
- **Competing readings:** a community reading treats any three-candle gap as an FVG (S1). The primary reading attends to offered-sides. These disagree on whether a gap that has already been partly traded is still an FVG and on what the boundary of relevance is. Preserve both (CF-09).
- **Unresolved:** operational definition of "offered," of "liquidity void," and of the lower-timeframe confirmation. Transcript quality limits the reading.

### Case CH-02 — Order block as the lowest down candle near support (ICT Order Blocks lesson)

- **Source:** ICT Mentorship Core Content – Month 04 – Orderblocks (YouTube `PIYh0CxoY9c`). Uploaded 2022-09-07; description says content is from December 2016. Grade P1 (partial transcript). Timestamp: not verified. The lesson opens by saying it is "the third teaching of eight from the december content."
- **Declared task (as read):** define a bullish order block, define its validation, define an entry technique, and define a stop placement.
- **Scale:** the lesson says the reader should use higher-timeframe support or resistance (monthly, weekly, or daily charts) for the reference.
- **Observables:** down-close candles, their range, their location relative to a support reference, and whether a later candle trades through the candle's high.
- **Candidate set (as read):**
  - The lowest down-close candle with the most open-to-close range near a support reference (primary definition).
  - The last down candle before the move (community definition, S1, not in primary text read).
  - The old low or old high used as the support reference (primary text: "a old low on a long term or higher time frame chart," or "an old high where price has moved above recently").
- **Source's reasoning as read:** validation occurs when a later candle trades through the high of the down candle. Entry is considered on a return to the candle's high after price has moved away. Stop placement is considered at the candle's low, and the 50% point of the block's range is described as a location to raise a stop after price moves away.
- **What the source establishes:** a procedure. Its wording is conditional ("is considered," "can be used").
- **What the source does not establish:** frequency of success, any sample, any statistical relationship between block features and subsequent movement.
- **Knowability:** the candle is knowable when closed. The reference is knowable when its swing is confirmed (a "old low" on a higher timeframe is knowable only after the higher-timeframe bar that defines it closes; its use while that bar is forming is a leak). The validation is knowable only when the trading-through candle closes (or, if intrabar, at the trade-through event with the caveat of PM-07).
- **Competing candidates:** if multiple down candles precede the move, the primary and community rules can select different candles. Preserve both.
- **Counterexample (hypothetical, symbolic):** the lowest down candle with most range lies far from the reference; the last down candle lies adjacent to it. The primary generator returns nothing (no candle near support); the community generator returns the adjacent candle. Neither is "the" order block until the task and definition are chosen.
- **Unresolved:** definition of "near" support; window of "the move"; body vs wick ("open to close" in the text read implies body, but the stop uses the candle's "low"); whether validation is intrabar or on close.

### Case CH-03 — Breaker block as a failed order block (community only)

- **Source:** third-party page (michaeljhuddleston.org; not verified as official). Grade S1.
- **Declared task:** explain a derivative zone.
- **Claim:** a breaker block is a failed order block that has undergone a liquidity sweep and a market structure shift.
- **Analysis:** the definition requires three prior concepts (OB, sweep, MSS). Each has its own definition conflict (CF-01, CF-02, CF-06). The breaker definition therefore inherits all the conflicts.
- **Knowability:** a breaker is known only after the failure event (close through or trade-through, per rule) and the MSS, which may occur several bars after the original OB. A breaker cannot be known at the time the original OB formed.
- **Use in this foundation:** an example of a derived concept whose validity depends on multiple unverified definitions. It is not used as a candidate generator in this version.

### Case CH-04 — Liquidity "offered" vs liquidity "resting" (two uses)

- **Source:** FVG lesson transcript (P1) and community liquidity pages (S1).
- **Observation:** the FVG transcript describes "buy side liquidity" as having been offered on a candle's low-to-close range. The community pages describe liquidity as stop orders resting above highs.
- **Analysis:** the transcript's usage refers to traded price ranges; the community usage refers to a hypothesized order cluster. The word is shared; the referent differs. A system that stores both under one label will mix an observed event with an inferred cause.
- **Action in this foundation:** store the transcript usage as `range_traded` (observed), and the community usage as `hypothesized_resting_orders` (inferred, unverified).

### Case CH-05 — Equal highs as a cluster (community definition, tolerance dependent)

- **Source:** community pages (S1/S2) describe equal highs/lows as clusters. A third-party AI-generated summary page (lilys.ai; the channel of the underlying video was not identified) describes a 4-hour chart with "two different swing points that are relatively equal or very close together" and gives video-time markers. The summary's timestamps and wording are **unverified** and are not reproduced here.
- **Analysis:** whether two lows are "relatively equal" depends on a tolerance that the sources do not define numerically in the text read. The same two lows may be a cluster at one tolerance and separate levels at another.
- **Hypothetical numeric-free example:** Lows L1 and L2 differ by a small fraction of the average bar range. Under tolerance τ1 they cluster; under a tighter τ0 they do not. The cluster label is a function of τ.
- **Counterexample:** a third low L3 is far below. L1 and L2 are a cluster for SSL purposes, but a structure reference for a different task may be L3 only.

### Case CH-06 — Hypothetical competing structure readings (symbolic)

Defined in file 03 §3.9. Included here as a chart-case template. No numbers. Labels: L_f (fine higher low), L_c (coarse higher low), bar b_break closes below L_f but above L_c. Three readings; each implies different zone and liquidity relevance; the evidence at b_break does not select one.

### Case CH-07 — Same bars, different tasks (symbolic)

Defined in file 02 §2.8. Three prior highs H_a, H_b, H_c. Each task (entry reference, invalidation, liquidity target, HTF bias) selects different candidates. Useful as a test: a selector that returns the same single high for all four tasks is probably not task-aware.

### Case CH-08 — Overlapping zones from a shared move (symbolic)

Defined in file 05 §5.11 and file 06 §6.5. An FVG and a community OB formed by the same three candles. The evidence is shared; counting them as two confirmations is a false independence error.

## 8.3 Cases the research could not verify

- The ICT Mitigation Block lesson (P2) — content not read.
- ICT lessons on market maker models and kill zones (P2, titles seen in listings) — content not read.
- Any ICT chart where the outcome is documented as a result. Such outcomes would be hindsight regardless. No result-based case is used as evidence here.
- Any community "video timestamps" — unverified.

## 8.4 Cross-case lessons

1. The same bars support several definitions. The definition is the choice; the chart does not choose it.
2. Several cases depend on a higher-timeframe reference whose confirmation time is later than the entry time. Knowability must be stored.
3. "Offered," "resting," and "traded" are different claims. Keep them separate.
4. A single word ("liquidity") can label observed events and hypothesized cause; the implementation must keep these separate.
