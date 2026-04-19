# Task A10: Database Merge (Old + New)

**Source:** Arbiter-Oink Phase 4 V2, Phase A; Phase 0 §data-continuity  
**Tier:** 🔴 CRITICAL — Requires Mike approval before execution  
**Dependencies:** A1 (signal_events — shipped), A2 (remaining_pct — shipped), A4 (PARTIALLY_CLOSED — shipped)  
**Production DB:** `/home/m/data/oinkfarm.db` (493 signals, 50 columns)  
**Old DB:** `/home/m/data/oinkfarm-old.db` (1,165 signals, 49 columns)  
**Codebase Verified At:** 2026-04-19

---

## 0. Executive Summary

OinkFarm has two databases: the "old" DB (Feb 8 – Apr 9, 1,165 signals) and the "new" DB (Mar 18 – present, 493 signals). There is a 22-day overlap window (Mar 18 – Apr 9) with 514 signals sharing the same `discord_message_id`. Task A10 merges them into a single unified DB for analytics, trader performance tracking, and historical reporting.

**⚠️ MIKE APPROVAL GATE:** This task modifies production data irreversibly. ANVIL must:
1. Create a verified backup before any merge
2. Run the merge on a COPY first
3. Present validation report to Mike
4. Only deploy to production after Mike's explicit go-ahead

---

## 1. Current State Analysis

### Database Comparison

| Property | Old DB (oinkfarm-old.db) | New DB (oinkfarm.db) |
|----------|--------------------------|----------------------|
| Signals | 1,165 | 493 |
| Columns | 49 (no `remaining_pct`) | 50 (has `remaining_pct`) |
| Date range | 2026-02-08 → 2026-04-09 | 2026-03-18 → present |
| Tables | signals, traders, servers, price_history, audit_log | signals, traders, servers, price_history, signal_events, quarantine + more |
| Status dist | 421 WIN, 317 LOSS, 242 CANCEL, 98 BE, 58 ACTIVE, 23 PENDING, 6 MANUAL | 171 LOSS, 92 WIN, 85 ACTIVE, 68 BE, 56 CANCEL, 11 PENDING, 7 MANUAL |

### Overlap Analysis

- **Date overlap window:** 2026-03-18 to 2026-04-09 (22 days)
- **Overlapping discord_message_ids:** 514
- **Old DB signals in overlap window:** 712
- **New DB signals in overlap window:** ~66
- **Old DB unique signals (pre-overlap):** 1,165 - 712 = 453 (Feb 8 – Mar 17)
- **Net new signals from old DB:** ~453 non-overlapping + (712 - 514) = ~651

### Schema Differences

| Column | Old DB | New DB | Merge Action |
|--------|--------|--------|-------------|
| remaining_pct | ❌ Missing | ✅ REAL DEFAULT 100.0 | Add with DEFAULT 100.0 for old signals |
| signal_events table | ❌ Missing | ✅ Present | Do not migrate (no events to migrate) |
| quarantine table | ❌ Missing | ✅ Present | Do not migrate |

### Stale Signals in Old DB

The old DB has 58 ACTIVE and 23 PENDING signals. These positions were active when the old DB was last used (Apr 9) but are now 10+ days stale. They should NOT be imported as ACTIVE/PENDING.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `scripts/merge_databases.py` | — | CREATE | Standalone merge script |
| `tests/test_db_merge.py` | — | CREATE | Merge validation tests |

### Files NOT Modified

- micro-gate-v3.py — no code changes needed
- lifecycle.py — no code changes needed
- The merge is a one-time data migration, not a code feature

---

## 3. SQL Changes

### Pre-Merge Schema Alignment (run on copy of old DB)

```sql
-- Add remaining_pct column to old DB copy (for schema alignment)
ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0;
```

### Stale Signal Override

```sql
-- Mark stale ACTIVE/PENDING signals in old DB
UPDATE signals SET
    status = 'CLOSED_MANUAL',
    notes = COALESCE(notes, '') || ' [A10: stale signal from pre-migration DB, closed at merge time]',
    closed_at = '2026-04-19T00:00:00Z',
    auto_closed = 1,
    close_source = 'db_merge_a10'
WHERE status IN ('ACTIVE', 'PENDING');
```

---

## 4. Implementation Notes

### 4a. Merge Algorithm (Python Script)

```
INPUTS:
  old_db = copy of /home/m/data/oinkfarm-old.db
  new_db = copy of /home/m/data/oinkfarm.db

STEP 1: Schema alignment
  - Add remaining_pct to old_db copy
  - Close stale ACTIVE/PENDING in old_db copy

STEP 2: Trader FK remapping
  - Read all traders from both DBs
  - For each old trader:
    a) If name+server matches a new trader → map old trader_id → new trader_id
    b) If no match → INSERT into new DB traders table → get new trader_id
  - Build trader_id_map: {old_id: new_id}

STEP 3: Server FK remapping
  - Read all servers from both DBs
  - For each old server:
    a) If server_id matches → keep
    b) If no match → INSERT into new DB servers table
  - Build server_id_map: {old_id: new_id}

STEP 4: Signal dedup + merge
  - Read discord_message_ids from new DB → dedup_set
  - For each signal in old DB:
    a) If discord_message_id IN dedup_set → SKIP (new DB version wins)
    b) Else → INSERT into new DB with remapped trader_id, server_id
       - Set remaining_pct = 100.0
       - Append notes: "[A10: imported from pre-migration DB]"
       - Preserve original id in notes for traceability

STEP 5: Validation
  - Count signals in merged DB
  - Expected: new_count + old_unique_count
  - Verify no duplicate discord_message_ids
  - Verify all trader_ids and server_ids are valid FKs
  - Verify status distribution is sane
```

### 4b. ID Handling

**CRITICAL:** Signal IDs will change for imported old signals. The new DB auto-increments from its current max ID. Old signal IDs are preserved in the notes field for traceability:

```
[A10: imported from pre-migration DB, original_id=742]
```

Old signal IDs should NOT be preserved as actual IDs — this would cause conflicts with new DB's auto-increment sequence.

### 4c. What NOT to Merge

- **signal_events:** Old DB doesn't have this table. No events to migrate.
- **quarantine:** Old DB doesn't have this table.
- **price_history:** Could be merged but is LOW priority and HIGH volume. **FORGE recommends: skip price_history merge.** If Mike wants it, plan a separate task.
- **audit_log:** Old DB has this table. Could merge for historical reference. **FORGE recommends: skip for now.** The audit_log schema may differ.

### 4d. Execution Sequence

```
1. cp /home/m/data/oinkfarm.db /home/m/data/oinkfarm-backup-pre-a10.db
2. cp /home/m/data/oinkfarm.db /home/m/data/oinkfarm-merge-test.db
3. python3 scripts/merge_databases.py \
     --old /home/m/data/oinkfarm-old.db \
     --target /home/m/data/oinkfarm-merge-test.db \
     --dry-run
4. python3 scripts/merge_databases.py \
     --old /home/m/data/oinkfarm-old.db \
     --target /home/m/data/oinkfarm-merge-test.db
5. python3 scripts/validate_merge.py --db /home/m/data/oinkfarm-merge-test.db
6. [MIKE REVIEWS VALIDATION REPORT]
7. systemctl --user stop oink-sync
8. cp /home/m/data/oinkfarm-merge-test.db /home/m/data/oinkfarm.db
9. systemctl --user start oink-sync
10. python3 scripts/validate_merge.py --db /home/m/data/oinkfarm.db
```

### 4e. Backup Verification

Before step 8, verify the backup:
```bash
sqlite3 /home/m/data/oinkfarm-backup-pre-a10.db "SELECT COUNT(*) FROM signals;"
# Must equal 493 (current count)
md5sum /home/m/data/oinkfarm-backup-pre-a10.db
```

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| test_dedup_overlap | Signal with discord_message_id in both DBs | Only new DB version present in merged DB | unit | MUST |
| test_unique_old_imported | Old signal with unique discord_message_id | Present in merged DB with [A10] note | unit | MUST |
| test_trader_remap | Old signal from trader "Trader_X" | trader_id remapped to new DB's trader_id for Trader_X | unit | MUST |
| test_stale_signals_closed | Old ACTIVE signal | status=CLOSED_MANUAL, close_source=db_merge_a10 | unit | MUST |
| test_remaining_pct_default | Imported old signal | remaining_pct=100.0 | unit | MUST |
| test_no_duplicate_dmids | Full merged DB | 0 duplicate discord_message_ids | integration | MUST |
| test_signal_count | Full merge | count = 493 + ~651 ≈ 1,144 (±10) | integration | MUST |
| test_all_fks_valid | Full merged DB | 0 orphan trader_ids, 0 orphan server_ids | integration | MUST |
| test_original_id_in_notes | Imported old signal | notes contains "original_id=NNN" | unit | SHOULD |
| test_dry_run_no_changes | --dry-run flag | Target DB unchanged, report printed | unit | MUST |

---

## 6. Acceptance Criteria

1. **Merged signal count:** 493 (existing) + ~651 (unique from old) ≈ 1,144 signals (±10)
2. **Zero duplicate discord_message_ids** in the merged DB
3. **All trader_ids and server_ids are valid** (no orphan FKs)
4. **No stale ACTIVE/PENDING signals** from old DB (all converted to CLOSED_MANUAL)
5. **remaining_pct = 100.0** for all imported old signals
6. **Notes tag present:** All imported signals have `[A10: imported from pre-migration DB]`
7. **Backup verified** before production deployment
8. **oink-sync restarts cleanly** after merge (no schema errors)

---

## 7. Rollback Plan

1. `systemctl --user stop oink-sync`
2. `cp /home/m/data/oinkfarm-backup-pre-a10.db /home/m/data/oinkfarm.db`
3. `systemctl --user start oink-sync`
4. Verify: `sqlite3 /home/m/data/oinkfarm.db "SELECT COUNT(*) FROM signals;"` → 493

**Rollback is clean** because we took a verified backup before the merge.

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| trader_id remapping fails (orphan FKs) | Medium | Broken trader queries | Validation step checks all FKs before production deploy |
| Duplicate discord_message_ids after merge | Low | Dedup logic confused | Explicit dedup in merge script + validation check |
| Production DB locked during oink-sync stop | Low | Missed price updates (~5 min) | Schedule merge during low-activity window |
| Backup corruption | Very Low | Data loss | md5sum verification before merge |
| Old DB has schema drift not detected | Low | Merge script errors | Dry-run catches schema mismatches |

---

## 9. Evidence

**DB queries run:**
```sql
-- Old DB signal count: 1,165
-- New DB signal count: 493
-- Overlapping discord_message_ids: 514
-- Old DB columns: 49 (no remaining_pct)
-- New DB columns: 50 (has remaining_pct)
-- Old DB stale ACTIVE: 58, stale PENDING: 23
-- Old DB date range: 2026-02-08 → 2026-04-09
-- New DB date range: 2026-03-18 → present
```

**Tables in old DB:** signals, traders, servers, price_history, audit_log  
**Tables NOT in old DB:** signal_events, quarantine

---

## 10. Mike Approval Gate

**⚠️ This task requires Mike's explicit approval at two points:**

### Gate 1: Plan Approval
Mike approves the merge algorithm and dedup strategy (new DB version wins for overlaps).

### Gate 2: Execution Approval
After ANVIL runs the merge on a test copy and presents the validation report, Mike reviews:
- Signal count matches expectations
- Status distribution is sane
- Trader remapping is correct
- No data anomalies

Only after Gate 2 does ANVIL deploy to production.

### Questions for Mike

**Q-A10-1:** Should price_history also be merged? It adds historical price data but is high-volume and could slow the merge. FORGE recommends deferring to a separate task.

**Q-A10-2:** Should the old DB's audit_log be merged? It has historical audit entries but the schema may differ. FORGE recommends skipping unless Mike specifically wants it.

**Q-A10-3:** Scheduling — should the merge happen during a quiet period (e.g., Sunday night when fewer signals arrive)? A ~5 min oink-sync downtime is expected.

---

*Forge 🔥 — "The merge script is the easy part. The validation is what makes it safe."*
