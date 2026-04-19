# 🛡️ GUARDIAN Phase 1 Review — A9: Denomination Multiplier Table

| Field | Value |
|---|---|
| Branch | `anvil/A9-denomination-multiplier` |
| Commits | `b9086018` (oinkfarm), `dc35867` (oink-sync) |
| Change Tier | 🟢 LIGHTWEIGHT (reviewed on request) |
| Review Round | Round 2 |
| Review Date | 2026-04-19 |
| PRs | `oinkfarm #132`, `oink-sync #8` |

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|---|---:|---:|---|
| 1 | Schema Correctness | 25% | 10 | Carried forward. No DDL, no migration, no schema mutation. `ResolveResult` remains additive metadata only. |
| 2 | Formula Accuracy | 25% | 10 | Reproduced the prior P1 path on Round 2 code. Valid PEPE / `1000PEPEUSDT` signal with SL now INSERTs successfully, with entry, SL, and all TPs normalized before downstream guards. |
| 3 | Data Migration Safety | 20% | 10 | Carried forward. No backfill, no destructive writes, no retroactive mutation of stored signals. |
| 4 | Query Performance | 10% | 9 | Carried forward. No new SQL or index requirement. Added work remains constant-time normalization and existing resolver metadata handling. |
| 5 | Regression Risk | 20% | 9 | Prior P2 dedup miss is fixed: replayed same-message path now skips as `DUPLICATE` after normalization. Two new end-to-end `_process_signal()` tests cover the previously missed live-ordering interactions. Minor deduction remains because this still touches hot-path ingest ordering in `micro-gate-v3.py`. |
|  | **OVERALL** | 100% | **9.80** | |

**Weighted score:** `(10×0.25) + (10×0.25) + (10×0.20) + (9×0.10) + (9×0.20) = 9.80`

## Re-Review Scope

Round 2 touched GUARDIAN-owned dimensions directly, so I re-scored the affected dimensions rather than carrying forward the whole review.

Affected areas re-verified:
- normalization ordering on the live `_process_signal()` path
- snowflake dedup behavior after normalization
- end-to-end regression coverage for the two prior blockers
- oink-sync H4 docstring correction

Unaffected dimensions carried forward:
- Schema Correctness
- Data Migration Safety
- Query Performance

## Pre-Deploy Baseline Snapshot

| Metric | Current Value |
|---|---:|
| SC-1 total signal_events | 320 |
| SC-1 distinct signals with events | 26 |
| SC-2 false closure rate | 11.8841% |
| SC-4 total signals | 493 |
| KPI-R1 breakeven 7d | 20.4167% |
| KPI-R4 NULL leverage | 80.1217% |
| KPI-R5 FILLED MARKET with NULL filled_at | 0 |
| KPI-R3 duplicate discord_message_id groups | 14 |

## Verification Evidence

### 1. Round 2 code landed as described
**VERIFIED ✅**

- `oinkfarm` branch tip fetched to `b9086018`
- `oink-sync` branch tip at `dc35867`
- Diff shows the intended Round 2 changes:
  - normalization moved earlier in `scripts/micro-gate-v3.py`
  - two new end-to-end tests added in `tests/test_denomination_gate.py`
  - `oink_sync/resolver.py` docstring corrected

### 2. P1 blocker reproduction, now fixed
**VERIFIED ✅**

I re-ran the original failure path against the actual Round 2 code using the real `_process_signal()` flow with:
- `exchange_ticker='1000PEPEUSDT'`
- `mark_price=3.5e-06`
- extracted entry `0.0035`
- stop loss `0.003`
- TPs `0.004 / 0.005 / 0.006`

**Round 2 result:**
```python
{'action': 'inserted', 'signal_id': 1, 'ticker': 'PEPE', 'direction': 'LONG', 'entry_price': 3.5e-06, 'order_type': 'MARKET', 'status': 'ACTIVE', 'fill_status': 'FILLED'}
```

Stored row:
```python
(3.5e-06, 3e-06, 4e-06, 5e-06, 6e-06,
 '[A9: denomination_adjusted /1000 via 1000PEPEUSDT] [extracted: cornix_regex]')
```

Interpretation:
- entry normalized correctly
- SL normalized before B11
- TP1/TP2/TP3 normalized before TP safety logic
- prior `SL_DEVIATION` rejection no longer occurs

### 3. P2 blocker reproduction, now fixed
**VERIFIED ✅**

I re-ran the replay path against the same Round 2 code.

First pass:
```python
{'action': 'inserted', 'signal_id': 2, 'ticker': 'PEPE', 'direction': 'LONG', 'entry_price': 3.5e-06, 'order_type': 'MARKET', 'status': 'ACTIVE', 'fill_status': 'FILLED'}
```

Second pass with same `discord_message_id` and normalized entry path:
```python
{'action': 'skipped', 'reason': 'DUPLICATE: id=2', 'signal_id': 2}
```

Signal count for that replayed message:
```text
1
```

Interpretation:
- dedup now probes the canonical normalized `entry_price`
- the replayed-message double-insert path from Round 1 is closed

### 4. Actual ordering in live code
**VERIFIED ✅**

`micro-gate-v3.py` now reflects the safe ordering:
- §3b: normalize `entry_price`
- §4: snowflake dedup sees normalized entry
- §5: price deviation guard sees normalized entry
- §8a: normalize `stop_loss`
- §8b: B11 compares normalized SL vs normalized entry
- §9: normalize TP values before TP safety check
- §9b: append A9 notes

This matches the requested remediation for both GUARDIAN blockers.

### 5. FET #1159 reference case
**VERIFIED ✅**

| id | ticker | direction | entry_price | exit_price | leverage | final_roi | status | remaining_pct |
|---:|---|---|---:|---:|---|---:|---|---:|
| 1159 | FET | LONG | 0.2285 | 0.2285 | NULL | 3.37 | CLOSED_WIN | 100.0 |

Reference integrity remains intact.

## Test Evidence

### Local suites run
```bash
cd /home/oinkv/oinkfarm && python3 -m pytest tests/test_denomination_gate.py -q
cd /home/oinkv/oinkfarm && python3 -m pytest tests/test_denomination_gate.py tests/test_a7_update_detection.py tests/test_micro_gate_filled_at.py tests/test_a5_confidence.py tests/test_micro_gate_source_url.py -q
cd /home/oinkv/oink-sync && python3 -m pytest tests/test_denomination.py -q
```

### Results
- `oinkfarm/tests/test_denomination_gate.py`: **15 / 15 passed**
- related targeted `oinkfarm` suites: **59 / 59 passed**
- `oink-sync/tests/test_denomination.py`: **23 / 23 passed**

### Full-suite note
A raw `python3 -m pytest -q` in `oinkfarm` still trips **4 archived test collection errors** under `_archived/2026-03-14-housekeeping/` due to missing historical script paths and `scripts.scan_daemon` imports. These are pre-existing archive issues and not caused by A9.

## Issues Found

No blocking data issues remain in Round 2.

Residual note:
- This change still modifies hot-path ingest ordering, so continued post-deploy observation is prudent if merged, but I did not find a remaining data-safety blocker.

## What’s Done Well

- The P1 normalization-ordering defect is fixed in the live path, not just in isolated helper tests.
- The P2 dedup mismatch is fixed at the correct layer by aligning probe and stored values.
- Two end-to-end `_process_signal()` tests now cover the exact regressions that Round 1 missed.
- The solution preserves additive metadata design and avoids any migration risk.
- FET #1159 remains untouched.

## Delta Table

| Dimension | Round 1 | Round 2 | Delta | Notes |
|---|---:|---:|---:|---|
| Schema | 10 | 10 | 0 | Unchanged |
| Formula | 4 | 10 | +6 | P1 fixed and reproduced live |
| Migration | 10 | 10 | 0 | Unchanged |
| Performance | 9 | 9 | 0 | Unchanged |
| Regression | 4 | 9 | +5 | P2 fixed, e2e coverage added |
| **OVERALL** | **7.20** | **9.80** | **+2.60** | |

## Verdict

**PASS ✅**

- Overall score: **9.80 / 10**
- Threshold if treated as 🟡 STANDARD: **≥ 9.0**
- User labeled this as 🟢 LIGHTWEIGHT, which would normally place it outside GUARDIAN’s mandatory gate, but on requested re-review it passes GUARDIAN’s data-safety bar cleanly.

Round 1 blockers are resolved.

---

*🛡️ GUARDIAN — Data Safety / Formula Accuracy / Migration / Performance / Regression Review*