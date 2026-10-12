# 00 — Evidence-Based Decision and Challenge to AR-1 (Deliverables A, H)

Scope: research and architecture only. No trading code, no live execution, no performance claims. The owner's repository was not inspected; the trading project's producers are treated as unknown internals and are covered only by integration contracts (file 05).

## A. Decision summary

1. **Keep** the deterministic, versioned kernel and the candidate ledger from AR-1. These are not learning problems and the evidence supports auditing them as ordinary software. No change.
2. **Replace** AR-1's central learned layer. AR-1 used a gradient-boosted ranker over admissible candidates plus a factor graph with learned pairwise factors. The evidence does not support that as the first learned component (§Challenge below).
3. **Adopt a staged, three-part learned design**, each part answering a question that the others cannot:
   - **S1 — Causal segmentation posterior (label-free).** Represents the "one large move, several nested moves, provisional turns" problem as a *probability distribution over partitions* at each declared scale, computed with causal filtering only. Fitting uses historical closed bars with no labels. This is the first build target because it addresses the swing problem directly and needs no judgement labels.
   - **S2 — Partial-label contextual selector (weakly supervised).** Learns which admissible candidate an expert-declared task accepts, using *sets* of acceptable candidates from annotation rather than one "correct" answer. Trained only after S1 produces stable candidate sets and after an annotation protocol exists. Its input is a bag of candidates, and attention weights show which candidate drove the score.
   - **S3 — Self-supervised temporal encoder with retrieval (optional research track).** Learns embeddings of price windows for analogue retrieval and novelty detection. It is gated: it is built only if S2 is limited by representation quality, and it is never evaluated by reconstruction error.
4. **Demote the factor graph.** Joint consistency is implemented first as *exact hard-constraint propagation* over the ledger. Learned pairwise coherence factors are deferred until annotated coherence data exists. A factor graph is adopted only when it demonstrably changes selections relative to independent per-task selection on held-out annotated cases.
5. **Owner-declared policies stay declared.** Declared rules and owner-chosen values (tolerances, ambiguity rules, scales, budgets, promotion margins) are recorded as declared, sensitivity-tested, and never presented as market truth.

## H. Recommended architecture (summary)

```
closed bars (causal)
  → deterministic kernel: candle semantics, declared generators, geometry, crossing, reclaim monitors
  → S1 causal segmentation posterior per declared scale (label-free; filtering only)
  → candidate ledger: every candidate × task status, no silent exclusion
  → task admissibility (exact hard constraints)
  → S2 partial-label selector over admissible bags (after annotation; abstention; attention)
  → hard-constraint propagation across linked tasks (exact)
  → interpretations: alternative sets with versions, posteriors, constraint status, unexamined list
  → [optional gated] S3 retrieval for novelty and analogues
```

Trading decisions are not part of this architecture. Any future decision layer must consume interpretations and must be evaluated separately (file 03 §4, dimensions E–G).

## Challenge to AR-1 (what the evidence changed)

| AR-1 claim | Challenge | Evidence | Revised position |
|---|---|---|---|
| Factor graph is the joint-inference layer. | Most joint relations are hard, deterministic constraints. Learned pairwise factors need annotated coherence labels that do not yet exist. Inference over large domains has exponential worst-case cost. | Factor-graph formalism is standard [M] (Kschischang et al. 2001). Exact inference cost depends on domain sizes; AR-1's own budget logic already acknowledged this. No source shows that a learned factor graph improves interpretation on market structure. | Hard-constraint propagation first. Factor graph only if it beats per-task selection on annotated held-out cases. |
| LightGBM LambdaRank as the unary scorer. | LambdaRank's label type is integer relevance grades (verified in LightGBM docs: `lambdarank` takes integer labels with a `label_gain` mapping). Forcing expert judgement into grades commits to an ordering the annotators did not produce. | Official LightGBM parameter documentation read (chunk 0 of 11). | Use set-valued (partial-label) supervision instead. Keep LightGBM only as a comparator if its inputs are S1 features. |
| A single "correct" structural reference is the target. | Multiple partitions can be valid at different scales; a point estimate hides the ambiguity the owner asked the system to preserve. | Online Bayesian changepoint filtering produces full posteriors over changepoint positions (Fearnhead & Liu 2007, abstract `[V]`). | Output a posterior over partitions per scale; select only inside a declared ambiguity rule. |
| Synthetic ground truth is enough for stage 1. | Synthetic truth tests whether an algorithm recovers the generator's structure. It does not establish that the generator matches markets. | Logical; consistent with the owner's constraint. | Synthetic is for mechanics and failure detection only; a real-data falsification test is required before any claim (file 04). |
| Future-based labels can be used when the task is "structure at scale". | DeepLOB's labels are direction classes computed from a future mean of mid-prices with a threshold α (verified from excerpts `[V]`). That is a *prediction* target. Using a similar construction for structure would embed the future into the definition of the object. | DeepLOB method excerpts read (see file 01). | Forbidden for structure. Allowed only as an explicitly named forward-looking evaluation target (objective E). |
| Self-supervised pretraining would help representation. | Masked-reconstruction results from forecasting papers do not test contextual selection. Reconstruction is not market understanding. | PatchTST arXiv excerpt (masked patch reconstruction) `[V]`; its evaluation targets are forecasting error on benchmark datasets, not structure selection. | S3 gated; evaluate retrieval against annotated selections, not reconstruction. |

## What the evidence did *not* change

- The principle that concept definitions live in the kernel and are contract-tested.
- The candidate ledger and "no silent exclusion" rule.
- The requirement that no label is derived from future profit for structure or concept application.
- The decision to defer trading decisions.

## Strongest practical alternative (stated plainly)

The strongest practical alternative to AR-1 is **S1 + S2 with a deterministic constraint layer**, rather than a joint learned model. It is simpler to falsify, uses label-free fitting where possible, and spends annotation effort only where a labelled decision is actually needed.

Limits of this recommendation:
- No experiment has been run. The recommendation rests on the properties of the methods and on the verified sources listed in file 01.
- Whether S1 produces useful segmentations on the owner's data is unknown and is the first falsification test (file 04).
- The annotation protocol and its quality are the main risk for S2, and they are owner decisions.
