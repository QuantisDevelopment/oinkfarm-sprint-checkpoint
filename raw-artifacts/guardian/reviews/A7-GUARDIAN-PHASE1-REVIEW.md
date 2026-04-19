# 🛡️ GUARDIAN Phase 1 Review — Task A7

| Field | Value |
|-------|-------|
| **Branch** | `anvil/A7-update-detected-guard` |
| **Commit** | `2036f097` |
| **Change Tier** | 🔴 CRITICAL (Financial Hotpath #6 — micro-gate INSERT logic) |
| **Review Round** | Round 1 |
| **Review Date** | 2026-04-19 |

---

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Schema Correctness | 25% | 10 | No DDL. 4 status IN clauses correctly broadened to include PARTIALLY_CLOSED (lines 384, 394, 410, 669). A7 guard placed between step 14 (trader FK) and step 15 (timestamp), before step 16 (INSERT). All resolved variables (trader_id, ticker, direction, entry_price, server_id) available at guard location. `event_store.py` registries updated (UPDATE_DETECTED in LIFECYCLE_EVENTS, A7_UPDATE_DETECTED in QUARANTINE_CODES). |
| 2 | Formula Accuracy | 25% | 10 | 5% threshold correctly implemented: `price_diff_pct = abs(entry_price - existing_entry) / existing_entry * 100`. Suppress when `price_diff_pct ≤ 5.0` (via `> 5.0` check for allow path). Boundary test confirms: 5.0% → suppress, 5.01% → allow. Zero-entry edge case: `existing_entry > 0 and entry_price > 0` guard prevents division by zero. |
| 3 | Data Migration Safety | 20% | 10 | No migration. No schema changes. No data modifications to existing rows. A7 is purely defensive (prevents INSERTs). Only append-only writes: signal_events, quarantine, gate-rejections.jsonl, and notes annotation on allowed INSERTs. |
| 4 | Query Performance | 10% | 10 | No new database queries. A7 reuses existing `_match_active()` result. The only addition is a Python-side percentage calculation. Status IN clause broadenings add one value to existing IN lists — unmeasurable impact at current scale. |
| 5 | Regression Risk | 20% | 10 | 20/20 A7 tests pass. 57/62 total pass (5 pre-existing failures confirmed on baseline commit). Existing test suites (test_micro_gate_filled_at: 8/8, test_micro_gate_source_url: 3/3) pass. GUARDIAN's Phase 0 concern (SHOULD-FIX #4) addressed with dedicated test `test_update_partially_closed_ticker_only_flags`. §4b complementary test verifies exact-entry signals caught by existing CROSS_CHANNEL_DUPLICATE before A7. |
| | **OVERALL** | 100% | **10.00** | |

**Weighted calculation:** (10×0.25) + (10×0.25) + (10×0.20) + (10×0.10) + (10×0.20) = 2.50 + 2.50 + 2.00 + 1.00 + 2.00 = **10.00**

---

## Pre-Deploy Baseline Snapshot

| Metric | Current Value | Source |
|--------|---------------|--------|
| SC-4 (Signal count) | 492 | `SELECT COUNT(*) FROM signals` @ 2026-04-19T11:06Z |
| UPDATE_DETECTED events | 0 | `signal_events WHERE event_type='UPDATE_DETECTED'` |
| A7_UPDATE_DETECTED quarantine | 0 (table absent) | quarantine table not yet present |
| gate-rejections.jsonl | 5,394 entries (0 A7) | File line count |
| KPI-R3 (Duplicate discord IDs) | 14 groups | Full table |
| KPI-R6 (Ingestion) | 24 last 24h, 39.3 avg/day | posted_at query |
| Status: ACTIVE | 77 | |
| Status: PARTIALLY_CLOSED | 2 | |
| Status: PENDING | 11 | |

---

## Formula Verification

**A7 does not modify PnL formulas.** No formula accuracy impact on existing signals.

**Reference case: FET #1159**
- Status: CLOSED_WIN, remaining_pct=100.0
- A7 impact: NONE — FET #1159 is closed, never enters `_match_active` as an active position, and A7 only affects the INSERT path.

**5% threshold verification:**
- Boundary test (entry=100.0, existing=100.0):
  - 105.0 → 5.0% → suppress ✅ (SHOULD-4)
  - 105.01 → 5.01% → allow ✅ (SHOULD-5)
- Real-world test (entry=65000.0, existing=65000.0):
  - 65650.0 → 1.0% → suppress ✅ (MUST-1)
  - 65200.0 → 0.31% → suppress ✅ (MUST-2)
  - 70000.0 → 7.69% → allow INSERT ✅ (MUST-3)

---

## Code Review Notes

### Guard Placement
```
Step 14: trader FK resolution (line 832)
  ↓
  trader_id, trader_name_raw, ticker, direction, entry_price, server_id — all resolved
  ↓
A7 GUARD (line 840) ← NEW
  ↓
Step 15: Timestamp (line 881)
  ↓
Step 16: INSERT (line 884)
```

Placement is correct — all required variables are resolved, and the guard fires before any INSERT attempt.

### Defensive Checks
1. `trader_id is not None` — skip A7 when no trader attribution ✅
2. `ticker and direction` — skip when missing core fields ✅
3. `match_conf in ("exact", "ticker_only")` — skip ambiguous/no_match ✅
4. `existing_entry > 0 and entry_price > 0` — prevent division by zero ✅
5. `> _A7_ENTRY_TOLERANCE_PCT` for allow path — correct operator (suppress is ≤5%) ✅

### Event Logging
- `_log_rejection(entry, "A7_UPDATE_DETECTED", ..., conn=conn)` — uses `conn=conn` kwarg (A1 signature). Writes to both gate-rejections.jsonl and quarantine table. ✅
- `_log_event(conn, "UPDATE_DETECTED", existing["id"], {...})` — module-level helper (line 61), best-effort, `commit=True`. Event payload includes suppressed_entry, existing_entry, price_diff_pct, extraction_method, discord_message_id. ✅

### Notes Annotation
On allow path: `notes = (notes or "") + f" [A7: ...]"` — correctly appends to the already-joined `notes` string (after line 824 `notes = " ".join(notes_parts)`). The `(notes or "")` handles None case. ✅

### Status IN Broadening (4 sites)
| Site | Line | Before | After | Verified |
|------|------|--------|-------|----------|
| `_match_active` exact-trader | 384 | ACTIVE, PENDING | + PARTIALLY_CLOSED | ✅ |
| `_match_active` canonical-name | 394 | ACTIVE, PENDING | + PARTIALLY_CLOSED | ✅ |
| `_match_active` ticker-only | 410 | ACTIVE, PENDING | + PARTIALLY_CLOSED | ✅ |
| §4b CROSS_CHANNEL_DUPLICATE | 669 | ACTIVE, PENDING | + PARTIALLY_CLOSED | ✅ |

### Return Value
Returns `{"action": "a7_update_detected", ...}` — consistent with micro-gate's existing return conventions. The `_dispatch` caller passes through without special handling. ✅

---

## Test Coverage Analysis

| Category | Count | Pass | Coverage |
|----------|-------|------|----------|
| MUST (core logic) | 7 | 7/7 | Suppress close entry, allow far entry, allow no existing, allow opposite dir, rejection logged, pending match |
| SHOULD (edges) | 8 | 8/8 | PARTIALLY_CLOSED, event logged, no-trader bypass, 5% boundary (both sides), ticker_only, ambiguous, notes annotation |
| ZERO (edge) | 3 | 3/3 | Zero existing entry, zero new entry, both zero |
| GUARDIAN-1 | 1 | 1/1 | UPDATE handler + PARTIALLY_CLOSED + ticker_only → LOW_CONFIDENCE flag |
| COMPLEMENTARY-1 | 1 | 1/1 | §4b exact match layer precedence |
| **TOTAL** | **20** | **20/20** | |

Regression suites: test_micro_gate_filled_at (8/8), test_micro_gate_source_url (3/3) — all pass. ✅

---

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|----------|-----------|-------------|----------|
| — | — | — | No issues found | — |

---

## What's Done Well

1. **Clean defensive architecture** — A7 only prevents INSERTs, never modifies existing data. The safest possible change category for a financial hotpath.
2. **Layered protection** — A7 complements §4b (exact match) without overlapping. COMPLEMENTARY-1 test explicitly verifies the handoff.
3. **Complete edge case coverage** — Zero-entry, no-trader, ambiguous match, opposite direction, boundary conditions all tested.
4. **GUARDIAN Phase 0 concern addressed** — SHOULD-FIX #4 (UPDATE handler + PARTIALLY_CLOSED + ticker_only) has a dedicated test (GUARDIAN-1).
5. **Minimal code footprint** — 44 net lines in micro-gate, 3 lines in event_store. High value-to-LOC ratio.
6. **Rich audit trail** — Every suppression gets 3 records (signal_events, quarantine, gate-rejections.jsonl). Every allow gets a notes annotation explaining the decision. Full transparency.

---

## Verdict

**PASS** ✅

- Overall score: **10.00** vs threshold 9.5
- No schema changes, no migrations, no data modifications to existing rows
- Purely defensive guard with comprehensive test coverage (20/20)
- 5% threshold correctly implemented with boundary verification
- All 4 status IN broadenings consistent with A4
- GUARDIAN Phase 0 concern resolved
- 5 test failures confirmed pre-existing (present on baseline commit)

ANVIL is cleared for deployment. GUARDIAN will initiate canary protocol on deployment notification — monitoring UPDATE_DETECTED events and gate-rejections for the first 48h.

---

*🛡️ GUARDIAN — Phase 1 Review*
*Reviewed: 2026-04-19T11:06Z*
