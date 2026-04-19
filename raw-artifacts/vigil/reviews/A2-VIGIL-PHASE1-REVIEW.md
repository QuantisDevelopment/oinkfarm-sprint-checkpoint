# VIGIL Review — Task A2: remaining_pct Model + Partial-Close PnL Accuracy

**Branch:** anvil/A2-remaining-pct-blended-pnl
**Commits:** 277a18f
**Change Tier:** 🔴 CRITICAL (Financial Hotpath #1 — calculate_blended_pnl())
**Review Round:** 1
**Review Date:** 2026-04-19 02:30 UTC

---

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | All 5 Phase 4 remaining_pct spec points implemented exactly: close_pct capture via default table with alloc_source flag, remaining_pct decrement with clamping, TP_HIT event payload with all 4 required fields, backward-compatible calculate_blended_pnl() rewrite, and fallback path for pre-A2 signals. FET #1159 math verified: 25% close → 1.68%, 50% close → 3.37%, None → 3.37% (legacy). |
| Test Coverage | 10/10 | 0.25 | 2.50 | 29 new tests covering all 8 acceptance criteria (AC1–AC8). FET #1159 regression (3 tests), backward compat (3 tests), multi-TP + SHORT (3 tests), edge cases incl. underflow clamping and zero entry price (4 tests), default fractions (3 tests), schema migration (3 tests), TP_HIT event enrichment (4 tests), gap-past-multiple-TPs (2 tests), remaining_pct=0 boundary (1 test), E2E lifecycle insert→TP→SL→final_roi (2 tests), pre-A2 migration (1 test). All 45 tests pass (29 A2 + 8 A1 + 8 yfinance). Phase 0 suggestion for E2E integration test was implemented. |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean 2-file change, no unrelated files (improvement over A1). Well-structured: default table as module-level constant, helper function `_default_close_fraction()`, `_collect_tp_close_pcts()` factored out. Comments explain "why" (MUST-FIX references, backward compat rationale). Two minor issues: (1) misleading docstring in `ensure_remaining_pct_column()` claims SQLite doesn't backfill existing rows with DEFAULT — it does (verified); (2) log.info mixes eager `%` formatting with lazy logging args. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Purely additive schema change: ALTER TABLE ADD COLUMN remaining_pct REAL DEFAULT 100.0. SQLite cannot DROP COLUMN but column is harmless if left. Functional rollback: revert lifecycle.py → remaining_pct ignored, legacy fixed-weight path resumes. No existing data modified. No destructive operations. |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Zero corruption risk. remaining_pct UPDATE in SAME SQL statement as tp_hit_at (not in event try/except — correct transaction scope). Re-reads remaining_pct before closure to handle same-cycle TP+SL. `_collect_tp_close_pcts()` wrapped in try/except (non-fatal). Empty dict → None conversion ensures pre-A2 signals get legacy path. NULL remaining_pct from pre-ALTER signals would also work correctly (though SQLite actually backfills DEFAULT). |
| **OVERALL** | | | **9.85** | |

---

## Issues Found

**MUST-FIX (blocks PASS):**

*(none)*

**SHOULD-FIX (advisory, improves score):**

1. **Misleading docstring in `ensure_remaining_pct_column()`** — The docstring says "NOTE: SQLite ALTER TABLE ADD COLUMN ... DEFAULT does NOT backfill existing rows — they get NULL." This is incorrect. SQLite DOES backfill existing rows with the DEFAULT value (verified independently: pre-existing row gets 100.0 after ALTER). ANVIL's own review request message acknowledges this ("Verified — SQLite DOES backfill"). The docstring should be corrected to match reality. The code behavior is correct regardless — the legacy path triggers on empty `tp_close_pcts`, not on NULL `remaining_pct`.

2. **Proposal §5 table vs code discrepancy for 1-TP signals** — The proposal table says "1 TP defined: TP1 closes 100%" but the code uses `{1: 0.5}` (50%). The code is correct — it preserves the legacy behavior where 1-TP signals use 50% weight at TP1 and 50% at exit price. The proposal table should be corrected. This is a documentation issue only; the implementation and tests are consistent.

**SUGGESTION (no score impact):**

1. **Log formatting consistency** — The log.info line at ~L648 mixes eager `%` formatting (for the optional remaining_pct suffix) with lazy log.info formatting. Consider using an f-string or fully lazy formatting for consistency.

---

## What's Done Well

- **Backward compatibility design is excellent.** The dual-path approach (event-sourced when `tp_close_pcts` is non-empty, legacy when empty/None) is clean and well-tested. The `or None` conversion on line 452 (`self._collect_tp_close_pcts(conn, sig_id) or None`) is a nice touch — empty dict becomes None, ensuring pre-A2 signals always get legacy behavior.

- **Transaction safety for remaining_pct.** The remaining_pct UPDATE is in the SAME SQL statement as tp_hit_at, not in the event try/except. This is the correct lesson from A1's zero-event root cause: remaining_pct is a signal mutation, not an audit log entry.

- **Gap-past-multiple-TPs handling.** The `run_remaining` variable correctly tracks sequential decrements within a single cycle, so a price gap from below TP1 to above TP3 produces the correct 100→50→25→0 sequence.

- **Re-read of remaining_pct before closure.** Line ~443 re-reads from DB before calling `calculate_blended_pnl()` to capture updates from `_process_tp_hits()` in the same cycle. This prevents stale-data PnL errors.

- **Clean branch.** Only 2 files changed, both directly relevant. No unrelated changes (yfinance issue from A1 not repeated).

- **Phase 0 suggestions implemented.** Both E2E lifecycle tests and the remaining_pct=0 boundary test were suggested in the Phase 0 review and are present.

- **All 8 acceptance criteria tested** with specific, meaningful assertions (not just "no exception thrown"). FET #1159 tested at three remaining_pct values with precise expected ROIs.

---

## Verdict: ✅ PASS

**Overall score: 9.85/10** — exceeds 🔴 CRITICAL threshold (≥9.5).

Clean, well-tested implementation of the remaining_pct model. Backward compatibility is proven by both unit tests and E2E lifecycle tests. Transaction safety is correct. The two SHOULD-FIX items are documentation corrections that don't affect runtime behavior.

Ready for GUARDIAN review.
