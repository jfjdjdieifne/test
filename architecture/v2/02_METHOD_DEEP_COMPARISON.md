# 02 — Deep Comparison of the Strongest Methods (C), Concept Mastery (§5), Movement Representation (§6)

Each method is described by what it can learn, what supervision it needs, what it cannot establish, how labels are obtained, how noise affects it, how uncertainty is handled, and how it is evaluated. Evidence classes follow file 01.

## 1. Movement and wave representation (§6, highest priority)

### 1.1 Scale representation

Options for representing scales, with their properties:

| Representation | What it is | Strength | Weakness | Evidence class |
|---|---|---|---|---|
| Fixed-window pivots (F-K in AR-1) | a bar is a turning point if it is extreme within k bars on each side, confirmed after k bars | Simple, causal once confirmed, auditable | Results depend strongly on k; a single k is an arbitrary declared value; confirmations are delayed | Deterministic |
| Reversal-size threshold (F-T) | a reversal is registered only after a declared move against the current leg | Simple; no time parameter | Threshold is a declared value; coarse thresholds hide fine structure (AR-1 worked case shows this) | Deterministic |
| Changepoint posteriors (S1) | a probability distribution over segment boundaries at a declared hazard/duration model | Represents uncertainty; gives alternatives; causal filtering is exact (Fearnhead & Liu, abstract) | Requires a model of segment behaviour; parameters must be fit or declared; posterior calibration is unverified | Abstract-level |
| Multi-scale hierarchy of segments | a tree of segments where each coarse segment contains fine segments | Matches "nested waves" directly | Containment must be enforced; tree construction is a modelling choice | Design |
| Wavelet or scale-space decompositions | decompose a signal into scale-indexed components | Explicit scale axis; classic signal analysis | Components are not turning points; mapping from coefficients to discrete structural objects is an extra, unvalidated step; boundary effects for causal use | UNVERIFIED for this use |
| Learned embeddings (TS2Vec, PatchTST-like) | representation vectors per window | Captures shape similarity | Not interpretable as turning points; similarity is not structure | Abstract / excerpt |

**Conclusion.** Scale should be a *declared index over generators*, not a learned quantity. The learned part should be the posterior over boundaries *within* a scale (S1) and the selection *among* admissible candidates (S2).

### 1.2 Turning points without future leakage

- **Causal test:** a turning point is usable at time t only if it is knowable at t. Fixed-window pivots become knowable only after the window. Filtering posteriors are knowable at each bar (no smoothing).
- **Smoothing is forbidden for decisions.** Offline methods (PELT, backward smoothing in HSMMs) use future data and may be used only for labels *in evaluation*, never as features.
- **Revision is explicit.** A candidate that changes after new bars becomes `superseded` with a link to its predecessor. The ledger shows both.

### 1.3 Linking nested movements

Two relations are factual and deterministic: **containment** (a fine leg lies inside a coarse leg's time and price span) and **shared endpoints** (two legs share a turning point). Both are kernel functions. Learned relations are not needed for linking; they are needed only for *which* linked interpretation is preferred (S2 plus constraint propagation).

### 1.4 Relevance to a declared task without a universal "important wave"

Relevance is defined by the task's declared role and admissibility rules. Example: "the reference for a declared structural reading" is admissible if it is confirmed at decision time, has the declared role relation to the current leg, and has not been violated. No candidate is intrinsically important. S2 learns only the expert's acceptance pattern inside that admissible set.

### 1.5 Distinguishing meaningful variation from artifacts

Three checks, all deterministic or label-free:
1. **Stability across declared parameter sweeps.** A candidate that appears only at one parameter value is flagged `FRAGILE`. The sweep is reported, not optimised.
2. **Agreement across independent generators** (F-K, F-T, S1). Agreement is a diagnostic count, not a truth signal.
3. **Gap and duplicate handling** in the bar store. Gaps create `UNKNOWN` segments rather than fabricated legs.

### 1.6 Generalization across volatility regimes and unfamiliar shapes

Generalization is an empirical claim and cannot be argued from the method. The design choices that make it testable:
- Features and posteriors are expressed in units of a *declared* scale measure, so that regime change is visible as a change in feature distribution rather than as a silent recalibration.
- Held-out regime evaluation is required (file 03): training and evaluation are split by volatility regime, not by random bars.
- Unfamiliar shapes are flagged by novelty measures (S3, if built) or by a posterior-entropy flag (S1), not handled silently.

## 2. Method comparison (C)

Ratings are ordinal design properties, not measured performance.

### 2.1 Causal segmentation and filtering

**Fearnhead & Liu (2007) — exact online filtering for multiple changepoints** (ABSTRACT_ONLY).
- *Learns:* posterior over the number and location of changepoints under a stated segment model. Can estimate segment parameters if the model includes them.
- *Supervision:* none required for the structure posterior; segment parameters may be fit on unlabelled history (EM or Bayesian updates).
- *Cannot establish:* that changepoints correspond to structural turning points the owner means; that the segment model is correct; relevance to ICT concepts.
- *Labels:* not needed for the posterior. Evaluation needs synthetic or annotated truth.
- *Noise:* the posterior spreads mass across boundaries when data are noisy; this is informative, not a failure, but it means a point selection requires a declared ambiguity rule.
- *Uncertainty:* the posterior itself. Calibration against annotated boundaries is not established.
- *Evaluation:* recovery of generator boundaries under declared families; coverage of annotated boundaries; posterior sharpness vs accuracy; causal-consistency test (filtering output on a truncated series equals the prefix of the full run).
- *Compute:* the exact method is quadratic in observations (abstract). The particle version is linear with approximation error (abstract). Choice depends on the data length per run.

**Explicit-duration HSMM** (Yu 2010; excerpts of the review and Dewar et al. 2012 `[V]` excerpts).
- *Learns:* segment durations and segment-level emission models with forward–backward inference.
- *Compute:* the review excerpt gives an explicit-duration forward–backward cost of order (M² + MD + MD²)T for M states and maximum duration D. Dewar et al. state that full-duration inference over long sequences is only tractable when durations are restricted to a bounded interval, and that truncation fails when true durations fall outside it.
- *Consequence for this project:* a bounded-duration filter with declared D is feasible; unbounded durations are not. D is a declared policy value and must be stated as such.
- *Implementation:* no maintained explicit-duration library was checked. Expect an in-house implementation.

**BOCPD** (Adams & MacKay 2007; ABSTRACT_ONLY). Same causal property; run-length posterior. Simpler than HSMM and not bounded by declared D, but its hazard function is a declared policy and it does not model nested scales directly. Serve as a baseline.

**PELT / offline changepoints** (Killick et al. 2012; METADATA_ONLY). Non-causal. Baseline for offline analysis and for label generation only if explicitly declared as offline; never a feature.

### 2.2 Partial-label and weakly supervised selection

**Partial-label learning** (Cour, Sapp & Taskar 2011; SECONDARY_SUMMARY).
- *Learns:* a classifier from examples each paired with a candidate set known to contain exactly one valid label.
- *Supervision:* candidate sets. For this project, the expert declares the acceptable candidate set for a snapshot and task.
- *Cannot establish:* which candidate is *correct*; only that the true label lies in the set.
- *Noise:* if the expert's set omits the valid candidate, the model is biased. Annotator agreement on sets must be measured.
- *Uncertainty:* the posterior over candidates within the set; disambiguation weights learned by the model.
- *Evaluation:* held-out annotated snapshots with a *set-coverage* metric (is the model's top choice inside the expert set?) and a *set-size* metric (how many candidates does the model need to cover the set?). Both are reported; neither claims correctness.

**Attention-based MIL** (Ilse et al. 2018; ABSTRACT_ONLY).
- *Learns:* bag-level labels from instance features via permutation-invariant attention; attention weights indicate instance contribution.
- *Fit for this project:* a snapshot-task is a bag; candidates are instances; the bag label is the expert's acceptable set. Attention gives an auditable contribution per candidate.
- *Cannot establish:* that attention weights are causal reasons; they are contributions *to the model's score*.
- *Compute:* small networks on CPU are plausible for small bags; training cost depends on bag size and count (not benchmarked here).

**Weak supervision with labelling functions** (Snorkel; Ratner et al. 2017/2018; ABSTRACT_ONLY plus method excerpt).
- *Learns:* accuracies and correlations of labelling functions without ground truth; produces probabilistic labels.
- *Fit for this project:* declared rules (for example, the owner's declared reference rule) become labelling functions, and expert heuristics become others. The label model estimates how much to trust each source.
- *Cannot establish:* accuracy against truth; it only aggregates sources whose dependence is modelled. Correlated rules that share a bug will be trusted together.
- *Noise handling:* the label model is the noise handler. Its estimated accuracies are themselves uncertain and must be reported.

**Positive-unlabelled and inverse reinforcement learning** (not recommended):
- PU learning assumes a labelled "positive" class sampled from the same distribution. Expert-chosen waves are not a random sample of positives; treating unchosen candidates as negatives asserts that they are wrong, which the owner's constraints forbid.
- IRL and GAIL (Ho & Ermon 2016, ABSTRACT_ONLY) model a sequence of expert actions in an environment. Expert wave-marking is not a sequential decision problem with a defined reward; the reward would have to be invented, which is equivalent to choosing the answer in advance.

### 2.3 Consistency and self-supervised learning

**Masked-patch reconstruction** (Nie et al. 2023; excerpts of arXiv v2 `[V]`). Learns to reconstruct masked patches of a univariate or channel-independent series. Reconstruction error measures predictive smoothness of the series, not structural understanding. The paper's evaluations are forecasting-error benchmarks.

**Contrastive temporal representations** (Franceschi et al. 2019; Eldele et al. 2021; Yue et al. 2022). These learn embeddings in which temporally close or augmented views are similar. Known failure modes for this project:
- *Trivial features:* the model can use a slow trend or a volatility level that is easy to match across augmented views, which carries no structure.
- *Leakage:* sampling negatives or positives using future windows couples the representation to information unavailable at decision time.
- *Mitigation:* causal windows only; augmentation families declared and reported; evaluation on annotated structural selections rather than on embedding quality.

**Cross-scale consistency** (idea, supported by multi-scale representation papers only as design motivation). A coarse segment should contain its fine segments. This is a hard constraint in the kernel, so it need not be learned. Learned use of it is redundant unless constraints are violated by a learned component.

### 2.4 Structured inference and joint interpretation

**Hard-constraint propagation over the ledger** (deterministic; no reference required beyond the design).
- *Learns:* nothing.
- *Gives:* exact consistency: which combinations of selections violate declared relations.
- *Cost:* linear in the number of links per task pair, with index queries.
- *Limit:* cannot rank consistent alternatives.

**Factor graphs with learned pairwise factors** (Kschischang et al. 2001; UNVERIFIED).
- *Learns:* pairwise potentials among linked task variables.
- *Requires:* annotated pairwise coherence labels, which do not exist; or synthetic consistency labels, which measure generator-hierarchy recovery only.
- *Cost:* exact inference is exponential in the worst case over component size; approximate inference (belief propagation) has no guarantee on loopy graphs.
- *Decision:* not adopted in the first build. Adopt only if an annotated held-out comparison shows that learned pairwise factors change selections in a direction the experts prefer, beyond what hard constraints already do.

**Graph neural networks** (Kipf & Welling 2017; UNVERIFIED). Learn message passing over candidate graphs. Require large labelled relational data; the risk of learning relational shortcuts is high. Not recommended before annotated relational data exist. PyTorch Geometric licence and activity were verified in AR-1 (MIT; pushed 2026-10-06).

**Multiple-hypothesis tracking** (Reid 1979; Blackman 2004; UNVERIFIED). Maintains alternative hypotheses with explicit pruning records. Architecturally relevant to the "two wave interpretations" case. Adopt the bookkeeping, not necessarily the tracker.

### 2.5 Ranking and gradient-boosted selectors

**LightGBM LambdaRank and rank_xendcg** (official documentation read `[V]`).
- *Learns:* a scoring function optimised for ranking metrics.
- *Supervision:* integer relevance labels. The documentation states that label values should be integers and that larger values represent higher relevance (example 0 bad, 1 fair, 2 good, 3 perfect). For lambdarank, labels must be smaller than the `label_gain` length.
- *Implication:* a ranker commits to an ordering and to a grade scale. Expert set annotations (S2) do not provide that. Use LightGBM as a comparator on S1 features only, if at all.
- *Compute:* CPU-friendly for tabular data.

### 2.6 Uncertainty and calibration

- **Temperature scaling** (Guo et al. 2017; SECONDARY_SUMMARY). A single scalar fitted on held-out data; the source notes that it works when the test distribution matches the training distribution. Market regime change violates this, so it cannot be relied on across regimes.
- **Conformal methods for time series** (Gibbs & Candès 2021; Xu & Xie 2021; SECONDARY_SUMMARY). Provide adaptive coverage under shift, with theory whose assumptions (known shift size, hidden Markov structure, no refit) are later relaxed in the literature. Use for interval-like or set-like outputs, with coverage reported over time blocks, not as a probability of correctness.
- **Posteriors from S1** are model-based. Their calibration against annotated boundaries must be measured, not assumed.

## 3. Concept mastery: necessity analysis (§5)

| Technique | Necessary? | Use in this project | Reason |
|---|---|---|---|
| Executable semantic contracts (typed, deterministic functions over closed bars) | **Necessary** | Each concept is a function with declared inputs, a knowability time, and an output status (`TRUE`, `FALSE`, `UNKNOWN`, `AMBIGUOUS`) | Makes definitions testable and removes hidden state |
| Lightweight typed time (`known_at` vs `event_time`) | **Necessary** (cheap) | Runtime type or assertion that no feature uses data later than `known_at` | Prevents the most common leakage class |
| Property-based testing (Hypothesis, PyPI 6.169.0 verified) | **Necessary** | Properties such as: a reclaim cannot be recognised before its crossing bar; a confirmed pivot is never removed by later bars; crossing queries return all crossings | Strong, cheap verification of kernel invariants |
| Metamorphic testing | **Necessary** | Adding a constant to all prices leaves price-difference definitions invariant; scaling all prices by a positive constant leaves ratio definitions invariant; appending bars leaves past confirmed outputs invariant; shifting the window start leaves relative structure invariant | Gives test oracles without ground truth labels |
| Temporal logic with robust semantics (STL; Maler & Nickovic 2004; Donzé et al. 2013, `[V]` abstract) | **Optional** | Express a declared sweep as "cross then reclaim within window" with quantitative margins | Useful when margins matter. A finite automaton suffices for discrete events. Do not introduce margin values without declaration |
| Formal verification (SMT/SAT) of constraint sets | **Unnecessary at current scale** | Exhaustive enumeration over small admissible sets is sufficient | Adds tooling without a demonstrated need |
| Program synthesis of concept rules from data | **Unnecessary and risky** | — | Synthesis from data would create doctrine that the owner has not declared |
| Neuro-symbolic concept learning with semantic loss (Xu et al. 2018; UNVERIFIED) | **Deferred** | Only if S2 must respect logical constraints in training | Hard filtering suffices for stage 1 |
| Machine learning for deterministic operations (e.g., reclaim detection) | **Forbidden** | — | A learned detector cannot be audited against a definition |

### 3.1 The liquidity-sweep example, in this framework

The owner's definition: a previously knowable reference level; a subsequent crossing; a declared return or reclaim condition; an explicit observation timeframe.

Executable form (no learning):
- Inputs: closed bars at the declared timeframe; a reference set with `known_at` times.
- State machine per reference: `UNTOUCHED → CROSSED(bar) → RECLAIMED(bar, within window) | FAILED(window expired)`.
- Intrabar ambiguity: if a single bar both crosses and reclaims a reference and the timeframe does not disambiguate order, the status is `UNKNOWN` (never assumed).
- The window and the reclaim condition are declared parameters with stated status.

What this does **not** establish: that resting orders (stop clusters) existed at the level. OHLC contains price and time, not the order book. The output is a price-behaviour pattern, and the documentation must say so.

## 4. Strongest methods — summary table

| Method | Learns | Label need | Handles wave ambiguity by | Causal risk | Maturity of implementation | Verdict |
|---|---|---|---|---|---|---|
| Fearnhead–Liu filtering / bounded HSMM filter (S1) | segment posterior, segment parameters | none for posterior | distributions over partitions | low if filtering only | exact method exists; implementation in-house | **Candidate A, first build** |
| Partial-label / attention-MIL selector (S2) | acceptance over admissible sets | expert acceptable sets | set-valued targets; attention | medium (features must be causal) | general methods; no market implementation found | **Candidate B, after annotation** |
| Masked/contrastive temporal encoder with retrieval (S3) | embeddings, analogues | none | similarity, not partitions | medium-high (leakage through sampling) | libraries exist (`torch`; Chronos Apache-2.0 for forecasting) | **Candidate C, gated research** |
| LightGBM LambdaRank | graded ordering | integer grades | none | low | mature | Comparator only |
| Factor graph with learned factors | joint potentials | annotated pairwise labels | joint alternatives | low | mature formalism | Deferred |
| GNN over candidates | relational messages | relational labels | implicit | medium | mature libraries | Not recommended now |
| IRL / GAIL | reward/policy from demonstrations | sequential demonstrations | none | — | — | Rejected for this task |
