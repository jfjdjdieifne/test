# 09 — Open-Source and Academic Methods

## 9.1 Scope

This file lists components that address specific sub-problems of the foundation. Inclusion does not mean recommendation to import. Code was **not** inspected or run (OS1 grade throughout). Licenses were verified only where stated. The mission prohibits importing code in this research phase.

Fields: ID · reference · URL · license · maintenance · capabilities (verified) · causal/hindsight behavior · training/inference needs · relevance · what it cannot solve.

---

## 9.2 Academic methods

### OS-01 — Bayesian Online Changepoint Detection (BOCPD)

- **Reference:** Adams, R. P. & MacKay, D. J. C. (2007), "Bayesian online changepoint detection," arXiv:0710.3742. https://arxiv.org/abs/0710.3742
- **Grade:** AC1 (abstract read).
- **Verified claims:** changepoints are abrupt variations in generative parameters; the paper derives an online algorithm for exact inference of the most recent changepoint; it computes the distribution over run length (time since last changepoint) by message passing; the implementation is modular across data types; it is demonstrated on three real datasets. The abstract names finance as one application area.
- **Causal behavior:** causal. Uses data up to t.
- **Training/inference:** requires a predictive model per run with a conjugate-style or other tractable form (the abstract says the parameters before and after changes are independent); a hazard function. Inference is cheap per step.
- **Relevance:** online movement-state change (file 01 §1.8). Not a structure-break detector in the ICT sense.
- **Cannot solve:** whether a statistical change is a market-structure event; the choice of observation model; non-independent regimes (the abstract's assumption).
- **Licence/maintenance:** not checked in this session.

### OS-02 — PELT (Pruned Exact Linear Time)

- **Reference:** Killick, R., Fearnhead, P., & Eckley, I. A. (2012), "Optimal detection of changepoints with a linear computational cost," Journal of the American Statistical Association 107(500): 1590–1598. DOI 10.1080/01621459.2012.737745. Library record read (Lancaster University research directory).
- **Grade:** AC1 (bibliographic record; algorithm described through the OS-03 documentation).
- **Verified claims:** the algorithm finds optimal segmentation under a penalty with a pruning rule that reduces computational cost (per ruptures documentation: average complexity O(CKn) under conditions, C = cost-call complexity, K = number of changes, n = samples).
- **Causal behavior:** **offline**. It uses the full series. Not valid as a live causal detector.
- **Training/inference:** cost function and penalty choice; cheap relative to brute force.
- **Relevance:** research labeling of movement segments; comparing offline segments against online detections for evaluation.
- **Cannot solve:** online detection; interpretation of segments as market structure; penalty selection.

### OS-03 — ruptures documentation of PELT (the PELT description cited in OS-02)

- **URL:** https://centre-borelli.github.io/ruptures-docs/user-guide/detection/pelt/ (documentation page read as search snippet; S2). Repository metadata and maintenance are in OS-09.
- **Use here:** source for the O(CKn) complexity statement and for the min_size/jump grid controls quoted in OS-02.

### OS-04 — Generative Adversarial Imitation Learning (GAIL)

- **Reference:** Ho, J. & Ermon, S. (2016), "Generative Adversarial Imitation Learning," arXiv:1606.03476. https://arxiv.org/abs/1606.03476
- **Grade:** AC1 (abstract read).
- **Verified claims:** learns a policy directly from expert demonstrations, without interaction with the expert or reinforcement signal; draws an analogy to generative adversarial networks; reports performance gains over existing model-free imitation methods on complex behaviors in large, high-dimensional environments.
- **Causal behavior:** the learned policy acts on the current state; training uses recorded demonstrations (the training data is hindsight-free only if the demonstrations were recorded causally).
- **Training/inference:** requires demonstration trajectories with states and actions, and an adversarial training loop.
- **Relevance:** conceptual reference for "learning from demonstrations" (mission §4). The demonstrated action here would be a candidate selection, not a trade.
- **Cannot solve:** chart-interpretation demonstrations do not exist in the required format; expert bias is learned as a feature; the paper's environments are simulated control tasks with interactive dynamics.

### OS-05 — TS2Vec: Towards Universal Representation of Time Series

- **Reference:** Yue, Z., Wang, Y., Duan, J., Yang, T., Huang, C., Tong, Y., & Xu, B. (2022), AAAI-22; arXiv:2106.10466. https://arxiv.org/abs/2106.10466
- **Grade:** AC1 (abstract read).
- **Verified claims:** hierarchical contrastive learning over augmented context views produces timestamp-level representations; subsequence representations via aggregation of timestamp representations; evaluated on 125 UCR and 29 UEA datasets for classification, plus forecasting and anomaly detection. Source code public.
- **Causal behavior:** the paper's representation at timestamp t uses a context window; whether the context is strictly past-only in an implementation must be checked (not verified; it is a design-check item for any financial use).
- **Training/inference:** unsupervised training on time series; GPU helpful.
- **Relevance:** self-supervised representation for candidate similarity and multiscale context (file 07 §7.3.5).
- **Cannot solve:** explain representation content; guarantee transfer to financial bars; provide ICT concepts.

### OS-06 — Purged and embargoed cross-validation (López de Prado)

- **Reference:** López de Prado, M. (2018), *Advances in Financial Machine Learning*, Chapter 7 (book not read in this session). Secondary descriptions read: an article (Medium, S1) and a concept page (quantmemo, S1).
- **Grade:** S1 (secondary). Book content not verified.
- **Verified claims (via secondary):** purging removes training observations whose label windows overlap test observations; embargo removes a buffer after the test block; combinatorial purged CV generates multiple test paths.
- **Causal behavior:** a validation method, not a model. Its purpose is leakage control. Its correctness depends on correctly computed label windows.
- **Relevance:** mandatory evaluation protocol for file 07.
- **Cannot solve:** leakage in feature engineering (an open-source purged-CV repository states this explicitly, OS-11); selection bias from many configurations; regime shift.

### OS-07 — Academic claim: order-flow imbalance and short-horizon price impact

- **Reference:** Cont, R., Kukanov, A., & Stoikov, S. (2014), "The Price Impact of Order Book Events," Journal of Financial Econometrics 12(1): 47–88 (preprint arXiv:1011.6402). https://arxiv.org/abs/1011.6402
- **Grade:** AC1 (abstract read).
- **Verified claims (G-level, with scope):** using NYSE TAQ data for 50 US stocks, over short time intervals, price changes are mainly driven by order flow imbalance (imbalance between supply and demand at the best bid and ask); the relation is linear with slope inversely proportional to market depth; robust to seasonality, stable across time scales and stocks in that study; the relation between price changes and trade volume is noisier.
- **Causal behavior:** the imbalance is computed from order-book events up to t.
- **Relevance:** the strongest verified microstructure relation in this set. It requires **order-book event data**, which OHLC bars do not contain. It is therefore a potential data-enrichment direction, not something the current chart-based concepts can use.
- **Cannot solve:** chart-level liquidity claims; stop-cluster mechanisms; anything about bars without order-book data; applicability to futures or FX without separate study.

### OS-08 — Multiscale and segmentation literature (not individually verified)

Areas the mission asks for, with known references the researcher expects to exist but **did not verify in this session** (AC2 status, to check before use): time-series segmentation surveys (e.g., Keogh et al.), hidden Markov models (e.g., Rabiner 1989 tutorial), wavelet multiresolution analysis, and Bai–Perron multiple structural-break tests. Each should be checked against its primary publication before citation in any audit trail.

---

## 9.3 Open-source components

### OS-09 — ruptures (change-point detection in Python)

- **URL:** https://github.com/deepcharles/ruptures
- **Read in session:** repository landing page (OS1).
- **License:** BSD 2-Clause ("BSD 2-Clause 'Simplified'"; copyright 2017–2021, ENS Paris-Saclay, CNRS). Verified this round from the repository LICENSE file (OS1).
- **Maintenance:** repository shows 600 commits, 9 branches, 19 tags; recent commits in May 2026 (e.g., "Added L1Potts class," "drop Python 3.9 and update dev tooling"). Latest-commit CI status is displayed as "failure" on the landing page at the time of reading. Treat as active but with a failing check that should be investigated before dependence.
- **Capabilities (documentation read):** includes PELT (OS-02) and a documented min_size and jump parameter for PELT grid control.
- **Causal behavior:** offline algorithms; not for live causal use.
- **Relevance:** research segmentation and evaluation baselines.
- **Cannot solve:** online detection; market semantics.

### OS-10 — TS2Vec official implementation

- **URL:** https://github.com/zhihanyue/ts2vec (landing page read; the link https://github.com/yuezhihan/ts2vec in the abstract redirects to this repository).
- **License:** MIT (copyright 2022, Zhihan Yue). Verified this round from the repository LICENSE file (OS1).
- **Maintenance:** 27 commits; most recent commit shown as "Fix typo" in June 2023; the landing page lists pinned requirements (Python 3.8, torch 1.8.1, scipy 1.6.1, numpy 1.19.2, pandas 1.0.1, scikit-learn 0.24.2, statsmodels 0.12.2, Bottleneck 1.3.2). These pins are old; a modern environment would need checking.
- **Capabilities:** training and evaluation scripts for UCR/UEA-style datasets and other listed benchmarks.
- **Causal behavior:** must be audited for past-only context in any financial use.
- **Relevance:** reference implementation for representation learning experiments.
- **Cannot solve:** financial representation quality; regime generalization; interpretability.

### OS-11 — Purged cross-validation repository (landtml/purgedcv)

- **URL:** https://github.com/landtml/purgedcv
- **Read in session:** repository description (OS1, search snippet and landing content).
- **License:** MIT (copyright 2026, landtml). Verified this round from the repository LICENSE file (OS1). The LICENSE page showed a commit dated 2026-07-23 ("Restructure as a proper package"); the package has changed since the earlier read.
- **Capabilities (per description):** scikit-learn-compatible combinatorial purged CV with embargo; the description states it produces splits and a path map and does not compute returns or performance metrics; it states it does **not** detect leakage in feature engineering.
- **Maintenance:** not verified (no commit history read).
- **Causal behavior:** split-level only; the user must compute label windows correctly.
- **Relevance:** candidate evaluation harness for file 07 §7.4. **Its description includes claims of a "formal no-leakage proof" and "independent empirical verification against ~98 years of real market data"; these claims were not verified and should be treated as the author's claims.**
- **Cannot solve:** feature leakage, hyperparameter overfitting, label design.

### Other components considered and not recommended in this version

- Generic "technical analysis" libraries: they compute indicators (B-level measurements) and do not address candidate selection or knowability. Not reviewed in depth; not recommended as a basis for contextual selection.
- Automatic "ICT indicator" scripts found in community results: not inspected; their definitions are unknown and often unverified. Not recommended for use as evidence.
- LLM-based chart readers: excluded by the mission's no-external-API constraint and by the lack of verified evidence (file 07 §7.3.9).

---

## 9.4 What a future team should evaluate first (research recommendation)

1. **Causal snapshot and knowability tracking** (no external library needed).
2. **Deterministic candidate generators with canonical test cases** (no library needed).
3. **Purged/embargoed splitter** (candidates: write locally, or evaluate OS-11 after license check).
4. **Offline segmentation baseline** (OS-09) for research labeling only.
5. **Causal change detection** (OS-01-style implementation) for online movement state, evaluated against labeled changes.
6. **Representation learning** (OS-05) only after a labeled downstream task exists.
7. **Order-book data** (OS-07) only if the project obtains order-book data; then its relations can be tested, not assumed.
