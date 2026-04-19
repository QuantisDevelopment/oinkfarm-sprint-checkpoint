# VIGIL Review — Task A10: Database Merge (Old + New)

**Branch:** `anvil/A10-database-merge`
**Commit:** `81ba4463`
**Change Tier:** 🔴 CRITICAL (threshold ≥ 9.5)
**Review Round:** 1
**Review Date:** 2026-04-19 18:15 UTC

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 9/10 | 0.30 | 2.70 | Matches Phase 4 Task A10: internal dedup (176 rows), overlap resolution (77 dmids — new wins), server FK remap (11/11), trader FK remap (89/89 + 1 placeholder), schema alignment (remaining_pct=100.0, leverage_source=NULL, sl_type=FIXED/NONE), validation queries, and Mike approval gate. Test-on-copy-first enforced. [A10] traceability tag on all 912 imported rows with original_id. Stale signal override path exists (ACTIVE/PENDING → CLOSED_MANUAL) though all 72 stale signals were in the overlap set and skipped. |
| Test Coverage | 4/10 | 0.25 | 1.00 | **No automated test file (test_a10_*.py).** The validation report demonstrates thorough manual testing against a test copy with correct results (1,406 signals, 0 merge-introduced dups, 0 orphan FKs, 0 NULL sl_types). However, there are zero repeatable pytest tests for: (a) internal dedup logic (ROW_NUMBER priority), (b) FK remapping with edge cases, (c) schema alignment defaults, (d) stale signal override path, (e) string server_id fixup, (f) orphan trader placeholder creation. A one-time validation report is evidence of a successful run, not regression protection. |
| Code Quality | 9/10 | 0.15 | 1.35 | Well-structured 448-line script with clear step progression (7 steps), JSON report output, dry-run mode, sample row preview, and informative console output. `_STRING_SERVER_FIXES` is pragmatic for 3 anomalous signals. The `values` dict construction via column-by-column mapping is readable and handles missing columns cleanly. `last_insert_rowid()` is correct for single-connection SQLite. |
| Rollback Safety | 10/10 | 0.15 | 1.50 | SHA256-verified backup at known path. Rollback recipe documented in validation report (stop services → cp backup → start services → verify count). Script runs against test copy only — production untouched until Mike approves. The merge is a single INSERT batch — rollback is full restore, no partial state. |
| Data Integrity | 9/10 | 0.15 | 1.35 | Dedup window function correctly prioritizes terminal status → non-NULL closed_at → latest updated_at → highest id. FK integrity validated post-merge (0 orphans). Schema alignment fills all new columns with correct defaults. NULL checks on dmid, sl_type, remaining_pct all pass. FET #1159 verified unchanged. 14 pre-existing dups correctly identified as not merge-introduced. One minor gap: sl_type for imported signals only classifies FIXED/NONE — no CONDITIONAL detection for old signals whose notes might contain conditional SL keywords. This is acceptable since the [SL:CONDITIONAL] notes tag was introduced in A8 (not present in old DB), but worth noting. |
| **OVERALL** | | | **7.90** | |

## Issues Found

**MUST-FIX (blocks PASS):**

1. **No automated tests for merge logic.** A 🔴 CRITICAL task touching 912 rows of production data has zero pytest coverage. The merge script contains non-trivial logic (ROW_NUMBER dedup, FK remapping with string fixups, orphan trader creation, stale signal override, schema alignment) that must be testable. Required:
   - `test_a10_merge.py` with at minimum:
     - Internal dedup: 3+ duplicate dmids → only best row selected (verify priority order)
     - FK remapping: server discord_id match, trader (name, server_id) match
     - String server_id fixup: "wolfxsignals-tg" → server 8 resolves correctly
     - Orphan trader: signal with non-existent trader_id → placeholder created
     - Schema alignment: imported row has remaining_pct=100.0, leverage_source=NULL, sl_type=FIXED or NONE
     - Overlap resolution: shared dmid → old side skipped, new side preserved
     - Stale override: ACTIVE signal not in overlap → status=CLOSED_MANUAL (this path wasn't exercised in production but IS in the code and must be tested)
     - Validation: count match, 0 merge-introduced dups, 0 orphan FKs
   - Tests should use in-memory SQLite with minimal fixture data (not require actual DB files)

**SHOULD-FIX (advisory, improves score):**

1. **`_STRING_SERVER_FIXES` has only 2 entries but validation report mentions 3 signals.** The fixup map covers "wolfxsignals-tg" → 8 and "chroma-trading" → 10. Verify that signal #1127's server_id maps through one of these two entries (the report groups "3 signals" but only 2 distinct string values). If there's a third distinct string, it's unhandled. (Minor — validation passed, so this likely works, but the mapping should be explicit.)

2. **Stale override dead code path.** All ACTIVE/PENDING signals in the old DB turned out to be in the overlap set (skipped), so the `is_stale` code path at lines 230-238 was never exercised in the actual merge. Since the code exists and handles a real scenario, it must be tested even if production data didn't trigger it.

**SUGGESTION (no score impact):**

1. The `_server_name_to_id` dict (line 138) is built but never used. Appears to be remnant from an earlier approach to string server_id resolution. Can be removed.

## What's Done Well
- **Validation report quality:** The A10-VALIDATION-REPORT.md is thorough — count deltas, overlap analysis, stale handling, schema alignment, FK integrity, sample rows, rollback recipe, and Mike approval gate. This is exactly how a data migration should be documented.
- **Dedup strategy:** The ROW_NUMBER window function with 4-level priority (terminal status → closed_at → updated_at → id) is the right approach for picking the "best" row.
- **Test-on-copy-first:** Running against `/tmp/oinkfarm-a10-merge-test.db` rather than production is exactly what Phase 4 requires.
- **Traceability:** Every imported row tagged with `[A10: imported from pre-migration DB, original_id=NNN]` enables forensic analysis.

## Verdict: 🔄 REVISE

**Overall 7.90 < 9.5** (CRITICAL threshold). The merge script itself is well-written with excellent documentation and validation, but the complete absence of automated tests for a CRITICAL data migration is a blocking gap. The Test Coverage dimension at 4/10 (present via validation report, but major gaps in automated coverage) pulls the overall below threshold.

**To pass:** Add `tests/test_a10_merge.py` with the tests listed in MUST-FIX #1. The merge function `run_merge()` is already cleanly factored for testing — create two in-memory SQLite DBs with fixture data, call `run_merge()`, and assert on the returned report + post-merge DB state.
