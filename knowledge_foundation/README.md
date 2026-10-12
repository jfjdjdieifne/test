# Causal Market Intelligence — Applied Knowledge Foundation (V1, research draft)

Status: **research knowledge only. No trading code, no strategy optimization, no performance claims.**
Prepared: 2026-10-12. Branch: `arena/5125ef9c-test`. Revision: R2 (targeted repair plus contextual selection; see file 14).

## Reading order

| File | Purpose |
|---|---|
| [00_RESEARCH_METHOD_AND_EVIDENCE.md](00_RESEARCH_METHOD_AND_EVIDENCE.md) | Evidence grades, category discipline, what was and was not verified |
| [01_PRICE_MOVEMENT.md](01_PRICE_MOVEMENT.md) | Observations, measurements, scale, movement change |
| [02_SWINGS_AND_WAVES.md](02_SWINGS_AND_WAVES.md) | Candidate turning points, knowability, task-dependent swing choice |
| [03_MARKET_STRUCTURE.md](03_MARKET_STRUCTURE.md) | Structure labels, breaks, competing structure views |
| [04_LIQUIDITY.md](04_LIQUIDITY.md) | Liquidity references as derived candidates, not observed orders |
| [05_FVG_ORDER_BLOCKS_ZONES.md](05_FVG_ORDER_BLOCKS_ZONES.md) | Zone candidates, ICT definitions vs community definitions |
| [06_MULTISCALE_CONTEXTUAL_REASONING.md](06_MULTISCALE_CONTEXTUAL_REASONING.md) | Dependency graph, interpretation ledger, revision |
| [07_LEARNING_AND_SELF_IMPROVEMENT.md](07_LEARNING_AND_SELF_IMPROVEMENT.md) | Six separate learning targets; learning approaches compared |
| [08_APPLIED_CHART_CASES.md](08_APPLIED_CHART_CASES.md) | Source-grounded cases (transcript-level) and labeled hypotheticals |
| [09_OPEN_SOURCE_AND_ACADEMIC_METHODS.md](09_OPEN_SOURCE_AND_ACADEMIC_METHODS.md) | Verified academic and open-source components |
| [10_CONFLICTS_UNCERTAINTIES_AND_LIMITS.md](10_CONFLICTS_UNCERTAINTIES_AND_LIMITS.md) | Conflicts, gaps, unresolved issues |
| [11_IMPLEMENTATION_KNOWLEDGE_CONTRACTS.md](11_IMPLEMENTATION_KNOWLEDGE_CONTRACTS.md) | Task contracts for a future implementation team |
| [12_SOURCE_INDEX.md](12_SOURCE_INDEX.md) | Every source, with ID, URL, type, verification status |
| [13_AUDIT_CONSISTENCY_AND_SUMMARY.md](13_AUDIT_CONSISTENCY_AND_SUMMARY.md) | Executive summary, consistency checks, audit instructions, next steps |
| [14_RESOLUTION_MAP_R2.md](14_RESOLUTION_MAP_R2.md) | R2 audit entry point: finding → change map, source changes, check results, exact file changes, open items |
| [15_CONTEXTUAL_SELECTION_METHOD.md](15_CONTEXTUAL_SELECTION_METHOD.md) | Contextual selection method: property classes, exclusions, justified vs unresolved states, dependency-aware combinations |
| [16_SWING_WAVE_SELECTION.md](16_SWING_WAVE_SELECTION.md) | Swing/wave task cards, containment and escape, provisional points |
| [17_SEED_PROCEDURES.md](17_SEED_PROCEDURES.md) | Seed procedure contracts SP-01 to SP-20 with required fields |
| [18_LOCAL_LEARNING_SELECTOR.md](18_LOCAL_LEARNING_SELECTOR.md) | Local (non-LLM) learner design: objectives A–D kept separate; regression protocol |
| [19_SELECTION_CASES.md](19_SELECTION_CASES.md) | Worked cases W1–W10, O1–O2 (constructed fixtures) |
| [claims_index.json](claims_index.json) | Machine-readable claim index for audit (142 claims, schema 1.1) |
| [checks/check_r2.py](checks/check_r2.py) | Read-only consistency checker (run: `python3 checks/check_r2.py`) |

## Claim ID convention

`PM-` price movement · `SW-` swings/waves · `MS-` structure · `LQ-` liquidity · `FZ-` FVG/OB/zones · `MR-` multiscale reasoning · `LL-` learning · `CC-` chart cases (renamed from `CH-` in R2) · `OS-` open source/academic · `CF-` conflicts · `IC-` implementation contracts · `CSM-` selection method · `SWS-` swing/wave selection · `SP-` seed procedures · `LRN-` learner design · `SRC-` sources.

Case labels (`CASE-01`…`CASE-08` in file 08; `W1`…`W10`, `O1`, `O2` in file 19) are a separate namespace and are not claim IDs.

Every claim that affects a selection carries: claim type (A–H, see file 00), evidence grade, source ID(s), scope, limitations, and related/conflicting claims. The full list is in `claims_index.json`.

## Repository note

The repository at `/home/user/test` contains pre-existing project files and archives. They were **not** opened or used as input for this research, to honor the mission's requirement of independent knowledge development. Nothing outside this folder was modified.
