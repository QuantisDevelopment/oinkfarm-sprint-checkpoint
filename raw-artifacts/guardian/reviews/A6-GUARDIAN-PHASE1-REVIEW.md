# 🛡️ GUARDIAN Phase 1 Review — A6: Ghost Closure Confirmation Flag

| Field | Value |
|---|---|
| Branch | `anvil/A6-ghost-closure-flag` |
| Commit | `c6cb99e` |
| Repo | `bandtincorporated8/signal-gateway` |
| Change Tier | 🟡 STANDARD |
| Review Round | Round 1 |
| Review Date | 2026-04-19 |
| PR | `#20` |

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|---|---:|---:|---|
| 1 | Schema Correctness | 25% | 10 | No DDL, no schema mutation, no new columns, no migration logic. `GHOST_CLOSURE` writes into the existing `signal_events` model only. |
| 2 | Formula Accuracy | 25% | 10 | No PnL, ROI, leverage, TP, SL, or lifecycle formula changes. FET #1159 remains intact. |
| 3 | Data Migration Safety | 20% | 10 | Zero backfill, zero destructive writes, zero schema touch. `close_source` is preserved and not overwritten. Rollback is trivial: git revert and optional delete of additive `GHOST_CLOSURE` rows if ever needed. |
| 4 | Query Performance | 10% | 10 | One bounded lookup on soft-close path only: `signals JOIN traders`, filtered by trader/ticker/direction/status and resolved by short Python tolerance scan. Low write volume, no new contention pattern, timeout=2 is non-fatal. |
| 5 | Regression Risk | 20% | 9 | Implementation satisfies all Phase 0 blockers and required checks. 9/9 A6 tests pass, 23/23 reconciler tests pass. Minor deduction: the dedicated A6 test file mirrors the inline DB path via helper instead of driving the full async router path end-to-end. Data semantics are still well covered. |
|  | **OVERALL** | 100% | **9.80** | |

**Weighted score:** `(10×0.25) + (10×0.25) + (10×0.20) + (10×0.10) + (9×0.20) = 9.80`

## Verification Checklist

### 1. Event INSERT + note UPDATE in ONE transaction
**VERIFIED ✅**
- Diff confirms both operations occur inside a single `with _sq3.connect(_DB, timeout=2) as _a6conn:` block in `signal_router.py`.
- INSERT executes first, then `SELECT changes()` gates the note UPDATE.
- Exception handling wraps the whole block and logs warning without crashing the hot path.

### 2. WARNING-path observability for no-match cases
**VERIFIED ✅**
- Warning log exists:
  - `"[router] A6: ghost_closure — no entry-matched signal for %s/%s/%s entry=%.4f (candidates=%d)"`
- The log carries trader, ticker, direction, entry, and candidate count, which is sufficient for post-deploy audit.

### 3. `close_source` preserved unchanged for provisional ghost closures
**VERIFIED ✅**
- No `close_source` write exists anywhere in the A6 diff.
- The note UPDATE is explicitly guarded with `WHERE id = ? AND close_source IS NULL`, which preserves confirmed-close rows.

### 4. 5% entry tolerance applied exactly as proposed
**VERIFIED ✅**
- Matching logic in `signal_router.py`:
  - `_a6_dev = abs(_a6_db_entry - _a6_action_entry) / _a6_action_entry`
  - `if _a6_dev <= 0.05:`
- This is the proposed exact tolerance behavior.

### 5. Tests cover BOTH multi-match selection and no-match skip branches
**VERIFIED ✅**
- `test_entry_discriminator_selects_correct_signal` covers multi-match resolution.
- `test_entry_outside_tolerance_skips_ghost_closure` covers no-match skip.
- `test_ghost_close_skipped_when_no_active_signal` adds an additional no-eligible-row branch.

## Test Evidence

### Requested test suites
```bash
python3 -m pytest tests/test_a6_ghost_closure.py -v
python3 -m pytest tests/test_reconciler.py -v
```

### Results
- `tests/test_a6_ghost_closure.py`: **9 / 9 passed**
- `tests/test_reconciler.py`: **23 / 23 passed**

### Notable covered behaviors
- event emitted on board-absent soft close
- note tag appended exactly once
- idempotent repeat absent cycles
- confirmed non-soft closes do not get tagged
- no-match path skips writes
- `PARTIALLY_CLOSED` is eligible
- multi-position selection uses entry discrimination correctly
- outside-tolerance case skips cleanly

## Diff Review Notes

Primary implementation added to:
- `scripts/signal_gateway/signal_router.py`
- `tests/test_a6_ghost_closure.py`

Confirmed implementation properties:
- gated on `detail.soft_close is True`
- signal lookup includes `status IN ('ACTIVE', 'PARTIALLY_CLOSED')`
- lookup ordered `ORDER BY s.id DESC`, then resolved with entry-price tolerance
- idempotent event write via `INSERT ... WHERE NOT EXISTS`
- note append coupled to successful first insert via `SELECT changes()`
- note tag format: `[A6: ghost_closure absent_count=N]`
- exception path logs warning and preserves router continuity

## FET #1159 Reference Case

**Reference query result:**

| id | ticker | direction | entry_price | exit_price | leverage | final_roi | status | remaining_pct |
|---:|---|---|---:|---:|---|---:|---|---:|
| 1159 | FET | LONG | 0.2285 | 0.2285 | NULL | 3.37 | CLOSED_WIN | 100.0 |

**Assessment:** ✅ unchanged

A6 is additive metadata only and does not alter lifecycle math, ROI computation, remaining_pct handling, or close-state formulas.

## Pre-Deploy Baseline Snapshot

| Metric | Current Value |
|---|---:|
| SC-1 total signal_events | 312 |
| SC-1 distinct signals with events | 25 |
| SC-2 false closure rate | 11.8841% |
| SC-4 total signals | 493 |
| KPI-R1 breakeven 7d | 20.4167% |
| KPI-R4 NULL leverage | 80.1217% |
| KPI-R5 FILLED MARKET with NULL filled_at | 0 |
| KPI-R3 duplicate discord_message_id groups | 14 |

Expected A6 impact: no change to SC-2, KPI-R1, KPI-R4, KPI-R5, or KPI-R3. Only additive audit metadata should appear on future organic ghost-closure events.

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|---|---|---|---|
| 1 | P3 | Regression Risk | Dedicated A6 tests mirror the inline DB logic with a helper rather than invoking the full async router path end-to-end. | `tests/test_a6_ghost_closure.py` structure |

**No P1 or P2 issues found.**

## What’s Done Well

- Phase 0 ambiguity around multi-position matching is properly resolved.
- Idempotency boundary is correct: note append only occurs when the event insert is new.
- `close_source` remains untouched, preserving the provisional nature of the marker.
- Warning-path observability is strong enough for field debugging.
- Scope is disciplined: no DDL, no migration, no financial hotpath mutation.

## Verdict

**PASS ✅**

- Overall score: **9.80 / 10**
- Threshold for 🟡 STANDARD: **≥ 9.0**
- No blocking data-safety issues remain.
- Safe to merge from GUARDIAN’s data perspective.

## Post-Deploy Verification Note

No formal canary is required. This task is additive metadata only.

Recommended lightweight verification after deployment:
1. wait for first organic board-absent soft close
2. confirm exactly one `GHOST_CLOSURE` event on the matched signal
3. confirm exactly one `[A6: ghost_closure ...]` note tag
4. confirm no `close_source` overwrite occurred

---

*🛡️ GUARDIAN — Data Safety / Formula Accuracy / Migration / Performance / Regression Review*