# OINKV Staleness Audit — TASK-A9-plan.md

**Task:** A9 — Denomination multiplier (1000-prefixed exchange symbols)
**Plan Tier (as drafted):** 🟢 LIGHTWEIGHT
**Base commits claimed by plan:** oink-sync `ab5d941`, micro-gate `69d6840a`
**Auditor:** Hermes Agent (subagent, read-only audit)
**Audit date:** 2026-04-19
**Plan version audited:** 1.0 (180 lines / 15 KB)
**Reference format:** `OINKV-AUDIT-WAVE2-A5.md`

---

## Summary Verdict

**OVERALL: ⚠️ APPROVE — but with one 🔴 DESIGN-CONFLICT finding and several 🟡 MINOR cleanups.**

The A9 plan is technically accurate against the codebase. The resolver-side primitives (`_DENOMINATION_MULTIPLIERS`, `denomination_multiplier_for()`, `ResolveResult.denomination_multiplier`) and the micro-gate-side 5-tuple contract are already implemented on feature branches and pass their unit tests (23/23 in `oink-sync/tests/test_denomination.py`). ANVIL is mid-implementation; the diffs match the plan.

The one **CRITICAL** finding is that **TASK-A9-plan.md contradicts the Wave 3 FORGE summary** (`A6-A11-SUMMARY.md` §"A9: Normalize at Comparison Time, Not INSERT Time"). The summary declares lifecycle-time normalization as the FORGE decision; the plan explicitly rejects lifecycle-time in §4e and implements INSERT-time. The implementation follows the plan, not the summary. The parent dispatch context quoted the summary, so this is the exact reconciliation Mike/ANVIL need.

**Financial Hotpath status:** ✅ **No drift on the hotpath.** `oink-sync/oink_sync/lifecycle.py` is **not touched** by A9 (verified: 0 hits for `multiplier|denomination|1000` in lifecycle.py). Neither `calculate_blended_pnl`, `_check_sl_tp`, `close_signal`, nor `update_sl` are modified. Tier stays 🟢 LIGHTWEIGHT.

---

## Environment Verification

| Fact | Value | Evidence |
|------|-------|----------|
| oink-sync master HEAD | `e9be741` (A4 PR #7 merged) | `git log master -1` |
| Plan's claimed base `ab5d941` | A4 branch tip, pre-merge (commit is in tree) | `git cat-file -t ab5d941` → commit |
| A9 working branch | `anvil/A9-denomination-multiplier` (checked out, uncommitted diff) | `git status` on `/home/oinkv/oink-sync` |
| Live oink-sync service cwd | `/home/oinkv/oink-sync` (PID 3976647, port 8889) | `readlink /proc/3976647/cwd` |
| Live oink-sync code | **master HEAD** (changes not yet loaded; `/resolve/PEPE` does not yet return `denomination_multiplier`) | `curl :8889/resolve/PEPE` |
| Canonical micro-gate path | `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1 508 LOC) | Plan §2 + file size |
| micro-gate canonical HEAD | `69d6840a feat(A5)` (matches plan's base) | `git log -1` in `.openclaw/workspace` |
| micro-gate working state | branch `anvil/A9-denomination-multiplier`, uncommitted A9 edits | `git status` |
| Secondary micro-gate copy | `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` (1 063 LOC, **no A9 changes**) | grep `denom_mult` → 0 |

Live service has not yet restarted to pick up the new resolver code — not a plan defect, but relevant for ANVIL's deploy checklist.

---

## Findings

### 🔴 CRITICAL — C1: Plan contradicts the Wave 3 FORGE summary on WHERE to normalize

The dispatch context quotes `A6-A11-SUMMARY.md`:

> **A9: Normalize at Comparison Time, Not INSERT Time** — Entry prices should be stored as extracted (raw denomination) because that's what the trader sees. The 1000x multiplier is applied only during PnL/SL/TP calculations in lifecycle.py. This preserves the original signal data.

`TASK-A9-plan.md` §0 and §4e say the **opposite**:

> **FORGE decision:** Fix at **INSERT time** in canonical micro-gate … (§0)
> ### 4e. Why not apply the multiplier in lifecycle.py? Reject the lifecycle-time approach for this task. … So lifecycle-time adjustment is strictly worse than INSERT-time normalization. (§4e)

Both documents were produced by FORGE within minutes of each other on 2026-04-19 (summary 14:25, plan 14:23). The **plan is the more detailed and reasoned artifact**, and its four reasons for choosing INSERT-time (DB gets clean data, gate-time `PRICE_DEVIATION` won't fire, SL/TP stored correctly, GUARDIAN analytics don't read broken data) are correct. The summary's one-paragraph framing is wrong.

Consequences of adopting the plan's position (which is what ANVIL is shipping):
- `lifecycle.py` is untouched — Financial Hotpath risk AVOIDED.
- Only forward-fix: the DB still carries prior mis-denominated rows (plan §4g acknowledges this, says no backfill needed).
- Trader's original quoted price is **not** preserved in the DB — the stored `entry_price` reflects the per-unit denomination. If that provenance matters for downstream auditors, it is only recoverable from `raw_text` or from the `[A9: denomination_adjusted /1000 via 1000PEPEUSDT]` note that the plan adds to the `notes` column.

**Action for Mike / ANVIL:**
1. Acknowledge that the authoritative design statement is the plan, not the summary line.
2. Either correct `A6-A11-SUMMARY.md` to match the plan (preferred) or escalate to Mike if he explicitly wants lifecycle-time normalization — in which case the plan needs a full rewrite and A9 jumps to the Financial Hotpath.

**Hotpath tier gate:** as currently planned and coded, A9 does **not** touch `calculate_blended_pnl`, `_check_sl_tp`, `close_signal`, `update_sl`, or any lifecycle SL/TP write path. Tier remains 🟢 LIGHTWEIGHT. Flipping the design to lifecycle-time (per the stale summary) would escalate to 🔴 CRITICAL — this is the "drift auto-escalates" rule from `vigil-workspace/AGENTS.md`.

---

### 🟡 MINOR — M1: Plan's "one known bad signal" identification is imprecise

Plan §0 / §1 claim:

> Only **one** currently stored row uses a `1000*` exchange ticker (`PEPE → 1000PEPEUSDT`), so this is still a low-volume, forward-fixable issue.

Verified query against `/home/oinkv/.openclaw/workspace/data/oinkfarm.db`:

```
id=1497 | PEPE | 1000PEPEUSDT | entry=3.657e-06 | SL=3.287e-06 | TP1=5.784e-06 | LONG | CLOSED_WIN
```

That row's `entry_price=3.657e-06` is the **per-unit PEPE price**, i.e. the contract price would be `3.657e-06 × 1000 ≈ 0.0036573`. So **id=1497 is stored correctly already** — it is *not* a bad signal under A9's definition. The plan mis-labels it as the "1 known bad signal" headline (also surfaced verbatim in the A6-A11-SUMMARY row "fixes 1 known bad signal").

The actually-suspect PEPE rows are:

```
id=1316 | PEPE | PF_PEPEUSD   | 0.0035035 | CLOSED_LOSS
id=1333 | PEPE | PF_PEPEUSD   | 0.003729  | CLOSED_LOSS
id=1399 | PEPE | PF_PEPEUSD   | 0.0035184 | CLOSED_LOSS
```

Kraken's `PF_PEPEUSD` is per-unit; real PEPE mark price is ≈ `3.5e-06`. These three rows are **1 000× too high for the per-unit exchange they resolved to**. The plan's implementation does **not** fix this case because §4d only acts when `denom_mult > 1`, which requires the resolved symbol to start with `1000PEPE/...`. `PF_PEPEUSD` has `denom_mult = 1`, so the normalization block is skipped and `PRICE_DEVIATION` will reject (or historically has rejected/accepted — note these three are already closed).

**Observed behaviour going forward:** whether a PEPE signal gets A9-normalized depends on resolver ordering. Current resolver picks `binance:1000PEPEUSDT` (verified via `curl :8889/resolve/PEPE`). As long as Binance leads, A9 works. If Binance data is stale and Kraken wins, A9 does not trigger and the price-deviation guard will bounce mis-quoted signals instead. This is acceptable but should be called out for ANVIL (post-implementation) and for GUARDIAN (post-deploy canary).

**No plan change required** — the design is fine — but the plan's narrative about "the one known bad signal" is misleading. Recommend ANVIL clarify this in the Phase-0 proposal.

---

### 🟡 MINOR — M2: Plan §2 puts integration tests in `signal-gateway/tests/`; actual implementation places them in `.openclaw/workspace/tests/`

Plan §2 row:

> `signal-gateway/tests/test_denomination_gate.py` | — | CREATE | Integration tests for micro-gate price normalization before INSERT

Actual file created by implementation: `/home/oinkv/.openclaw/workspace/tests/test_denomination_gate.py` (313 LOC). This **matches the canonical micro-gate path** used elsewhere on A9 (gate code goes to `.openclaw/workspace/scripts/micro-gate-v3.py`, not to `signal-gateway/scripts/micro-gate-v3.py`), so the actual location is correct.

This is a duplicate of the exact canonical-file drift documented in `OINKV-AUDIT-WAVE2-A5.md` §C1 — plan author is writing file paths as `signal-gateway/...` even though the canonical copy is `.openclaw/workspace/...`. A9 inherits the same issue; ANVIL has transparently rerouted to the canonical tree.

**Action:** Update the plan file-list row (documentation only) so that VIGIL doesn't ding the PR for missing the stated test location.

---

### 🟡 MINOR — M3: SL/TP normalization location diverges from plan snippet (acceptable)

Plan §4d presents entry + SL + TP normalization as one contiguous block BEFORE the price-deviation guard (§4d pseudo-code normalizes `entry_price`, `stop_loss`, `tp1..3` in one `if denom_mult > 1:` block).

Actual canonical `micro-gate-v3.py` split the block:

- **Lines 704–716:** entry-only normalization block (before §5 price deviation guard). Sets `_a9_adjusted` flag for the SL/TP follow-up.
- **Lines 833–847:** SL/TP/notes normalization under `if _a9_adjusted:`, run **after** §8/§8b/§8c SL processing (including A15 SL→entry recovery) and §9 TP safety check.

This split is **arguably better**: A15's SL-from-raw-text recovery and B11's SL-deviation guard operate on pre-normalized SL values, then A9 divides by `denom_mult` once SL/TP have been finalized. If the plan's single-block code had been implemented literally, SL/TP would have been normalized before A15's raw-text recovery ran and A15 could have recovered an already-normalized SL into a nonsensical value.

**No defect** — implementation is more correct than the plan snippet. Flag for documentation sync.

---

### 🟡 MINOR — M4: Multiplier table is conservative; no extension procedure

The 8-symbol table in plan §4b / §1 ("Affected ticker set") hard-codes the most common Binance/Bybit 1000-prefixed symbols. Plausibly missing (as of 2026-04-19): `1000TURBO`, `1000CHEEMS`, `1000APU`, `1000MOG`, `1000SATS`, `1000WHY`. Some of these have rotated in and out of exchange listings.

Plan §8 says mitigations include "Centralize multiplier table in resolver.py for easy extension" — OK, but the plan does not define:
- How a new symbol gets added (FORGE plan? GUARDIAN observation? manual edit?).
- Whether the resolver should log a warning when it resolves a `1000*` symbol that is NOT in the table (falling back silently to `multiplier=1` would mis-price a signal, same class of bug A9 is fixing).

**Action:** Low-priority follow-up. Recommend the `denomination_multiplier_for()` helper log a `log.warning` when it sees `symbol.startswith("1000") and len(symbol) > 4 and multiplier == 1`, so new Binance listings surface as known-unknowns. Not blocking A9 merge.

---

### 🟡 MINOR — M5: Live oink-sync has not reloaded; `/resolve/{ticker}` still returns pre-A9 shape

`curl http://localhost:8889/resolve/PEPE` returns:

```json
{"ticker":"PEPE","source":"binance","symbol":"1000PEPEUSDT","asset_class":"crypto","available_on":["binance","bybit","kraken"]}
```

No `denomination_multiplier` field. Reason: the service (PID 3976647) started 2026-04-19 02:39 and the resolver/model edits were made later on the `anvil/A9-denomination-multiplier` branch. Until systemd restarts `oink-sync.service`, `denom_mult` coming out of `resolve_exchange()` in the micro-gate will be the `int(data.get("denomination_multiplier", 1) or 1)` fallback — i.e. `1` — and A9 normalization will be a no-op on every live signal.

This is **expected** for an in-flight branch, not a plan defect. Flag for ANVIL's deploy checklist and for GUARDIAN's canary: after deploy, verify `curl :8889/resolve/PEPE` includes `"denomination_multiplier": 1000`.

---

### 🟡 MINOR — M6: Plan's resolver and micro-gate path labels are a mix of old and new conventions

Plan §2 and §9 variously refer to:
- `oink-sync/oink_sync/resolver.py` (relative — matches `/home/oinkv/oink-sync/...`, the live tree).
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (absolute — canonical).
- `signal-gateway/tests/test_denomination_gate.py` (relative — does **not** map to a live production tree; this is the stale path documented in WAVE2-A5-AUDIT §C1).

No conflict with reality — the `oink-sync/` and `.openclaw/workspace/scripts/` paths both resolve to canonical live code — but the mixed style will recur in the Phase-0 proposal if not cleaned up.

---

### 🟢 CONFIRMED — CF1: `_DENOMINATION_MULTIPLIERS` dict does not collide with any existing resolver logic

Grep of `oink-sync/oink_sync/resolver.py` for `multiplier|1000|denomination|PEPE|FLOKI|SHIB` on the live `anvil/A9-denomination-multiplier` working tree:

- 9 hits in the new A9 block (lines 13–29, matches plan §4b verbatim).
- 1 hit at line 103: `"PEPECOIN": "PEPE"` in `_ALIASES` (pre-existing, unrelated to denomination).
- No `1000` literals anywhere else in the file.
- No prior denomination handling, no conflict.

Plan's claim "There are **no** denomination aliases like `PEPE -> 1000PEPE`, and no multiplier table" (§1) is fully accurate.

---

### 🟢 CONFIRMED — CF2: `ResolveResult` dataclass extension is additive and correct

`git diff master -- oink_sync/models.py` on the A9 branch:

```diff
@@ class ResolveResult:
     fuzzy_to: str | None = None     # corrected ticker if fuzzy-matched
+    denomination_multiplier: int = 1  # A9: 1000 for 1000PEPE-style symbols

@@ def to_dict(self) -> dict:
         "available_on": self.available_on,
+        "denomination_multiplier": self.denomination_multiplier,
```

Matches plan §4a exactly. Default `1` preserves backward compatibility for any JSON consumer that hasn't been updated.

---

### 🟢 CONFIRMED — CF3: `resolve_exchange()` 5-tuple contract matches plan §4c

File `.openclaw/workspace/scripts/micro-gate-v3.py`:

- Line 217: docstring "Returns (exchange_ticker, exchange, mark_price, asset_class, denomination_multiplier)".
- Line 237: `denom_mult = int(data.get("denomination_multiplier", 1) or 1)  # A9`.
- Line 252: returns the 5-tuple with `denom_mult` on success.
- Lines 258, 270, 276: all three error / fallback paths default to `1` (plan §4c "Default to `1` for fallback and error paths" — CONFIRMED).
- Line 661: single call site `exchange_ticker, exchange_name, mark_price, asset_class, denom_mult = resolve_exchange(ticker, server)`.

---

### 🟢 CONFIRMED — CF4: INSERT-time normalization placement matches plan §4d / §4f

Actual implementation at `.openclaw/workspace/scripts/micro-gate-v3.py` lines 704–716 (entry) and 833–847 (SL/TP + notes):

- §4c dedup → §4c-A9 entry normalization → §5 price deviation guard (matches plan's "normalize before the price deviation guard").
- §4f ambiguity heuristic (ratio neither ~1 nor ~N) matched: `_a9_ambiguous = True` → note `[A9: denomination_ambiguous ... ratio=X.XX]` at line 846.
- Plan's `0.5 × N ≤ ratio ≤ 2.0 × N` adjustment window matched at line 709.
- Plan's `[A9: denomination_adjusted /N via 1000PEPEUSDT]` note format matched at line 843.

Minor reshuffling (M3 above) but logically equivalent.

---

### 🟢 CONFIRMED — CF5: Test coverage for §5 is in place

`oink-sync/tests/test_denomination.py` (124 LOC, 23 tests, **23 passed** under Python 3.13) covers:

- §5 unit tests MUST-row #1 `test_denomination_multiplier_for_1000pepe` ✅
- §5 unit tests MUST-row #2 `test_denomination_multiplier_for_pf_pepe` ✅ (named `test_pf_pepeusd_returns_1`)
- §5 unit tests MUST-row #3 `test_resolve_result_includes_multiplier` ✅ (two tests: `test_to_dict_includes_multiplier_default` + `test_to_dict_includes_multiplier_1000`)
- Regression covers `BTCUSDT`, `ETHUSDT`, `None`, empty string, case-insensitivity, whitespace.

`.openclaw/workspace/tests/test_denomination_gate.py` (313 LOC) covers plan §5 integration MUST-rows 4–7 and regression row 8 — `test_adjusts_entry_before_price_deviation` at line 170 verifies the exact scenario in §5 row 4.

Pytest was run (unit only, `-q`): **23 passed in 0.02 s**.

---

### 🟢 CONFIRMED — CF6: `lifecycle.py` is not on the A9 modification list and has zero A9 hits

Grep `/home/oinkv/oink-sync/oink_sync/lifecycle.py` for `multiplier|1000|denomination`: **0 matches**. Grep for `calculate_blended_pnl|_check_sl_tp|close_signal|update_sl`: 7 matches, all pre-existing function definitions / call sites that A9 does not touch. Hotpath clean.

---

### 🟢 CONFIRMED — CF7: Fuzzy-match path preserves the multiplier

Plan §4b fuzzy-match branch (implicit) is honoured at `resolver.py:244`:

```python
corrected = ResolveResult(
    ticker=raw, source=result.source, symbol=result.symbol,
    asset_class=result.asset_class, available_on=result.available_on,
    fuzzy_from=t, fuzzy_to=fuzzy_hit,
    denomination_multiplier=result.denomination_multiplier,   # ← A9
)
```

A fuzzy-corrected PEPECOIN→PEPE→1000PEPEUSDT path still carries `denomination_multiplier=1000` to the gate. No regression on the existing `_ALIASES` table.

---

## Financial Hotpath Flag

**NOT TRIGGERED.** A9 as planned and as implemented does not touch `oink_sync/lifecycle.py`, does not modify `calculate_blended_pnl`, `_check_sl_tp`, `close_signal`, `update_sl`, or any SL/TP write path. Tier remains 🟢 LIGHTWEIGHT.

🚨 **Conditional hotpath flag:** If Mike chooses to honour the `A6-A11-SUMMARY.md` line ("apply multiplier only during PnL/SL/TP calc in lifecycle.py") instead of the plan's INSERT-time design, **A9 becomes a Financial Hotpath change** and auto-escalates to 🔴 CRITICAL. Current implementation is safely on the non-hotpath side — ratify the plan to keep it there.

---

## File Drift Summary

| File | Canonical location | Drift? |
|------|--------------------|--------|
| `resolver.py` | `/home/oinkv/oink-sync/oink_sync/resolver.py` | Single canonical copy. Live process cwd matches. |
| `models.py` | `/home/oinkv/oink-sync/oink_sync/models.py` | Single canonical copy. |
| `micro-gate-v3.py` | `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1 508 LOC) | **Drift:** `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` (1 063 LOC) has **no A9 changes**. Same canonical-copy issue documented in `OINKV-AUDIT-WAVE2-A5.md`. Canonical is `.openclaw/workspace`. |
| `lifecycle.py` | `/home/oinkv/oink-sync/oink_sync/lifecycle.py` | Single canonical copy. Untouched by A9 (correct). |
| `tests/test_denomination.py` | `/home/oinkv/oink-sync/tests/` | Single canonical copy. |
| `tests/test_denomination_gate.py` | `/home/oinkv/.openclaw/workspace/tests/` | Plan documents the wrong path (`signal-gateway/tests/`). Canonical location was used in implementation. See M2. |

---

## Recommended Actions (in priority order)

1. **🔴 Mike:** Adjudicate C1 — confirm INSERT-time design and correct the `A6-A11-SUMMARY.md` §"A9: Normalize at Comparison Time" paragraph to match `TASK-A9-plan.md` §0/§4e. Implementation is correct under the plan's position.
2. **🟡 FORGE:** Update TASK-A9-plan.md §2 to point the integration-test file at `.openclaw/workspace/tests/test_denomination_gate.py` (M2). Update §0/§1 to clarify the "1 known bad signal" claim — id=1497 is already correctly stored; the real anomaly class is PEPE-on-PF_PEPEUSD rows which A9 does NOT fix (M1).
3. **🟡 ANVIL:** Include in the Phase-0 proposal the post-deploy validation: `curl :8889/resolve/PEPE` must return `denomination_multiplier=1000` after `systemctl restart oink-sync.service` (M5).
4. **🟡 GUARDIAN:** Post-deploy canary should watch for signals tagged `[A9: denomination_adjusted /1000 ...]` AND for any signal where `exchange_ticker LIKE '1000%' AND entry_price > mark_price * 10` — the latter indicates A9 failed to fire.
5. **🟡 Follow-up (not blocking):** Add `log.warning` in `denomination_multiplier_for()` for unknown `1000*` symbols (M4).

---

## Evidence (raw artefacts consulted)

**Files read / grep'd (read-only):**
- `/home/oinkv/forge-workspace/plans/TASK-A9-plan.md` (180 lines)
- `/home/oinkv/forge-workspace/plans/A6-A11-SUMMARY.md` (95 lines)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A5.md` (reference format)
- `/home/oinkv/oink-sync/oink_sync/resolver.py` (324 lines, with A9 edits)
- `/home/oinkv/oink-sync/oink_sync/models.py` (with A9 edits)
- `/home/oinkv/oink-sync/oink_sync/lifecycle.py` (grep only, no A9 changes)
- `/home/oinkv/oink-sync/tests/test_denomination.py` (124 lines)
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1 508 lines, with A9 edits)
- `/home/oinkv/.openclaw/workspace/tests/test_denomination_gate.py` (313 lines)
- `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` (1 063 lines, no A9 changes — drift copy)

**Git inspections:**
- `cd /home/oinkv/oink-sync && git log master / git log --all / git status / git diff HEAD`
- `cd /home/oinkv/.openclaw/workspace && git log / git status`
- `cd /home/oinkv/signal-gateway && git log`

**DB queries (read-only, `/home/oinkv/.openclaw/workspace/data/oinkfarm.db`):**

```sql
SELECT id, ticker, exchange_ticker, entry_price, stop_loss, take_profit_1, direction, status
FROM signals
WHERE ticker IN ('PEPE','1000PEPE','FLOKI','1000FLOKI','SHIB','1000SHIB','BONK','1000BONK')
ORDER BY ticker, id;

SELECT COUNT(*) FROM signals WHERE notes LIKE '%A9:%';   -- 0 (feature not yet live)
```

**Live service probe:**
- `curl -s http://localhost:8889/resolve/PEPE` → returned pre-A9 JSON shape (no `denomination_multiplier` field) → confirms live code is pre-A9.

**Test execution:**
- `cd /home/oinkv/oink-sync && python3 -m pytest tests/test_denomination.py -q` → `23 passed in 0.02s`.

---

*Hermes Agent — read-only audit, no source modifications. Only write: this file.*
