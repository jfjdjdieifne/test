# 00 — Executive Engineering Decision (A, B, O)

## A. Decision

Build a **knowledge-constrained structured inference system** (option D in §B), delivered in stages:

1. **Deterministic kernel.** Candle semantics, swing/leg candidate generators, geometric objects (for example FVG spans), status machines, containment and crossing relations, and dependency bookkeeping. Versioned and contract-tested. Learned components have read-only access.
2. **Candidate ledger.** Every candidate produced by every declared generator is stored with provenance. Each (task, candidate) pair has an explicit status: scored, excluded with a reason, not examined because of a declared budget, or pending knowability. Nothing is dropped silently.
3. **Task-conditioned admissibility.** Hard constraints (knowable at decision time, role matches task, geometric validity) define the admissible set exactly. No top-k pruning presented as market irrelevance.
4. **Learned unary scorers** for contextual preferences inside the admissible set, starting with a gradient-boosted ranker over factual features. Outputs are scores plus abstention, never a single "correct" answer when the admissible set is ambiguous.
5. **Coherence layer.** Linked tasks (structural reference, event binding, invalidation, liquidity reading) form a factor graph whose connected components are small. Exact enumeration inside components under an explicit budget; beam or belief propagation beyond it, with the unexamined remainder recorded. The output is a set of coherent interpretations, each with its constraint status.
6. **Interpretation graph** with dependencies. A revised kernel output or a new bar marks dependent interpretations for recomputation.

**First build target:** structural swing/reference selection (tasks T-S1 reference, T-S2 binding, T-S5 falsifier), trained first on synthetic hierarchical price data with known turning points and on fidelity to declared rules. Human-annotated coherence labels come later. FVG and ICT entry-model work come after the swing layer has passed its own tests. Trade decision quality is out of scope for this architecture (see objective F in file 03).

**Why this and not a larger model:** the owner's stated failure mode is that concepts are applied inconsistently and context is lost. The main risk is contextual selection (which swing, which reference, which invalidation) under a small amount of trustworthy label data. Pure rules hard-code one contextual choice. Pure learning has no valid labels for "correct wave". The staged design keeps each decision either deterministic, declared, or learned under a named objective, and it makes the learned part small enough to validate.

**Decision gates:**
- No stage advances without passing its contract tests and its pre-registered evaluation.
- Failure to beat the declared baseline is a valid outcome. In that case the deterministic rule stays in production and the learned scorer is archived.
- No model is deployed automatically on recent profit or any other recent outcome (see file 04).

## B. Architecture comparison

Ratings are ordinal and qualitative (low / medium / high). They describe design properties, not measured performance. No benchmark numbers exist for this system.

| Option | Description | Strengths | Weaknesses | Label need | Explainability | Local CPU feasibility | Verdict |
|---|---|---|---|---|---|---|---|
| **A. Pure deterministic** | All choices are coded rules (declared policies). | Fully auditable; cheap; testable. | Hard-codes contextual choices; cannot express preference learned from annotation; inconsistency persists across rule variants. | None | High | High | Required as kernel and as baseline. Not sufficient for contextual selection. |
| **B. Independent learned selectors** | One classifier or ranker per task (swing, liquidity, FVG, entry), each trained separately. | Simple to build; each task evaluable. | Ignores cascades: the selected reference changes which liquidity and invalidation are meaningful; can produce mutually incompatible outputs. | Per task; moderate | Medium | High | Acceptable as the unary layer inside D. Not acceptable alone. |
| **C. Joint structured inference** | One probabilistic model over all linked variables (factor graph or structured prediction), trained jointly. | Captures dependencies; coherent outputs by construction. | Needs joint labels that do not exist; exact inference grows with domain size; harder to debug. | High (joint) | Medium | Medium, depends on domain size | Use the inference formalism, not the joint training from scratch. |
| **D. Knowledge-constrained learned structured inference** | Deterministic kernel and admissibility define the feasible set; learned unary scores; coherence factors over small components; explicit budgets and ledger. | Feasible set is exact and auditable; learned parts are limited; cascades are represented; abstention and unexamined space are explicit. | More moving parts than A or B; coherence factors need annotated data; requires careful budget reporting. | Staged | Medium–high (feasible set and factors are inspectable) | Medium–high | **Recommended.** |
| **E. Staged combination** | Sequence A → B → C, with D as the target state; each stage gated by tests. | Lowest risk; each stage yields a usable, testable system; failures localize to a stage. | Requires discipline to avoid staying at a partial stage; duplicated interfaces during transition. | Staged | High | High | This is the **delivery plan** for D. |

**Selection rule used.** The most complex option (C, full joint learning) is not selected automatically. It is rejected for now because (1) the required joint labels do not exist and cannot be created from future profitability, (2) its failure modes are hard to localize, and (3) the components that matter most (feasible set, dependencies, budgets) do not need learning at all. D keeps the joint *inference* structure but learns only the parts that have a defensible objective.

## O. Rejected approaches (explicit)

Each item is rejected for a stated reason. Rejection does not mean the underlying idea is wrong in every context; it means it is not admissible for this system.

1. **Compound concept checklists as signals** (for example "BOS + FVG + sweep = buy"). Rejected: conjunction is a trading decision rule; it has no validity evidence in this foundation and repeats the confirmation-stacking failure pattern described in the brief.
2. **Indicator accumulation** (many oscillators or overlays combined by weight). Rejected: adds inputs without a definition, creates unlabelled thresholds, and cannot be audited against ICT concept definitions.
3. **LLM as the reasoning core, or as a required service.** Rejected by the owner's constraint. Normal operation must be local Python with free or open tools. Language models may be used offline for drafting documentation only, with no effect on runtime outputs.
4. **Labelling "correct wave" or "correct swing" from future profitability.** Rejected: confounds structure with outcome and leaks future information into the definition of the object being learned.
5. **Judging concept application by profit.** Rejected: a trade outcome is a joint result of concept application, risk, execution and luck. It cannot validate that the concept was applied correctly.
6. **Universal "most important", "largest", "newest" or "closest" level rules.** Rejected: universal importance rules are prohibited; recency and proximity appear only as declared, unvalidated slots (see foundation file 17).
7. **Top-k pruning as a claim of market irrelevance.** Rejected: pruning is permitted only as an explicit, budgeted operation that records every unexamined candidate.
8. **End-to-end reinforcement learning on PnL.** Rejected: rewards are outcome-based, sparse and confounded; the policy would learn exposure and luck; it also requires live execution, which is out of scope.
9. **Graph neural network over all candidates from day one.** Rejected for the first stage: no labels for relational structure; combinatorial candidate sets; cost without evidence. Re-evaluated only after stage 3 data exists.
10. **Generic research framework as the first deliverable.** Rejected: the owner asked for a working path through swing and reference selection first; a framework without a first target is the failure mode being avoided.
11. **Starting with FVG profitability.** Rejected: it bypasses the swing and reference problem, which determines what an FVG is relative to.
12. **Self-supervised discovery of ICT concepts.** Rejected as a route to "understanding". Unsupervised representations may be used for similarity and diagnostics (file 03), but they do not establish that a representation matches an ICT concept.
13. **Learning that edits the kernel.** Rejected: a learned model that changes a definition would silently redefine every downstream output.
14. **Selecting the most complex model automatically when it scores higher on a single validation split.** Rejected: complexity must be justified by a pre-registered comparison on held-out data, with the simpler baseline reported alongside.
15. **Declared numeric defaults presented as evidence** (for example a fixed multiple of volatility swept until results look good). Rejected: the owner prohibits arbitrary policy values and silent parameter assignment; values must be declared by the owner, labelled, and sensitivity-tested.
