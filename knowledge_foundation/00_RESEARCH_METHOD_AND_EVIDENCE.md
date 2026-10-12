# 00 — Research Method and Evidence

## 0.1 Purpose

This file defines how every other file in this foundation labels its claims, what sources were actually inspected, and what was not verified. An auditor should be able to start here and understand the strength of any statement elsewhere.

## 0.2 Claim categories (mandatory labels)

| Code | Category | Meaning | Example |
|---|---|---|---|
| A | Direct observation | Something present in the recorded data (OHLC bar, timestamp, volume if recorded) | "Bar 14 closed lower than it opened." |
| B | Derived measurement | Deterministic function of observations under a stated definition | "Bar 14 range = high − low." |
| C | Representation | A way of organizing movement (swing list, segment, run-length posterior) | "A zigzag series of alternating pivots." |
| D | Operational definition | A chosen, scoped rule that makes a concept computable | "Pivot = bar whose high exceeds the highs of k bars on each side." |
| E | ICT source interpretation | What an ICT source says or demonstrates, with provenance | "ICT's Order Blocks lesson defines a bullish OB as …" |
| F | Researcher-proposed principle | A reasoning principle proposed here, not stated by a source | "Knowability time must be stored with every candidate." |
| G | Empirically supported relationship | Supported by quantitative evidence in a cited study | "Order-flow imbalance has a roughly linear relation to short-horizon price change (Cont et al., 2014, on NYSE TAQ data for 50 US stocks)." |
| H | Trading decision or risk policy | Actions, sizing, thresholds for trading | Not produced by this research. |

Rule: a claim in one category must never be presented as another. In particular, E (ICT says) and G (evidence shows) must not be merged, and D (our definition) must not be presented as market truth.

## 0.3 Evidence grades

| Grade | Meaning |
|---|---|
| P1 | Primary ICT material whose transcript text was read in this session (partial reads noted). |
| P2 | Primary ICT material whose metadata/title/listing was read but whose content was not. |
| S1 | Secondary/community material read in full enough to quote. |
| S2 | Secondary material read only as search snippet. |
| AC1 | Academic paper: abstract read from the publisher/arXiv page in this session. Full text not read unless stated. |
| AC2 | Academic claim known to the researcher but not re-verified in this session. Flagged; should not be relied on without check. |
| OS1 | Open-source project page read (README/repo metadata). Code not inspected or run. |

## 0.4 Sources inspected in this session

Full list with URLs in `12_SOURCE_INDEX.md`. Summary:

- ICT FVG lesson (YouTube `FgacYSN9QEo`, "ICT Mentorship Core Content – Month 04 – ICT Fair Value Gaps FVG"): transcript text read in part (first portion of the lesson). Grade P1 (partial).
- ICT Order Blocks lesson (YouTube `PIYh0CxoY9c`, "ICT Mentorship Core Content – Month 04 – Orderblocks"): transcript text read in part (opening section covering definition, validation, entry, stop placement). Grade P1 (partial).
- ICT Mitigation Blocks, Market Maker Models, Divergence Phantoms and other Month 04/2023 lessons: titles and IDs seen in listings only. Grade P2.
- Secondary sources on liquidity, breaker blocks, kill zones, FVG, order blocks: Grade S1/S2.
- Academic: Adams & MacKay 2007 (AC1), Killick et al. 2012 (AC1 via library record; ruptures documents the algorithm), Cont–Kukanov–Stoikov (AC1), Ho & Ermon 2016 (AC1), Yue et al. TS2Vec (AC1), López de Prado purged/embargoed CV (S1 via secondary and an OS1 repo; the book itself not read).

## 0.5 Verification limits (important for the auditor)

1. **No chart viewing.** No ICT chart image or video frame was inspected. Any statement about what a chart "shows" comes from transcript text, not from the chart.
2. **No verified timestamps.** The fetch returned transcripts without time markers. No `mm:ss` reference in this foundation is verified. Where a timestamp appears in a third-party summary, it is marked unverified.
3. **Transcript quality.** The returned text contains recognition-style artifacts (e.g., "105 15", "bullet shorter block", "voltage order blocks", "we don't h"). Numeric values read from transcripts are **not** used as market facts. Provenance (manual vs auto-generated captions) of the transcript was not verified.
4. **Truncation.** Both primary ICT transcripts were cut off within their opening sections. Statements about what the rest of each lesson says are unknown, not assumed.
5. **Historical age.** The description of the two primary lessons states that the audio and visuals are "exactly as they were distributed in December 2016" (2016 Premium ICT Mentorship Core Content). ICT's later teaching may differ. Upload dates (2022) are not the teaching dates.
6. **Secondary sources disagree with each other and with the primary text read.** See `10_CONFLICTS_UNCERTAINTIES_AND_LIMITS.md`.
7. **Commercial and affiliate content.** Many search results for ICT concepts are trading-education sites with promotional content. They were treated as community interpretations only and never as evidence of market behavior.
8. **Not checked:** full ICT Mentorship curriculum, 2022–2024 ICT lectures, Mitigation Block and Market Maker Model lesson contents, the original ICT Twitter/X posts, and any ICT written material outside the videos cited.

## 0.6 Method used

1. Identify primary ICT lesson sources and read their opening transcripts.
2. Identify community definitions for the same concept and record disagreements (not resolve them silently).
3. Read academic abstracts for each methodological direction and note what each one does and does not solve (causal vs hindsight, online vs offline).
4. Extract operational definitions that make concepts computable, label each one as D (ours), and record the parameters that remain unresolved.
5. For each analytical task, define candidate generation, context dependence, competing alternatives, and insufficiency conditions (see file 11).
6. Record conflicts instead of merging them.

## 0.7 Causality discipline used throughout

Every candidate element is assigned a **knowability time**: the earliest bar index at which the element could have been known from data available at that moment. Examples:

- A pivot defined with k bars on each side is knowable only after k subsequent bars close. Its *occurrence* time and its *knowability* time differ.
- A bar's high and low are known when the bar closes, but **the order in which the high and low occurred inside the bar is not recorded in OHLC data.** Questions like "did the sweep occur before the displacement inside this bar?" cannot be answered from OHLC alone (see PM-07).
- Offline segmentation methods (e.g., PELT) use the whole series and must not be used as causal inputs for a live decision (see LL-03).

## 0.8 Claim IDs and index

Claims are listed in `claims_index.json` with: `id`, `type`, `grade`, `sources`, `scope`, `limitations`, `related`, `conflicts`. Major narrative claims in the markdown files cite these IDs in square brackets, e.g., `[SW-03]`.

## 0.9 What this method does NOT establish

- That any ICT concept has predictive value.
- That any zone, liquidity pool, or structure break is caused by institutional behavior.
- That any probability or confidence level applies to any setup. No such numbers are given in this foundation, because none were verified.
