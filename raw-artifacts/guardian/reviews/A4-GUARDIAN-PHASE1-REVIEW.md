## GUARDIAN Review — A4

| Field | Value |
|-------|-------|
| **Branch** | anvil/A4-partially-closed-status |
| **Commits** | ab5d941523c7bdc929fd6bc82b3bac3811884bd8 |
| **Change Tier** | 🔴 CRITICAL |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-19 |

### Dimension Scores
| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | 10 | No schema migration. `PARTIALLY_CLOSED` fits existing uppercase status constraint. `STATUS_CHANGED` added to lifecycle event catalog. No incompatible trigger behavior found on `signals`; atomic status+remaining update is safe. |
| 2 | Formula Accuracy | 25% | 10 | Same-cycle all-TP close calls `calculate_blended_pnl()` with event-sourced `_collect_tp_close_pcts()` plus current TP close_pct, preventing limbo and preserving weighted ROI semantics. FET #1159 remains intact in production (`final_roi=3.37`, `remaining_pct=100.0`, `CLOSED_WIN`). Local reference calc still yields 1.6779% pre-rounding, matching the expected 1.68% case. |
| 3 | Data Migration Safety | 20% | 10 | Backfill is additive, idempotent, and rollback-safe. PR description includes pre-SELECT evidence for IDs 1561 and 1602, abort-if-rowcount>4 guard, explicit `BEGIN/COMMIT`, and anomaly note for #1602. No destructive DDL or irreversible rewrite. |
| 4 | Query Performance | 10% | 9 | The approved blast-radius expansion to 10 sites is correct. Broadening `status='ACTIVE'` to `IN ('ACTIVE','PARTIALLY_CLOSED')` does invalidate the ACTIVE-only partial index path and falls back to broader status indexing. At current scale this is acceptable and explicitly acknowledged in the PR. Small deduction for the planner regression, even though it is operationally low-risk today. |
| 5 | Regression Risk | 20% | 10 | All 10 required hotpath sites are present: lifecycle L1-L5 plus engine E1-E5, including E5 `_calculate_pnl()` so PARTIALLY_CLOSED rows do not silently lose PnL updates. Same-cycle closure path is implemented, no PARTIALLY_CLOSED limbo remains, and relevant tests plus the existing lifecycle/event suites passed locally (66 passed total across new + existing suites). |
| | **OVERALL** | 100% | **9.90** | |

### Pre-Deploy Baseline Snapshot
| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-1 (Audit trail) | 137 total signal_events; 16/432 modified historical signals with events | 2026-04-19 daily run |
| SC-2 (False closures) | 12.0588% | 2026-04-19 daily run |
| SC-3 (PnL accuracy screen) | 17 heuristic deviations >0.5pp | 2026-04-19 daily run |
| SC-4 (Signal count) | 490 | 2026-04-19 daily run |
| KPI-R1 (Breakeven %) | 21.097% | 2026-04-19 daily run |
| KPI-R4 (NULL leverage %) | 80.0% | 2026-04-19 daily run |

### Issues Found
| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| 1 | P3 | Query Performance | `IN ('ACTIVE','PARTIALLY_CLOSED')` no longer uses the current ACTIVE-only partial index path | Query-plan check during review |
| 2 | P3 | Regression Risk | `test_sl_proximity_includes_partially_closed` assertion is weaker than the strongest possible form | Test file review; function executes and scan path is broadened, but test does not assert returned alert contents |
| 3 | P3 | Code consistency | Same-cycle closure re-queries `posted_at` instead of threading it through from the parent row | `lifecycle.py` review; low impact |

### Formula Verification
**Reference case: FET #1159**
- Entry price: 0.2285
- Exit price: 0.2285
- Direction: LONG
- Leverage: NULL / ignored by policy
- Expected ROI: 1.68%
- Computed ROI: 1.6779%
- Match: ✅

**Walkthrough:**
`calculate_blended_pnl()` remains unchanged for non-partial, non-event-sourced legacy cases. The A4 changes only alter status transitions and same-cycle full-TP closure handling. Production row #1159 remains `CLOSED_WIN`, `remaining_pct=100.0`, with no PARTIALLY_CLOSED path involvement, so the reference case is preserved.

### What's Done Well
- The Phase 0 blocker was resolved correctly: engine.py was expanded in all required places, including the critical `_calculate_pnl()` gate.
- Same-cycle full TP closure is implemented cleanly, with no open-state limbo.
- Backfill procedure is disciplined and reviewer-friendly.
- Test coverage is strong and the relevant existing suites still pass unmodified.

### Verdict
**PASS**
- Overall score: **9.90** vs threshold **9.5**
- This change is safe to proceed from a data perspective. The only deductions are minor advisories, not blockers.

Forward to orchestrator.
