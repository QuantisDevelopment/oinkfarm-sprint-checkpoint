# VIGIL Proposal Review — A6: Ghost Closure Confirmation Flag

**Verdict:** ✅ **APPROVE**

**Task:** A6 — Ghost Closure Confirmation Flag
**Proposal:** `/home/oinkv/anvil-workspace/proposals/A6-PHASE0-PROPOSAL.md`
**FORGE plan:** `/home/oinkv/forge-workspace/plans/TASK-A6-plan.md` (v1.0)
**Reviewer:** VIGIL 🔍
**Review date:** 2026-04-19 14:27 CEST
**Tier:** 🟡 STANDARD

---

## Spec Alignment

**Assessment: ALIGNED** ✅

The proposal correctly implements Phase 4 §2 (Signal Lifecycle Accuracy) and Phase 5 §BS-3 (Ghost Closure Auditing). Verified against source code at signal-gateway commit `38eb8e8`:

1. **Reconciler board_absent CLOSE logic verified.** Two code paths at reconciler.py lines 260–275 and 333–345 both emit `soft_close=True` with `absent_count` in detail dict. The proposal correctly identifies these as the trigger points and correctly does NOT modify reconciler.py.

2. **signal_router.py `_route_board_update()` confirmed as correct instrumentation target.** Lines 3869–3975: the CLOSE branch currently does `board_counts["closures"] += 1` and calls `_queue_reconciler_action_notification()` — no DB write. The proposal adds DB instrumentation at exactly the right point.

3. **Existing inline sqlite3 pattern verified.** Lines 3907–3921 use the exact pattern the proposal describes: `import sqlite3 as _sq3`, `os.environ.get("OINKFARM_DB", ...)`, `_sq3.connect(_DB, timeout=2)`, try/except wrapper. The proposal's approach is consistent with the existing codebase.

4. **`GHOST_CLOSURE` confirmed in LIFECYCLE_EVENTS.** event_store.py line 71. No changes to event_store.py needed — correct.

5. **No Financial Hotpath involvement.** signal_router.py contains zero references to `calculate_blended_pnl`, `_check_sl_tp`, `close_signal`, `update_sl`, or `remaining_pct`. Zero `UPDATE signals` statements exist in this file. The proposed change writes to `signal_events` (metadata) and appends to `signals.notes` (cosmetic). No financial path impact. Stays 🟡 STANDARD.

6. **No schema changes.** `signal_events` table already exists (A1). `close_source` column already exists. No DDL needed. This is purely additive instrumentation.

7. **D1 (inline sqlite3 vs event_store import) is sound.** signal_router.py is in the signal-gateway repo; event_store.py is in oink-sync/oinkfarm. Importing across repos would create a cross-module dependency in a 4,375-LOC monolith. The inline pattern is already established at lines 3907–3921.

8. **D2 (INSERT...WHERE NOT EXISTS idempotency) is sound.** First-event-wins is the correct semantic — subsequent absent snapshots don't add information. The SQL is correct.

9. **D3 (note append guarded by `close_source IS NULL`) is sound.** Verified: signal_router.py has zero references to `close_source` and zero `UPDATE signals` statements. At the time A6's instrumentation runs, the signal's `close_source` will indeed be NULL for genuine ghost closures. Signals already closed via confirmed sources (sl_hit, pilot_closure, etc.) will be correctly excluded.

10. **D4 (PARTIALLY_CLOSED in signal lookup) is correct.** Matches A4 broadening pattern. A partially-closed signal that disappears from the board is still a ghost closure.

11. **D5 (new test file `test_a6_ghost_closure.py`) overrides FORGE plan §5** which says `test_reconciler.py`. The proposal's reasoning is correct — different SUT (signal_router instrumentation vs Reconciler class), different file. Consistent with A1/A4/A5/A7 naming convention.

---

## Acceptance Criteria Coverage

**Assessment: WELL COVERED** ✅

| AC # | Criterion | Test(s) Covering It | Adequate? |
|------|-----------|-------------------|-----------|
| 1 | GHOST_CLOSURE event written after board_absent CLOSE | `test_board_absent_close_emits_ghost_closure_event` (MUST) | ✅ |
| 2 | Notes field contains `[A6: ghost_closure absent_count=N]` | `test_board_absent_close_appends_ghost_note` (MUST) | ✅ |
| 3 | Max 1 GHOST_CLOSURE event per signal_id | `test_board_absent_close_idempotent` (MUST) | ✅ |
| 4 | Non-fatal: DB failure doesn't block notification | `test_ghost_close_skipped_when_no_active_signal` (MUST) | ✅ |
| 5 | Post-deploy verification query produces results | Canary plan §10 | ✅ |
| 6 | All existing test_reconciler.py tests pass | Regression gate | ✅ |

Additional coverage:
- `test_confirmed_close_not_tagged_ghost` (MUST) — false positive prevention
- `test_ghost_closure_event_source_is_signal_router` (SHOULD) — source field verification
- `test_partially_closed_signal_gets_ghost_closure` (SHOULD) — A4 interaction

7 tests (5 MUST + 2 SHOULD) covering 6 acceptance criteria. Thorough.

---

## Concerns

**None blocking approval.** Two implementation notes for Phase 1:

### ⚠️ Note 1: `created_at` format inconsistency in proposed SQL

The proposal's event INSERT SQL (§5) explicitly sets `created_at = datetime('now')`, which produces `YYYY-MM-DD HH:MM:SS`. However, the production `signal_events.created_at` column default uses `strftime('%Y-%m-%dT%H:%M:%f','now')`, producing `YYYY-MM-DDTHH:MM:SS.SSS` (ISO 8601 with milliseconds and T separator).

**Recommendation for Phase 1:** Either:
- **Option A (preferred):** Omit `created_at` from the INSERT, letting the column default handle the format — consistent with all existing events.
- **Option B:** Use `strftime('%Y-%m-%dT%H:%M:%f','now')` explicitly if the INSERT must specify the value.

This is a minor format consistency issue — not spec-breaking — but VIGIL will check for it in Phase 1 review.

### ⚠️ Note 2: FORGE plan schema simplification

The FORGE plan §4e shows a simplified `signal_events` schema missing columns (`field`, `old_value`, `new_value`, `source_msg_id`) and using different defaults. The proposal's INSERT doesn't reference these columns, so this is harmless — but ANVIL should be aware the production schema is richer than the plan shows. The `payload NOT NULL DEFAULT '{}'` constraint means the INSERT MUST include a payload value (not NULL).

---

## Suggestions

1. **Test 4 (`test_confirmed_close_not_tagged_ghost`):** The test description says "cross-verified" closure, but the guard in code is `soft_close is True`. Consider also testing the inverse: a CLOSE action *without* `soft_close` in detail (e.g., a normal reconciler CLOSE from cross-verification) should NOT emit GHOST_CLOSURE. This might be implicitly covered, but an explicit negative test would be clearer.

2. **Note append atomicity:** The `COALESCE(notes, '') || ' [A6: ...]'` pattern always prepends a space. If `notes` is NULL, the result starts with a space: `' [A6: ...]'`. Consider `CASE WHEN notes IS NULL THEN '[A6: ...]' ELSE notes || ' [A6: ...]' END` — or just accept the leading space as cosmetic. Not a spec issue.

3. **Repo context for tests:** Since A6 targets signal-gateway (not oinkfarm/.openclaw/workspace), ensure the test DB fixture matches the production `signal_events` schema including the A1-added columns (`field`, `old_value`, `new_value`, `source_msg_id`), not the simplified FORGE schema.

---

## Phase 1 Notes for VIGIL

When reviewing the Phase 1 code submission:

- **Tier:** 🟡 STANDARD (no Financial Hotpath involvement confirmed)
- **Threshold:** ≥9.0 overall
- **Repo:** signal-gateway (bandtincorporated8/signal-gateway), NOT oinkfarm
- **Key verification points:**
  - `soft_close is True` guard strictly checked (not truthy, not `== True`, use `is True` or explicit check)
  - `INSERT...WHERE NOT EXISTS` idempotency guard present
  - `close_source IS NULL` guard on note append
  - `created_at` either omitted (column default) or uses `strftime('%Y-%m-%dT%H:%M:%f','now')` — NOT `datetime('now')`
  - try/except wrapper around entire DB write block; notification fires regardless
  - `status IN ('ACTIVE', 'PARTIALLY_CLOSED')` in signal lookup
  - All 7 tests pass; all existing test_reconciler.py tests pass unmodified

---

**Verdict: ✅ APPROVE**

The proposal is well-grounded in source code evidence. The instrumentation point is correct (`_route_board_update()` CLOSE branch), the approach is minimal and consistent with existing patterns (inline sqlite3, non-fatal wrapper), and the test strategy covers all 6 acceptance criteria with 7 tests. No schema changes, no Financial Hotpath involvement, clean rollback. The two notes above are implementation-level details for VIGIL to check in Phase 1, not proposal blockers.

Proceed to Phase 1 implementation (pending GUARDIAN approval).

---

*VIGIL 🔍 — Phase 0 Review*
*2026-04-19 14:27 CEST*
