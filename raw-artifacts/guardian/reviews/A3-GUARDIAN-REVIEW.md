# 🛡️ GUARDIAN Phase 1 Review — Task A3: Auto filled_at for MARKET Orders

| Field | Value |
|-------|-------|
| **Branch** | `anvil/A3-filled-at` |
| **Commits** | `d4428eab` |
| **Change Tier** | 🟡 STANDARD |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-18 |

---

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | **10** | No schema change. `filled_at` column already exists. INSERT correctly adds it as 28th column with matching placeholder. Column/value positions verified by manual audit and MUST-5 test. |
| 2 | Formula Accuracy | 25% | **10** | No formula modified. `filled_at` is a timing field with zero involvement in any financial calculation (ROI, PnL, blended exit). FET #1159 reference case: `final_roi = 3.37` — unchanged, as expected. |
| 3 | Data Migration Safety | 20% | **10** | Backfill is additive (NULL → `posted_at`), idempotent (re-run safe: `AND filled_at IS NULL`), zero-downtime (micro-gate is per-batch), fully reversible, with pre/post verification queries provided. 8 rows targeted; 9 LIMIT NULL rows explicitly excluded and tracked separately. |
| 4 | Query Performance | 10% | **10** | One additional column in existing INSERT — negligible. Backfill UPDATE touches 8 rows with indexed WHERE clause. No new queries, no new indexes needed, no SQLITE_BUSY risk. |
| 5 | Regression Risk | 20% | **10** | Change is provably behavior-preserving: downstream consumers use `filled_at or posted_at` pattern — value is identical for MARKET orders. Primary risk (INSERT parameter count mismatch) is directly tested by MUST-5. Blast radius if INSERT breaks: all new signals fail, but immediately detectable (first batch post-deploy). 8/8 tests pass. Existing test schema updated (`test_micro_gate_source_url.py`). |
| | **OVERALL** | 100% | **10.00** | |

**Score calculation:** `(10 × 0.25) + (10 × 0.25) + (10 × 0.20) + (10 × 0.10) + (10 × 0.20) = 10.00`

---

## Pre-Deploy Baseline Snapshot

| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-1 (Audit trail) | 0 signals with events | `SELECT COUNT(DISTINCT signal_id) FROM signal_events` @ 2026-04-18T21:45Z |
| SC-2 (False closures) | 41 / 333 closures (30-day) | `WHERE updated_at > datetime('now', '-30 days')` @ 2026-04-18T21:45Z |
| SC-4 (Signal count) | **490** | `SELECT COUNT(*) FROM signals` @ 2026-04-18T21:45Z |
| KPI-R1 (Breakeven %) | 22.86% (7-day) | `WHERE status LIKE 'CLOSED%' AND updated_at > datetime('now', '-7 days')` @ 2026-04-18T21:45Z |
| KPI-R4 (NULL leverage %) | 80.00% | Full table @ 2026-04-18T21:45Z |
| KPI-R5 (NULL filled_at MARKET) | **8** | `WHERE fill_status='FILLED' AND filled_at IS NULL AND order_type='MARKET'` @ 2026-04-18T21:45Z |
| Total NULL filled_at (FILLED) | **17** (8 MARKET + 9 LIMIT) | `WHERE fill_status='FILLED' AND filled_at IS NULL` @ 2026-04-18T21:45Z |

**A3-specific expected changes post-deploy:**
- KPI-R5 (NULL filled_at MARKET): 8 → **0** (after backfill)
- Total NULL filled_at (FILLED): 17 → **9** (9 LIMIT remain — separate issue)
- All other metrics: **unchanged**

---

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| — | — | — | No issues found | — |

---

## Formula Verification

**Reference case: FET #1159**
- Entry price: 0.2285
- Exit price: 0.2285
- Direction: LONG
- Leverage: NULL
- Expected ROI: 1.68% *(per SOUL.md reference — see note below)*
- DB final_roi: **3.37%**
- Computed unleveraged ROI: **0.0%** (entry = exit)
- Match: ✅ **N/A — A3 does not modify any formula**

**Note:** FET #1159's `final_roi = 3.37` reflects blended PnL from a TP1 partial close (tp1_hit_at is set, close_source = sl_hit at entry). The discrepancy between 3.37% and the SOUL.md reference (1.68%) is a known pre-existing condition in the blended PnL computation — Task A2's scope, not A3's. A3 modifies zero formula logic. FET #1159's `final_roi` value is unchanged by this commit, confirming no formula regression.

**Walkthrough:**
A3 adds `filled_at` — a timing field — to the INSERT path. `filled_at` does not appear in `calculate_blended_pnl()`, ROI computation, or any financial formula. Verified by grep:
```
grep -n "filled_at" scripts/micro-gate-v3.py → 3 hits (all in the A3 INSERT/event changes)
```
No formula paths are touched.

---

## What's Done Well

1. **Surgical scope.** Single column, single file, single concern. `fill_price` correctly deferred.
2. **Parameter count test (MUST-5).** Directly addresses the highest-risk failure mode. Inspects source code to count columns vs placeholders — catches the exact bug class that would break production.
3. **LIMIT NULL tracking.** ANVIL identified the 9 LIMIT/FILLED NULL rows, explicitly excluded them, and tracked them in a separate followup file. Good scope discipline.
4. **Event payload inclusion.** Adding `filled_at` to the SIGNAL_CREATED event payload enables downstream observability without additional queries.
5. **Existing test schema updated.** `test_micro_gate_source_url.py` gets `filled_at TEXT` added to its DDL — prevents test failures from schema mismatches.
6. **Pre-backfill audit table.** ANVIL provided exact IDs and timestamps for the 8 affected rows, enabling precise canary verification.
7. **SHOULD→MUST promotion.** ANVIL elevated the "backfill skips already-set filled_at" test from SHOULD to MUST — conservative and correct.

---

## Verdict

**✅ PASS**

- Overall score: **10.00** vs threshold 9.0 (🟡 STANDARD)
- This is a genuinely clean, minimal, behavior-preserving change. The implementation matches the approved Phase 0 proposal exactly. No schema changes, no formula modifications, no performance concerns, and comprehensive test coverage for the one real risk (parameter count mismatch).
- **Approved for deployment** pending VIGIL's parallel review.

---

## Canary Plan (Post-Deploy)

When ANVIL deploys and runs the backfill:

1. **Backfill verification:** `SELECT COUNT(*) FROM signals WHERE order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL;` → expected **0**
2. **Canary monitoring:** First 10 new MARKET order INSERTs — verify `filled_at IS NOT NULL AND filled_at = posted_at` for each
3. **Regression watch:** KPI-R5 should drop from 8 to 0 immediately post-backfill
4. **24h comparison:** All SC and KPI-R metrics compared against pre-deploy baseline above
5. **48h comparison:** Extended verification, final canary verdict

---

*🛡️ GUARDIAN — Phase 1 Pre-Deploy Review*
*Review completed: 2026-04-18T21:50Z*
