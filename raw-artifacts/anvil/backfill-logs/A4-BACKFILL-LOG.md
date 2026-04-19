# A4 Backfill Log

**Executed:** 2026-04-19 12:45 CEST (10:45:10 UTC)
**Operator:** ANVIL (⚒️)
**Task:** A4 — PARTIALLY_CLOSED Status
**PR:** oink-sync #7 (merge commit e9be741a)

## Pre-SELECT

```sql
SELECT id, status, remaining_pct, tp1_hit_at, tp2_hit_at, tp3_hit_at
FROM signals
WHERE status='ACTIVE' AND remaining_pct > 0.0 AND remaining_pct < 100.0;
```

| id   | status | remaining_pct | tp1_hit_at | tp2_hit_at | tp3_hit_at |
|------|--------|---------------|------------|------------|------------|
| 1602 | ACTIVE | 50.0 | 2026-04-18T18:33:11.683240+00:00 | 2026-04-19T02:34:50.784126+00:00 | 2026-04-19T03:53:49.080547+00:00 |
| 1561 | ACTIVE | 50.0 | 2026-04-18T11:43:40.233269+00:00 | 2026-04-19T07:23:26.619491+00:00 | (null) |

**Rowcount: 2** (threshold ≤4 — PROCEED)

### Anomaly: Signal #1602

tp3_hit_at is set while remaining_pct=50.0. This is a **pre-existing data quality issue** (pre-A4), not an A4 regression. Documented in proposal §2E. Root cause: tp3 was hit but remaining_pct was not decremented (likely pre-A2 behavior before remaining_pct tracking existed).

## Transaction SQL

```sql
BEGIN;
UPDATE signals
SET status = 'PARTIALLY_CLOSED',
    updated_at = strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')
WHERE status = 'ACTIVE'
  AND remaining_pct > 0.0
  AND remaining_pct < 100.0
  AND id IN (1561, 1602);
-- changes() = 2
COMMIT;
```

## Post-Verification

```
1561|PARTIALLY_CLOSED|50.0|2026-04-19T10:45:10.843+00:00
1602|PARTIALLY_CLOSED|50.0|2026-04-19T10:45:10.843+00:00
```

Zero ACTIVE rows with 0 < remaining_pct < 100 remain.

## Status Distribution (post-backfill)

| status | count |
|--------|-------|
| ACTIVE | 77 |
| CANCELLED | 57 |
| CLOSED_BREAKEVEN | 69 |
| CLOSED_LOSS | 176 |
| CLOSED_MANUAL | 7 |
| CLOSED_WIN | 93 |
| PARTIALLY_CLOSED | 2 |
| PENDING | 11 |

**Total: 492**
