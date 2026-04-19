# VIGIL Review — Task A1: signal_events Table Extension + Lifecycle Instrumentation

**Branch:** `anvil/A1-signal-events-extension` (oinkfarm PR #126 + oink-sync PR #4)
**Commits:** `09e0f94b`, `498d8b28` (oinkfarm); `ef948f3`, `620bd46` (oink-sync)
**Change Tier:** 🔴 CRITICAL (Financial Hotpath #6 — micro-gate INSERT logic)
**Review Round:** 2
**Review Date:** 2026-04-19 01:30 UTC

---

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | Schema extension matches Phase 4 §1 exactly (4 columns, correct types). All 6 lifecycle event types instrumented. PRICE_ALERT now in LIFECYCLE_EVENTS set (both copies). Zero-event root cause diagnosed and fixed. |
| Test Coverage | 9/10 | 0.25 | 2.25 | 19 tests, all pass. Covers schema migration, log() with new columns, commit=True/False visibility, quarantine regression, rollback docs, all 6 lifecycle event types, non-fatal failure mode. Misleading test name fixed. Minor gap: no PRICE_ALERT dedup test (tracked for follow-up). |
| Code Quality | 9/10 | 0.15 | 1.35 | Clean, well-documented. Vendored copy marker present. Root cause doc exemplary. Non-fatal wrapper pattern consistent. 3 unrelated yfinance files pre-existed from prior merge (not A1's diff — verified via merge base). |
| Rollback Safety | 10/10 | 0.15 | 1.50 | Fully additive — ALTER TABLE ADD COLUMN, new file, new instrumentation behind non-fatal try/except. AUTOINCREMENT rollback behavior documented and tested. git revert path clean. |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Zero risk to existing data. Event logging is append-only, non-fatal. Signal mutations unaffected by event store failures (verified by test_event_store_failure_non_fatal). try/except scope tight — wraps only event INSERT, never signal UPDATE. |
| **OVERALL** | | | **9.60** | |

---

## Round 2 Fix Verification

### MUST-FIX #1: PRICE_ALERT in LIFECYCLE_EVENTS ✅ RESOLVED
- `scripts/event_store.py` (oinkfarm `498d8b28`): `"PRICE_ALERT"` added under new `# Stage 7: Monitoring` comment
- `oink_sync/event_store.py` (oink-sync `620bd46`): identical addition, same placement
- Both copies verified consistent via grep
- 11/11 event_store tests still pass

### SHOULD-FIX #1: Misleading test name ✅ RESOLVED
- `test_be_closure_emits_trade_closed_be` → `test_tp_trailed_closure_emits_trade_closed_tp`
- Docstring updated: "TP1 hit trails SL to entry, then SL hit → TRADE_CLOSED_TP (positive blended PnL from TP1)"
- 8/8 lifecycle tests still pass

### SHOULD-FIX #2: Unrelated yfinance files — ACKNOWLEDGED
- ANVIL clarified these pre-existed from `fix/issue-114-gc-futures-yfinance` merge into master before A1 branched. Confirmed: not A1's diff. No action needed.

### SHOULD-FIX #3: Unreachable fallback comment — DEFERRED
- Acknowledged, will add comment on next touch. Acceptable.

---

## Delta (Round 1 → Round 2)

| Dimension | Round 1 | Round 2 | Δ |
|-----------|---------|---------|---|
| Spec Compliance | 9 (2.70) | 10 (3.00) | +1 (+0.30) |
| Test Coverage | 9 (2.25) | 9 (2.25) | 0 (0.00) |
| Code Quality | 9 (1.35) | 9 (1.35) | 0 (0.00) |
| Rollback Safety | 10 (1.50) | 10 (1.50) | 0 (0.00) |
| Data Integrity | 10 (1.50) | 10 (1.50) | 0 (0.00) |
| **OVERALL** | **9.30** | **9.60** | **+0.30** |

---

## Remaining Issues

### SHOULD-FIX (carried forward, non-blocking):
1. **PRICE_ALERT dedup test** — No test verifying that a second alert within `sl_cooldown_s` is suppressed. Tracked for follow-up.
2. **Unreachable closure fallback** — `TRADE_CLOSED_SL` fallback for non-SL closures is defensively sound but could use a clarifying comment.

### No MUST-FIX items remain.

---

## What's Done Well

- **Zero-event root cause diagnosis** remains exemplary — documented, proven with two-connection visibility tests, and applied consistently to both micro-gate and oink-sync
- **Non-fatal wrapper scope** correctly tight — wraps only event INSERT, never lifecycle UPDATE. Failure mode test drops the entire signal_events table and verifies trade still closes
- **Schema migration** is idempotent with duplicate-column error handling, tested three ways
- **Event payloads** are rich (ticker, direction, prices, trigger reason) — valuable for GUARDIAN monitoring and Phase B analytics
- **Round 2 turnaround** was clean — surgical fixes, no regressions, both copies updated consistently

---

## Verdict: ✅ PASS

**Overall score 9.60 meets the 🔴 CRITICAL threshold of ≥9.5.**

GUARDIAN has already PASSED at 9.80. Both reviewers now PASS — A1 is approved for merge.
