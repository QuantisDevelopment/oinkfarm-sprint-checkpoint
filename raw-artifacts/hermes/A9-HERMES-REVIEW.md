# Hermes Review — A9: Denomination Multiplier Table

**PRs:** oinkfarm #132 (`890afce1`) + oink-sync #8 (`c8b653f`)
**Branch:** anvil/A9-denomination-multiplier
**Reviewed:** 2026-04-19
**VIGIL score:** 9.15 PASS

## Verdict: 🟡 CONCERNS — mergeable, flag for post-merge monitoring

The implementation is correct for the INSERT-time scope it targets. No blocking regression. However, I found two scope-gap issues that VIGIL didn't flag (UPDATE/CLOSURE paths lack A9 normalization) and one narrow ordering issue (cross-channel dedup runs before A9 normalization). All three are narrow / per-plan-scope, but worth explicit monitoring.

---

## Verification Steps Completed

### 1. VIGIL review read ✅
Confirmed 9.15 PASS, correctly upgraded tier STANDARD, all 15 checkpoint items verified.

### 2. PR diffs inspected ✅
- **oink-sync #8:** 3 files (+155/-0): `models.py` (+2), `resolver.py` (+29), new `tests/test_denomination.py` (+124)
- **oinkfarm #132:** 6 files (+331/-9): `scripts/micro-gate-v3.py` (+38/-5), new `tests/test_denomination_gate.py` (+289), 4 test files updated for 5-tuple

### 3. Tests run locally ✅
- **oink-sync:** `89/89 passed` (including 23 new denomination tests) — matches VIGIL
- **oinkfarm (tests/):** `83 passed, 5 failed` — the 5 failures confirmed pre-existing (reproduced on parent commit `69d6840a` before A9 changes: `test_micro_gate_mutation_guard` x3, `test_micro_gate_wg_alert_override` x2)
- **oinkfarm new `test_denomination_gate.py`:** `13/13 passed`

### 4. Downstream consumer audit ✅
- `resolve_exchange` in oinkfarm: **only one caller** — `_process_signal` line 661 (updated). No other callers in oinkfarm/api, portfolio_stats, lifecycle, or extractors.
- `oinkdb-api.py:265` calls `kraken_resolver.resolve_exchange()` (different module, returns dict not tuple, untouched signature) — ✅ safe
- `ResolveResult(...)` constructor — 2 production call sites in `resolver.py` (direct @253, fuzzy @236), both propagate `denomination_multiplier` correctly
- `to_dict()` serialization correctly includes field
- All 4 test stubs updated to 5-tuple (confirmed via diff)

### 5. Edge-path verification ✅
- Fuzzy-match path propagates denomination_multiplier from corrected result (resolver.py:244)
- 404 / HTTP-error / kraken-fallback all return `multiplier=1` (backward compatible)
- Dry-run parity: `dry_run_insert` path returns `entry_price` AFTER A9 step 4c normalization → parity maintained ✅

---

## Issues Found

### 🟡 H1 — Cross-channel dedup runs BEFORE A9 normalization (narrow ordering regression)
**Location:** `micro-gate-v3.py` lines 678–714 (step 4b dedup at 678, A9 normalization at 701)

Step 4b cross-channel dedup queries `WHERE trader_id=? AND ticker=? AND direction=? AND entry_price=?` using the un-normalized raw `entry_price` (e.g., `0.003657`). Step 4c then normalizes and writes `3.657e-06`.

Scenario: Channel A posts 1000PEPE @ entry=0.003657 → inserted normalized as 3.657e-06. Moments later, the same trader cross-posts the same signal to Channel B (different dmid). Step 4b compares raw 0.003657 against DB's stored 3.657e-06 → miss → duplicate row created.

**Pre-A9, both would have been stored as 0.003657 and dedup worked.** Post-A9, this dedup is broken for the 8 normalized tickers when a trader cross-posts.

**Severity:** NARROW (8 tickers, cross-posting trader only). No table UNIQUE constraint covers this — `discord_message_id` UNIQUE only catches same-dmid retries, not cross-channel.

**Fix:** Move step 4c (A9 normalization) above steps 4 and 4b. Safe reorder since 4c only touches prices.

### 🟡 H2 — UPDATE path has NO A9 normalization (scope gap, creates mixed-denomination rows)
**Location:** `_process_update()` lines 1061–1086

Trader UPDATE messages quoting SL/TP in contract denomination (e.g., "SL → 0.003" for 1000PEPE) would write raw into DB. Row becomes: `entry_price=3.657e-06` (normalized), `stop_loss=0.003` (raw) — mixed denominations.

The B14 guard at line 1077 checks `abs(new_sl - _entry) / _entry < 0.005` — with normalized entry=3.657e-06 and un-normalized new_sl=0.003, ratio is ~820 (huge), B14 does not fire, raw write proceeds.

This is scope-consistent with the plan ("INSERT-time normalization only"), but it's a real data-integrity gap. Downstream PnL calculation would blend normalized entry × raw exit → garbage.

**Fix:** Apply the same A9 ratio-heuristic in `_process_update` against `sig["entry_price"]` (which by then IS normalized). Follow-up task A9.1.

### 🟡 H3 — CLOSURE path has NO A9 normalization (same scope gap)
**Location:** `_process_closure()`

Trader "Closed at 0.0036" with normalized entry=3.657e-06 → PnL math explodes. Same mitigation/scope as H2.

### 🟢 H4 — Docstring drift (VIGIL S1 re-confirmed)
`denomination_multiplier_for()` docstring says "stripped of USDT/USDC/USD suffixes" but the function actually does prefix matching via `startswith()`. Misleading, not incorrect. Minor nit.

### 🟢 H5 — Test helper duplicates production logic (VIGIL S2 re-confirmed)
`_a9_normalize()` in `test_denomination_gate.py` replicates the math rather than invoking `_process_signal()`. Divergence risk. At least one integration test through the actual function should exist.

---

## What's Done Well
- Surgical diff, only one consumer of the 5-tuple change, clean migration
- Ratio 3-way classification (adjust / pass-through / ambiguous) is defensive
- Boundary tests at exact `mult×0.5` and `mult×2.0` bounds
- Fuzzy-match path correctly propagates multiplier through the `corrected` reconstruction
- All fallback paths (404, HTTP error, kraken fallback) return `multiplier=1` — backward safe
- Dry-run parity maintained (A9 4c at line 701 runs before INSERT at line 945/946, so `dry_run_insert` returns normalized `entry_price`)
- Known-bad PEPE scenario reproduced as test
- No schema changes, pure git revert rollback
- All 4 existing test stubs updated for 5-tuple correctly

---

## Summary

**Tests:** oink-sync 89/89 ✅, oinkfarm 83/83 existing ✅ (5 pre-existing failures unchanged — confirmed on parent commit), oinkfarm new 13/13 ✅.

**Downstream check:** only one `resolve_exchange` tuple consumer in oinkfarm, cleanly updated. `oinkdb-api.py` uses a separate (dict-returning) `kraken_resolver.resolve_exchange` — untouched. No break.

**Merge decision:** 🟡 CONCERNS — ship it, but:
- **Fix H1 pre-merge if quick** (reorder A9 4c above 4/4b) — narrow but real regression vs pre-A9 for the 8 tickers when cross-posted
- **Follow-up task for H2/H3** (UPDATE/CLOSURE A9 normalization) — creates mixed-denomination rows; acknowledge and schedule A9.1
- **Post-deploy canary:** ANVIL/GUARDIAN should grep for signals where `entry_price < 1e-4` and later `stop_loss > 1e-3` on same row (H2 smoking gun)
- Watch first 10 `1000*USDT` signals for correct `[A9: denomination_adjusted /1000]` tag

## Final Verdict: 🟡 CONCERNS
