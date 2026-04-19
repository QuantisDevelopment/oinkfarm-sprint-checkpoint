# OINKV-AUDIT-WAVE2-A4 (Hermes fallback — OinkV LLM timeout)

**Auditor:** Hermes subagent (fallback; OinkV main lane hit FailoverError at 11:19 CEST on 2026-04-19)
**Date:** 2026-04-19
**Plan:** TASK-A4-plan.md
**Base commit verified:** oink-sync `6b21a2074413395b400b6f95494ae80d77ecef59` (HEAD = `6b21a20 feat(A2): remaining_pct model + partial-close PnL accuracy`) ✅ matches plan

---

## Summary
- **Findings:** 1 critical · 5 minor · 13 confirmed
- **Verdict:** **NEEDS REVISION** (lifecycle.py analysis is correct, but the plan omits a required `engine.py` scope expansion)
- **Scope note:** Plan correctly targets post-A1+A2 `oink-sync/oink_sync/lifecycle.py`, but A4 does **not** function end-to-end unless `oink-sync/oink_sync/engine.py` is updated in the same wave. The lifecycle layer can flip rows to `PARTIALLY_CLOSED`, but the engine layer still filters them out of price tracking and lifecycle input.

---

## Critical Staleness

### CRITICAL-A4-1 — `engine.py` excludes `PARTIALLY_CLOSED`, so A4 would orphan the new status after TP1
- **Plan:** `TASK-A4-plan.md` modifies only `lifecycle.py` and states the task is additive with no lifecycle showstoppers.
- **Actual:** `oink_sync/engine.py` still hard-codes `ACTIVE/PENDING` throughout the price pipeline:
  - `_load_tracked_tickers()` line **203**: `WHERE status IN ('ACTIVE','PENDING') AND ticker IS NOT NULL`
  - `_load_tracked_tickers()` line **219**: yfinance enrichment query also uses `status IN ('ACTIVE','PENDING')`
  - `_write_prices_to_db()` line **263**: selects only `ACTIVE/PENDING` rows before building `lifecycle_prices`
  - `self.lifecycle.run_cycle(conn, lifecycle_prices)` line **329** depends on that filtered `lifecycle_prices` map
  - `_repair_exchange_matched_flags()` line **355** also filters to `ACTIVE/PENDING`
  - `_calculate_pnl()` line **458** returns `None` for any status other than `ACTIVE`, so `PARTIALLY_CLOSED` rows would stop updating `pnl_percent` even if selected
- **Impact:** After A4 flips a signal from `ACTIVE` to `PARTIALLY_CLOSED`, it can fall out of tracked-ticker refresh, stop receiving `current_price`/`pnl_percent` writes, and stop reaching `lifecycle.run_cycle()` via `lifecycle_prices`. For non-crypto tickers this also risks dropping the symbol from the yfinance tracked set. Net effect: the new status can be silently orphaned after the first TP hit.
- **Suggested fix:** Add `oink-sync/oink_sync/engine.py` to A4 scope. Broaden `_load_tracked_tickers()` (both queries) and `_write_prices_to_db()` to include `PARTIALLY_CLOSED`, treat `PARTIALLY_CLOSED` like `ACTIVE` in `_calculate_pnl()`, and review `_repair_exchange_matched_flags()` for status-model consistency. Until this is added, A4 is not READY.

---

## Minor Staleness

### MINOR-A4-1 — `_process_tp_hits()` UPDATE statement line range off by ~2 lines
- **Plan:** §4b line 166: *"Currently (A2 shipped code, lines ~604–612)"*
- **Actual:** The `UPDATE signals SET {hit_col}=?, stop_loss=?, remaining_pct=?, updated_at=? WHERE id=?` block is at **lines 606–616** of `oink_sync/lifecycle.py` (16-line window, not 9).
- **Impact:** Cosmetic — the code block quoted in the plan matches current source verbatim; only the line range is slightly off.
- **Suggested fix:** Re-word to *"lines ~606–616"* or drop line numbers and reference by marker comment.

### MINOR-A4-2 — Closure UPDATE cited as "line ~481", actually at line 470
- **Plan:** §1 line 93 and §4c line 194: *"closure path in `_check_sl_tp()` (lifecycle.py line ~481)"*
- **Actual:** The `UPDATE signals SET status=?, exit_price=?, ...` statement is at **line 470**; the `WHERE id=? AND status='ACTIVE' AND fill_status='FILLED'` predicate (the key target of the A4 change) is at **line 473**.
- **Impact:** ANVIL will still find the right code instantly by grepping `status='ACTIVE' AND fill_status='FILLED'` (unique match). Plan quote is byte-identical to current source.
- **Suggested fix:** Update to *"line ~473"* (or ~470).

### MINOR-A4-3 — Status distribution table is a stale snapshot
- **Plan:** §1 lines 39–46:
  ```
  ACTIVE 85 · CANCELLED 56 · CLOSED_BREAKEVEN 68 · CLOSED_LOSS 171
  CLOSED_MANUAL 7 · CLOSED_WIN 92 · PENDING 11
  ```
- **Actual** (`signals.db` this morning):
  ```
  ACTIVE 79 · CANCELLED 57 · CLOSED_BREAKEVEN 69 · CLOSED_LOSS 176
  CLOSED_MANUAL 7 · CLOSED_WIN 93 · PENDING 11
  ```
- **Impact:** Cosmetic — the *shape* is correct (same 7 status values, no `PARTIALLY_CLOSED` yet, same ordering). Absolute counts drifted by 0–6 rows as oink-sync continues to close signals throughout the day.
- **Suggested fix:** None strictly required — plans drift against live data constantly. Consider stamping "snapshot time".

### MINOR-A4-4 — Pre-A4 backfill expected rows is now 2, not 0
- **Plan:** §1 line 147 and §4e line 246: *"Expected pre-A4: 0 rows (A2 shipped 2026-04-19, no partial signals yet)"* and *"Expected rows affected: 0"*.
- **Actual:** `SELECT COUNT(*) FROM signals WHERE status='ACTIVE' AND remaining_pct > 0.0 AND remaining_pct < 100.0;` returns **2**:
  ```
  1602 | ACTIVE | 50.0 | tp1=2026-04-18T18:33 | tp2=2026-04-19T02:34 | tp3=2026-04-19T03:53
  1561 | ACTIVE | 50.0 | tp1=2026-04-18T11:43 | tp2=2026-04-19T07:23 | tp3=NULL
  ```
- **Impact:** The backfill SQL will flip **2** real production rows to `PARTIALLY_CLOSED` on deployment — not 0. This is the *intended* behavior of A4, but the plan's "If > 0: confirm with Mike before proceeding" clause now triggers. Both rows are genuine partial-TP signals that logically ought to become PARTIALLY_CLOSED, so this is a green-light data point, not a red flag.
- **Suggested fix:** Update expected row count in §4e to *"~2 rows as of audit time (IDs 1561, 1602 — both legitimate partial-TP closures from A2's first hours in production)"* so ANVIL doesn't pause on the Mike-confirm gate unnecessarily.

### MINOR-A4-5 — DQ-A4-1 overstates `LIFECYCLE_EVENTS` enforcement
- **Plan:** §10 DQ-A4-1 line 362: *"The `EventStore.LIFECYCLE_EVENTS` set ... lists the valid event types. ... if not [present], ANVIL must add it before emitting it."*
- **Actual:** `LIFECYCLE_EVENTS` is defined at `oink_sync/event_store.py:53` but it is **informational only** — `EventStore.log()` (lines 138–166) does NOT validate the `event_type` argument against this set. The current set:
  ```
  SIGNAL_CREATED, ORDER_FILLED, LIMIT_EXPIRED, SL_MODIFIED, SL_TO_BE,
  TP_MODIFIED, TP_HIT, PARTIAL_CLOSE, TRAILING_STOP_SET, ENTRY_CORRECTED,
  TRADE_CLOSED_SL, TRADE_CLOSED_TP, TRADE_CLOSED_MANUAL, TRADE_CLOSED_BE,
  GHOST_CLOSURE, TRADE_CANCELLED, TRADE_RESTORED, MANUAL_SQL_FIX, PRICE_ALERT
  ```
  `STATUS_CHANGED` is **not** in the set, but omitting it will **not** cause emission to fail — `log()` accepts arbitrary strings.
- **Impact:** ANVIL will not be blocked by a runtime assertion. Best-practice hygiene still argues for adding `STATUS_CHANGED` to the set for documentation parity.
- **Suggested fix:** Soften DQ-A4-1 to *"should add for documentation consistency; not a runtime blocker"*.

---

## Confirmed Accurate

1. ✅ **Base commit** — plan cites `6b21a2074`; actual HEAD = `6b21a2074413395b400b6f95494ae80d77ecef59`.
2. ✅ **`_process_tp_hits()` signature** — plan §1 line 53–57 quotes the signature; exact byte match at `lifecycle.py:540–544` (`self, conn, sig_id, ticker, direction, entry, current, sl, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit, now, events, *, remaining_pct=None`).
3. ✅ **`_check_sl_tp()` main SELECT** — plan §1 line 68–74 quotes 18-column SELECT with `WHERE status='ACTIVE' AND exchange_matched=1 AND exchange_ticker IS NOT NULL`; verified verbatim at `lifecycle.py:384–390` (the `FROM signals WHERE ...` tail is at **line 389**, matching the plan's line-388 citation within ±1).
4. ✅ **`_check_limit_fills()` PENDING guard** — plan §1 line 79–85 quotes `WHERE status='PENDING' AND exchange_matched=1`; verified at `lifecycle.py:670`. Plan correctly concludes no change needed.
5. ✅ **Closure path quoted SQL** — plan §4c lines 197–203 quotes the full `UPDATE signals SET status=?, exit_price=?, final_roi=?, ... WHERE id=? AND status='ACTIVE' AND fill_status='FILLED'` statement; verified byte-exact at `lifecycle.py:469–475`.
6. ✅ **`calculate_blended_pnl()` location** — plan §1 line 89 cites lines ~117–200; actual function spans **117–197**.
7. ✅ **`remaining_pct` column shape (A2 artifact)** — `ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0` confirmed at `lifecycle.py:265`; DB schema shows column `remaining_pct REAL DEFAULT 100.0` appended to signals table. Plan's §4a transition rules use the same column correctly.
8. ✅ **`status VARCHAR(20) CHECK (status = UPPER(status))` constraint** — plan line 32 asserts the CHECK accepts any uppercase 20-char string. Verified: schema declares `status VARCHAR(20) NOT NULL CHECK (status = UPPER(status))` AND redundant triggers `trg_status_upper_insert` / `trg_status_upper_update`. `'PARTIALLY_CLOSED'` (15 chars, all upper) satisfies both — no DDL needed. ✅
9. ✅ **`STATUS_CHANGED` currently unused** — plan assumption implicit in §0 and §4d. Confirmed: `rg STATUS_CHANGED` across oink-sync returns 0 matches; `signal_events` table has 0 STATUS_CHANGED rows (top event_types: PRICE_ALERT 223, TRADE_CLOSED_SL 5, SL_MODIFIED 3, TP_HIT 3, SIGNAL_CREATED 2, LIMIT_EXPIRED 1, MANUAL_SQL_FIX 1, TRADE_CLOSED_TP 1).
10. ✅ **`PARTIALLY_CLOSED` not yet present** — plan §1 line 48 asserts "No PARTIALLY_CLOSED rows exist". Confirmed: 0 rows, 0 string occurrences anywhere in oink-sync source.
11. ✅ **A1 `_log_event` integration** — plan §4d proposes emitting STATUS_CHANGED via `self._log_event()`. Method exists on `Lifecycle` class at `lifecycle.py:302–322`, accepts `field`/`old_value`/`new_value` kwargs (the Phase 4 A1 columns). Delegates to `EventStore.log(commit=True)` — plan's usage pattern is correct.
12. ✅ **A1 `TP_HIT` / `SL_MODIFIED` / `TRADE_CLOSED_*` emission sites** — already wired in `_process_tp_hits()` (lines 632, 636) and `_check_sl_tp()` closure (line 494). Adding a STATUS_CHANGED emission fits the same pattern ANVIL already has working. ✅
13. ✅ **signal-gateway A7 cross-reference** — plan §9 line 352 states `signal-gateway/scripts/micro-gate-v3.py::_match_active()` queries `status IN ('ACTIVE','PENDING')` and will need broadening in A7. Confirmed at `micro-gate-v3.py:276` (`def _match_active`) with matching WHERE on lines 292, 302, 318.

---

## Open Questions

### OQ-A4-1 — Expand A4 scope to `engine.py` before Mike approval?
Yes. This is not an optional cleanup. Without the engine-layer changes in CRITICAL-A4-1, `PARTIALLY_CLOSED` rows stop behaving like live positions from the engine's perspective.
**Recommendation for Mike:** Require FORGE to revise A4 so `engine.py` ships in the same change set as `lifecycle.py`.

### OQ-A4-2 — Backfill gate: 2 real rows exist, unblock or manual-confirm?
§4e says "Expected rows affected: 0 · If > 0: confirm with Mike before proceeding". Current DB shows **2 legitimate rows** (IDs 1561, 1602 — both `remaining_pct=50.0` with ≥1 real `tp*_hit_at` timestamp from 2026-04-18/19). These are exactly the population A4 is designed to cover.
**Recommendation for Mike:** Pre-approve the backfill of these 2 specific rows; no live intervention needed. Consider annotating the backfill SQL with `AND id IN (1561, 1602)` as an explicit safety guard, or proceed with the unbounded predicate since it's semantically equivalent.

### OQ-A4-3 — Class name nit (no action required for A4)
The plan references methods on the lifecycle class (`_process_tp_hits`, `_check_sl_tp`, `_check_limit_fills`) without ever naming the class. The actual class is `Lifecycle` (not `LifecycleManager` as the wave-1 audit OINKV-AUDIT.md §"Architectural Differences" asserted). This doesn't affect A4 since the plan never uses the class name, but wave-1 audit is itself mildly stale on this point. Logged here for cross-audit hygiene only.

### OQ-A4-4 — Add `STATUS_CHANGED` to `LIFECYCLE_EVENTS` set?
Non-blocking (see MINOR-A4-5). ANVIL should add it for docs consistency. No code forces this; all existing lifecycle emits (PRICE_ALERT, TRADE_CLOSED_*, SL_MODIFIED, TP_HIT, ORDER_FILLED, LIMIT_EXPIRED) *are* in the set, so adding STATUS_CHANGED keeps the pattern uniform.

---

## Audit Coverage Notes

- **Files read (targeted, with offsets):** `oink_sync/lifecycle.py` lines 100–290 (blended PnL + Lifecycle class init), 290–360 (event helpers + run_cycle), 380–740 (the A4 modification surfaces), 800–830, 978–1008; `oink_sync/event_store.py` full scan for `LIFECYCLE_EVENTS` + `log()`; `oink_sync/engine.py` lines 1–520 covering `_load_tracked_tickers()`, `_write_prices_to_db()`, `_repair_exchange_matched_flags()`, `_calculate_pnl()`, and the `lifecycle.run_cycle()` handoff.
- **DB queries run:** status distribution, pre-A4 partial candidates, event_type histogram on `signal_events`, full schema dump of `signals` table.
- **Cross-repo verification:** signal-gateway `_match_active()` confirmed for DQ-A4/A7 cross-ref.
- **Not audited (out of scope for A4):** Phase 0 proposal format, test fixture patterns in `tests/test_remaining_pct.py` (only confirmed the file exists for plan's "same fixture pattern" claim).
