# 🧠 HERMES Independent Review — PR #125 / Task A3 (Auto filled_at for MARKET)

**Branch:** `anvil/A3-filled-at` @ `d4428eab`
**Tier:** 🔴 CRITICAL (Financial Hotpath #6: micro-gate INSERT)
**Review mode:** Third-party sanity check (VIGIL PASS 9.85, GUARDIAN PASS 10.00)
**Date:** 2026-04-18

---

## Positional audit — INSERT in `_process_signal` (scripts/micro-gate-v3.py:844-862)

Manually counted the three lists (column list / `?` placeholders / Python tuple):

| # | Column           | Placeholder | Bound value |
|---|------------------|-------------|-------------|
| 1–5 | discord_message_id, channel_id, channel_name, server_id, trader_id | ?×5 | dmid, channel_id, channel, server_id, trader_id |
| 6–10 | ticker, direction, order_type, entry_price, stop_loss | ?×5 | ticker, direction, order_type, entry_price, stop_loss |
| 11–13 | take_profit_1/2/3 | ?×3 | tp1, tp2, tp3 |
| 14–17 | status, confidence, notes, raw_text | ?×4 | status, confidence, notes, entry.get("raw_text","") |
| 18–20 | posted_at, updated_at, source_url | ?×3 | posted_at, _now_iso(), source_url |
| 21–25 | leverage, asset_class, exchange_ticker, exchange, exchange_matched | ?×5 | leverage, asset_class, exchange_ticker, exchange_name, exchange_matched |
| 26–28 | fill_status, message_type, **filled_at** | ?×3 | fill_status, "SIGNAL", **filled_at** |

**28 columns = 28 placeholders = 28 bound values, all positionally aligned.** Column-28 (`filled_at`) maps to bound-28 (`filled_at` variable). No mismatch.

## Risk checks

- **a. Count match:** ✅ 28/28/28.
- **b. Column order:** ✅ Prod schema (`.schema signals`) has `filled_at` declared mid-table, but that is irrelevant — this INSERT uses a named column list, so only intra-list positional alignment matters. Verified.
- **c. Backfill SQL scope:** ✅ `WHERE order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL` is strict, idempotent, and leaves the 9 LIMIT/FILLED NULLs untouched. Cannot corrupt data; worst case re-run is a no-op.
- **d. Downstream consumers expecting `filled_at IS NULL` for MARKET:** ✅ None. Repo-wide grep for `filled_at IS NULL` / `is None` returns only the archived `oinkdb-agent/CHECKLIST-v2.md` note stating "market orders **may not**" have filled_at (permissive, not required). `portfolio_stats.py:410,917`, `api/oinkdb-api.py:1152`, and `kraken-sync.py:566` all use the `filled_at or posted_at` pattern — when `filled_at == posted_at`, the computed value is **identical** to the pre-A3 fallback. Provably behavior-preserving.
- **e. Grace-period in kraken-sync.py (this repo's equivalent of oink-sync/lifecycle.py):** ✅ Line 566 `ref_ts = row["filled_at"] or row["posted_at"]`. For new MARKET rows, `filled_at` is set to the exact same value that the `or` fallback was producing pre-A3 — zero drift in grace-period window. LIMIT rows still NULL at INSERT, set by kraken-sync itself at line 736 (untouched by A3).

## Test run (independent verification)

Checked out branch into workspace, ran `pytest tests/test_micro_gate_filled_at.py tests/test_micro_gate_source_url.py -x -q` → **11 passed in 0.03s**. Reverted workspace. MUST-5 (regex-based column/placeholder count test) is the single most valuable test here — directly traps the one plausible failure mode.

## Concrete findings beyond VIGIL

1. **Order-type inference coverage gap (low):** Lines 682-689 *infer* `order_type` when `ext.get("order_type")` is missing (`MARKET` if |deviation|<2%, else `LIMIT`). Both tests set `order_type` explicitly; no test exercises the inferred path hitting A3's ternary. Low risk — the ternary is symmetric in both inputs — but an inferred-path test would close the loop.
2. **`dry_run` returns pre-A3 (line 837) before `filled_at` is computed (line 842):** dry-run inspection cannot see what `filled_at` *would* be. VIGIL noted this. Not a correctness issue, but operationally annoying for pre-deploy audits.
3. **Backfill SQL is only a test constant (`_BACKFILL_SQL`), not a migration artifact.** VIGIL flagged. Agree — worth promoting to `scripts/backfill-a3-filled-at.sql` for production audit trail of the exact DDL executed.
4. **`posted_at` type pass-through:** if a caller ever hands in a non-string `timestamp`, `filled_at` mirrors it faithfully. Consistency preserved; no new failure mode.
5. **`api/oinkdb-api.py:1152` WebSocket `limit_filled` event** uses `sig.get("filled_at") or datetime.now(...)`. A3 does not alter LIMIT fill path, and MARKET orders never emit `limit_filled` (they start FILLED — no PENDING→FILLED transition observed). Confirmed no side-effect.

Nothing VIGIL or GUARDIAN missed rises to the level of a blocker.

---

## Verdict: ✅ LGTM

Truly surgical change — 10 production lines, 381 test lines, one comment block, zero formula impact, zero schema change, provably equivalent downstream behavior via the pre-existing `filled_at or posted_at` idiom. MUST-5 (count-match regex) is excellent risk mitigation for the only real failure mode. Concur with VIGIL 9.85 PASS and GUARDIAN 10.00 PASS. Ship it, run the 8-row backfill, run the 10-signal canary.

*— 🧠 HERMES, independent third-party review, 2026-04-18*
