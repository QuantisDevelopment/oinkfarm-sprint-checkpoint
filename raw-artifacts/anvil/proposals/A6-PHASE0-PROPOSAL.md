# A6 Phase 0 Proposal — Ghost Closure Confirmation Flag

**Task:** A6 — Ghost Closure Confirmation Flag  
**Tier:** 🟡 STANDARD  
**Author:** ANVIL (⚒️)  
**Date:** 2026-04-19  
**Revision:** 1 (addressing GUARDIAN REQUEST CHANGES from R0)  
**Spec Reference:** Phase 4 §2 (Signal Lifecycle Accuracy), Phase 5 §BS-3 (Ghost Closure Auditing)  
**Plan Source:** `/home/oinkv/forge-workspace/plans/TASK-A6-plan.md` (v1.0)  
**Dependencies:** A1 ✅ (event_store), A4 ✅ (PARTIALLY_CLOSED), A5 ✅ (confidence scoring)

**R0 Review Feedback Addressed:**
- GUARDIAN BLOCKING #1: Ambiguous signal lookup → added entry-price discriminator with 5% tolerance (§5 revised)
- GUARDIAN BLOCKING #2: Note append not idempotent → coupled note UPDATE to successful first-INSERT via `changes()` check (§5 revised)
- VIGIL Note #1: `created_at` format → omitted from INSERT, column default handles ISO 8601 (§5 revised)
- VIGIL Note #2: Single connection/transaction → event INSERT + note UPDATE share one `with conn:` block (§4 D6 added)

---

## 1. Problem Statement

When the reconciler detects a position has disappeared from the board for `absent_count >= absent_threshold` (default 3 snapshots), it emits a board_absent CLOSE action with `soft_close=True`. Currently, this action:

- ✅ Fires a Telegram notification to the operator (via `_queue_reconciler_action_notification()`)
- ❌ Does NOT write a `GHOST_CLOSURE` event to `signal_events` — even though the event type was declared in A1 (event_store.py line 70–71)
- ❌ Does NOT leave any DB-queryable trace on the signals row

There is no way to programmatically query "which signals were ghost-closed" or "how many ghost closures occurred this week" without parsing Telegram notification history.

---

## 2. Approach

**Single-file change:** Modify `_route_board_update()` in `signal_router.py` to instrument the existing `kind == "CLOSE"` branch when `detail.get("soft_close") is True`.

When a board_absent CLOSE action is processed:

1. **Look up the matching signal** — query `signals JOIN traders` for the ACTIVE/PARTIALLY_CLOSED signal matching (trader, ticker, direction). Use inline `sqlite3` — same pattern already used at signal_router.py lines 3907–3921 for board INSERT dedup checking.

2. **Write GHOST_CLOSURE event** — idempotent INSERT into `signal_events` with `WHERE NOT EXISTS` guard (max 1 event per signal_id). Payload includes `absent_count`, `trader`, `ticker`, `direction`, `board_channel`. Source = `'signal_router'`.

3. **Append note tag** — UPDATE `signals.notes` to append `[A6: ghost_closure absent_count=N]`, guarded by `close_source IS NULL` (don't tag signals already closed via confirmed sources).

4. **Non-fatal wrapper** — Entire DB write block wrapped in try/except, WARNING-level logging on failure. Notification flow (existing `_queue_reconciler_action_notification()`) executes regardless.

**What this does NOT do:**
- Does NOT update `close_source` — ghost closures from the board reconciler are soft/provisional. The actual DB close (with `close_source='board_absent'`) happens downstream via the OinkDB webhook pipeline.
- Does NOT add a `ghost_confirmed BOOLEAN` column — per FORGE decision, `close_source` already distinguishes closure types. Query-time distinction is sufficient.
- Does NOT modify `reconciler.py` — the reconciler already correctly emits `soft_close=True` + `absent_count` in the action detail.
- Does NOT modify `event_store.py` — `GHOST_CLOSURE` already exists in `LIFECYCLE_EVENTS`.

---

## 3. Canonical Repository & File Locations

| Component | Repo | Path | Notes |
|-----------|------|------|-------|
| signal_router.py | signal-gateway | `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` | Primary change target (4,375 LOC, HEAD `38eb8e8`) |
| reconciler.py | signal-gateway | `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` | Read-only — verify `soft_close=True` pattern |
| event_store.py | oinkfarm | `/home/oinkv/.openclaw/workspace/scripts/event_store.py` | NO changes — `GHOST_CLOSURE` already in LIFECYCLE_EVENTS |
| Tests | signal-gateway | `/home/oinkv/signal-gateway/tests/test_a6_ghost_closure.py` (new) | 7 tests per plan §5 |

**⚠️ Repo clarification:** A6 targets the **signal-gateway** repo (bandtincorporated8/signal-gateway), NOT the oinkfarm workspace. signal_router.py lives exclusively in signal-gateway. The oinkfarm workspace has micro-gate-v3.py but NOT signal_router.py.

The branch will be created in signal-gateway: `anvil/A6-ghost-closure-flag` from HEAD `38eb8e8`.

---

## 4. Key Implementation Decisions

### D1: Inline sqlite3 vs. event_store.py import

**Decision:** Use inline `sqlite3` writes, NOT `event_store.py` import.

**Rationale:** signal_router.py is a monolith (4,375 LOC) that already uses inline sqlite3 at lines 3907–3921 for board dedup. Importing event_store.py would introduce a new module dependency into the God Object. The inline pattern is battle-tested in this file and keeps the change minimal. The event INSERT is a 3-line SQL statement — there's no abstraction benefit from using EventStore.log() here.

### D2: Idempotency strategy

**Decision:** INSERT ... WHERE NOT EXISTS guard (max 1 GHOST_CLOSURE event per signal_id).

**Rationale:** The reconciler can fire board_absent CLOSE across multiple snapshot cycles for the same position. Per FORGE plan §4d, the first event is the meaningful one — subsequent absent snapshots don't add information. Dedup at INSERT time is cheaper than pre-checking and avoids TOCTOU.

### D3: Note append guard

**Decision:** Append `[A6: ghost_closure absent_count=N]` only when `close_source IS NULL`.

**Rationale:** If `close_source` is already set (e.g., `'sl_hit'`, `'pilot_closure'`), the signal was already closed via a confirmed source. Appending a ghost_closure note to a confirmed-closed signal would be misleading.

### D4: Signal lookup — status IN ('ACTIVE', 'PARTIALLY_CLOSED')

**Decision:** Include PARTIALLY_CLOSED signals in the lookup (matches A4 broadening pattern).

**Rationale:** A partially-closed signal that disappears from the board is still a ghost closure. Excluding PARTIALLY_CLOSED would create a blind spot for signals that had partial TPs hit before disappearing.

### D5: Test file location

**Decision:** New file `tests/test_a6_ghost_closure.py` rather than appending to existing `tests/test_reconciler.py`.

**Rationale:** test_reconciler.py (584 LOC) tests the Reconciler class itself. A6 tests the signal_router instrumentation that runs *after* the reconciler produces actions. Different SUT, different test file. Consistent with A1/A4/A5/A7 test naming convention (`test_a{N}_*.py`).

### D6: Single connection/transaction for event + note (NEW — R1)

**Decision:** Event INSERT and note UPDATE execute within the same `with conn:` block (implicit transaction).

**Rationale:** Ensures atomicity — if the INSERT succeeds but the UPDATE fails (or vice versa), the transaction rolls back. Also enables the `changes()` coupling pattern for note idempotency (see §5). Matches the inline sqlite3 connection pattern already established in signal_router.py.

---

## 5. SQL Operations (No DDL)

**Signal lookup (revised — entry-price discriminator):**
```sql
SELECT s.id, s.entry_price FROM signals s
JOIN traders t ON s.trader_id = t.id
WHERE LOWER(t.name) = LOWER(?)
  AND UPPER(s.ticker) = UPPER(?)
  AND UPPER(s.direction) = UPPER(?)
  AND s.status IN ('ACTIVE', 'PARTIALLY_CLOSED')
ORDER BY s.id DESC;
```
Then in Python, select the row whose `entry_price` is closest to the reconciler action's `entry` value within a 5% tolerance:
```python
_action_entry = float(action.get("entry") or 0)
matches = cursor.fetchall()
best = None
for row in matches:
    sig_id, db_entry = row[0], float(row[1] or 0)
    if _action_entry > 0 and db_entry > 0:
        deviation = abs(db_entry - _action_entry) / _action_entry
        if deviation <= 0.05:  # 5% tolerance, consistent with A7 threshold
            best = sig_id
            break  # rows ordered by id DESC — first match is most recent
    elif _action_entry == 0 and db_entry == 0:
        best = sig_id  # both zero-entry (rare) — take most recent
        break
if best is None:
    _LOG.warning("[router] A6: ghost_closure — no entry-matched signal for %s/%s/%s entry=%.4f",
                 _trader, _ticker, _direction, _action_entry)
    # Skip DB write, notification still fires
```
**Why 5%:** Matches A7's entry-proximity threshold for UPDATE→NEW detection. Board-scraped entries may have minor formatting discrepancies vs. DB entries. 5% is wide enough to account for rounding but narrow enough to distinguish distinct positions at different price levels.

**Why not exact match:** Board entries may be scraped as rounded values (e.g., `0.1234` vs DB `0.12340000`). Float comparison with tolerance is the established pattern in this codebase (A7 uses the same threshold).

**Event INSERT (revised — omit created_at, let column default handle ISO 8601):**
```sql
INSERT INTO signal_events (signal_id, event_type, payload, source)
SELECT ?, 'GHOST_CLOSURE', ?, 'signal_router'
WHERE NOT EXISTS (
    SELECT 1 FROM signal_events
    WHERE signal_id = ? AND event_type = 'GHOST_CLOSURE'
);
```

**Note append (revised — coupled to successful first-INSERT via `changes()`):**
```python
# Inside the same connection/transaction:
cursor.execute(event_insert_sql, params)
if cursor.connection.total_changes and conn.execute("SELECT changes()").fetchone()[0] > 0:
    # First insert succeeded — safe to append note exactly once
    cursor.execute(
        """UPDATE signals
           SET notes = CASE WHEN notes IS NULL THEN ? ELSE notes || ' ' || ? END,
               updated_at = strftime('%Y-%m-%dT%H:%M:%f','now')
           WHERE id = ? AND close_source IS NULL""",
        (note_tag, note_tag, sig_id),
    )
```
**Why `changes()` coupling:** This eliminates the TOCTOU gap between checking for existing events and appending notes. If the INSERT was a no-op (event already exists), `changes()` returns 0 and the note UPDATE is skipped. The note is written exactly once, on the same transaction as the first event INSERT. This addresses GUARDIAN's blocking concern #2.

**Why `CASE WHEN notes IS NULL`:** Avoids leading space when `notes` is NULL (per VIGIL suggestion #2 from R0 review).

No schema migration. No ALTER TABLE. No new columns.

---

## 6. Test Strategy

9 tests in `tests/test_a6_ghost_closure.py`:

| # | Test | Priority | What it proves |
|---|------|----------|----------------|
| 1 | `test_board_absent_close_emits_ghost_closure_event` | MUST | GHOST_CLOSURE event written with correct signal_id and payload |
| 2 | `test_board_absent_close_appends_ghost_note` | MUST | Notes field contains `[A6: ghost_closure absent_count=N]` |
| 3 | `test_board_absent_close_idempotent` | MUST | Max 1 GHOST_CLOSURE event AND max 1 note tag per signal_id across multiple absent cycles |
| 4 | `test_confirmed_close_not_tagged_ghost` | MUST | No GHOST_CLOSURE for non-board_absent closures (including cross-verified CLOSE without soft_close) |
| 5 | `test_ghost_close_skipped_when_no_active_signal` | MUST | No DB write + WARNING log when no matching signal exists |
| 6 | `test_ghost_closure_event_source_is_signal_router` | SHOULD | `source='signal_router'` in event row |
| 7 | `test_partially_closed_signal_gets_ghost_closure` | SHOULD | PARTIALLY_CLOSED signals are ghost-closure eligible |
| 8 | `test_entry_discriminator_selects_correct_signal` | MUST | When trader has 2 ACTIVE signals for same ticker+direction at different entries, GHOST_CLOSURE attaches to the entry-matched signal |
| 9 | `test_entry_outside_tolerance_skips_ghost_closure` | MUST | When reconciler entry doesn't match any DB signal within 5%, no DB write + WARNING log |

**Test approach:** Create an in-memory SQLite DB with signals/traders/signal_events tables (matching production schema including A1 columns: `field`, `old_value`, `new_value`, `source_msg_id`). Mock the signal_router's DB path to point at it. Simulate board_absent CLOSE actions by calling the instrumentation block directly (extracted helper or inline test). No need to instantiate the full SignalRouter — just the DB write logic.

**Test #8 specifically:** Insert two signals for the same trader+ticker+direction but at different entries (e.g., entry=100.0 and entry=200.0). Emit ghost closure with action entry=100.5 (within 5% of 100.0). Verify GHOST_CLOSURE attaches to signal with entry=100.0, not entry=200.0.

**Test #9 specifically:** Insert one signal with entry=100.0. Emit ghost closure with action entry=200.0 (100% deviation, far outside 5%). Verify no GHOST_CLOSURE event, no note append, WARNING logged.

---

## 7. Rollback Plan

1. `git revert <A6-commit>` in signal-gateway
2. Restart signal-gateway service
3. Optional cleanup:
   ```sql
   DELETE FROM signal_events WHERE event_type='GHOST_CLOSURE' AND source='signal_router';
   UPDATE signals SET notes = REPLACE(notes, ' [A6: ghost_closure absent_count=', '')
     WHERE notes LIKE '%ghost_closure%';  -- Note: REPLACE won't handle the trailing N], needs a migration script for exact cleanup
   ```
4. Zero data integrity risk — GHOST_CLOSURE events are additive metadata only

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| No matching ACTIVE/PARTIALLY_CLOSED signal at lookup time | Medium | None — skip + log | Guard with `if row is None: return` + WARNING |
| sqlite3 timeout (SQLITE_BUSY) | Low | None — notification still fires | try/except, non-fatal |
| False positive ghost closure (non-board_absent triggers) | Very Low | Low — spurious event | Strict `soft_close is True` guard |
| signal_events table missing (pre-A1 state) | Near Zero | None — try/except | A1 shipped and verified in production |

---

## 9. Scope Boundary

**In scope:**
- GHOST_CLOSURE event emission in `_route_board_update()`
- Note tag append
- 7 tests

**Out of scope:**
- Modifying reconciler.py
- Adding new columns to signals table
- Updating close_source on the signals row (downstream OinkDB handles this)
- signal_router.py refactoring (reserved for A8/B-phase God Object work)
- Backfill of historical ghost closures (no ghost closures exist in DB — nothing to backfill)

---

## 10. Canary Plan

**Type:** Passive observation (same as A4/A7 canaries — no active verification needed).

**Trigger:** First organic board_absent CLOSE after deploy.

**Verification query:**
```sql
SELECT se.signal_id, se.payload, se.created_at, s.ticker, s.notes
FROM signal_events se
JOIN signals s ON se.signal_id = s.id
WHERE se.event_type = 'GHOST_CLOSURE'
ORDER BY se.created_at DESC
LIMIT 10;
```

**Expected:** After first board_absent cycle post-deploy, at least 1 GHOST_CLOSURE row appears with valid payload containing `absent_count`, `trader`, `ticker`. The matching signal's notes contain `[A6: ghost_closure ...]`.

**Timeline:** Ghost closures are infrequent (depends on board activity and position disappearances). May take days to observe the first organic event. No rush — metadata-only impact.
