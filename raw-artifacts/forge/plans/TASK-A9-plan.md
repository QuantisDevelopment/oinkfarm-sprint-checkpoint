# Task A.9: Denomination Multiplier Table

**Source:** Arbiter-Oink Phase 4 §3 (Signal Metadata Enrichment), Phase 5 §BS-9 (Ticker Denomination Drift)
**Tier:** 🟢 LIGHTWEIGHT
**Dependencies:** None
**Estimated Effort:** 0.5 day
**Plan Version:** 1.0
**Codebase Verified At:** micro-gate `69d6840a` / oink-sync `ab5d941` (2026-04-19)

---

## 0. Executive Summary

Some crypto venues list micro-cap assets using prefixed contract symbols like `1000PEPEUSDT`, `1000FLOKIUSDT`, and `1000SHIBUSDT`. The resolver currently returns the exchange-native symbol correctly, but neither oink-sync nor micro-gate carries any denomination metadata. If the trader quotes the contract-denominated price while the live price feed returns the per-unit price, the gate can reject the signal as `PRICE_DEVIATION`, or worse, store mis-scaled entry/SL/TP values that later produce broken PnL and closure logic.

**Verified production evidence:**
- `PEPE` appears 4 times in production with entry prices spanning `3.657e-06` to `0.003729`, a 1000× range
- One row already resolved to `exchange_ticker='1000PEPEUSDT'` with `entry_price=3.657e-06`
- Three rows resolved to `exchange_ticker='PF_PEPEUSD'` with entry prices around `0.0035`
- `FLOKI` appears once as `PF_FLOKIUSD` at `0.0286`
- Only **one** currently stored row uses a `1000*` exchange ticker (`PEPE → 1000PEPEUSDT`), so this is still a low-volume, forward-fixable issue

**FORGE decision:** Fix at **INSERT time** in canonical micro-gate, but source the multiplier from **oink-sync resolver metadata**. Specifically:
1. Add a `_DENOMINATION_MULTIPLIERS` table in `oink-sync/oink_sync/resolver.py`
2. Extend `ResolveResult` to include `denomination_multiplier`
3. Expose that field via `/resolve/{ticker}` (already serialized by `to_dict()`)
4. In canonical micro-gate, consume `denomination_multiplier` from `resolve_exchange()` and normalize `entry_price`, `stop_loss`, and TP prices **before** the price deviation guard runs

This avoids lifecycle-time math hacks and guarantees the DB stores prices in the same denomination as the live oracle.

---

## 1. Current State Analysis

### resolver.py has aliases, but no denomination metadata

Verified in `oink-sync/oink_sync/resolver.py`:

```python
_ALIASES = {
    "MONAD": "MON",
    "PUMPFUN": "PUMP",
    "RNDR": "RENDER",
    ...
    "PEPECOIN": "PEPE",
    "DONALDTRUMP": "TRUMP",
}
```

There are **no** denomination aliases like `PEPE -> 1000PEPE`, and no multiplier table.

### ResolveResult has no multiplier field

Verified in `oink-sync/oink_sync/models.py`:

```python
@dataclass
class ResolveResult:
    ticker: str
    source: str
    symbol: str
    asset_class: str = "crypto"
    available_on: list[str] = field(default_factory=list)
    fuzzy_from: str | None = None
    fuzzy_to: str | None = None
```

The `symbol` can be `1000PEPEUSDT`, but callers have no structured way to know that the symbol implies a multiplier.

### micro-gate resolve_exchange() returns only 4 values

Verified in canonical micro-gate:

```python
def resolve_exchange(ticker, server):
    ...
    return exchange_ticker, exchange_name, mark_price, asset_class
```

Call site in `_process_signal()`:

```python
exchange_ticker, exchange_name, mark_price, asset_class = resolve_exchange(ticker, server)
```

No multiplier is returned to the INSERT path.

### The price deviation guard runs before any denomination adjustment

Verified in canonical micro-gate lines ~692–708:

```python
if mark_price and mark_price > 0 and entry_price > 0:
    deviation = abs(entry_price - mark_price) / mark_price
    if deviation > 0.35:
        _log_rejection(entry, "PRICE_DEVIATION", ...)
        return {"action": "rejected", ...}
```

This is the critical bug surface. A signal quoted in 1000-unit denomination can be rejected **before insert** if its entry price is 1000× the live mark.

### Production evidence: PEPE 1000× spread is real

Verified query:

```sql
SELECT id, ticker, exchange_ticker, entry_price, direction, status
FROM signals
WHERE ticker IN ('PEPE','FLOKI','1000PEPE','1000FLOKI','SHIB','1000SHIB')
ORDER BY ticker, id;
```

Results:

```
1241 | FLOKI | PF_FLOKIUSD   | 0.0286    | LONG | CLOSED_LOSS
1316 | PEPE  | PF_PEPEUSD    | 0.0035035 | LONG | CLOSED_LOSS
1333 | PEPE  | PF_PEPEUSD    | 0.003729  | LONG | CLOSED_LOSS
1399 | PEPE  | PF_PEPEUSD    | 0.0035184 | LONG | CLOSED_LOSS
1497 | PEPE  | 1000PEPEUSDT  | 3.657e-06 | LONG | CLOSED_WIN
```

### Current `1000*` exchange_ticker usage is small but present

Verified query:

```sql
SELECT ticker, exchange_ticker, COUNT(*)
FROM signals
WHERE exchange_ticker LIKE '1000%'
GROUP BY ticker, exchange_ticker;
```

Result:

```
PEPE | 1000PEPEUSDT | 1
```

### Affected ticker set

The resolver `_ALIASES` dict does **not** identify denomination-prefixed symbols. The multiplier table therefore must be explicit. Based on common Binance/Bybit listings and the task brief, the initial supported set should be:

| Prefix | Multiplier |
|--------|------------|
| `1000PEPE` | 1000 |
| `1000FLOKI` | 1000 |
| `1000SHIB` | 1000 |
| `1000BONK` | 1000 |
| `1000LUNC` | 1000 |
| `1000RATS` | 1000 |
| `1000X` | 1000 |
| `1000CAT` | 1000 |

Only `PEPE` is confirmed in production today, but the table should be forward-looking.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `oink-sync/oink_sync/resolver.py` | module-level | ADD | Add `_DENOMINATION_MULTIPLIERS` dict and helper `denomination_multiplier_for(symbol)` |
| `oink-sync/oink_sync/models.py` | `ResolveResult` | MODIFY | Add `denomination_multiplier: int = 1` field and include in `to_dict()` |
| `oink-sync/oink_sync/resolver.py` | `resolve()` | MODIFY | Populate `ResolveResult.denomination_multiplier` from resolved `symbol` |
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | `resolve_exchange()` | MODIFY | Read `denomination_multiplier` from oink-sync `/resolve/{ticker}` response and return 5-tuple |
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_signal()` | MODIFY | Normalize entry/SL/TP prices before price deviation guard when multiplier applies |
| `oink-sync/tests/test_denomination.py` | — | CREATE | Unit tests for multiplier lookup and resolver serialization |
| `signal-gateway/tests/test_denomination_gate.py` | — | CREATE | Integration tests for micro-gate price normalization before INSERT |

---

## 3. SQL Changes

### 3a. No schema migration required

This task is logic-only. The normalization happens before INSERT, so no new DB columns are needed.

### 3b. Verification queries

```sql
-- Inspect future 1000-prefixed rows
SELECT id, ticker, exchange_ticker, entry_price, stop_loss, take_profit_1
FROM signals
WHERE exchange_ticker LIKE '1000%'
ORDER BY id DESC
LIMIT 20;

-- Expected after A9:
-- entry_price / stop_loss / TPs are stored in the same denomination as live mark_price
```

---

## 4. Implementation Notes

### 4a. Extend ResolveResult instead of inventing a second lookup path

Because micro-gate already calls oink-sync `/resolve/{ticker}`, the cleanest design is to attach `denomination_multiplier` to the resolver response.

**models.py:**

```python
@dataclass
class ResolveResult:
    ticker: str
    source: str
    symbol: str
    asset_class: str = "crypto"
    available_on: list[str] = field(default_factory=list)
    fuzzy_from: str | None = None
    fuzzy_to: str | None = None
    denomination_multiplier: int = 1
```

And in `to_dict()`:

```python
"denomination_multiplier": self.denomination_multiplier,
```

### 4b. Resolver helper in `resolver.py`

```python
_DENOMINATION_MULTIPLIERS = {
    "1000PEPE": 1000,
    "1000FLOKI": 1000,
    "1000SHIB": 1000,
    "1000BONK": 1000,
    "1000LUNC": 1000,
    "1000RATS": 1000,
    "1000X": 1000,
    "1000CAT": 1000,
}


def denomination_multiplier_for(symbol: str) -> int:
    s = (symbol or "").upper().strip()
    for prefix, mult in _DENOMINATION_MULTIPLIERS.items():
        if s.startswith(prefix):
            return mult
    return 1
```

Then in `resolve()`:

```python
mult = denomination_multiplier_for(best_sym)
result = ResolveResult(
    ticker=raw,
    source=best_name,
    symbol=best_sym,
    asset_class=self._infer_class(t, best_name),
    available_on=[...],
    denomination_multiplier=mult,
)
```

### 4c. canonical micro-gate `resolve_exchange()` returns 5-tuple

Current return:

```python
return exchange_ticker, exchange_name, mark_price, asset_class
```

New return:

```python
return exchange_ticker, exchange_name, mark_price, asset_class, denomination_multiplier
```

Default to `1` for fallback and error paths.

### 4d. Normalize before the price deviation guard

This is the most important implementation detail.

Current flow:
1. resolve exchange
2. cross-channel duplicate check
3. **price deviation guard**
4. infer order type
5. INSERT

A9 must insert a normalization step **between exchange resolution and price deviation guard**.

Recommended logic:

```python
# after resolve_exchange(...)
exchange_ticker, exchange_name, mark_price, asset_class, denom_mult = resolve_exchange(ticker, server)

if denom_mult > 1 and mark_price and mark_price > 0 and entry_price and entry_price > 0:
    ratio = entry_price / mark_price
    # only adjust when trader price is approximately N x live price
    if denom_mult * 0.5 <= ratio <= denom_mult * 2.0:
        entry_price = round(entry_price / denom_mult, 10)
        if stop_loss is not None:
            stop_loss = round(stop_loss / denom_mult, 10)
        if tp1 is not None:
            tp1 = round(tp1 / denom_mult, 10)
        if tp2 is not None:
            tp2 = round(tp2 / denom_mult, 10)
        if tp3 is not None:
            tp3 = round(tp3 / denom_mult, 10)
        notes_parts.append(f"[A9: denomination_adjusted /{denom_mult} via {exchange_ticker}]")
```

### 4e. Why not apply the multiplier in lifecycle.py?

Reject the lifecycle-time approach for this task.

If lifecycle.py adjusted entry/exit comparisons later:
- the DB would still contain mis-scaled `entry_price`
- `PRICE_DEVIATION` would still reject good signals at gate time
- SL/TP thresholds would still be mis-stored
- GUARDIAN analytics would still read broken raw data

So lifecycle-time adjustment is strictly worse than INSERT-time normalization.

### 4f. Ambiguity handling

Some trader messages may already quote the per-unit price even when the exchange symbol is `1000PEPEUSDT`. Therefore **do not blindly divide** whenever a 1000-prefixed ticker appears. Require the live-price ratio heuristic to indicate that the submitted price is approximately `N × mark_price`.

If the ratio is already approximately 1.0, no adjustment.

If the ratio is neither ~1.0 nor ~N.0, append a note and do not adjust:

```python
notes_parts.append(
    f"[A9: denomination_ambiguous {exchange_ticker} ratio={ratio:.2f}]"
)
```

### 4g. Existing rows

Only one stored row currently uses a `1000*` exchange ticker. All current affected rows are already closed, so **no backfill is required** for Phase A. This is a forward-fix.

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_denomination_multiplier_for_1000pepe` | `symbol='1000PEPEUSDT'` | returns `1000` | unit | MUST |
| `test_denomination_multiplier_for_pf_pepe` | `symbol='PF_PEPEUSD'` | returns `1` | unit | MUST |
| `test_resolve_result_includes_multiplier` | resolver returns `1000PEPEUSDT` | JSON contains `denomination_multiplier: 1000` | unit | MUST |
| `test_gate_adjusts_entry_before_price_deviation` | `entry_price=0.0035`, `mark_price=0.0000035`, `symbol='1000PEPEUSDT'` | entry normalized to `0.0000035`, signal not rejected for price deviation | integration | MUST |
| `test_gate_adjusts_sl_and_tp_levels` | same as above with SL/TP values in contract denomination | all price levels divided by 1000 | integration | MUST |
| `test_gate_does_not_adjust_when_ratio_is_one` | `entry_price≈mark_price`, `symbol='1000PEPEUSDT'` | no adjustment applied | integration | MUST |
| `test_gate_marks_ambiguous_ratio` | ratio neither ~1 nor ~1000 | no adjustment; note contains `A9: denomination_ambiguous` | integration | SHOULD |
| `test_non_prefixed_symbol_no_change` | `BTCUSDT`, multiplier=1 | no normalization | regression | MUST |

---

## 6. Acceptance Criteria

1. `GET /resolve/PEPE` returns `denomination_multiplier=1000` when resolver chooses `1000PEPEUSDT`
2. canonical micro-gate consumes the multiplier and adjusts prices before the `PRICE_DEVIATION` guard
3. New 1000-prefixed signals store `entry_price`, `stop_loss`, and TP fields in the same denomination as the live oracle
4. Non-prefixed symbols remain unchanged
5. Existing resolver behavior for non-denomination tickers is unaffected

---

## 7. Rollback Plan

1. Revert oink-sync resolver/model changes: `git revert <A9-oink-sync-commit>`
2. Revert canonical micro-gate changes: `git revert <A9-micro-gate-commit>`
3. Restart oink-sync and the micro-gate consumer
4. Verify:
   ```sql
   SELECT COUNT(*) FROM signals WHERE notes LIKE '%A9: denomination_adjusted%';
   ```
   New rows after rollback should stop receiving the tag

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| False-positive normalization for already-correct prices | Low | Medium | Require ratio≈multiplier before adjusting |
| False-negative on valid 1000-ticker signal | Medium | Low | Add note for ambiguous ratios and review manually |
| Missing a future 1000-prefixed asset | Medium | Low | Centralize multiplier table in resolver.py for easy extension |
| Breaking `/resolve` consumers that assume old response shape | Low | Low | Additive JSON field only, no removals |
| Adjusting entry without adjusting SL/TP | Low | HIGH | MUST-PASS integration test on all price fields |

---

## 9. Evidence

**Files read:**
- `/home/oinkv/oink-sync/oink_sync/resolver.py` (commit `ab5d941`) — full resolver structure, `_ALIASES`, `resolve()`
- `/home/oinkv/oink-sync/oink_sync/models.py` — `ResolveResult` dataclass
- `/home/oinkv/oink-sync/oink_sync/app.py` — `/resolve/{ticker}` endpoint returns `result.to_dict()`
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (commit `69d6840a`) — `resolve_exchange()` and `_process_signal()` price deviation guard

**Database queries run:**
```sql
SELECT ticker, COUNT(*) as cnt, MIN(entry_price), MAX(entry_price)
FROM signals
WHERE ticker IN ('PEPE','1000PEPE','FLOKI','1000FLOKI','SHIB','1000SHIB','BONK','1000BONK','LUNC','1000LUNC')
GROUP BY ticker
ORDER BY ticker;
-- FLOKI | 1 | 0.0286 | 0.0286
-- PEPE  | 4 | 3.657e-06 | 0.003729

SELECT id, ticker, exchange_ticker, entry_price, direction, status
FROM signals
WHERE ticker IN ('PEPE','FLOKI','1000PEPE','1000FLOKI','SHIB','1000SHIB')
ORDER BY ticker, id;
-- confirmed PEPE/FLOKI rows listed in §1

SELECT ticker, exchange_ticker, COUNT(*)
FROM signals
WHERE exchange_ticker LIKE '1000%'
GROUP BY ticker, exchange_ticker;
-- PEPE | 1000PEPEUSDT | 1
```

**Git commits reviewed:**
- `ab5d941` — oink-sync HEAD
- `69d6840a` — canonical micro-gate HEAD
