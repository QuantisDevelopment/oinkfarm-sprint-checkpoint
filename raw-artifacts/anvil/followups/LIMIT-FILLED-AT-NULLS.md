# Follow-up: LIMIT Orders with NULL filled_at

**Filed by:** ⚒️ ANVIL
**Date:** 2026-04-18
**Related Task:** A3 (Auto filled_at for MARKET orders)
**Priority:** Low — no functional impact (downstream code falls back to posted_at)

## Issue

9 LIMIT/FILLED signals have `filled_at IS NULL` in the production database. These should have been populated by `LifecycleManager._check_limit_fills()` in oink-sync when the PENDING→ACTIVE transition was detected.

## Affected Rows

```sql
SELECT id, ticker, posted_at, filled_at
FROM signals
WHERE order_type = 'LIMIT'
  AND fill_status = 'FILLED'
  AND filled_at IS NULL;
```

| ID   | Ticker |
|------|--------|
| 981  | CHZ    |
| 1136 | BTC    |
| 1165 | ENA    |
| 1188 | BTC    |
| 1237 | BTC    |
| 1244 | TAO    |
| 1308 | HYPE   |
| 1311 | HEMI   |
| 1490 | HYPE   |

## Root Cause (Suspected)

These signals likely transitioned PENDING→FILLED before `_check_limit_fills()` was instrumented to set `filled_at`, or the transition was handled by a different code path that didn't populate the field.

## Recommended Fix

Investigate `_check_limit_fills()` in `oink_sync/lifecycle.py` to:
1. Confirm it sets `filled_at` on PENDING→FILLED transitions
2. Backfill the 9 affected rows (would need to determine the actual fill timestamp — unlike MARKET orders, `posted_at` is NOT the correct fill time for LIMIT orders)

## Impact

**None currently.** Downstream consumers (`lifecycle.py` grace period, `portfolio_stats.py` hold time) use `filled_at or posted_at` patterns. The fallback to `posted_at` is functionally acceptable but semantically incorrect for LIMIT orders (fill time ≠ post time).

## Out of Scope for A3

A3 explicitly targets MARKET orders only. LIMIT order `filled_at` requires a different value source (actual exchange fill time, not `posted_at`).
