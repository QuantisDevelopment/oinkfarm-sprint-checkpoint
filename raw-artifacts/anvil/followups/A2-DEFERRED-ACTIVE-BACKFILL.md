# ✅ CLOSED: Backfill remaining_pct on ACTIVE Signals

**Task:** A2 follow-up
**Created:** 2026-04-19
**Closed:** 2026-04-19
**Priority:** LOW — cosmetic consistency
**Resolution:** Not needed. SQLite ALTER TABLE ADD COLUMN with DEFAULT 100.0 backfills ALL existing rows automatically. Mike confirmed all 490 signals have remaining_pct=100.0 after deploy.

## What
Run `UPDATE signals SET remaining_pct = 100.0 WHERE remaining_pct IS NULL AND status IN ('ACTIVE', 'PENDING')` to normalize the column for active signals.

## Why deferred
- Default 100.0 means NULL and 100.0 are semantically identical for new code
- calculate_blended_pnl() handles NULL remaining_pct via backward-compat path
- Mike should confirm whether this is desired

## Risk
Extremely low — sets column to its own default value. No behavioral change.
