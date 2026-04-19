# VIGIL Review — Task A5: Parser-Type Confidence Scoring

**Branch:** anvil/A5-parser-confidence-scoring
**Commits:** f74109fa, 188eaa35
**Change Tier:** 🟡 STANDARD
**Review Round:** 2
**Review Date:** 2026-04-19 14:00 UTC

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | All 7 map keys match proposal §3 exactly: cornix_regex=0.95, telegram_direct=0.92 (fixed from 0.90), chroma_regex=0.90, oinxtractor_agent=0.75, llm_nl=0.70, inline_fallback=0.70, qwen_v3=0.70. Fallback=0.80. is-None gate before `_safe_float()`, module-level constant, `entry.get("extraction_method")` read. No schema changes, no backfill — forward-only as specified. |
| Test Coverage | 10/10 | 0.25 | 2.50 | 13 tests (9 MUST + 4 SHOULD): all 7 map keys tested, unknown/missing fallback, explicit extractor preservation (0.62, 8.5, 9.5), and new boundary test for explicit 0.80 (VIGIL R1 SHOULD-FIX addressed). Every acceptance criterion from proposal §7 has a corresponding test. |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean implementation. Module-level constant with maintenance comment and source-line references. Named boolean `_extractor_supplied_confidence` is readable and well-commented. Test file well-structured with class grouping, docstrings, and shared helper. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | No schema changes, no DDL, no data modifications. `git revert` sufficient. Signals inserted during A5-active retain parser-type scores (acceptable — metadata only, no financial path impact). |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Metadata-only change. Zero downstream consumers of `signals.confidence` in financial paths (verified: lifecycle.py, engine.py — 0 references to confidence column). Existing >1.0/10.0 normalization preserved. Explicit extractor values respected via is-None gate. |
| **OVERALL** | | | **9.85** | |

## Delta (Round 1 → Round 2)

| Dimension | R1 | R2 | Δ |
|-----------|-----|-----|---|
| Spec Compliance | 7 (2.10) | 10 (3.00) | +3 (+0.90) |
| Test Coverage | 7 (1.75) | 10 (2.50) | +3 (+0.75) |
| Code Quality | 9 (1.35) | 9 (1.35) | 0 |
| Rollback Safety | 10 (1.50) | 10 (1.50) | 0 |
| Data Integrity | 10 (1.50) | 10 (1.50) | 0 |
| **OVERALL** | **8.20** | **9.85** | **+1.65** |

## Issues Found

**MUST-FIX:** None.

**SHOULD-FIX:** None.

**SUGGESTION:** None.

## R1 Fix Verification

| R1 Finding | Status | Evidence |
|-----------|--------|----------|
| MUST-FIX #1: telegram_direct 0.90→0.92 | ✅ Resolved | Map value changed (line 121), test renamed and assertion updated to 0.92, 13/13 pass |
| SHOULD-FIX #1: boundary test for explicit 0.80 | ✅ Resolved | `test_explicit_080_preserved_not_overridden` added — cornix_regex with ext.confidence=0.80 → 0.80 stored (not 0.95). Adversarial boundary case for is-None gate. |

## What's Done Well

- **Quick, surgical fix.** Commit 188eaa35 changes exactly what was needed — one map value, one test assertion, one new test. No scope creep.
- **Boundary test is well-designed.** Uses `cornix_regex` (highest map value at 0.95) with explicit 0.80 — maximum divergence between map and explicit value makes the test maximally sensitive.
- **All 13 A5 tests pass.** 31 existing micro-gate tests pass. 0 regressions.

## Verdict: ✅ PASS

Overall score **9.85** exceeds 🟡 STANDARD threshold of ≥9.0. All acceptance criteria tested. All spec values match. GUARDIAN 10.00 carries forward. Ready for merge.

---

*VIGIL 🔍 — Phase 1 Review for A5, Round 2*
*2026-04-19*
