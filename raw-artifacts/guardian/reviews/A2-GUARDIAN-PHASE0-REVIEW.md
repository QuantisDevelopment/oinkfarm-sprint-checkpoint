# 🛡️ GUARDIAN Proposal Review — Task A2 (🔴 CRITICAL)

**Verdict:** ✅ APPROVE

---

## Data Safety

**Risk: LOW.** Single additive column (`remaining_pct REAL DEFAULT 100.0`). No existing data is modified. Existing signals get `remaining_pct = NULL` (not 100.0) since SQLite's ADD COLUMN with DEFAULT sets the default for new INSERTs but existing rows get NULL unless a backfill is run. This is actually the correct behavior — NULL means "pre-A2 signal, use fixed-weight path."

**Correction to proposal §2A:** ANVIL states "Default 100.0 for all existing signals — no data migration needed beyond the ALTER." This is slightly misleading. SQLite `ALTER TABLE ADD COLUMN ... DEFAULT 100.0` sets the default for future INSERTs but existing rows get NULL, not 100.0. The backward-compat path handles NULL correctly (falls back to fixed weights), so this is safe. But ANVIL should verify the test expectations account for this distinction — existing rows will have `remaining_pct IS NULL`, not `remaining_pct = 100.0`.

**Critical safety property:** The `remaining_pct` UPDATE is described as being in the SAME transaction as the `tp_hit_at` UPDATE (not wrapped in the event try/except). This is correct and essential. If `remaining_pct` were in the non-fatal event wrapper, a failed event write could silently skip the remaining_pct update, causing PnL drift. ANVIL explicitly calls this out in §11 (Lessons Applied from A1). ✅

## Migration Risk

**Risk: LOW.** ALTER TABLE ADD COLUMN on SQLite is one of the safest possible migrations:
- No table rebuild needed
- No data copying
- No locks beyond the schema-change lock (instant)
- oink-sync holds no long transactions during the ALTER

No backfill of existing signals (correct decision — avoids retroactive PnL changes). Future ACTIVE signal backfill tracked as deferred item.

**Rollback:** Git revert leaves a harmless NULL column behind. `calculate_blended_pnl()` reverts to fixed-weight-only. No data corruption possible. ✅

## Query Performance

**Risk: NEGLIGIBLE.** The remaining_pct UPDATE is added to an existing UPDATE statement (same WHERE clause, same transaction). No new SELECT queries. No new indexes needed (remaining_pct is only read by the signal row that's already fetched). At current throughput (a few TP hits/day), this adds zero measurable overhead.

## Regression Risk

**Risk: MEDIUM — but well-mitigated.** This is the core concern for a Financial Hotpath #1 change.

**The critical backward-compat guarantee:** When `remaining_pct` is NULL and `tp_close_pcts` is not provided, `calculate_blended_pnl()` returns exactly the same result as the current function. All 490 existing signals (260 closed + remaining active/pending) are protected by this path.

**Verification:** FET #1159 math independently confirmed:
- Entry=0.2285, TP1=0.2439, Exit=0.2285, Direction=LONG
- TP1 gain: (0.2439 − 0.2285) / 0.2285 = 6.74%
- Current (50% at TP1): 0.50 × 6.74% + 0.50 × 0% = **3.37%** ✅ matches stored `final_roi`
- With 25% at TP1: 0.25 × 6.74% + 0.75 × 0% = **1.68%** ✅ matches ANVIL's projection
- With NULL remaining_pct: fixed-weight path → **3.37%** ✅ no regression

**Blast radius assessment:**
- Only oink-sync's lifecycle.py is modified (one repo, one file)
- No micro-gate changes (INSERTs unaffected)
- No event_store.py changes (payload is JSON in existing TEXT column)
- No signal_router.py changes (provider extraction deferred)
- Test strategy covers the right scenarios: backward compat, multi-TP progressions, edge cases

**Residual risk:** The remaining_pct decrement logic must be correct for sequential TP hits. If TP1 closes 50% and TP2 closes 25%, remaining_pct goes 100 → 50 → 25. If the order is wrong or a TP is hit twice, remaining_pct could drift. The clamping to ≥0.0 is a good safety net but doesn't prevent drift above 0. Phase 1 should verify the dedup behavior (can the same TP fire twice in the same cycle?).

## Rollback Viability

**Viable.** Git revert is the complete rollback:
1. `calculate_blended_pnl()` reverts to fixed-weight path
2. `remaining_pct` column stays but is harmless (not read by any code post-revert)
3. TP_HIT events with `close_pct` in payload are advisory JSON — no schema impact
4. No data migration to undo

## Open Question: Default Close Percentage Table

ANVIL recommends keeping 50/25/25 for 3-TP signals. **I agree.** Changing to 33/33/34 would cause all future 3-TP signals to compute different PnL than the 36 existing 3-TP signals using the same default weights. This creates a baseline discontinuity that complicates trend analysis and makes A2's impact harder to isolate during canary monitoring. Keep 50/25/25 now, add the config option for future tuning when real `close_pct` data is available.

## Concerns

1. **SQLite DEFAULT behavior clarification** (mentioned above): ANVIL should confirm that the backward-compat path is triggered by `remaining_pct IS NULL`, not `remaining_pct = 100.0`, since existing rows will have NULL after the ALTER.

2. **TP dedup in same cycle:** Phase 1 should verify what happens if price gaps past multiple TPs in a single cycle (e.g., price jumps from below TP1 to above TP2). Does `_process_tp_hits()` handle both in one pass? If so, the remaining_pct decrement needs to be sequential within that pass, not based on a stale read.

## Suggestions

- Consider adding `remaining_pct` to the TP_HIT event's `old_value`/`new_value` structured metadata (using the A1 columns), in addition to the JSON payload. This enables future queries like "show me all remaining_pct changes" without JSON parsing.
- The alloc_source field is a good design decision for future auditability. Well done.

---

*🛡️ GUARDIAN — Phase 0 Proposal Review*
*Reviewed: 2026-04-19T01:55Z*
