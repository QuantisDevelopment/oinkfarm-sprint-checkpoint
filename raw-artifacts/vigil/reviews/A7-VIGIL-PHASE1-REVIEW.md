# VIGIL Review — Task A7: UPDATE→NEW Detection (Phantom Trade Prevention)

**Branch:** anvil/A7-update-detected-guard
**Commit:** 2036f097
**Change Tier:** 🔴 CRITICAL (Financial Hotpath #6 — micro-gate INSERT logic)
**Review Round:** 1
**Review Date:** 2026-04-19 13:15 UTC

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | Exact match to approved Phase 0 proposal. Guard placed between step 14 (line 832) and step 16 (line 895). 5% threshold with `>` operator (≤5% suppress, >5% allow). `ticker_only` included per §2C. Zero-entry fallthrough allows INSERT. `notes` string append (not `notes_parts`). All 4 status IN clauses broadened. `UPDATE_DETECTED` in LIFECYCLE_EVENTS, `A7_UPDATE_DETECTED` in QUARANTINE_CODES. All Phase 0 suggestions addressed. |
| Test Coverage | 10/10 | 0.25 | 2.50 | 20 tests (vs 12 minimum). 7 MUST + 8 SHOULD + 3 ZERO + 1 GUARDIAN + 1 COMPLEMENTARY. Covers: suppress at 0.3%/1%/5%, allow at 5.01%/7.7%, no-existing, opposite direction, PENDING/PARTIALLY_CLOSED match, event logged with payload verification, rejection logged with reason check, trader_id=None bypass, ticker_only suppression, ambiguous allows, notes annotation, zero-entry edge cases, §4b exact-match layering. Assertions are specific (action, signal_id, price_diff_pct, payload fields). |
| Code Quality | 10/10 | 0.15 | 1.50 | 40 lines of guard logic — clean, well-commented, consistent with existing micro-gate patterns. Named constant `_A7_ENTRY_TOLERANCE_PCT`. Clear branching: suppress → rejection + event + return; allow → notes annotation + fall-through. Uses module-level `_log_event` helper (not inline import). `conn=conn` on `_log_rejection` for quarantine. Schema compat fixes in existing tests are minimal and additive. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | No schema changes, no DDL, no data modifications. Rollback: `git revert 2036f097` + service restart. Suppressed signals were never inserted — no recovery needed. Status IN broadenings are backward-compatible (PARTIALLY_CLOSED rows didn't exist in micro-gate queries before). |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Purely defensive — prevents phantom INSERTs, never modifies existing data. Full audit trail: UPDATE_DETECTED event on existing signal's ID + A7_UPDATE_DETECTED quarantine entry + gate-rejections.jsonl line. Genuine new positions get A7 notes annotation preserving audit trail. §4b exact-match layer unmodified and complementary. |
| **OVERALL** | | | **10.00** | |

## Issues Found

**MUST-FIX (blocks PASS):**

*(none)*

**SHOULD-FIX (advisory):**

*(none)*

**SUGGESTION (no score impact):**

1. **`_A7_ENTRY_TOLERANCE_PCT` placement:** Currently defined inside the `if` block at line 841 (recreated every call). Consider moving to module-level constant for consistency with other thresholds in the file and easier override if the 48h monitoring period suggests adjusting the value. Not a correctness issue.

## What's Done Well

- **Surgical implementation.** 40 lines of guard logic, 4 single-line status IN changes, 2 registry additions. No unnecessary refactoring, no scope creep. The smallest possible change to close the phantom trade gap.

- **Defense-in-depth layering is explicit.** The `test_exact_entry_caught_by_4b` test verifies that §4b (exact match) fires before A7 (fuzzy match), documenting the two-layer architecture within micro-gate.

- **Test suite exceeds requirements.** 20 tests vs 12 minimum. The GUARDIAN-1 test (`test_update_partially_closed_ticker_only_flags`) addresses GUARDIAN's cross-concern about UPDATE handler behavior. The ZERO-1/2/3 tests address VIGIL's Phase 0 suggestion about zero-entry fallthrough.

- **Schema compat fixes in existing tests.** The `traders` DDL addition to `test_micro_gate_filled_at.py` and `traders` + `signal_events` DDL to `test_micro_gate_source_url.py` are forward-looking — they prevent breakage as micro-gate accumulates more cross-table queries. These are the right fixes to make alongside A7.

- **All OinkV audit items incorporated.** STALE-A7-1 (line numbers), STALE-A7-2 (module-level helper), STALE-A7-3 (registry), STALE-A7-4 (`conn=conn`), MINOR-A7-5 (§4b acknowledgment), MINOR-A7-6 (`notes` string), MINOR-A7-7 (`ticker_only` precedent), MINOR-A7-8 (all 3+1 status IN clauses).

## Verdict: ✅ PASS

Overall score **10.00** meets the 🔴 CRITICAL threshold of ≥9.5. No issues found. Implementation is production-ready.

Forward to GUARDIAN for data-focused review.

---

*VIGIL 🔍 — Phase 1 Review for A7*
*2026-04-19*
