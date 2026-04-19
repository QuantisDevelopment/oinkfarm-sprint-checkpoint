# Task A7: UPDATE→NEW Detection (Phantom Trade Prevention)

**Source:** Arbiter-Oink Phase 4 V2, Phase A element; DOC3 EC-B1 (risk score 60)  
**Tier:** 🔴 CRITICAL — Phantom trades corrupt signal counts, trader performance, and PnL aggregates  
**Dependencies:** A1 (event_store — shipped), A4 (PARTIALLY_CLOSED — should ship first to include in status check)  
**Repo:** bandtincorporated8/oinkfarm  
**Canonical file:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, 61,460 bytes, HEAD `498d8b28`)  
**Note:** The signal-gateway copy at `scripts/micro-gate-v3.py` (1,063 LOC) is stale — do NOT use it as the implementation target.

---

## 0. Executive Summary

When an LLM extraction classifies a trader UPDATE message (e.g., "SL moved to 0.48") as a NEW signal, the current INSERT path creates a phantom duplicate — a second signal for the same trader/ticker/direction alongside the real one. This is the single most damaging extraction failure mode because it inflates signal counts, corrupts win rates, and creates irreconcilable PnL discrepancies.

**The fix:** Before INSERT, check if an ACTIVE/PENDING/PARTIALLY_CLOSED signal already exists for the same (trader_id, ticker, direction). If found, reclassify as UPDATE and route to the existing UPDATE handler instead of inserting a new row.

**Scope:** micro-gate-v3.py INSERT path only. Three existing protection layers are complementary:
- **Board reconciler** (signal-gateway repo): B10 flip-flop suppression (reconciler.py:141-146)
- **signal_router cross-channel dedup** (signal-gateway repo): exact (trader, ticker, direction, entry) match at line 3589+
- **micro-gate §4b CROSS_CHANNEL_DUPLICATE guard** (canonical micro-gate line 656-680): exact (trader_id, ticker, direction, entry_price) match

A7 adds a **fourth, fuzzier layer** inside micro-gate that catches the residual set: same trader/ticker/direction but entry price within 5% (UPDATE misclassified as NEW).

---

## 1. Current State Analysis

### The Gap: Text Extraction Path Has No UPDATE→NEW Guard

There are three ingestion paths that reach micro-gate:

| Path | UPDATE→NEW Protection | How |
|------|----------------------|-----|
| Board reconciler | ✅ Has protection | B10 flip-flop suppression (reconciler.py:141-146), entry-correction detection (175-214) — signal-gateway repo |
| signal_router cross-channel dedup | ✅ Has protection | signal_router.py line 3589+ — exact match on (trader, ticker, direction, entry_price) — signal-gateway repo |
| micro-gate §4b CROSS_CHANNEL_DUPLICATE | ✅ Has protection | canonical micro-gate line 656-680 — exact (trader_id, ticker, direction, entry_price) match |
| Text extraction → OinkDB → micro-gate NEW (fuzzy) | ❌ **NO PROTECTION** | LLM classifies UPDATE as NEW → OinkDB sends as NEW → micro-gate INSERTs if entry price differs slightly from existing |

The cross-channel dedup in signal_router.py requires **exact entry_price match**, so it doesn't catch:
- UPDATE messages where the LLM extracts a slightly different entry (e.g., market price instead of original entry)
- Messages where the LLM invents an entry price from context

### Current INSERT Path (canonical micro-gate line 608-897)

The `_process_signal()` function (line 608) handles NEW signals. Steps 1-15 validate and normalize. Step 16 does `INSERT OR IGNORE` (line 855). There is **no fuzzy check** between step 14 (trader FK resolution, line 832) and step 16 (INSERT) for existing active positions with similar entry prices. The exact-match §4b guard (line 656-680) fires earlier but only catches byte-identical entry prices.

### Known Production Impact

From OinXtractor memory (Q1 error pattern): **15 phantom trades** traced to UPDATE→NEW misclassification. These are signals where:
- The same trader had an active position in the same ticker + direction
- The LLM extracted a "new signal" from what was actually a position update
- The phantom signal was inserted alongside the real one

### Existing `_match_active()` Function (canonical micro-gate line 368)

```python
def _match_active(conn, trader_name, ticker, direction, server_id):
    """Match an UPDATE/CLOSURE to active DB position.
    Returns (signal_row, confidence) or (None, reason).
    """
```

This function already does exactly what A7 needs — it searches for ACTIVE/PENDING signals with the same (trader_id, ticker, direction) via **three** `WHERE s.status IN ('ACTIVE', 'PENDING')` clauses (lines 384, 394, 410 — exact-trader, canonical-name, and ticker-only fallback). It's currently used only by the UPDATE and CLOSURE handlers. A7 reuses it for the NEW handler.

**A4 dependency note:** When A4 ships, all three status IN clauses must add PARTIALLY_CLOSED. A7 automatically benefits from this via the shared `_match_active()` function.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_signal()` (line 608) | MODIFY | Add UPDATE→NEW check between step 14 (line 832) and step 16 (line 855) |
| `.openclaw/workspace/scripts/micro-gate-v3.py` | `_match_active()` (line 368) | MODIFY | Add PARTIALLY_CLOSED to all three status IN clauses at lines 384, 394, 410 (when A4 ships) |
| `.openclaw/workspace/scripts/event_store.py` | `LIFECYCLE_EVENTS` set (line 53) | MODIFY | Add `"UPDATE_DETECTED"` to the registry |
| `.openclaw/workspace/scripts/event_store.py` | `QUARANTINE_CODES` set (line 80) | MODIFY | Add `"A7_UPDATE_DETECTED"` to the quarantine registry |
| `.openclaw/workspace/tests/test_a7_update_detection.py` | — | CREATE | Test UPDATE→NEW detection scenarios |

### Functions NOT Modified

- `signal_router.py` (signal-gateway repo) — cross-channel dedup is a separate layer in a different repo
- `reconciler.py` (signal-gateway repo) — board path already has B10 protection
- `_match_active()` query logic — reused as-is; only status IN clause updated for A4

---

## 3. SQL Changes

### No Schema Migration Required

The signals table already has all needed columns. The `_match_active()` query just needs PARTIALLY_CLOSED added to the status IN clause (after A4 ships).

### _match_active() Query Update (after A4)

Three identical clauses must be updated (canonical lines 384, 394, 410):

```sql
-- Current (lines 384, 394, 410):
WHERE s.status IN ('ACTIVE', 'PENDING')

-- After A4 (all three sites):
WHERE s.status IN ('ACTIVE', 'PENDING', 'PARTIALLY_CLOSED')
```

Additionally, the §4b CROSS_CHANNEL_DUPLICATE guard (line 669) has a fourth `status IN ('ACTIVE', 'PENDING')` clause that should also be updated for completeness.

### event_store.py Changes

```python
# In LIFECYCLE_EVENTS set (line 53), add:
    "UPDATE_DETECTED",    # A7: phantom trade suppression

# In QUARANTINE_CODES set (line 80), add:
    "A7_UPDATE_DETECTED",  # A7: UPDATE misclassified as NEW
```

---

## 4. Implementation Notes

### 4a. The UPDATE→NEW Guard (Insert Between Steps 14 and 16)

After step 14 (trader_id resolved, canonical line 832) and before step 16 (INSERT, line 855), add:

```python
    # ── A7: UPDATE→NEW detection ──
    # Before INSERT, check if an active position already exists for this
    # trader+ticker+direction. If so, this is likely an UPDATE misclassified
    # as NEW by the LLM. Route to UPDATE handler instead.
    _A7_ENTRY_TOLERANCE_PCT = 5.0
    if trader_id is not None and ticker and direction:
        existing, match_conf = _match_active(conn, trader_name_raw, ticker, direction, server_id)
        if existing is not None and match_conf in ("exact", "ticker_only"):
            # Check if entry prices differ significantly (genuine new position)
            existing_entry = existing.get("entry_price", 0) or 0
            if existing_entry > 0 and entry_price > 0:
                price_diff_pct = abs(entry_price - existing_entry) / existing_entry * 100
                if price_diff_pct > _A7_ENTRY_TOLERANCE_PCT:
                    # Genuine new position at materially different level — allow INSERT
                    # Note: notes_parts is already joined into `notes` at step 12 (line 824),
                    # so we append directly to the `notes` string.
                    notes = (notes or "") + (
                        f" [A7: existing #{existing['id']} at {existing_entry}, "
                        f"new entry {entry_price} differs by {price_diff_pct:.1f}% — allowing INSERT]"
                    )
                else:
                    # Likely UPDATE misclassified as NEW — suppress INSERT
                    _log_rejection(entry, "A7_UPDATE_DETECTED",
                        f"Active signal #{existing['id']} exists for "
                        f"{trader_name_raw}/{ticker}/{direction} "
                        f"(entry diff {price_diff_pct:.1f}%, threshold {_A7_ENTRY_TOLERANCE_PCT}%)",
                        conn=conn)  # conn= required for quarantine table
                    
                    # Emit UPDATE_DETECTED event via module-level _log_event helper (line 61)
                    _log_event(conn, "UPDATE_DETECTED", existing["id"], {
                        "suppressed_entry": entry_price,
                        "existing_entry": existing_entry,
                        "price_diff_pct": round(price_diff_pct, 2),
                        "extraction_method": method,
                        "discord_message_id": dmid,
                    })
                    
                    return {
                        "action": "a7_update_detected",
                        "existing_signal_id": existing["id"],
                        "ticker": ticker,
                        "direction": direction,
                        "entry_price": entry_price,
                        "existing_entry": existing_entry,
                        "price_diff_pct": round(price_diff_pct, 2),
                        "reason": "UPDATE misclassified as NEW — suppressed",
                    }
```

**Key differences from v1.0 of this plan:**
- Uses module-level `_log_event()` helper (line 61) instead of inline `EventStore` import — the canonical micro-gate already has this helper with 13+ existing call sites
- Passes `conn=conn` to `_log_rejection()` so the rejection reaches the quarantine table (post-A1 signature requires it)
- Writes to `notes` string directly instead of `notes_parts` (which was already joined at line 824, step 12)
- Defines `_A7_ENTRY_TOLERANCE_PCT = 5.0` as a named constant for testability

### 4b. The 5% Threshold Rationale

The entry price threshold distinguishes between:
- **UPDATE→NEW misclassification** (entry ≈ existing entry): LLM extracted the current market price or re-extracted the original entry from context. Price diff < 5%.
- **Genuine new position** (entry ≠ existing entry): Trader opened a second position at a materially different level (e.g., averaging down, or a completely new trade after partial close). Price diff > 5%.

**Why 5%?** Based on the price deviation gates already in micro-gate: MARKET orders allow 10% deviation, LIMIT orders allow 30%. A 5% threshold is conservative enough to catch most misclassifications while permitting genuine averaging-in positions.

**Edge case: Same trader, same ticker, opposite direction** — This is already handled because `_match_active` matches on direction. A LONG and a SHORT for the same ticker are different positions and won't trigger the guard.

### 4c. The `ticker_only` Match Confidence

When `_match_active` returns `ticker_only` confidence (matched on ticker+direction but different trader attribution), A7 should still suppress. This handles the case where the LLM mis-attributes the trader name but correctly extracts the ticker.

**Code precedent:** `_process_closure` (canonical line 1063) **REFUSES** closure on `ticker_only` match with `LOW_CONFIDENCE_CLOSURE` — the established precedent for destructive/irreversible actions on weak matches is to refuse. Since an INSERT is irreversible (phantom trade), A7 should follow the same pattern.

**Recommendation:** Include `ticker_only` in the suppress set. Monitor A7_UPDATE_DETECTED rejections for the first 48h. If false positives are observed (different real traders being blocked), tighten to `exact` only.

### 4d. Event Logging

The UPDATE_DETECTED event is logged via the module-level `_log_event()` helper (canonical line 61), using the **existing signal's ID** (not the suppressed signal, which has no ID). This helper is already best-effort, uses `commit=True` (A1 fix from commit `09e0f94b`), wraps exceptions, and defaults `source="micro-gate"`. No inline import needed — 13+ existing call sites in the file use this same helper.

**Important:** `UPDATE_DETECTED` must be added to the `LIFECYCLE_EVENTS` set in `event_store.py` (line 53) before A7 ships. The event will INSERT regardless (EventStore.log doesn't validate against the set), but VIGIL and GUARDIAN check the registry. Similarly, `A7_UPDATE_DETECTED` should be added to `QUARANTINE_CODES` (line 80) so quarantine entries are properly registered.

### 4e. Interaction with signal_router.py Cross-Channel Dedup

The signal_router.py dedup (line 3591+) checks exact (trader, ticker, direction, entry_price). A7 checks (trader, ticker, direction) with a 5% entry tolerance. These are complementary:
- signal_router catches exact duplicates early (before OinkDB processing)
- A7 catches fuzzy UPDATE→NEW at the gate (after OinkDB processing)

Both can fire independently. No conflict.

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| test_a7_suppress_same_entry | NEW signal for trader X, ticker BTC, direction LONG, entry 65000. Existing ACTIVE signal #100 for same trader/ticker/direction at entry 65000 | Return `a7_update_detected`, rejection logged as A7_UPDATE_DETECTED | unit | must |
| test_a7_suppress_close_entry | Same as above but new entry 65200 (0.3% diff < 5%) | Suppress — still treated as UPDATE | unit | must |
| test_a7_allow_different_entry | Same as above but new entry 70000 (7.7% diff > 5%) | Allow INSERT — genuine new position, notes include A7 explanation | unit | must |
| test_a7_allow_no_existing | NEW signal for trader X, ticker ETH — no existing active position | Allow INSERT normally, no A7 interference | unit | must |
| test_a7_allow_opposite_direction | Existing ACTIVE LONG for BTC. New SHORT for BTC from same trader | Allow INSERT — different direction | unit | must |
| test_a7_partially_closed_match | Existing PARTIALLY_CLOSED signal (after A4). New signal same trader/ticker/direction | Suppress — PARTIALLY_CLOSED is still an active position | unit | should |
| test_a7_event_logged | Suppressed signal emits UPDATE_DETECTED event with correct payload | Event in signal_events table with suppressed_entry, existing_entry, price_diff_pct | integration | should |
| test_a7_rejection_logged | Suppressed signal logged in gate-rejections.jsonl with reason A7_UPDATE_DETECTED | JSONL entry with correct fields | unit | must |
| test_a7_no_trader_id_bypass | NEW signal with unresolvable trader (trader_id=None) | Skip A7 check entirely, proceed to INSERT | unit | should |

---

## 6. Acceptance Criteria

1. **No phantom duplicates for UPDATE→NEW misclassifications:** Given an ACTIVE/PENDING/PARTIALLY_CLOSED signal for trader X / ticker Y / direction Z, a NEW signal for the same combination with entry price within 5% is suppressed with A7_UPDATE_DETECTED rejection.

2. **Genuine new positions allowed:** When entry prices differ by >5%, the INSERT proceeds normally with an A7 note in the notes field.

3. **Event audit trail:** Every suppression emits an UPDATE_DETECTED event to signal_events with the existing signal's ID, suppressed entry, and price diff.

4. **Rejection logging:** Every suppression is logged in gate-rejections.jsonl with reason `A7_UPDATE_DETECTED`.

5. **No false suppressions in test suite:** All 9 test cases pass.

6. **Opposite direction allowed:** A LONG and SHORT for the same ticker from the same trader are independent positions.

7. **No performance impact:** The `_match_active` query is already indexed (trader_id + status + ticker + direction via existing indexes). One additional SELECT per INSERT is negligible.

---

## 7. Rollback Plan

A7 is purely defensive — it only prevents INSERTs, never modifies existing data. Rollback is:

1. **Revert the code change:** Remove the A7 block between steps 14 and 16 in `_process_signal()`
2. **No data migration needed:** No schema changes, no existing data modified
3. **Verify:** Signals suppressed during A7's operation cannot be recovered (they were never inserted). If a legitimate signal was suppressed, it would need manual re-entry via OinkDB.

**Risk of rollback:** Any phantom duplicates that A7 would have caught will resume entering the DB. This is the pre-A7 behavior.

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| False positive: legitimate new signal suppressed because trader re-enters same ticker/direction at similar price | Medium | One missed signal (recoverable via manual entry) | 5% threshold allows genuine averaging-in. Monitor A7_UPDATE_DETECTED rejections for first 48h. |
| False negative: UPDATE misclassified as NEW with entry price >5% different | Low | Phantom duplicate (same as pre-A7) | This represents a genuine price difference. The misclassification is rare when entry prices are far apart. |
| `ticker_only` match too aggressive | Medium | Suppresses signal from different trader on same ticker | Initial deploy includes `ticker_only`. If false positives observed, tighten to `exact` only. |
| Event store import fails in micro-gate context | Low | Suppression still works, event just isn't logged | try/except wraps event logging. Rejection JSONL is the primary audit trail. |

---

## 9. Evidence

### Codebase Verification (against canonical `.openclaw/workspace/scripts/micro-gate-v3.py`)

| What | Verified | Canonical Location |
|------|----------|-------------------|
| `_process_signal()` INSERT path | ✅ | line 608 (function def) through line 897 |
| `_match_active()` function | ✅ | line 368 |
| `_match_active()` status IN clauses | ✅ | lines 384, 394, 410 (three copies) + line 669 (§4b guard) |
| trader_id resolved before INSERT | ✅ | step 14, line 832 (`_get_or_create_trader`) |
| INSERT is step 16 | ✅ | line 855 (`INSERT OR IGNORE`) |
| `notes` string finalized at step 12 | ✅ | line 824 (`notes = " ".join(notes_parts)`) — A7 must append to `notes` not `notes_parts` |
| `_log_event()` module-level helper | ✅ | line 61 (best-effort, commit=True, 13+ existing call sites) |
| `_log_rejection(conn=)` signature | ✅ | line 297 (conn= kwarg required for quarantine) |
| B14 SL guard as reference pattern | ✅ | lines 967-985 (similar guard-before-action pattern) |
| §4b CROSS_CHANNEL_DUPLICATE guard | ✅ | lines 656-680 (exact-match layer, complementary to A7's fuzzy match) |
| signal_router cross-channel dedup | ✅ | signal_router.py line 3589+ (signal-gateway repo, exact match) |
| Reconciler B10 flip-flop suppression | ✅ | reconciler.py:141-146 (signal-gateway repo, board path) |
| event_store.py LIFECYCLE_EVENTS | ✅ | `.openclaw/workspace/scripts/event_store.py` line 53 (UPDATE_DETECTED must be added) |
| event_store.py QUARANTINE_CODES | ✅ | line 80 (A7_UPDATE_DETECTED must be added) |
| `_process_closure` ticker_only precedent | ✅ | canonical line 1063 (REFUSES closure on ticker_only — supports Q-A7-1) |

### Current HEAD

| Repo | Commit | Notes |
|------|--------|-------|
| oinkfarm (canonical micro-gate) | 498d8b28 | `.openclaw/workspace/scripts/micro-gate-v3.py` — 1,407 LOC |
| signal-gateway | 38eb8e8 | signal_router.py (cross-channel dedup), reconciler.py (B10) |
| oink-sync | 6b21a20 | event_store.py (vendored copy) |

---

## 10. Open Question for Mike

**Q-A7-1: Should `ticker_only` matches be included in the suppression set?**

- **Include (recommended):** Catches more phantom duplicates, especially when LLM mis-attributes trader names. Risk: may suppress a legitimate signal from a different trader on the same ticker+direction.
- **Exclude (conservative):** Only `exact` trader matches are suppressed. Fewer false positives but more phantom duplicates escape.

**Code precedent supports INCLUDE:** `_process_closure` (canonical line 1063) REFUSES closure on `ticker_only` match. Precedent for destructive/irreversible actions on weak matches is to refuse. An INSERT is irreversible (phantom trade), so by analogy, suppress.

**Recommendation:** Start with `ticker_only` included. Monitor A7_UPDATE_DETECTED rejections for the first 48h. If any show different real traders being blocked, switch to `exact` only.

---

*Forge 🏗️ — "The last line of defense against phantom trades. One check, before the INSERT, changes everything."*

---

## Revisions — 2026-04-19 (Wave 2 audit)

Applied based on OinkV staleness audit (`OINKV-AUDIT-WAVE2-A7.md`). All changes are surgical — plan structure and rationale preserved.

| Audit Code | What Changed |
|---|---|
| STALE-A7-1 | All line numbers remapped to canonical `.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC). Stale signal-gateway refs (1,063 LOC) replaced. |
| STALE-A7-2 | Removed inline `from oink_sync.event_store import EventStore` — replaced with module-level `_log_event()` helper (canonical line 61, 13+ existing call sites). |
| STALE-A7-3 | Added `event_store.py` to §2 Files to Modify — `UPDATE_DETECTED` must be registered in `LIFECYCLE_EVENTS` and `A7_UPDATE_DETECTED` in `QUARANTINE_CODES`. |
| STALE-A7-4 | Fixed `_log_rejection()` call to include `conn=conn` kwarg (post-A1 signature requires it for quarantine table). |
| MINOR-A7-5 | §0 Scope and §1 Gap table now list all four protection layers including micro-gate's existing §4b CROSS_CHANNEL_DUPLICATE guard. |
| MINOR-A7-6 | "Allow INSERT" branch now appends to `notes` string directly (not `notes_parts` which was already joined at step 12, line 824). |
| MINOR-A7-7 | Q-A7-1 now cites code precedent: `_process_closure` (line 1063) refuses on `ticker_only`. Recommendation unchanged (include). |
| MINOR-A7-8 | §3 SQL Changes now documents all three `WHERE s.status IN` clauses (lines 384, 394, 410) plus the §4b guard (line 669). |
| NEW | Added `_A7_ENTRY_TOLERANCE_PCT = 5.0` named constant recommendation per audit. |
