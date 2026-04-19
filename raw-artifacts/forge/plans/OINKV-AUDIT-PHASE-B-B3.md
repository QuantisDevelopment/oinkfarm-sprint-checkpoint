# OinkV Engineering Audit — FORGE Plan B3 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback, OinkV LLM timeout)
**Date:** 2026-04-19
**Scope:** TASK-B3-plan.md — Parallel-Write Verification Period (dual-write SQLite + PostgreSQL)
**Verdict:** 🔴 **CRITICAL** — Write-site inventory is structurally stale: two claims target functions/files that don't exist, the reconciler column list is missing 9+ post-A-wave columns, and the inventory omits an entire third repo (signal-gateway) that writes to both `signals` and `signal_events`.

**Provenance:** OinkV `main` agent LLM-timed-out on Phase B audit dispatch at 2026-04-19T19:23:36Z. Per sprint-orchestrator skill "Hermes-Subagent Fallback" section, dispatched via `delegate_task`. Subagent hit 50-iteration cap; content recovered from subagent summary per "Hermes-Level Review via delegate_task — Iteration Budget Pitfall" fallback.

---

## ⛔ SHOWSTOPPER: B3's Write-Site Inventory Misses an Entire Repo

Phase A Wave 1 audit documented that lifecycle writes live in **oink-sync**. B3 correctly redirected lifecycle references away from `kraken-sync.py` (no regression there — good). However, A6 added a new third write path in a **third repo** that B3's §1 inventory does not list:

| Repo | File | Operation | Ignored by B3 |
|------|------|-----------|----------------|
| signal-gateway | `scripts/signal_gateway/signal_router.py:4023` | `INSERT INTO signal_events ... 'GHOST_CLOSURE'` | 🔴 yes |
| signal-gateway | `scripts/signal_gateway/signal_router.py:4035` | `UPDATE signals SET notes=... WHERE id=?` (A6 ghost_closure note append) | 🔴 yes |

**Impact:** If B3 wires dual-write only through `oink_db.py` consumed by oinkfarm/micro-gate and oink-sync, **signal_router.py's DB writes would never reach PostgreSQL** and would never be reconciled. The reconciler would be blind to GHOST_CLOSURE events and note mutations emitted by A6.

ANVIL must either (a) route signal_router through the same `oink_db.connect()` B1 introduced, or (b) add a third dual-write site there.

---

## 1. Write-Site Inventory — Line-by-Line Verification

Verified against `oinkfarm @ 50b23834`, `oink-sync @ e9be741`, `signal-gateway @ c6cb99e`.

| # | Plan Claim (file, func, line, op) | Actual | Verdict |
|---|-----------------------------------|--------|---------|
| 1 | micro-gate `_process_signal()` line 979 INSERT signals | `_process_signal()` at line **637**; INSERT at line **984** (`INSERT OR IGNORE INTO signals`) | 🟡 MINOR — plan line points at the `try:` block above the INSERT; actual INSERT 5 lines later. Function name correct. |
| 2 | lifecycle.py `_check_sl_tp()` line 515 | `_check_sl_tp()` at line **383**; the UPDATE-and-close is at line **471**; line 515 is the `conn.commit()` at end of method | 🔴 **CRITICAL** — line drift **132 lines** (well beyond ±20). Method name correct but the original reference to line 515 is meaningless. Plan needs line 471 for the primary close UPDATE. |
| 3 | micro-gate `_process_update()` line 1050+ | `_process_update()` at line **1029**; UPDATE signals at line **1151** | ✅ MATCH — function starts within ±20 of claim. Actual write site is 1151 (plan says "1050+" which is permissive). |
| 4 | lifecycle.py `_close_signal()` line 797 | **`_close_signal()` DOES NOT EXIST** in oink-sync/oink_sync/lifecycle.py. `grep -n 'close_signal' lifecycle.py` returns zero hits. Line 797 is `conn.commit()` inside `_check_limit_fills()`. | 🔴 **CRITICAL — FUNCTION DOES NOT EXIST.** The close path is an inline UPDATE inside `_check_sl_tp()` at line 471-478. Plan invented a function. |
| 5 | micro-gate `_process_closure()` line 1175+ | `_process_closure()` at line **1175** exact; UPDATE blocks at lines 1229, 1289, 1297, 1398 | ✅ EXACT MATCH |
| 6 | `event_store.py` `log_event()` line 157 | Method is named **`log()`** (not `log_event()`); exists at line 141 in oinkfarm `scripts/event_store.py` and line 139 in oink-sync `oink_sync/event_store.py`. INSERT at lines 160/158 | 🟡 MINOR — method name wrong (`log_event()` → `log()`); line ±3. **Also:** A1 VENDORED event_store.py into oink-sync, so there are now TWO copies. Plan does not disambiguate; reconciler needs to know both paths write through. |
| 7 | engine.py `_scan_once()` line 311 UPDATE signals | **`_scan_once()` DOES NOT EXIST.** Actual method is `_write_prices_to_db()` at line **254**. UPDATE at line **312** (`UPDATE signals SET current_price=?, pnl_percent=?`). | 🔴 **CRITICAL — FUNCTION NAME WRONG.** Line 311 is within 1 of the correct UPDATE, but the containing method is misnamed. |
| 8 | engine.py `_scan_once()` line 316 INSERT price_history | **Wrong file AND wrong function AND wrong operation.** Line 316 of engine.py is **another UPDATE** (`UPDATE signals SET opened_price=? WHERE id=? AND opened_price IS NULL`). The actual `INSERT INTO price_history` is in **`oink_sync/lifecycle.py` line 1084**, inside `_write_price_history()`. | 🔴 **CRITICAL** — the plan claims `INSERT INTO price_history` lives in engine.py; it lives in lifecycle.py. This is a structural misidentification. |
| 9 | micro-gate `_get_or_create_trader()` line 392 UPDATE traders | `_get_or_create_trader()` at line **386**; `UPDATE traders` at line **392** | ✅ EXACT MATCH |
| 10 | micro-gate `_quarantine()` line 358 INSERT quarantine | `_quarantine()` at line **358**; note: the INSERT is actually issued inside `event_store.quarantine_entry()` (line 177 of event_store.py) — `_quarantine()` delegates via `es.quarantine_entry()`. | 🟡 MINOR — function/line correct but the plan implies a direct `INSERT INTO quarantine`; it's indirect through EventStore. Same translation logic applies, but ANVIL must ensure the vendored event_store is also dual-write-wrapped. |

### Verdict tally for §1 inventory

- **2 🔴 CRITICAL** — function doesn't exist (`_close_signal`, `_scan_once`)
- **2 🔴 CRITICAL** — structural wrong-file/wrong-op (price_history INSERT in lifecycle.py, not engine.py)
- **1 🔴 CRITICAL** — 132-line drift on `_check_sl_tp`
- **3 🟡 MINOR** — line or method-name drift
- **3 ✅ OK**

---

## 2. Missing Write Sites (between plan draft and current code)

B3 assumes the 11 sites in §1 are the complete write surface. They are not. Additional writes ANVIL will need to route through the dual-write layer:

| Wave | New Write Site | File:Line | Operation | In B3 §1? |
|------|----------------|-----------|-----------|-----------|
| A1 | `_log_event()` from micro-gate `_process_update()` | micro-gate-v3.py:1158, 1163 | INSERT signal_events (SL_MODIFIED/SL_TO_BE, ORDER_FILLED) | ❌ (only "event_store" abstract row) |
| A1 | `_log_event()` from micro-gate `_process_closure()` | micro-gate-v3.py:1236, 1315 | INSERT signal_events (TRADE_CANCELLED, TRADE_CLOSED_*) | ❌ |
| A1 | `self._log_event()` from oink-sync `_check_sl_tp` | lifecycle.py:496 | INSERT signal_events (TRADE_CLOSED_*) | ❌ |
| A1 | `self._log_event()` from oink-sync `_check_limit_fills` | lifecycle.py:780 | INSERT signal_events (ORDER_FILLED) | ❌ |
| A1 | oink-sync `_process_tp_hits()` TP_HIT events | lifecycle.py:542+ | INSERT signal_events (TP_HIT) | ❌ |
| A4 | oink-sync PARTIALLY_CLOSED status transition | lifecycle.py (TP partial close path) | UPDATE signals SET status='PARTIALLY_CLOSED' | ❌ |
| A6 | signal_router ghost closure | signal_router.py:4023, 4035 | INSERT signal_events + UPDATE signals (notes) | ❌ — **entire repo missing** |
| — | engine.py `_repair_exchange_matched_flags()` | engine.py:375 | UPDATE signals SET exchange_matched=1 | ❌ |
| — | oink-sync `_expire_stale_limits()` | lifecycle.py:859 | UPDATE signals SET status='CANCELLED', fill_status='EXPIRED_UNFILLED' | ❌ |
| — | oink-sync `_check_limit_fills()` ACTIVE transition | lifecycle.py:768 | UPDATE signals SET status='ACTIVE', fill_status='FILLED' | ❌ |
| — | oink-sync `_process_tp_hits()` SL trail UPDATE | lifecycle.py:630, 654, 661 | UPDATE signals SET tp{1,2,3}_hit_at=?, stop_loss=? | ❌ |

### A7/A9/A10/A11 specific check

- **A7 (UPDATE→NEW detection)** — adds conditional *suppression* of INSERT at micro-gate-v3.py:944 (`# Likely UPDATE misclassified as NEW — suppress INSERT`). Does NOT introduce a new write site. B3 does not need to enumerate it. ✅
- **A9 (denomination multiplier)** — normalizes entry/SL/TP at **pre-INSERT** time in `_process_signal()`. No new write site. The existing INSERT at line 984 is where the normalized values land. ✅ but note the column list in §3 reconciler should cover `exchange_ticker` (A9 can change which exchange_ticker a signal gets).
- **A10 (historical filled_at backfill)** — correctly exempted by task description as one-time; not a dual-write concern. ✅
- **A11 (leverage_source)** — adds a new column populated at INSERT (micro-gate) and in the historical migration; no new write site. But the reconciler must compare this column (see §3 below). ❌ missing from reconciler.

---

## 3. Reconciliation Design — Column Coverage Gaps

B3 §3 defines the recent-signals spot-check SELECT:

```sql
SELECT id, discord_message_id, ticker, direction, status, entry_price,
       stop_loss, remaining_pct, pnl_percent, final_roi, closed_at
FROM signals ...
```

### Columns verified in current live schema (sqlite3 /home/m/data/oinkfarm.db)

```
id, discord_message_id, channel_id, channel_name, server_id, trader_id,
message_type, ticker, direction, order_type, entry_price, stop_loss,
take_profit_1, take_profit_2, take_profit_3, leverage, asset_class,
confidence, exchange_ticker, exchange, exchange_matched, current_price,
pnl_percent, last_price_update, status, fill_status, fill_price, filled_at,
limit_expiry_hours, exit_price, final_roi, is_win, closed_at, auto_closed,
close_source, parent_signal_id, last_trader_update, raw_text, notes,
trader_comment, posted_at, updated_at, tp1_hit_at, tp2_hit_at, tp3_hit_at,
source_url, close_source_url, hold_hours, opened_price, remaining_pct,
leverage_source, sl_type
```

### Columns added post-plan-draft that the spot-check SELECT OMITS

| Column | Added By | Risk If Un-Reconciled |
|--------|----------|------------------------|
| `filled_at` | A3 (write) + A10 (104 historical backfill) | 🔴 HIGH — grace-period calc in oink-sync depends on this; A3 is the whole reason it's now populated for MARKETs |
| `sl_type` | A8 | 🟡 MED — SL classification (FIXED/MANUAL/CONDITIONAL) silently drifts |
| `leverage_source` | A11 | 🟡 MED — leverage provenance drift invisible |
| `opened_price` | pre-A but populated by engine.py | 🟡 MED — engine.py backfill path (line 317) not spot-checked |
| `exchange_matched`, `exchange_ticker`, `exchange` | pre-A | 🟡 MED — A9 normalization side-effects invisible |
| `tp1_hit_at`, `tp2_hit_at`, `tp3_hit_at` | pre-A | 🔴 HIGH — partial-close PnL (A2) depends on these timestamps; dual-write divergence would corrupt blended PnL |
| `hold_hours` | pre-A but populated on close | 🟡 MED |
| `close_source`, `close_source_url` | pre-A | 🔴 HIGH — closure source attribution divergence would mask A6 ghost_closure correctness |
| `fill_status`, `fill_price` | pre-A | 🔴 HIGH — lifecycle state machine correctness hinges on this |
| `leverage`, `auto_closed`, `is_win` | pre-A | 🟡 MED |
| `notes` | pre-A, touched by A6 ghost-closure note append | 🔴 HIGH — A6 note mutations invisible if not compared |
| `current_price`, `last_price_update` | high-churn | 🟢 LOW — expected to diverge briefly; consider excluding with a tolerance window |

### signal_events reconciler SELECT

Plan §3 spot-checks:
```sql
SELECT id, signal_id, event_type, source, created_at FROM signal_events
```

Current schema (verified): `id, signal_id, event_type, payload, source, created_at, field, old_value, new_value, source_msg_id`.

**Missing from reconciler:**
- `payload` (the entire JSON blob — divergence here means an event's business meaning differs)
- `field`, `old_value`, `new_value`, `source_msg_id` (**all four added by A1**)

🔴 The reconciler's current signal_events SELECT would pass even if A1's semantic columns diverge. Column list must be expanded.

### Missing tables from row-count comparison

Plan §3 counts: `signals, signal_events, traders, servers, price_history, quarantine`. All present in live DB. ✅

But: `audit_log` table exists in live DB (`.tables` shows it) and is not in the comparison. ANVIL should confirm whether it's in the B2 migration scope.

---

## 4. Cross-Repo Consistency Check

Cross-reference against OINKV-AUDIT.md Wave-1 finding (all Phase A plans referenced dead kraken-sync.py):

- B3 §1 lifecycle references: `lifecycle.py` (oink-sync) ✅ correct
- B3 §1 engine references: `engine.py` (oink-sync) ✅ correct repo, but wrong function (`_scan_once` → `_write_prices_to_db`) and wrong location for price_history INSERT
- B3 §1 kraken-sync references: **zero** ✅ no regression to the Wave-1 mistake
- B3 §4e rollback: correctly does not reference kraken-sync service ✅

**However**: B3 misses the **signal-gateway** repo entirely (see SHOWSTOPPER). This is a *new* cross-repo gap introduced because B3 was drafted before A6 merged.

---

## 5. Stale Reference / Drift Tally

| Category | Count |
|----------|-------|
| 🔴 CRITICAL — function name doesn't exist | 2 (`_close_signal`, `_scan_once`) |
| 🔴 CRITICAL — wrong file for operation | 1 (price_history INSERT in lifecycle.py, not engine.py) |
| 🔴 CRITICAL — line drift >20 | 1 (`_check_sl_tp` 515→383, ~132 lines) |
| 🔴 CRITICAL — missing repo coverage | 1 (signal-gateway / signal_router.py) |
| 🔴 CRITICAL — missing reconciler column coverage | 9+ columns, 4 signal_events columns |
| 🟡 MINOR — method name typo (`log_event` → `log`) | 1 |
| 🟡 MINOR — line drift ≤20 | 3 |
| 🟡 MINOR — EventStore indirection not called out | 1 (`_quarantine` goes via EventStore, not direct INSERT) |
| ✅ Correct | 3 write-site rows, 0 kraken-sync regressions, 0 dead-code claims |

---

## 6. Top 3 Blockers for ANVIL

1. **🔴 BLOCKER: Signal-gateway repo missing from write-site inventory.** A6 (merged before B3 execution) added two new write sites in `signal-gateway/scripts/signal_gateway/signal_router.py`. If dual-write is wired only through oinkfarm+oink-sync, ghost-closure writes silently skip PostgreSQL and the reconciler never sees them. B3 §1 must add a third repo to the inventory, and §2 must list the signal-gateway file(s) in "Files to Modify" (or document a routing strategy).

2. **🔴 BLOCKER: Two phantom function names in write-site inventory.** `_close_signal()` at lifecycle.py:797 and `_scan_once()` at engine.py:311 **do not exist**. ANVIL cannot instrument a function that isn't there. Replace with: `_check_sl_tp()` (line 383, close UPDATE at 471) for closures; `_write_prices_to_db()` (line 254, UPDATE at 312) for price updates; and separately `_write_price_history()` in lifecycle.py (line 1064, INSERT at 1084) for price_history.

3. **🔴 BLOCKER: Reconciler spot-check misses the columns that prove A1-A11 correctness.** Reconciler SELECTs omit `filled_at, sl_type, leverage_source, tp1_hit_at, tp2_hit_at, tp3_hit_at, fill_status, close_source, notes, opened_price` and all four A1 event columns (`field, old_value, new_value, source_msg_id`) + `payload`. A divergence in any of these would not be caught — defeating the "7 consecutive clean days" acceptance criterion.

---

## 7. What B3 Gets Right (credit)

- ✅ No regression to kraken-sync references (Wave-1 lesson absorbed).
- ✅ Correctly identifies oink-sync + micro-gate as the primary write surfaces.
- ✅ Fire-and-forget dual-write semantics with SQLite authoritative is the correct architecture.
- ✅ Daily reconciliation + JSON report format is reasonable.
- ✅ Rollback plan is clean (env-var disable, no data loss because SQLite authoritative).
- ✅ Risk table recognizes SQL-translation-miss and silent secondary failure.
- ✅ 7-14 day verification duration aligns with Phase 4 V3 spec §2.
- ✅ `_process_closure()` line number at 1175 is exact.
- ✅ `_quarantine()` line number at 358 is exact.
- ✅ `_get_or_create_trader()` line 392 is exact.

---

## 8. Required Plan Revisions (for ANVIL / Mike)

1. **Rewrite §1 Write Sites Inventory** with verified function names and lines (see §1 table above). Add the six+ missing write paths from §2.
2. **Add signal-gateway to §2 Files to Modify.** Either route `signal_router.py` through `oink_db.connect()` or add a third dual-write wrapper.
3. **Expand §3 Reconciliation Queries** — signals spot-check SELECT to include all 13 post-A-wave columns; signal_events SELECT to include `payload, field, old_value, new_value, source_msg_id`.
4. **Disambiguate event_store.py location** — oinkfarm copy + oink-sync vendored copy both write; both code paths need dual-write wiring.
5. **Clarify `_quarantine()` indirection** — the INSERT is via `EventStore.quarantine_entry()`, not a direct `INSERT INTO quarantine`. Dual-write must wrap the EventStore layer, not just the caller.
6. **Update §0 `Canonical files verified at:`** — currently says "micro-gate `46154543`"; verify that's still HEAD after A1-A11 (current HEAD of oinkfarm workspace is `50b23834`).

---

## Ship-readiness

**NOT SHIP-READY — REWRITE §1 + §3 REQUIRED.** B3's overall architecture (dual-write with SQLite authoritative + daily reconciler + 7-14 day verification) is correct and the rollback semantics are clean. But the **write-site inventory is materially inaccurate** (2 phantom functions + 1 structural misidentification + 132-line drift) and the **reconciler is blind to the columns that make Phase A's data correctness auditable**. ANVIL cannot execute this plan without first fixing the inventory, or the verification period will pass with undetected divergences that Mike won't discover until cutover.

**Recommended action:** FORGE revises §1 (verified write sites, post-A1-A11 inventory including signal-gateway) and §3 (reconciler column coverage). Estimated revision effort: 60-90 min. All revisions are additive/corrective; the core architecture stands.

---

*Audit complete. Hermes fallback, 2026-04-19.*
