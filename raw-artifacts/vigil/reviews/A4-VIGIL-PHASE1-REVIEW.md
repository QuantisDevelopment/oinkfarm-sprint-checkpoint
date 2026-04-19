# VIGIL Review — Task A4: PARTIALLY_CLOSED Status

**Branch:** anvil/A4-partially-closed-status
**Commit:** ab5d941
**Change Tier:** 🔴 CRITICAL (Financial Hotpath #1, #2, #5)
**Review Round:** 1
**Review Date:** 2026-04-19 12:40 UTC

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | All 10 modification sites match Phase 0 approved approach exactly. Same-cycle closure (DQ-A4-2) properly implemented. STATUS_CHANGED dedup via pre-read. LIFECYCLE_EVENTS hygiene entry added. Deferred consumers (oinkdb-api, signal-gateway) properly documented with follow-up task IDs. Phase 4 §2 PARTIALLY_CLOSED status addition fully realized. |
| Test Coverage | 9/10 | 0.25 | 2.25 | 21 new tests covering all 9 acceptance criteria. All MUST-priority tests present. Happy path, edge cases (gap-past-all-TPs, 2-TP variant, two-cycle TP→SL sequence), regression guards, and engine.py tests included. SHOULD-FIX: `test_sl_proximity_includes_partially_closed` doesn't assert the signal appears in the returned alerts list — it verifies the query and that the function runs, but the assertion is weaker than other monitoring tests. |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean structure. Same-cycle closure path well-commented with DQ-A4-2 reference. STATUS_CHANGED dedup logic clear. `current_status` variable threaded through correctly. Minor: same-cycle closure re-queries `posted_at` via separate SELECT (L626) while the SL closure path reuses `row[15]` from the original fetch (L470) — functional but inconsistent. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Purely additive: no schema changes, no DDL. Rollback is one SQL UPDATE (`SET status='ACTIVE' WHERE status='PARTIALLY_CLOSED'`) + code revert. STATUS_CHANGED events remain in append-only audit log (correct). Backfill procedure includes explicit transaction, abort threshold (>4 rows), and anomaly check. |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | All 10 monitoring sites broadened — no PARTIALLY_CLOSED signal can be orphaned from price tracking, PnL calculation, SL/TP monitoring, SL proximity alerts, or price history. E5 fix prevents silent PnL zeroing. Same-cycle closure uses event-sourced `tp_close_pcts` with current TP's `close_pct` correctly added before `calculate_blended_pnl()` call. Events committed with `commit=True` ensures `_collect_tp_close_pcts` reads TP1/TP2 events at TP3. |
| **OVERALL** | | | **9.60** | |

## Issues Found

**MUST-FIX (blocks PASS):**

*(none)*

**SHOULD-FIX (advisory, improves score):**

1. **`test_sl_proximity_includes_partially_closed` weak assertion** — `tests/test_partially_closed.py:400-410`: The test verifies the signal exists in DB and the function runs without error, but doesn't assert the signal appears in the returned `alerts` list (or at minimum that the function processed it). Other monitoring tests (`test_price_history_includes_partially_closed`, `test_partially_closed_monitored_in_next_cycle`) have stronger assertions that verify actual output. Strengthening this would bring Test Coverage to 10.

2. **`posted_at` re-query in same-cycle closure** — `lifecycle.py:625-627`: The same-cycle closure path does `conn.execute("SELECT posted_at FROM signals WHERE id=?", (sig_id,))` while the SL closure path 55 lines earlier uses `row[15]` from the original `_check_sl_tp()` SELECT (which already fetches `posted_at`). The `posted_at` value is available in the original row — passing it through `_process_tp_hits()` would avoid the extra query and be consistent with the existing pattern.

**SUGGESTION (no score impact):**

1. **`test_no_status_changed_on_same_cycle_close` assertion clarity** — The test asserts `len(sc_events) <= 1` with a comment explaining TP1's STATUS_CHANGED fires before TP3 closes. Consider asserting `== 1` (not `<= 1`) since for a 3-TP gap-past scenario, exactly 1 STATUS_CHANGED should always fire (ACTIVE→PARTIALLY_CLOSED on TP1). The `<= 1` is technically correct but less precise.

## What's Done Well

- **Blast radius analysis is exemplary.** ANVIL found 10 sites across 2 files (5 lifecycle.py + 5 engine.py), exceeding FORGE's initial 3. The E5 `_calculate_pnl()` fix is particularly important — without it, engine.py would fetch PARTIALLY_CLOSED rows but silently return `None` for their PnL, a data integrity failure that would be difficult to diagnose in production.

- **Same-cycle closure (DQ-A4-2) is well-engineered.** The `_collect_tp_close_pcts` + current TP addition pattern correctly assembles the full allocation dict before calling `calculate_blended_pnl()`. The `break` after closure prevents further TP processing on a closed signal.

- **STATUS_CHANGED dedup is clean.** Using `current_status == "ACTIVE"` pre-read with in-memory update (`current_status = "PARTIALLY_CLOSED"`) after emission is the right pattern — no risk of duplicate events even when multiple TPs hit in one cycle.

- **Deferred consumer documentation** (A4-F1, A4-F2) with clear rationale for deferral is good engineering practice. The signal-gateway deferral to A7 avoids redundant work.

- **Test suite is comprehensive** — 21 tests with a good mix of unit, integration, and regression guards. The two-cycle `test_single_tp_hit_then_sl_closure` test is particularly valuable as an E2E lifecycle verification.

## Verdict: ✅ PASS

Overall score **9.60** meets the 🔴 CRITICAL threshold of ≥9.5. No MUST-FIX issues. The 2 SHOULD-FIX items are genuine improvements but do not affect correctness or data integrity. Implementation is production-ready.

Forward to GUARDIAN for data-focused review.

---

*VIGIL 🔍 — Phase 1 Review for A4*
*2026-04-19*
