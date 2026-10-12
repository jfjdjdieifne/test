# 06 — Multiscale Contextual Reasoning

## 6.1 What this file addresses

Files 01–05 define elements. This file addresses how an analyst (human or program) combines elements across scales and tasks into an interpretation, how such an interpretation can be wrong because of an early representation choice, and how it should be revised.

## 6.2 Principle: a checklist is a workflow, not a sequence of market events

The ICT-style presentation often reads as an order: bias → structure → liquidity → zone → entry. Market events need not occur in that order (mission §10). A workable model is:

- A set of **tasks** (questions to answer).
- A set of **candidate elements** from files 01–05.
- A **dependency graph** indicating which elements a task requires.
- An **evidence ledger** per interpretation.

The order in which elements are evaluated is an implementation choice. It should not be used as a causal claim about the market.

## 6.3 Task list (the analytical questions)

| Task ID | Question | Depends on |
|---|---|---|
| T-BIAS | Which structural readings are active at each scale? | Movement (01), swings (02), structure (03) |
| T-REF | Which swing/structure references are relevant to a given question? | T-BIAS, swings |
| T-LIQ | Which liquidity candidates are relevant as references? | T-REF, liquidity (04) |
| T-ZONE | Which zone candidates are relevant and in what status? | T-REF, zones (05) |
| T-INV | What observation would falsify the current interpretation? | T-REF, T-ZONE |
| T-REV | Has new information changed any dependent interpretation? | All |

Tasks are not mutually exclusive. They are answered in a dependency order that the implementation chooses; the market does not supply one.

## 6.4 Dependency graph and cascading errors

Example dependency chain: movement representation → swing family → structure reference → liquidity candidate → zone candidate → invalidation level.

**Cascading error:** if the first link is unsuitable, every downstream output is internally consistent but contextually wrong. Example:

- Step 1: a 1-minute zigzag with a small threshold yields a swing that is a fine-scale noise pivot.
- Step 2: the structure label is based on that pivot; a break is declared.
- Step 3: a liquidity candidate is generated from the same pivot ("equal lows").
- Step 4: a zone (OB) is selected as the last opposing candle before the "move."
- Step 5: an invalidation level is set beneath the zone.

Each step's computation is correct given its input. The chain is contextually inappropriate because step 1 chose the wrong scale for the task. The error is not visible in any single calculation.

**Mitigation (F):** store the representation choices at each step, and evaluate alternative upstream choices in parallel (see §6.7). Do not validate step N in isolation.

## 6.5 Shared evidence is not independent evidence

Multiple elements often come from the same bars. Examples:

- An FVG and an OB formed by the same three candles.
- An equal-high cluster and a swing high that is one of its members.
- A structure break and a liquidity sweep of the same level.

**Rule:** count evidence by its source bars. Two elements sharing the same bars share evidence. An evidence ledger must record a `source_bars` set and flag overlaps. Presenting "three confluences" as independent is a false independence error (mission §15).

No "confluence count" is a probability. Any statement like "three confluences imply 75% confidence" is prohibited here and is not supported by any verified source.

## 6.6 Competing interpretations and the evidence ledger

For a given question, maintain a set of interpretations, each with:

- `statement` (e.g., "coarse structure is bullish; fine structure is bearish after a close-based break")
- `supporting_observations` (bar IDs, element IDs, with knowability)
- `contradicting_observations`
- `assumptions` (e.g., "wick-based break rule", "session = New York midnight to midnight"—example only)
- `what_would_change_this` (the falsifiers)
- `status`: active / weakened / superseded / unresolved

Interpretations are not ranked by a single score. Presentation may show all active ones, with the falsifiers for each.

## 6.7 Multiple upstream representations

Run alternative representations in parallel: fine and coarse swing families, close-based and wick-based breaks, primary and community OB generators. Each run produces its own ledger. When they agree, that agreement is shared evidence unless they used disjoint bars. When they disagree, record the disagreement as the interpretive state, not as noise.

## 6.8 Contradictory information

Contradiction types:

1. **Scale contradiction:** coarse bullish, fine bearish. Not an error; a state.
2. **Rule contradiction:** close-based break says broken; wick-based says not. The rule choice decides, but the rule choice is not evidence about the market.
3. **Element contradiction:** a zone is validated but also invalidated by a close. Two rules, two statuses.

None of these should be resolved by averaging. Resolution, if needed for a downstream action, must be a separately defined policy (outside this research; see H in file 00).

## 6.9 Incomplete observations

- Partial bars at the present time: treat as unclosed, do not use for confirmed states.
- Missing bars (data gaps): mark the period as unobserved; do not interpolate structure across it without a flag.
- Missing volume or order-book data: any claim requiring them becomes "unsupported."

## 6.10 Unresolved questions and how to keep them open

An interpretation may remain unresolved after all available data is used. The output should say:

- what is unresolved,
- what observation would resolve it,
- which candidates remain plausible.

Forcing a resolution (e.g., choosing the most recent candidate) is a policy choice, not analysis.

## 6.11 Revising dependent interpretations

When a new bar arrives:

1. Recompute the status of every element whose definition depends on it (provisional swings, takes, validations).
2. Propagate status changes along the dependency graph (e.g., a swing invalidated → structure reference changes → liquidity candidate's context changes → zone relevance changes).
3. Do not overwrite prior outputs. Append a revision record with the bar that caused it.
4. For each revised interpretation, check whether the earlier decision (if any) would have been different under the new information. This is an audit of knowability, not of profit.

## 6.12 Historical references becoming relevant

A reference from weeks ago can become relevant when price returns to it. Relevance is conditional on current price and task, not on age alone. A system must not drop old references silently (memory-window choice) nor keep all references forever without relevance criteria. The window itself is a parameter; its effect must be tested (file 07).

## 6.13 Examples where interpretation is genuinely plausible in several ways

**Hypothetical:** Coarse bias up, fine structure broke down, a fine FVG formed inside a coarse OB-like candle, and a buy-side cluster sits above. Possible interpretations:

- (i) Pullback within a coarse uptrend; buy-side cluster is a target.
- (ii) Structure transition; coarse uptrend under pressure; buy-side cluster may be a failure level.
- (iii) Range; neither reading dominates.

Each has falsifiers. For (i): a close below the coarse reference. For (ii): a reclaim of the fine structure. For (iii): a clean break in either direction. The analysis is complete when all three are presented with their falsifiers and their dependence on the chosen representations.

## 6.14 Common incorrect applications

- Treating a chain of elements as a proof when each link depends on the previous link's definition.
- Counting shared-bar elements as independent confirmations.
- Using hindsight labels (e.g., "this zone held") to justify selecting it before the outcome.
- Calling a list of present elements a "setup" without stating the task it answers.

## 6.15 Concrete counterexamples

- **Hypothetical:** Three elements (FVG, OB, liquidity cluster) all trace back to a single impulsive bar. An analyst reports "triple confluence." The independent evidence is one bar.
- **Hypothetical:** A fine-scale structure break is followed by a coarse-scale structure continuation. A system that updates only the fine layer announces a reversal; a system that keeps coarse and fine layers reports a pullback. The data is the same; the representation differs.

## 6.16 Source-grounded point

The ICT Order Blocks primary lesson (P1) presents an entry procedure that depends on a higher-timeframe support reference and a validation bar. It is therefore a dependent procedure: the zone is not meaningful without the reference and validation. This is consistent with §6.4, but the lesson text read does not describe how alternative references should be evaluated, so that part is open (CF-10).

## 6.17 What the research does not establish

- That any dependency order is optimal.
- That multiscale agreement predicts outcomes.
- That an evidence ledger improves decisions. (It is a transparency device; its value is an empirical question.)

## 6.18 Implications for a causal implementation

- Build the pipeline as: candidate generators → candidate store (with knowability) → task-specific selectors → interpretation objects with ledgers → revision log.
- Make selectors explicit and swappable; log which selector and parameters produced each output.
- Expose alternatives in every output.
- Include an audit mode that re-runs the pipeline using only data available at a given bar and compares it with the logged output.
