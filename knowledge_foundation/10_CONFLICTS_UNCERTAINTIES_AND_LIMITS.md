# 10 — Conflicts, Uncertainties and Limits

## 10.1 Purpose

This file records what is disputed, what is unknown, and what this research cannot support. Each item has an ID (CF-xx for conflicts, GP-xx for gaps, UN-xx for unresolved analytical questions) that is cross-referenced in `claims_index.json`.

## 10.2 Conflicts between sources (not resolved silently)

### CF-01 — Order block definition (primary vs community)
- **Primary (P1):** lowest down-close candle with most range, near a support level; validated by later trade-through of its high.
- **Community (S1):** last opposing candle before displacement; sweep required in one source; FVG preferred in another.
- **Status:** unresolved. Both implemented as separate generators (IC-05).
- **Evidence that would resolve:** none in the scope of this research; a labeled-annotation study would show agreement rates but not correctness.

### CF-02 — Market structure shift / break of structure terminology
- **Status:** the primary text read does not define MSS or BOS. Community sites disagree or are unverified. Do not adopt a definition as ICT doctrine.

### CF-03 — "Break" implies "reversal"
- **Mission prohibits** the universal rule. Community sources often imply it. No verified evidence in this research supports a universal implication.
- **Status:** unresolved; the relationship is an empirical question (LL-03).

### CF-04 — Close-based vs wick-based breaks and swing definitions
- **Status:** both legitimate D-choices. Their empirical performance is not established.

### CF-05 — Liquidity mechanism (stop clusters attract price)
- **Claim in community sources:** stop clusters at obvious levels are targeted.
- **Verified research:** microstructure studies on order-flow imbalance (OS-07) do not address chart-level stop clusters. No verified study in this session tests chart-level liquidity attraction against matched controls.
- **Status:** unsupported as a mechanism; treat as a hypothesis for testing (file 07).

### CF-06 — Sweep definition and "run vs sweep"
- **Conflicts:** wick-through vs close-back; reversal-after-N vs immediate. "Run vs sweep" depends on subsequent price (hindsight).
- **Status:** rule choice; hindsight labels must be flagged.

### CF-07 — Retracement reference levels (e.g., 50% points)
- **Source:** the ICT Order Blocks lesson text read uses the 50% of a block's range as a location for stop management (E). Community sources use 50% as a "mean threshold" (S1).
- **Status:** the use as a stop-management reference is ICT-stated (E). The claim that it predicts price is unsupported.

### CF-08 — "Displacement" and "impulsive" move definitions
- **Status:** used in community sources, no numeric standard. Any numeric threshold is a parameter, not a fact.

### CF-09 — FVG definition (three-candle imbalance vs offered-range boundary)
- **Primary (P1):** a range where one side of liquidity is "offered," typically confirmed on a lower timeframe.
- **Community (S1):** three-candle imbalance.
- **Status:** unresolved; both are candidate generators.

### CF-10 — Evaluation of alternative higher-timeframe references
- **Primary text read:** prefers higher-timeframe support/resistance references; does not describe an evaluation method for alternatives.
- **Status:** an open gap.

### CF-11 — Session and kill-zone timing claims
- **Community sources** (S1/S2) state specific session windows for "kill zones" (one page gives London and New York windows in UTC). These times depend on daylight-saving and exchange conventions, and their predictive value is unverified.
- **Status:** not used in this foundation as facts. Any session definition in an implementation must be explicit and tested.

### CF-12 — Historical vs current ICT teaching
- The primary lessons read are from December 2016 content (re-uploaded 2022). Later ICT material may differ. Attribution must use the lesson's date.

## 10.3 Gaps in the source material (GP)

- **GP-01:** Full transcripts of the two primary lessons were not read. Their later sections may define additional rules, exceptions, or alternatives.
- **GP-02:** No chart images or video frames were inspected. Any claim about what a chart "shows" is not verified visually.
- **GP-03:** No verified timestamps. Several community summaries contain timestamps that were not checked.
- **GP-04:** The ICT Mitigation Block, Market Maker Model, Divergence and other lessons were seen only as listings (P2).
- **GP-05:** No ICT primary liquidity lesson was read. The liquidity definitions here come from secondary sources and one primary-listing-level mention.
- **GP-06:** No verified empirical study of ICT concepts (FVG, OB, liquidity, breakers, kill zones) was found in this session. This is the largest evidence gap.
- **GP-07:** The academic change-point, representation, and imitation papers were read at abstract level. Full methods, experiments, and reproducibility were not reviewed.
- **GP-08:** Some foundational references (HMMs, Bai–Perron, segmentation surveys, the López de Prado book) are flagged AC2/S1 and need primary verification before citation in an audit.
- **GP-09:** Open-source licenses were not verified for ruptures and TS2Vec; purgedcv license heading empty in read content.
- **GP-10:** Intra-bar ordering is not recoverable from OHLC (PM-07). Any analysis requiring it needs finer data.
- **GP-11:** No order-book, volume-profile or tick data were examined. Any claim about participation is unsupported without them.

## 10.4 Unresolved analytical questions (UN)

- **UN-01:** What is the correct window for "the move" that precedes an order-block candidate?
- **UN-02:** What operational meaning should "near support" take, and at what scale?
- **UN-03:** What tolerance defines "equal" highs/lows, and is it task-invariant?
- **UN-04:** When multiple readings of structure coexist, which should the output emphasize for a given task? (This is a presentation policy, not a market fact.)
- **UN-05:** Does a higher-timeframe reference predict anything better than a lower-timeframe reference, for any defined outcome? (Unknown.)
- **UN-06:** Does FVG status (unfilled/partly filled) carry predictive information? (Unknown.)
- **UN-07:** Are session-based liquidity levels more informative than swing-based levels? (Unknown.)
- **UN-08:** How should overlapping zones from different scales be combined, if at all? (Unknown; presenting them separately is the default.)
- **UN-09:** What minimal dataset of annotated causal snapshots is needed to evaluate contextual selection? (Design question, file 07 §7.6.)
- **UN-10:** Is intra-bar sequencing needed for the tasks the project cares about? (Depends on task; file 01 §1.7.)

## 10.5 Limits of this research

- It does not establish that ICT concepts are valid or invalid.
- It does not establish predictive usefulness of any candidate, zone, level, or structure reading.
- It does not provide thresholds, weights, or confidence values. Where a parameter exists, it is marked unresolved.
- It does not evaluate any trading strategy, risk policy, or execution.
- It does not assess any specific instrument's market microstructure.
- Its source base is partly secondary and partly transcript-based, with transcript quality issues.

## 10.6 Hypothesis register (for future testing; not findings)

- **HY-01:** Causal structure readings at two scales, with explicit disagreement, better explain subsequent movement than single-scale readings. (Untested.)
- **HY-02:** Candidates with knowable-at-creation status produce different results from retrospective candidates in a causal evaluation. (Untested; expected by construction but the magnitude is unknown.)
- **HY-03:** Chart-level liquidity candidates are not distinguishable from matched non-level candidates in forward movement. (Untested; a null hypothesis worth testing.)
- **HY-04:** FVG and OB candidates overlap in evidence such that their joint count overstates independent support. (Structurally true for shared bars; magnitude untested.)
- **HY-05:** Offline segmentation boundaries are not reliable as live structural breaks. (Structurally expected by causality; test with causal detection.)

Each hypothesis requires a pre-registered test design (file 11 and file 07). None should be treated as a finding.
