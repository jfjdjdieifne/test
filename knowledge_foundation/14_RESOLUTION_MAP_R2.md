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
| No retired CH-prefixed case labels remain | Same script | PASS |
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

## 14.10 Reconciliation with the independent audit (R3)

**Context.** An independent audit of the baseline (commit `612b012`, audit branch named `arena/5c3e60c7-test`; this session's branch is `arena/5125ef9c-test`) was received after R2. It reported six findings (F-01 HIGH, F-02 MEDIUM, F-03 LOW, F-04 MEDIUM, F-05 LOW, F-06 INFORMATIONAL) and no CRITICAL findings. The auditor's cited evidence was checked against the current files. The R2 changes are the subject of the re-audit, not the baseline.

### 14.10.1 Resolution matrix

| Finding | Auditor's evidence and concern | Current state (verified in this round) | Resolution in R3 | Status |
|---|---|---|---|---|
| **F-01** HIGH | 02 §2.7 gives task heuristics only as prose; IC-03 leaves selection as [JUDGMENT]; no seed selector exists; the falsifier-invalidation rule is not formalized (J-1: name it `SEL-INV-FALSIFIER`). | Confirmed before R3: IC-03 had no selector blocks. R2 had added SP-01…SP-20 in file 17, but they were not linked to IC-03. | File 11 IC-03 now has four seeds: SEL-INV-FALSIFIER (deterministic given interpretation), SEL-HTF-BIAS (declared policy, source-supported direction; unset slots P-REC and the scale table), SEL-ENTRY-REF (declared policy; unset slot P-PROX; residual unresolved), SEL-LIQ-TARGET (unresolved by design). File 17 §17.4 classifies every SP procedure as D, P, S, or E. | Partly resolved; residual in 14.10.2 |
| **F-02** MEDIUM | PM-01 mis-sourced; FZ-06 typed G; grades F/B/D undefined; CF-11 cites SRC-COMM-BIO against file 12. | PM-01: fixed in R2 (sources empty, NOT_SOURCE_BASED). FZ-06: CF in R2. F/B/D: mapped in R2, no such grades remain (grade counts in §14.5). CF-11: **still cited SRC-COMM-BIO**; confirmed defect. | CF-11 sources removed; provenance researcher; no source in file 12 supports session windows, so the entry is a gap record (R3, logged in revision_log). | Resolved |
| **F-03** LOW | 13.2 "0 missing IDs" conflicts with bare case IDs with the retired CH prefix (eight of them) absent from the index. | R2 renamed case labels to CASE-0n and CH-* claim IDs to CC-*. Checker: no retired CH-prefixed case label remains. 13.2 rewritten. | No further change. | Resolved |
| **F-04** MEDIUM | G-OB-P cannot run without UN-01 / UN-02 values; the auditor proposed declared values (window = swing-bounded leg; "near" = X × ATR with X swept 0.5–2.0). | The R2 register had slots but no explicit execution status. | **Auditor's numeric proposal not adopted**: the owner's instruction prohibits arbitrary policy values and silent parameter assignment, and the 0.5–2.0 sweep is itself an unsourced value. R3 adds an explicit execution status (NOT RUNNABLE until declared), lists options for P-W and P-N without values (including a set relation that needs no number), and adds the same status to IC-08. | Resolved as "blocked with options"; the owner's declaration is the residual |
| **F-05** LOW | Learning layer excludes trade-outcome learning; update degradation covered briefly; forgetting not named. | R2 file 18 names catastrophic forgetting (18.8), has the regression protocol (18.7), and marks objective D out of scope. | No change to scope. The auditor's "rolling backtests per regime" is a trade-outcome method, which is out of scope. File 07 §7.10 is unchanged; file 18 supersedes it for regression. | Resolved in file 18 |
| **F-06** INFORMATIONAL | The % check should name the 38% example and the 75% prohibited example. | Both occur (01 and 06). | 13 §13.2 percent row now names them and records a manual review of each hit. | Resolved |

### 14.10.2 Remaining HIGH findings

**F-01 is downgraded from HIGH to MEDIUM, not closed.** Reasons:
- Deterministic selection now exists for the falsifier-based invalidation (SEL-INV-FALSIFIER, SP-04). This is the auditor's exact J-1 example.
- For HTF-bias and entry-reference, the foundation now provides seeds that can be implemented, but each depends on owner-declared slots (P-REC, P-PROX, the scale table, and the SP-15 base rule). The foundation cannot and should not supply these values.
- Ranking among plausible candidates remains empirically unresolved (class E). This is correct under the user's constraints, and it is an open choice, not a defect.

No other HIGH finding remains.

### 14.10.3 Answer to the F-01 question: do SP-01…SP-20 make justified choices?

- **Defensible deterministic selection (D):** knowability gate, crossing binding (given basis), falsifier binding (given a reference-form interpretation), containment, logical consistency, structural window, confirmation status, leg construction, taken-status computation.
- **Declared operational policy (P):** the scale table (SP-02), the requirement list used by dominance (SP-06), the recency rule for "most recent opposite leg" (SP-15), and the origin rule used in W1 and T-S1.
- **ICT-source-supported (S):** SP-09 and SP-10 (OB trade-through and low-stop, P1 wording, partial transcript), and the HTF-bias direction in SEL-HTF-BIAS.
- **Empirically unresolved (E):** recency versus depth among entry legs; which of several plausible candidates to prefer; any proximity criterion.

**Did the procedures introduce unvalidated recency, size, proximity or scale rules?** Recency and scale: yes, but only as declared policies (P), labelled as such (SP-15, the T-S1 origin rule, SP-02), with the requirement that sensitivity analysis and alternatives be reported. Size: no selection criterion uses it. Proximity: no relevance criterion uses it; it appears only as the unset slot P-PROX. Recency was also present in some worked cases as the basis of a "definite" label. R3 corrects the labels in W1 (now "definite only conditional on declared policy P-ORIGIN"). W2 and W7 policies are now flagged as illustrative, not recommended.

### 14.10.4 Corrections to the worked cases and claims (R3)

- W1 label corrected (declared policy, unvalidated).
- W2 and W7 example policies labelled illustrative.
- W10 retains its definite label, which is conditional on the declared close basis (already stated).
- SWS-04 statement now marks the provisional-exclusion default as P-class.
- Worked-case claims were checked for unsupported selection conclusions: no case presents a ranking as a fact. The only definite outcomes are either deterministic (given stated definitions) or labelled conditional on a declared policy.

### 14.10.5 Pending verification and not adopted

- **Body-versus-wick passage** (reported by the auditor): not reproduced in this session. The page returned an error on chunk 0 and navigation-only content on chunks 1 and 2. It is **not** added as a source statement. Recorded as a pending action in file 05 §5.4a.
- **Third-party transcript renderings** the auditor cites (glasp.co, videohighlight, opentools.ai): not re-checked in R3.
- **Repository and license characterizations** the auditor re-checked via the GitHub API: not re-run in R3. The licenses were verified in R2.

### 14.10.6 Exact changed files in R3

| File | Change |
|---|---|
| `11_IMPLEMENTATION_KNOWLEDGE_CONTRACTS.md` | IC-03 seed selectors (SEL-*), IC-08 G-OB-P execution status |
| `05_FVG_ORDER_BLOCKS_ZONES.md` | §5.4a execution status of G-OB-P, options for P-W and P-N (no values), pending body/wick item |
| `16_SWING_WAVE_SELECTION.md` | T-S1 and T-S4 policy-status lines |
| `17_SEED_PROCEDURES.md` | §17.4 justification classes (D/P/S/E) |
| `19_SELECTION_CASES.md` | W1 label; example-policy note (W2/W7) |
| `13_AUDIT_CONSISTENCY_AND_SUMMARY.md` | §13.2 percent row names the 38% and 75% examples |
| `claims_index.json` | CF-11 sources removed; SWS-04 statement labelled P-class; revision logs |
| `checks/check_r2.py` | Added SP-definition and SEL-definition cross-checks |
| `14_RESOLUTION_MAP_R2.md` | This section |

### 14.10.7 Validation results (R3, run in this session)

Command: `python3 checks/check_r2.py` from `knowledge_foundation/`. Result: **0 failures**.
- claims_index.json parses; 142 claims; 0 duplicate IDs.
- Provenance and grade rules: pass.
- Related, conflict and source references: pass.
- Claim-like IDs cited in markdown exist: pass (allowlist of three reviewed false positives).
- No retired CH-0n labels: pass.
- Every SP procedure cited in files 15–19 is defined in file 17: pass.
- Every SEL-* cited is defined in file 11: pass.
- mm:ss tokens: only video durations (file 12 and quoted in 13 and 14).
- Percent-like tokens: each hit listed and manually reviewed (13 §13.2).
- Type distribution: A 1, B 1, CF 42, D 8, E 7, E* 2, F 77, G 4 (total 142). Grade distribution: NOT_SOURCE_BASED 82, NOT_APPLICABLE 27, AC1 8, P1 11, S1 6, OS1 3, AC2 2, P2 1, S2 1, CF 1.

Not run: a programmatic check that the new SEL seed text matches any source (none is claimed); a semantic review by a second human reviewer.

### 14.10.8 Unresolved choices (R3, cumulative)

From §14.4 (items 1–15), plus:
16. P-REC: the meaning and value of "recent enough" for HTF-bias (SEL-HTF-BIAS).
17. P-PROX: the meaning, units and value of "close to current price" (SEL-ENTRY-REF).
18. Scale table entries for HTF-BIAS and entry roles (SP-02).
19. Base rule for retracements (SP-15) and origin rule (P-ORIGIN, T-S1).
20. P-W and P-N for G-OB-P (owner declaration; options in file 05 §5.4a).
21. Verification of the body/wick passage (file 05 §5.4a pending).
22. Ranking among survivors of the same task (class E).

### 14.10.9 Independent re-audit instructions

1. Check out the commit that contains R3 on `arena/5125ef9c-test` (it is committed locally; it is not pushed). Do not rely on the baseline `612b012`.
2. Run `python3 checks/check_r2.py` from `knowledge_foundation/`. Expect 0 failures.
3. F-01: open file 11 IC-03 and confirm the four seeds and their justification tags. Open file 17 §17.4 and confirm each SP procedure has a class. Check whether any seed produces a ranking or assigns a value to an unset slot. Each must do neither.
4. F-02: confirm CF-11 has no sources, and that no grade outside the vocabulary remains (checker output).
5. F-04: confirm file 05 §5.4a lists no numeric value for P-W or P-N, and that file 11 IC-08 carries the NOT RUNNABLE status.
6. Worked cases: for each of W1–W10 and O1–O2 in file 19, confirm that every "definite" result names its basis, and that every policy is labelled P or S.
7. Pending item: re-read the full OB transcript (all chunks). If the body/wick passage is confirmed, add it as a P1 statement. Do not add it from secondary transcripts without verification.
8. Confirm that no claim presents a market fact that is in fact a declared policy.
