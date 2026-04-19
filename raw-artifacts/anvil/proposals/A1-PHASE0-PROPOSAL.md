# Phase 0 — Technical Proposal: Task A1

## signal_events Table Extension + Lifecycle Instrumentation

**Task:** A1 — signal_events table + 12 event type instrumentation
**Tier:** 🔴 CRITICAL
**Phase 4 Ref:** §1 (signal_events), Phase 2 V2 (event log schema)
**Author:** ⚒️ ANVIL
**Date:** 2026-04-19
**Proposal Version:** 1.0

---

## 1. Problem Statement

The `signal_events` table and `EventStore` class exist (GH#22, commit `387a8a4d`) but are functionally dead:

- **0 events in production** — `SELECT COUNT(*) FROM signal_events` returns 0
- **micro-gate instrumentation is present** (13 `_log_event` call sites) but **not firing** — the production deployment includes the code, `EventStore` imports successfully from the scripts directory, yet no events are being written
- **oink-sync has zero integration** — the main lifecycle engine (`lifecycle.py`, 811 LOC) handles SL/TP detection, limit fills, limit expiry, closures, and PnL computation with NO event logging whatsoever
- **Schema is incomplete** — missing 4 columns required by Phase 4: `field`, `old_value`, `new_value`, `source_msg_id`

The result: no audit trail for any signal lifecycle transition. When a signal's SL changes, TP is hit, or a trade closes, there is no record of WHAT changed, WHEN, or WHY.

---

## 2. Approach

### 2A. Schema Extension (ALTER TABLE)

Add 4 columns to the existing `signal_events` table via `ALTER TABLE`:

```sql
ALTER TABLE signal_events ADD COLUMN field TEXT;
ALTER TABLE signal_events ADD COLUMN old_value TEXT;
ALTER TABLE signal_events ADD COLUMN new_value TEXT;
ALTER TABLE signal_events ADD COLUMN source_msg_id TEXT;
```

This is safe because:
- Table has 0 rows — no data migration needed
- ALTER TABLE ADD COLUMN is purely additive in SQLite
- Existing callers that don't pass new params get NULL — correct behavior
- New columns are nullable — no constraint violations possible

The migration will be embedded in `EventStore.ensure_schema()` as idempotent ALTER statements (wrapped in try/except for "duplicate column" errors).

### 2B. EventStore.log() Signature Extension

Extend `EventStore.log()` to accept `field`, `old_value`, `new_value`, `source_msg_id` as optional keyword arguments. The INSERT statement grows from 4 to 8 columns. Backward-compatible: existing callers (micro-gate) continue working unchanged.

### 2C. Zero-Event Diagnostic

Before instrumenting oink-sync, diagnose WHY micro-gate's existing instrumentation produces 0 events. Verified so far:

| Check | Result |
|-------|--------|
| Production HEAD includes GH#22? | ✅ `3b5453b7` (post-A3 merge) includes `387a8a4d` |
| EventStore importable from scripts dir? | ✅ `python3 -c "from event_store import EventStore"` succeeds |
| signal_events table exists? | ✅ 6 columns, 3 indexes present |
| signal_events row count? | ❌ 0 rows |

**Hypothesis:** micro-gate's `_log_event()` calls are wrapped in best-effort try/except. The likely cause is a transaction/connection issue — `_get_event_store()` re-initializes on connection mismatch, and micro-gate uses ephemeral connections per batch. If `ensure_schema()` fails silently or the connection closes before commit, events are lost.

**Action:** I will add diagnostic logging to `_get_event_store()` and `_log_event()` to trace the exact failure point. If the root cause is transactional, I'll fix the commit pattern. If it's a path issue, I'll fix the DB path resolution.

### 2D. oink-sync Lifecycle Instrumentation

**Cross-repo dependency resolution:** `event_store.py` lives in the oinkfarm repo (`scripts/event_store.py`). `lifecycle.py` lives in the standalone `oink-sync` repo. I will **vendor `event_store.py` into oink-sync** as `oink_sync/event_store.py`:

- Single file copy (209 LOC), no shared-package complexity
- oink-sync gets its own `EventStore` that evolves independently
- Both copies share the same schema (same `_SCHEMA_SQL`)
- oinkfarm-side copy continues serving micro-gate

**Integration pattern:** Lazy-init `EventStore` inside `Lifecycle.__init__()` or on first `run_cycle()` call. Follow micro-gate's proven pattern: try/except wrapper, non-fatal on failure, never blocks lifecycle operations.

**Event emission points (6 types in lifecycle.py):**

| Method | Line | Event Type | Trigger |
|--------|------|-----------|---------|
| `_check_sl_tp()` → closure path | ~330 | `TRADE_CLOSED_SL` / `TRADE_CLOSED_TP` / `TRADE_CLOSED_BE` | SL/TP/BE hit closes trade |
| `_process_tp_hits()` | ~406 | `TP_HIT` + `SL_MODIFIED` (trail) | TP level hit, SL trailed up |
| `_check_limit_fills()` | ~460 | `ORDER_FILLED` (LIMIT_FILLED) | PENDING → ACTIVE transition |
| `_expire_stale_limits()` | ~510 | `LIMIT_EXPIRED` | Stale limit auto-cancelled |
| `_check_sl_proximity()` | ~580 | `PRICE_ALERT` | Price within alert threshold of SL/TP |

**oinkdb-api.py instrumentation (3 types):** Deferred to a follow-up sub-task or separate Phase 0 — oinkdb-api.py is a FastAPI application with different lifecycle patterns and will require its own review. This proposal focuses on event_store schema + oink-sync instrumentation.

### 2E. Reconciler GHOST_CLOSURE Events

The standalone reconciler at `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` (924 LOC) handles board/alert reconciliation. GHOST_CLOSURE events should be emitted from its close path. However, the reconciler is a separate service with its own import context. I will assess whether to instrument it in this task or defer to a follow-up.

---

## 3. Alternatives Considered

### Alternative A: Raw SQL Instead of Vendoring EventStore

Instead of copying `event_store.py` into oink-sync, write raw INSERT statements directly in `lifecycle.py`.

**Rejected because:**
- Duplicates schema creation logic
- No quarantine support
- No `get_events()` / `stats()` API for future use
- Vendoring is a single 209-LOC file copy — minimal overhead

### Alternative B: Shared Package (pip installable)

Create a shared `oinkfarm-events` package that both repos depend on.

**Rejected because:**
- Over-engineered for a 209-LOC utility
- Adds pip dependency management complexity
- Both repos deploy to the same machine — no distribution benefit
- Can be refactored later during Phase B PostgreSQL migration

### Alternative C: Defer oink-sync Instrumentation, Fix micro-gate First

Focus only on fixing the 0-event problem + schema extension. Defer lifecycle.py instrumentation.

**Rejected because:**
- oink-sync handles the MAJORITY of lifecycle transitions (SL/TP hits, closures, limit fills)
- micro-gate only handles initial INSERT and some closure webhooks
- Without oink-sync instrumentation, the event log remains mostly empty even after micro-gate is fixed
- The Phase 4 spec explicitly lists oink-sync event types as A1 deliverables

---

## 4. Data Impact Assessment

### Schema Change

| Column | Type | Nullable | Default | Impact |
|--------|------|----------|---------|--------|
| `field` | TEXT | Yes | NULL | New column — no existing data affected |
| `old_value` | TEXT | Yes | NULL | New column — no existing data affected |
| `new_value` | TEXT | Yes | NULL | New column — no existing data affected |
| `source_msg_id` | TEXT | Yes | NULL | New column — no existing data affected |

**Zero data risk:** Table has 0 rows. ALTER TABLE ADD COLUMN on an empty table is the safest possible migration.

### Write Volume Estimate

Current oink-sync cycle runs every ~60 seconds. Per cycle:
- ~89 ACTIVE signals checked for SL/TP → 0-5 events expected (closures/TP hits are infrequent)
- ~12 PENDING signals checked for limit fills → 0-1 events expected
- Price alerts → 0-10 per cycle (proximity checks)

**Expected steady-state:** ~50-200 events/day. SQLite handles this trivially.

### Existing Data Safety

- The `signals` table (489 rows) is NOT modified by this change
- `quarantine` table (11 rows) is NOT modified
- Event logging is purely additive (INSERT only, no UPDATE/DELETE on signal_events)
- Non-fatal wrapper ensures lifecycle operations continue if event logging fails

---

## 5. Test Strategy

### Unit Tests (event_store.py changes)

| Test | What it verifies |
|------|-----------------|
| `test_schema_migration_adds_columns` | ALTER TABLE adds 4 new columns to existing schema |
| `test_schema_migration_idempotent` | Running ensure_schema() twice doesn't error |
| `test_log_with_new_columns` | log() accepts field/old_value/new_value/source_msg_id |
| `test_log_without_new_columns` | Existing callers still work (NULL for new columns) |
| `test_source_msg_id_persisted` | source_msg_id correctly stored and queryable |

### Integration Tests (lifecycle.py instrumentation)

| Test | What it verifies |
|------|-----------------|
| `test_tp_hit_emits_event` | TP1 hit in _check_sl_tp → TP_HIT + SL_MODIFIED events |
| `test_sl_closure_emits_event` | SL hit → TRADE_CLOSED_SL event with exit_price, final_roi |
| `test_limit_fill_emits_event` | PENDING→ACTIVE → ORDER_FILLED event |
| `test_limit_expire_emits_event` | Stale limit → LIMIT_EXPIRED event |
| `test_price_alert_emits_event` | Near-SL price → PRICE_ALERT event |
| `test_event_store_failure_non_fatal` | Corrupt event_store → lifecycle continues normally |
| `test_event_count_full_lifecycle` | Full signal lifecycle → correct event sequence |

### Regression Tests

| Test | What it verifies |
|------|-----------------|
| `test_quarantine_still_works` | Quarantine writes unaffected |
| `test_existing_micro_gate_events_work` | micro-gate event logging still functions |
| All existing tests | 26 passing tests remain passing |

---

## 6. Rollback Plan

### Code Rollback
```bash
git revert <A1-commit-hash>
systemctl --user restart oink-sync
```

### Schema Rollback (if needed)
SQLite cannot DROP COLUMN. If rollback of schema is required:
```sql
-- Recreate without new columns
CREATE TABLE signal_events_backup AS
SELECT id, signal_id, event_type, payload, source, created_at
FROM signal_events;

DROP TABLE signal_events;
ALTER TABLE signal_events_backup RENAME TO signal_events;

-- Recreate indexes
CREATE INDEX idx_events_signal ON signal_events(signal_id, event_type);
CREATE INDEX idx_events_time ON signal_events(created_at);
CREATE INDEX idx_events_type ON signal_events(event_type);
```

### Risk of Rollback
- **Minimal:** Event logging is purely additive. Removing it means losing new audit data, but no existing functionality breaks.
- **No downstream dependency:** No code currently READS from signal_events in production — it's write-only for now.

---

## 7. Scope Boundaries

### In Scope
- ✅ Schema extension (4 new columns via ALTER TABLE)
- ✅ EventStore.log() signature extension
- ✅ Zero-event diagnostic + fix
- ✅ oink-sync lifecycle.py instrumentation (6 event types)
- ✅ Vendor event_store.py into oink-sync repo
- ✅ Unit + integration tests

### Out of Scope (Deferred)
- ❌ oinkdb-api.py instrumentation (ENTRY_CORRECTED, FIELD_CORRECTED, NOTE_ADDED) — separate service, separate review
- ❌ Reconciler GHOST_CLOSURE instrumentation — separate code path assessment needed
- ❌ `source NOT NULL` constraint enforcement — enforce at app level now, schema-level in Phase B
- ❌ Phase B PostgreSQL migration considerations

---

## 8. Implementation Plan

### Day 1
1. Diagnose + fix zero-event problem in micro-gate
2. Extend EventStore schema (4 columns) + ensure_schema() migration
3. Extend EventStore.log() signature
4. Write unit tests for schema + log changes
5. Vendor event_store.py into oink-sync

### Day 2
6. Instrument lifecycle.py (6 event emission points)
7. Write integration tests for lifecycle events
8. Run full test suite — verify 0 regressions
9. Push branch, request review

### Estimated Total: 1.5–2 days

---

## 9. Financial Hotpath Assessment

**Does this diff touch Financial Hotpath functions?**

| Hotpath Function | Touched? | Explanation |
|-----------------|----------|-------------|
| `calculate_blended_pnl()` | ❌ No | No changes to PnL calculation |
| `_check_sl_tp()` | ⚠️ Yes — adding event logging calls | Non-mutating: only appends to signal_events AFTER the existing UPDATE |
| `close_signal()` | ❌ No | Not directly modified |
| `update_sl()` | ❌ No | Not directly modified |
| lifecycle.py SL/TP write paths | ⚠️ Yes — adding event logging calls | Same as _check_sl_tp — logging only, not modifying the UPDATE |
| micro-gate INSERT logic | ⚠️ Yes — fixing existing event logging | Diagnostic only, not changing INSERT |
| remaining_pct computation | ❌ No | Not touched |

**Tier justification:** 🔴 CRITICAL because:
1. We instrument inside `_check_sl_tp()` and `_process_tp_hits()` — Financial Hotpath #2 and #5
2. Any error in the event logging try/except wrapper could theoretically affect the enclosing transaction
3. The vendored EventStore in oink-sync shares a DB connection with lifecycle operations

**Mitigation:** All event logging is wrapped in non-fatal try/except. Event INSERT happens WITHIN the same transaction (before `conn.commit()`), so it can't create orphaned state. If the try/except fails, the lifecycle UPDATE still commits normally.

---

## 10. Design Questions for Mike (from FORGE Plan)

### DQ-1: Schema Extension vs JSON-only (FORGE DQ-1)
**FORGE recommends Option A** (ALTER TABLE) — I agree. The 4 new columns enable structured queries without JSON parsing. Cost is near-zero on an empty table.

**My recommendation: Option A.** Proceed with ALTER TABLE.

### DQ-2: oinkdb-api.py Scope (new)
The FORGE plan includes oinkdb-api.py instrumentation (3 event types). I propose deferring this to a follow-up task. Rationale: oinkdb-api.py is a FastAPI app with a different lifecycle pattern (async, connection pool), and instrumenting it requires its own review for thread safety and connection handling.

**My recommendation: Defer to A1b or A4.** Keep A1 focused on event_store schema + oink-sync.

### DQ-3: Reconciler GHOST_CLOSURE Scope (FORGE DQ-2)
The reconciler is a standalone service at a different import path. GHOST_CLOSURE events should come from `micro-gate._process_closure()` when `close_source` indicates reconciler origin, AND from the standalone reconciler's close path.

**My recommendation: Defer reconciler instrumentation.** micro-gate already has `_log_event` calls in its closure path — once the zero-event bug is fixed, GHOST_CLOSURE-like events will flow from micro-gate. Reconciler instrumentation can follow in A1b.
