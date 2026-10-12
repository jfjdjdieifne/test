# 03 — Training Labels, Data Acquisition, and Evaluation Design (E, §11, §16)

## 1. Label sources, what each can teach, and what it cannot

| Source | Can teach | Cannot teach | Maturity | Main risk |
|---|---|---|---|---|
| **Historical OHLCV** (closed bars) | Segment structure statistics; posterior fits (label-free); stability of candidates; regime-conditional feature distributions | Which structure the owner means; any "correct" wave | Exact as data; labels none | Vendor errors, gaps, session conventions, survivorship-free? (source-dependent) |
| **Higher-resolution trades / quotes** | Finer timing for intrabar order; more reliable reclaim timing; resolution for ambiguity cases | Hidden resting orders (not in trade prints) without order-book data | Exact as data | Data cost and licensing; volume of data |
| **Order-book depth (LOB)** | Depth and queue-state features; the microstructure context that a price-only definition cannot show | Intent; resting-order identity of stops | Exact as data where recorded | Expensive; LOB labels in published work are future-based (DeepLOB) |
| **Source-verified chart annotations** (expert marks with a written protocol) | Acceptable-set preferences for contextual selection (S2) | Ground truth; annotator bias; generalisation across annotators | Medium | Low agreement; drift across sessions |
| **Original educational examples** (course lessons, transcripts) | Candidate operational definitions and the structure of teaching examples; hypotheses to test | Validation of any concept; chart coordinates must not be invented; transcript errors (earlier sessions found auto-transcript errors) | Low (source grade) | Doctrine presented as fact; misquoted rules |
| **Synthetic hierarchical series with known turning points** | Recovery mechanics; failure detection; regression of the kernel | Market structure; that the generator resembles markets | Exact by construction | Generator too easy or too similar to the rule being tested |
| **Operationally derived labels** (declared rules as labelling functions) | Fidelity of learned components to a declared rule; weak supervision inputs | Correctness of the rule | Exact relative to the rule | Circularity: evaluating a learner against the rule it was trained to copy |
| **Historical outcome observations** (forward returns or trade results) | Objective E (predictive usefulness) and objective F (decision quality), evaluated under the matched-control protocol | Concept application; structure correctness; attribution of a loss to one stage | Matures after horizon; confounded | Hindsight contamination; multiple comparisons; regime dependence |

**Rule carried from the owner's constraints.** Outcome labels never supervise structure or concept application (A–D). They are used only for E and F.

## 2. Annotation as evidence, not as truth

Annotations (chart judgements by humans) are treated as **noisy, set-valued observations of expert judgement**, not as absolute truth. Consequences:

1. **Protocol.** Written, versioned instructions: which observables may be used; which bars are visible (only bars up to the decision time, unless the question concerns resolution, in which case that is stated); allowed answers (`ACCEPTABLE_SET`, `NONE_ACCEPTABLE`, `AMBIGUOUS`, `INSUFFICIENT_INFORMATION`).
2. **Multiple annotators** on a subset, with inter-annotator agreement measured on sets (e.g., overlap of acceptable sets). Agreement levels are reported; no threshold for acceptance is set here (owner declares).
3. **Annotator identity and time are stored** so that drift and individual bias can be analysed.
4. **Re-annotation of a golden subset** later to test annotator drift.
5. **Disagreement is data.** Cases where annotators disagree are reported as ambiguity, and the abstention target is built from them.
6. **Self-consistency of the owner.** If the owner is the sole annotator, the protocol must include a delayed re-annotation of a random subset without access to the earlier answers. Otherwise the annotation measures memory.

## 3. Label maturity and timing

- Each label carries `known_at` (when the label was determined) and `snapshot_time` (the decision time it applies to).
- Labels that depend on later bars (LS-PERS, LS-OUT) carry a `matures_at` and are unavailable to any training set before it.
- Purging: any training example whose label horizon overlaps an evaluation example's window is removed from training for that evaluation.

## 4. Evaluation dimensions (§11 A–G)

For each dimension: observable target, data, metrics, independent baseline, failure modes, claim limits.

### A. Operational concept accuracy
- **Target:** whether a deterministic concept function returns the status its declared definition specifies on test cases.
- **Data:** hand-written positive, negative, near-miss and edge cases per concept (versioned); synthetic cases generated from the definition itself (these test implementation, not doctrine).
- **Metrics:** case pass rate (required to be complete for deterministic definitions); coverage of definition branches; number of `AMBIGUOUS` outputs and their handling.
- **Baseline:** a second independent implementation written by a different builder from the same definition text.
- **Failure modes:** the test cases encode the same misunderstanding as the code; definitions with two sourced variants silently resolved to one.
- **Claim limit:** agreement with the definition, not with the market or the teacher's intent.

### B. Candidate extraction coverage
- **Target:** whether the generators produce the structural objects an expert or a generator says exist.
- **Data:** synthetic truth (LS-SYN); annotated acceptable sets on real snapshots.
- **Metrics:** recall of annotated or synthetic structures among emitted candidates at declared tolerances; false-candidate rate; per-scale breakdown; ledger completeness (every candidate has a status).
- **Baseline:** declared generators alone; S1 alone; both combined.
- **Failure modes:** tolerance choice dominates the result; coverage measured only on easy regimes; candidates emitted but silently excluded.
- **Claim limit:** coverage relative to the stated reference, not to "all waves" (no such reference exists).

### C. Information-time correctness
- **Target:** every feature and selection is computable from information known at the decision time.
- **Data:** the bar store with ingestion timestamps; replay of truncated histories.
- **Metrics:** replay equality (outputs on a truncated history equal the prefix outputs of the full run for all decision times); count of features with `known_at` later than `snapshot_time` (must be zero); revisions and their supersession records.
- **Baseline:** none needed; this is a pass/fail property.
- **Failure modes:** ingestion timestamps that are later than bar close; repaint of indicators; feature engineering that averages across the decision bar.
- **Claim limit:** shows that the pipeline does not use later data; does not show that the signal is useful.

### D. Contextual selection fidelity
- **Target:** whether the selected candidate is in the expert-acceptable set on held-out annotated snapshots; abstention matches expert ambiguity.
- **Data:** annotated snapshots with acceptable sets; held-out annotators; held-out periods; held-out instruments.
- **Metrics:** set coverage (top choice in acceptable set); set size needed to cover (for ranked lists); abstention precision and recall against `AMBIGUOUS`; agreement with declared rule where the rule is the target.
- **Baselines (all reported):** declared rule; uniform over admissible set; recency-only (declared, labelled as policy); S1 posterior mode (where applicable); label-permutation control (a shuffled-label model must score near the chance rate of the admissible set — this distinguishes learning from memorising noise).
- **Failure modes:** learner exploits a feature that correlates with annotator habit (for example chart zoom level); overfit to one annotator; acceptable sets too large to be informative.
- **Claim limit:** agreement with the annotators on these snapshots, not with market truth.

### E. Interpretation coherence
- **Target:** hard constraints satisfied (exact); annotated coherence judgements; propagation correctness after revision.
- **Data:** constructed interpretation sets; annotated coherence pairs; revision replays.
- **Metrics:** constraint violation count (required zero); coherence agreement; propagation test pass rate.
- **Baseline:** per-task independent selection; deterministic constraints alone.
- **Failure modes:** coherence annotations that reward consistency with a flawed selection; components too large to enumerate, forcing approximation.
- **Claim limit:** internal consistency. Coherence is not truth: two coherent interpretations may both be wrong, and the output must keep both.

### F. Predictive usefulness
- **Target:** whether a selection or interpretation carries information about a pre-declared forward statistic, relative to matched controls.
- **Data:** historical bars with a frozen forward-statistic definition; matched controls drawn from the same regime, scale and time-of-day distribution.
- **Metrics:** difference from matched controls with interval estimates; stability across regime blocks; multiple-trial adjustment when many definitions are tried (for example the probability of backtest overfitting, Bailey et al. 2017, METADATA_ONLY/UNVERIFIED).
- **Baseline:** matched random controls; declared rule; no selection.
- **Failure modes:** multiple comparisons across horizons and definitions; regime concentration; control mismatch; hindsight definitions.
- **Claim limit:** statistical association with the chosen forward statistic in the tested periods. Not a trading result.

### G. Trading decision quality
- **Target:** outcomes of a decision policy under costs, slippage and risk limits.
- **Status:** out of scope. A decision policy does not yet exist, and its definition is an owner decision. Required before any work: a written policy, cost and slippage model, risk policy, and passing F on an independent period.
- **Failure modes:** decision policy tuned to the same periods used for F; costs modelled as zero; luck mistaken for analysis quality.
- **Claim limit:** the results of a single policy under stated costs in stated periods.

## 5. Splits and leakage prevention

- **Chronological holdout by default.** The final period is untouched until the protocol is frozen.
- **Purged walk-forward** for any label with a horizon: purge length equals the label horizon; an embargo is declared and reported.
- **Holdout families and instruments:** synthetic families held out by generator parameters; real evaluation held out by instrument where the owner has more than one.
- **Annotator holdout:** a subset of annotators' items is excluded from training.
- **Regime holdout:** evaluation blocks chosen by volatility regime *definitions declared in advance*, not chosen after seeing results.
- **Leakage checks:** replay equality (dimension C), label-permutation control (dimension D), and a check that no feature uses a bar with a later `known_at`.

## 6. Distinguishing learning from memorisation

Required controls for any learned component:
1. **Label-permutation control:** the same training procedure on shuffled labels must not reproduce held-out performance.
2. **Held-out instrument and period:** performance must hold on data not seen in training.
3. **Feature ablation:** removing features that encode identity (instrument ID, absolute price level) must not destroy performance if the claim is about structure.
4. **Simple-baseline dominance check:** a learned model must be compared with the simplest declared rule and reported even if it loses.

## 7. What counts as evidence of understanding in this project

Operational evidence only:
- The concept's test cases pass (A).
- Candidates cover annotated structures at declared tolerances (B).
- The pipeline is information-time correct (C).
- Selections match expert acceptable sets above the label-permutation and simple-baseline controls (D).
- Interpretations are constraint-consistent and revision-stable (E).
- Any predictive association survives matched controls and multiple-trial adjustment (F).

No single number represents understanding. A claim of understanding must cite the dimensions and controls above.
