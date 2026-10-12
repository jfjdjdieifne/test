# 04 — Three-Candidate Shortlist, Adversarial Challenge, Falsification (G, F, L)

Three candidates are distinct architectures, not versions of one design:
- **Candidate A — Causal segmentation posterior (label-free).** Represents partition uncertainty at declared scales.
- **Candidate B — Partial-label set selector with attention.** Learns acceptance among admissible candidates from expert sets.
- **Candidate C — Self-supervised encoder with retrieval.** Learns embeddings for analogues and novelty; gated.

Each is described under the ten headings requested in §14. Ratings are design properties, not measured results.

---

## Candidate A — Causal segmentation posterior

**1. Actual learning mechanism.** Bounded-duration (explicit or run-length) segmentation filter with a learned or fitted segment model (emission and duration parameters). Learning is parameter fitting on historical closed bars by maximum likelihood, EM, or Bayesian updating. The output is a filtering distribution over boundary positions and segment labels at each declared scale.

**2. Required data and labels.** Closed bars per scale; no labels for fitting. Evaluation requires synthetic truth (mechanics) and annotated boundaries (real structure; LS-ANN).

**3. Handling of wave ambiguity.** Mass across several boundary hypotheses is retained. The posterior is the representation of ambiguity; a point estimate is produced only by a declared decision rule, and the ambiguity rule is declared.

**4. Linking selections.** Nested scales are linked by containment constraints (kernel). A coarse-scale boundary is consistent with fine-scale boundaries inside it; inconsistent pairs are flagged, not averaged.

**5. Generalization.** Fitted parameters are regime-dependent. Generalization is tested by fitting on some volatility regimes and evaluating on others. Parameters are not refit on the evaluation block.

**6. Local compute feasibility.** Forward filtering with bounded durations D and M segment states costs on the order of M²·D per observation in the explicit-duration formulation summarised from Yu (2010) (excerpt); the number of states and D are declared policy values. Feasible on a single CPU core for modest M and D; the builder must measure. Quadratic exact filtering in the number of observations (Fearnhead & Liu, abstract) is not acceptable for long histories without the particle approximation.

**7. Integration with existing causal producers.** Consumes the same closed-bar stream the producers use. Emits posteriors as additional candidate fields with provenance. Must not replace producer outputs; compared against them.

**8. Failure modes.**
- Segment model misspecified; posteriors confidently wrong.
- Declared D too small: true segments exceed the duration window and inference fails (Dewar et al. excerpt).
- Posterior mass diffuse in noisy regimes; ambiguity rule never triggers.
- Parameter drift across regimes unnoticed.
- Smoothing accidentally used for features (leakage).

**9. Evidence supporting it.** Abstract-level evidence that exact online filtering of multiple changepoints is possible (Fearnhead & Liu 2007); abstract-level evidence of explicit-duration models and their computational constraints (Yu 2010; Dewar et al. excerpt). No evidence that it recovers market structure. Evidence grade: ABSTRACT_ONLY.

**10. Falsification experiment.**
- *Hypothesis:* the posterior-mode boundaries at each declared scale recover generator boundaries better than the declared pivot and reversal rules on held-out synthetic families, at declared tolerances.
- *Protocol:* generator families with noise, gaps and regime switches; held-out parameter regions; metrics per family.
- *Falsified if:* the declared rules match or beat the posterior-mode on held-out families, or if the causal filter's output on truncated data differs from its prefix on the full run.
- *Real-data test:* on the owner's closed bars, annotated boundaries (small pilot, protocol from file 03) — falsified if posterior-mode agreement with annotated boundaries is no better than the declared rules on held-out annotated snapshots.

---

## Candidate B — Partial-label set selector with attention

**1. Actual learning mechanism.** For each (snapshot, task) bag of admissible candidates, a permutation-invariant attention pooling produces a bag score; an instance-level attention head gives per-candidate weights. Training maximises the likelihood that the true (unknown) valid candidate lies in the expert's acceptable set, with a disambiguation term that weights candidates within the set. Abstention is a separate output trained on `AMBIGUOUS` and `NONE_ACCEPTABLE` annotations.

**2. Required data and labels.** Annotated snapshots with acceptable sets (LS-ANN), multiple annotators on a subset, admissible candidate sets computed by the deterministic kernel. Synthetic truth may pretrain (LS-SYN) but must be reported separately.

**3. Handling of wave ambiguity.** Acceptable sets can contain more than one candidate, so the model is trained to be consistent with ambiguity rather than forced to choose. Its output is a distribution over the admissible set, plus abstention.

**4. Linking selections.** Linked tasks (reference, binding, falsifier) are bags whose candidates are linked by hard constraints from the kernel. Cross-task consistency is enforced by constraint propagation, not learned. A learned pairwise term is added only after annotated coherence data exists.

**5. Generalization.** Features are kernel-computed and factual (age, containment flags, displacement in declared units, crossed status). Generalization across instruments and regimes is tested with held-out instruments and regime blocks. The model's attention is inspected for reliance on identity features.

**6. Local compute feasibility.** Bags are small (bounded by admissible-set size, which the kernel reports). Training is CPU-feasible for small networks or gradient-boosted approximations of the bag score. Memory scales with number of bags × candidates × features. Not benchmarked; the builder must measure admissible-set sizes first.

**7. Integration with existing causal producers.** Consumes producer outputs as candidates with provenance and as features only if their `known_at` is verified. Producer disagreement becomes a feature (count of agreeing producers), not a vote with weight.

**8. Failure modes.**
- Acceptable sets are too large (uninformative) or systematically narrow (overconfident).
- Annotator habits learned as signal (zoom level, chart style, time of annotation).
- Attention weights read as causal reasons (they are not).
- Label-noise overfitting; memorisation of snapshots that recur in several bags.
- Abstention never triggered, or triggered by sample-size effects.

**9. Evidence supporting it.** Partial-label learning is established as a method (Cour et al. 2011; SECONDARY_SUMMARY). MIL with attention is established (Ilse et al. 2018; ABSTRACT_ONLY). Snorkel shows that heuristic sources with unknown accuracy can be combined through a generative label model (ABSTRACT_ONLY/excerpt). No evidence that these methods improve market-structure selection. Evidence grade: general methods, not market evidence.

**10. Falsification experiment.**
- *Hypothesis:* on held-out annotated snapshots (held-out annotators, held-out period), the model's top candidate lies in the expert acceptable set more often than (a) the declared rule, (b) recency-only, (c) uniform over admissible, and (d) a label-permuted model, with abstention matching annotated ambiguity above chance.
- *Falsified if:* any of (a)–(d) matches or exceeds the model on set coverage, or the label-permuted model reaches comparable coverage, or the model's advantage disappears on the held-out annotator.
- *Required:* at least two annotators on an overlap subset; inter-annotator agreement reported; the minimum sample size is set by the owner's annotation budget and a pre-run power check (the builder must state the check and the effect size of interest; none is set here).

---

## Candidate C — Self-supervised encoder with retrieval (gated)

**1. Actual learning mechanism.** A masked-patch or contrastive temporal encoder trained on causal windows from many series. Output: embeddings. Retrieval: nearest-neighbour search over embeddings returns past windows with similar shape, with their stored kernel outputs (structures, statuses). Novelty: distance to nearest neighbours, reported as an out-of-support flag.

**2. Required data and labels.** Historical closed bars only for pretraining. No labels. Evaluation requires annotated selections or structural references.

**3. Handling of wave ambiguity.** Retrieval returns multiple analogues with different structural outcomes; the system shows the distribution of their kernel-derived structures rather than picking one.

**4. Linking selections.** Analogue retrieval is per window; linking is through the kernel, as in A and B. The encoder does not learn relations.

**5. Generalization.** Explicitly tested as novelty detection: performance should degrade gracefully (flag rate rises) on out-of-support regimes. Claims of generalisation are limited to retrieval quality on held-out periods.

**6. Local compute feasibility.** Pretraining is GPU-favourable; CPU is possible for small encoders over short windows. Retrieval index memory scales with windows × embedding dimension. Not benchmarked.

**7. Integration with existing causal producers.** Stores embeddings alongside producer outputs; never modifies producers. Uses only windows ending at or before the decision bar.

**8. Failure modes.**
- Trivial features dominate embeddings (trend, volatility level).
- Retrieval returns similarity in price level rather than shape (if not normalised; normalisation is a declared choice).
- Future leakage through negative sampling or augmentation that peeks ahead.
- Reconstruction quality mistaken for understanding.
- Retrieval neighbours from the same episode (temporal clustering) inflate apparent accuracy.

**9. Evidence supporting it.** Masked reconstruction and contrastive representation learning for time series are established as methods (Franceschi et al. 2019; Eldele et al. 2021; Yue et al. 2022; Nie et al. 2023 — SECONDARY_SUMMARY or excerpt). Forecasting benchmarks for these methods do not test structure selection. Evidence grade: method-level, not application-level.

**10. Falsification experiment.**
- *Hypothesis:* retrieved analogues' kernel structures predict the expert acceptable set better than the declared rule on held-out annotated snapshots, after controlling for recency and volatility level (matched neighbours).
- *Falsified if:* matched-neighbour baselines match the retrieval, or retrieval performs no better than random windows with matching volatility.
- *Gate:* build only if Candidates A and B are both evaluated and B's failures are attributable to representation (not to labels or constraints).

---

## G. Ranking and comparison summary

| Criterion | A: Segmentation posterior | B: Partial-label selector | C: Encoder + retrieval |
|---|---|---|---|
| Needs labels to start | No | Yes (expert sets) | No (labels for evaluation) |
| Addresses multiple valid partitions | Directly | Partly (set-valued targets) | Partly (multiple analogues) |
| Causal risk | Low (filtering only) | Medium (feature causality) | Medium–high (sampling leakage) |
| Interpretability | Medium (posterior and parameters) | High (attention per candidate, kernel features) | Low–medium (nearest neighbours are inspectable) |
| Implementation maturity | Method exists; code in-house | Methods exist; no market implementation found | Libraries exist; no structure-selection implementation found |
| Compute (qualitative) | Low–medium, CPU | Low, CPU | Medium–high, GPU favourable |
| Main falsifier | Declared rules match on synthetic and annotated boundaries | Label-permutation or simple baselines match | Matched-neighbour baselines match |
| Role in recommendation | **First build** | **Second stage, after annotation** | **Gated research** |

## Adversarial case results (F)

Each case shows how each architecture *behaves computationally*, not its intention. Cases use only illustrative numbers.

### Case A — A large wave contains many smaller valid waves
- **Kernel:** containment is deterministic; each fine leg is linked to its containing coarse leg.
- **A:** the coarse-scale posterior and fine-scale posteriors both place mass; the containment check flags pairs where the coarse boundary falls between fine boundaries (inconsistency). Cost: one filter per scale; containment check linear in fine boundaries per coarse segment.
- **B:** the admissible set for a "reference" task at a coarse scale contains only coarse candidates; fine candidates are excluded by the role rule *and recorded as excluded*, not dropped. The bag is smaller, not wrong.
- **C:** nearest neighbours of a coarse window may be windows with many fine waves; retrieval can return a mixture. Flag as ambiguous if neighbours' structures disagree.
- **Result:** the containment problem is solved by the kernel in all three; A and C require explicit reporting of mixed neighbours.

### Case B — A turning point visible in hindsight but not confirmed at decision time
- **Kernel:** fixed-window pivots are unknowable until the window ends; the ledger records `PENDING_KNOWABILITY` for the decision time. Replay equality (file 03 §4C) detects any use.
- **A:** the filtering posterior at time t gives mass to a boundary only if the data up to t support it; the hindsight boundary appears in the smoothed posterior, which is never used. The filtering posterior may show mass that later disappears; this is recorded as a revision.
- **B:** excluded by admissibility (not knowable). If a feature used a smoothed value, replay equality fails.
- **C:** retrieval from a historical window ending at its own decision bar contains no future; retrieval *targets* that used future structure must be excluded from neighbour outcome statistics unless their structures were knowable at their own decision times.
- **Result:** all three need the replay test; A's filter must be filtering-only by construction.

### Case C — Two different wave interpretations produce different structural references
- **Kernel:** two interpretation sets, both constraint-consistent, kept separately with their generator versions.
- **A:** the posterior over partitions contains both as modes or as separate scales; the output includes both with posterior masses (not normalised across scales as if they were comparable without a declared rule).
- **B:** the bag for the reference task contains both candidates; the expert set may contain both; if the expert set is singleton, the model's top choice is one and the other is recorded as an unexamined alternative. A learned pairwise factor is not used.
- **C:** retrieval returns analogues supporting each reading; the distribution is reported.
- **Result:** the system outputs alternatives in all three; none chooses a winner by outcome.

### Case D — Seventy FVG candidates exist, but only some belong to the movement under study
- **Kernel:** each FVG has a deterministic geometry and status. Membership in "the movement under study" requires a declared relation (for example, formed within a declared displacement, which requires its own definition). Without that definition, membership is `UNKNOWN`, not guessed.
- **A:** not applicable to FVG membership, except as a time-segment context if the declared displacement uses a segment.
- **B:** bag = FVGs satisfying the declared membership relation (exact); the learned part is applied only to that bag. Non-members are recorded as excluded with reasons.
- **C:** retrieval over FVG windows would mix members and non-members unless the membership relation is in the encoder's input. Not recommended for this case.
- **Result:** membership must be a deterministic relation first. Learning cannot define membership.

### Case E — An old level becomes relevant again
- **Kernel:** the old level is a candidate with its original `confirmed_at`; relevance to the current task requires a declared re-entry or touch relation. Intervening crossings are recorded (count and bar indexes).
- **A:** a boundary in the old segment remains in the filter's state only if the model's duration window still covers it; with bounded D, a level older than the window is no longer represented. This is a *known limitation*: the ledger records the level as `OUT_OF_WINDOW` rather than silently losing it.
- **B:** the old level is in the bag if the declared relation is satisfied; age is a feature, not a relevance rule.
- **C:** embeddings of old windows are not compared to current windows unless within the retrieval horizon declared.
- **Result:** the bounded-duration limit in A is a real trade-off and must be reported, because "old levels" are exactly the case where bounded windows fail.

### Case F — An apparently coherent analysis is built on an unsuitable initial wave
- **Kernel:** coherence is only internal; the system must report the root candidate and its generator and parameter provenance. Sensitivity to the declared parameter sweep flags fragility.
- **A:** posterior sensitivity to the segment model is the diagnostic; a single model producing a sharp posterior is a warning, not evidence. Compare across two segment models.
- **B:** if the bag's candidates all come from one generator, the bag has no alternatives; the system must report "single-generator bag".
- **C:** retrieval neighbours may share the same unsuitable structure; the matched-neighbour baseline catches this.
- **Result:** no architecture can detect an unsuitable initial wave from within its own coherence. Detection requires the sweep and the independent-generator comparison (AR-1 §1.5).

### Case G — A human expert and a model disagree
- **Kernel:** both are recorded as interpretations or labels with their provenance.
- **A:** disagreement is reported as a boundary-level difference with posterior masses.
- **B:** the model's top choice outside the expert set is an error on the evaluation; a model's top choice inside the set is not proof of correctness, only of agreement. Disagreement cases are routed to review and labelled as annotation candidates, not treated as model errors automatically.
- **C:** retrieval evidence supporting the model's view is shown to the expert; expert can reject the analogue set.
- **Result:** disagreement is the main source of new annotations; it must not automatically update labels (file 03 §2).

### Case H — A trade loses despite a defensible analysis
- **Kernel and ledger:** the interpretation and its provenance are stored with the decision time.
- **Attribution:** loss decomposition by stage (AR-1 file 05 §5) is required before any component changes. A loss alone is not evidence against the analysis.
- **Any architecture:** the outcome is an objective-F observation. It cannot change A, B or C's labels.
- **Result:** no architecture has a "defensible analysis loses" pathway other than the attribution protocol.

### Case I — Market volatility changes sharply
- **Kernel:** declared scale measures are recomputed; features expressed in declared units shift; drift monitors fire.
- **A:** fitted segment parameters become misspecified; posterior sharpness changes. Requires an explicit regime-change check and refit under the registry gate, never silent online updates.
- **B:** feature distributions shift; OOD flag raised for snapshots outside training support; abstention rate monitored.
- **C:** embeddings of the new regime may lie far from the index; novelty flag fires; retrieval results are reported as out-of-support.
- **Result:** A is most exposed (parameters); B is exposed through features; C signals novelty most directly but gives least structural guidance.

### Case J — A combination of events not seen during training
- **Kernel:** the combination is handled by the same deterministic rules; no learning needed for their status.
- **A:** the segmentation filter operates on the new combination without a learned event type; behaviour is governed by the fitted segment model.
- **B:** the bag may be empty (no admissible candidates) → `NO_ADMISSIBLE`; or the model scores an unfamiliar bag → OOD flag. Abstention is the designed response.
- **C:** novelty flag fires; nearest neighbours are of limited relevance; reported as such.
- **Result:** all three must treat unseen combinations as reportable states (`NO_ADMISSIBLE`, `OOD`), never as default classifications.

## L. Falsification criteria (project-level)

The architecture is considered wrong, and the corresponding component is removed or redesigned, if any of the following hold on the pre-registered protocol:

1. The declared rules match or beat the segmentation posterior at declared tolerances on held-out synthetic families **and** on held-out annotated boundaries.
2. The partial-label selector does not beat the label-permuted model and the simple baselines on held-out annotators and held-out periods.
3. Replay equality fails for any feature, or any output uses data later than its `known_at`.
4. The ledger omits any candidate for any task at any decision time.
5. A learned component is found to write to kernel tables or to alter a definition hash.
6. Annotation agreement is too low for the acceptable-set target to carry information (threshold to be declared by the owner before annotation starts).
7. Largest coherence component exceeds the declared budget on realistic snapshots, and approximate inference changes the interpretation set in ways that matter (measured on annotated cases).

Falsification outcomes are reported as results. No criterion is relaxed after seeing data.
