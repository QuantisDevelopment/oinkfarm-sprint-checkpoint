# A4 Phase 0 Technical Proposal — PARTIALLY_CLOSED Status

**Revision 1** — Addresses GUARDIAN REQUEST_CHANGES (4 blocking concerns)
**Previous verdict:** VIGIL ✅ APPROVE, GUARDIAN 🔄 REQUEST CHANGES
**Delta:** §2B expanded to 10 sites across 2 files; §2C rewritten (same-cycle closure); §2E rewritten (guarded backfill); §2G added (query performance); §6 added (staged rollout for deferred consumers)

**Task:** A4 — PARTIALLY_CLOSED Status for Partial TP Signals
**Tier:** 🟡 STANDARD (Phase 1 auto-escalates to 🔴 CRITICAL per Financial Hotpath #2 and #5)
**Repos:** oink-sync (`QuantisDevelopment/oink-sync`)
**Branch:** `anvil/A4-partially-closed-status`
**Base commit:** `6b21a20` (master, post-A2)
**Dependencies:** A1 ✅ shipped, A2 ✅ shipped, A3 ✅ shipped
**FORGE plan:** `/home/oinkv/forge-workspace/plans/TASK-A4-plan.md`
**OinkV audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A4.md` (0 critical, 5 minor)
**Phase 4 Ref:** §2 (Signal Lifecycle Accuracy), §ADAPT/status-model

---

## 1. Problem

After A2, `remaining_pct` is correctly decremented on every TP hit, but the signal's `status` remains `'ACTIVE'`. A signal with TP1 hit (50% closed, remaining_pct=50.0) is indistinguishable from a brand-new signal. This creates:

1. **Misleading lifecycle state** — dashboards and queries cannot differentiate fresh vs. partially-closed signals
2. **A7 gap** — the upcoming UPDATE→NEW phantom-trade guard needs `PARTIALLY_CLOSED` in its status check set
3. **Monitoring gaps** — if we ever split monitoring logic by status, partial signals could be orphaned

## 2. Approach

Add `'PARTIALLY_CLOSED'` as a new status value. No schema migration required — the existing `CHECK (status = UPPER(status))` constraint accepts any uppercase string ≤20 chars, and `'PARTIALLY_CLOSED'` is 15 chars, fully uppercase.

### 2A. Status Transition Rules

| Condition | Status |
|-----------|--------|
| `remaining_pct = 100.0`, no TP hit | `ACTIVE` |
| `0 < remaining_pct < 100.0`, ≥1 TP hit | `PARTIALLY_CLOSED` |
| `remaining_pct = 0.0` (all TPs hit in one cycle) | `CLOSED_WIN` **same cycle** (no open limbo state) |
| SL hit (any remaining_pct) | Final close status (`CLOSED_WIN`/`CLOSED_LOSS`/`CLOSED_BREAKEVEN`) |

### 2B. Modification Sites — Full Blast Radius (10 sites across 2 files)

GUARDIAN correctly identified that my original proposal scoped changes too narrowly to `lifecycle.py`. The full blast radius includes `engine.py`, which feeds lifecycle with price data and PnL calculations. A PARTIALLY_CLOSED signal that falls out of `engine.py`'s tracked set would silently stop receiving price/PnL updates — a HIGH-impact data integrity gap.

#### engine.py (5 sites — NEW in Revision 1)

| # | Function | Line | Current predicate | Change |
|---|----------|------|-------------------|--------|
| E1 | `_load_tracked_tickers()` | 203 | `status IN ('ACTIVE','PENDING')` | → `IN ('ACTIVE','PENDING','PARTIALLY_CLOSED')` |
| E2 | `_load_tracked_tickers()` (yfinance) | 219 | `status IN ('ACTIVE','PENDING')` | → `IN ('ACTIVE','PENDING','PARTIALLY_CLOSED')` |
| E3 | `_write_prices_to_db()` | 263 | `status IN ('ACTIVE','PENDING')` | → `IN ('ACTIVE','PENDING','PARTIALLY_CLOSED')` |
| E4 | `_repair_exchange_matched_flags()` | 355 | `status IN ('ACTIVE','PENDING')` | → `IN ('ACTIVE','PENDING','PARTIALLY_CLOSED')` |
| E5 | `_calculate_pnl()` | 458 | `if normalized_status != "ACTIVE": return None` | → `if normalized_status not in ("ACTIVE", "PARTIALLY_CLOSED"): return None` |

**E5 is the most critical engine.py fix.** Without it, `_write_prices_to_db()` would fetch PARTIALLY_CLOSED rows (after E3 broadening) but `_calculate_pnl()` would return `None` for them, silently zeroing out PnL tracking.

#### lifecycle.py (5 sites — unchanged from v0)

| # | Function | Line | Current predicate | Change |
|---|----------|------|-------------------|--------|
| L1 | `_check_sl_tp()` — main SELECT | 389 | `WHERE status='ACTIVE' AND exchange_matched=1` | → `status IN ('ACTIVE','PARTIALLY_CLOSED')` |
| L2 | `_check_sl_tp()` — closure UPDATE | 473 | `AND status='ACTIVE' AND fill_status='FILLED'` | → `status IN ('ACTIVE','PARTIALLY_CLOSED')` |
| L3 | `_process_tp_hits()` — UPDATE | ~610 | No status reference | Add `status='PARTIALLY_CLOSED'` when `0 < run_remaining < 100`; same-cycle close when `run_remaining = 0.0` |
| L4 | `_check_sl_proximity()` — SELECT | 811 | `WHERE status='ACTIVE' AND fill_status='FILLED'` | → `status IN ('ACTIVE','PARTIALLY_CLOSED')` |
| L5 | `_write_price_history()` — SELECT | 988 | `WHERE status='ACTIVE' AND exchange_matched=1` | → `status IN ('ACTIVE','PARTIALLY_CLOSED')` |

#### Sites correctly excluded

| File | Function | Line | Why excluded |
|------|----------|------|-------------|
| lifecycle.py | `_check_limit_fills()` | 689 | Sets `status='ACTIVE'` from `'PENDING'` — PENDING→ACTIVE transition, unrelated |
| engine.py | `_calculate_pnl()` PENDING branch | 456 | Returns `0.0` for PENDING — correct, PARTIALLY_CLOSED should use ACTIVE math |

### 2C. Status UPDATE Atomicity + Same-Cycle Closure (DQ-A4-2)

*Revised per GUARDIAN concern #2 — eliminates all-TPs-hit limbo.*

Merge the status flip into the same `UPDATE` statement as `remaining_pct` in `_process_tp_hits()`:

**When `0 < run_remaining < 100` (partial TP hit):**
```python
conn.execute(
    f"UPDATE signals SET {hit_col}=?, stop_loss=?, "
    f"remaining_pct=?, status='PARTIALLY_CLOSED', updated_at=? "
    f"WHERE id=? AND status IN ('ACTIVE','PARTIALLY_CLOSED')",
    (now, new_sl, run_remaining, now, sig_id),
)
```

**When `run_remaining = 0.0` (all TPs hit in one cycle — DQ-A4-2):**
```python
# Same-cycle final close. Do NOT leave signal in open limbo.
conn.execute(
    f"UPDATE signals SET {hit_col}=?, stop_loss=?, "
    f"remaining_pct=0.0, status='CLOSED_WIN', "
    f"final_roi=?, closed_at=?, updated_at=? "
    f"WHERE id=? AND status IN ('ACTIVE','PARTIALLY_CLOSED')",
    (now, new_sl, blended_pnl, now, now, sig_id),
)
```

This ensures:
- First TP hit: `ACTIVE → PARTIALLY_CLOSED` ✅
- Second TP hit: `PARTIALLY_CLOSED → PARTIALLY_CLOSED` (idempotent) ✅
- All TPs in one cycle: direct close to `CLOSED_WIN` in the same cycle ✅ (no limbo)
- Already closed signals: guard prevents flip-back ✅

**Same-cycle closure requires calling `calculate_blended_pnl()` inside `_process_tp_hits()` when `run_remaining = 0.0`.** This is a new callsite for blended PnL that didn't exist before. The function already exists and is tested (A2). The TP close percentages are available from the current loop's `tp_close_pcts` dict. `remaining_pct=0.0` means all allocation is consumed — `final_roi` is fully determined.

### 2D. STATUS_CHANGED Event

Emit a `STATUS_CHANGED` event on `ACTIVE → PARTIALLY_CLOSED` transition only:

```python
# Pre-read current_status from the row data already fetched by _check_sl_tp()
if current_status == "ACTIVE" and 0 < run_remaining < 100:
    self._log_event(conn, "STATUS_CHANGED", sig_id, {
        "old_status": "ACTIVE",
        "new_status": "PARTIALLY_CLOSED",
        "trigger": "tp_hit",
        "tp_level": tp_idx,
        "remaining_pct": run_remaining,
        "ticker": ticker,
        "direction": direction,
    }, field="status", old_value="ACTIVE", new_value="PARTIALLY_CLOSED")
```

**Dedup rule:** Only emit when `current_status == "ACTIVE"` (pre-read from row data passed into `_process_tp_hits()`). Subsequent TP hits on already-PARTIALLY_CLOSED signals emit TP_HIT events only — no duplicate STATUS_CHANGED. The single-threaded SQLite execution model guarantees no race between SELECT and UPDATE within a cycle.

**LIFECYCLE_EVENTS set:** Add `STATUS_CHANGED` to the set at `event_store.py:53` for documentation parity. Not a runtime blocker (the set is informational only), but every other emitted event type is in the set.

### 2E. Pre-A4 Backfill (Guarded Deployment Step)

*Revised per GUARDIAN concern #3 — explicit transaction, abort threshold, anomaly handling.*

**Mike has pre-approved this backfill** for ≤4 qualifying rows.

```sql
-- STEP 1: Pre-check (paste full output into PR description)
SELECT id, status, remaining_pct, tp1_hit_at, tp2_hit_at, tp3_hit_at
  FROM signals
 WHERE status='ACTIVE'
   AND remaining_pct > 0.0
   AND remaining_pct < 100.0;

-- ABORT CONDITIONS (any one triggers abort + escalate to Mike):
-- 1. rowcount > 4
-- 2. Any row has tp3_hit_at IS NOT NULL while remaining_pct > 0
--    (anomalous: all 3 TPs hit but still open — e.g. signal #1602)
--    → Flag for Mike review before proceeding

-- STEP 2: Execute backfill in explicit transaction
BEGIN;
UPDATE signals
   SET status='PARTIALLY_CLOSED'
 WHERE status='ACTIVE'
   AND remaining_pct > 0.0
   AND remaining_pct < 100.0;

-- STEP 3: Verify post-count matches pre-count
SELECT COUNT(*) FROM signals WHERE status='PARTIALLY_CLOSED';
-- Expected: equals pre-check rowcount (2, IDs #1561, #1602)
COMMIT;
```

**Anomaly note on signal #1602:** This signal has `tp3_hit_at` set while `remaining_pct=50.0`, which is inconsistent (all 3 TPs claimed hit but 50% allocation remains). This is a pre-existing data quality issue from before A2's event-sourced close percentages. The backfill correctly marks it as `PARTIALLY_CLOSED` (it IS partially closed — remaining_pct confirms this). The tp3_hit_at anomaly is a data quality follow-up, not an A4 blocker. Document in PR description.

### 2F. Rollback Plan

1. `git revert <A4-commit>` in oink-sync
2. Rollback SQL:
   ```sql
   UPDATE signals SET status='ACTIVE' WHERE status='PARTIALLY_CLOSED';
   ```
3. `systemctl --user restart oink-sync`
4. Verify: `SELECT COUNT(*) FROM signals WHERE status='PARTIALLY_CLOSED'` → 0

Safe because reverting to ACTIVE restores full monitoring coverage (pre-A4 behavior). STATUS_CHANGED events remain in `signal_events` (append-only audit log — acceptable and consistent with rollback design).

### 2G. Query Performance Acknowledgement

*Added per GUARDIAN concern #4.*

Broadening `WHERE status='ACTIVE'` to `WHERE status IN ('ACTIVE','PARTIALLY_CLOSED')` affects the partial covering index `ix_signal_exchange_active` (`WHERE status='ACTIVE' AND exchange_matched=1`). The SQLite query planner will fall back to the broader `ix_signals_status` index for the `IN (...)` predicate.

At the current scale (~490 rows in `signals`), this plan change has negligible performance impact. A full table scan at 490 rows completes in <1ms on this hardware. No index rebuild is required in Phase 1.

If the table grows past ~10K rows, a replacement partial index `ix_signal_exchange_open` (`WHERE status IN ('ACTIVE','PARTIALLY_CLOSED') AND exchange_matched=1`) would restore covering-index performance. This is a future optimization, not a Phase 1 concern.

---

## 3. Staged Rollout — Deferred Consumers

*Added per GUARDIAN concern #1.*

A4 covers **oink-sync** (engine.py + lifecycle.py) — the full data pipeline from price fetch → PnL calculation → TP/SL monitoring → status transition. This is the critical path.

The following consumers are **deferred** to named follow-up tasks. They are read-only reporting or dedup queries — not data-pipeline critical:

### Deferred: oinkdb-api (follow-up task: A4-F1)

| Endpoint / Function | Current predicate | Impact of not changing | Priority |
|---------------------|-------------------|----------------------|----------|
| `/signals/open` | `status = 'ACTIVE'` | PARTIALLY_CLOSED signals not shown in "open" view | MEDIUM |
| `/signals/active` | `status = 'ACTIVE'` | Same | MEDIUM |
| `/market/sentiment` | `status = 'ACTIVE'` | Sentiment calc excludes partial signals | LOW |
| `/alerts/divergence` | `status = 'ACTIVE'` | Divergence alerts miss partial signals | MEDIUM |
| Trader summary counters | `status = 'ACTIVE'` | Active count underreports | LOW |

**Rationale for deferral:** oinkdb-api is a read-only API consumed by dashboards and monitoring. No data loss occurs — signals still close correctly, PnL is still calculated. The only impact is UI underreporting of open positions. These are ~12 SQL sites across ~1500 lines of oinkdb-api.py, warranting their own review to avoid a sprawling A4 PR.

**Follow-up:** `/home/oinkv/anvil-workspace/followups/A4-F1-OINKDB-API-STATUS-BROADENING.md` (to be created at merge time)

### Deferred: signal-gateway (follow-up task: A4-F2)

| File | Sites | Impact of not changing | Priority |
|------|-------|----------------------|----------|
| `micro-gate-v3.py` | 3 sites (lines 384, 394, 410) — dedup/match queries | New signals matching a PARTIALLY_CLOSED signal's ticker+server won't be detected as duplicates | LOW (A7 addresses this explicitly) |
| `signal_router.py` | 5 sites (lines 2245, 2255, 2322, 3072, 3616) — active/pending match queries | Same dedup gap | LOW (A7 addresses this) |

**Rationale for deferral:** These are dedup/match queries that check "is there already an active signal for this ticker?" When A7 (UPDATE→NEW detection) is implemented, it will explicitly add `PARTIALLY_CLOSED` to `_match_active()` — this is already in A7's FORGE plan. Changing these in A4 would be redundant pre-A7 work. The only risk in the interim is a rare race where a new signal for the same ticker arrives while an existing signal is PARTIALLY_CLOSED — this already happens today (the dedup only checks ACTIVE/PENDING, not remaining_pct), so A4 does not make it worse.

**Follow-up:** `/home/oinkv/anvil-workspace/followups/A4-F2-SIGNAL-GATEWAY-STATUS-BROADENING.md` (to be created at merge time; mostly superseded by A7)

---

## 4. Test Strategy

New file: `tests/test_partially_closed.py` (same fixture pattern as `test_remaining_pct.py`)

| Test | Priority | What it proves |
|------|----------|----------------|
| `test_tp1_hit_sets_partially_closed` | MUST | TP hit → status='PARTIALLY_CLOSED', remaining_pct correct |
| `test_tp2_hit_on_partially_closed_signal` | MUST | Second TP on PARTIALLY_CLOSED → stays PARTIALLY_CLOSED, remaining_pct decrements |
| `test_sl_hit_closes_partially_closed_signal` | MUST | SL closure works for PARTIALLY_CLOSED signals (closure guard broadened) |
| `test_gap_past_all_tps_same_cycle_close` | MUST | All TPs in one cycle → remaining_pct=0.0, closes as CLOSED_WIN in same cycle (DQ-A4-2) |
| `test_status_changed_event_emitted` | MUST | ACTIVE→PARTIALLY_CLOSED produces STATUS_CHANGED event |
| `test_no_duplicate_status_event_on_second_tp` | MUST | Second TP hit does NOT emit redundant STATUS_CHANGED |
| `test_partially_closed_monitored_in_next_cycle` | MUST | PARTIALLY_CLOSED signals included in `_check_sl_tp()` row scan |
| `test_active_only_signal_unchanged` | MUST | ACTIVE signals without TP hits remain ACTIVE (regression guard) |
| `test_limit_fills_ignores_partially_closed` | MUST | `_check_limit_fills()` does NOT touch PARTIALLY_CLOSED signals |
| `test_sl_proximity_includes_partially_closed` | MUST | `_check_sl_proximity()` scans PARTIALLY_CLOSED signals (site L4) |
| `test_price_history_includes_partially_closed` | MUST | `_write_price_history()` writes for PARTIALLY_CLOSED signals (site L5) |
| `test_engine_tracks_partially_closed_tickers` | MUST | `_load_tracked_tickers()` includes PARTIALLY_CLOSED signal tickers (site E1) |
| `test_engine_pnl_calc_partially_closed` | MUST | `_calculate_pnl()` returns valid PnL for PARTIALLY_CLOSED signals (site E5) |
| `test_engine_writes_prices_for_partially_closed` | MUST | `_write_prices_to_db()` updates PARTIALLY_CLOSED rows (site E3) |
| `test_backfill_query_correctness` | SHOULD | Backfill SQL flips qualifying rows |
| `test_blended_pnl_unaffected_by_status` | SHOULD | `calculate_blended_pnl()` returns same value regardless of status field |

**Existing test suites must pass unmodified:**
- `test_remaining_pct.py` (29 tests)
- `test_lifecycle_events.py` (8 tests)
- `test_yfinance_afterhours.py` (8 tests)

---

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| PARTIALLY_CLOSED signals orphaned from monitoring | HIGH | 10 sites broadened across lifecycle.py + engine.py. Integration tests for L1, L4, L5, E1, E3, E5. |
| SL closure silently skips PARTIALLY_CLOSED | HIGH | Site L2 broadened. `test_sl_hit_closes_partially_closed_signal`. |
| engine.py PnL returns None for PARTIALLY_CLOSED | HIGH | Site E5 fixed. `test_engine_pnl_calc_partially_closed`. |
| All-TPs-hit leaves signal in open limbo | MEDIUM | Same-cycle closure in `_process_tp_hits()` (§2C). `test_gap_past_all_tps_same_cycle_close`. |
| STATUS_CHANGED event emitted multiple times | LOW | Pre-read dedup: only emit when current_status == 'ACTIVE'. |
| Backfill hits unexpected rows | LOW | Pre-deploy SELECT + abort threshold + explicit transaction (§2E). |
| Partial index regression | LOW | Acknowledged in §2G. Negligible at 490-row scale. |
| oinkdb-api underreports open signals | LOW | Deferred to A4-F1. Read-only reporting, no data loss. |

---

## 6. Acceptance Criteria

1. After any TP hit where `0 < remaining_pct < 100`, signal status = `'PARTIALLY_CLOSED'`
2. When all TPs hit in one cycle (`remaining_pct = 0.0`), signal closes as `CLOSED_WIN` in the **same cycle** — no open limbo state
3. `PARTIALLY_CLOSED` signals are included in `_check_sl_tp()`, `_check_sl_proximity()`, `_write_price_history()`, `_load_tracked_tickers()`, `_write_prices_to_db()`, `_repair_exchange_matched_flags()`, and `_calculate_pnl()` monitoring
4. SL closure works on `PARTIALLY_CLOSED` signals with correct `final_roi` (blended PnL)
5. Every `ACTIVE → PARTIALLY_CLOSED` transition emits a `STATUS_CHANGED` event
6. No duplicate `STATUS_CHANGED` events for subsequent TP hits on already-PARTIALLY_CLOSED signals
7. `_check_limit_fills()` does NOT include PARTIALLY_CLOSED signals
8. All existing tests pass without modification
9. `SELECT COUNT(*) FROM signals WHERE status NOT IN ('ACTIVE','PENDING','PARTIALLY_CLOSED','CLOSED_WIN','CLOSED_LOSS','CLOSED_BREAKEVEN','CLOSED_MANUAL','CANCELLED')` returns 0

---

## Revision 1 Delta Summary

| GUARDIAN Concern | Resolution |
|------------------|------------|
| **#1: Scope too narrow** | Added 5 engine.py sites (E1–E5). Critical: E5 (`_calculate_pnl()`) would return None for PARTIALLY_CLOSED. oinkdb-api deferred to A4-F1 (read-only). signal-gateway deferred to A4-F2 (mostly superseded by A7). |
| **#2: DQ-A4-2 limbo** | §2C rewritten. Same-cycle closure when `remaining_pct = 0.0`: call `calculate_blended_pnl()` inside `_process_tp_hits()` and close as CLOSED_WIN immediately. No open limbo state. |
| **#3: Backfill procedure** | §2E rewritten with explicit BEGIN/COMMIT, pre-SELECT with ID paste, abort threshold (>4), anomaly check for tp3_hit_at+remaining_pct inconsistency (signal #1602). |
| **#4: Query plan** | §2G added. Acknowledges ix_signal_exchange_active partial index regression. Negligible at 490-row scale. No index rebuild in Phase 1. |

| VIGIL Carry-Forward | Status |
|---------------------|--------|
| Phase 1 auto-escalates to 🔴 CRITICAL | Acknowledged in header |
| STATUS_CHANGED dedup via pre-read | §2D uses pre-read approach consistently |
| LIFECYCLE_EVENTS entry | §2D confirms hygiene addition |
| `test_gap_past_all_tps` naming | Renamed to `test_gap_past_all_tps_same_cycle_close` — scope: verifies same-cycle closure (one call, not two cycles) |

---

*ANVIL ⚒️ — Phase 0 Proposal for A4 (Revision 1)*
*Original: 2026-04-19*
*Revised: 2026-04-19 — Addresses GUARDIAN REQUEST_CHANGES*
