# A1 Zero-Event Root Cause — micro-gate event_store silent writes

**Task:** A1 — signal_events Table Extension + Lifecycle Instrumentation
**Date:** 2026-04-19
**Status:** Root cause confirmed and fixed

## Symptom

Production had:

```sql
SELECT COUNT(*) FROM signal_events;
-- 0
```

Despite micro-gate already containing 13 `_log_event()` call sites.

## Root Cause

All existing micro-gate `_log_event()` call sites occurred **after** the enclosing lifecycle `conn.commit()`.

Pattern observed:

1. `signals` row INSERT / UPDATE / CLOSE is executed
2. `conn.commit()` is called
3. `_log_event(conn, ...)` is called
4. `EventStore.log(..., commit=False)` inserts into `signal_events`
5. No second commit occurs for that event INSERT
6. Connection is reused or closed, leaving the event INSERT in a dangling uncommitted transaction

Result: signal mutations persisted, event rows did not.

## Confirmed Call-Site Pattern

Affected paths in `scripts/micro-gate-v3.py` included:
- `SIGNAL_CREATED`
- update/override event writes
- `ORDER_FILLED`
- `TRADE_CANCELLED`
- closure event writes

In each case, the event write happened after the already-committed signal mutation.

## Fix Applied

`micro-gate-v3.py::_log_event()` now calls:

```python
es.log(event_type, signal_id, payload, source, commit=True)
```

This makes event INSERTs self-committing and preserves VIGIL's transaction-scope requirement:
- the non-fatal wrapper still covers **only** the event INSERT path
- signal INSERT/UPDATE/CLOSE exceptions are not swallowed
- event logging failure degrades to missed audit trail, not corrupted signal state

## Why This Fix Was Chosen

Alternative considered: move every `_log_event()` call before the enclosing `conn.commit()`.

Rejected for Phase 1 because:
- more invasive across multiple hot paths
- easier to accidentally broaden try/except scope around signal mutations
- `commit=True` is already supported by `EventStore.log()` and fixes the exact bug with minimal blast radius

## Verification Logic

The new unit coverage proves the behavioral difference:
- `commit=True` → event visible from second connection
- `commit=False` → event not visible from second connection

See:
- `/home/oinkv/.openclaw/workspace/tests/test_event_store_a1.py`
  - `test_commit_true_persists_event`
  - `test_commit_false_not_visible_to_other_conn`

## Follow-on Relevance

This finding directly informed the oink-sync instrumentation pattern in A1:
- lifecycle event logging also uses self-committing event writes
- avoids repeating the same silent-loss bug in a second service

## Reviewer Concern Mapping

- **VIGIL:** tight try/except scope preserved
- **GUARDIAN:** root cause documented for future oinkdb-api / reconciler work
