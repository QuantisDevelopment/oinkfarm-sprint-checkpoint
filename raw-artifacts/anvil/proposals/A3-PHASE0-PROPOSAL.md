# Phase 0 Technical Proposal — Task A3: Auto filled_at for MARKET Orders

**Author:** ⚒️ ANVIL
**Date:** 2026-07-22
**Task:** A3 — Auto filled_at for MARKET Orders
**Tier:** 🟡 STANDARD
**Phase 4 Ref:** §1 (Auto filled_at), Phase 0 (NULL rate analysis)
**Dependencies:** None — independent task
**Estimated Effort:** 0.5 days

---

## 1. Problem Statement

MARKET orders inserted via `micro-gate-v3.py` (`_process_signal()`, line ~842) are immediately filled at INSERT time (`fill_status='FILLED'`), but `filled_at` is never set — it remains NULL. The INSERT statement covers 27 columns; `filled_at` is not among them.

**Current production state** (verified against live DB):
- 17 FILLED signals have NULL `filled_at`
- Of those: **8 are MARKET orders** (the target of this task), **9 are LIMIT orders** (separate issue — those should have been set by `_check_limit_fills()` but weren't; out of scope for A3)
- Downstream code (`oink_sync/lifecycle.py` line ~280, `portfolio_stats.py` line ~406) falls back to `posted_at` when `filled_at` is NULL, so functional impact is minor — but the data model is incorrect and Phase 6 SC-3 requires accurate timing data.

## 2. Proposed Approach

**Single-file code change** in `scripts/micro-gate-v3.py`:

1. Add `filled_at` as the 28th column in the INSERT statement within `_process_signal()`
2. Set the value conditionally:
   - `order_type == 'MARKET'` → `filled_at = posted_at` (MARKET = instant fill; `posted_at` is the Discord message timestamp or `_now_iso()` fallback)
   - `order_type == 'LIMIT'` → `filled_at = None` (set later by `LifecycleManager._check_limit_fills()` in oink-sync when the PENDING→ACTIVE transition is detected)
3. **One-time backfill SQL** for the 8 existing MARKET/FILLED signals with NULL `filled_at`:
   ```sql
   UPDATE signals
   SET filled_at = posted_at
   WHERE order_type = 'MARKET'
     AND fill_status = 'FILLED'
     AND filled_at IS NULL;
   ```
4. Verification query post-backfill: `SELECT COUNT(*) FROM signals WHERE order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL;` → expected 0.

**Scope boundary:** A3 addresses `filled_at` ONLY. `fill_price` for MARKET orders (DQ-A3-1 from FORGE) is deferred per FORGE's recommendation — trivial follow-up if desired.

## 3. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Value for MARKET filled_at | `posted_at` | Semantically correct — MARKET orders fill at the moment the trader posts. Same timestamp source used downstream as fallback already. |
| LIMIT orders at INSERT | `None` | Existing flow in `LifecycleManager._check_limit_fills()` (oink-sync line ~451) sets `filled_at` on PENDING→ACTIVE transition. No change needed. |
| Backfill scope | MARKET + FILLED + NULL filled_at only | Precise WHERE clause. Does NOT touch the 9 LIMIT orders with NULL filled_at (different root cause, out of scope). |
| fill_price for MARKET | Deferred | Keep A3 focused. One column, one change, one PR. |

## 4. Test Strategy

| Test | Type | Priority |
|------|------|----------|
| MARKET order INSERT → `filled_at == posted_at` | Unit | MUST |
| LIMIT order INSERT → `filled_at IS NULL` | Unit | MUST |
| Backfill sets `filled_at = posted_at` for qualifying rows | Unit | MUST |
| Backfill skips LIMIT orders | Unit | MUST |
| Backfill skips signals that already have `filled_at` set | Unit | SHOULD |
| Parameter count (28 columns, 28 placeholders) dry-run validation | Unit | MUST |

All tests written against a fresh in-memory SQLite DB using the production schema. No production data touched during testing.

## 5. Risk Assessment

| Dimension | Risk Level | Notes |
|-----------|-----------|-------|
| **Schema** | 🟢 NONE | No schema change. `filled_at` column already exists in `signals` table. |
| **Formula** | 🟢 NONE | No financial calculation affected. |
| **Migration** | 🟢 LOW | Backfill UPDATE touches 8 rows with a precise WHERE clause. Reversible (set back to NULL). |
| **Performance** | 🟢 NONE | One additional column in INSERT — negligible. |
| **Regression** | 🟡 LOW | Primary risk: INSERT parameter count mismatch (27→28 columns, 27→28 placeholders). Mitigated by dry-run test and explicit placeholder count verification. |

**Highest-risk dimension:** Regression — if the `?` placeholder count doesn't match the column count, ALL new signal INSERTs fail. Mitigation: dedicated test that counts columns vs placeholders, plus dry-run INSERT before deploy.

## 6. Rollback Plan

1. `git revert <commit>` — removes `filled_at` from INSERT; new MARKET orders revert to NULL `filled_at`
2. Downstream fallback (`filled_at or posted_at`) handles NULL gracefully — zero functional regression on rollback
3. Backfill data is harmless to leave in place (`filled_at = posted_at` is the correct value); no data rollback needed
4. No service restart required — micro-gate-v3.py is invoked per-batch by signal-gateway, not a long-running service

## 7. Files Changed

| File | Change | Repo |
|------|--------|------|
| `scripts/micro-gate-v3.py` | MODIFY — add `filled_at` to INSERT in `_process_signal()` | oinkfarm |
| `tests/test_micro_gate_filled_at.py` | CREATE — unit tests for filled_at behavior | oinkfarm |

## 8. For GUARDIAN Specifically

- **Data change:** Backfill UPDATE sets `filled_at = posted_at` for 8 MARKET/FILLED signals with NULL `filled_at`
- **Verification query (pre-backfill):** `SELECT id, ticker, trader_id, posted_at, filled_at FROM signals WHERE order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL;`
- **Verification query (post-backfill):** Same query → expected 0 rows
- **Canary scope:** First 10 new MARKET order INSERTs after deploy — verify `filled_at IS NOT NULL` and `filled_at == posted_at` for each
- **No formula/PnL impact** — this task does not touch any financial calculation path

---

*Submitted for VIGIL + GUARDIAN review — Phase 0 approval required before implementation.*
