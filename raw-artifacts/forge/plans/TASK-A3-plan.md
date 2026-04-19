# Task A.3: Auto filled_at for MARKET Orders

## ⚠️ POST-AUDIT REVISIONS

**Date:** 2026-04-19
**Auditor:** OinkV 👁️🐷

This plan has been revised after OinkV code audit (see `OINKV-AUDIT.md`). Key changes:

- **Dead-code redirect (contextual references only):** Interactions with the lifecycle engine now correctly point at `oink-sync/oink_sync/lifecycle.py` (`LifecycleManager._check_limit_fills()` at line ~451), not `scripts/kraken-sync.py` (inactive since 2026-04-07).
- **Line-number corrections:** The grace-period read site is at line ~280 in `oink_sync/lifecycle.py` (tuple index access `row[16] or row[15]` — not dict access), not line ~566 in kraken-sync.py.
- **Core logic is unchanged and correct:** the INSERT modification in `micro-gate-v3.py` and the backfill SQL both remain sound. A3 was the plan least affected by the audit.

---

**Source:** Arbiter-Oink Phase 4 §1 (Auto filled_at), Phase 0 (NULL rate analysis)
**Tier:** 🟡 STANDARD
**Dependencies:** None — independent task
**Estimated Effort:** Phase 4 says 0.5 days; FORGE assessment: 0.5 days (straightforward column population)
**Plan Version:** 1.0
**Codebase Verified At:** `521d4411` (2026-04-18)

---

## 0. Executive Summary

MARKET orders are filled immediately at insertion, but the `filled_at` timestamp is never set in the INSERT path. This leaves 16 FILLED signals with NULL `filled_at`, and every new MARKET order continues the pattern. The fix is simple: set `filled_at = posted_at` for MARKET orders at INSERT time.

Additionally, a one-time backfill sets `filled_at = posted_at` for existing MARKET/FILLED signals with NULL `filled_at`.

---

## 1. Current State Analysis

### The Problem

In `micro-gate-v3.py`, the INSERT statement (line ~840-860 approximately) inserts 27 columns into the `signals` table. **`filled_at` is not among them.** When `order_type='MARKET'` and `fill_status='FILLED'`, the signal is immediately filled — but `filled_at` remains NULL.

**Impact:**
- `filled_at` is used by `kraken-sync.py` for grace period calculation (line ~566): `ref_ts = row["filled_at"] or row["posted_at"]`
- `filled_at` is used by `portfolio_stats.py` for hold time calculation (line ~406): `start = s.get("filled_at") or s.get("posted_at")`
- Both fall back to `posted_at`, so the functional impact is minor — but the data model is incorrect
- Phase 6 success criterion SC-3 requires accurate timing data

### Current Data State

```sql
SELECT fill_status, COUNT(*) FROM signals GROUP BY fill_status;
-- FILLED: 429, PENDING: 15, EXPIRED_UNFILLED: 40, CANCELLED: 1, UNFILLED: 4

SELECT order_type, COUNT(*) FROM signals GROUP BY order_type;
-- MARKET: 380, LIMIT: 109

SELECT COUNT(*) FROM signals WHERE filled_at IS NULL AND fill_status='FILLED';
-- Result: 16

SELECT COUNT(*) FROM signals WHERE filled_at IS NOT NULL AND fill_status='FILLED';
-- Result: 413
```

**Analysis:** 16 out of 429 FILLED signals have NULL `filled_at`. The other 413 got `filled_at` set via the UPDATE path (when kraken-sync detects a limit fill: `check_limit_fills()` at line ~736 sets `filled_at`).

The 16 NULL-filled signals are MARKET orders that were inserted directly as FILLED but never had `filled_at` set. This aligns with the INSERT statement not including `filled_at`.

### Key Files

| File | Path | LOC | Relevance |
|------|------|-----|-----------|
| micro-gate-v3.py | scripts/micro-gate-v3.py | 1,393 | INSERT path — needs to set filled_at |
| lifecycle.py | oink-sync: oink_sync/lifecycle.py | 811 | `LifecycleManager._check_limit_fills()` already sets filled_at on LIMIT→FILLED transitions |
| portfolio_stats.py | scripts/portfolio_stats.py | 1,051 | Reads filled_at for hold time calculation |

### Key Functions

| Function | File | Current Behavior | Change Required |
|----------|------|-----------------|----------------|
| `_process_signal()` | micro-gate-v3.py | INSERT without filled_at | Add filled_at = posted_at when order_type = 'MARKET' |
| `check_limit_fills()` | kraken-sync.py (line ~712) | Sets filled_at on PENDING→ACTIVE | No change needed — already correct for LIMIT orders |

### The INSERT Statement (Current)

Located in `_process_signal()` in micro-gate-v3.py (approximately line ~840):

```sql
INSERT OR IGNORE INTO signals
(discord_message_id, channel_id, channel_name, server_id, trader_id,
 ticker, direction, order_type, entry_price, stop_loss,
 take_profit_1, take_profit_2, take_profit_3,
 status, confidence, notes, raw_text,
 posted_at, updated_at, source_url,
 leverage, asset_class, exchange_ticker, exchange, exchange_matched,
 fill_status, message_type)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Note:** 27 columns, `filled_at` is NOT included.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| scripts/micro-gate-v3.py | `_process_signal()` | MODIFY | Add `filled_at` to INSERT — set to `posted_at` when `order_type='MARKET'`, NULL for LIMIT |
| tests/test_micro_gate_filled_at.py | — | CREATE | Test that MARKET orders get filled_at = posted_at |

---

## 3. SQL Changes

### 3a. Code Change (INSERT modification)

The INSERT statement in `_process_signal()` should add `filled_at` to both the column list and values:

**Column list becomes 28 columns:**
```sql
INSERT OR IGNORE INTO signals
(discord_message_id, channel_id, channel_name, server_id, trader_id,
 ticker, direction, order_type, entry_price, stop_loss,
 take_profit_1, take_profit_2, take_profit_3,
 status, confidence, notes, raw_text,
 posted_at, updated_at, source_url,
 leverage, asset_class, exchange_ticker, exchange, exchange_matched,
 fill_status, message_type, filled_at)   -- ← added
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Value for `filled_at`:**
- When `order_type == 'MARKET'`: `posted_at` (same timestamp as posting — MARKET = instant fill)
- When `order_type == 'LIMIT'`: `None` (will be set later by `check_limit_fills()`)

### 3b. Backfill Existing NULL-filled_at MARKET Signals

```sql
-- One-time backfill: set filled_at = posted_at for MARKET orders that are FILLED but have NULL filled_at
UPDATE signals
SET filled_at = posted_at
WHERE order_type = 'MARKET'
  AND fill_status = 'FILLED'
  AND filled_at IS NULL;

-- Verification:
SELECT COUNT(*) FROM signals WHERE filled_at IS NULL AND fill_status = 'FILLED';
-- Expected: 0
```

**Note:** This UPDATE must be run by ANVIL (DB write access). FORGE has verified the affected row count is 16.

---

## 4. Implementation Notes

### 4a. Minimal Change

This is a very contained change:
1. Add one column name (`filled_at`) and one value (`posted_at if MARKET else None`) to the INSERT statement
2. Add one `?` placeholder to the VALUES tuple
3. Run one backfill UPDATE

### 4b. The fill_price Question

When `order_type='MARKET'`, the signal is filled at approximately `entry_price`. Currently, `fill_price` is also NULL for MARKET orders in the INSERT path. The Arbiter-Oink report doesn't explicitly address `fill_price` for MARKET orders in Task A3, but it's worth noting:

```sql
SELECT COUNT(*) FROM signals WHERE order_type='MARKET' AND fill_price IS NULL;
-- ANVIL should run this to determine scope
```

**FORGE recommendation:** A3 should ONLY address `filled_at`. If Mike wants `fill_price` set for MARKET orders too (e.g., `fill_price = entry_price`), that can be a separate lightweight task or added to A3's scope with Mike's approval.

### 4c. Interaction with oink-sync lifecycle.py

`oink_sync/lifecycle.py` uses `filled_at` in two places:
1. **Grace period** (line ~280): `ref_ts = row[16] or row[15]  # filled_at or posted_at`
2. **Limit fill detection** (`_check_limit_fills()` line ~451): Sets `filled_at` when PENDING→ACTIVE.

### 4d. posted_at Value

In the INSERT path, `posted_at` is set to:
```python
posted_at = entry.get("timestamp") or _now_iso()
```
This is the timestamp from the extraction payload (Discord message timestamp), falling back to now. Setting `filled_at = posted_at` for MARKET orders is semantically correct — the signal is filled at the moment the trader posts it (MARKET orders execute immediately).

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_market_order_has_filled_at` | Insert MARKET order via `_process_signal()` | `SELECT filled_at FROM signals WHERE id=X` returns non-NULL value equal to posted_at | unit | MUST |
| `test_limit_order_null_filled_at` | Insert LIMIT order via `_process_signal()` | `SELECT filled_at FROM signals WHERE id=X` returns NULL | unit | MUST |
| `test_backfill_fills_null_market` | Insert MARKET/FILLED signal with NULL filled_at, run backfill SQL | `filled_at` equals `posted_at` | unit | MUST |
| `test_backfill_skips_limit` | Insert LIMIT/PENDING signal with NULL filled_at, run backfill SQL | `filled_at` remains NULL | unit | MUST |
| `test_existing_filled_at_not_overwritten` | Signal with existing non-NULL filled_at, run backfill SQL | `filled_at` unchanged | unit | SHOULD |
| `test_grace_period_uses_filled_at` | Insert MARKET signal with filled_at set, check kraken-sync grace period | Grace period calculated from filled_at (same value as posted_at) | integration | SHOULD |

---

## 6. Acceptance Criteria

1. **Zero NULL filled_at for FILLED signals:** `SELECT COUNT(*) FROM signals WHERE fill_status='FILLED' AND filled_at IS NULL` returns 0 (after backfill + new code)
2. **New MARKET orders get filled_at:** Every new MARKET order INSERT sets `filled_at = posted_at`
3. **LIMIT orders unaffected:** New LIMIT orders still have `filled_at = NULL` at INSERT (set later by `check_limit_fills()`)
4. **All existing tests pass:** Zero regressions
5. **Hold time calculations correct:** `portfolio_stats.py` reports same hold times (no functional change, just cleaner data source)

---

## 7. Rollback Plan

1. **Code rollback:**
   - `git revert <commit-hash>` — removes `filled_at` from INSERT statement
   - New signals will again have NULL filled_at for MARKET orders
   - Existing fallback logic (`filled_at or posted_at`) handles this gracefully
2. **Data rollback:**
   - The backfill set `filled_at = posted_at` for 16 signals. To undo:
   ```sql
   -- Only if needed (generally harmless to leave):
   UPDATE signals SET filled_at = NULL
   WHERE order_type = 'MARKET'
     AND filled_at = posted_at
     AND id IN (/* specific IDs from pre-backfill audit */);
   ```
   - **FORGE recommendation:** Don't undo the backfill — `filled_at = posted_at` is the correct value regardless.
3. **No service restart needed** — micro-gate-v3.py is invoked per-batch, not a long-running service.

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| INSERT statement parameter count mismatch | Low | High (INSERT fails) | Test with dry_run before deploy; count ? placeholders carefully |
| Backfill affects wrong signals | Very Low | Low | WHERE clause is precise (order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL) |
| filled_at value semantically wrong for some signals | Very Low | Low | posted_at is the best available timestamp for MARKET fill time |
| Grace period behavior changes | Zero | — | `filled_at or posted_at` → `filled_at` (same value); no functional change |

---

## 9. Evidence

**Files read:**
- `scripts/micro-gate-v3.py` (commit `521d4411`) — full INSERT path in `_process_signal()`, confirmed `filled_at` not in column list
- `scripts/kraken-sync.py` lines 540-570 — grace period logic using `filled_at or posted_at`
- `scripts/kraken-sync.py` lines 712-758 — `check_limit_fills()` sets `filled_at` on limit transitions
- `scripts/portfolio_stats.py` lines 405-410 — hold time calculation using `filled_at or posted_at`

**Queries run:**
```sql
SELECT COUNT(*) FROM signals WHERE filled_at IS NULL AND fill_status='FILLED';
-- Result: 16

SELECT COUNT(*) FROM signals WHERE filled_at IS NOT NULL AND fill_status='FILLED';
-- Result: 413

SELECT order_type, COUNT(*) FROM signals GROUP BY order_type;
-- Result: MARKET=380, LIMIT=109

SELECT fill_status, COUNT(*) FROM signals GROUP BY fill_status;
-- Result: FILLED=429, PENDING=15, EXPIRED_UNFILLED=40, CANCELLED=1, UNFILLED=4
```

**Grep verification:**
```bash
grep -n "filled_at" scripts/micro-gate-v3.py
# Result: 0 matches — confirmed filled_at is NEVER referenced in micro-gate
```

---

## 10. Design Questions for Mike

### DQ-1: fill_price for MARKET Orders

Should A3 also set `fill_price = entry_price` for MARKET orders at INSERT time? Currently `fill_price` is NULL for MARKET orders until they close. Setting `fill_price = entry_price` would be semantically correct (MARKET orders fill at approximately entry price), but it's a minor additional scope.

**FORGE recommendation:** Keep A3 focused on `filled_at` only. If `fill_price` for MARKET orders is desired, it can be a trivial follow-up or folded into A3 with Mike's approval.
