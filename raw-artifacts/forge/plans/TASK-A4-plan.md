# Task A.4: PARTIALLY_CLOSED Status for Partial TP Signals

**Source:** Arbiter-Oink Phase 4 §2 (Signal Lifecycle Accuracy), Phase 3 §ADAPT/status-model
**Tier:** 🟡 STANDARD
**Dependencies:** A1 (event_store in oink-sync ✅ shipped), A2 (remaining_pct model ✅ shipped)
**Estimated Effort:** 0.5–1 day
**Plan Version:** 1.0
**Codebase Verified At:** oink-sync `6b21a2074` / signal-gateway `38eb8e879` (2026-04-19)

---

## 0. Executive Summary

After Task A2, `remaining_pct` is correctly decremented on every TP hit. However, the signal `status` field remains `'ACTIVE'` after a partial TP hit — there is no distinction between a brand-new signal and one that has already had some position closed. This causes:

1. **Misleading status** — a signal that has had TP1 hit (25% closed) looks identical to one fresh from INSERT
2. **A7 lookup gap** — the UPDATE→NEW detection task (A7) needs to detect existing positions by status; `PARTIALLY_CLOSED` must be in the set
3. **GUARDIAN/VIGIL scoring** — data integrity dimensions penalize status fields that don't reflect true lifecycle state

This plan adds `status='PARTIALLY_CLOSED'` as the canonical state between first TP hit and final closure. It is **additive only**: no existing status values change, no schema migration is required (the existing CHECK constraint accepts any uppercase string), and rollback is a single SQL UPDATE.

---

## 1. Current State Analysis

### Status Check Constraint (Verified)

```sql
-- PRAGMA table_info(signals) — status column:
-- 24|status|VARCHAR(20)|1||0
-- No explicit CHECK enum in current SQLite schema — the CHECK merely enforces UPPER(status)
-- (per A1 plan: "status VARCHAR(20) NOT NULL CHECK (status = UPPER(status))")
-- 'PARTIALLY_CLOSED' is 15 characters, fully uppercase → passes the CHECK
```

### Current Status Distribution (as of 2026-04-19)

```
ACTIVE          85
CANCELLED       56
CLOSED_BREAKEVEN 68
CLOSED_LOSS     171
CLOSED_MANUAL    7
CLOSED_WIN      92
PENDING         11
```

No `PARTIALLY_CLOSED` rows exist. This is expected — A4 hasn't been implemented.

### Current `_process_tp_hits()` Logic (lifecycle.py lines ~540–665)

```python
def _process_tp_hits(
    self, conn, sig_id, ticker, direction, entry, current,
    sl, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit,
    now, events, *, remaining_pct=None,
):
```

After computing `run_remaining` (A2 logic), the method:
1. Updates `tp{N}_hit_at`, `stop_loss`, and `remaining_pct` in one SQL statement
2. Emits `TP_HIT` and `SL_MODIFIED` events
3. **Does NOT update `status`** — this is the gap this task fills

### `_check_sl_tp()` Main Query (lifecycle.py line 388)

```python
rows = conn.execute(
    "SELECT id, ticker, exchange_ticker, entry_price, direction, leverage, "
    "stop_loss, take_profit_1, take_profit_2, take_profit_3, "
    "tp1_hit_at, tp2_hit_at, tp3_hit_at, fill_status, notes, "
    "posted_at, filled_at, remaining_pct "
    "FROM signals WHERE status='ACTIVE' AND exchange_matched=1 AND exchange_ticker IS NOT NULL"
).fetchall()
```

`PARTIALLY_CLOSED` signals are **not included** in this query — they will stop being monitored after TP1 hit. This must be fixed.

### `_check_limit_fills()` Query (lifecycle.py line ~667)

```python
rows = conn.execute(
    "FROM signals WHERE status='PENDING' AND exchange_matched=1 AND exchange_ticker IS NOT NULL"
)
```

Correctly excludes `PARTIALLY_CLOSED` (already filled). **No change needed here.**

### `calculate_blended_pnl()` Function (lifecycle.py lines ~117–200)

Accepts `remaining_pct` as a parameter. Already handles partial-close signals correctly — the value is read from the DB, not derived from status. **No changes needed in PnL calculation.**

### Closure Path in `_check_sl_tp()` (lifecycle.py line ~481)

```python
"WHERE id=? AND status='ACTIVE' AND fill_status='FILLED'",
```

The `UPDATE signals SET status=?...` closure query has `AND status='ACTIVE'` guard. This will **silently skip closing `PARTIALLY_CLOSED` signals** via SL. Must be updated.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `oink-sync/oink_sync/lifecycle.py` | `_process_tp_hits()` | MODIFY | After remaining_pct update, if `0 < run_remaining < 100`, add status UPDATE to `'PARTIALLY_CLOSED'` in the same SQL statement |
| `oink-sync/oink_sync/lifecycle.py` | `_check_sl_tp()` — main query | MODIFY | Change `WHERE status='ACTIVE'` to `WHERE status IN ('ACTIVE','PARTIALLY_CLOSED')` |
| `oink-sync/oink_sync/lifecycle.py` | `_check_sl_tp()` — closure UPDATE guard | MODIFY | Change `AND status='ACTIVE'` to `AND status IN ('ACTIVE','PARTIALLY_CLOSED')` in the UPDATE statement |
| `oink-sync/oink_sync/lifecycle.py` | `_check_sl_tp()` — closure | MODIFY | Emit `STATUS_CHANGED` event after status transition to `PARTIALLY_CLOSED` |
| `oink-sync/tests/test_partially_closed.py` | — | CREATE | Unit + integration tests for PARTIALLY_CLOSED lifecycle |

---

## 3. SQL Changes

### 3a. No Schema Migration Required

The `signals.status` column is `VARCHAR(20) NOT NULL` with a CHECK that enforces `status = UPPER(status)`. The string `'PARTIALLY_CLOSED'` is 15 characters and fully uppercase — it satisfies this constraint without any DDL changes.

```sql
-- Verification query (run before/after implementation):
SELECT COUNT(*) FROM signals WHERE status='PARTIALLY_CLOSED';
-- Expected pre-implementation: 0
-- Expected post-implementation (after first TP hit in production): >= 1
```

### 3b. Rollback SQL (if needed)

```sql
-- Emergency rollback: revert PARTIALLY_CLOSED → ACTIVE
UPDATE signals SET status='ACTIVE' WHERE status='PARTIALLY_CLOSED';
-- Then redeploy pre-A4 code
```

### 3c. Evidence: No Ambiguity in Status Transition

```sql
-- A PARTIALLY_CLOSED signal has:
--   remaining_pct > 0.0 AND remaining_pct < 100.0
--   AND (tp1_hit_at IS NOT NULL OR tp2_hit_at IS NOT NULL)
-- This is mutually exclusive with pure ACTIVE (remaining_pct = 100.0)

SELECT id, status, remaining_pct, tp1_hit_at, tp2_hit_at, tp3_hit_at
FROM signals
WHERE status='ACTIVE' AND remaining_pct < 100.0 AND remaining_pct > 0.0;
-- Expected pre-A4: 0 rows (A2 sets remaining_pct but doesn't flip status)
-- If any rows exist here, they are candidates for backfill to PARTIALLY_CLOSED
```

---

## 4. Implementation Notes

### 4a. Status Transition Rules

| Condition | Status |
|-----------|--------|
| `remaining_pct = 100.0` and no TP hit | `ACTIVE` |
| `0 < remaining_pct < 100.0` and ≥1 TP hit | `PARTIALLY_CLOSED` |
| `remaining_pct = 0.0` | Final close status (`CLOSED_WIN`/`CLOSED_LOSS`/`CLOSED_BREAKEVEN`) |
| SL hit (any remaining_pct) | Final close status |

### 4b. The UPDATE Statement in `_process_tp_hits()`

Currently (A2 shipped code, lines ~604–612):

```python
if run_remaining is not None:
    conn.execute(
        f"UPDATE signals SET {hit_col}=?, stop_loss=?, "
        f"remaining_pct=?, updated_at=? WHERE id=?",
        (now, new_sl, run_remaining, now, sig_id),
    )
else:
    conn.execute(
        f"UPDATE signals SET {hit_col}=?, stop_loss=?, updated_at=? WHERE id=?",
        (now, new_sl, now, sig_id),
    )
```

**A4 change (pseudocode — ANVIL implements):**

After the UPDATE, check `run_remaining`:
- If `0 < run_remaining < 100`: issue a **separate** `UPDATE signals SET status='PARTIALLY_CLOSED' WHERE id=? AND status='ACTIVE'`
  - Use a separate statement (or merge into the above) to flip status
  - Only flip from `ACTIVE → PARTIALLY_CLOSED`, not from any final closed state
  - Emit `STATUS_CHANGED` event after the flip

**ANVIL decision:** Whether to merge the status column into the same UPDATE statement (cleaner, single round-trip) or keep it separate (easier to see the logic). Either is acceptable; FORGE recommends merging for atomicity.

### 4c. The Closure Guard Fix

Current closure path (lifecycle.py ~line 481):

```python
cur = conn.execute(
    "UPDATE signals SET status=?, exit_price=?, final_roi=?, is_win=?, "
    "closed_at=?, close_source=?, auto_closed=1, current_price=?, "
    "pnl_percent=?, last_price_update=?, updated_at=?, hold_hours=? "
    "WHERE id=? AND status='ACTIVE' AND fill_status='FILLED'",
    ...
)
```

The `AND status='ACTIVE'` guard prevents `PARTIALLY_CLOSED` signals from being closed via SL. Must be changed to:

```sql
WHERE id=? AND status IN ('ACTIVE','PARTIALLY_CLOSED') AND fill_status='FILLED'
```

### 4d. STATUS_CHANGED Event Payload

Emit via the existing `self._log_event()` mechanism:

```python
{
    "event_type": "STATUS_CHANGED",
    "payload": {
        "old_status": "ACTIVE",
        "new_status": "PARTIALLY_CLOSED",
        "trigger": "tp_hit",
        "tp_level": tp_idx,
        "remaining_pct": run_remaining,
        "ticker": ticker,
        "direction": direction
    },
    "field": "status",
    "old_value": "ACTIVE",
    "new_value": "PARTIALLY_CLOSED"
}
```

### 4e. Pre-A4 Signal Backfill

Signals created before A4 with `remaining_pct < 100.0` will remain `ACTIVE`. These are rare (A2 only shipped on 2026-04-19), but a one-time backfill should be included in the deployment:

```sql
-- One-time backfill at deployment (run BEFORE deploying A4 code):
UPDATE signals
SET status='PARTIALLY_CLOSED'
WHERE status='ACTIVE'
  AND remaining_pct IS NOT NULL
  AND remaining_pct > 0.0
  AND remaining_pct < 100.0;
-- Expected rows affected: 0 (A2 hasn't been running long enough)
-- If > 0: confirm with Mike before proceeding
```

### 4f. `_check_sl_tp()` Query Broadening

The main monitoring query change is critical — without it, `PARTIALLY_CLOSED` signals will be orphaned and never receive further SL/TP monitoring. This is the highest-risk change in the plan.

Current (line 388–389):
```sql
FROM signals WHERE status='ACTIVE' AND exchange_matched=1 AND exchange_ticker IS NOT NULL
```

Must become:
```sql
FROM signals WHERE status IN ('ACTIVE','PARTIALLY_CLOSED') AND exchange_matched=1 AND exchange_ticker IS NOT NULL
```

---

## 5. Test Specification

All tests should be added to `oink-sync/tests/test_partially_closed.py` using the same DB fixture pattern as `test_remaining_pct.py`.

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_tp1_hit_sets_partially_closed` | Signal with TP1/TP2 defined, current price = TP1. Run `_check_sl_tp()`. | `status='PARTIALLY_CLOSED'`, `remaining_pct=75.0` (25% closed on TP1 of 2-TP signal) | integration | MUST |
| `test_tp2_hit_on_partially_closed_signal` | Signal already in `PARTIALLY_CLOSED` (remaining_pct=75.0). Current price = TP2. Run `_check_sl_tp()`. | `status='PARTIALLY_CLOSED'`, `remaining_pct=25.0` (second tier closed) | integration | MUST |
| `test_sl_hit_closes_partially_closed_signal` | Signal in `PARTIALLY_CLOSED` (remaining_pct=75.0). Current price <= SL. Run `_check_sl_tp()`. | `status='CLOSED_LOSS'` (or `CLOSED_WIN` if SL trailed past BE), `final_roi` computed | integration | MUST |
| `test_tp3_hit_closes_fully_when_remaining_zero` | Signal with 3 TPs, all hit sequentially (remaining_pct=0.0 after TP3). Run `_check_sl_tp()`. | `status='CLOSED_WIN'`, `remaining_pct=0.0`, all 3 `tp{n}_hit_at` set | integration | MUST |
| `test_status_changed_event_emitted` | Signal transitions ACTIVE→PARTIALLY_CLOSED via TP1 hit. | `signal_events` has 1 `STATUS_CHANGED` row with `old_value='ACTIVE'`, `new_value='PARTIALLY_CLOSED'` | integration | MUST |
| `test_partially_closed_monitored_in_next_cycle` | Signal in `PARTIALLY_CLOSED`. Run `_check_sl_tp()` with price not at any threshold. | `_check_sl_tp()` includes the signal in its row scan (query returns it) | unit | MUST |
| `test_active_only_signal_unchanged` | Signal with no TPs defined or price not at TP. Run `_check_sl_tp()`. | `status='ACTIVE'` unchanged | regression | MUST |
| `test_limit_fills_ignores_partially_closed` | Signal in `PARTIALLY_CLOSED`. Run `_check_limit_fills()`. | Signal not included in fill check query (already filled) | unit | MUST |
| `test_calculate_blended_pnl_unaffected` | Call `calculate_blended_pnl()` with `remaining_pct=75.0` (A2 path). | Returns same value regardless of status field (PnL logic unchanged) | unit | SHOULD |
| `test_backfill_query_correctness` | Insert signal with `remaining_pct=60.0, status='ACTIVE'`. Run backfill SQL. | `status='PARTIALLY_CLOSED'` | unit | SHOULD |

---

## 6. Acceptance Criteria

1. **Status transitions:** After any TP hit where `remaining_pct` drops below 100 but stays > 0, the signal's `status` in DB is `'PARTIALLY_CLOSED'`
2. **Continued monitoring:** `PARTIALLY_CLOSED` signals are included in `_check_sl_tp()` monitoring cycles (verified by query inspection or integration test)
3. **SL closure works:** A `PARTIALLY_CLOSED` signal that hits its SL is closed (status = `CLOSED_WIN`/`CLOSED_LOSS`/`CLOSED_BREAKEVEN`) with correct `final_roi` using blended PnL
4. **EVENT_CHANGED event:** Every `ACTIVE → PARTIALLY_CLOSED` transition produces a `STATUS_CHANGED` event in `signal_events`
5. **No existing status regressions:** `SELECT COUNT(*) FROM signals WHERE status NOT IN ('ACTIVE','PENDING','PARTIALLY_CLOSED','CLOSED_WIN','CLOSED_LOSS','CLOSED_BREAKEVEN','CLOSED_MANUAL','CANCELLED')` returns 0
6. **All existing tests pass:** `test_remaining_pct.py`, `test_lifecycle_events.py`, and all 6 signal-gateway tests pass without modification

---

## 7. Rollback Plan

1. **Revert code:** `git revert <A4-commit-hash>` in oink-sync repo
2. **Revert status in production DB:**
   ```sql
   UPDATE signals SET status='ACTIVE' WHERE status='PARTIALLY_CLOSED';
   ```
   This is safe — PARTIALLY_CLOSED signals are still being monitored at SL level, so setting them ACTIVE restores full monitoring without data loss
3. **Restart service:** `systemctl --user restart oink-sync`
4. **Verify rollback:**
   ```sql
   SELECT COUNT(*) FROM signals WHERE status='PARTIALLY_CLOSED';
   -- Expected: 0
   SELECT COUNT(*) FROM signals WHERE status='ACTIVE';
   -- Should include all previously PARTIALLY_CLOSED signals
   ```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| PARTIALLY_CLOSED signals not included in `_check_sl_tp()` query (missed fix) | Low | HIGH — signals stop being monitored | Include `test_partially_closed_monitored_in_next_cycle` as MUST-PASS before merge |
| Closure UPDATE guard not updated — SL never fires for PARTIALLY_CLOSED | Medium | HIGH — signals orphaned at SL hit | Integration test `test_sl_hit_closes_partially_closed_signal` covers this; VIGIL must verify |
| STATUS_CHANGED emitted multiple times for same transition (if cycle runs twice) | Low | Low — duplicate events, no data change | The UPDATE uses `AND status='ACTIVE'` guard — rowcount=0 on second attempt means no duplicate |
| Backfill converts signals that are actually done (remaining_pct=0.0 edge) | Very low | Low | Backfill SQL explicitly excludes `remaining_pct=0.0` |
| Pre-A4 signals with remaining_pct=NULL incorrectly handled | Very low | None | `0 < remaining_pct < 100` check requires non-NULL — NULL values pass through unchanged |

---

## 9. Evidence

**Files read:**
- `/home/oinkv/oink-sync/oink_sync/lifecycle.py` (commit `6b21a207`, lines 117–665 full read of relevant sections)
- `/home/oinkv/oink-sync/tests/test_remaining_pct.py` (patterns and fixtures reviewed)
- `/home/oinkv/oink-sync/tests/test_lifecycle_events.py` (A1 test patterns)

**Database queries run:**
```sql
-- Status distribution
SELECT status, COUNT(*) FROM signals GROUP BY status;
-- ACTIVE: 85, PENDING: 11, CLOSED_WIN: 92, CLOSED_LOSS: 171, CLOSED_BREAKEVEN: 68, CLOSED_MANUAL: 7, CANCELLED: 56

-- Check for pre-A4 partial signals (candidates for backfill)
SELECT COUNT(*) FROM signals WHERE status='ACTIVE' AND remaining_pct > 0.0 AND remaining_pct < 100.0;
-- Result: 0 (A2 shipped 2026-04-19, no partial signals yet)

-- Schema verification
PRAGMA table_info(signals);
-- status: VARCHAR(20) NOT NULL, no explicit enum constraint
-- remaining_pct: REAL DEFAULT 100.0
```

**Git commits reviewed:**
- `6b21a207` — oink-sync HEAD (post-A2): `_process_tp_hits()` updates `remaining_pct` but not `status`
- `38eb8e87` — signal-gateway HEAD: `_match_active()` queries `status IN ('ACTIVE','PENDING')` — will need updating in A7 to include `PARTIALLY_CLOSED`

---

## 10. Design Questions for Mike

### DQ-A4-1: STATUS_CHANGED event type in LIFECYCLE_EVENTS set

The `EventStore.LIFECYCLE_EVENTS` set (in `oink_sync/event_store.py`) currently lists the valid event types. `STATUS_CHANGED` may already be in this set (from A1 instrumentation) — if not, ANVIL must add it before emitting it.

**ANVIL action:** Check `LIFECYCLE_EVENTS` in `oink_sync/event_store.py` for `'STATUS_CHANGED'`. If missing, add it.

### DQ-A4-2: Remaining_pct=0.0 via TP hit — PARTIALLY_CLOSED or close immediately?

If all TPs are hit in one cycle (e.g., gap-past-all-TPs), `remaining_pct` will be 0.0. Should the signal transition to `PARTIALLY_CLOSED` (with remaining_pct=0.0) and then close on the next cycle, or should it close immediately within the same cycle?

**FORGE recommendation:** Close immediately when `remaining_pct=0.0` — this avoids a one-cycle limbo state and is consistent with the intent of "fully closed via TPs". Set status to `CLOSED_WIN` directly, not `PARTIALLY_CLOSED`.
