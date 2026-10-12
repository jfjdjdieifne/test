# 01 — Academic References and Open-Source Candidates (C, D)

Tags: `[V]` verified this session or in an earlier session (abstract, page or repository metadata read); `[M]` bibliographic detail from memory, must be checked before citation. Repository metadata is licence and activity only. **README claims are not performance evidence.**

## C. Academic references

### C.1 Changepoints and segmentation (swing-candidate generation, baselines)

- Adams, R. P. & MacKay, D. J. C. (2007). *Bayesian Online Changepoint Detection.* arXiv:0710.3742. `[V]` abstract. Online, causal run-length posterior. Relevant as a causal candidate generator and as a baseline. Its output is a probability of a changepoint, which is not the same as a validated swing.
- Killick, R., Fearnhead, P. & Eckley, I. A. (2012). *Optimal detection of changepoints with a linear computational cost.* JASA 107(500). DOI 10.1080/01621459.2012.737745 `[V]` metadata. Exact penalised segmentation (PELT). Offline: uses the whole segment, so it is **not causal** and must not be used for knowable-at-time candidates without a leakage test.
- Segment-based BOCPD, DOI 10.1145/3459637.3482167 `[V]` metadata (ACM proceedings; the venue and year are not confirmed in this session, so check before citing). Reference for segment-level extensions; not yet evaluated for this use.

### C.2 Representation learning for time series (optional comparators, not doctrine)

- Franceschi, J.-Y., Dieuleveut, A. & Jaggi, M. (2019). *Unsupervised scalable representation learning for multivariate time series.* NeurIPS, vol. 32. `[V]` citation via a verified secondary survey. Triplet-based (T-Loss) representation with time-based sampling. Relevant as an unsupervised comparator; sampling choices must be checked for leakage of future context into representations used for past decisions.
- Eldele, E. et al. (2021). *Time-series representation learning via temporal and contextual contrasting (TS-TCC).* IJCAI, pp. 2352–2359. `[V]` citation via verified secondary survey.
- Yue, Z. et al. (2022). *TS2Vec: Towards universal representation of time series.* arXiv:2106.10466 `[V]` abstract. Hierarchical contrastive representation at multiple scales. Relevant because its multi-scale structure resembles the scale-indexed candidate design. Check whether its context windows are causal for each use.

### C.3 Structured prediction and joint inference

- Kschischang, F. R., Frey, B. J. & Loeliger, H.-A. (2001). *Factor graphs and the sum-product algorithm.* IEEE Trans. Inf. Theory 47(2). `[M]`. Formalism for the coherence layer.
- Koller, D. & Friedman, N. (2009). *Probabilistic Graphical Models.* MIT Press. `[M]`. Reference for exact and approximate inference, and for when joint structure is worth its cost.
- Lafferty, J., McCallum, A. & Pereira, F. (2001). *Conditional random fields.* ICML. `[M]`. Discriminative joint labelling over sequences; relevant analogue for conditional coherence scoring.
- Taskar, B., Guestrin, C. & Koller, D. (2004). *Max-margin Markov networks.* NeurIPS. `[M]`.
- Tsochantaridis, I. et al. (2005). *Large margin methods for structured and interdependent output variables.* JMLR. `[M]`.

### C.4 Ranking (contextual selection inside the admissible set)

- Burges, C. J. C. (2010). *From RankNet to LambdaRank to LambdaMART: an overview.* Microsoft Research Technical Report MSR-TR-2010-82. `[M]`. Listwise objectives for choosing among candidates.

### C.5 Multi-hypothesis tracking (keeping alternative interpretations alive)

- Reid, D. B. (1979). *An algorithm for tracking multiple targets.* IEEE Trans. Automatic Control 24(6). `[M]`. The original MHT formulation: keep multiple hypotheses, prune with explicit rules, track which hypotheses were pruned.
- Blackman, S. S. (2004). *Multiple hypothesis tracking for multiple target tracking.* IEEE Aerospace and Electronic Systems Magazine. `[M]`.

The architectural transfer is conceptual: alternative swing or reference interpretations are hypotheses; pruning must be budgeted and recorded.

### C.6 Neuro-symbolic constraints and weak supervision

- Xu, J. et al. (2018). *A semantic loss function for deep learning with symbolic knowledge.* ICML. `[M]`. Penalises outputs that violate logical constraints. Relevant to making kernel constraints differentiable if ever needed; the first stage uses hard filtering instead.
- Garcez, A. d'A. & Lamb, L. C. (2020). *Neurosymbolic AI: the 3rd wave.* arXiv:2012.05876. `[M]`. Survey framing.
- Ratner, A. et al. (2018). *Snorkel: rapid training data creation with weak supervision.* VLDB. arXiv:1711.10160. `[M]`. Labelling functions combined by a generative label model. Relevant to combining declared rules and annotator heuristics; noisy labels must carry their source and be sensitivity-tested.

### C.7 Continual learning and replay

- Kirkpatrick, J. et al. (2017). *Overcoming catastrophic forgetting in neural networks.* PNAS. `[M]`. Elastic weight consolidation. Not selected for stage 1; see file 04.
- Ross, S., Gordon, G. & Bagnell, D. (2011). *A reduction of imitation learning and structured prediction to no-regret online learning (DAgger).* AISTATS. `[M]`. Relevant to recording the system's own decisions and their corrections, and to the danger of training on its own outputs.
- Ho, J. & Ermon, S. (2016). *Generative adversarial imitation learning.* arXiv:1606.03476 `[V]` abstract. Not recommended for this system (requires an expert policy that does not exist for market analysis).

### C.8 Uncertainty and calibration

- Angelopoulos, A. N. & Bates, S. (2021). *A gentle introduction to conformal prediction and distribution-free uncertainty quantification.* arXiv:2107.07511 `[M]`. Coverage guarantees rely on exchangeability; time series violate it, so any conformal method here must use time-blocked calibration and report the caveat.
- Gal, Y. & Ghahramani, Z. (2016). *Dropout as a Bayesian approximation.* ICML. `[M]`. Approximate predictive uncertainty by ensembles or dropout; ensembles are preferred for the first stage because they are simpler to audit.

### C.9 Financial-evaluation methodology (applies to objectives E and F)

- López de Prado, M. (2018). *Advances in Financial Machine Learning.* Wiley. `[M]`. Purged and embargoed cross-validation; sample weighting; warning on label leakage through overlapping horizons.
- Bailey, D. H., Borwein, J., López de Prado, M. & Zhu, Q. J. (2017). *The probability of backtest overfitting.* Journal of Computational Finance. `[M]`.
- Bailey, D. H. & López de Prado, M. (2014). *The deflated Sharpe ratio.* Journal of Portfolio Management. `[M]`. Adjusts for multiple trials; applies only if a metric of that kind is ever used.

### C.10 Regime and structure modelling

- Hamilton, J. D. (1989). *A new approach to the economic analysis of nonstationary time series and the business cycle.* Econometrica 57(2). `[M]`. Markov regime switching; a candidate hidden-state model for regime-conditioned admissibility, not used in stage 1.

### C.11 Market microstructure (context for liquidity-level definitions)

- Cont, R., Kukanov, A. & Stoikov, S. (2014). *The price impact of order book events.* Journal of Financial Econometrics (journal details `[M]`). arXiv:1011.6402 `[V]` abstract. Shows that short-horizon price changes relate to order-flow imbalance. Used only as background; it does not validate any ICT concept.

## D. Verified open-source candidates

Checked this session via the GitHub API (licence, language, last push, default branch) or the repository's LICENSE file. "Fit" describes the role in this architecture; it is not a popularity or quality claim. Each candidate must be re-checked for maintenance and tests before adoption.

| Candidate | Licence (verified) | Language | Last push (verified) | Role in this design | Adoption stance |
|---|---|---|---|---|---|
| `deepcharles/ruptures` | BSD-2-Clause `[V]` (LICENSE file) | Python | Recent activity seen in earlier session | Offline changepoint baselines (PELT and others) for comparison | **Baseline only.** Offline, non-causal; never used for knowable-at-time candidate generation. |
| `hildensia/bayesian_changepoint_detection` | MIT `[V]` | Python | 2026-09-24 `[V]` | Reference implementation of online BOCPD | Candidate for causal baseline. Prefer reimplementation from the paper if the project must keep its dependency surface small; both options are permissible under MIT. |
| `pgmpy/pgmpy` | MIT `[V]` | Python | 2026-10-05 `[V]`; default branch `dev` `[V]`; 654 open issues `[V]` | Discrete factor graphs and probabilistic inference for small coherence components | Candidate for prototyping exact inference in components. Check whether its inference scales to the component sizes actually produced before adoption. |
| `lightgbm-org/LightGBM` (queried as `microsoft/LightGBM`; the API redirected) | MIT `[V]` | C++ core, Python and R interfaces | 2026-10-12 `[V]`; 539 open issues `[V]` | Gradient-boosted ranker for the unary layer (stage 1) | **Primary candidate** for the unary scorer: CPU-feasible, tabular, ranking objectives. Must be validated against baselines; it is chosen for fit, not popularity. |
| `pyg-team/pytorch_geometric` | MIT `[V]` | Python | 2026-10-06 `[V]` | Graph neural networks for relational coherence | **Deferred.** Consider only after stage-3 labels exist and a relational baseline fails. |
| `dstl/Stone-Soup` | MIT `[V]` | Python | 2026-10-09 `[V]`; 130 open issues `[V]` | Multi-target tracking framework; MHT-type algorithms per its description | **Design reference** for hypothesis management and pruning records. Adoption as a dependency is not recommended for stage 1; the framework targets sensor tracking and may bring a large surface. |
| `ContinualAI/avalanche` | MIT `[V]` | Python | **2025-03-11 `[V]`**, about 19 months before the review date; a maintenance risk | Continual-learning strategies (replay, regularisation) | **Reference only.** Stage 1 replay is simple enough to implement directly in the owner's pipeline. Re-check maintenance before any adoption. |
| `landtml/purgedcv` | MIT `[V]` (LICENSE file) | Python | Recent restructure commit `[V]` (per earlier session) | Purged and embargoed cross-validation splitters | **Candidate** for objective splits (file 03). Verify splitter semantics against the purge rule in file 03 before use. |
| `zhihanyue/ts2vec` | MIT `[V]` (LICENSE file) | Python | Not re-checked this session | Representation comparator (TS2Vec) | Optional comparator in stage 2+. Causality of its windows must be tested. |

### Candidates considered and not checked

Other packages (for example general feature-extraction libraries, other tracking or changepoint libraries) were not checked in this session. They are not recommended here; any future adoption requires its own licence, maintenance and causality check.

### Recorded limitations

- The repository metadata does not establish correctness, speed, or accuracy for any purpose in this system.
- Licence checks reflect the repository files as fetched; a licence in a subdirectory or vendored code was not checked.
