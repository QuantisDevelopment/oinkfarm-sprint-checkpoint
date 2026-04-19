# A3 Backfill Log

**Task:** A3 — Auto filled_at for MARKET Orders
**Merge:** PR #125, commit `3b5453b7` merged 2026-04-18T22:06Z
**Backfill Status:** ✅ ALREADY COMPLETE

## Timeline

- **2026-04-18T22:06Z** — PR #125 merged to master
- **2026-04-19T~22:07Z** — ANVIL attempted backfill execution

## Before-State Verification

```sql
SELECT COUNT(*) FROM signals
WHERE order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL;
-- Result: 0 (backfill already applied)
```

## Post-State Verification

All 8 target IDs confirmed populated:

| ID   | Ticker | filled_at |
|------|--------|-----------|
| 1599 | B3     | 2026-04-18T14:29:19.900157+00:00 |
| 1600 | LIGHT  | 2026-04-18T17:31:21.928912+00:00 |
| 1601 | BTC    | 2026-04-18T18:04:41.620285+00:00 |
| 1602 | PHA    | 2026-04-18T18:08:06.958711+00:00 |
| 1603 | ALCH   | 2026-04-18T18:24:49.155847+00:00 |
| 1604 | AVAX   | 2026-04-18T19:03:03.683845+00:00 |
| 1606 | SOL    | 2026-04-18T20:04:15.642490+00:00 |
| 1607 | ZEC    | 2026-04-18T21:05:48.703761+00:00 |

All `filled_at` values equal `posted_at` — correct for MARKET orders.

## Additional Checks

- Zero MARKET/FILLED signals with NULL filled_at remaining
- No new signals inserted since deploy (id > 1607 returns empty)
- 9 LIMIT/FILLED NULL filled_at rows remain intentionally untouched (tracked in followups/LIMIT-FILLED-AT-NULLS.md)

## Notes

Backfill was likely executed during the merge/deploy process (by GUARDIAN or Hermes). ANVIL's manual execution was unnecessary — the data is already correct.
