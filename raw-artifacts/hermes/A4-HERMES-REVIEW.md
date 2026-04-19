# Hermes-Level Review — A4 PARTIALLY_CLOSED (PR #7)
**Commit:** ab5d941 | **Tier:** 🔴 CRITICAL | **Date:** 2026-04-19
**VIGIL:** 9.60 PASS | **GUARDIAN:** (pending) | **Hermes:** ✅ LGTM

Repo inspected: `/home/oinkv/oink-sync` @ `anvil/A4-partially-closed-status` (ab5d941), base `master`. Diff: +724 / -16 across 4 files.

---

## Verification Table

| # | Item | Evidence | Status |
|---|------|----------|--------|
| 1a | **L1** `_check_sl_tp()` SELECT broadened to include PARTIALLY_CLOSED and select `status` col | `oink_sync/lifecycle.py:388-389` — `SELECT … status FROM signals WHERE status IN ('ACTIVE','PARTIALLY_CLOSED') AND exchange_matched=1 …` | ✅ |
| 1b | **L2** `_check_sl_tp()` closure UPDATE guard broadened | `lifecycle.py:475` — `WHERE id=? AND status IN ('ACTIVE','PARTIALLY_CLOSED') AND fill_status='FILLED'` | ✅ |
| 1c | **L3** `_process_tp_hits()` signature adds `current_status`, sets PARTIALLY_CLOSED on partial, same-cycle close on run_remaining==0.0 | `lifecycle.py:545` (sig), `:609-658` (UPDATE branches) | ✅ |
| 1d | **L4** `_check_sl_proximity()` query broadened | `lifecycle.py:890` — `WHERE status IN ('ACTIVE','PARTIALLY_CLOSED') AND fill_status='FILLED'` | ✅ |
| 1e | **L5** `_write_price_history()` query broadened | `lifecycle.py:1067` — `WHERE status IN ('ACTIVE','PARTIALLY_CLOSED') AND exchange_matched=1 …` | ✅ |
| 1f | **E1** `_load_tracked_tickers()` tracked tickers include PARTIALLY_CLOSED | `engine.py:203` | ✅ |
| 1g | **E1b** Same function's yfinance sub-query | `engine.py:219` | ✅ |
| 1h | **E2** `_write_prices_to_db()` scan | `engine.py:263` | ✅ |
| 1i | **E3** `_repair_exchange_matched_flags()` scan | `engine.py:355` | ✅ |
| 1j | **E5** `_calculate_pnl()` status filter includes `'PARTIALLY_CLOSED'` | `engine.py:458` — `if normalized_status not in ("ACTIVE", "PARTIALLY_CLOSED"): return None` | ✅ |
| 2 | **Same-cycle closure** — when last TP takes remaining_pct→0, `calculate_blended_pnl()` called with full `tp_close_pcts` (events + current), single atomic UPDATE sets `status='CLOSED_WIN'`, `final_roi`, `exit_price`, `closed_at`, `close_source='tp_all_hit'`, `auto_closed=1`, `hold_hours` — **no PARTIALLY_CLOSED limbo** | `lifecycle.py:611-640`: `_tp_close_pcts = self._collect_tp_close_pcts(conn, sig_id) or {}`, `_tp_close_pcts[tp_idx] = close_pct`, then single UPDATE. `test_gap_past_all_tps_no_partially_closed_limbo` asserts `status != 'PARTIALLY_CLOSED'` and `== 'CLOSED_WIN'`. | ✅ |
| 3 | **STATUS_CHANGED in LIFECYCLE_EVENTS**, emitted only on ACTIVE→PARTIALLY_CLOSED (dedup via `current_status == "ACTIVE"` guard + in-function update of local `current_status` to prevent duplicates on later TPs in same cycle) | `event_store.py:62`; `lifecycle.py:665-678` (emission + `current_status = "PARTIALLY_CLOSED"` on line 678); tests `test_no_duplicate_status_event_on_second_tp`, `test_no_status_changed_on_same_cycle_close` pass. | ✅ |
| 4 | **Test `test_gap_past_all_tps_same_cycle_close` asserts `final_roi == expected_blended_pnl` numerically** | `tests/test_partially_closed.py:265-272` — builds expected via `calculate_blended_pnl(...)` and asserts `row["final_roi"] == round(expected_pnl, 2)`. Expected=17.5 (0.5·10 + 0.25·20 + 0.25·30). Event-sourced path with `{1:50,2:25,3:25}` and legacy path produce identical result (remaining_frac=0 drops the exit term in both). Test passes. | ✅ |
| 5 | **Backfill SQL** — pre-SELECT for IDs 1561/1602, abort-if-rowcount>4, BEGIN/COMMIT, anomaly handler for #1602 (`tp3_hit_at` set with `remaining_pct=50.0`) | `A4-PROPOSAL.md:137-165` contains the exact form. Test `test_backfill_query_correctness` (tests/test_partially_closed.py:522-538) verifies the SQL body. PR body textual presence cannot be cross-checked offline (no `gh` auth), but proposal is canonical and marker files reference it. | ✅ (proposal) / 🟡 (PR body unverifiable offline) |
| 6 | **Downstream consumers** — see section below | Multiple grep hits across oinkfarm, oinkdb-api, signal-gateway | 🟡 DEFERRED (per plan §10, A4-F1 + A4-F2) |
| 7 | **FET #1159 reference case** blended-PnL path unchanged | `tests/test_remaining_pct.py::test_fet_1159_legacy_unchanged`, `::test_fet_1159_25pct_close`, `::test_fet_1159_50pct_close` all PASS | ✅ |
| 8 | **Tests**: 21 new + existing | See "Test Results" section — **58 passed, 0 failed** for oink-sync targeted suites. Full repo has 4 unrelated failures in `test_yfinance_afterhours.py` due to missing `pandas`/`yfinance` modules in this env — not A4-related. | ✅ |
| 9 | **Dry-run parity** — no dry_run branch in engine.py / lifecycle.py production path | `grep -rn "dry_run\|DRY_RUN" oink_sync/` → 0 hits. No asymmetry to flag. | ✅ |

---

## Findings

### ✅ Correctness — strong
- The same-cycle close UPDATE (`lifecycle.py:629-640`) includes every required field in one atomic statement: `tp{hit_col}`, `stop_loss`, `remaining_pct=0.0`, `status='CLOSED_WIN'`, `exit_price`, `final_roi`, `is_win=1`, `closed_at`, `close_source='tp_all_hit'`, `auto_closed=1`, `current_price`, `pnl_percent`, `last_price_update`, `updated_at`, `hold_hours`. Matches MUST-FIX #2 atomicity requirement.
- The `_tp_close_pcts` assembly on `lifecycle.py:615-616` correctly builds the dict from prior TP_HIT events **plus** the current TP (whose event hasn't been emitted yet), preventing silent weight undercounting.
- The STATUS_CHANGED dedup is achieved two ways: (a) guard `current_status == "ACTIVE"` on line 667, (b) local mutation `current_status = "PARTIALLY_CLOSED"` on line 678 so a subsequent TP in the same loop iteration doesn't re-emit. Correct.
- The closure UPDATE on both the SL path (`:475`) and TP-all-hit path (`:636`) uses `status IN ('ACTIVE','PARTIALLY_CLOSED')` as row guard — prevents double-close under concurrency (harmless given single-threaded SQLite, still good defense-in-depth).
- E5 is correctly implemented: `if normalized_status not in ("ACTIVE", "PARTIALLY_CLOSED"): return None` — PnL no longer silently returns None for partial-closed signals. Regression test covers ACTIVE/PENDING/CLOSED_WIN too.

### 🟡 Minor observations (non-blocking)
1. **No rowcount check on same-cycle TP-all-hit UPDATE** (`lifecycle.py:629-640`). The SL closure path re-reads rowcount and logs a warning if 0 (`:479-484`). The same-cycle close path does not. Given single-threaded SQLite + the row guard, a silent no-op is extremely unlikely, but mirroring the SL pattern would be more defensive. Not a blocker.
2. **Fresh `datetime.now(timezone.utc)` on `:624`** instead of reusing the `now_dt` from the caller. Negligible skew (micro-seconds); consistent with `now` passed as ISO string into UPDATE. Minor.
3. **Re-fetching `posted_at`** via a nested `conn.execute("SELECT posted_at FROM signals WHERE id=?", …)` inside the same transaction (`:626`). The caller already has `row[15] = posted_at`. Minor perf duplication, not a correctness issue.
4. **Backfill SQL body in PR description cannot be verified here** because `gh` is not authenticated in this environment. Proposal and Phase1-APPROVED marker confirm the canonical form; canonical SQL is also exercised by `test_backfill_query_correctness`. 🟡 trust-but-verify via GitHub UI before deploy.

### 🟡 Downstream coverage — intentional partial scope
The PR modifies oink-sync only. Many **read/filter sites** in sibling repos still say `status='ACTIVE'` (or `status IN ('ACTIVE','PENDING')`) and will therefore **exclude** PARTIALLY_CLOSED signals. This is called out in the FORGE plan as deferred to A4-F1 (oinkdb-api) and A4-F2 (signal-gateway dedup). The plan (TASK-A4-plan.md:352) explicitly notes `_match_active()` in signal-gateway needs an A7/later update. Hermes confirms the scope boundary is sound: partials stay monitored/priced by oink-sync itself, which is the critical path.

---

## Downstream Consumer Grep Results

```
# /home/oinkv/oinkfarm (signal reporting/dashboards — read-only views):
scripts/portfolio-summary.py:39,58,74,87,95,102  status = 'ACTIVE'        ← excludes PARTIALLY_CLOSED
scripts/update-prices.py:44,84,116,123            status='ACTIVE'          ← excludes (external updater — N/A for oink-sync)
scripts/dashboard.py:52,74,93,105,124,139         status = 'ACTIVE'        ← dashboard counts, excludes
scripts/closure-scanner.py:93                     status = 'ACTIVE'        ← external scanner, excludes
scripts/hl-backfill-match.py:45                   status='ACTIVE'          ← external, excludes
scripts/intern-verify.py:103                      status='ACTIVE'          ← ops tool
scripts/auto-close-failsafe.py:51                 status = 'ACTIVE'        ← external failsafe
scripts/db-audit-v2.py:57,63,70,82,113,121-123    status='ACTIVE'          ← audit
scripts/e2e-test.py:106                           status = 'ACTIVE'        ← test harness
scripts/signal-quality-report.py:66               status = 'ACTIVE'        ← report

# /home/oinkv/oinkdb-api/oinkdb-api.py:
lines 324,409,445,619,674,865,934,989,1127,1539,1603  status = 'ACTIVE'    ← API endpoints, will omit partials
  → DEFERRED per plan to A4-F1 (oinkdb-api broadening follow-up)

# /home/oinkv/signal-gateway/scripts/:
kraken-sync.py:143,146,465,547,879,1054,1311      status IN ('ACTIVE','PENDING') / status='ACTIVE'
micro-gate-v3.py:292,302,318,447,839              status IN ('ACTIVE','PENDING') / status='ACTIVE'
signal_gateway/signal_router.py:2245,2255,2322,3072,3616,3917  status IN ('ACTIVE','PENDING')
  → DEFERRED per plan to A4-F2 (signal-gateway dedup — critical: dedup checks
    would currently MISS PARTIALLY_CLOSED, allowing duplicate opens. Must land
    before A4 changes land in production-critical signal-gateway path.)

# /home/oinkv/oink-sync (this PR's scope):
All 10 intended sites modified; NO stray `status='ACTIVE'` left in lifecycle/engine read paths.
Limit-fill path (`status='PENDING'`) intentionally unchanged — correct.
Expiry/cancel paths (`status='PENDING'`) intentionally unchanged — correct.
```

**Hermes assessment:** the in-scope changes are complete and internally consistent. The deferred downstream work is pre-acknowledged by the plan and non-blocking *for merging this oink-sync PR*, but the signal-gateway dedup blindspot (A4-F2) should be explicitly tracked before deploying A4 to the path that feeds signal-gateway's router, or duplicate-opens become possible while a signal is PARTIALLY_CLOSED.

---

## Test Results

```
$ cd /home/oinkv/oink-sync && python3 -m pytest tests/test_partially_closed.py \
      tests/test_lifecycle_events.py tests/test_remaining_pct.py -v --tb=short
============================= test session starts ==============================
collected 58 items

tests/test_partially_closed.py ......................                  [ 37%]
tests/test_lifecycle_events.py ........                                [ 50%]
tests/test_remaining_pct.py .............................              [100%]

============================== 58 passed in 0.06s ==============================

# 21 new A4 tests PASS (all MUST + SHOULD cases from plan §5)
# 8 A1 event tests carry forward (no regression)
# 29 A2 remaining_pct tests carry forward — includes FET #1159 (3 cases)

# Full repo run (tests/):
62 passed, 4 failed in tests/test_yfinance_afterhours.py
  └─ failures: ModuleNotFoundError: 'pandas'/'yfinance' in this sandbox —
     unrelated to A4; pre-existing environmental gap in this reviewer's venv.
```

Targeted A4 numeric-verification tests all pass, including `test_gap_past_all_tps_same_cycle_close` (final_roi === expected blended PnL).

---

## Verdict: ✅ LGTM

Implementation is complete, atomic, and test-covered. All 10 sites modified (L1–L5 + E1–E5), E5 correctly admits PARTIALLY_CLOSED into `_calculate_pnl()`, same-cycle closure eliminates the PARTIALLY_CLOSED limbo state with full blended-PnL correctness, STATUS_CHANGED dedup is both runtime-guarded and hygiene-registered, and FET #1159 regressions remain green. The only non-trivial follow-ups (signal-gateway dedup A4-F2, oinkdb-api A4-F1, oinkfarm dashboards) are explicitly deferred in the FORGE plan and do not block this PR; Hermes flags A4-F2 as the most time-sensitive downstream task. Proceed to GUARDIAN canary on merge.
