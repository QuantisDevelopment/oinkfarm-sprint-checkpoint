# Task A.1: signal_events Table + 12 Event Type Instrumentation

## ⚠️ POST-AUDIT REVISIONS

**Date:** 2026-04-19
**Auditor:** OinkV 👁️🐷

This plan has been revised after OinkV code audit (see `OINKV-AUDIT.md`). Key changes:

- **Dead-code redirect:** All references to `scripts/kraken-sync.py` (inactive since 2026-04-07) have been redirected to the live lifecycle engine at `oink-sync/oink_sync/lifecycle.py` (`LifecycleManager` class, 811 LOC). Functions are methods on the class, not module-level, and line numbers differ.
- **Cross-repo `event_store` resolution:** `event_store.py` lives in the oinkfarm repo; `lifecycle.py` lives in the standalone `oink-sync` repo. **RECOMMENDED PATH: vendor `event_store.py` into oink-sync as `oink_sync/event_store.py`** (single source of truth, no shared-package complexity, ANVIL writes one import path). The oinkfarm-side `event_store.py` remains for `micro-gate-v3.py`.
- **Integration pattern + service name:** Class-based lazy-init (not module-level globals). Service restart is `systemctl --user restart oink-sync` (user-level, no sudo). A standalone reconciler at `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` was also identified as a GHOST_CLOSURE event source.

---

**Source:** Arbiter-Oink Phase 4 §1, Phase 2 V2 (event log schema)
**Tier:** 🔴 CRITICAL
**Dependencies:** None — this is the foundation task
**Estimated Effort:** Phase 4 says 1-2 days; FORGE assessment: 1-2 days (reduced — event_store.py already exists with Phase 1 dual-write from GH#22)
**Plan Version:** 1.0
**Codebase Verified At:** `521d4411` (2026-04-18)

---

## 0. Executive Summary

The `signal_events` table and `EventStore` class already exist (GH#22, commit `387a8a4d`). The schema is in production but **contains 0 events** — instrumentation in micro-gate-v3.py is present but `kraken-sync.py` (the main lifecycle engine) has NO event store integration. This plan upgrades the existing infrastructure:

1. **Extend the schema** to add `field`, `old_value`, `new_value`, `source_msg_id` columns (Phase 4 spec)
2. **Instrument kraken-sync.py** for 6 event types: SL_UPDATED (via TP trailing), TP_HIT, TRADE_CLOSED_SL/TP/BE, LIMIT_FILLED, LIMIT_EXPIRED, PRICE_ALERT
3. **Instrument oinkdb-api.py** for 3 event types: ENTRY_CORRECTED, FIELD_CORRECTED, NOTE_ADDED
4. **Diagnose and fix the 0-event problem** in production (micro-gate events should be logging but aren't)
5. **Add GHOST_CLOSURE event type** to reconciler flow (currently handled via micro-gate's `_process_closure`)

---

## 1. Current State Analysis

### What Already Exists

**event_store.py** (209 LOC, `scripts/event_store.py`)
- `EventStore` class with `log()`, `quarantine_entry()`, `resolve_quarantine()`, `get_events()`, `stats()`
- Schema: `signal_events(id, signal_id, event_type, payload, source, created_at)` + indexes
- `quarantine(id, signal_id, error_code, error_detail, raw_payload, source, created_at, resolved_at, resolution)`
- 18 event types defined in `LIFECYCLE_EVENTS` set
- 15 quarantine error codes in `QUARANTINE_CODES` set
- Idempotent schema creation via `ensure_schema()`

**micro-gate-v3.py** (1,393 LOC, `scripts/micro-gate-v3.py`)
- Imports `EventStore` with graceful fallback (lines ~30-49)
- `_log_event()` helper — best-effort, non-fatal (lines ~51-57)
- Already emits: `SIGNAL_CREATED`, `SL_MODIFIED`, `SL_TO_BE`, `ORDER_FILLED`, `TRADE_CLOSED_SL/TP/BE/MANUAL`, `TRADE_CANCELLED`
- Quarantine writes on all 11 rejection paths

**kraken-sync.py** (1,840 LOC, `scripts/kraken-sync.py`)
- **NO event_store import. NO event logging.**
- Handles: SL/TP detection (`check_sl_tp()`), limit fills (`check_limit_fills()`), limit expiry (`expire_stale_limits()`), closures, PnL calculation
- This is the primary lifecycle engine — it processes the majority of state transitions

**oinkdb-api.py** (1,748 LOC, `api/oinkdb-api.py`)
- FastAPI application serving REST + WebSocket endpoints
- Has field correction logic (entry corrections via `/signals/{id}` endpoints)
- **NO event_store import. NO event logging.**

### Current Schema State

```sql
-- signal_events table EXISTS but has 0 rows:
-- Table structure (from PRAGMA table_info):
-- id         INTEGER PRIMARY KEY AUTOINCREMENT
-- signal_id  INTEGER NOT NULL
-- event_type TEXT NOT NULL
-- payload    TEXT NOT NULL DEFAULT '{}'
-- source     TEXT
-- created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))

-- Indexes exist:
-- idx_events_signal ON signal_events(signal_id, event_type)
-- idx_events_time ON signal_events(created_at)
-- idx_events_type ON signal_events(event_type)

-- quarantine table has 11 entries (active):
-- CROSS_CHANNEL_DUPLICATE: 3, MISSING_FIELD: 3, PRICE_DEVIATION: 3, EXCHANGE_NOT_FOUND: 2
```

### Phase 4 Target Schema (from Arbiter-Oink)

```sql
CREATE TABLE signal_events (
    id          INTEGER PRIMARY KEY,
    signal_id   INTEGER NOT NULL REFERENCES signals(id),
    event_type  TEXT NOT NULL,
    field       TEXT,           -- ❌ MISSING in current schema
    old_value   TEXT,           -- ❌ MISSING in current schema
    new_value   TEXT,           -- ❌ MISSING in current schema
    payload     TEXT,           -- ✅ EXISTS (DEFAULT '{}')
    source      TEXT NOT NULL,  -- ⚠️ EXISTS but nullable (current schema allows NULL)
    source_msg_id TEXT,         -- ❌ MISSING in current schema
    created_at  DATETIME NOT NULL DEFAULT (datetime('now'))  -- ✅ EXISTS (different format)
);
```

### Key Files

| File | Path | LOC | Relevance |
|------|------|-----|-----------|
| event_store.py | scripts/event_store.py | 209 | EventStore class — needs schema extension + new methods |
| lifecycle.py | oink-sync repo: oink_sync/lifecycle.py | 811 | Main lifecycle engine (LifecycleManager class) — needs full event instrumentation |
| micro-gate-v3.py | scripts/micro-gate-v3.py | 1,393 | Already instrumented — verify working, add missing events |
| oinkdb-api.py | api/oinkdb-api.py | 1,748 | Correction/note endpoints — needs event instrumentation |

### Key Functions Needing Instrumentation

| Function | File | Current Behavior | Events to Emit |
|----------|------|-----------------|----------------|
| `LifecycleManager._check_sl_tp()` | oink_sync/lifecycle.py (line ~259) | Detects SL/TP hits, trails SL, closes trades | TP_HIT, SL_UPDATED (trail), TRADE_CLOSED_SL/TP/BE |
| `LifecycleManager._check_limit_fills()` | oink_sync/lifecycle.py (line ~428) | Detects PENDING→ACTIVE transitions | LIMIT_FILLED (ORDER_FILLED) |
| `LifecycleManager._expire_stale_limits()` | oink_sync/lifecycle.py (line ~475) | Auto-cancels stale limits | LIMIT_EXPIRED |
| `LifecycleManager._check_sl_proximity()` | oink_sync/lifecycle.py (line ~550) | Near-SL/TP price alerts | PRICE_ALERT |
| Various endpoints | oinkdb-api.py | Field corrections, notes | ENTRY_CORRECTED, FIELD_CORRECTED, NOTE_ADDED |

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| scripts/event_store.py | `_SCHEMA_SQL` | MODIFY | Add `field`, `old_value`, `new_value`, `source_msg_id` columns via ALTER TABLE migration |
| scripts/event_store.py | `EventStore.log()` | MODIFY | Accept optional `field`, `old_value`, `new_value`, `source_msg_id` params |
| scripts/event_store.py | `EventStore.ensure_schema()` | MODIFY | Add migration step for new columns (ALTER TABLE IF NOT EXISTS pattern) |
| oink_sync/lifecycle.py | LifecycleManager.__init__() | MODIFY | Initialize EventStore on construction (or lazy-init pattern) |
| oink_sync/lifecycle.py | LifecycleManager._check_sl_tp() | MODIFY | Emit TP_HIT, SL_UPDATED (trail), TRADE_CLOSED events |
| oink_sync/lifecycle.py | LifecycleManager._check_limit_fills() | MODIFY | Emit ORDER_FILLED events |
| oink_sync/lifecycle.py | LifecycleManager._expire_stale_limits() | MODIFY | Emit LIMIT_EXPIRED events |
| oink_sync/lifecycle.py | LifecycleManager._check_sl_proximity() | MODIFY | Emit PRICE_ALERT events |
| oink-sync repo: event_store integration | — | CREATE or VENDOR | event_store.py must be made importable from oink-sync (see cross-repo note above) |
| api/oinkdb-api.py | correction endpoints | MODIFY | Emit ENTRY_CORRECTED, FIELD_CORRECTED, NOTE_ADDED events |
| tests/test_event_store.py | — | CREATE | Unit tests for EventStore schema migration + new columns |
| oink-sync/tests/test_lifecycle_events.py | — | CREATE | Unit tests for lifecycle event emission |

---

## 3. SQL Changes

### 3a. Schema Migration (add missing columns)

```sql
-- Run as part of EventStore.ensure_schema() migration step
-- These are additive ALTERs — safe against existing 0-row table

ALTER TABLE signal_events ADD COLUMN field TEXT;
ALTER TABLE signal_events ADD COLUMN old_value TEXT;
ALTER TABLE signal_events ADD COLUMN new_value TEXT;
ALTER TABLE signal_events ADD COLUMN source_msg_id TEXT;

-- Verification:
-- PRAGMA table_info(signal_events);
-- Should show 10 columns: id, signal_id, event_type, payload, source, created_at,
--   field, old_value, new_value, source_msg_id
```

### 3b. Source NOT NULL enforcement (deferred)

The Phase 4 spec says `source TEXT NOT NULL`. The current schema allows NULL. Since we have 0 rows, this could be fixed, but ALTER TABLE in SQLite cannot change column constraints. Options:
1. **Enforce at application level** (EventStore.log() validates source is not None) — recommended for Phase A
2. **Recreate table** with NOT NULL constraint — risky for production, defer to Phase B PostgreSQL migration

**FORGE recommendation:** Enforce at application level in Phase A. Add `assert source is not None` or default to caller name in `EventStore.log()`.

---

## 4. Implementation Notes

### 4a. Zero-Event Diagnostic

The production DB has 0 events despite micro-gate instrumentation being present. Possible causes:
1. **Production service runs older code** — the GH#22 commit (`387a8a4d`) may not be deployed yet
2. **EventStore import fails on production** — the `try/except` in micro-gate silently swallows import errors
3. **DB path mismatch** — micro-gate connects to a different DB path than where we're querying

**ANVIL action required:** Before implementing A1 instrumentation, verify that:
- `git rev-parse HEAD` on the production server matches `521d4411` or later
- `event_store.py` is importable from the micro-gate process (test: `python3 -c "from event_store import EventStore"` in the scripts dir)
- DB_PATH in `oink_config.py` resolves to the same file we're querying

### 4b. kraken-sync.py Event Store Integration Pattern

kraken-sync.py uses a long-lived `sqlite3.Connection` (via `get_db()` at line ~280). The EventStore should be initialized once and reused. Follow micro-gate's pattern:

```python
# In LifecycleManager.__init__() or as a lazy property:
# EventStore must be vendored or installed in oink-sync's Python environment
# (it lives in oinkfarm repo — cross-repo dependency, see audit note)
#
# Option A — vendor event_store.py into oink-sync:
#   Copy scripts/event_store.py → oink_sync/event_store.py
#
# Option B — raw SQL inserts (no EventStore class dependency):
#   Write directly to signal_events table from lifecycle.py
#
# Integration pattern (class-based, not module-level):
class LifecycleManager:
    def __init__(self, cfg=None):
        self.cfg = cfg or LifecycleConfig()
        self._event_store = None  # lazy-init on first run_cycle

    def _get_event_store(self, conn):
        if self._event_store is None or self._event_store.conn is not conn:
            try:
                self._event_store = EventStore(conn)
                self._event_store.ensure_schema()
            except Exception:
                self._event_store = None
        return self._event_store

    def _log_event(self, conn, event_type, signal_id, payload=None):
        try:
            es = self._get_event_store(conn)
            if es:
                es.log(event_type, signal_id, payload, source="oink-sync")
        except Exception:
            pass  # Non-fatal
```

### 4c. Event Emission Points in check_sl_tp()

The `LifecycleManager._check_sl_tp()` method (line ~259) delegates TP handling to `_process_tp_hits()` (line ~358):

**TP Hit Path** (partial close — trails SL, does NOT close trade):
- Handled in `_process_tp_hits()` at line ~358-425
- The `conn.execute(f"UPDATE signals SET {hit_col}=?...` is at approximately line ~406

**Closure Path** (SL hit — closes trade with blended PnL):
- Handled inline in `_check_sl_tp()` at approximately line ~318-354
- The `conn.execute("UPDATE signals SET status=?...` is at approximately line ~328

### 4d. Event Payloads

Each event's payload should be a JSON dict capturing the state at the time of the event:

| Event Type | Payload Keys |
|------------|-------------|
| `TP_HIT` | `tp_level`, `tp_price`, `current_price`, `new_sl`, `old_sl`, `remaining_tps` |
| `SL_MODIFIED` | `old_sl`, `new_sl`, `trigger` (= "tp_trail" or "manual") |
| `TRADE_CLOSED_SL` | `exit_price`, `final_roi`, `status`, `close_source`, `hold_hours` |
| `TRADE_CLOSED_TP` | same as above |
| `TRADE_CLOSED_BE` | same as above |
| `ORDER_FILLED` | `fill_price`, `old_status`, `new_status` |
| `LIMIT_EXPIRED` | `reason`, `age_days` |
| `PRICE_ALERT` | `alert_type` (= "near_sl" or "near_tp"), `current_price`, `threshold_price`, `distance_pct` |
| `ENTRY_CORRECTED` | `old_entry`, `new_entry`, `corrector` |
| `FIELD_CORRECTED` | `field`, `old_value`, `new_value`, `corrector` |
| `NOTE_ADDED` | `note_text`, `author` |
| `GHOST_CLOSURE` | `detection_source`, `board_state`, `signal_id` |
| `TRADE_RESTORED` | `restored_from`, `restored_by` |

### 4e. Transaction Safety

oink-sync's lifecycle methods use explicit `conn.commit()` calls (see `_check_sl_tp()` line ~354: `if events: conn.commit()`). Event logging should be inserted BEFORE the `conn.commit()` call to ensure the event row is in the same transaction as the signal UPDATE.

**Critical:** Event logging must NEVER block or delay the signal UPDATE. The `try/except` wrapper in `_log_event()` ensures this.

### 4f. Backward Compatibility

- The ALTER TABLE additions are purely additive — no existing columns change
- The `field`, `old_value`, `new_value`, `source_msg_id` columns should all be nullable (no DEFAULT constraint)
- Existing `EventStore.log()` callers that don't pass the new params will get NULL for those columns — this is correct
- The `payload` JSON blob already captures most event data; the new columns provide structured access for common query patterns

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_schema_migration_adds_columns` | Run `ensure_schema()` on DB with old schema (no field/old_value/new_value/source_msg_id) | PRAGMA table_info shows all 10 columns | unit | MUST |
| `test_schema_migration_idempotent` | Run `ensure_schema()` twice on same DB | No error, columns exist once | unit | MUST |
| `test_log_with_new_columns` | `es.log("SL_MODIFIED", 1, payload={...}, source="kraken-sync", field="stop_loss", old_value="100", new_value="105")` | Row with field="stop_loss", old_value="100", new_value="105" | unit | MUST |
| `test_log_without_new_columns` | `es.log("TP_HIT", 1, payload={...}, source="kraken-sync")` | Row with field=NULL, old_value=NULL, new_value=NULL | unit | MUST |
| `test_kraken_tp_hit_emits_event` | Simulate TP1 hit in `check_sl_tp()` with mock DB | signal_events has TP_HIT row with correct payload | integration | MUST |
| `test_kraken_sl_closure_emits_event` | Simulate SL hit closure in `check_sl_tp()` | signal_events has TRADE_CLOSED_SL row with exit_price, final_roi | integration | MUST |
| `test_kraken_limit_fill_emits_event` | Simulate PENDING→ACTIVE transition in `check_limit_fills()` | signal_events has ORDER_FILLED row | integration | MUST |
| `test_kraken_limit_expire_emits_event` | Simulate stale limit expiry | signal_events has LIMIT_EXPIRED row | integration | MUST |
| `test_event_store_failure_non_fatal` | Corrupt/unavailable event store, run check_sl_tp() | SL/TP detection works normally, no crash | integration | MUST |
| `test_source_not_null_enforcement` | Call `es.log()` with source=None | Either raises ValueError or defaults to caller name | unit | SHOULD |
| `test_event_count_after_full_lifecycle` | Process: INSERT signal → TP1 hit → TP2 hit → SL hit closure | 4+ events in signal_events for that signal_id | integration | SHOULD |
| `test_quarantine_still_works` | Reject a signal through micro-gate | quarantine table has new row | regression | MUST |

---

## 6. Acceptance Criteria

1. **Event coverage:** After 24 hours of production operation, `SELECT COUNT(*) FROM signal_events` > 0 for at least 3 different event types
2. **Schema complete:** `PRAGMA table_info(signal_events)` shows all 10 columns (id, signal_id, event_type, field, old_value, new_value, payload, source, source_msg_id, created_at)
3. **kraken-sync instrumented:** Every SL/TP detection, closure, limit fill, and limit expiry produces a corresponding signal_events row
4. **Non-fatal guarantee:** If signal_events table is dropped or corrupted, kraken-sync.py and micro-gate-v3.py continue to function normally with no crashes
5. **Zero regressions:** All 6 existing tests pass: `test_dashboard_registry_safeguard`, `test_micro_gate_mutation_guard`, `test_micro_gate_source_url`, `test_micro_gate_wg_alert_override`, `test_oinkdb_api_registry_validate`, `test_registry_validator`
6. **Quarantine functional:** Quarantine writes continue to work (regression test)

---

## 7. Rollback Plan

1. **Schema rollback:**
   - The new columns cannot be removed via ALTER TABLE DROP in SQLite
   - If needed: `CREATE TABLE signal_events_backup AS SELECT id, signal_id, event_type, payload, source, created_at FROM signal_events; DROP TABLE signal_events; ALTER TABLE signal_events_backup RENAME TO signal_events;`
   - Then recreate indexes
2. **Code rollback:**
   - `git revert <commit-hash>` — reverts kraken-sync.py and oinkdb-api.py event instrumentation
   - event_store.py changes are backward-compatible (old callers still work)
3. **Service restart:**
   - `systemctl --user restart oink-sync` (user-level service, no sudo needed)
4. **Verification:**
   - `SELECT COUNT(*) FROM signal_events` — should show no new events after rollback
   - kraken-sync.py SL/TP detection continues to work (check ACTIVE signals are still monitored)

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Event logging adds write latency to kraken-sync | Low | Low — ~0.1ms/event on SQLite | Non-fatal try/except wrapper; monitor SQLITE_BUSY count |
| Zero-event bug not diagnosed before deployment | Medium | Medium — events still won't log | ANVIL must verify production deployment state FIRST |
| Schema migration fails on production | Low | Low — ALTERs are additive on empty table | Test ALTER on copy of production DB first |
| kraken-sync import path issues | Medium | Low — graceful fallback means no crash | Follow exact import pattern from micro-gate-v3.py (proven working) |
| oinkdb-api.py event store init conflicts with FastAPI lifecycle | Low | Medium — could affect API startup | Lazy init pattern (same as micro-gate), not at import time |

---

## 9. Evidence

**Files read:**
- `scripts/event_store.py` (commit `521d4411`, full read)
- `scripts/micro-gate-v3.py` (commit `521d4411`, full read — 1,393 LOC)
- `scripts/kraken-sync.py` (commit `521d4411`, full read — 1,840 LOC, functions listed at all `def` lines)
- `api/oinkdb-api.py` (commit `521d4411`, function signatures + corrections flow)
- All 6 test files in `tests/` directory

**Queries run:**
```sql
PRAGMA table_info(signal_events);
-- Result: 6 columns (id, signal_id, event_type, payload, source, created_at)

SELECT COUNT(*) FROM signal_events;
-- Result: 0

SELECT COUNT(*) FROM quarantine;
-- Result: 11

SELECT event_type, COUNT(*) FROM signal_events GROUP BY event_type;
-- Result: (empty — 0 events)

SELECT error_code, COUNT(*) FROM quarantine GROUP BY error_code ORDER BY cnt DESC;
-- Result: CROSS_CHANNEL_DUPLICATE:3, MISSING_FIELD:3, PRICE_DEVIATION:3, EXCHANGE_NOT_FOUND:2
```

**Git history checked:**
```
git show 387a8a4d --stat  # GH#22: Event Store + Quarantine Phase 1 dual-write
# Modified: scripts/event_store.py (209 new), scripts/micro-gate-v3.py (+135/-13)
```

**Critical discovery — Arbiter-Oink report file name mapping:**
- Report references `lifecycle.py` → actual file is `oink-sync/oink_sync/lifecycle.py` (ported from kraken-sync.py, 811 LOC)
- Report references `engine.py` → actual file is `oink-sync/oink_sync/engine.py` (price polling + DB writes, 548 LOC)
- `scripts/kraken-sync.py` is LEGACY CODE (inactive since 2026-04-07, kept for rollback)
- Report references `signal_router.py` (4,366 LOC God Object) → **does not exist in current codebase**
- Report references `micro-gate-v3.py` → ✅ correct, exists at `scripts/micro-gate-v3.py`

---

## 10. Design Questions for Mike

### DQ-1: Schema Extension vs. Phase 4 Exact Spec

The Phase 4 spec includes `field`, `old_value`, `new_value`, `source_msg_id` columns. The current schema only has `payload` (JSON blob). Two options:

**Option A (Recommended):** Add the 4 columns via ALTER TABLE. This enables structured SQL queries like `SELECT * FROM signal_events WHERE field='stop_loss'` without JSON parsing.

**Option B:** Keep the current schema and store field/old_value/new_value inside the JSON `payload`. Simpler migration, but harder to query.

**FORGE recommendation:** Option A — the ALTER TABLE cost is near-zero on a 0-row table, and the structured columns will be valuable for Phase B PostgreSQL migration and KPI computation.

### DQ-2: Reconciler Event Source

The Arbiter-Oink report references a "reconciler" as a separate writer that emits GHOST_CLOSURE events. In the current codebase:
- There is no standalone `reconciler.py` file
- Reconciler logic appears to flow through micro-gate-v3.py's `_process_closure()` function
- WG reconciler events are tracked in `api/signals_by_route.py` as lifecycle events from a `lifecycle-events.jsonl` file

**Note:** A standalone reconciler DOES exist at `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py`. It handles board/alert reconciliation for WealthGroup lifecycle signals, with state persisted to `/home/oinkv/signal-gateway/status/reconciler-state.json`. GHOST_CLOSURE events should be emitted from this reconciler's close path (CLOSE_ACTIONS set includes CLOSE, CLOSE_WIN, CLOSE_LOSS, SL_HIT, etc.) AND from micro-gate's `_process_closure()` which handles closure webhooks.
