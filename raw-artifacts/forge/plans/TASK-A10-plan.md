# Task A10: Database Merge (Old + New) — v2

**Source:** Arbiter-Oink Phase 4 V2, Phase A; Phase 0 §data-continuity  
**Tier:** 🔴 CRITICAL — Requires Mike approval before execution  
**Dependencies:** A1 ✅, A2 ✅, A4 ✅, A6 ✅, A8 ✅, A9 ✅, A11 ✅ — all shipped 2026-04-19  
**Production DB:** `/home/m/data/oinkfarm.db` (494+ signals, 52 columns)  
**Old DB:** `/home/m/data/oinkfarm-old.db` (1,165 signals, 49 columns)  
**Codebase Verified At:** 2026-04-19T18:00Z (post-A8 merge `46154543`)  
**Base commits:** oinkfarm `46154543`, oink-sync `e9be741`, signal-gateway `c6cb99e`  
**Plan version:** v2 (revised from v1 per OINKV-AUDIT-WAVE3-A10, addressing 3 CRITICAL + 8 MINOR findings)

---

## 0. Executive Summary

OinkFarm has two databases: the "old" DB (Feb 8 – Apr 9, 1,165 signals) and the "new" DB (Mar 18 – present, 494+ signals). There is a 22-day overlap window (Mar 18 – Apr 9) with 514 signals sharing the same `discord_message_id`. Task A10 merges them into a single unified DB for analytics, trader performance tracking, and historical reporting.

**⚠️ MIKE APPROVAL GATE:** This task modifies production data irreversibly. ANVIL must:
1. Create a verified backup before any merge
2. Run the merge on a COPY first
3. Present validation report to Mike
4. Only deploy to production after Mike's explicit go-ahead

**v2 changes:** Schema aligned to 52 columns (A8 `sl_type` + A11 `leverage_source`), A9 denomination normalization applied to old-DB 1000* tickers, atomic swap via `mv`, PENDING→CANCELLED split, server FK match on `discord_server_id`.

---

## 1. Current State Analysis

### Database Comparison

| Property | Old DB (oinkfarm-old.db) | New DB (oinkfarm.db) |
|----------|--------------------------|----------------------|
| Signals | 1,165 | 494+ (live count at execution time) |
| Columns | 49 (no `remaining_pct`, `leverage_source`, `sl_type`) | 52 (has all three) |
| Date range | 2026-02-08 → 2026-04-09 | 2026-03-18 → present |
| Tables | signals, traders, servers, price_history, audit_log | signals, traders, servers, price_history, signal_events, quarantine + more |
| Status dist | 421 WIN, 317 LOSS, 242 CANCEL, 98 BE, 58 ACTIVE, 23 PENDING, 6 MANUAL | 176 LOSS, 93 WIN, 79 ACTIVE, 69 BE, 57 CANCEL, 11 PENDING, 7 MANUAL, 2 PARTIALLY_CLOSED |

### Overlap Analysis

- **Date overlap window:** 2026-03-18 to 2026-04-09 (22 days)
- **Overlapping discord_message_ids:** 514
- **Old DB signals in overlap window:** 712
- **New DB signals in overlap window:** ~66
- **Old DB unique signals (pre-overlap):** 1,165 - 712 = 453 (Feb 8 – Mar 17)
- **Net new signals from old DB:** ~453 non-overlapping + (712 - 514) = ~651

### Schema Differences (v2 — 3 columns, not 1)

| Column | Old DB | New DB | Merge Action |
|--------|--------|--------|-------------|
| `remaining_pct` (cid 49) | ❌ Missing | ✅ REAL DEFAULT 100.0 | Add with DEFAULT 100.0 for imported signals |
| `leverage_source` (cid 50) | ❌ Missing | ✅ VARCHAR(20) DEFAULT NULL | Add; backfill EXPLICIT where old leverage IS NOT NULL, else NULL |
| `sl_type` (cid 51) | ❌ Missing | ✅ VARCHAR(15) DEFAULT 'FIXED' | Add; backfill per A8 rules: FIXED/CONDITIONAL/NONE |
| `signal_events` table | ❌ Missing | ✅ Present (355+ events) | Do NOT migrate — old DB has no events. Imported rows will have zero events. |
| `quarantine` table | ❌ Missing | ✅ Present | Do NOT migrate |

### A9 Denomination Impact on Old DB

A9 (merged 2026-04-19 16:22Z) normalizes entry_price/stop_loss/TP values for 1000*-denominated tickers at ingestion. The new DB contains only base-ticker rows (e.g., `PEPE` not `1000PEPE`) with normalized prices. The old DB may contain pre-normalization rows where:
- Ticker is `1000PEPE`, `1000FLOKI`, `1000SHIB`, `1000BONK`, etc. — stored at 1000x denomination
- Or ticker is `PEPE` but entry_price is 1000x the current base price

The merge script MUST normalize these before dedup to prevent mixed-scale analytics.

### Stale Signals in Old DB

The old DB has 58 ACTIVE and 23 PENDING signals. These positions were active when the old DB was last used (Apr 9) but are now 10+ days stale:
- **58 ACTIVE** → set to `CLOSED_MANUAL` (positions entered the market but went stale)
- **23 PENDING** → set to `CANCELLED` (limit orders that never filled)

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `scripts/merge_databases.py` | — | CREATE | Standalone merge script with A8/A9/A11 handling |
| `tests/test_db_merge.py` | — | CREATE | Merge validation tests (14 tests) |

### Files NOT Modified

- micro-gate-v3.py — no code changes needed
- lifecycle.py — no code changes needed
- The merge is a one-time data migration, not a code feature

---

## 3. SQL Changes

### 3a. Pre-Merge Schema Alignment (run on copy of old DB)

```sql
-- Add three missing columns to old DB copy (schema alignment to 52 columns)
ALTER TABLE signals ADD COLUMN remaining_pct   REAL        DEFAULT 100.0;
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
ALTER TABLE signals ADD COLUMN sl_type         VARCHAR(15) DEFAULT 'FIXED';
```

### 3b. A11 leverage_source Backfill (on old DB copy)

```sql
-- Signals where leverage was explicitly provided → EXPLICIT
UPDATE signals SET leverage_source = 'EXPLICIT'
  WHERE leverage IS NOT NULL;
-- NULL leverage → leave leverage_source as NULL (provenance unknown for historical data)
```

### 3c. A8 sl_type Backfill (on old DB copy)

```sql
-- Signals with notes containing [SL:CONDITIONAL] → CONDITIONAL
UPDATE signals SET sl_type = 'CONDITIONAL'
  WHERE notes LIKE '%SL:CONDITIONAL%';
-- Signals with NULL stop_loss → NONE
UPDATE signals SET sl_type = 'NONE'
  WHERE stop_loss IS NULL AND sl_type = 'FIXED';
-- All remaining signals keep sl_type = 'FIXED' (the DEFAULT)
```

### 3d. A9 Denomination Normalization (on old DB copy, BEFORE dedup)

```sql
-- Identify 1000*-denominated tickers and normalize prices
-- Divide entry_price, stop_loss, take_profit_1/2/3 by 1000
-- Rename ticker from 1000X to X
-- Append normalization note

UPDATE signals SET
    entry_price   = entry_price / 1000.0,
    stop_loss     = CASE WHEN stop_loss     IS NOT NULL THEN stop_loss / 1000.0     ELSE NULL END,
    take_profit_1 = CASE WHEN take_profit_1 IS NOT NULL THEN take_profit_1 / 1000.0 ELSE NULL END,
    take_profit_2 = CASE WHEN take_profit_2 IS NOT NULL THEN take_profit_2 / 1000.0 ELSE NULL END,
    take_profit_3 = CASE WHEN take_profit_3 IS NOT NULL THEN take_profit_3 / 1000.0 ELSE NULL END,
    exit_price    = CASE WHEN exit_price    IS NOT NULL THEN exit_price / 1000.0    ELSE NULL END,
    fill_price    = CASE WHEN fill_price    IS NOT NULL THEN fill_price / 1000.0    ELSE NULL END,
    opened_price  = CASE WHEN opened_price  IS NOT NULL THEN opened_price / 1000.0  ELSE NULL END,
    ticker = SUBSTR(ticker, 5),  -- Remove '1000' prefix
    notes = COALESCE(notes, '') || ' [A10-merge: denomination_adjusted /1000]'
WHERE ticker LIKE '1000%';
```

**Known 1000* tickers:** 1000PEPEUSDT, 1000SHIBUSDT, 1000BONKUSDT, 1000FLOKIUSDT, 1000RATSUSDT, 1000LUNCUSDT, 1000XECUSDT, 1000SATSUSDT.

**Verification after normalization:**
```sql
-- Must be 0 after normalization
SELECT COUNT(*) FROM signals WHERE ticker LIKE '1000%';
```

### 3e. Stale Signal Override (on old DB copy)

```sql
-- ACTIVE signals → CLOSED_MANUAL (positions entered market but went stale)
UPDATE signals SET
    status = 'CLOSED_MANUAL',
    notes = COALESCE(notes, '') || ' [A10: stale active signal from pre-migration DB, closed at merge time]',
    closed_at = '2026-04-19T00:00:00Z',
    auto_closed = 1,
    close_source = 'db_merge_a10_stale_active'
WHERE status = 'ACTIVE';

-- PENDING signals → CANCELLED (limit orders that never filled)
UPDATE signals SET
    status = 'CANCELLED',
    notes = COALESCE(notes, '') || ' [A10: stale pending signal from pre-migration DB, cancelled at merge time]',
    closed_at = '2026-04-19T00:00:00Z',
    auto_closed = 1,
    close_source = 'db_merge_a10_stale_pending'
WHERE status = 'PENDING';
```

---

## 4. Implementation Notes

### 4a. Merge Algorithm (Python Script)

```
INPUTS:
  old_db = copy of /home/m/data/oinkfarm-old.db
  new_db = copy of /home/m/data/oinkfarm.db

STEP 1: Schema alignment (on old_db copy)
  - Add remaining_pct, leverage_source, sl_type columns (§3a)
  - Backfill leverage_source (§3b)
  - Backfill sl_type (§3c)
  - Apply A9 denomination normalization (§3d)
  - Override stale ACTIVE→CLOSED_MANUAL, PENDING→CANCELLED (§3e)

STEP 2: Trader FK remapping
  - Read all traders from both DBs
  - For each old trader:
    a) If name+server matches a new trader → map old trader_id → new trader_id
    b) If no match → INSERT into new DB traders table → get new trader_id
  - Build trader_id_map: {old_id: new_id}

STEP 3: Server FK remapping
  - Read all servers from both DBs
  - For each old server:
    a) If discord_server_id matches a new server → map old server_id → new server_id
    b) If no match → INSERT into new DB servers table → get new server_id
  - Build server_id_map: {old_id: new_id}
  - NOTE: Match on discord_server_id (natural key), NOT on auto-increment id

STEP 4: Signal dedup + merge
  - Read discord_message_ids from new DB → dedup_set
  - For each signal in old DB:
    a) If discord_message_id IN dedup_set → SKIP (new DB version wins)
    b) Else → INSERT into new DB with remapped trader_id, server_id
       - All 52 columns populated (schema-aligned in STEP 1)
       - Append notes: "[A10: imported from pre-migration DB, original_id=NNN]"

STEP 5: Validation
  - Count signals in merged DB
  - Capture pre-merge count from new DB at script start (not hardcoded)
  - Expected: pre_merge_count + old_unique_count
  - Verify no duplicate discord_message_ids
  - Verify all trader_ids and server_ids are valid FKs
  - Verify status distribution is sane
  - Verify sl_type distribution: FIXED (majority), NONE (where SL was NULL), CONDITIONAL (if notes matched)
  - Verify leverage_source distribution: ~651 new NULL rows (imported), ~98 EXPLICIT (existing)
  - Verify 0 rows with ticker LIKE '1000%'
  - Verify every imported row has sl_type, leverage_source, remaining_pct populated
```

### 4b. ID Handling

**CRITICAL:** Signal IDs will change for imported old signals. The new DB auto-increments from its current max ID. Old signal IDs are preserved in the notes field for traceability:

```
[A10: imported from pre-migration DB, original_id=742]
```

Old signal IDs should NOT be preserved as actual IDs — this would cause conflicts with new DB's auto-increment sequence.

### 4c. What NOT to Merge

- **signal_events:** Old DB doesn't have this table. No events to migrate. Imported rows will have zero events — this is expected and documented. GUARDIAN should be informed to skip event-completeness checks for imported rows (identifiable by `notes LIKE '%A10: imported%'`).
- **quarantine:** Old DB doesn't have this table.
- **price_history:** Could be merged but is LOW priority and HIGH volume. **FORGE recommends: skip price_history merge.** If Mike wants it, plan a separate task.
- **audit_log:** Old DB has this table. Could merge for historical reference. **FORGE recommends: skip for now.** The audit_log schema may differ.

### 4d. Execution Sequence

```
1. Checkpoint WAL on production DB:
   sqlite3 /home/m/data/oinkfarm.db "PRAGMA wal_checkpoint(TRUNCATE);"

2. Create verified backup:
   cp /home/m/data/oinkfarm.db /home/m/data/oinkfarm-backup-pre-a10.db
   sqlite3 /home/m/data/oinkfarm-backup-pre-a10.db "SELECT COUNT(*) FROM signals;"
   md5sum /home/m/data/oinkfarm-backup-pre-a10.db

3. Create test copy:
   cp /home/m/data/oinkfarm.db /home/m/data/oinkfarm-merge-test.db

4. Dry run:
   python3 scripts/merge_databases.py \
     --old /home/m/data/oinkfarm-old.db \
     --target /home/m/data/oinkfarm-merge-test.db \
     --dry-run

5. Execute merge:
   python3 scripts/merge_databases.py \
     --old /home/m/data/oinkfarm-old.db \
     --target /home/m/data/oinkfarm-merge-test.db

6. Validate:
   python3 scripts/validate_merge.py --db /home/m/data/oinkfarm-merge-test.db

7. [MIKE REVIEWS VALIDATION REPORT]

8. Stop services + atomic swap:
   systemctl --user stop oink-sync
   systemctl --user stop micro-gate  # if running as service
   sqlite3 /home/m/data/oinkfarm.db "PRAGMA wal_checkpoint(TRUNCATE);"
   cp /home/m/data/oinkfarm-merge-test.db /home/m/data/oinkfarm.db.new
   sync
   mv -f /home/m/data/oinkfarm.db.new /home/m/data/oinkfarm.db  # atomic rename

9. Verify symlink resolution:
   sqlite3 /home/oinkv/.openclaw/workspace/data/oinkfarm.db "SELECT COUNT(*) FROM signals;"

10. Start services:
    systemctl --user start oink-sync
    systemctl --user start micro-gate

11. Post-deploy validation:
    python3 scripts/validate_merge.py --db /home/m/data/oinkfarm.db
```

### 4e. Backup Verification

Before step 8, verify the backup:
```bash
sqlite3 /home/m/data/oinkfarm-backup-pre-a10.db "SELECT COUNT(*) FROM signals;"
# Must equal pre-merge count (captured at step 2)
md5sum /home/m/data/oinkfarm-backup-pre-a10.db
```

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| test_dedup_overlap | Signal with discord_message_id in both DBs | Only new DB version present in merged DB | unit | MUST |
| test_unique_old_imported | Old signal with unique discord_message_id | Present in merged DB with [A10] note | unit | MUST |
| test_trader_remap | Old signal from trader "Trader_X" | trader_id remapped to new DB's trader_id for Trader_X | unit | MUST |
| test_server_remap_by_discord_id | Old server with discord_server_id="123" | Matched to new server with same discord_server_id, not by auto-inc id | unit | MUST |
| test_stale_active_closed | Old ACTIVE signal | status=CLOSED_MANUAL, close_source=db_merge_a10_stale_active | unit | MUST |
| test_stale_pending_cancelled | Old PENDING signal | status=CANCELLED, close_source=db_merge_a10_stale_pending | unit | MUST |
| test_remaining_pct_default | Imported old signal | remaining_pct=100.0 | unit | MUST |
| test_sl_type_backfill | Imported signal with NULL stop_loss | sl_type='NONE' | unit | MUST |
| test_sl_type_fixed | Imported signal with stop_loss=50.0 | sl_type='FIXED' | unit | MUST |
| test_leverage_source_backfill | Imported signal with leverage=10.0 | leverage_source='EXPLICIT' | unit | MUST |
| test_leverage_source_null | Imported signal with NULL leverage | leverage_source=NULL | unit | MUST |
| test_a9_normalization | Old signal with ticker='1000PEPE', entry=0.008 | ticker='PEPE', entry=0.000008; notes contains 'denomination_adjusted' | unit | MUST |
| test_no_1000_tickers | Full merged DB | 0 rows with ticker LIKE '1000%' | integration | MUST |
| test_no_duplicate_dmids | Full merged DB | 0 duplicate discord_message_ids | integration | MUST |
| test_signal_count | Full merge | count = pre_merge + ~651 (±10) | integration | MUST |
| test_all_fks_valid | Full merged DB | 0 orphan trader_ids, 0 orphan server_ids | integration | MUST |
| test_all_52_columns | Imported old signal | All 52 columns present and populated | integration | MUST |
| test_original_id_in_notes | Imported old signal | notes contains "original_id=NNN" | unit | SHOULD |
| test_dry_run_no_changes | --dry-run flag | Target DB unchanged, report printed | unit | MUST |

---

## 6. Acceptance Criteria

1. **Merged signal count:** pre_merge_count (captured at execution time) + ~651 (unique from old) ≈ 1,145+ signals (±10)
2. **Zero duplicate discord_message_ids** in the merged DB
3. **All trader_ids and server_ids are valid** (no orphan FKs)
4. **Stale ACTIVE → CLOSED_MANUAL** (58 signals, close_source=db_merge_a10_stale_active)
5. **Stale PENDING → CANCELLED** (23 signals, close_source=db_merge_a10_stale_pending)
6. **remaining_pct = 100.0** for all imported old signals
7. **sl_type distribution post-merge:** majority FIXED, ~28+ NONE (where SL was NULL), ≤small number CONDITIONAL (if notes matched)
8. **leverage_source distribution post-merge:** ~651 new NULL rows (imported unknown provenance), ~98 EXPLICIT (existing)
9. **Zero rows with ticker LIKE '1000%'** — all denomination-normalized
10. **All 52 columns present** in every imported row
11. **Notes tag present:** All imported signals have `[A10: imported from pre-migration DB]`
12. **Backup verified** before production deployment
13. **Symlink resolution verified** post-swap
14. **oink-sync restarts cleanly** after merge (no schema errors)

---

## 7. Rollback Plan

1. `systemctl --user stop oink-sync`
2. `systemctl --user stop micro-gate`
3. `sqlite3 /home/m/data/oinkfarm-backup-pre-a10.db "PRAGMA wal_checkpoint(TRUNCATE);"`
4. `cp /home/m/data/oinkfarm-backup-pre-a10.db /home/m/data/oinkfarm.db.rollback`
5. `sync`
6. `mv -f /home/m/data/oinkfarm.db.rollback /home/m/data/oinkfarm.db`
7. `sqlite3 /home/oinkv/.openclaw/workspace/data/oinkfarm.db "SELECT COUNT(*) FROM signals;"` — verify matches pre-merge count
8. `systemctl --user start oink-sync`
9. `systemctl --user start micro-gate`

**Rollback is clean** because we took a verified backup before the merge. Rollback also uses atomic rename.

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| trader_id remapping fails (orphan FKs) | Medium | Broken trader queries | Validation step checks all FKs before production deploy |
| Duplicate discord_message_ids after merge | Low | Dedup logic confused | Explicit dedup in merge script + validation check |
| A9 normalization misses a 1000* variant | Low | Mixed-scale prices for that ticker | Explicit check: 0 rows with ticker LIKE '1000%' post-merge |
| sl_type backfill misclassifies historical signals | Low | Incorrect metadata (not data loss) | Conservative default: FIXED; NONE only where SL truly NULL |
| Production DB locked during oink-sync stop | Low | Missed price updates (~5 min) | Schedule merge during low-activity window |
| Atomic swap fails (disk full) | Very Low | Swap aborted, old DB intact | `sync` + `mv` is atomic on same filesystem; backup available |
| Backup corruption | Very Low | Data loss | md5sum verification + WAL checkpoint before backup |
| Imported rows have zero signal_events | Expected | Event-completeness queries break for historical rows | GUARDIAN informed to filter on `notes LIKE '%A10: imported%'` |

---

## 9. Evidence

**DB queries run (at audit time 2026-04-19T18:00Z):**
```sql
SELECT COUNT(*) FROM signals;                           -- 494
PRAGMA table_info(signals);                             -- 52 columns
SELECT sl_type, COUNT(*) FROM signals GROUP BY sl_type; -- FIXED|466, NONE|28
SELECT leverage_source, COUNT(*)
  FROM signals GROUP BY leverage_source;                -- NULL|396, EXPLICIT|98
SELECT COUNT(*) FROM signal_events;                      -- 355
SELECT COUNT(*) FROM traders;                            -- 99
SELECT COUNT(*) FROM servers;                            -- 11
-- Old DB signal count: 1,165
-- Overlapping discord_message_ids: 514
-- Old DB stale ACTIVE: 58, stale PENDING: 23
-- Old DB date range: 2026-02-08 → 2026-04-09
-- New DB date range: 2026-03-18 → present
```

**Note:** Signal count will drift between plan approval and execution. The merge script captures pre_merge_count at runtime — not hardcoded.

**Tables in old DB:** signals, traders, servers, price_history, audit_log  
**Tables NOT in old DB:** signal_events, quarantine

---

## 10. Mike Approval Gate

**⚠️ This task requires Mike's explicit approval at two points:**

### Gate 1: Plan Approval
Mike approves the merge algorithm, dedup strategy (new DB version wins for overlaps), A9 normalization approach, and stale-signal handling (ACTIVE→CLOSED_MANUAL, PENDING→CANCELLED).

### Gate 2: Execution Approval
After ANVIL runs the merge on a test copy and presents the validation report, Mike reviews:
- Signal count matches expectations
- Status distribution is sane
- sl_type / leverage_source distributions are correct
- No rows with ticker LIKE '1000%'
- Trader remapping is correct
- No data anomalies

Only after Gate 2 does ANVIL deploy to production.

### Questions for Mike

**Q-A10-1:** Should price_history also be merged? It adds historical price data but is high-volume and could slow the merge. FORGE recommends deferring to a separate task.

**Q-A10-2:** Should the old DB's audit_log be merged? It has historical audit entries but the schema may differ. FORGE recommends skipping unless Mike specifically wants it.

**Q-A10-3:** Scheduling — should the merge happen during a quiet period (e.g., Sunday night when fewer signals arrive)? A ~5 min oink-sync + micro-gate downtime is expected.

**Q-A10-4:** Should the merge script synthesize a single `IMPORTED` event per imported row in signal_events for bookkeeping, or leave imported rows with zero events? FORGE recommends leaving zero events (simpler, no false audit trail) with GUARDIAN informed to exclude imported rows from event-completeness checks.

---

*Forge 🔥 — "The merge script is the easy part. The validation is what makes it safe."*
*v2 — revised 2026-04-19T18:07Z per OINKV-AUDIT-WAVE3-A10 (3 CRITICAL + 8 MINOR)*
