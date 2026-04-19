# Task A.2: remaining_pct Model + Blended PnL Fix

## ⚠️ POST-AUDIT REVISIONS

**Date:** 2026-04-19
**Auditor:** OinkV 👁️🐷

This plan has been revised after OinkV code audit (see `OINKV-AUDIT.md`). Key changes:

- **Dead-code redirect:** `calculate_blended_pnl()` is in `oink-sync/oink_sync/lifecycle.py` (line ~102, module-level function), NOT `scripts/kraken-sync.py` (inactive since 2026-04-07). `check_sl_tp()` is a method — `LifecycleManager._check_sl_tp()` (line ~259) — and TP handling is delegated to a separate method `LifecycleManager._process_tp_hits()` (line ~358). The `remaining_pct` decrement must live in `_process_tp_hits()`, not `_check_sl_tp()`.
- **Corrected `calculate_blended_pnl()` signature:** The oink-sync version has **no `leverage` parameter** (leverage-free zone — Mike directive 2026-03-23 enforced at type level) and uses **boolean `tp*_hit` params, not timestamps**. The rewrite applies to the oink-sync signature: `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit)`.
- **Service + repo:** Rollback service restart is `systemctl --user restart oink-sync` (user-level, no sudo). Active lifecycle code lives in a separate standalone repo (`oink-sync`), not in `oinkfarm/scripts/`.

---

**Source:** Arbiter-Oink Phase 4 §1 (remaining_pct model), Phase 2 V2 (PnL accuracy)
**Tier:** 🔴 CRITICAL
**Dependencies:** A1 (signal_events table — TP_HIT events with close_pct in payload)
**Estimated Effort:** Phase 4 says 1-2 days; FORGE assessment: 2-3 days (regex extraction across multiple alert formats + PnL rewrite + thorough testing)
**Plan Version:** 1.0
**Codebase Verified At:** `521d4411` (2026-04-18)

---

## 0. Executive Summary

The current `calculate_blended_pnl()` function in `kraken-sync.py` (line ~316) uses **fixed allocation weights** (TP1=50%, TP2=25%, TP3=25%) regardless of what the trader's actual partial-close percentages are. This overstates or understates ROI — the Arbiter-Oink report identifies FET #1159 as a concrete example where the displayed ROI was 3.37% vs the actual 1.68%.

This plan:
1. **Adds `remaining_pct` column** to the `signals` table (FLOAT DEFAULT 100.0)
2. **Captures `close_pct`** from TP_HIT events (extracted from alert text or assumed from standard splits)
3. **Rewrites `calculate_blended_pnl()`** to use event-sourced close percentages
4. **Updates `check_sl_tp()`** to decrement `remaining_pct` on each TP hit
5. **Flags assumed vs extracted allocations** in the TP_HIT event payload (`alloc_source: "extracted"|"assumed"`)

---

## 1. Current State Analysis

### Current PnL Calculation

**Function:** `calculate_blended_pnl()` in `oink-sync/oink_sync/lifecycle.py` (line ~102, module-level function)

```python
def calculate_blended_pnl(
    entry: float, exit_price: float, direction: str,
    tp1, tp2, tp3,
    tp1_hit, tp2_hit, tp3_hit,   # ← booleans (truthy/falsy), NOT timestamps
) -> float:
```

**Current behavior:**
- No `leverage` parameter (removed in oink-sync port — Mike directive enforced at the type level)
- `tp*_hit` params are booleans (truthy = hit), not timestamp strings
- Fixed weight map based on how many TPs are *defined* (not how many hit):
  - 1 TP defined: TP1=50%, remainder=50% at exit
  - 2 TPs defined: TP1=50%, TP2=50%
  - 3 TPs defined: TP1=50%, TP2=25%, TP3=25%
- Iterates over hit TPs, applies weight, remainder exits at `exit_price`
- Leverage is intentionally ignored (Mike directive 2026-03-23)
- Returns `round(blended, 4)`

**Current callers:**
- `check_sl_tp()` in `kraken-sync.py` (line ~659) — called on SL hit closure
- No other callers found (grep verified)

### The Problem

The fixed 50/25/25 split doesn't match reality:
- Some providers close 25% at TP1, 25% at TP2, 50% at TP3
- Some providers close 33/33/34
- WG (Wealth Group) typically does 50/25/25, but not always
- When TP1 hits at 25% and the rest closes at SL, the blended PnL is very different from a 50% close at TP1

**FET #1159 reference case:** Entry=0.065, TP1 hit at 0.068 (25% close), rest closed at SL. Current system reports 3.37% ROI (assuming 50% close at TP1). Actual ROI with 25% close = 1.68%.

### Current Data State

```sql
-- No remaining_pct column exists:
-- PRAGMA table_info(signals) shows 49 columns, none named remaining_pct

-- TP hit distribution:
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN tp1_hit_at IS NOT NULL THEN 1 ELSE 0 END) as tp1_hits,
  SUM(CASE WHEN tp2_hit_at IS NOT NULL THEN 1 ELSE 0 END) as tp2_hits,
  SUM(CASE WHEN tp3_hit_at IS NOT NULL THEN 1 ELSE 0 END) as tp3_hits
FROM signals WHERE status IN ('CLOSED_WIN', 'CLOSED_LOSS', 'CLOSED_BREAKEVEN');
-- Result: total=326, tp1_hits=TBD, tp2_hits=TBD, tp3_hits=TBD
-- (ANVIL should run this exact query to understand current TP hit patterns)

-- Signals count:
SELECT COUNT(*) FROM signals;
-- Result: 489
```

### Key Files

| File | Path | LOC | Relevance |
|------|------|-----|-----------|
| lifecycle.py | oink-sync: oink_sync/lifecycle.py | 811 | Contains `calculate_blended_pnl()` (line ~102), `LifecycleManager._check_sl_tp()` (line ~259), `_process_tp_hits()` (line ~358) |
| micro-gate-v3.py | scripts/micro-gate-v3.py | 1,393 | Closure processing, may need close_pct extraction |
| event_store.py | scripts/event_store.py | 209 | TP_HIT events will carry close_pct |

### Key Functions

| Function | File | Line (approx) | Current Signature | Change Required |
|----------|------|---------------|-------------------|-----------------|
| `calculate_blended_pnl()` | oink_sync/lifecycle.py | ~102 | `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit)` | Rewrite to use event-sourced close percentages |
| `LifecycleManager._check_sl_tp()` | oink_sync/lifecycle.py | ~259 | `(self, conn, prices)` | Add remaining_pct tracking on TP hits |
| `LifecycleManager._process_tp_hits()` | oink_sync/lifecycle.py | ~358 | `(self, conn, sig_id, ticker, ...)` | Decrement remaining_pct, store close_pct in event |
| `_process_closure()` | micro-gate-v3.py | ~1040 (approx) | `(entry, ext, conn, dry_run)` | Extract close_pct from closure alert text |

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| scripts/kraken-sync.py | `calculate_blended_pnl()` | MODIFY | Rewrite to accept close percentages from events instead of fixed weights |
| scripts/kraken-sync.py | `check_sl_tp()` | MODIFY | Decrement remaining_pct on TP hit; store close_pct in TP_HIT event; pass close_pcts to blended PnL |
| scripts/kraken-sync.py | closure path in `check_sl_tp()` | MODIFY | Read remaining_pct from DB for blended PnL on closure |
| scripts/micro-gate-v3.py | `_process_closure()` | MODIFY | Extract close_pct from closure alert text if available |
| tests/test_blended_pnl.py | — | CREATE | Comprehensive PnL calculation tests with various close percentages |
| tests/test_remaining_pct.py | — | CREATE | remaining_pct tracking through TP hit sequence |

---

## 3. SQL Changes

### 3a. Add remaining_pct column

```sql
-- Run BEFORE code changes
ALTER TABLE signals ADD COLUMN remaining_pct FLOAT DEFAULT 100.0;

-- Verification:
-- PRAGMA table_info(signals);
-- Should show remaining_pct column with DEFAULT 100.0

-- All existing signals get remaining_pct = 100.0 (correct default —
-- existing signals don't have event-sourced close data, so they'll
-- continue using the assumed allocation fallback)
```

### 3b. Backfill for active signals with TP hits already recorded

```sql
-- For signals that already have TP hits but no remaining_pct tracking,
-- we need to estimate remaining_pct from the tp*_hit_at columns.
-- This uses the current fixed weights as best-guess:

-- Signals with TP1 hit: remaining_pct = 50 (if 1 TP defined: 0)
-- Signals with TP1+TP2 hit: remaining_pct depends on TP count defined
-- etc.

-- FORGE recommendation: Do NOT backfill. Leave existing signals at 100.0
-- and flag them with alloc_source="legacy" in any future event queries.
-- The fixed-weight calculation is still used as fallback for these signals.
-- Only NEW TP hits (after this change is deployed) will have accurate remaining_pct.
```

---

## 4. Implementation Notes

### 4a. New calculate_blended_pnl() Signature

The function should be refactored to accept explicit close percentages:

```
# New approach — ANVIL decides exact signature, this is the WHAT:
# 
# Option 1: Accept a list of (tp_price, close_pct) tuples
# Option 2: Accept remaining_pct directly and compute
# 
# The key requirement: the function must use ACTUAL close percentages
# from the signal's TP_HIT events, not fixed weights derived from
# how many TP levels are defined.
#
# Fallback: when close percentages are not available (legacy signals
# or signals from providers that don't specify close %), fall back
# to the current fixed allocation with alloc_source="assumed" flag.
```

### 4b. TP Hit Flow (Modified)

Current flow: `_check_sl_tp()` delegates TP handling to `_process_tp_hits()` (separate method):
1. `_check_sl_tp()` detects SL breach → closes trade
2. If no SL breach → calls `_process_tp_hits()` which:
   - Iterates TP1→TP2→TP3 ascending
   - On hit: trails SL to previous TP level (or entry), writes alert to JSONL file
   - Returns events list

New flow:
1. TP level hit detected
2. Determine `close_pct` for this TP level:
   - **If extractable from event/alert data:** Use extracted value
   - **If not extractable:** Use standard assumed split (current weights)
3. UPDATE: `remaining_pct = remaining_pct - close_pct`, `tp*_hit_at = now`, `stop_loss = new_sl`
4. Emit TP_HIT event with `close_pct`, `remaining_pct` (new value), `alloc_source`
5. Emit SL_MODIFIED event (trailing SL)

### 4c. Close Percentage Extraction

The close percentage comes from two possible sources:

**Source 1: Alert text from reconciler/board messages**
Patterns to match (from WG and other providers):
- `"TP1 (25%)"` → close_pct = 25
- `"TP1 hit - 50% closed"` → close_pct = 50
- `"Take Profit 1 ✅ (33%)"` → close_pct = 33
- `"TP1 reached, closing 25%"` → close_pct = 25

**Source 2: Assumed from TP count** (fallback)
When text doesn't contain explicit percentages:
- 1 TP defined: TP1 = 100%
- 2 TPs: TP1 = 50%, TP2 = 50%
- 3 TPs: TP1 = 50%, TP2 = 25%, TP3 = 25%
This is the CURRENT behavior and serves as the fallback.

**Important:** In `check_sl_tp()` (kraken-sync.py), the TP hit is detected purely from price crossing the TP level — there is NO alert text available at this point. The close percentage extraction from alert text happens in the micro-gate flow when processing board updates. Therefore:

**The recommended approach for kraken-sync TP hits:**
- Use assumed split as default (same as current behavior)
- Store `alloc_source: "assumed"` in the TP_HIT event payload
- When a board update later confirms the close percentage, micro-gate can emit a corrective event or update the signal's close data

**The recommended approach for micro-gate board closures:**
- Extract close_pct from the alert/closure text using regex
- Store `alloc_source: "extracted"` in the event payload
- If close_pct cannot be extracted, use assumed split

### 4d. Closure PnL Calculation (Modified)

When a trade is closed (SL hit in `check_sl_tp()`), the new flow:

1. Read `remaining_pct` from the signal's current DB state
2. Query `signal_events` for this signal's TP_HIT events to get the close percentages at each TP level
3. Compute blended PnL: `sum(close_pct/100 * pnl_at_tp_price) + (remaining_pct/100 * pnl_at_exit_price)`
4. Or equivalently: modify `calculate_blended_pnl()` to read close_pct from events if available, else fall back to current weights

**Performance note:** Reading from `signal_events` adds a SELECT query per closure. With ~1-5 closures/day and an indexed table, this is negligible.

### 4e. Edge Cases

| Edge Case | Handling |
|-----------|----------|
| All TPs hit, then SL hit | remaining_pct should be 0 (or very small). Blended PnL = weighted sum of all TP exits. |
| No TPs hit, SL hit | remaining_pct = 100. Simple PnL = pnl_at_exit_price. |
| TP1 hit (50%), then trade manually closed | remaining_pct = 50. Blended = 50% at TP1 + 50% at exit. |
| Close_pct extraction finds > 100% total | Cap at 100%. Log anomaly. |
| Close_pct = 0 in alert text | Skip — treat as informational, not a partial close. |
| Remaining_pct goes negative | Guard: `remaining_pct = max(0, remaining_pct - close_pct)` |
| Legacy signals (pre-deployment) | remaining_pct = 100.0 (DEFAULT), fallback to assumed weights |
| Signal with TP hits but remaining_pct = 100 (pre-deployment) | Detected by: `tp1_hit_at IS NOT NULL AND remaining_pct = 100.0`. Use assumed weights. |

### 4f. Backward Compatibility

- `remaining_pct DEFAULT 100.0` means ALL existing signals get 100.0 — this is correct
- The old `calculate_blended_pnl()` behavior is preserved as the fallback when close percentages are unavailable
- Existing closed signals retain their already-computed `final_roi` — no retroactive recalculation
- New closures after deployment use the improved calculation
- API endpoints that return `final_roi` or `pnl_percent` continue to work (they read from the DB column, not recalculate)

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_fet_1159_correct_roi` | entry=0.065, TP1 hit at 0.068 (25% close), SL hit at 0.063 (75% remaining) | ROI ≈ 1.68% (not 3.37%) | unit | MUST |
| `test_standard_50_25_25_split` | entry=100, TP1=105 (50%), TP2=110 (25%), SL hit at 98 (25% remaining) | Blended = 0.5×5% + 0.25×10% + 0.25×(-2%) = 4.5% | unit | MUST |
| `test_no_tp_hit_simple_pnl` | entry=100, SL hit at 95, no TPs hit | ROI = -5.0%, remaining_pct = 100 | unit | MUST |
| `test_all_tp_hit_full_close` | entry=100, TP1=105 (50%), TP2=110 (25%), TP3=115 (25%), all hit, then SL (0% remaining) | Blended = 0.5×5% + 0.25×10% + 0.25×15% = 8.75% | unit | MUST |
| `test_remaining_pct_decrements` | Signal created (100%), TP1 hit (25% close), check remaining_pct | remaining_pct = 75.0 | integration | MUST |
| `test_remaining_pct_double_tp` | TP1 hit (50%), TP2 hit (25%), check remaining_pct | remaining_pct = 25.0 | integration | MUST |
| `test_remaining_pct_negative_guard` | TP1 hit (60%), TP2 hit (60%), check remaining_pct | remaining_pct = 0.0 (clamped, not -20) | unit | MUST |
| `test_assumed_vs_extracted_flag` | TP hit without text extraction vs with "TP1 (25%)" text | Event payload: alloc_source="assumed" vs "extracted" | unit | SHOULD |
| `test_legacy_signal_fallback` | Signal with tp1_hit_at set but remaining_pct=100 (pre-deployment) | Falls back to assumed weights, correct PnL | unit | MUST |
| `test_short_direction_pnl` | SHORT entry=100, TP1=95 (50% close), SL hit at 102 | Blended = 0.5×5% + 0.5×(-2%) = 1.5% | unit | MUST |
| `test_blended_pnl_closure_event` | Full lifecycle: insert → TP1 hit → SL closure | TRADE_CLOSED event has correct final_roi using event-sourced close_pcts | integration | MUST |

---

## 6. Acceptance Criteria

1. **FET #1159 passes:** A test scenario matching FET #1159 (entry=0.065, TP1 hit at 0.068 with 25% close, SL hit rest) produces ROI within 0.1pp of 1.68%
2. **remaining_pct tracks correctly:** After each TP hit, `SELECT remaining_pct FROM signals WHERE id=X` shows the correct decremented value
3. **TP_HIT events carry close_pct:** `SELECT payload FROM signal_events WHERE event_type='TP_HIT'` JSON payloads include `close_pct` and `alloc_source` keys
4. **Backward compatibility:** Existing closed signals' `final_roi` values are UNCHANGED
5. **Fallback works:** Signals without extractable close_pct still get correct PnL using assumed weights
6. **All existing tests pass:** Zero regressions
7. **PnL accuracy improvement measurable:** Manual audit of 10 new closures post-deployment shows ROI error < 0.5pp

---

## 7. Rollback Plan

1. **Schema rollback:**
   ```sql
   -- SQLite cannot DROP COLUMN in older versions; if needed:
   -- Create backup table without remaining_pct, copy data, rename
   -- But simpler: remaining_pct DEFAULT 100.0 is harmless if unused
   ```
2. **Code rollback:**
   - `git revert <commit-hash>` — reverts calculate_blended_pnl() changes and remaining_pct tracking
   - The old fixed-weight calculation is restored
3. **Data safety:**
   - Existing `final_roi` values in the DB are NOT modified by this change
   - remaining_pct column remains at 100.0 for all pre-deployment signals
   - No data migration or backfill to undo
4. **Service restart:**
   - `systemctl --user restart oink-sync`
5. **Verification:**
   - Run `calculate_blended_pnl()` with known inputs → confirm old behavior restored
   - Check that ACTIVE signals are still monitored correctly

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| PnL calculation regression (wrong ROI for new closures) | Medium | HIGH | FET #1159 test + 10 additional test vectors covering all edge cases |
| remaining_pct drift on concurrent writes | Very Low | Medium | SQLite serialized writes; kraken-sync is single-process |
| Close_pct extraction regex mismatches | Medium | Low | Fallback to assumed weights with `alloc_source="assumed"` flag; regex can be refined iteratively |
| Existing signals' final_roi retroactively wrong | Zero | — | Plan explicitly does NOT recalculate historical PnL |
| Performance impact from signal_events query on closure | Very Low | Low | Indexed query, ~1-5 closures/day, <1ms per query |
| Assumed weights differ from actual provider splits | Medium (ongoing) | Medium | `alloc_source` flag allows post-hoc audit; accuracy improves as more providers' close_pct patterns are extracted |

---

## 9. Evidence

**Files read:**
- `scripts/kraken-sync.py` lines 298-400: `calculate_pnl()` and `calculate_blended_pnl()` — full function bodies
- `scripts/kraken-sync.py` lines 540-710: `check_sl_tp()` — full function body including TP hit path and closure path
- `scripts/micro-gate-v3.py` lines 1040+: `_process_closure()` — closure matching and PnL override logic

**Queries run:**
```sql
PRAGMA table_info(signals);
-- Result: 49 columns, no remaining_pct

SELECT fill_status, COUNT(*) FROM signals GROUP BY fill_status;
-- Result: FILLED=429, PENDING=15, EXPIRED_UNFILLED=40, CANCELLED=1, UNFILLED=4

SELECT order_type, COUNT(*) FROM signals GROUP BY order_type;
-- Result: MARKET=380, LIMIT=109

SELECT COUNT(*) FROM signals WHERE filled_at IS NULL AND fill_status='FILLED';
-- Result: 16

SELECT COUNT(*) FROM signals WHERE filled_at IS NOT NULL AND fill_status='FILLED';
-- Result: 413
```

**Key code observations:**
- `calculate_blended_pnl()` is only called from `check_sl_tp()` (grep verified)
- Leverage is stripped from PnL calculation (Mike directive 2026-03-23)
- TP hits in `check_sl_tp()` only trail SL — they NEVER close the trade (board is authoritative for closures)
- The `_write_alert()` call on TP hit already tracks `remaining_tps` but NOT close_pct

---

## 10. Design Questions for Mike

### DQ-1: Retroactive PnL Recalculation

Should FORGE/ANVIL produce a one-time backfill script that recalculates `final_roi` for existing closed signals using the correct close percentages (where determinable)?

**Option A (Recommended):** No retroactive recalculation. Existing `final_roi` values are preserved. Only new closures after deployment use the improved calculation. Rationale: extracting historical close percentages is unreliable without event data, and changing historical ROI may confuse users.

**Option B:** Run a one-off correction for signals where the actual close_pct can be determined from raw_text patterns. Flag corrected signals in notes.

### DQ-2: Default Close Percentages by Provider

Different trading signal providers use different standard splits. Should we maintain a per-provider (per-server) configuration mapping for assumed close percentages?

**Current approach:** Hard-coded 50/25/25 for all providers.
**Proposed approach:** Per-server configuration in `channel-registry.json` or a new config, e.g.:
```json
{ "wealthgroup": {"tp_splits": [50, 25, 25]}, "stock-vip": {"tp_splits": [33, 33, 34]} }
```

**FORGE recommendation:** Start with the hard-coded fallback (current behavior). Add per-provider config as a follow-up task if the `alloc_source="assumed"` audit reveals significant differences across providers.
