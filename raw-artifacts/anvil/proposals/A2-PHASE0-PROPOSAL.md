# Phase 0 — Technical Proposal: Task A2

## remaining_pct Model + Partial-Close PnL Accuracy

**Task:** A2 — remaining_pct model, close_pct extraction, calculate_blended_pnl() rewrite
**Tier:** 🔴 CRITICAL (Financial Hotpath #1 — calculate_blended_pnl())
**Phase 4 Ref:** §1 (remaining_pct implementation specification), Phase A critical path step 3–5
**Author:** ⚒️ ANVIL
**Date:** 2026-04-19
**Proposal Version:** 1.0
**Depends on:** A1 (signal_events + TP_HIT instrumentation) — ✅ MERGED

---

## 1. Problem Statement

`calculate_blended_pnl()` uses **fixed allocation weights** (50/50 for 1 TP, 50/50 for 2 TPs, 50/25/25 for 3 TPs) regardless of actual close percentages communicated by signal providers. This produces incorrect ROI for any signal where the actual close percentage differs from the hardcoded split.

**FET #1159 (reference case):**
- LONG entry 0.2285, TP1=0.2439, exit at SL=0.2285 (trailed to entry after TP1 hit)
- Current stored ROI: **3.37%** — uses 50% weight on TP1 hit, 50% on exit at entry
- Actual ROI depends on the provider's close percentage for TP1
- If TP1 closes 25%: `0.25 × ((0.2439-0.2285)/0.2285) + 0.75 × 0 = 1.68%`
- If TP1 closes 50%: `0.50 × 6.74% + 0.50 × 0 = 3.37%` (current calculation)
- The 3.37% is only correct if the provider actually closed 50% at TP1

**Scale:** 36 of 260 closed signals have at least one TP hit. Every one of these may have an incorrect ROI.

**Root cause:** No `close_pct` is captured from provider alerts, and no per-signal tracking of how much position remains open.

---

## 2. Approach

### 2A. New Column: `remaining_pct` on `signals` table

```sql
ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0;
```

- **Semantics:** Percentage of original position still open (100.0 = fully open, 0.0 = fully closed)
- **Default 100.0** for all existing signals — no data migration needed beyond the ALTER
- **Updated on each TP hit:** `remaining_pct = remaining_pct - close_pct`
- Safe: purely additive, nullable, no existing column affected

### 2B. close_pct Extraction from TP_HIT Context

When oink-sync detects a TP hit in `_process_tp_hits()`, the close percentage must come from somewhere. There are **two possible sources**, and the proposal must be clear about which A2 covers:

#### Source 1: Provider alert text (reconciler/signal_router.py)
Providers like Cornix emit alerts like "TP1 (25%) hit" or "Closed 25% at TP1". Extracting `close_pct` from these messages requires:
- Regex enhancement in signal_router.py or the reconciler
- Parsing TP hit notification messages (which are UPDATE-type, not INSERT-type)
- Storing `close_pct` on the TP_HIT event or on the signals row

**Problem:** oink-sync's `_process_tp_hits()` detects TPs by **price comparison** (current price ≥ TP level), NOT from provider messages. oink-sync has no access to the original alert text. By the time oink-sync sees a TP hit, the provider may or may not have sent a close notification.

#### Source 2: Default close percentages based on TP structure
When `close_pct` is not available from provider text, use a configurable fallback:
- 1 TP defined: TP1 closes 100%
- 2 TPs defined: TP1 closes 50%, TP2 closes 50%  
- 3 TPs defined: TP1 closes 33%, TP2 closes 33%, TP3 closes 34%

This is already what happens implicitly in the current fixed-weight system, but it's not stored per-signal.

#### Decision: A2 scope

**A2 implements Source 2 (structured fallback) + the infrastructure for Source 1.**

Rationale:
- Source 1 (provider text extraction) requires changes to signal_router.py or reconciler — those are separate modules with separate review surface
- A2's value is: (a) make the allocation per-signal instead of hardcoded, (b) store it on the event for auditability, (c) build the plumbing so Source 1 can plug in later
- The `alloc_source` field ("assumed" vs "extracted") enables tracking which signals have real vs default percentages

**Future follow-up:** Extract `close_pct` from Cornix/WG TP hit messages in signal_router.py and write to the TP_HIT event's `close_pct` field. That follow-up replaces "assumed" with "extracted" allocations.

### 2C. `calculate_blended_pnl()` Rewrite

**Current signature:**
```python
def calculate_blended_pnl(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit) -> float
```

**New signature:**
```python
def calculate_blended_pnl(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit, remaining_pct=None, tp_close_pcts=None) -> float
```

**Logic:**
1. If `tp_close_pcts` is provided (dict like `{1: 25.0, 2: 25.0}`), use those weights
2. Else if `remaining_pct` is provided and < 100.0, derive weights from remaining_pct + TP hit count
3. Else fall back to current fixed-weight logic (backward compatible — no behavior change for callers that don't pass the new params)

**Key constraint:** Existing callers that don't pass `remaining_pct` or `tp_close_pcts` get **exactly the same result as today**. Zero regression for signals without the new data.

### 2D. TP_HIT Event Enhancement

A1 already emits TP_HIT events from `_process_tp_hits()`. A2 extends the payload:

```python
self._log_event(conn, "TP_HIT", sig_id, {
    "tp_level": tp_idx,
    "tp_price": tp_val,
    "close_pct": close_pct,           # NEW: percentage closed at this TP
    "remaining_pct": new_remaining,    # NEW: remaining after this close
    "alloc_source": "assumed",         # NEW: "assumed" or "extracted"
    "current_price": current,
    "new_sl": new_sl,
    "old_sl": old_sl,
    ...
})
```

### 2E. `remaining_pct` Update in `_process_tp_hits()`

On each TP hit:
1. Determine `close_pct` (from event data if "extracted", else from default table)
2. Read current `remaining_pct` from the signal row (or 100.0 if NULL)
3. Compute `new_remaining = remaining_pct - close_pct`
4. Clamp: `new_remaining = max(0.0, new_remaining)`
5. UPDATE signals SET remaining_pct = ? WHERE id = ?
6. Emit TP_HIT event with close_pct and remaining_pct in payload

### 2F. Backfill Strategy for Existing Signals

**No retroactive backfill of remaining_pct for existing closed signals.** Rationale:
- 260 closed signals, 36 with TP hits — none have close_pct data
- Retroactively guessing close_pct would use the same default assumptions
- Better to leave existing signals as-is (remaining_pct = NULL = "pre-A2 signal") and let the new logic apply to future signals
- `calculate_blended_pnl()` backward-compat path handles NULL remaining_pct identically to current behavior

**Exception:** If Mike wants, a follow-up can backfill remaining_pct = 100.0 on all ACTIVE signals so the field is non-NULL going forward. Low risk, tracked as deferred.

---

## 3. Files Changed

| File | Repo | Change | Risk |
|------|------|--------|------|
| `oink_sync/lifecycle.py` | oink-sync | `_process_tp_hits()`: compute close_pct, update remaining_pct, enhance TP_HIT event payload; `_check_sl_tp()` closure block: pass remaining_pct to blended_pnl | 🔴 Financial Hotpath #1, #2 |
| `oink_sync/lifecycle.py` | oink-sync | `calculate_blended_pnl()`: extend signature, add event-sourced weight path | 🔴 Financial Hotpath #1 |
| `tests/test_lifecycle_events.py` | oink-sync | New tests for remaining_pct + blended PnL | — |
| `tests/test_remaining_pct.py` | oink-sync | **New file:** dedicated remaining_pct + blended PnL test suite | — |

### Files NOT changed (scoping boundary)
- `signal_router.py` — No provider text extraction in A2 (follow-up)
- `micro-gate-v3.py` — No changes; micro-gate handles INSERTs, not TP hit detection
- `event_store.py` — No schema changes needed; payload is JSON (existing TEXT column)
- `scripts/event_store.py` (canonical) — No changes

---

## 4. Schema Change

```sql
-- Single additive column
ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0;
```

**Rollback:**
- SQLite: Cannot DROP COLUMN. But remaining_pct column with 100.0 defaults is harmless to leave in place.
- Functional rollback: revert lifecycle.py to pre-A2 (remaining_pct ignored, blended_pnl uses fixed weights)
- Column can be cleaned up in a future schema housekeeping pass if A2 is fully reverted

---

## 5. Default Close Percentage Table

| TPs Defined | TP1 close_pct | TP2 close_pct | TP3 close_pct | Source |
|-------------|--------------|--------------|--------------|--------|
| 1           | 100%         | —            | —            | Phase 4 spec |
| 2           | 50%          | 50%          | —            | Current behavior |
| 3           | 50%          | 25%          | 25%          | Current behavior |

**Note:** The Phase 4 spec says "TP1 (25%)" in the example, suggesting some providers close 25% per TP. The default table above preserves current behavior. When `alloc_source: "extracted"` is available (future), the actual close percentage overrides.

**Open question for Mike:** Should the default table change to equal-split (33/33/34 for 3 TPs) or keep the current 50/25/25? This affects all "assumed" allocations going forward. The spec example of 25% suggests equal-split may be intended. **Recommendation:** Keep 50/25/25 as default for now (matches current behavior), add a config option to lifecycle.cfg for alternative default splits. This avoids changing PnL for existing-pattern signals while enabling future tuning.

---

## 6. Test Strategy

### 6A. FET #1159 Regression Test
- Entry=0.2285, TP1=0.2439, exit=0.2285, direction=LONG
- With remaining_pct=None (pre-A2 signal): ROI = 3.37% (current behavior, no regression)
- With remaining_pct=75.0 (TP1 closed 25%): ROI = 1.68%
- With remaining_pct=50.0 (TP1 closed 50%): ROI = 3.37%

### 6B. Multi-TP Scenarios
- 3 TPs defined, all 3 hit: remaining_pct goes 100 → 50 → 25 → 0
- 2 TPs defined, TP1 hit, then SL at entry: weighted blended PnL
- 1 TP defined, TP1 hit: remaining_pct = 0, fully closed at TP

### 6C. Edge Cases
- remaining_pct underflow: close_pct > remaining_pct → clamp to 0
- NULL remaining_pct (pre-A2 signal): fallback to fixed-weight path
- 0 TPs defined: no TP hits possible, remaining_pct stays 100.0
- TP hit with close_pct = 0: no-op (defensive)

### 6D. Backward Compatibility
- All existing `calculate_blended_pnl()` callers get identical results
- Existing signals with NULL remaining_pct behave exactly as before
- No change to signals that never hit a TP

### 6E. Integration: Event Payload Verification
- TP_HIT events contain close_pct, remaining_pct, alloc_source
- Sequential TP hits: remaining_pct decreases correctly across events

---

## 7. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| AC1 | `remaining_pct` column exists on signals table with DEFAULT 100.0 | `PRAGMA table_info(signals)` |
| AC2 | TP hit updates remaining_pct on the signal row | SELECT after simulated TP hit |
| AC3 | TP_HIT event payload includes close_pct, remaining_pct, alloc_source | Event query after TP hit |
| AC4 | `calculate_blended_pnl()` with remaining_pct=None returns same result as current | FET #1159: 3.37% unchanged |
| AC5 | `calculate_blended_pnl()` with remaining_pct=75 (25% TP1 close) returns 1.68% for FET #1159 | Math verification |
| AC6 | remaining_pct never goes below 0.0 | Edge case test |
| AC7 | alloc_source = "assumed" for all A2 allocations (no extraction yet) | Event payload check |
| AC8 | No regression in existing lifecycle tests | Full test suite pass |

---

## 8. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Incorrect PnL for future signals | HIGH | FET #1159 regression test + 5 additional scenarios with known expected ROI |
| Existing signals get different PnL | HIGH | Backward-compat: NULL remaining_pct = fixed-weight path. Zero change for existing. |
| remaining_pct drift from actual position | MEDIUM | alloc_source tracking enables future audit. Reconciler can verify. |
| ALTER TABLE on production with active writes | LOW | Single additive column with DEFAULT. oink-sync holds no long transactions. |
| close_pct extraction accuracy (future) | N/A | Not in A2 scope. Follow-up item. |

---

## 9. Rollback Plan

1. **Git revert** the lifecycle.py changes → remaining_pct column stays but is ignored
2. `calculate_blended_pnl()` reverts to fixed-weight-only path
3. remaining_pct column is harmless (DEFAULT 100.0, not read by any other code)
4. TP_HIT events with close_pct payload are also harmless (payload is advisory)
5. No data corruption possible — remaining_pct is written alongside (not instead of) existing fields

---

## 10. Deferred Items (tracked)

| Item | Reason | Follow-up file |
|------|--------|---------------|
| Provider text close_pct extraction | Requires signal_router.py/reconciler changes, separate review surface | `followups/A2-DEFERRED-CLOSE-PCT-EXTRACTION.md` |
| Backfill remaining_pct=100.0 on ACTIVE signals | Low value, Mike decision | `followups/A2-DEFERRED-ACTIVE-BACKFILL.md` |
| Configurable default close_pct splits | Nice-to-have, not blocking | In lifecycle.cfg when needed |
| ROI audit of 50 signals (Phase A gate) | Depends on A2 being in production + having real data | Phase A gate checklist |

---

## 11. Lessons Applied from A1

| A1 Lesson | A2 Application |
|-----------|---------------|
| Zero-event root cause (commit=True) | remaining_pct UPDATE is in the same transaction as tp_hit_at UPDATE — no dangling writes |
| Non-fatal wrapper scope | remaining_pct UPDATE is part of the signal mutation, NOT wrapped in event try/except. Only the TP_HIT event INSERT is wrapped. |
| Vendored copy divergence | No new vendoring in A2 — changes are only in oink-sync lifecycle.py |
| LIFECYCLE_EVENTS completeness | No new event types in A2 — TP_HIT already in the set |
| Test naming accuracy | All test names match what they assert |

---

*End of A2 Phase 0 Proposal v1.0*
*Tier: 🔴 CRITICAL — Financial Hotpath #1 (calculate_blended_pnl())*
*Ready for VIGIL + GUARDIAN review*
