# 05 — Integration Contracts, Local Compute, First Build, Stop Conditions, Unknowns, Builder Actions (D, I, J, K, L-stop, M, N)

## 1. Integration with the trading project's existing producers (§18)

The owner reports existing causal ingestion, multiple swing/wave producers, structural event detection, liquidity and zone candidates, multitimeframe observations, candidate provenance, historical trajectories, walk-forward evaluation, calibration infrastructure, and dependency/evidence records. **These were not inspected.** The contracts below are what this architecture requires from them. Where a producer already satisfies a contract, use it; do not duplicate it.

| Existing capability (reported) | Contract this architecture needs | Builder must verify before integrating |
|---|---|---|
| Causal market-data ingestion | Closed bars with `open_time`, `close_time`, `ingest_time`, source ID, content hash; gaps flagged | That `ingest_time` exists and is at or after `close_time`; how duplicates and corrections are stored |
| Multiple swing/wave producers | Each emits candidates with `generator_id`, `version`, parameters by reference, `confirmed_at_bar`, and `status` (confirmed / provisional / superseded) | Whether each producer is causal at emission (no smoothing); whether parameters are declared or internally tuned; whether any producer uses the decision bar's close before it is complete |
| Structural event detection | Events with `known_at`; definitions by ID and hash | Whether events are computed with future bars anywhere; whether definitions are versioned |
| Liquidity and zone candidates | Candidates with reference level, `known_at`, and status history (crossed, reclaimed, failed) | Whether touches and crosses are computed on closed bars only; how intrabar ambiguity is handled |
| Multitimeframe observations | Mapping from fine bars to the coarse bar that contains them, with completion time | Whether a coarse bar is treated as known only at its close time |
| Candidate provenance | Provenance chain to source bars and generator run | Whether provenance is stored per candidate or only per run |
| Historical trajectories | Snapshot-indexed histories of candidates and statuses | Whether trajectories allow replay equality (file 03 §4C) |
| Walk-forward evaluation | Purge and embargo logic; split definitions | Whether purge length is set from label horizon or is a fixed constant |
| Calibration infrastructure | Calibration records keyed by model version and split | Whether calibration uses time-blocked holdouts; whether it is applied to any probability currently shown |
| Dependency and evidence records | Dependency graph from outputs to inputs and versions | Whether it can drive recomputation (the interpretation graph in file 02 §E) |

**Integration rules.**
1. Producers remain the source of their own candidates; this architecture reads them through the candidate ledger and adds provenance, admissibility and the S1/S2 layers.
2. Any producer that fails the causal check is quarantined from features and from labels until fixed. It is not silently corrected.
3. Where two producers disagree, both are kept. Agreement counts are features; neither overrides the other.
4. Calibration outputs from the existing infrastructure are used as baselines for any new probability; they are not assumed to transfer to new models.

## 2. Local compute plan (J, I)

**No performance numbers are given.** None has been measured for this system or for the owner's hardware. The reasoning below is structural. Verified package facts are from PyPI metadata read this session.

### 2.1 Cost categories

| Category | Work | Scaling (structural) | Main resource |
|---|---|---|---|
| Initial feature extraction | Build bars, candidates, index, admissibility | Linear in bars; index queries proportional to matches | CPU, memory for index |
| S1 fitting | Bounded-duration filter with EM or Bayesian updates | Per observation proportional to states × declared D (explicit-duration form); iterations × data | CPU |
| S2 training | Bag-level models over admissible sets | Proportional to bags × candidates × features × epochs | CPU for gradient-boosted or small attention models; GPU optional for neural |
| S3 pretraining (gated) | Masked or contrastive encoder | Proportional to windows × window length × model size × epochs | GPU favoured |
| Historical replay | Re-run kernel and S1 on past bars for replay equality | Linear in bars; fully parallel across instruments | CPU |
| Live inference | Per-bar incremental update | Proportional to affected candidates and tasks | CPU; latency must be measured |
| Model update | Retrain under registry gate | Same as training; plus shadow evaluation period | CPU or GPU |
| Storage | Bars, candidates, ledger, features, interpretations, model artifacts | Bars × instruments × timeframes; candidate and ledger rows grow with bars × scales × tasks | Disk |

### 2.2 Hardware options (owner hardware unknown)

- **CPU-only (stage 0–2):** sufficient for kernel, S1 with modest D and M, and S2 with gradient-boosted or small attention models. Memory is the usual constraint for candidate ledgers over long histories.
- **GPU (optional, stage 3+):** needed only if S3 is built or if a neural S2 is preferred and CPU training time is unacceptable. Measure before buying.
- **Storage:** plan for append-only logs plus materialised views. Size must be measured on the owner's bar history.

### 2.3 Software (verified this session)

| Package | Use | Licence (verified) | Last upload (PyPI) | Note |
|---|---|---|---|---|
| `hypothesis` | Property-based contract tests | (not parsed) | 2026-10-11 | Use for kernel invariants |
| `river` | Incremental statistics and streaming learners | (not parsed) | 2026-08-21 | Candidate for incremental features |
| `lightgbm` | Comparator or S2 approximation on tabular bags | MIT (AR-1) | 2026-07-18 | Ranking objective needs integer relevance (see file 02 §2.5) |
| `statsmodels` | Regime or Markov-switching comparators | (not parsed) | 2026-08-27 | Comparator only |
| `hmmlearn` | Standard HMM comparator | BSD (classifier) | 2024-10-31 | No explicit-duration model; older release |
| `ruptures` | Offline changepoint baselines | BSD-2-Clause | 2025-11-27 | Offline only |
| `torch` | S3 or neural S2 | (not parsed) | 2026-09-30 | Large dependency; gated |
| `chronos-forecasting` | Possible forecasting comparator | Apache-2.0 | 2026-09-08 | Not a structure model |

**Explicit-duration HSMM:** no maintained package was checked; S1 likely needs an in-house bounded-duration filter with tests. That is a build-cost item, not evidence against the method.

### 2.4 What must be reported on every run

Wall-clock time per stage; peak memory; row counts (bars, candidates, ledger entries, bags); largest admissible-set size; largest coherence component (if built) and whether inference was exact or approximate; count of `NOT_EXAMINED` entries; replay-equality result; seed and data hash.

## 3. Data acquisition route (§16 and §19)

**Start small, do not claim more data guarantees improvement.**

1. **Stage D0 — one instrument, one fine and one coarse timeframe, the owner's existing closed bars.** Enough to run the kernel, S1 fitting, and replay tests. Length is whatever the owner already has; the builder records gaps.
2. **Stage D1 — expert acceptable-set annotation pilot.** A written protocol (file 03 §2); a small set of snapshots drawn from a declared sampling rule (for example stratified by regime block, using only the regime definitions declared in advance); at least two annotators on an overlap subset. Size set by the owner's annotation budget and a pre-run check; the builder states the effect size of interest before annotating.
3. **Stage D2 — expand history and instruments** only after the replay and leakage tests pass on D0. Each expansion is a new data manifest with its own hash.
4. **Stage D3 — outcome observations** only for objectives E and F, with matured labels and purged splits.

Why this order: the swing problem is solved (or not) on structure before any learner is trained on judgement; annotation is the only route to contextual labels; outcome labels come last because they are the most confounded.

**Trustworthy-label check:** if the D1 annotation's inter-annotator agreement is below a threshold the owner declares before annotation starts, the S2 route stops and the team returns to the protocol. No threshold is set here.

## 4. First build specification (K)

### 4.1 Scope
- Price movement → swings and waves → structural references only.
- One instrument, two timeframes, owner-selected; declared generator families F-K and F-T from AR-1, plus S1 posterior at declared scales.
- Tasks: structural reference (T-S1), binding of reference to its forming leg (T-S2), falsifier (T-S5), as defined in the owner's task list.
- **Excluded:** FVG ranking, liquidity-sweep tasks (apart from the deterministic sweep definition used for testing), entry models, trading decisions, profit optimisation, LLMs, GNNs.

### 4.2 Phases and gates

**Phase 0 — kernel, contracts, declared baselines (no learning).**
- Bar store with replay; candle semantics with `UNKNOWN`; F-K and F-T generators with declared parameters; candidate ledger; admissibility for T-S1, T-S2, T-S5; reclaim-monitor for the sweep definition as a deterministic example.
- Property-based and metamorphic tests (file 02 §3) and replay-equality test passing.
- Output: declared-rule interpretations for each task on the owner's bars.

**Phase 1 — S1 on real and synthetic data (label-free fitting).**
- Fit bounded-duration segment models on D0 data (in-sample for fitting only); synthetic families for mechanics with known boundaries.
- Compare posterior-mode boundaries with declared rules on:
  - synthetic held-out families (file 04 A falsification),
  - annotated boundaries from a small pilot (only if D1 has begun).
- Gate: S1 is kept as a candidate representation only if it is not dominated by declared rules on the pre-registered metrics; otherwise its outputs are shown as diagnostics only.

**Phase 2 — S2 on annotated snapshots.**
- Starts only after D1 data exist and inter-annotator agreement is reported.
- Models: attention-MIL or a small bag-level model; LightGBM comparator on the same features (not as the primary learner).
- Controls: label-permutation model; declared rule; recency-only; uniform over admissible; matched-annotator holdout.
- Gate: pre-registered margin over controls on held-out annotators and periods. The margin is declared by the owner before evaluation.

**Phase 3 — linking and abstention.**
- Hard-constraint propagation across T-S1, T-S2, T-S5; interpretation sets with alternatives; abstention evaluated against annotated ambiguity.
- A learned pairwise coherence factor is considered only if Phase 2 data include coherence annotations and the held-out comparison shows change beyond hard constraints.

**Phase 4 — S3 (gated).** Only if Phase 2 errors are attributable to representation. Not planned in this build.

### 4.3 Acceptance criteria
- Every interpretation has versions, constraint status, posterior or set status, and listed alternatives.
- Every candidate has a ledger status for every task at each decision time.
- Replay equality passes on the full history.
- Each comparison reports all baselines, their parameters, and the split.
- No output is labelled "correct", "understood", or "profitable". Outputs are interpretations under declared definitions.
- Learned components can be disabled; the system then serves declared rules with a visible `FALLBACK` status.

### 4.4 Fallback
A failed gate serves the declared rule. The failed learned version is archived with its report. Failure is an outcome, not a defect to be hidden.

## 5. Stop conditions (§20) — assessed

| Stop condition | Status for this build | Action |
|---|---|---|
| Learning target invalid | **Applies to any target built on future profit or on future-based structure labels.** Those are excluded. S1 is label-free; S2 targets expert acceptable sets, which are valid as annotation targets but not as ground truth | Proceed with S1 Phase 0–1. S2 waits for D1 and an agreement report |
| Labels leak future outcomes | **Applies if DeepLOB-style future construction is used for structure.** Excluded by design | Enforced by replay and `known_at` tests |
| Required inputs cannot be reproduced | **Unknown.** Depends on owner's bar history and producers | Builder inspects (§6). If the bar history cannot be reproduced exactly, Phase 0 stops |
| Method depends on unavailable proprietary infrastructure | **Not applicable to S1 or S2.** S3 may need GPU | — |
| Evaluation cannot distinguish learning from memorisation | **Addressed** by label-permutation, held-out annotators, held-out periods | Required controls in file 03 §6 |
| Computational cost unjustified | **Unknown until measured.** No benchmark exists | Phase 1 measures S1 cost before any further build |

The stop conditions are used to bound scope, not to avoid the swing problem. The first build addresses the swing problem directly, in its label-free form, before any judgement-based learning.

## 6. Remaining unknowns (M)

1. **The owner's bar history:** length, instruments, timeframes, source, gaps, session conventions, timezone.
2. **Whether the owner's producers are causal at emission**, and whether they store `ingest_time`.
3. **Declared scale measures and parameter values** for F-K, F-T, and S1 (window lengths, reversal sizes, duration windows D, numbers of states M). None is set here; all must be declared and sensitivity-tested.
4. **Task definitions T-S1, T-S2, T-S5** in the owner's own words, with admissibility rules.
5. **Annotation protocol, annotators, and their availability.** Whether the owner can recruit a second annotator.
6. **Inter-annotator agreement threshold** for the S2 route (owner declares before annotation).
7. **Pre-registered promotion margins** and **effect size of interest**.
8. **Hardware:** CPU, RAM, storage, GPU presence.
9. **Licences** of any owner code or data to be reused.
10. **Whether the owner's existing definitions match the foundation's variants**, and the owner's decision on each conflict.
11. **Whether the sweep definition's reclaim condition is declared** (window length and tolerance are owner declarations).
12. **The full text of the key papers** (Fearnhead & Liu 2007; Yu 2010; Cour et al. 2011; Ilse et al. 2018; Gibbs & Candès 2021; Franceschi et al. 2019). Currently verified only at abstract, excerpt or secondary level.
13. **The audit attachment** referenced in earlier sessions (not found in the workspace).

## 7. Builder's next actions (N)

**Before writing any code (inspection, read-only):**
1. Inspect the bar ingestion path: confirm `ingest_time`, `close_time`, duplicates, corrections, gaps, session and timezone conventions.
2. List every swing/wave producer: its inputs, parameters, whether it uses smoothing or future bars, and whether it stores `confirmed_at_bar`.
3. Inspect the structural event and liquidity/zone producers for the same causal properties; record where intrabar ambiguity is resolved and how.
4. Inspect the walk-forward and calibration code: purge and embargo logic, split definitions, calibration holdouts.
5. Inspect dependency and evidence records: can they drive recomputation?
6. Identify existing tests; note which ones check causality, replay, or leakage.
7. Record the hardware available.

**Phase 0 (first code, after inspection):**
8. Write the contract tests from file 02 §3 and file 02 §3's property list before the kernel code; run them against the producers' outputs as a compatibility check.
9. Build the candidate ledger and admissibility for T-S1, T-S2, T-S5 as thin adapters over existing producers, not as new generators, where a producer already meets the contract.
10. Produce the declared-rule baseline interpretations on the owner's bars; store them with versions.

**Phase 1:**
11. Implement a bounded-duration filter with declared D and M; test on synthetic families with known boundaries; test filtering-only property (truncated run equals prefix).
12. Compare with declared rules under the pre-registered metrics. Report the result, including negative results.

**Do not in this build:**
- Use future profit or future-based structure labels.
- Add FVG or liquidity tasks.
- Add an LLM or external paid API.
- Modify existing producers' definitions to improve a metric.
- Duplicate producers when a contract adapter suffices.

## 8. Final statement on evidence

- The verified sources support the existence and properties of the methods named (online changepoint filtering, explicit-duration models, partial-label learning, attention-based MIL, weak supervision, conformal adaptation, calibration, STL monitoring). They do not show that any of these improves market-structure selection.
- The main new evidence from this round is negative for the earlier design: the factor-graph layer lacks its labels, and the LightGBM ranker needs graded relevance labels that the annotation protocol would have to invent. These are corrected in the shortlist.
- Benchmarks reported in the reviewed papers (forecasting error, LOB direction accuracy) do not test contextual structure selection and are not cited as evidence of this capability.
