# 14 — Resolution Map, Changes, and Checks (Round R2)

This file is the audit entry point for the targeted repair round. It maps each finding to the change that addresses it, records source and evidence changes, lists the consistency checks actually run, and states what remains open. It does not restate the method; it points to files 15–19.

## 14.0 Deliverable index (A–N)

| Letter | Deliverable | Where |
|---|---|---|
| A | Patched files | §14.7 |
| B | Updated claims index | §14.3 |
| C | Resolution map (findings → changes) | §14.1 |
| D | Contextual selection methodology | File 15 |
| E | Seed procedure contracts | File 17 |
| F | Worked cases | File 19 |
| G | Dependency reasoning | File 15 §15.8, §15.9; file 16 §16.9 |
| H | Local learner design | File 18 |
| I | Unresolved choices | §14.4 |
| J | Source and evidence changes | §14.2 |
| K | Consistency checks (commands and results) | §14.5 |
| L | Exact file-change list | §14.7 |
| M | What can be implemented now | §14.8 |
| N | What needs empirical learning or evidence | §14.8 |

## 14.1 Finding → change map

**Caveat on finding text.** The audit report was not received in the workspace (§14.6). The six findings below are identified only by the titles given in the repair request. Each mapping is to the title, not to an audit quotation. This must be cross-checked against the audit text before sign-off.

| Finding (title as given) | Change in R2 | Where to check |
|---|---|---|
| **F-01** Incomplete context-to-selection procedure | New method (task cards, property classes, exclusions, comparison, justified vs unresolved states, dependency-aware combination evaluation, layered non-circular structure); swing/wave task cards; seed procedures with required fields; worked cases | Files 15, 16, 17, 19 |
| **F-02** Claim-index category and provenance defects | Provenance vocabulary and rules; non-spec grades (B, D, F, A) mapped to NOT_SOURCE_BASED; CF mapped to NOT_APPLICABLE with original kept in `grade_previous`; type corrections (MS-02, LQ-01 to E*; OS-06 G→F; PM-12, PM-13, OS-01, OS-02 G→D; FZ-06 G→CF); PM-01 sources emptied (cited paper did not support the claim); OS-08 provenance academic; rule check automated in `checks/check_r2.py` | `claims_index.json`; `checks/check_r2.py` |
| **F-03** Case-label namespace | Claim prefix `CH-*` renamed `CC-*` (CC-04, CC-OB-STOP, CC-HYPO-STRUCT); case labels `CH-0n` → `CASE-0n` in files 08, 11, 13; file 13 collision note corrected (no collision remains: the index has no `CASE-*` IDs); new worked cases use W1–W10, O1–O2 | `claims_index.json`; files 08, 11, 13, 19 |
| **F-04** Unresolved G-OB-P parameters | G-OB-P parameter register in file 05 §5.4a: P-L, P-C, P-N, P-W, P-R, P-V, P-K, P-T, P-E, each with readings and declared-policy slots, no numeric values; body/wick refinement table; generator described as a family of variants with no single authoritative generator; UN-11 and UN-12 open questions in file 10 | File 05 §5.4a; file 10 |
| **F-05** Learning-update and regression limits | Local learner design with objectives A–D kept separate; limits of learning updates (data drift, label drift, feedback loops, forgetting, non-stationary features, small strata); regression protocol (golden set, per-objective dashboards, replay buffer, shadow run, abstention monitoring, authority order, versioning, named approval) | File 18 §18.3, §18.7, §18.8; LRN-* claims |
| **F-06** Minor audit-check description inaccuracies | File 13 §13.2 rewritten to state the actual checks run, with commands; manual review is no longer described as programmatic; the "Pass" for quote matching is replaced by the re-fetch result (§14.5); the namespace note is corrected; licenses are now verified (§13.4) | File 13 §13.2, §13.4; §14.5 |

## 14.2 Source and evidence changes (J)

| Change | Source | Effect | Grade status |
|---|---|---|---|
| ICT order-block body/wick wording refined: selection uses candle body range ("most range between open to close" in chunk 0); validation and stop use high/low (wick) wording; "50 percent of the order block total range" with undefined total range | ICT Order Blocks transcript (chunk 0 re-fetched this round; chunks 1–4 unread) | File 05 §5.4a, file 17 SP-09/SP-10, file 19 O1; UN-11 | P1 retained; no upgrade |
| FVG transcript quotations verified against chunk 0 in this round (not re-fetched earlier): "one side of the market liquidity is offered", "typically confirmed with a liquidity void on the lower time frame charts in the same range of price", "traded up into", "buy side liquidity had been offered", "a daily chart" | ICT FVG transcript (chunk 0 of 3; auto-caption) | Files 05 and 08 quotations now verified; the "105 15" fragments identified as artifacts and not used | P1 retained (partial transcript, auto-caption) |
| "a old low on a long term or higher time frame chart" and "third teaching of eight" | ICT OB transcript | Not verified in chunk 0; quotations removed; paraphrased in file 08 | Downgraded from quoted to paraphrase |
| Transcript artifact phrases ("bullet shorter block", "20 pip range" as a figure, "voltage order blocks") | Both transcripts | Removed from quotations; described as artifacts in files 00 and 05 | None (not used as facts) |
| ruptures license | GitHub LICENSE page, `deepcharles/ruptures` | BSD-2-Clause (copyright 2017–2021, ENS Paris-Saclay, CNRS). Verified this round. | OS1 |
| TS2Vec license | GitHub LICENSE page, `zhihanyue/ts2vec` | MIT (copyright 2022, Zhihan Yue). Verified. | OS1 |
| purgedcv license | GitHub LICENSE page, `landtml/purgedcv` | MIT (copyright 2026, landtml). Repository commit of 2026-07-23 shown on the page. Verified. | OS1 |
| PELT wording | Documentation and paper metadata | Softened (file 01 §1.8); no claim that PELT is causal | Unchanged grade |
| Liquidity-sweep page (innercircletrader.net) | Secondary page | Reattributed to unverified-official (file 04 §4.7) | Downgraded attribution |
| Equal-lows example (4-hour) | AI-generated summary page | Attributed to the summary, timestamps not reproduced (file 08) | Downgraded attribution |
| BOS/CHoCH contrast | Secondary | Removed as unverified (file 03 §3.6) | Removed |

Not changed: source grades for the academic abstracts (AC1/AC2); no academic source was upgraded.

## 14.3 Claims index (B)

- File: `claims_index.json`, schema 1.1, revision R2.
- Claims: **142** (100 at the start of R2 plus 42 added: CSM-01…08, SWS-01…08, SP-01…20, LRN-01…06).
- Added entries use: type F (researcher, NOT_SOURCE_BASED) except SP-09 and SP-10 (type E, grade P1, ICT-primary), SP-11 (type F, grade P1, mixed ICT-primary + researcher), SP-17 (type F, grade S1, mixed researcher + secondary-community).
- Type distribution (recounted by `checks/check_r2.py` in R2): A 1, B 1, CF 42, D 8, E 7, E* 2, F 77, G 4 (total 142). Grade distribution: NOT_SOURCE_BASED 82, NOT_APPLICABLE 27, AC1 8, P1 11, S1 6, OS1 3, AC2 2, P2 1, S2 1, CF 1.
- Revision logs: each changed claim has per-field entries (from, to, round). Added claims have a `created` entry.
- Rule check: zero violations (§14.5).

## 14.4 Unresolved choices (I)

The following are deliberately left open. Each must be settled by a named decision, a source re-read, or empirical evidence, not by this foundation.

1. **Candle selection for order blocks** (P-L, P-C; file 05 §5.4a). The readings of the attachment of "lowest" and of conjunctive vs prioritized combination listed in file 05 §5.4a (P-L, P-C).
2. **Trade-through basis** (wick vs close) for validation (P-V).
3. **Total range definition** for the 50% stop-raise reference (UN-11).
4. **Lower-timeframe confirmation void** for FVG (SP-11; AI).
5. **Break basis** (close vs wick) for event binding (SP-03).
6. **Boundary-tie rule** for containment (SWS-06).
7. **Recency vs depth** for entry-timing legs (SWS-07, W2).
8. **Representation families and parameters** `k`, `τ`, and the view definitions (file 16 §16.2; W9). No values are given.
9. **Direction-match policy** for zones (W7; O-class).
10. **Liquidity reading** (R-up vs R-down; W6), and cluster tolerance (SP-17).
11. **Provisional-point policy** (whether provisional points may ever be references; SWS-04a).
12. **Budget B** for combination evaluation (file 15 §15.9). No default.
13. **Abstention and support-check policy** for the learner (LRN-05).
14. **Whether confirmed turning points may be revised** (SP-13).
15. **Interpretation of "reversal"** (W5, AI).

## 14.5 Consistency checks (K) — commands and results

All commands were run from `/home/user/test/knowledge_foundation` in this round. The script is `checks/check_r2.py` (read-only; exit status 0 on pass).

| Check | Command or method | Result |
|---|---|---|
| Claims index is valid JSON; IDs unique | `python3 checks/check_r2.py` (json.load; set size) | PASS; 142 claims; 0 duplicates |
| Provenance/grade rules (E→ICT-primary; E*→secondary-community; G→academic/open-source; P→ICT; AC→academic; OS1→open-source; NOT_SOURCE_BASED has no sources) | Same script | PASS, 0 violations |
| Related, conflict, and source references resolve (sources checked against file 12) | Same script | PASS |
| Claim-like IDs cited in markdown exist in the index | Same script; regex over `*.md`; namespaces excluded by design; allowlist of three reviewed false positives (`OB-C`, `OB-P` generator names; `OS-01-` prose hyphen) | PASS |
| No retired `CH-0n` labels remain | Same script | PASS |
| Timestamp-like tokens (`mm:ss`) | Same script | 2 found, both in file 12 and both video **length** metadata (17:57 and 35:47) from the fetch metadata, not transcript timestamps. Not used as timestamps. |
| Percentage-like tokens | Same script | Found in files 01, 05, 06, 07, 08, 10, 13, 17, 19. These are cited as ICT-stated references (e.g., the 50% reference) or as declared parameter examples; none is an asserted market fact. Manual review recorded; no change needed. |
| Quotation match in files 05 and 08 (FVG transcript) | Re-fetch of FVG chunk 0 this round; manual comparison | Matched (listed in §14.2). Not a programmatic match. |
| Quotation match in file 08 (OB transcript) | Not re-run; chunk 0 only | Two quotations unverified → paraphrased (§14.2). Remaining quotations from the OB transcript were not re-checked this round. |
| Licenses | Four GitHub LICENSE pages read | Verified (§14.2) |

Corrections to file 13 §13.2 that these checks require are in §14.1, F-06.

Checks **not** run in this round: a programmatic quotation match against saved transcript text (transcripts were not saved to disk); a full read of OB transcript chunks 1–4; any test of the procedures on data (none exists in the foundation; they are seeds).

## 14.6 Audit attachment status and open items

- The audit attachment referred to in the request is **not present** in the workspace or the filesystem (searched in the previous round and again at the start of this one). No audit text was received.
- Findings F-01 to F-06 are therefore addressed by their titles only. The user has been asked to resend the audit for an exact cross-check.
- The swing/wave priority items 1–10 (file 16 §16.1), the lettered items A–L (file 15 §15.2), and deliverables A–N (§14.0) are the working mapping. They must be cross-checked against the original request wording.

## 14.7 Exact file-change list (A, L)

From `git status` at the end of this round, relative to commit `612b012`:

| File | Status | Change |
|---|---|---|
| `00_RESEARCH_METHOD_AND_EVIDENCE.md` | modified | Transcript artifact description (no garbled quotations); §0.4 chunk-level read status (chunk 0 of 3 and chunk 0 of 5) |
| `05_FVG_ORDER_BLOCKS_ZONES.md` | modified | §5.4a G-OB-P register; body/wick table; variant description; artifact quotations removed |
| `08_APPLIED_CHART_CASES.md` | modified | CASE-0n labels; quotations paraphrased where unverified |
| `09_OPEN_SOURCE_AND_ACADEMIC_METHODS.md` | modified | Verified licenses; OS-03 replaced; purged CV reference corrected |
| `10_CONFLICTS_UNCERTAINTIES_AND_LIMITS.md` | modified | UN-11, UN-12 added; GP-09 partly resolved |
| `11_IMPLEMENTATION_KNOWLEDGE_CONTRACTS.md` | modified | Case label update |
| `12_SOURCE_INDEX.md` | modified | Verified license rows |
| `13_AUDIT_CONSISTENCY_AND_SUMMARY.md` | modified | §13.2 corrected; §13.3 namespace note corrected; §13.4 licenses |
| `claims_index.json` | modified | R2: 142 claims |
| `15_CONTEXTUAL_SELECTION_METHOD.md` | new | Method |
| `16_SWING_WAVE_SELECTION.md` | new | Swing/wave task cards |
| `17_SEED_PROCEDURES.md` | new | SP-01…SP-20 |
| `18_LOCAL_LEARNING_SELECTOR.md` | new | Learner design and regression protocol |
| `19_SELECTION_CASES.md` | new | W1…W10, O1, O2 |
| `14_RESOLUTION_MAP_R2.md` | new | This file |
| `checks/check_r2.py` | new | Consistency checker |
| `README.md` | modified | Index of files 14–19 and the R2 status (see §14.8) |

Other files (01, 02, 03, 04, 06, 07) were unchanged in this round relative to commit `612b012`.

## 14.8 What can be implemented now (M) and what needs empirical learning (N)

**Implementable now, without learning** (given declared parameters):
- Knowability gate, binding, containment, falsifier, dominance, logical consistency, leg construction, confirmation status, supersession, revision propagation (SP-01, SP-03 to SP-08, SP-13, SP-14, SP-19, SP-20).
- Replay-consistency test harness and golden-set fixtures from file 19.
- Sensitivity analysis over declared grids (SP-12) and representation-dependence reports (SP-16).
- Objective A as an exact-match harness (declared procedures only).
- Order-block validation and stop per the primary wording read (SP-09, SP-10), with UN-11 and P-L/P-C left as explicit unresolved states.

**Requires a declaration or a decision (not learning):**
- The items listed in §14.4, especially the representation parameters, the budget B, the direction-match policy, and the break basis.

**Requires empirical learning or evaluation (not yet available):**
- Objective B preferences: an annotation campaign on pre-outcome snapshots with agreement measured (file 18 §18.3).
- Objective C usefulness: causal, purged, out-of-sample evaluation against matched controls. No outcome data has been collected or evaluated in this foundation.
- The EP-coded choices (recency vs depth, which reference to prefer when several are admissible).
- Support-check and abstention policies for OOD states (LRN-05).

**Open items for the foundation (not implemented here):**
- Done in R2: `00` §0.4 and README read-status wording (chunk-level).
- Full read of OB transcript chunks 1–4 and FVG chunks 1–2 (not read).
- Re-check of the OB transcript quotations against saved text (not saved).

## 14.9 Audit notes

- No new source was added beyond those in file 12, and no new source grade was assigned.
- No trading decision, strategy, or optimization is specified. Objective D is out of scope (file 18).
- No universal threshold, confidence percentage, or universal importance score is introduced.
- Learned components are not presented as ICT doctrine (LRN-01, CSM-08).
