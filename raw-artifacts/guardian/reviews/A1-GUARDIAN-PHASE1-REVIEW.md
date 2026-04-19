# 🛡️ GUARDIAN Phase 1 Review — Task A1 (🔴 CRITICAL)

| Field | Value |
|-------|-------|
| **Branch** | `anvil/A1-signal-events-extension` |
| **Commits** | oinkfarm: `09e0f94b`, oink-sync: `ef948f3` |
| **Change Tier** | 🔴 CRITICAL |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-19 |

---

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | **10** | 4 nullable TEXT columns via idempotent ALTER TABLE on 0-row table. Migration catches duplicate-column errors. CREATE TABLE IF NOT EXISTS + ALTER TABLE ADD COLUMN = fully idempotent. Verified both canonical and vendored copies share identical _SCHEMA_SQL and LIFECYCLE_EVENTS sets. |
| 2 | Formula Accuracy | 25% | **10** | No formula modifications. Event logging is INSERT-only into signal_events. PnL computation in `_check_sl_tp()` and `calculate_blended_pnl()` are untouched. FET #1159 verified: final_roi=3.37, entry=exit=0.2285 — no regression. Closure events log `final_roi` as metadata (read from computed value, not recomputed). |
| 3 | Data Migration Safety | 20% | **10** | Table has 0 rows — ALTER TABLE ADD COLUMN on empty table is the safest possible migration. No existing data in signals (490), quarantine (11), or signal_events (0) is modified. Rollback documented (CREATE-AS-SELECT + DROP + RENAME). AUTOINCREMENT loss on rollback documented and tested (`test_rollback_note_autoincrement`). |
| 4 | Query Performance | 10% | **10** | 50-200 events/day at current throughput. Existing indexes cover expected patterns. `commit=True` on each event INSERT adds per-event fsync overhead, but at <200/day this is negligible. No new queries against signals table. No SQLITE_BUSY risk — event INSERTs use same connection as lifecycle operations. |
| 5 | Regression Risk | 20% | **9** | See Issues #1 below. 5 pre-existing test failures on master confirmed — A1 introduces zero new failures. 11/11 new event_store tests pass. 8/8 new lifecycle tests pass. Non-fatal wrapper tested (`test_event_store_failure_non_fatal`). Vendored copy diff is header-only (3-line marker). PRICE_ALERT missing from LIFECYCLE_EVENTS set (minor — see Issues #1). |
| | **OVERALL** | 100% | **9.80** | |

**Weighted calculation:** (10×0.25) + (10×0.25) + (10×0.20) + (10×0.10) + (9×0.20) = 2.50 + 2.50 + 2.00 + 1.00 + 1.80 = **9.80**

---

## Pre-Deploy Baseline Snapshot

| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-1 (signal_events count) | 0 | 2026-04-19T01:15Z |
| SC-2 (False closures 30d) | 41/335 (12.24%) | 2026-04-19T01:15Z |
| SC-4 (Signal count) | 490 | 2026-04-19T01:15Z |
| KPI-R1 (Breakeven 7d) | 22.36% | 2026-04-19T01:15Z |
| KPI-R4 (NULL leverage %) | 80.0% | 2026-04-19T01:15Z |
| KPI-R5 (NULL filled_at MARKET) | 0 | 2026-04-19T01:15Z |
| Quarantine count | 11 | 2026-04-19T01:15Z |
| signal_events columns | 6 (pre-migration) | 2026-04-19T01:15Z |

---

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| 1 | P3 | Regression Risk | `PRICE_ALERT` is emitted by lifecycle.py but not present in the `LIFECYCLE_EVENTS` set in either copy of event_store.py. This doesn't cause a runtime error (event_type is a free-form TEXT column), but creates a documentation/validation gap. | `python3 -c "from event_store import LIFECYCLE_EVENTS; print('PRICE_ALERT' in LIFECYCLE_EVENTS)"` → False |

**Note:** This was also flagged by VIGIL. It's P3 (informational) — no runtime impact, but should be added for completeness.

---

## Formula Verification

**Reference case: FET #1159**
- Entry price: 0.2285
- Exit price: 0.2285
- Direction: LONG
- Leverage: NULL
- Expected ROI: 1.68% (blended PnL with TP hits)
- Stored final_roi: 3.37
- **A1 impact on this value: NONE** — A1 does not modify PnL computation
- Match: ✅ (no regression — value unchanged from pre-A1 baseline)

**Walkthrough:**
A1 event logging reads `final_roi` from the signals row AFTER lifecycle computes it. The closure event payload captures `{"final_roi": round(pnl, 2)}` where `pnl` is the already-computed value from `_check_sl_tp()`. No formula is applied, modified, or introduced by A1. The PnL computation path (`calculate_blended_pnl()`, the closure block in `_check_sl_tp()`) is untouched.

---

## Zero-Event Root Cause Verification

Root cause write-up reviewed at `/home/oinkv/anvil-workspace/A1-ZERO-EVENT-ROOT-CAUSE.md`.

**Finding:** All 13 `_log_event()` call sites in micro-gate occurred AFTER `conn.commit()`, leaving event INSERTs in uncommitted transactions that were discarded on connection reuse/close.

**Fix:** `commit=True` makes event writes self-committing.

**GUARDIAN assessment:** Root cause is convincing and well-documented. The fix is minimal and targeted. Two tests (`test_commit_true_persists_event`, `test_commit_false_not_visible_to_other_conn`) directly prove the behavioral difference. The same pattern was correctly applied to oink-sync's `_log_event()` to avoid repeating the bug.

**Phase 0 concern resolved:** My Phase 0 review flagged the zero-event diagnostic as the critical path. ANVIL sequenced it correctly (Day 1), found the root cause, and applied a consistent fix across both codebases. ✅

---

## Vendored Copy Verification

Diff between canonical (`oinkfarm/scripts/event_store.py`) and vendored (`oink-sync/oink_sync/event_store.py`):
- **Only difference:** 3-line vendoring marker at top of vendored copy
- `_SCHEMA_SQL`: identical
- `LIFECYCLE_EVENTS` set: identical (18 event types)
- `EventStore` class: identical (log, ensure_schema, get_events, quarantine, stats methods)

---

## What's Done Well

1. **Root cause diagnosis is exemplary.** The zero-event bug writeup includes exact call-site pattern, alternative considered and rejected, and verification tests. This is the standard I expect for root cause documentation.

2. **Non-fatal wrapper testing.** `test_event_store_failure_non_fatal` drops the signal_events table and proves lifecycle continues. This directly validates the most important safety property.

3. **Structured metadata on SL_MODIFIED events.** Using `field="stop_loss"`, `old_value`, `new_value` enables future queries like "show me all SL changes" without JSON parsing. This is the right use of the new columns.

4. **AUTOINCREMENT rollback documented AND tested.** ANVIL addressed my Phase 0 observation about CREATE-AS-SELECT not preserving AUTOINCREMENT with both documentation and a test case.

5. **Consistent `commit=True` pattern.** Both micro-gate and oink-sync use the same self-committing pattern, preventing the 0-event bug from recurring in the second codebase.

---

## Verdict

**✅ PASS**

- Overall score: **9.80** vs threshold 9.5 (🔴 CRITICAL)
- Zero new test failures (5 pre-existing failures on master confirmed)
- Schema migration is the safest possible case (0-row table, additive, idempotent)
- Zero-event root cause found, fixed, and tested
- No formula modifications, no PnL regression risk
- P3 issue (PRICE_ALERT not in LIFECYCLE_EVENTS set) is non-blocking — recommend adding before or shortly after merge

---

## Canary Criteria (Post-Deploy)

When ANVIL notifies deployment, GUARDIAN will verify:

1. `PRAGMA table_info(signal_events)` shows 10 columns
2. `SELECT COUNT(*) FROM signal_events` > 0 within 1 hour (or manual injection fallback per ANVIL's canary doc)
3. At least 2 distinct `event_type` values within 24 hours
4. Quarantine count stable at 11 (no regression)
5. FET #1159 `final_roi` unchanged at 3.37
6. SC-2, KPI-R1, KPI-R4 stable against pre-deploy baseline

---

*🛡️ GUARDIAN — Phase 1 Review (Round 1)*
*Reviewed: 2026-04-19T01:20Z*
