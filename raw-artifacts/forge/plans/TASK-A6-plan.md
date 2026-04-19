# Task A.6: Ghost Closure Confirmation Flag

**Source:** Arbiter-Oink Phase 4 §2 (Signal Lifecycle Accuracy), Phase 5 §BS-3 (Ghost Closure Auditing)
**Tier:** 🟡 STANDARD
**Dependencies:** A1 (event_store ✅ shipped), A4 (PARTIALLY_CLOSED ✅ shipped), A5 (parser confidence ✅ shipped)
**Estimated Effort:** 0.5 day
**Plan Version:** 1.0
**Codebase Verified At:** signal-gateway `38eb8e879` / oink-sync `ab5d941` / micro-gate `69d6840a` (2026-04-19)

---

## 0. Executive Summary

The reconciler (`reconciler.py`) already detects ghost closures: when a position disappears from the board for `absent_count >= absent_threshold` (default: 3 snapshots), it emits a `CLOSE` action with `source='board_absent'` and `soft_close=True`. However, this action currently flows only to the notification queue (`_queue_reconciler_action_notification()`) — it triggers a Telegram alert to the operator but:

1. **No GHOST_CLOSURE event is written** to `signal_events`. The `GHOST_CLOSURE` event type already exists in `LIFECYCLE_EVENTS` (event_store.py line 71) but is never emitted.
2. **`close_source='board_absent'` is not persisted** to the signals DB row when the reconciler triggers a soft close.
3. **There is no way to query "how many ghost closures happened"** or "which signals were ghost-closed vs confirmed-closed" without manually parsing Telegram notification history.

This plan adds instrumentation: when signal_router.py processes a board_absent CLOSE action, it writes the GHOST_CLOSURE event directly to signal_events (via sqlite3 inline write, matching the existing pattern used elsewhere in signal_router.py) and appends a `[A6: ghost_closure absent_count=N]` note to the signal row.

**FORGE decision on ghost_confirmed column:** Do NOT add a `ghost_confirmed BOOLEAN` column. The `close_source` field already distinguishes closure types: `close_source='board_absent'` identifies ghost closures while `close_source IN ('sl_hit', 'tp_all_hit', 'pilot_closure', 'wg_alert')` identifies confirmed closures. A new column would be redundant. Query-time distinction is sufficient for analytics.

---

## 1. Current State Analysis

### Reconciler Logic (reconciler.py, lines 260–275)

```python
if orphan["absent_count"] >= self.absent_threshold:
    actions.append(
        self._build_action(
            "CLOSE",
            orphan,
            timestamp=ts,
            source="board_absent",
            confidence="MEDIUM",
            reason="soft_close_after_absent_threshold",
            detail={
                "close_source": "board_absent",
                "soft_close": True,
                "absent_count": orphan["absent_count"],
            },
        )
    )
    continue
```

This code exists and works. Also verified at lines 333–345 (second code path for missing-key-entirely scenario, identical structure).

### signal_router.py Board Processing (lines 3869–3975)

After the reconciler produces actions, `_route_board_update()` iterates them:

```python
for action in actions:
    kind = str(action.get("action") or "").upper()
    ...
    elif kind == "CLOSE":
        board_counts["closures"] += 1
    emitted_actions += 1
    self._queue_reconciler_action_notification(action, ...)
```

For CLOSE actions, only `_queue_reconciler_action_notification()` is called — which sends a Telegram notification only. **No DB write occurs here.**

### GHOST_CLOSURE in LIFECYCLE_EVENTS (event_store.py, line 71)

```python
LIFECYCLE_EVENTS = {
    ...
    "GHOST_CLOSURE",
    ...
}
```

The event type is registered and valid. Zero GHOST_CLOSURE events currently in signal_events (confirmed below).

### signal_router.py inline sqlite3 pattern (existing)

Signal_router already uses inline sqlite3 writes for board INSERT dedup checking (lines 3907–3921):
```python
import sqlite3 as _sq3
_DB = os.environ.get("OINKFARM_DB", "/home/m/data/oinkfarm.db")
with _sq3.connect(_DB, timeout=2) as _dconn:
    _dup = _dconn.execute(...).fetchone()
```

The same pattern can be used to write GHOST_CLOSURE events when a board_absent CLOSE is processed.

### close_source distribution (DB verified)

```sql
SELECT close_source, COUNT(*) FROM signals GROUP BY close_source ORDER BY cnt DESC;
```
Results: `sl_hit` (many), `pilot_closure` (many), `wg_alert` (some), `tp_all_hit` (some), `manual_close` (few), `retracted` (few), `board_absent` (0 — A6 not yet implemented), NULL (94 — auto-closed by oink-sync SL hits, close_source correctly set there).

### signal_events current state

```sql
SELECT event_type, COUNT(*) FROM signal_events GROUP BY event_type;
```
No GHOST_CLOSURE rows (0). Confirmed.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `signal-gateway/scripts/signal_gateway/signal_router.py` | `_route_board_update()` | MODIFY | When `kind == 'CLOSE'` and `detail.get('soft_close') is True`, write GHOST_CLOSURE event to signal_events + append note to signals row |
| `signal-gateway/tests/test_reconciler.py` | — | ADD | Tests for GHOST_CLOSURE event emission on board_absent CLOSE |

**Files NOT modified:**
- `reconciler.py` — already correct. The `soft_close=True` flag in detail is the trigger.
- `event_store.py` — GHOST_CLOSURE already in LIFECYCLE_EVENTS.
- `lifecycle.py` (oink-sync) — ghost closures originate from board signals, not price monitoring.
- `micro-gate-v3.py` — ghost closure is board-reconciler path, not signal-ingestion path.
- `signals` table schema — no new columns needed.

---

## 3. SQL Changes

### 3a. No schema migration required

The `close_source` column (`VARCHAR(50)`) already accepts `'board_absent'`. The `signal_events` table already exists (from A1). No DDL changes needed.

### 3b. GHOST_CLOSURE event INSERT (inline in signal_router.py)

```sql
-- Written inline within signal_router._route_board_update() when kind=='CLOSE' and soft_close==True
INSERT INTO signal_events (signal_id, event_type, payload, source, created_at)
VALUES (?, 'GHOST_CLOSURE', ?, 'signal_router', datetime('now'));
-- payload: JSON with {"absent_count": N, "trader": ..., "ticker": ..., "board_channel": ...}
```

### 3c. Signal note append (inline in signal_router.py)

```sql
UPDATE signals
SET notes = COALESCE(notes, '') || ' [A6: ghost_closure absent_count=' || ? || ']',
    updated_at = datetime('now')
WHERE id = ?
  AND close_source IS NULL;   -- safety guard: don't overwrite if already closed via confirmed source
```

**Note:** The `close_source` column is NOT updated here. Ghost closures from the board reconciler are soft/provisional — the operator gets notified, and the actual DB close (with `close_source='board_absent'`) happens via the normal OinkDB webhook pipeline (pilot_closure path or manual). The event log provides the audit trail; the note provides inline traceability.

### 3d. Verification queries

```sql
-- Confirm GHOST_CLOSURE events exist post-A6
SELECT COUNT(*) FROM signal_events WHERE event_type='GHOST_CLOSURE';
-- Expected pre-A6: 0; post-A6 (after first board_absent CLOSE): >= 1

-- Confirm ghost notes are being written
SELECT id, ticker, notes FROM signals WHERE notes LIKE '%ghost_closure%';

-- Confirm close_source distribution (should NOT add 'board_absent' entries until close is confirmed)
SELECT close_source, COUNT(*) FROM signals GROUP BY close_source;
```

---

## 4. Implementation Notes

### 4a. Signal matching for the inline write

When `_route_board_update()` detects a board_absent CLOSE, it has `action.get("trader")`, `action.get("ticker")`, and `action.get("direction")` from the reconciler. The `signal_id` must be looked up via the same pattern used elsewhere in signal_router.py:

```python
# Pseudocode — ANVIL implements
import sqlite3 as _sq3
_DB = os.environ.get("OINKFARM_DB", "/home/m/data/oinkfarm.db")
_trader = action.get("trader") or ""
_ticker = str(action.get("ticker") or "").upper()
_direction = str(action.get("direction") or "").upper()
with _sq3.connect(_DB, timeout=2) as _dconn:
    row = _dconn.execute(
        """SELECT s.id FROM signals s
           JOIN traders t ON s.trader_id = t.id
           WHERE LOWER(t.name) = LOWER(?)
             AND UPPER(s.ticker) = UPPER(?)
             AND UPPER(s.direction) = UPPER(?)
             AND s.status IN ('ACTIVE', 'PARTIALLY_CLOSED')
           ORDER BY s.id DESC LIMIT 1""",
        (_trader, _ticker, _direction),
    ).fetchone()
if row is None:
    _LOG.warning("[router] A6: ghost_closure — no matching ACTIVE/PARTIALLY_CLOSED signal for %s/%s/%s",
                 _trader, _ticker, _direction)
    # Emit notification only, skip DB write
else:
    sig_id = row[0]
    # Write GHOST_CLOSURE event and append note
```

### 4b. Non-fatal DB write pattern

Matching existing signal_router.py error handling: wrap the DB write in try/except, log at WARNING level if it fails, and allow the notification to proceed regardless. Ghost closure instrumentation must never block the notification flow.

```python
try:
    # inline sqlite3 write
    ...
except Exception as _e:
    _LOG.warning("[router] A6: ghost_closure DB write failed: %s", _e)
```

### 4c. Absent count in event payload

The `detail.get("absent_count")` from the reconciler action contains the snapshot count that triggered the threshold. Include it in the GHOST_CLOSURE payload:

```python
_payload = json.dumps({
    "absent_count": action.get("detail", {}).get("absent_count"),
    "trader": _trader,
    "ticker": _ticker,
    "direction": _direction,
    "board_channel": action.get("board_channel", ""),
})
```

### 4d. Idempotency concern

If the reconciler fires board_absent CLOSE for the same position across multiple snapshot cycles (e.g., the signal stays missing for 5+ snapshots), GHOST_CLOSURE events may be emitted multiple times. Mitigation:

- After the first GHOST_CLOSURE event is written, check if the signal has already been ghost-closed (e.g., check `notes LIKE '%ghost_closure%'`) and skip re-emitting.
- OR: accept duplicate events (each snapshot is a valid data point about the position's continued absence) and filter by `MIN(created_at)` in analytics queries.

**FORGE recommendation:** Accept the first GHOST_CLOSURE event only — check if `signal_events` already has a GHOST_CLOSURE row for this `signal_id` before inserting:

```sql
INSERT INTO signal_events (signal_id, event_type, payload, source, created_at)
SELECT ?, 'GHOST_CLOSURE', ?, 'signal_router', datetime('now')
WHERE NOT EXISTS (
    SELECT 1 FROM signal_events
    WHERE signal_id = ? AND event_type = 'GHOST_CLOSURE'
);
```

### 4e. signal_events schema (verified from A1)

```sql
CREATE TABLE IF NOT EXISTS signal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT,
    source TEXT,
    created_at DATETIME DEFAULT (datetime('now'))
);
```

The `source` column uses `TEXT` — use `'signal_router'` for A6-written events (distinguishes from `'oink-sync'` events).

---

## 5. Test Specification

All tests added to `signal-gateway/tests/test_reconciler.py` using the existing `ReconcilerTests` fixture pattern.

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_board_absent_close_emits_ghost_closure_event` | Position tracked. Run 3 snapshots with position absent (absent_count hits threshold=3). Verify GHOST_CLOSURE event is inserted into in-memory signal_events table. | `signal_events` has 1 row with `event_type='GHOST_CLOSURE'`, `signal_id` matches the tracked signal, payload contains `absent_count=3` | integration | MUST |
| `test_board_absent_close_appends_ghost_note` | Same as above. Verify signal notes field. | `signals.notes` contains substring `'ghost_closure absent_count=3'` | integration | MUST |
| `test_board_absent_close_idempotent` | Run 5 absent snapshots (threshold=3). Verify event not duplicated. | `signal_events` has exactly 1 GHOST_CLOSURE row for this signal_id | integration | MUST |
| `test_confirmed_close_not_tagged_ghost` | Position absent + close alert present (cross-verified). Run snapshot. | No GHOST_CLOSURE event. Reconciler emits CLOSE with `source='board+alerts cross-verified'` (not board_absent) | integration | MUST |
| `test_ghost_close_skipped_when_no_active_signal` | Board_absent CLOSE emitted by reconciler but no matching ACTIVE signal in DB. | No DB write attempted; WARNING logged; notification still fires | unit | MUST |
| `test_ghost_closure_event_source_is_signal_router` | Same as first test. | GHOST_CLOSURE event row has `source='signal_router'` | unit | SHOULD |
| `test_partially_closed_signal_gets_ghost_closure` | Signal in PARTIALLY_CLOSED status disappears from board. | GHOST_CLOSURE event written; `signal_id` matches PARTIALLY_CLOSED signal | integration | SHOULD |

---

## 6. Acceptance Criteria

1. **Event written:** After `absent_count >= absent_threshold` triggers a board_absent CLOSE, a `GHOST_CLOSURE` event exists in `signal_events` with the matching `signal_id`
2. **Note appended:** The closed signal's `notes` field contains `[A6: ghost_closure absent_count=N]`
3. **No duplicate events:** A single signal accumulates at most 1 GHOST_CLOSURE event in `signal_events`, even if multiple board snapshots fire
4. **Non-fatal:** If the DB write fails (timeout, lock), the Telegram notification is still sent and the error is logged at WARNING — no exception propagation
5. **Query confirms coverage:**
   ```sql
   SELECT COUNT(*) FROM signal_events WHERE event_type='GHOST_CLOSURE';
   -- Expected: >= 1 in production after first board_absent cycle post-A6
   ```
6. **Regression:** All existing `test_reconciler.py` tests continue to pass without modification

---

## 7. Rollback Plan

1. **Revert code:** `git revert <A6-commit-hash>` in signal-gateway repo
2. **Clean up events (optional):**
   ```sql
   DELETE FROM signal_events WHERE event_type='GHOST_CLOSURE' AND source='signal_router';
   ```
3. **Clean up notes (optional):**
   ```sql
   UPDATE signals SET notes = REPLACE(notes, ...) WHERE notes LIKE '%ghost_closure%';
   -- Use sqlite3 REPLACE() or Python migration script to strip the appended tags
   ```
4. **Restart service:** `systemctl --user restart signal-gateway` (or equivalent)
5. **Verification:**
   ```sql
   SELECT COUNT(*) FROM signal_events WHERE event_type='GHOST_CLOSURE';
   -- Expected: 0 (or historical events created before rollback)
   ```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Signal lookup fails (no matching ACTIVE row) | Medium — position may have already been manually closed | Low — just skip the DB write, log warning | Covered by `test_ghost_close_skipped_when_no_active_signal` |
| sqlite3 timeout under DB load | Low | None — notification still fires | try/except with WARNING log, non-fatal |
| GHOST_CLOSURE emitted for non-ghost closure (false positive) | Low — only fires when `detail.get('soft_close') is True` | Low — adds a spurious event and note | Guard strictly on `soft_close=True` in detail |
| Note accumulates across multiple absent snapshots before dedup kicks in | Low — handled by INSERT...WHERE NOT EXISTS guard | Low — cosmetic DB bloat | Idempotent insert per implementation note §4d |
| `signal_events` table not yet initialized in signal-gateway context | Very low — A1 shipped; schema exists | None — `ensure_schema()` is idempotent | Wrap in try/except |

---

## 9. Evidence

**Files read:**
- `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` (commit `38eb8e87`) — lines 237–275, 310–360: verified board_absent CLOSE logic with `soft_close=True` and `absent_count` in detail
- `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` (commit `38eb8e87`) — lines 3869–3975: verified CLOSE actions only go to `_queue_reconciler_action_notification()`, no DB write
- `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` — lines 3907–3921: verified existing inline sqlite3 pattern for board INSERT dedup
- `/home/oinkv/oink-sync/oink_sync/event_store.py` (commit `ab5d941`) — line 71: `GHOST_CLOSURE` confirmed in `LIFECYCLE_EVENTS` set
- `/home/oinkv/signal-gateway/tests/test_reconciler.py` — reviewed existing test patterns and setUp fixture

**Database queries run:**
```sql
-- signal_events event types
SELECT event_type, COUNT(*) FROM signal_events GROUP BY event_type;
-- GHOST_CLOSURE: 0 (not yet implemented)

-- close_source distribution
SELECT close_source, COUNT(*) FROM signals GROUP BY close_source;
-- board_absent: 0 confirmed

-- signals schema
PRAGMA table_info(signals);
-- No ghost_confirmed column exists; close_source VARCHAR(50) already present
```

**Git commits reviewed:**
- `38eb8e87` — signal-gateway HEAD
- `ab5d941` — oink-sync HEAD
- `69d6840a` — micro-gate HEAD
