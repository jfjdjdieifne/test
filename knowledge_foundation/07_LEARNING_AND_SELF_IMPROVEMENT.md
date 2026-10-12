# 07 — Learning and Self-Improvement

## 7.1 Purpose

Explain how a local Python system could learn contextual selection (which candidate to use for which task) from source-supported knowledge, annotated examples, and historical market data, without memorizing chart examples and without leaking future information into training.

## 7.2 Six learning targets — do not conflate them

| # | Target | Question it answers | Typical measurement |
|---|---|---|---|
| 1 | Concept fidelity | Does the implementation follow the stated definition (e.g., G-OB-P vs G-OB-C)? | Unit tests against written examples; agreement with a reference implementation |
| 2 | Extraction correctness | Are the bars, swings, levels and zones computed correctly from data? | Recomputation checks; data-quality tests; manual audits on sampled charts |
| 3 | Contextual selection | Given the task, which candidate is chosen (and which alternatives kept)? | Agreement with annotated selections; calibration of alternatives; ablation of context features |
| 4 | Interpretation quality | Is the resulting interpretation coherent, with ledger, falsifiers, and revisions? | Expert rubric; consistency checks; falsifier coverage |
| 5 | Predictive usefulness | Do the features/candidates have statistical relation to future movement? | Out-of-sample, purged evaluation; baseline comparisons |
| 6 | Trading decision quality | Do decisions based on the interpretation produce acceptable risk-adjusted results? | Out of scope for this research (H); requires execution and cost modeling |

**Rule:** a high score on one target says nothing about the others. For example, a system can have perfect concept fidelity (it implements G-OB-P exactly) and poor predictive usefulness. A system can predict well by exploiting a computational artifact (e.g., a look-ahead bug) while having poor extraction correctness.

## 7.3 Learning approaches compared

For each approach: problem solved, training information needed, evaluation, leakage prevention, generalization, uncertainty, compute, limitations.

### 7.3.1 Explicit analytical knowledge (rules)

- **Problem solved:** concept fidelity (target 1); auditability; transparency of candidate generators.
- **Training information:** none; the definitions are the knowledge. Source text (P1/S1).
- **Evaluation:** unit tests on hand-written cases; reproducibility.
- **Leakage:** avoided by construction if knowability is enforced in code.
- **Generalization:** only as far as the definitions cover; no adaptation.
- **Uncertainty:** represented as the set of alternative generators, not as probabilities.
- **Compute:** trivial.
- **Limitations:** cannot discover contextual selection; ICT source definitions conflict (CF-01); parameters unresolved (e.g., "near," tolerance).

### 7.3.2 Structured contextual inference (explicit probabilistic or rule-based context model)

- **Problem solved:** combining context features (scale, structure reading, liquidity status) into a ranked set of interpretations with explicit assumptions.
- **Training information:** can be small; parameters may be set by domain judgment and then validated.
- **Evaluation:** calibration against annotated cases; sensitivity analysis of each parameter.
- **Leakage:** same as rules; ensure all features are causal.
- **Generalization:** better than rules if features are truly contextual; sensitive to misspecification.
- **Uncertainty:** explicit (can represent competing hypotheses).
- **Compute:** low.
- **Limitations:** the structure is chosen by the designer; a wrong structure yields confident-looking but wrong ranks (cascading error, file 06 §6.4).

### 7.3.3 Learning from demonstrations (imitation)

- **Problem solved:** learning which candidate an expert selected in a context, when the expert's choices are recorded.
- **Verified method family:** generative adversarial imitation learning, which derives a policy from expert demonstrations via an adversarial formulation without explicit reward recovery [OS-04]. The paper is about control environments with an interactive expert setting.
- **Training information:** recorded expert decisions with the state the expert saw (the causal chart state at the decision time). The decision is the label; the expert's reasons are not a label.
- **Evaluation:** agreement with held-out expert decisions; but agreement with a teacher is not correctness.
- **Leakage:** the demonstration state must be snapshot-at-time; annotations made after seeing the outcome are not demonstrations of selection and must be excluded or flagged.
- **Generalization:** only to contexts similar to the demonstrations; it learns the expert's habits, including biases.
- **Uncertainty:** the expert's disagreement can be recorded as soft labels; GAIL-type methods do not naturally produce calibrated uncertainty.
- **Compute:** moderate, but the data bottleneck is labeling.
- **Limitations:** the cited paper addresses imitation in simulated environments with a continuing state; applying it to chart selection requires a new formulation. Demonstrations from ICT videos are not recorded decisions with the causal state, and the ICT lesson text read does not provide a labeled dataset (see §7.5).

### 7.3.4 Supervised contextual ranking

- **Problem solved:** given a task and a set of candidates at bar t, rank them by relevance for that task. Label must be defined by the task (e.g., "candidate was later used as a reference," which is itself hindsight and must be labeled as such).
- **Training information:** candidate sets snapshot at t, and labels from later bars, with purged splits.
- **Evaluation:** ranking metrics on purged, time-separated folds; comparison to a naive baseline (e.g., nearest candidate).
- **Leakage:** labels overlap in time with features; purging and embargo required (§7.4).
- **Generalization:** depends on regime diversity; overfitting risk is high.
- **Uncertainty:** ensembles or calibrated probabilities; calibration must be evaluated out of sample.
- **Compute:** low to moderate on local hardware.
- **Limitations:** the "relevance" label is a choice; different labels yield different selectors. Labels based on future price success are hindsight; the mission prohibits using future price success to manufacture earlier correctness.

### 7.3.5 Self-supervised time-series representation learning

- **Problem solved:** learning representations of movement at arbitrary timestamps and subsequences that can support candidate generation or similarity queries, without labels.
- **Verified method:** TS2Vec learns hierarchical contrastive representations at each timestamp, and aggregates them to subsequence representations, evaluated on classification, forecasting, and anomaly detection benchmarks (UCR/UEA and others) [OS-05]. Its paper evaluates on benchmark datasets, not on chart-interpretation tasks.
- **Training information:** unlabeled time series. Must be only training-period data.
- **Evaluation:** the representation's usefulness is evaluated only on a downstream labeled task (e.g., similarity to annotated structure states), not on the representation itself.
- **Leakage:** the representation must not be fitted on test periods; normalization must be causal.
- **Generalization:** unknown for financial series; the benchmark results do not transfer automatically.
- **Uncertainty:** not built-in; representation distance is not a probability.
- **Compute:** moderate; GPU helpful for training. The repository (OS-05) pins older library versions and last shows activity in 2023 (see file 09).
- **Limitations:** representations may encode non-causal or regime-specific patterns; they do not explain themselves; they do not produce ICT concepts.

### 7.3.6 Sequential probabilistic models

- **Problem solved:** online probability of a regime change or run length (BOCPD), or hidden-state inference over time.
- **Verified method:** BOCPD computes the run-length posterior online with message passing, for independent parameters before/after changes [OS-01]. Its paper demonstrates three real datasets; financial use is named in the abstract as one area of application, but no market performance claim is made there.
- **Training information:** a predictive model for each run and a hazard function; limited data needed to start but requires careful priors.
- **Evaluation:** log predictive likelihood; detection delay vs false alarms on labeled changes (labels must be defined a priori).
- **Leakage:** causal by design; offline reruns for research must not be used as live inputs.
- **Generalization:** depends on the assumed observation model; misspecification is common.
- **Uncertainty:** explicit posterior over run lengths. Strength.
- **Compute:** low.
- **Limitations:** statistical change is not a market-structure event (file 01 §1.8). The model does not know ICT concepts.
- Hidden Markov models are a common related family. They are **not verified in this session** (AC2 status) and should be checked before use.

### 7.3.7 Multiscale representation learning

- **Problem solved:** joint representation of coarse and fine scales for a context query.
- **Training information:** multi-resolution data; alignment of bars across scales must be causal (coarse bar available only when closed).
- **Evaluation:** downstream tasks; alignment tests (no coarse bar used before its close).
- **Leakage:** the most common error. A coarse bar's OHLC includes fine bars after the current time when the coarse bar is still forming.
- **Generalization:** untested for this domain.
- **Limitations:** more inputs increase overfitting risk; a shared representation hides which scale mattered.

### 7.3.8 Hybrid systems

Explicit definitions (for fidelity and auditability) + structured inference (for competing interpretations) + learned ranking or representation (for contextual selection, validated) + sequential probabilistic change detection (for online movement state). This is the most consistent with the mission's requirement that knowledge be source-supported, causal, and auditable. It is also the most complex to evaluate; each layer needs its own target (§7.2).

### 7.3.9 Large language models — explicitly not recommended as the core

The mission requires a system that does not depend on an external language-model API. Even apart from that constraint, a language model's fluency about ICT concepts is not evidence that its chart reading is correct. Language-model outputs cannot be treated as supporting evidence for any element. This foundation does not evaluate LLMs as a core component. (Any future use for drafting explanations must be separately justified.)

## 7.4 Leakage prevention

Mandatory controls for any learning step:

1. **Snapshot inputs at decision time.** Features and candidate sets are generated by the causal pipeline (file 11) using only bars closed at that time.
2. **Label windows.** Labels computed from future bars define a window. Samples whose label windows overlap the test window must be **purged** from training; an **embargo** buffer after the test block removes serially correlated neighbors. This is the López de Prado approach (purged k-fold and combinatorial purged cross-validation, AFML Ch. 7 as cited by secondary and open-source sources) [OS-06, S1]. The book itself was not read in this session.
3. **Hindsight labels separated.** Any label that uses future price (e.g., "candidate was later swept") is labeled `hindsight` and never used as a feature.
4. **Preprocessing fitted on training only.** Normalization, scaling, clustering, and parameter selection must be fitted on training folds.
5. **No selection on the test set.** Parameter sweeps must be nested or counted against a documented search budget.
6. **Multiple comparisons.** Many candidate generators and parameters create many tests; record every configuration tried. A best-performing configuration selected from many is not evidence of predictive power.

## 7.5 What the available source material can and cannot supply

- ICT lessons read in this session supply **definitions and procedures** (P1). They do not supply labeled outcomes, sample sizes, or recorded decision states.
- Community sites supply **claims** of high probability or institutional mechanisms, without verified data (S1; treated as non-evidence).
- Therefore: learning targets 1 and partly 3 can be seeded from source text. Targets 3 (with real labels), 4, 5 need data created by the project itself (annotations of causal states with recorded decisions, and historical market data with proper splits). Target 6 is out of scope.

## 7.6 Annotation protocol for contextual selection (research recommendation)

For learning target 3:

1. Freeze the chart state at a bar t, with only data up to t (causal snapshot).
2. Present the candidate set (all generators, all families) without outcome data.
3. Ask an annotator (human, or a documented rule set) to select candidates for each task and to list alternatives they consider plausible.
4. Record the annotator's stated reasons as text, with the candidates they rejected and why.
5. Measure inter-annotator agreement; disagreement is information, not noise to be averaged away.
6. Only then reveal later data for hindsight labels, in a separate table.

This separates "what a careful analyst would have selected at t" from "what happened later."

## 7.7 Measuring concept fidelity separately

Write a set of canonical test cases per generator, each case stating the expected output under the source definition (for G-OB-P, the lowest down-close with most range near the reference; for G-OB-C, the last opposing candle). Expected outputs come from the definitions, not from outcomes. Keep the cases in the repository alongside the generators, but as test data. This target is deterministic and should be near 100% by construction; if not, the implementation is wrong.

## 7.8 Predictive usefulness and decision quality are not the same

A candidate may be predictive of short-horizon volatility and useless for direction. A selector may improve predictive usefulness and still not yield decision quality after costs, slippage, and risk policy (H). Evaluate predictive usefulness on defined outcomes; leave decision quality to a separate, explicitly scoped policy study.

## 7.9 Self-improvement without memorization

To generalize rather than memorize:

- Use many regimes and instruments, with time-separated validation.
- Prefer features that are definable across instruments (ranges relative to ATR-like scales) to absolute price levels.
- Penalize model complexity; report learning curves; check whether accuracy improves with more data (the mission says more data is not automatically better understanding).
- Keep a held-out, untouched period for final evaluation, used once.

## 7.10 Revising learned selectors

When new data arrives, retrain only through the same protocol. Record every version. A selector whose performance drops in a new regime should be flagged, not silently replaced.

## 7.11 Uncertainty representation

- Candidate sets carry alternatives; this is uncertainty in representation.
- Probabilities for "relevance" must be calibrated out of sample; uncalibrated scores are not probabilities.
- No fixed confidence percentage is supported by this research (mission §15).

## 7.12 Implications for a causal implementation

- Build the causal snapshot function first; everything else depends on it.
- Build the annotation schema and the hindsight-label schema as separate tables.
- Build purged/embargoed splitters before any model.
- Start with target 1 and target 2 (deterministic tests), then target 3 with annotations, then target 5.
- Do not connect any learned output to a trading decision inside this research scope (H).
