# 🛡️ GUARDIAN Phase 1 Review — Task A6: Ghost Closure Confirmation Flag

| Field | Value |
|-------|-------|
| **Branch** | `anvil/A6-ghost-closure-flag` |
| **Commits** | `c6cb99e1b7f5c5ac79f1cc39c1438719bfcae8c8` |
| **Change Tier** | 🟡 STANDARD |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-19 |
| **PR** | `#20` |

---

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | **10** | No DDL, no column changes, no constraint changes. A6 uses existing `signal_events` schema and existing `signals.notes` / `close_source` fields correctly. `GHOST_CLOSURE` already exists in the lifecycle event catalog. |
| 2 | Formula Accuracy | 25% | **10** | No financial formula or PnL math changed. The new logic writes additive audit metadata only. FET #1159 remains unchanged in production: `CLOSED_WIN`, `final_roi=3.37`, `remaining_pct=100.0`. |
| 3 | Data Migration Safety | 20% | **10** | No migration, no backfill, no destructive update. Write path is additive and transaction-scoped. `close_source` is intentionally left unchanged for provisional ghost closures, which is the correct safety boundary. |
| 4 | Query Performance | 10% | **9** | The new lookup is small and operationally acceptable at current scale, but it does introduce a new `signals JOIN traders` query on each soft-close path, with candidate filtering and `ORDER BY s.id DESC` and no new supporting index. Low risk today, slight deduction for added lookup cost. |
| 5 | Regression Risk | 20% | **9** | The two critical Phase 0 safety concerns are implemented correctly: entry-discriminated lookup and idempotent note coupling via `changes()`. Diff inspection confirms the instrumentation is in the actual `elif kind == "CLOSE"` branch. 9/9 A6 tests, 23/23 reconciler tests, and 281/281 full-suite tests passed. Minor deduction because the dedicated A6 test file mirrors the inline DB logic through a helper rather than exercising the full async router path end-to-end. |
| | **OVERALL** | 100% | **9.70** | |

**Score calculation:** `(10 × 0.25) + (10 × 0.25) + (10 × 0.20) + (9 × 0.10) + (9 × 0.20) = 9.70`

---

## Review Evidence

### Diff scope reviewed
```text
scripts/signal_gateway/signal_router.py
tests/test_a6_ghost_closure.py
```

```text
2 files changed, 499 insertions(+), 0 deletions(-)
```

### Code verification
Confirmed in `signal_router.py`:
- A6 logic sits inside the real `elif kind == "CLOSE":` branch
- guarded by `detail.get("soft_close") is True`
- entry discriminator uses `abs(db_entry - action_entry) / action_entry <= 0.05`
- event INSERT and note UPDATE run inside one sqlite connection/transaction
- note append occurs only when `SELECT changes()` indicates first insert succeeded
- no `close_source` mutation exists in the diff
- WARNING path includes trader, ticker, direction, entry, and candidate count

### Test verification
```text
python3 -m pytest -q tests/test_a6_ghost_closure.py
Result: 9 passed

python3 -m pytest -q tests/test_reconciler.py
Result: 23 passed

python3 -m pytest -q
Result: 281 passed, 1 pre-existing warning
```

### Reference record re-check
```text
SELECT id,ticker,direction,entry_price,exit_price,leverage,final_roi,status,remaining_pct
FROM signals WHERE id=1159;

1159 | FET | LONG | 0.2285 | 0.2285 | NULL | 3.37 | CLOSED_WIN | 100.0
```

---

## Pre-Deploy Baseline Snapshot

| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-1 (signal_events total) | 305 | production DB @ review time |
| SC-2 (False closures) | 11.8841% | rolling 30-day query @ review time |
| SC-4 (Signal count) | 493 | `SELECT COUNT(*) FROM signals` @ review time |
| KPI-R1 (Breakeven %) | 20.4167% | 7-day rolling query @ review time |
| KPI-R4 (NULL leverage %) | 80.1217% | full-table query @ review time |
| KPI-R5 (NULL filled_at, FILLED MARKET) | 0 | production DB @ same review window |
| KPI-R3 (duplicate discord_message_id groups) | 14 | production DB @ same review window |

**Expected A6 post-deploy effect:** no immediate shift in SC-2, KPI-R1, KPI-R4, KPI-R5, or KPI-R3. The primary observable change is future appearance of `GHOST_CLOSURE` events plus matching note tags after organic board-absent soft closes.

---

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| 1 | P3 | Query Performance | Soft-close path adds a new `signals JOIN traders` lookup with candidate scan + `ORDER BY s.id DESC`, without a new dedicated index | Diff review of `signal_router.py` |
| 2 | P3 | Regression Risk | The dedicated A6 tests validate a mirrored helper instead of driving the full async `_route_board_update()` path end-to-end | `tests/test_a6_ghost_closure.py` review |

**No P1/P2 issues found.**

---

## Formula Verification

**No financial formula changes in A6.**

**Reference case: FET #1159**
- Entry price: **0.2285**
- Exit price: **0.2285**
- Direction: **LONG**
- Leverage: **NULL**
- Stored ROI: **3.37%**
- Status: **CLOSED_WIN**
- Remaining %: **100.0**
- Match: ✅ unchanged

**Assessment:** A6 adds ghost-closure audit metadata only. It does not touch lifecycle PnL, blended ROI, leverage handling, or closure-price math. The production reference row remains intact.

---

## What’s Done Well

1. **Phase 0 blockers were resolved correctly.** The write target is no longer ambiguous because the lookup is entry-discriminated instead of newest-row wins.
2. **Idempotency is implemented at the right boundary.** Coupling note append to successful first insert prevents duplicate audit tags across repeated absent cycles.
3. **Transaction safety is correct.** Event and note writes share one sqlite transaction.
4. **Observability is good.** The no-match WARNING includes enough data for post-deploy audit investigation.
5. **Scope discipline is strong.** No schema churn, no backfill, no `close_source` overreach, no financial hotpath changes.

---

## Verdict

**✅ PASS**

- Overall score: **9.70** vs threshold **≥9.0** (🟡 STANDARD)
- Data-safety blockers from Phase 0 are resolved in the implementation.
- The change is additive, rollback-friendly, and appropriately bounded to audit metadata.
- Minor deductions are advisory only, not blockers.

**Deployment readiness:** Yes.

---

## Canary Focus (Post-Deploy)

When ANVIL deploys A6, GUARDIAN should verify:

1. **First organic ghost closure**
   ```sql
   SELECT se.signal_id, se.payload, se.created_at, s.ticker, s.notes
   FROM signal_events se
   JOIN signals s ON se.signal_id = s.id
   WHERE se.event_type='GHOST_CLOSURE'
   ORDER BY se.created_at DESC
   LIMIT 10;
   ```
   Expect at least one row with valid `absent_count`, trader, ticker, direction, and matching note tag.

2. **Idempotency under repeated absent cycles**
   ```sql
   SELECT signal_id, COUNT(*)
   FROM signal_events
   WHERE event_type='GHOST_CLOSURE'
   GROUP BY signal_id
   HAVING COUNT(*) > 1;
   ```
   Expect zero rows.

3. **Confirmed-close protection**
   ```sql
   SELECT id, notes, close_source
   FROM signals
   WHERE notes LIKE '%[A6: ghost_closure %' AND close_source IS NOT NULL;
   ```
   Expect empty or manually explainable result set.

4. **No broader KPI regression**
   - SC-2, KPI-R1, KPI-R4, KPI-R5 should remain stable post-deploy.

---

*🛡️ GUARDIAN — Phase 1 Pre-Deploy Review (🟡 STANDARD)*
