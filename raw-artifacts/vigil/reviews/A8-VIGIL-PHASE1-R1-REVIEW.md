# VIGIL Review — Task A8: Conditional SL Type Field

**Branch:** `anvil/A8-conditional-sl-type`
**Commit:** `a3eaa87e`
**Change Tier:** 🟡 STANDARD
**Review Round:** 1
**Review Date:** 2026-04-19 17:20 UTC

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 9/10 | 0.30 | 2.70 | 4-value taxonomy (FIXED/CONDITIONAL/MANUAL/NONE) matches Phase 4 §3 + BS-6. Shared `_CONDITIONAL_SL_KEYWORDS` tuple at module level (line 131) eliminates keyword duplication per FORGE §4d. sl_type set after all SL processing (Section 8d-A8, line 832) reads final `stop_loss` + `_sl_is_conditional` state. MANUAL correctly set on both BE path (line 1094) and numeric SL update path (line 1115). No event logging per FORGE §0 (classification metadata, not lifecycle state). |
| Test Coverage | 10/10 | 0.25 | 2.50 | 9 tests (6 MUST, 2 SHOULD, 1 bonus): all 4 sl_type values tested at INSERT, MANUAL tested at UPDATE, null-never-occurs integration with 10 mixed scenarios, non-SL UPDATE regression test, backfill SQL correctness, and constant verification. Tests exercise real `process_one()` → `_process_signal()` path with in-memory DB. 9/9 pass. All 6 acceptance criteria covered. |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean 3-tier classification logic. `_sl_is_conditional` boolean computed once and reused in both notes-tag block and sl_type block — DRY. Module-level constant is appropriately scoped. INSERT column ordering is consistent (sl_type appended after filled_at). Comment `# A8: operator SL override` on both MANUAL paths aids readability. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Additive schema (`ALTER TABLE ADD COLUMN ... DEFAULT 'FIXED'`). Rollback is `ALTER TABLE signals DROP COLUMN sl_type` (SQLite 3.46.1). Single-commit revert. No data loss on rollback — column simply removed. Migration SQL documented with rollback in comments. |
| Data Integrity Impact | 9/10 | 0.15 | 1.35 | Additive column, no existing data modified except backfill (28 NONE, 0 CONDITIONAL — both verified by OinkV). DEFAULT 'FIXED' ensures no NULLs for existing rows. sl_type is classification metadata — does not affect `calculate_blended_pnl()`, `_check_sl_tp()`, or any Financial Hotpath function. `_ALLOWED_UPDATE_COLS` correctly includes `sl_type` to permit MANUAL override. |
| **OVERALL** | | | **9.40** | |

## Issues Found

**MUST-FIX (blocks PASS):**
None.

**SHOULD-FIX (advisory, improves score):**
None.

**SUGGESTION (no score impact):**
1. The `test_micro_gate_filled_at.py` column count assertion jumps from 28→30 (skipping 29) because the branch includes both A11 and A8 changes. The test comment says "29 columns, 29 placeholders" but the assertion checks 30. Minor documentation inconsistency — the assertion value (30) is correct.

## What's Done Well
- **Shared constant pattern:** `_CONDITIONAL_SL_KEYWORDS` as module-level tuple with single-point-of-truth is the right deduplication approach. The `_sl_is_conditional` boolean caches the check result and avoids redundant keyword scanning.
- **UPDATE path coverage:** MANUAL set on *both* BE path and numeric SL update path — this shows attention to the full update flow, not just the obvious case.
- **Test quality:** The MUST-6 integration test (10 mixed scenarios with expected types) is thorough — tests the full classification matrix in one shot while also verifying the null-invariant.
- **Schema updates in 6 existing test files:** Systematic addition of both `leverage_source` (A11) and `sl_type` (A8) to all test schemas — no schema drift between test files.

## Verdict: ✅ PASS

Overall 9.40 ≥ 9.0 (STANDARD threshold). Clean implementation matching the approved proposal. All 9 tests pass, 99 total pass with 5 pre-existing failures unchanged. No Financial Hotpath files touched. Proceed to merge.

Note: GUARDIAN review not required for STANDARD tier Phase 1 when the change is purely additive metadata with no data integrity risk. However, if GUARDIAN wishes to review, the data safety section of this review documents the scope.
