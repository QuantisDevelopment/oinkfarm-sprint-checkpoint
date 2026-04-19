# VIGIL Review — Task A5: Parser-Type Confidence Scoring

**Branch:** anvil/A5-parser-confidence-scoring
**Commits:** f74109fa, 188eaa35
**Change Tier:** 🟡 STANDARD
**Review Round:** 2
**Review Date:** 2026-04-19 14:00 UTC

---

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | All 7 map keys verified against source: cornix_regex=0.95, telegram_direct=0.92 (R1 MUST-FIX resolved), chroma_regex=0.90, oinxtractor_agent=0.75, llm_nl=0.70, inline_fallback=0.70, qwen_v3=0.70. Fallback=0.80. `_extractor_supplied_confidence = ext.get("confidence") is not None` check placed BEFORE `_safe_float()` — correct ordering. Module-level `PARSER_CONFIDENCE_MAP` constant. `entry.get("extraction_method", "unknown")` read from top-level entry dict. No schema changes, no backfill — forward-only as specified. |
| Test Coverage | 10/10 | 0.25 | 2.50 | 13 tests (9 MUST + 4 SHOULD): all 7 map keys have dedicated assertions, unknown/missing fallback tested, explicit extractor preservation tested (0.62, 8.5→0.85, 9.5→0.95), and new boundary test `test_explicit_080_preserved_not_overridden` (R1 SHOULD-FIX resolved — adversarial case using cornix_regex with ext.confidence=0.80, confirming is-None gate does NOT apply map's 0.95). All 6 acceptance criteria from proposal §7 covered. 13/13 pass. |
| Code Quality | 9/10 | 0.15 | 1.35 | Carried forward from R1. Clean implementation: module-level constant with maintenance comment and source-line references. Named boolean `_extractor_supplied_confidence` is readable. Test file well-structured with class grouping, docstrings, and shared `_insert_and_get_confidence` helper. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Carried forward from R1. No schema changes, no DDL, no data modifications. `git revert` sufficient. Signals inserted during A5-active retain parser-type scores (acceptable — metadata only, no financial path impact). |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Carried forward from R1. Metadata-only change. Zero downstream consumers of `signals.confidence` in financial paths (verified Phase 0: lifecycle.py, engine.py — 0 references). Existing >1.0/10.0 normalization preserved intact. Explicit extractor values respected via is-None gate. |
| **OVERALL** | | | **9.85** | |

---

## Delta (Round 1 → Round 2)

| Dimension | R1 | R2 | Δ |
|-----------|-----|-----|---|
| Spec Compliance | 7 (2.10) | 10 (3.00) | +3 (+0.90) |
| Test Coverage | 7 (1.75) | 10 (2.50) | +3 (+0.75) |
| Code Quality | 9 (1.35) | 9 (1.35) | 0 (carried) |
| Rollback Safety | 10 (1.50) | 10 (1.50) | 0 (carried) |
| Data Integrity | 10 (1.50) | 10 (1.50) | 0 (carried) |
| **OVERALL** | **8.20** | **9.85** | **+1.65** |

---

## R1 Fix Verification

| R1 Finding | Status | Evidence |
|-----------|--------|----------|
| **MUST-FIX #1:** `telegram_direct` 0.90→0.92 per Phase 0 spec | ✅ Resolved | Map value at line 121: `"telegram_direct": 0.92`. Test `test_telegram_direct_gets_092` asserts 0.92. Passes. |
| **SHOULD-FIX #1:** Add boundary test for explicit 0.80 | ✅ Resolved | `test_explicit_080_preserved_not_overridden` added (SHOULD-4). Uses `cornix_regex` with `ext_confidence=0.80` — maximum divergence between map value (0.95) and explicit value (0.80) makes the is-None gate maximally testable. Passes. |

---

## Issues Found

**MUST-FIX:** None.

**SHOULD-FIX:** None.

**SUGGESTION:** None.

---

## Regression Check

- **A5 tests:** 13/13 PASSED ✅
- **Full test suite:** 70 passed, 5 failed
- **5 failures are pre-existing** (verified: identical failures on parent commit without A5 changes). Affected files: `test_micro_gate_mutation_guard.py` (3 failures), `test_micro_gate_wg_alert_override.py` (2 failures). These pre-date A5 and are unrelated to confidence scoring.
- **A5 introduces 0 regressions.** ✅

---

## What's Done Well

- **Surgical fix.** Commit 188eaa35 changes exactly what R1 required — one map value (0.90→0.92), one test assertion update, one new boundary test. No scope creep.
- **Boundary test is well-designed.** `test_explicit_080_preserved_not_overridden` uses `cornix_regex` (highest map value at 0.95) with explicit `ext.confidence=0.80` — this is the adversarial maximum-divergence case that would catch a broken is-None gate.
- **Implementation quality throughout.** The `PARSER_CONFIDENCE_MAP` constant with inline source references, the named `_extractor_supplied_confidence` boolean, and the maintenance comment are all production-grade.

---

## Verdict: ✅ PASS

Overall score **9.85** exceeds 🟡 STANDARD threshold of ≥9.0. Both R1 findings resolved. 13/13 A5 tests pass. 0 regressions introduced. GUARDIAN's 10.00 PASS carries forward (fix commits are entirely in VIGIL's domain — spec value + tests).

**Ready for merge.**

---

*VIGIL 🔍 — Phase 1 Review for A5, Round 2*
*2026-04-19 14:00 UTC*
