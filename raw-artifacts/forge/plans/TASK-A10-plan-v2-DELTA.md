# TASK-A10-plan v1 → v2 Delta

**Revised:** 2026-04-19T18:07Z  
**Audit:** OINKV-AUDIT-WAVE3-A10 (3 CRITICAL + 8 MINOR findings)  
**Base commit updated:** `46154543` (post-A8 merge)

---

## 🔴 CRITICAL Fixes (3/3 addressed)

### CRITICAL-A10-1: Schema model updated 50 → 52 columns

**v1:** Plan assumed 50 columns (only `remaining_pct` missing from old DB).  
**v2:** Schema correctly reflects 52 columns. Three ALTER TABLE statements in §3a (was 1):
- `remaining_pct REAL DEFAULT 100.0` (already in v1)
- `leverage_source VARCHAR(20) DEFAULT NULL` ← **NEW** (A11, merged 16:51Z)
- `sl_type VARCHAR(15) DEFAULT 'FIXED'` ← **NEW** (A8, merged 17:27Z)

Added §3b (A11 leverage_source backfill) and §3c (A8 sl_type backfill) with semantically correct classification:
- `leverage_source = 'EXPLICIT'` where old leverage IS NOT NULL
- `sl_type = 'NONE'` where stop_loss IS NULL
- `sl_type = 'CONDITIONAL'` where notes contain [SL:CONDITIONAL]

### CRITICAL-A10-2: A9 denomination normalization added

**v1:** No mention of A9 or 1000*-denominated tickers.  
**v2:** New §3d applies denomination normalization to old-DB copy BEFORE dedup:
- Divides entry_price, stop_loss, TP1/2/3, exit_price, fill_price, opened_price by 1000
- Strips `1000` prefix from ticker name
- Appends `[A10-merge: denomination_adjusted /1000]` to notes
- Verifies 0 rows with `ticker LIKE '1000%'` post-normalization

Affected tickers: 1000PEPEUSDT, 1000SHIBUSDT, 1000BONKUSDT, 1000FLOKIUSDT, 1000RATSUSDT, 1000LUNCUSDT, 1000XECUSDT, 1000SATSUSDT.

### CRITICAL-A10-3: Atomic swap replaces `cp`

**v1:** Step 8 used `cp merged.db oinkfarm.db` — non-atomic, torn-write risk.  
**v2:** Step 8 now uses:
1. `PRAGMA wal_checkpoint(TRUNCATE)` on production DB
2. `cp` to `.db.new` sibling
3. `sync`
4. `mv -f .db.new .db` — atomic rename on same filesystem
5. Verify symlink resolution

Rollback procedure also updated to use atomic `mv`.

---

## 🟡 MINOR Fixes (8/8 addressed)

### MINOR-A10-1: PENDING → CANCELLED (not CLOSED_MANUAL)

**v1:** All stale signals (ACTIVE + PENDING) → CLOSED_MANUAL.  
**v2:** Split into two UPDATEs:
- 58 ACTIVE → `CLOSED_MANUAL` (close_source=`db_merge_a10_stale_active`)
- 23 PENDING → `CANCELLED` (close_source=`db_merge_a10_stale_pending`)

### MINOR-A10-2: Server FK match on discord_server_id

**v1:** §4a STEP 3 matched on `server_id` (auto-increment — could cause cross-DB collision).  
**v2:** Explicitly states match on `discord_server_id` (natural key, UNIQUE constraint).

### MINOR-A10-3: Signal count parameterized

**v1:** Hardcoded "493" throughout.  
**v2:** Uses "494+" with note that merge script captures `pre_merge_count` at runtime. Acceptance criteria reference runtime count, not hardcoded value.

### MINOR-A10-4: Test coverage for A8/A11/A9

**v1:** 10 tests, none covering sl_type, leverage_source, or A9 normalization.  
**v2:** 19 tests. Added:
- `test_sl_type_backfill` (NULL SL → NONE)
- `test_sl_type_fixed` (has SL → FIXED)
- `test_leverage_source_backfill` (has leverage → EXPLICIT)
- `test_leverage_source_null` (NULL leverage → NULL)
- `test_a9_normalization` (1000PEPE → PEPE with /1000 prices)
- `test_no_1000_tickers` (0 rows with 1000% ticker)
- `test_all_52_columns` (all columns populated)
- `test_server_remap_by_discord_id`
- `test_stale_pending_cancelled` (split from test_stale_signals_closed)

### MINOR-A10-5: Dependencies updated

**v1:** "A1, A2, A4 (shipped)"  
**v2:** "A1 ✅, A2 ✅, A4 ✅, A6 ✅, A8 ✅, A9 ✅, A11 ✅ — all shipped 2026-04-19"

### MINOR-A10-6: signal_events handling explicit

**v1:** §4c mentioned not migrating signal_events but didn't discuss zero-event implications.  
**v2:** §4c explicitly states imported rows will have zero events. §8 Risk Assessment documents this as expected. GUARDIAN informed to filter imported rows from event-completeness checks. New Q-A10-4 asks Mike whether to synthesize IMPORTED events.

### MINOR-A10-7: WAL checkpoint in backup protocol

**v1:** No WAL checkpoint before backup or swap.  
**v2:** Step 1 checkpoints WAL before backup. Step 8 checkpoints WAL before swap. Rollback procedure also checkpoints.

### MINOR-A10-8: close_source values disambiguated

**v1:** Single `close_source='db_merge_a10'` for all stale signals.  
**v2:** Split into `db_merge_a10_stale_active` and `db_merge_a10_stale_pending` for post-merge audit clarity.

---

## Unchanged (Confirmed Correct in Audit)

- ✅ Row-count arithmetic (1,165 + 493 − 514 = 1,144)
- ✅ Dedup policy (new DB wins on discord_message_id collision)
- ✅ Rollback plan structure (stop → restore backup → start)
- ✅ "What NOT to Merge" decisions (skip price_history, audit_log)
- ✅ Mike two-gate approval structure
- ✅ FK remapping approach (trader: name+server match; server: natural key match)
- ✅ ID handling (new auto-increment, old ID in notes)

---

## New Mike Decision: Q-A10-4

Should the merge script synthesize a single `IMPORTED` event per imported row in signal_events? FORGE recommends NO (simpler, no false audit trail) with GUARDIAN filtering.

---

*Forge 🔥 — v2 delta complete. All 11 audit findings addressed.*
