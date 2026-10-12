# 13 — Consistency Results, Audit Instructions, and Executive Summary

## 13.1 Executive summary (what a future team can build from this)

**Buildable now, as deterministic infrastructure (FACT-LOGIC):**

1. A causal bar store with `knowable_bar` discipline and a replay audit (IC-12). This is the prerequisite for everything else.
2. Swing candidate generators by named family, with parameters and knowability (IC-02).
3. Structure views and typed break events under explicit rules, kept as competing views (IC-04, IC-05).
4. Liquidity candidate sets (individual extremes, tolerance clusters, prior-period extremes, session extremes) with taken status, without asserting resting orders (IC-06).
5. Three separate zone generators: the three-candle FVG, the ICT-primary order block (lowest down-close with most range near a reference), and the community "last opposing candle" order block; with status histories (IC-08, IC-09).
6. Interpretation ledgers with supporting/contradicting observations, shared-bar detection, falsifiers, and revision logs (IC-10, IC-11).
7. Test harnesses: canonical definition-based test cases for each generator (learning target 1), purged/embargoed splitters (IC-13).

**Requires learning, annotation, or new evidence (JUDGMENT):**

- Which swing, structure view, liquidity candidate, or zone is relevant for a task (IC-03, IC-07).
- Whether any candidate, break, or zone carries predictive information (LL targets 3–5).
- Whether ICT's primary OB definition or the community definition better matches any intended analytical use (CF-01). An annotation protocol is sketched in file 07 §7.6; no outcome study is designed yet.
- Whether liquidity-level attraction exists beyond matched controls (HY-03).

**Not supported by this research:** any claim that these concepts predict outcomes; any confidence percentage; any universal selection rule; any performance claim; any institutional-causation claim.

**Most important caveat:** the primary ICT evidence available here is two partially read transcripts from 2016 material. The remainder of ICT's teaching, and every chart shown in those lessons, was not inspected.

## 13.2 Internal consistency checks performed

| Check | Method | Result |
|---|---|---|
| Claim index is valid JSON | Python `json.load` | Pass |
| Claim IDs unique | `checks/check_r2.py` (count vs unique set) | Pass (142 claims in R2, 0 duplicates) |
| Claim-like IDs cited in markdown exist in index | `checks/check_r2.py`: regex over `*.md`; namespaces excluded by design; three reviewed false positives allowlisted | Pass in R2 (0 missing). Earlier ‘0 missing’ statement was a manual claim and is superseded. |
| All `related` and `conflicts` references resolve | Set membership | Pass after two fixes (LQ-03 reference, and a claim-ID/case-label collision now resolved by renaming claims CH-* to CC-*) |
| Source IDs cited in index and markdown exist in file 12 | `checks/check_r2.py` (set membership against `12_SOURCE_INDEX.md`) | Pass in R2. (Replaces the earlier ‘manual review, partially checked’ entry.) |
| Quotations from primary transcripts match the text retrieved | **Not programmatic.** R2: FVG chunk 0 re-fetched and quotations in 05 and 08 compared by hand (matched). OB chunk 0: two unverified quotations paraphrased; the rest not re-checked. Transcripts are not saved to disk, so no programmatic match is possible. R1’s ‘Pass’ was a manual review and is not a programmatic result. | Partially verified (see file 14, §14.5) |
| Retracted or corrected claims | Manual | Corrected: (a) attribution of a liquidity-sweep page to an unverified domain (04); (b) BOS/CHoCH contrast not verified (03); (c) equal-lows example source attribution (08); (d) a mis-numbered OS reference (09) and a wrong purged-CV repository reference (09); (e) a wrongly fetched unrelated arXiv paper excluded (12); (f) PELT description wording (01). |
| No numeric market facts | Manual review in R2 of numerals in files 05, 08, 10, 16–19 (percent and price-like tokens listed by the checker) | Numbers are paper or repository metadata, video lengths, commit dates, cited ICT references (e.g., 50% stop-raise reference), fixture ordinals in files 16 and 19 (labelled as symbols, not prices), or declared-parameter examples. The transcript "20 pip" figure is not used. R1 had not run this check. |
| No invented timestamps | `checks/check_r2.py` (mm:ss tokens) | Two tokens found, both video durations in file 12 (17:57 and 35:47), taken from fetch metadata. No transcript timestamp is used as verified. R1 had not run this check. |
| No confidence percentages | `checks/check_r2.py` (percent-like tokens per file) | Percent tokens are ICT-stated references (e.g., 50%) or declared-parameter examples; no confidence or probability threshold is given (LRN-05). |
| No universal rules | Manual review against mission §9 | Rules stated are conditional. Prohibited universal rules appear only as prohibitions. |

## 13.3 Known inconsistencies still present (disclosed)

1. Some files use the word "claim" for both numbered claims and for prose examples. The index is the authoritative list; prose examples carry no claim ID unless listed.
2. Case labels CASE-01 … CASE-08 (file 08) and W1–W10, O1–O2 (file 19) are a separate namespace from claim IDs. The index contains no `CASE-*` IDs. The earlier shared `CH-0n` labels are retired (R2, F-03).
3. Several contracts (IC-xx) are classified as type `F` (researcher-proposed) in the index, though they include `FACT-LOGIC` parts. The classification refers to the contract as a whole.
4. Gradings for open-source components (OS1) reflect landing-page reads only. They are not evaluations of code quality.
5. The academic abstracts were read in full; their experiment sections were not. Claims are restricted accordingly.

## 13.4 Source-verification status

- Verified: transcript text for SRC-ICT-FVG (chunk 0 of 3, re-read in R2) and SRC-ICT-OB (chunk 0 of 5, re-read in R2); abstracts for SRC-AM07, SRC-CKS14, SRC-HE16, SRC-TS2V; library record for SRC-KFE12; repository pages for SRC-RUP, SRC-TS2V-REPO, SRC-PCV-REPO; **licenses verified in R2**: ruptures BSD-2-Clause, TS2Vec MIT, purgedcv MIT.
- Not verified: the full ICT lessons (chunks 1–4 of OB; chunks 1–2 of FVG); any ICT chart; any ICT timestamp; the López de Prado book; HMM, Bai–Perron, segmentation-survey and wavelet references.
- Snippet-only: several community and one academic (ACM segment-based BOCPD) sources.

## 13.5 Instructions for the independent auditor

**Step 1 — Start here.** Read `00_RESEARCH_METHOD_AND_EVIDENCE.md` §0.2–0.5. This defines the categories, grades, and verification limits.

**Step 2 — Check the grade of each claim you audit.** In `claims_index.json`, find the claim ID. If the grade is `S1`, `S2`, `OS1`, `AC2`, or `CF`, the claim is weaker than a verified primary statement, and you should judge it accordingly.

**Step 3 — Verify sources independently.** For each `P1` claim:
- Open the URL in `12_SOURCE_INDEX.md`.
- Compare the quoted fragment with the lesson transcript, noting that auto-caption errors are expected.
- Check whether the statement is ICT's own (E) or a paraphrase (E-paraphrase). The index does not distinguish these; the auditor should.
- Determine the lesson's teaching date (the description states December 2016 content).

**Step 4 — Test the separation of categories.** For each claim that uses the words "institutional," "resting," "liquidity," "respected," or "confirmed," verify that it is labeled with a category from file 00 and that no F or D claim is presented as an observation.

**Step 5 — Test knowability.** For each candidate-generation or selection claim, ask: at what bar could this have been known? Check the file's stated `knowable_bar` rule. Look for any use of later bars.

**Step 6 — Test the independence of evidence.** For each claim that counts "confluences," check whether the elements share source bars (file 06 §6.5).

**Step 7 — Check conflicts are preserved.** For each conflict in file 10, verify that the foundation does not silently choose a side. The CF entries should give both readings.

**Step 8 — Check hypotheticals.** Every example labeled hypothetical or symbolic must contain no market numbers. Verify this.

**Step 9 — Check overreach.** Search for: "should," "always," "never," "guaranteed," "high probability," "institutional" used as fact, and "confidence" with numbers. Each instance must be a quoted source statement, a prohibition, or a clearly labeled hypothesis.

**Step 10 — Check the gaps.** Read `10_CONFLICTS_UNCERTAINTIES_AND_LIMITS.md` §10.3. Confirm no gap is concealed in a summary.

**Reporting.** Report findings by claim ID, with: (a) the claim's grade, (b) what you verified, (c) your verdict (supported / overstated / mis-categorized / unsupported / contradicted), and (d) the minimum change needed.

## 13.6 Remaining work a follow-up round should prioritize

0. (Resolved R2) Verified open-source licenses: ruptures BSD-2-Clause, TS2Vec MIT, purgedcv MIT.
1. Read the full text of both primary ICT lessons, with timestamps, and update SRC-ICT-FVG and SRC-ICT-OB entries.
2. Read the primary ICT liquidity, market structure, and mitigation lessons (P2 items).
4. Obtain the López de Prado chapter and verify the purging and embargo definitions directly.
5. Design (not run) a causal annotation study for contextual selection (file 07 §7.6).
6. Design (not run) a matched-control test for liquidity-level attraction (HY-03) and a pre-registered test for HY-01 and HY-02.
7. Check whether any intra-bar sequencing data is available for the project's instrument (GP-10).

## 13.6 R2 pointers

- Repair map, changes, and check results: `14_RESOLUTION_MAP_R2.md` (§14.1 findings, §14.5 check commands and results, §14.6 audit attachment status).
- Method and designs: files 15–19. Checker: `checks/check_r2.py`.
