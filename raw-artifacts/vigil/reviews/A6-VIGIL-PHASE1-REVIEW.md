# VIGIL Review — Task A6: Ghost Closure Confirmation Flag

**Branch:** anvil/A6-ghost-closure-flag
**Commits:** c6cb99e
**Change Tier:** 🟡 STANDARD
**Review Round:** 1
**Review Date:** 2026-04-19 15:10 CEST

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 9/10 | 0.30 | 2.70 | GHOST_CLOSURE event emission matches Phase 4 §2 / Phase 5 §BS-3. Correct instrumentation point in `_route_board_update()` CLOSE branch. `soft_close is True` identity check (line 3971). Idempotent INSERT with WHERE NOT EXISTS. Entry-price discriminator with 5% tolerance matching A7. Note append guarded by `close_source IS NULL`. Signal lookup includes PARTIALLY_CLOSED (A4-consistent). One minor gap: test schema missing 4 A1 columns (`field`, `old_value`, `new_value`, `source_msg_id`). |
| Test Coverage | 9/10 | 0.25 | 2.25 | 9 tests (7 MUST + 2 SHOULD) covering all 6 acceptance criteria. Tests verify: event emission, note append, idempotency (3 cycles), negative case (non-soft_close), no-match skip, source field, PARTIALLY_CLOSED eligibility, entry discriminator correctness, tolerance boundary. Test helper `_run_ghost_closure()` mirrors production SQL exactly. All 9 pass. Existing 23 test_reconciler.py tests unaffected. Minor gap: no explicit test for try/except non-fatal behavior (DB failure path). |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean implementation. `_a6_` prefix namespace prevents variable collision in the 4,375-LOC monolith — consistent with existing inline patterns. Clear section markers (`── A6:` / `── End A6 ──`). Appropriate log levels: INFO for first write, DEBUG for idempotent skip, WARNING for failures and no-match. `json.dumps` for payload. CASE WHEN for NULL-safe notes. Single connection/transaction per D6. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Pure `git revert` — single file change in signal_router.py. GHOST_CLOSURE events are additive metadata in signal_events (deletable). Note tags are appendable/strippable. No schema changes. No DDL. No destructive operations. Zero data integrity risk on rollback. |
| Data Integrity Impact | 9/10 | 0.15 | 1.35 | Additive metadata only — writes to signal_events (new rows) and signals.notes (append). Does NOT update close_source, status, entry_price, or any financial fields. Non-fatal wrapper ensures notification flow is never blocked. `changes()` coupling eliminates note duplication. Entry-price discriminator prevents misattribution to wrong signal. `close_source IS NULL` guard prevents tagging confirmed-closed signals. |
| **OVERALL** | | | **9.15** | |

## Issues Found

**MUST-FIX (blocks PASS):**
None.

**SHOULD-FIX (advisory, improves score):**
1. **Test schema missing A1 columns.** The test fixture `_SCHEMA` for `signal_events` is missing `field TEXT`, `old_value TEXT`, `new_value TEXT`, `source_msg_id TEXT` columns that exist in production (added by A1). While these columns are nullable and don't affect A6's INSERT, including them improves test fidelity and prevents future test failures if any downstream code assumes these columns exist. Add after `created_at`:
   ```sql
   , field TEXT, old_value TEXT, new_value TEXT, source_msg_id TEXT
   ```

**SUGGESTION (no score impact):**
1. **Explicit DB failure test.** Consider adding a test that forces a DB error (e.g., drop signal_events table before calling `_run_ghost_closure`) and verifies the function returns gracefully without raising. This would exercise the try/except path. Not blocking — the non-fatal wrapper is visible in the production diff and follows the established pattern.

## What's Done Well
- **Entry-price discriminator** with 5% tolerance is well-implemented — correctly handles the `ORDER BY id DESC` iteration (newest-first) with tolerance check, matching A7's established pattern.
- **`changes()` coupling** for note idempotency is elegant — eliminates TOCTOU entirely by gating the UPDATE on the INSERT's actual effect within the same transaction.
- **NULL-safe CASE WHEN** for notes avoids the leading-space issue I flagged in Phase 0 Suggestion #2.
- **Placement** of A6 block within the CLOSE branch is correct — sits between `board_counts["closures"] += 1` and the downstream `emitted_actions += 1` / `_queue_reconciler_action_notification()`, ensuring notification flow is never blocked regardless of A6 outcome.
- **Test #8 (entry discriminator)** is well-designed — inserts two signals at different entries and verifies the correct one is matched, including negative verification that the wrong signal has no event.
- **Idempotency test** (#3) runs 3 cycles and verifies both event count AND note count — thorough.
- **Variable namespacing** with `_a6_` prefix is disciplined and consistent with the monolith's existing patterns.

## Verdict: ✅ PASS

**Overall score 9.15 ≥ 9.0 (STANDARD threshold).** Implementation faithfully matches the Phase 0 approved proposal. All Phase 1 verification points from the approval marker are satisfied:

| Checkpoint | Status |
|------------|--------|
| `soft_close is True` identity check | ✅ Line 3971 |
| `INSERT...WHERE NOT EXISTS` idempotency | ✅ Lines 4025–4031 |
| `close_source IS NULL` guard on note | ✅ Line 4039 |
| `created_at` omitted (column default) | ✅ INSERT only specifies signal_id, event_type, payload, source |
| try/except non-fatal wrapper | ✅ Lines 3979–4056 |
| `status IN ('ACTIVE', 'PARTIALLY_CLOSED')` | ✅ Line 3988 |
| Entry-price discriminator (5% tolerance) | ✅ Lines 3993–4003 |
| `changes()` coupling for note | ✅ Line 4033 |
| 9/9 tests pass | ✅ Verified |
| 23/23 existing reconciler tests pass | ✅ Verified |

Proceed to GUARDIAN review.
