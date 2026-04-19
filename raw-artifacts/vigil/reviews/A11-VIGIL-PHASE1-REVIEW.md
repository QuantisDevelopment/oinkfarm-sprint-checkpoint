# VIGIL Review — A11: Leverage Source Tracking (LIGHTWEIGHT)

**Branch:** `anvil/A11-leverage-source-tracking`
**Head SHA:** `2945ada0577a040d1995d0b54bc5a1d3bb708bfe`
**Review Date:** 2026-04-19
**Tier:** 🟢 LIGHTWEIGHT (no Financial Hotpath touch)
**Verdict:** ✅ PASS

---

## Reason

Clean, minimal implementation — 3 lines of logic + INSERT column addition. All 5 planned tests pass through real `_process_signal()`. Schema migration is additive with correct backfill predicate. 90/90 tests pass; 5 pre-existing failures unchanged.

## Details

- `leverage_source` correctly reads **post-normalization** `leverage` — if the extractor provides an unparseable string (e.g. `"5x-10x"`), both `leverage` and `leverage_source` are `NULL` (MUST-4 test confirms). Reading `ext.get("leverage")` pre-normalization would have incorrectly set `leverage_source = 'EXPLICIT'` for unparseable values, so the ordering choice is the right one.
- INSERT column count 28→29, placeholder count matches ✅
- Migration SQL is additive (`ADD COLUMN ... DEFAULT NULL`) with clean rollback (`DROP COLUMN`) ✅
- 6 existing test files updated with `leverage_source` in schema — no regressions ✅
- No Financial Hotpath files touched — tier confirmed 🟢 LIGHTWEIGHT ✅

## Phase 0 Ordering Concern — Closed

My Phase 0 review flagged: "verify `ext.get("leverage")` is read BEFORE the normalization block mutates the local variable." After reading the diff, the implementation intentionally reads POST-normalization, and that is correct here because parse failure collapses both values to `None`, matching the plan §5 `test_range_leverage` spec. Concern closed.

## Test Evidence

- 90/90 pass on branch HEAD
- 5 pre-existing failures unchanged (mutation_guard AttributeError + wg_alert_override logic — unrelated)
- New tests: `tests/test_a11_leverage_source.py` (+214 lines, 5 MUST + 1 SHOULD) covers EXPLICIT, NULL, `"10x"` string parse, `"5x-10x"` unparseable, backfill correctness through real `_process_signal()`.

## Files Changed (oinkfarm)

- `scripts/micro-gate-v3.py` (+8/-2)
- `scripts/migrations/a11_leverage_source.sql` (+8, new)
- `tests/test_a11_leverage_source.py` (+214, new)
- 6 existing test files: schema update for new column

## Verdict

✅ **PASS** — LIGHTWEIGHT threshold met (no numeric score required per SOUL.md §6). Approved for merge. GUARDIAN Phase 1 not required (LIGHTWEIGHT tier).

---

*Transcribed from VIGIL webchat delivery at 2026-04-19T14:43:15Z by the Hermes orchestrator for disk-record compliance. Original webchat run: 97c685a8-93ec-4fc7-b0ef-3f0bc00a419a.*
