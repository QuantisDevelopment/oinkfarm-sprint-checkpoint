# A11 Backfill Log

**Task:** A11 — Leverage Source Tracking
**Executed:** 2026-04-19 (during implementation phase, before deploy)

## Migration
```sql
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
```
Column added at position 50 in signals table schema.

## Backfill
```sql
UPDATE signals SET leverage_source = 'EXPLICIT' WHERE leverage IS NOT NULL;
```

**Rows affected:** 98 (matched expected count from plan)

## Verification
```
leverage_source | count
----------------|------
NULL            | 396
EXPLICIT        | 98
TOTAL           | 494
```

## Notes
- Production DB (`/home/m/data/oinkfarm.db`) is symlinked from `.openclaw/workspace/data/oinkfarm.db` — same physical file. Migration + backfill applied once in workspace, automatically present in production path.
- All NULL-leverage rows correctly retain `leverage_source = NULL`.
