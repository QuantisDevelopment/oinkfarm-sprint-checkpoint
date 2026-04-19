# A8 Backfill Log — sl_type Column

## Pre-Migration State
- **Total signals:** 494
- **sl_type column:** did not exist

## Migration Executed
- **Script:** `scripts/migrations/a8_sl_type.sql`
- **Timestamp:** 2026-04-19T15:28Z

### Steps in Migration
1. `ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED'`
   - All 494 rows get DEFAULT 'FIXED'
2. `UPDATE signals SET sl_type = 'CONDITIONAL' WHERE notes LIKE '%SL:CONDITIONAL%' AND sl_type = 'FIXED'`
   - **Rows affected:** 0 (no existing signals had `[SL:CONDITIONAL]` tags)
3. `UPDATE signals SET sl_type = 'NONE' WHERE stop_loss IS NULL AND notes NOT LIKE '%SL:CONDITIONAL%' AND sl_type = 'FIXED'`
   - **Rows affected:** 28

## Post-Migration Distribution

| sl_type | Count |
|---------|-------|
| FIXED | 466 |
| NONE | 28 |
| CONDITIONAL | 0 |
| MANUAL | 0 |
| **NULL** | **0** ✅ |
| **Total** | **494** |

## Reference Case Verification
- **FET #1159:** `stop_loss=0.2285`, `sl_type=FIXED` ✅
  - Numeric SL present → correctly classified as FIXED

## Integrity Checks
```sql
SELECT COUNT(*) FROM signals WHERE sl_type IS NULL;
-- Result: 0 ✅

SELECT sl_type, COUNT(*) FROM signals GROUP BY sl_type;
-- FIXED|466
-- NONE|28
```
