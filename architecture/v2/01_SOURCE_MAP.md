# 01 — Global Source Map and Verification Quality (B, D)

## Verification classes used

No source in this session was read in full method text. Classes are therefore applied conservatively:

| Class | Meaning in this map |
|---|---|
| PRIMARY_METHOD_READ | Full method section read. **None assigned in this session.** |
| PRIMARY_EXPERIMENT_READ | Full experiment section read. **None assigned.** |
| IMPLEMENTATION_INSPECTED | Source code read. **None assigned**; repository metadata only. |
| OFFICIAL_DOCS_READ | Maintained project documentation read directly. |
| ABSTRACT_ONLY | Abstract or citation-level abstract read, or excerpts of the method text seen in search results (not a full read). |
| SECONDARY_SUMMARY | Claim taken from another paper or review that cites the source. |
| METADATA_ONLY | Bibliographic record, licence or activity fields only. |
| UNVERIFIED | Cited from memory or not checked. |

Rule applied: a claim is not promoted from a lower class to a higher one. Benchmark results found in READMEs or abstracts are not used as evidence unless the benchmark tests the capability in question (see the "tests needed capability?" column).

## B. Source map

### B.1 Changepoints, segmentation and filtering

| Source | Venue/ID (verified) | Class | Relevance | Tests needed capability? |
|---|---|---|---|---|
| Adams & MacKay, Bayesian Online Changepoint Detection | arXiv:0710.3742 | ABSTRACT_ONLY (from earlier session) | Causal run-length posterior | No. Generic changepoints, not wave structure |
| Fearnhead & Liu, On-line inference for multiple changepoint problems | JRSSB 69(4):589–605; DOI 10.1111/j.1467-9868.2007.00601.x | ABSTRACT_ONLY (RePEc and Wiley abstracts) | Exact online filtering of the joint posterior over number and position of changepoints, cost quadratic in observations; particle approximation linear | Partly. Changepoints in a sequence model; relevant to partition posteriors |
| Yu, Hidden semi-Markov models | Artificial Intelligence 174(2):215–243, 2010 (venue from citing papers) | ABSTRACT_ONLY (review excerpts seen in search results) | Explicit-duration state models; forward–backward over durations | Partly; models segment durations directly |
| Dewar, Wiggins & Wood, Inference in HMMs with explicit state duration distributions (IEEE 2012 paper) | `cs.ubc.ca` PDF excerpt | ABSTRACT_ONLY (excerpt) | Shows exact EDHMM forward–backward cost grows with duration range; truncation fails if true durations fall outside the allowed interval | Yes, for implementation constraints |
| Killick, Fearnhead & Eckley (PELT) | JASA 2012; DOI 10.1080/01621459.2012.737745 | METADATA_ONLY | Offline exact penalised segmentation | No causal use. Baseline only |
| Ruptures library (PELT and others) | BSD-2-Clause; PyPI 1.1.10, last upload 2025-11-27 (verified) | ABSTRACT_ONLY (PELT documentation snippet, earlier session) | Offline baselines | Baseline only |

### B.2 Learning from partial, weak or set-valued supervision

| Source | Venue/ID | Class | Relevance | Tests needed capability? |
|---|---|---|---|---|
| Cour, Sapp & Taskar, Learning from Partial Labels | JMLR 12:1501–1536, 2011 | SECONDARY_SUMMARY (cited by Lou, ICML 2012, and by a 2020s AAAI partial-label paper; the JMLR abstract itself was not read) | Each example has a candidate label set, exactly one of which is valid | Yes: the set-valued supervision pattern matches expert "acceptable set" annotation |
| Lou, Structured Learning from Partial Annotations | ICML 2012 PDF (`icml.cc/2012/papers/753.pdf`) | ABSTRACT_ONLY (excerpt) | Structured outputs trained on partial annotations; reports that a partially annotated model can outperform a fully annotated model on the stated task when about 40% of data is annotated | Structured tasks, but a different domain. Result is not transferable as evidence |
| Ilse, Tomczak & Welling, Attention-Based Deep MIL | ICML 2018, pp. 2127–2136 | ABSTRACT_ONLY (mlanthology abstract) | Bag-level labels; attention gives per-instance weights; permutation-invariant pooling | Yes: candidate set per snapshot is the bag |
| Ratner et al., Snorkel: Rapid Training Data Creation with Weak Supervision | VLDB 11(3); arXiv:1711.10160 | ABSTRACT_ONLY plus excerpt of method (VLDB PDF text seen) | Labelling functions combined by a generative model over their accuracies and correlations, without ground truth | Yes, for combining declared rules and annotator heuristics. Does not establish that labels are correct |

### B.3 Uncertainty and non-stationarity

| Source | Venue/ID | Class | Relevance |
|---|---|---|---|
| Gibbs & Candès, Adaptive Conformal Inference under Distribution Shift | NeurIPS 34 (2021), pp. 1660–1672; arXiv:2106.00170 | SECONDARY_SUMMARY (cited with assumptions in Zaffran et al. 2022 and in a JMLR 2024/25 DtACI paper) | Online adjustment of coverage level; the original theory assumes the size of shift is known and a hidden Markov structure; later work relaxes these |
| Xu & Xie, EnbPI / Conformal prediction interval for dynamic time series | ICML 2021 | SECONDARY_SUMMARY | Ensemble conformal intervals for time series under a mixing assumption |
| Angelopoulos, Candès & Tibshirani, Conformal PID control | NeurIPS 2023; arXiv:2307.16895 | METADATA_ONLY (from a literature list) | Control-style adaptive coverage |
| Lu et al., Learning under Concept Drift: A Review | IEEE TKDE 31(12):2346–2363, 2018 (DOI 10.1109/TKDE.2018.2876857) | ABSTRACT_ONLY (arXiv 2004.05785 abstract) | Taxonomy of drift detection, understanding and adaptation |
| Guo, Pleiss, Sun & Weinberger, On Calibration of Modern Neural Networks | ICML 2017 | SECONDARY_SUMMARY (author blog and reviews) | Temperature scaling as a one-parameter post-hoc calibration; works when test distribution matches training distribution |

### B.4 Temporal logic and specification monitoring

| Source | Venue/ID | Class | Relevance |
|---|---|---|---|
| Maler & Nickovic, Monitoring Temporal Properties of Continuous Signals | FORMATS 2004, LNCS 3253, pp. 152–166; DOI 10.1007/978-3-540-30206-3_12 | METADATA_ONLY | Signal temporal logic (STL) monitoring foundation |
| Donzé, Ferrère & Maler, Efficient Robust Monitoring for STL | CAV 2013, LNCS (Springer, 2013) | ABSTRACT_ONLY (Springer abstract) | Linear-time robust monitoring of STL, with margin semantics |

### B.5 Representation learning and self-supervision

| Source | Venue/ID | Class | Relevance |
|---|---|---|---|
| Franceschi, Dieuleveut & Jaggi, Unsupervised scalable representation learning for multivariate time series | NeurIPS 2019 (vol. 32) | SECONDARY_SUMMARY (survey text, 2024 arXiv survey) | Triplet-based representations; time-based sampling |
| Eldele et al., TS-TCC | IJCAI 2021, pp. 2352–2359 | SECONDARY_SUMMARY | Contrastive temporal and contextual learning with augmentation |
| Yue et al., TS2Vec | arXiv:2106.10466; AAAI 2022 [M for venue] | ABSTRACT_ONLY (earlier session) | Hierarchical multi-scale contrastive representation |
| Nie et al., PatchTST (A Time Series is Worth 64 Words) | ICLR 2023; arXiv:2211.14730 | ABSTRACT_ONLY (arXiv v2 text excerpts: patching, channel independence, masked reconstruction with 40% of patches masked) | Patch tokens and masked pretraining. Its reported forecasting gains are not evidence for selection. Repository README percentages were not used |
| Ansari et al., Chronos | arXiv:2403.07815 (TMLR 2024) | ABSTRACT_ONLY (arXiv html excerpt); licence Apache-2.0 from PyPI metadata (`chronos-forecasting` 2.3.2, last upload 2026-09-08) | Pretrained probabilistic forecaster. Forecasting benchmark, not a structure benchmark |

### B.6 Structured inference, tracking and sequential decision

| Source | Venue/ID | Class | Relevance |
|---|---|---|---|
| Kschischang, Frey & Loeliger, Factor graphs and the sum-product algorithm | IEEE Trans. Inf. Theory 47(2), 2001 | UNVERIFIED (from memory) | Formalism for the coherence layer |
| Reid, An algorithm for tracking multiple targets | IEEE TAC 24(6), 1979 | UNVERIFIED | Multiple-hypothesis tracking origin |
| Ho & Ermon, Generative Adversarial Imitation Learning | arXiv:1606.03476 | ABSTRACT_ONLY | Requires an expert policy, which this task lacks |
| Burges, From RankNet to LambdaRank to LambdaMART | MSR-TR-2010-82 | UNVERIFIED | Listwise ranking background |

### B.7 Market microstructure and LOB prediction (boundary evidence)

| Source | Venue/ID | Class | Relevance and limit |
|---|---|---|---|
| Zhang, Zohren & Roberts, DeepLOB | arXiv:1808.03668; IEEE TSP vol. 67 no. 11, 2019, starting p. 3001 (from PDF header) | ABSTRACT_ONLY plus method excerpts (labelling section) | Labels are direction classes from smoothed future mid-price means against a threshold α. **Demonstrates the future-label construction that must not be used for structure.** Its benchmark (LOB mid-price direction) does not test wave or reference selection |
| Cont, Kukanov & Stoikov, The price impact of order book events | arXiv:1011.6402 | ABSTRACT_ONLY | Order-flow imbalance and short-horizon price change; background only |

## C. Gap statement

- **No source in this map tests contextual selection among market structure representations** (the owner's central question). The closest evidence is partial-label learning and set-based MIL, which are general methods, not market evidence.
- **No source validates ICT concepts** as objective market features. The earlier foundation's ICT sources are educational and of low evidence grade (see the foundation's source register). They define candidate operational rules, not validated relations.
- **Most method evidence is secondary or abstract-level.** A full-text read of Fearnhead & Liu, Cour et al., Gibbs & Candès, Ilse et al., and Franceschi et al. is a prerequisite before any citation is treated as a method specification.

## D. Open-source implementation findings

Checked this session: PyPI JSON metadata (licence, latest upload), and official documentation where noted. Popularity was not used as a criterion.

| Package | Licence | Latest PyPI upload (verified) | Relevance | Maintenance note |
|---|---|---|---|---|
| `river` (online ML) | verified via PyPI summary "Online machine learning in Python"; licence field not populated in metadata | 0.26.1, 2026-08-21 | Streaming learners and incremental statistics; candidate for incremental feature computation | Actively released |
| `hmmlearn` | BSD (classifier field) | 0.3.3, **2024-10-31** | Gaussian and categorical HMMs; no explicit-duration model | Older release; check before depending on it |
| `statsmodels` | (licence classifier not parsed) | 0.15.0, 2026-08-27 | Markov-switching regression and related models | Actively released; verify the regime model's assumptions before use |
| `lightgbm` | MIT (AR-1 verification) | 4.7.0, 2026-07-18 | Ranking objectives (lambdarank; rank_xendcg) with integer relevance labels | Official docs read |
| `torch` | (not parsed) | 2.14.1, 2026-09-30 | Needed for any neural encoder (S3) | Heavy dependency; only if S3 is built |
| `chronos-forecasting` | Apache-2.0 (PyPI classifier) | 2.3.2, 2026-09-08 | Pretrained forecaster; not designed for structure selection | Possible comparator only |
| `pytorch-forecasting` | MIT (classifier) | 1.8.0, 2026-06-24 | Forecasting datasets and models | Not needed for stage 1 |
| `hypothesis` | (licence not parsed) | 6.169.0, 2026-10-11 | Property-based testing for contract tests | Actively released; directly useful for kernel contracts |
| `ruptures` | BSD-2-Clause | 1.1.10, 2025-11-27 | Offline changepoint baselines | Baseline only |
| `bayesian_changepoint_detection` (GitHub, earlier session) | MIT | GitHub push 2026-09-24 | BOCPD reference implementation | Reimplementation from the paper is an acceptable alternative |

Not verified this session: no explicit-duration HSMM library was found and checked. S1 therefore likely requires an in-house implementation of a bounded-duration segmentation filter, with tests against synthetic data. This is a build-cost point, not a finding of absence.
