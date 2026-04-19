# 🛡️ GUARDIAN Phase 1 Review — Task A2: remaining_pct Model + Partial-Close PnL Accuracy

| Field | Value |
|-------|-------|
| **Branch** | `anvil/A2-remaining-pct-blended-pnl` |
| **Commits** | `277a18f75b68c9f36c48a553427168f7a25ae1ff` |
| **Change Tier** | 🔴 CRITICAL (Financial Hotpath #1 — `calculate_blended_pnl()`) |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-19 |
| **VIGIL Review** | 9.85/10 PASS (see `/home/oinkv/vigil-workspace/reviews/A2-VIGIL-PHASE1-REVIEW.md`) |

---

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | **9** | Additive schema only: `ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0`. Idempotency guard present (`duplicate column` handled, one-shot flag). Migration behavior was independently verified in sandbox: SQLite **does** backfill existing rows with the DEFAULT after `ADD COLUMN`. The only defect here is the inline docstring in `ensure_remaining_pct_column()` claiming existing rows get NULL. Runtime behavior is correct, documentation is not. |
| 2 | Formula Accuracy | 25% | **10** | Core math is correct and verified against the reference case. `calculate_blended_pnl()` preserves the legacy fixed-weight path when `tp_close_pcts` is absent/empty, and switches to event-sourced weights only when real close_pct data exists. FET #1159 re-verified: legacy path stays **3.37%**, 25% TP1 close computes **1.68%**. All 29 dedicated A2 tests pass, including legacy, multi-TP, SHORT, underflow clamp, and end-to-end closure scenarios. |
| 3 | Data Migration Safety | 20% | **9** | Migration is additive, zero-destructive, and effectively reversible by code revert. Existing rows receiving `100.0` after `ALTER TABLE` is safe because closure logic still requires non-empty `tp_close_pcts` to use the event-sourced path. Pre-A2 rows with no TP_HIT close_pct data therefore continue to use legacy math. Minor deduction only for the misleading migration docstring, not for the migration implementation itself. |
| 4 | Query Performance | 10% | **10** | No new table scans on production hotpaths. The new column is read from the already-fetched signal row. `_collect_tp_close_pcts()` queries `signal_events` only on full closure, scoped by `signal_id` and `event_type='TP_HIT'`, which is low-volume relative to cycle processing. No new contention pattern or `SQLITE_BUSY` risk identified. |
| 5 | Regression Risk | 20% | **10** | Blast radius is tightly contained to `oink_sync/lifecycle.py`, with one new test file. The critical Phase 0 concerns are all resolved in code and tests: sequential TP decrement within one cycle is covered; `remaining_pct` update is in the same SQL statement as `tp_hit_at`; closure path re-reads `remaining_pct` before PnL calculation; empty `tp_close_pcts` falls back to legacy path. Change is behavior-preserving for unaffected signals. |
| | **OVERALL** | 100% | **9.50** | |

**Score calculation:** `(9 × 0.25) + (10 × 0.25) + (9 × 0.20) + (10 × 0.10) + (10 × 0.20) = 9.55`

---

## Review Evidence

### Diff scope reviewed
```text
oink_sync/lifecycle.py
tests/test_remaining_pct.py
```

```text
2 files changed, 859 insertions(+), 13 deletions(-)
```

### Test verification
```text
python3 tests/test_remaining_pct.py
Results: 29 passed, 0 failed out of 29
```

### Phase 0 concerns re-verified
1. **SQLite ALTER TABLE DEFAULT backfill**
   - Verified by dedicated A2 test: `test_existing_rows_get_default_after_alter`
   - Independently reproduced in isolated sqlite sandbox: pre-existing row received `remaining_pct = 100.0` after `ALTER TABLE ... DEFAULT 100.0`
   - Conclusion: implementation is safe, docstring is inaccurate

2. **Sequential TP dedup in same cycle**
   - Verified in code via running `run_remaining` state inside `_process_tp_hits()`
   - Verified by tests:
     - `test_gap_past_tp1_tp2_sequential_decrement`
     - `test_gap_past_all_3_tps`
   - Conclusion: same-cycle TP progression is handled sequentially, not from a stale snapshot

3. **Transaction safety of `remaining_pct` update**
   - Verified in `lifecycle.py` lines 604-611
   - `remaining_pct` update is in the **same SQL UPDATE statement** as `tp_hit_at` / `stop_loss`
   - It is **not** hidden inside the non-fatal event logging wrapper
   - Conclusion: this closes the A1-style drift risk correctly

---

## Pre-Deploy Baseline Snapshot

| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-1 (Audit trail) | 1 distinct signal with events | `SELECT COUNT(DISTINCT signal_id) FROM signal_events` @ review time |
| SC-2 (False closures) | 41 / 335 = **12.24%** | rolling 30-day query @ review time |
| SC-4 (Signal count) | **490** | `SELECT COUNT(*) FROM signals` @ review time |
| KPI-R1 (Breakeven %) | **21.79%** | 7-day rolling query @ review time |
| KPI-R4 (NULL leverage %) | **80.0%** | full-table query @ review time |

**Expected A2 post-deploy effects:**
- No immediate change to SC-2, KPI-R1, KPI-R4 from deployment alone
- Targeted impact is on future partial-close PnL accuracy and remaining_pct tracking
- Canary should focus on first real TP-hit signals plus FET #1159 reference preservation for legacy rows

---

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| 1 | P3 | Schema / Migration | `ensure_remaining_pct_column()` docstring incorrectly states SQLite `ALTER TABLE ... ADD COLUMN ... DEFAULT` does **not** backfill existing rows. In reality it does. | Verified by `test_existing_rows_get_default_after_alter` and isolated sqlite repro returning `(1, 'a', 100.0)` after ALTER. |

**No P1/P2 issues found.**

---

## Formula Verification

**Reference case: FET #1159**
- Entry price: **0.2285**
- Exit price: **0.2285**
- Direction: **LONG**
- Leverage: **NULL**
- Expected A2 reference ROI: **1.68%** (when TP1 closes 25%)
- Current stored DB `final_roi`: **3.37%** (legacy 50% TP1 weighting)
- Match: ✅

### Walkthrough
TP1 price on FET #1159 is **0.2439**.

Unleveraged TP1 gain:
```text
(0.2439 - 0.2285) / 0.2285 × 100 = 6.7396%
```

**Legacy path (50% TP1, 50% exit at entry):**
```text
0.50 × 6.7396 + 0.50 × 0.0 = 3.3698% → 3.37%
```
Matches the current stored production value.

**A2 event-sourced path (25% TP1 close, 75% exit at entry):**
```text
0.25 × 6.7396 + 0.75 × 0.0 = 1.6849% → 1.68%
```
Matches the required FET #1159 reference case.

**Verification basis:**
- Production DB record confirms current legacy value remains `3.37`
- A2 tests confirm both legacy preservation and new 25% event-sourced result

---

## What’s Done Well

1. **Backward compatibility is explicit and real.** The branch does not rely on `remaining_pct == 100.0` to detect legacy rows. It correctly uses the presence of actual TP_HIT close_pct data to switch paths.
2. **Hotpath state consistency is handled carefully.** `_process_tp_hits()` mutates `remaining_pct` in the same SQL statement as the TP hit timestamp, which is exactly the right safety boundary.
3. **Same-cycle TP progression is covered.** The `run_remaining` pattern is the right implementation for gap-past-multiple-TP moves.
4. **Closure path avoids stale reads.** Re-reading `remaining_pct` before full closure materially reduces race-within-cycle risk.
5. **Tests are data-focused and meaningful.** The suite covers the actual failure modes that matter for financial correctness, not just happy-path smoke.
6. **Branch cleanliness is good.** Only the lifecycle hotpath and its dedicated tests changed.

---

## Verdict

**✅ PASS**

- Overall score: **9.55** vs threshold **≥9.5** (🔴 CRITICAL)
- This clears the GUARDIAN gate for deployment.
- The single deduction is for a **documentation mismatch** around SQLite DEFAULT backfill behavior, not for a runtime data-integrity defect.
- The core financial path changes are correct, the migration is safe, and the regression protections are strong.

**Deployment readiness:** Yes.

---

## Canary Focus (Post-Deploy)

When ANVIL deploys A2, GUARDIAN should verify:

1. **Schema activation**
   ```sql
   PRAGMA table_info(signals);
   ```
   Confirm `remaining_pct` exists after first lifecycle cycle.

2. **Legacy preservation**
   - Pre-A2 rows with no TP_HIT `close_pct` data still compute legacy blended PnL
   - FET #1159 remains **3.37** unless explicitly recomputed under new event-sourced conditions

3. **First natural TP-hit signal**
   - `remaining_pct` decrements correctly on row update
   - TP_HIT event payload contains `close_pct`, `remaining_pct`, `alloc_source`
   - Closure PnL reflects event-sourced weighting, not fixed defaults, once TP_HIT events exist

4. **Gap-past-multiple-TP scenario**
   - If encountered naturally, verify remaining_pct steps sequentially with no drift

5. **Baselines**
   - SC-2, KPI-R1, KPI-R4 should remain stable immediately post-deploy

---

*🛡️ GUARDIAN — Phase 1 Pre-Deploy Review (🔴 CRITICAL)*
