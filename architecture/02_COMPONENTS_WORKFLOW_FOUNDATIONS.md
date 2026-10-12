# 02 — Components, Data Structures, Inference Workflow, Uncertainty, Foundational Mastery (E, F, H)

## E. Component design

| # | Component | Responsibility | Learned? | Writes to |
|---|---|---|---|---|
| K1 | **Bar store** | Immutable closed bars per instrument and timeframe, with timestamps, timezone, source and a content hash. Gaps and duplicates recorded, not repaired silently. | No | Bars (append-only) |
| K2 | **Candle-semantics kernel** | Body, range, wick, close location; intrabar-order ambiguity flagged as `UNKNOWN`, never resolved by assumption. | No | Derived fields |
| K3 | **Candidate generators** | Declared families: fractal/pivot (F-K), threshold-reversal (F-T), changepoint-based (F-C), each with parameters and version. Each generator emits candidates with provenance. | No | Candidate store |
| K4 | **Geometry and status kernel** | Spans (for example FVG), crossing, touching, containment, traded-through status machines. | No | Status events |
| K5 | **Relation index** | Interval trees over time and price levels for crossing, containment and time-overlap queries. Returns *all* matches; no sampling. | No | Index |
| K6 | **Candidate ledger** | Per (task, candidate) status: `SCORED`, `EXCLUDED(reason)`, `NOT_EXAMINED(budget)`, `PENDING_KNOWABILITY`. Append-only. | No | Ledger |
| K7 | **Task admissibility** | Hard constraints per task (role, knowability at decision time, validity). Produces the exact admissible set. | No (rules written by owner, versioned) | Ledger |
| L1 | **Feature extractor** | Factual, causal features per (task, candidate, snapshot). Schema versioned. | No | Feature store |
| L2 | **Unary scorer** | Gradient-boosted ranker (stage 1); later optional encoder-based scorer. Outputs score, abstention logit, feature attributions. | Yes | Scores (non-authoritative until validated) |
| L3 | **Coherence layer** | Factor graph over linked tasks; hard constraints (exact) plus learned pairwise factors (stage 3). Budgeted inference. | Partly (stage 3) | Interpretations |
| L4 | **Interpretation graph** | Typed dependencies from interpretations to their inputs (candidates, kernel outputs, model versions). Drives recomputation. | No | Dependency graph |
| G1 | **Label service** | Produces labels only from the sources defined in file 03, each tagged with source and maturity. | No | Label store |
| G2 | **Trainer and evaluator** | Purged walk-forward splits, pre-registered metrics, baseline comparison, report generation. | No | Model registry (candidate state) |
| G3 | **Registry and promotion gate** | Versioned artifacts; `candidate → shadow → champion`; rollback. Promotion only through the gate in file 04. | No | Registry |
| R1 | **Regression harness** | Contract tests on the kernel and golden snapshots. Must pass before any learned change is evaluated. | No | Test reports |

**Separation rule.** Learned components (L2, L3 learned factors, and the trainer) import read-only interfaces from the kernel. They cannot write to K1–K7 tables, change definitions, or alter a label. A kernel change requires a version bump and a full R1 run.

## F. Data structures

Schemas are logical. Field names are proposals for the builder; no storage technology is implied beyond what file 04 specifies.

### F.1 Core records

```
Bar {
  instrument_id, timeframe, open_time_utc, close_time_utc,
  open, high, low, close, volume?,   // as supplied by the source
  source_id, ingest_id, content_hash,
  flags: {gap_before, duplicate, intrabar_order_unknown}
}

Snapshot {                 // a decision-time view; the only input to tasks
  snapshot_id, instrument_id, decision_time_utc,
  last_closed_bar_index,   // nothing with a later knowable time may enter
  kernel_version, generator_set_version, feature_schema_version
}

Candidate {
  candidate_id,            // hash of (generator_id, generator_params_hash, instrument, timeframe, bar span)
  generator_id, generator_version, params_ref,   // params are DECLARED values, referenced by id
  kind,                    // e.g. PIVOT_HIGH, PIVOT_LOW, TR_TURN, CHANGEPOINT, LEG, SPAN
  start_bar, end_bar, price_levels: {…},
  confirmed_at_bar,        // first bar at which the candidate was knowable
  status: {confirmed | provisional | superseded | broken_at_bar?},
  provenance: {source_bar_hashes, generator_run_id}
}

LedgerEntry {
  snapshot_id, task_id, candidate_id,
  status: SCORED | EXCLUDED | NOT_EXAMINED | PENDING_KNOWABILITY,
  reason_code,             // e.g. NOT_KNOWABLE, ROLE_MISMATCH, BUDGET_EXHAUSTED, CONSTRAINT_FAILED
  score_ref?, model_version?
}

Interpretation {
  interpretation_id, snapshot_id,
  members: {task_id -> candidate_id | NONE | AMBIGUOUS_SET},
  constraint_status: {satisfied | violated(rule_id) | unchecked(budget)},
  joint_score?,            // ordinal; calibrated only if validated (see §Uncertainty)
  depends_on: [kernel_version, model_version, candidate_ids...],
  alternatives_pruned: [{interpretation_id, reason_code, budget_ref}]
}
```

### F.2 Task definitions (owner-declared)

Each task carries: `task_id`, `role` (for example REFERENCE, BINDING, FALSIFIER), `admissibility_rules` (hard), `declared_policy_slots` (for example P-REC, P-PROX from foundation file 17, unset until the owner declares them), `label_sources` (file 03), and `status` (`DECLARED`, `VALIDATED`, `RETIRED`).

### F.3 Feature schema (stage 1, unary layer)

Features are factual and causal at the snapshot. None encodes a universal rule.

| Group | Feature | Type | Note |
|---|---|---|---|
| Task | `task_id`, `role` | categorical | |
| Representation | `generator_id`, `scale_id` | categorical | scale identifiers are declared, not swept silently |
| Status | `confirmed` flag, `bars_since_confirmation` | bool, int | age is an input, not a relevance rule |
| Geometry | signed displacement from candidate to last close, in units of a **declared** scale measure | float | the measure and its window are owner-declared |
| Structure | number of confirmed candidates of the same kind between candidate and last close | int | count, not threshold |
| Relation | containment flag against parent-scale candidates; crossed flag; traded-through flag | bool | from K4/K5 |
| Context | rank by recency among same-kind candidates | int | feature only; recency is not a ranking |
| Diagnostics | number of generators that produced an equivalent candidate | int | agreement count, not a vote weight |

Learned thresholds are a known hazard: a tree model will create cut points that are not declared. Mitigations are in file 05 §L (item 3) and in the calibration caveat above.

### F.4 Model input and output

- **Input to L2:** one row per (snapshot, task, admissible candidate). Rows with the same snapshot form a group for listwise objectives.
- **Output from L2:** `score(candidate)`; `abstain_logit(snapshot, task)`; per-row feature attributions; model version and feature schema version.
- **Output from L3:** a set of interpretations (not a single answer), each with constraint status and the list of alternatives not examined.

## Inference workflow

### W1. Incremental update on a new closed bar

1. K1 appends the bar; K2 computes derived fields; ambiguity flags set where intrabar order is unknown.
2. K3 updates each generator's state machine. Work is O(number of active generator states), not O(history).
3. Candidates that become confirmed at this bar are written with `confirmed_at_bar`. Candidates confirmed earlier are not rewritten; a later revision is a new event with `superseded` linking to the old record.
4. K5 index inserts. Crossing and containment are checked only against candidates whose time spans overlap the new bar's window (index query), so cost is proportional to the affected set.
5. For each task in the dependency graph whose inputs changed, K7 recomputes the admissible set and the ledger. Tasks whose inputs did not change are not recomputed.
6. L1 extracts features for affected rows; L2 scores them; L3 recomputes only the factor components that contain a changed variable.
7. Snapshot record and interpretation records are written with all version identifiers.

### W2. Full decision-time inference (one snapshot)

1. Snapshot fixed: `last_closed_bar_index`, versions.
2. Enumerate candidates from the current K3 state; exclude by knowability first (exact).
3. Per task: admissible set (exact); ledger entries for every candidate in the set and for every excluded candidate with reason.
4. Score admissible sets with L2. If a budget is set for scoring, unscored candidates are recorded as `NOT_EXAMINED(budget)`. No silent truncation.
5. Build the interdependency graph among task variables. Partition into connected components by hard or learned factors.
6. For each component: if the product of domain sizes is within the declared budget, enumerate exactly; otherwise run declared approximate inference (beam or loopy belief propagation) and record the boundary of the search.
7. Emit interpretations, their constraint status, and the list of pruned or unexamined alternatives. Attach `depends_on`.

### Complexity (structural, not benchmarked)

- Candidate generation: linear in new bars, times the number of generator states.
- Admissibility per task: linear in candidates (after the index).
- Scoring: linear in admissible rows × features.
- Coherence: product of domain sizes within each component. This is the principal scaling risk. Components are kept small by the hard constraints and by declared task scope. The size of the largest component is reported on every run; it is a diagnostic, not a claim.
- Pairwise candidate enumeration is never performed globally; it is performed only within index-returned neighbourhoods.

## Uncertainty representation

Each output carries explicit fields, and the system never reports a bare number as confidence.

| Field | Meaning | When it is populated |
|---|---|---|
| `score` | ordinal ranking value from L2 | always for scored rows |
| `calibrated_prob` | probability on held-out data | only after a calibration check on time-blocked data passes; otherwise `null` |
| `abstain` + `reason` | the system declines to choose among an admissible set | when no candidate meets the declared ambiguity rule, or when the admissible set is empty |
| `ensemble_spread` | disagreement among ensemble members | when ensembles are used |
| `ood_flag` | snapshot features outside training support (declared check) | always computed |
| `status` | `provisional`, `confirmed`, `superseded` | always |
| `constraint_status` | `satisfied`, `violated(rule)`, `unchecked(budget)` | always for interpretations |

**Calibration caveat.** Conformal-style coverage needs exchangeability, which time series do not satisfy. Any set-valued output must be calibrated on time-blocked hold-outs with the caveat recorded in the report.

**Ambiguity rule.** "Ambiguous" is a declared policy, not a learned value. The owner declares when the top-ranked gap is too small to choose; until then, the system emits the full ranked list and no abstention claim.

## H. Foundational mastery: safeguards

The owner's central requirement is that the system must not master concepts in appearance only. The following are structural safeguards, not training tricks.

1. **Definitions live in the kernel.** Every concept used by a task maps to a kernel generator or a geometry rule with a definition ID from the foundation's concept specs. A learned model cannot introduce a new concept.
2. **Definition hashing.** Each definition's canonical text and parameter set is hashed into `generator_version`. Outputs cite the hash. A changed definition is a different object, even when its name is unchanged.
3. **Contract tests** (R1), for example:
   - Candle semantics: an ambiguous intrabar order produces `UNKNOWN` (never a choice).
   - Knowability: a candidate is never scored before `confirmed_at_bar` for the snapshot.
   - Monotonicity: adding a bar never changes an earlier confirmed candidate; only a `superseded` event may be added, and it is logged.
   - Crossing: a level crossed in the window is returned exactly, and no crossed level is omitted from the crossing query.
   - Completeness of the ledger: every candidate of the snapshot has exactly one ledger status per task.
4. **Read-only learning.** A learned output cannot write to kernel tables; a failing contract test overrides any model score.
5. **Declared-rule fidelity tests.** Where a learned scorer approximates a declared rule (for example during bootstrapping), agreement with the rule is measured on held-out snapshots, and disagreements are stored for review. Agreement is not treated as correctness of the rule.
6. **Mastery probes (understanding tests).** Specified in file 05 §Understanding tests.
7. **Attribution logging.** Every interpretation records which kernel version, generator parameters and model version produced it, so a regression can be traced to one component.
