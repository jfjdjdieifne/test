# 02 — Swings and Waves

## 2.1 What the concept represents

A **swing** is a candidate turning point: a bar or price level at which the recent direction of movement appears to reverse, under a stated definition. A **wave** (or leg) is a representation of movement between two chosen swings. Neither is a market fact. A swing is a *selection* made under a definition, at a scale, with a knowability time.

## 2.2 What is directly observable

- Bars and their highs and lows (A).
- The ordering of bars.

Not observable: which turning point a participant "considers" important, or whether any order rested at it.

## 2.3 What remains interpretive

- Which candidate swing is "the" swing for a task.
- Whether a swing is "significant," "structural," or "external."
- Whether a leg is part of a larger wave, a corrective move, or noise (the wave-count problem is interpretive; no verified ICT primary source in this session defines a wave-count procedure).

## 2.4 How candidate turning points are generated

Verified in the literature as families of methods (see `09_*`): fixed-window pivot detection, zigzag with a threshold, change-point segmentation, and multiscale pivot sets. Each is an **operational definition (D)**.

Candidate families and their knowability:

| Family | Definition sketch (D) | Knowable when | Unresolved parameter |
|---|---|---|---|
| k-bar pivot | High greater than highs of k bars on each side | k bars after the pivot bar | k |
| Threshold zigzag | Reversal confirmed when price moves a threshold from the extreme | At threshold crossing | threshold (price or volatility-scaled) |
| Structural pivot from closes | Local extreme on closes only | k bars after | k; close vs wick |
| Change-point boundary | Boundary from segmentation | Offline: after the whole series; Online: at detection lag | penalty / hazard rate |
| Level from prior period | Prior day/week high/low | At period close | period definition, timezone |

No family is universally correct. Each yields a different candidate set on the same data. **A system must store which family and which parameters produced each swing.**

## 2.5 Knowability is part of the definition

A swing that is confirmed only after k later bars was an *occurrence* at bar p, but *knowable* only at bar p+k. Any analysis that uses the swing at bar q with p < q < p+k uses information that was not available. This is a leakage issue, not a style issue.

Consequence for ICT-style language: a source that says "the swing low that was taken" may be describing a fact known after subsequent bars. Such statements are valid for retrospective chart reading but not for causal decisions unless the knowability time is respected.

## 2.6 Nested movement representations

Movement can be represented at several scales simultaneously. A coarse swing sequence and a fine swing sequence can coexist. Nesting is a representation choice:

- **Containment:** a fine leg lies inside a coarse leg. Measurement of "the wave" requires saying which level it is.
- **Cross-scale disagreement:** coarse and fine views imply different direction. Both are valid representations; neither has automatic priority.

Preserve both views as competing representations (see file 03 §3.8 and file 06).

## 2.7 How a swing appropriate for one task can be unsuitable for another

Same bars, different tasks:

- **Task: HTF bias.** Relevant swings are coarse, confirmed, and recent enough to represent the current regime. A fine swing is usually unsuitable.
- **Task: entry reference.** Relevant swings may be fine-scale, close to the current price, and tied to a specific zone. A coarse swing is usually too far to act on.
- **Task: liquidity target.** Relevant swings are those where resting stop-like orders are plausibly clustered, but this is a derived inference (see file 04). The "most recent" swing may not be the most obvious level.
- **Task: invalidation.** The relevant swing is the one that, if traded through, makes the current interpretation false. This is often *not* the swing that is most significant on a chart.

The point: a single "swing high" variable cannot serve all four tasks. Each task requires its own candidate set, selection rule, and justification.

## 2.8 Examples where several candidates are plausible

**Symbolic example (hypothetical, no numbers):** Bars show three prior highs: H_a (coarse, 3 days earlier, not yet traded through), H_b (medium, 1 day earlier, traded through once and reclaimed), H_c (fine, 2 hours earlier, the most recent high).

- Entry reference: H_c is the most recent and close; H_b may define the region where the last displacement occurred; H_a defines the coarse range boundary.
- Invalidation: if the current interpretation is bullish, invalidation might be the most recent higher low, not H_a.
- Liquidity target: H_a is untaken and obvious on the daily chart; H_c is taken; H_b is partly taken.
- Which is "the" swing high? The question is underdetermined without the task. Preserve all three with their task labels.

**Source-grounded example (E):** The primary ICT Order Blocks lesson (P1) says a support line "can be in the form of a old low on a long term or higher time frame chart," and that "it could be an old high where price has moved above recently." It also says "the main thing is you want to be using it on a higher time frame charts like a monthly weekly or daily" (transcript, auto-caption quality uncertain). This is a source-stated preference for coarse scale for support/resistance references, but it is a verbal instruction, not a measured performance result (G not established).

## 2.9 What the source evidence actually establishes

- ICT primary text read: it prefers higher-timeframe references for support/resistance (E, P1).
- It does not, in the text read, define a numeric swing rule, a window length, or a confirmation procedure. Those are missing.
- No empirical study was verified showing that higher-timeframe swings have better predictive value than lower-timeframe swings for any outcome. This is an open question (CF-05).

## 2.10 Was the choice knowable?

The auditor should ask for every swing reference: at what bar was it knowable under its family's definition? A later price move that "respected" a swing is not evidence that the choice was correct at the time. Reviewing outcomes after the fact is a valid research activity only if the labels are clearly marked as hindsight (file 07 §7.4).

## 2.11 Common incorrect applications

- Using the most extreme high in a window as "the" swing without stating the window.
- Re-anchoring a leg when a later bar is added, without logging that the earlier reference changed.
- Treating a single wick as a swing without a close-based or threshold-based validation (or stating that the wick definition is intended).
- Assuming a swing is more important because it is older or higher; importance is a task-dependent, unscored property (see §2.13).

## 2.12 Concrete counterexamples

- **Hypothetical:** A system defines swing high as the highest high in the prior 20 bars. This creates a swing change every time an old swing ages out of the window, even without new price action. The "structure" flips without any new market event.
- **Hypothetical:** Two fine-scale swings are 1 tick apart. Treating them as "equal highs" (a liquidity concept, file 04) is a tolerance choice, not an observation.

## 2.13 No universal importance score

The mission prohibits universal importance rules. Accordingly:

- Age, height, number of touches, volume at the swing, and time spent near the level are each candidate features.
- None is a sufficient measure of importance across tasks, scales, or instruments.
- Any combined score must be learned or validated per task and must not be presented as a universal rule (file 07).

## 2.14 Alternatives that remain legitimate

- Pivot-based and threshold-based swing families.
- Closes-only and wick-inclusive definitions.
- Coarse-scale and fine-scale references for the same level.
- Offline labeled swings for research and online causal swings for live use.

## 2.15 Insufficient information for a decision

- A swing sequence without its definition and parameters.
- Swings on a series with gaps (weekends, halts) without a stated calendar treatment.
- A coarse swing computed from partial data (e.g., the forming weekly bar) used as if closed.

## 2.16 How new observations change interpretation

- New bars can confirm a provisional swing, invalidate it, or leave it unchanged. Log each state transition.
- A new bar can make a previously "untaken" level taken. Liquidity status (file 04) must be recomputed, not assumed.
- A new coarse bar can change a fine-scale interpretation's context; the fine-scale output does not change, but its interpretation may.

## 2.17 Implications for a causal implementation

- Swing objects must have: `id`, `family`, `params`, `scale`, `direction`, `price`, `occurrence_bar`, `knowable_bar`, `status` (provisional / confirmed / invalidated), `task_tags`.
- Keep the full candidate set, not only the selected swing. Selection is a separate, logged step.
- Do not implement a universal "best swing" function. Implement candidate generators and task-specific selectors with explicit unresolved states (file 11).
