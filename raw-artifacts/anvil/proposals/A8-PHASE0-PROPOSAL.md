# A8 Phase 0 Proposal — Conditional SL Type Field

**Task:** A8 — Conditional SL Type Field  
**Tier:** 🟡 STANDARD  
**Target:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (canonical oinkfarm copy)  
**Spec:** FORGE plan at `/home/oinkv/forge-workspace/plans/TASK-A8-plan.md`  
**OinkV Audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A8.md` — 🟢 READY-WITH-MINOR-EDITS  
**Date:** 2026-04-19

---

## Problem

The `signals` table stores `stop_loss FLOAT` but has no structured way to distinguish the *type* of stop-loss: was it an explicit numeric price? A text-based condition ("SL if daily close below X")? An operator override? Or simply not provided? Micro-gate already detects conditional SL text and writes `[SL:CONDITIONAL ...]` to the free-text `notes` field, but this can't be reliably queried or aggregated.

Current state (verified post-A11 merge):
- 28 signals (5.7%) have `stop_loss IS NULL` — no SL provided
- 0 signals have `[SL:CONDITIONAL...]` in notes (detection is recent, no signals processed with flag yet)
- No `sl_type` column exists (current column count: 51 including `leverage_source` from A11)

## Approach

Add `sl_type VARCHAR(15) DEFAULT 'FIXED'` column to signals. Four canonical values:

| Value | Meaning | Trigger |
|-------|---------|---------|
| `FIXED` | Explicit numeric SL, extraction succeeded | `stop_loss IS NOT NULL`, no conditional keywords in `sl_note` |
| `CONDITIONAL` | Text-based condition detected | `sl_note` contains conditional keywords (with or without extracted numeric) |
| `MANUAL` | Operator-issued SL override via UPDATE message | `_process_update()` changes `stop_loss` |
| `NONE` | No SL provided or determinable | `stop_loss IS NULL`, no conditional keywords |

**Schema change:**
```sql
ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED';
```

**Backfill** (two-step):
```sql
-- Step 1: Tag conditional SL signals (expected: 0 rows currently)
UPDATE signals SET sl_type = 'CONDITIONAL' WHERE notes LIKE '%SL:CONDITIONAL%' AND sl_type = 'FIXED';

-- Step 2: Tag no-SL signals (expected: 28 rows)
UPDATE signals SET sl_type = 'NONE' WHERE stop_loss IS NULL AND notes NOT LIKE '%SL:CONDITIONAL%' AND sl_type = 'FIXED';
```

Post-backfill distribution: FIXED 466, NONE 28, CONDITIONAL 0, MANUAL 0 (total 494).

## Key Decisions

1. **Shared keyword constant.** The conditional-SL keyword list (`"close below"`, `"close above"`, `"4h"`, `"1d"`, `"daily"`, `"weekly"`, `"h2"`, `"h4"`, `"d1"`, `"5m"`, `"15m"`, `"1h"`) currently appears once in the notes-tag block (line 764). Per FORGE §4d, I'll extract it to a module-level `_CONDITIONAL_SL_KEYWORDS` tuple and reference it in both the existing notes-tag block and the new sl_type logic. This eliminates the drift risk flagged in the plan's risk assessment.

2. **sl_type logic placement.** After Section 8c (A15 SL guard, ends ~line 787) and before Section 9 (TP safety check, line 826). Per OinkV MINOR-A8-3, the plan's "after line 799" is imprecise — I'll place after the complete SL processing section ends, so sl_type reads final stop_loss and sl_note values.

3. **UPDATE path: MANUAL override.** When `_process_update()` receives a `stop_loss` change, I'll also set `sl_type = 'MANUAL'`. Requires adding `"sl_type"` to `_ALLOWED_UPDATE_COLS` (line 1050). Non-SL updates leave `sl_type` unchanged.

4. **Test location.** Following A5/A7/A11 convention, tests go in `/home/oinkv/.openclaw/workspace/tests/test_a8_sl_type.py` (not `signal-gateway/tests/` per plan §5 — OinkV MINOR-A8-1 correction).

5. **oink-sync test_lifecycle_events.py schema update.** OPTIONAL (OinkV MINOR-A8-4). I'll add `sl_type TEXT DEFAULT 'FIXED'` to the in-memory schema for forward-compatibility, but it's not required for correctness since oink-sync tests don't exercise the micro-gate INSERT path.

6. **No event logging.** `sl_type` is set at INSERT time (or updated to MANUAL via operator UPDATE). No lifecycle event needed — it's classification metadata, not a state transition.

7. **Deploy via cp + systemctl restart** (same pattern as A5/A9/A11).

## Test Strategy

8 tests in `tests/test_a8_sl_type.py` (6 MUST, 2 SHOULD):

| Test | Type | Priority |
|------|------|----------|
| Numeric SL, no conditional → FIXED | unit | MUST |
| No SL, no note → NONE | unit | MUST |
| sl_note with conditional keyword, no numeric → CONDITIONAL | unit | MUST |
| sl_note with conditional keyword + extracted numeric → CONDITIONAL | unit | MUST |
| Operator UPDATE changes SL → MANUAL | unit | MUST |
| 10 mixed signals, none have sl_type=NULL | integration | MUST |
| UPDATE changes only notes, sl_type unchanged | regression | SHOULD |
| Backfill SQL correctness | unit | SHOULD |

## For GUARDIAN Specifically

**Data impact:** Additive column with DEFAULT 'FIXED'. No existing data modified except:
- 28 signals backfilled from FIXED → NONE (NULL SL signals)
- 0 signals backfilled to CONDITIONAL (no existing [SL:CONDITIONAL] notes)

**Formula/calculation impact:** None. `sl_type` is classification metadata. oink-sync `lifecycle.py` does not read or use sl_type. `calculate_blended_pnl()` and `_check_sl_tp()` are not touched.

**Schema safety:** `ALTER TABLE ADD COLUMN` with DEFAULT is SQLite-safe (no table rebuild). Backfill uses targeted WHERE clauses. Rollback: `ALTER TABLE signals DROP COLUMN sl_type` (SQLite 3.46.1 supports this).

## Acceptance Criteria

1. `PRAGMA table_info(signals)` shows `sl_type` column, `VARCHAR(15)`, DEFAULT `'FIXED'`
2. `SELECT COUNT(*) FROM signals WHERE sl_type IS NULL` returns 0 (both pre-existing via DEFAULT and new via INSERT)
3. Correct classification: FIXED for numeric SL, CONDITIONAL for keyword-detected, NONE for absent, MANUAL for operator UPDATE
4. Backfill: 28 NULL-SL signals → NONE, rest → FIXED (via DEFAULT)
5. Shared `_CONDITIONAL_SL_KEYWORDS` constant used in both notes-tag and sl_type blocks
6. All existing tests pass, INSERT column count = 30 (was 29 after A11)

## Rollback

```sql
ALTER TABLE signals DROP COLUMN sl_type;
```
SQLite 3.46.1 supports DROP COLUMN natively. Revert micro-gate commit. No data loss.
