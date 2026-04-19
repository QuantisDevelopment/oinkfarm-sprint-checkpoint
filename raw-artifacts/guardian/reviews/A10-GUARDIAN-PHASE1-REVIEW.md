# 🛡️ GUARDIAN Phase 1 Review — A10: Database Merge (Old + New)

| Field | Value |
|---|---|
| Branch | `anvil/A10-database-merge` |
| Commits | `50b23834` |
| Change Tier | 🔴 CRITICAL |
| Review Round | Round 2 |
| Review Date | 2026-04-19 |
| PR | `oinkfarm #135` |

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|---|---:|---:|---|
| 1 | Schema Correctness | 25% | 10 | Re-verified on fresh isolated replay. Imported rows land with `remaining_pct=100.0`, `sl_type` classified to `FIXED/NONE`, `leverage_source=NULL`, and FK remaps remain clean. Post-merge checks: 0 NULL `remaining_pct`, 0 NULL `sl_type`, 0 orphan traders, 0 orphan servers. |
| 2 | Formula Accuracy | 25% | 10 | No financial formula or PnL math changed. FET #1159 remains intact before and after replay: `sl_type=FIXED`, `remaining_pct=100.0`, `stop_loss=0.2285`, `final_roi=3.37`. |
| 3 | Data Migration Safety | 20% | 10 | Round 1 blocker is fixed. `len(import_errors) == 0` now participates in final validation, closing the silent-skip PASS path. Fresh replay on temp copy still imports 912 rows cleanly and the new tests explicitly fail validation on unmapped FK / unknown string server cases. |
| 4 | Query Performance | 10% | 9 | Single-run offline migration only. Current dataset replay remains efficient at this scale. No production hot-path query regression introduced. Minor deduction retained because validation/dedup still performs full-table work during the one-shot merge, which is acceptable but not unusually optimized. |
| 5 | Regression Risk | 20% | 9 | Risk materially reduced. Round 2 adds 27 focused tests covering dedup priority, FK remap, string server fixups, orphan trader placeholder, schema alignment, overlap resolution, stale override, validation semantics, and import-error fatality. Minor deduction remains because this is still a one-shot CRITICAL migration script, not a routine path. |
|  | **OVERALL** | 100% | **9.80** | |

**Weighted score:** `(10×0.25) + (10×0.25) + (10×0.20) + (9×0.10) + (9×0.20) = 9.80`

## Re-Review Scope

Round 2 touched GUARDIAN-owned dimensions directly, so I re-scored the affected dimensions rather than carrying forward Round 1 unchanged.

Re-verified areas:
- import-errors-as-fatal validation semantics
- stale signal `closed_at` runtime timestamp behavior
- readonly connection handling in `_connect()`
- automated coverage for the migration script
- fresh dry-run and live replay on an isolated production copy

## Pre-Deploy Baseline Snapshot

Production DB remains untouched at review time.

| Metric | Current Value |
|---|---:|
| SC-1 total signal_events | 356 |
| SC-1 distinct signals with events | 27 |
| SC-2 false closure rate | 11.8841% |
| SC-4 total signals | 494 |
| KPI-R3 duplicate discord_message_id groups | 14 |
| KPI-R4 NULL leverage | 80.1619% |
| KPI-R5 FILLED MARKET with NULL filled_at | 0 |

## Verification Evidence

### 1. Round 2 fixes are present in code
**VERIFIED ✅**

Diff from Round 1 (`81ba4463`) to Round 2 (`50b23834`) shows:
- `_connect()` now skips `PRAGMA journal_mode=WAL` for readonly connections
- stale override uses `_now_iso()` instead of hardcoded `2026-04-19T00:00:00Z`
- final validation now requires `len(import_errors) == 0`
- new `tests/test_a10_merge.py` added with 27 tests

### 2. Automated coverage now exists and runs cleanly
**VERIFIED ✅**

Executed:
```bash
cd /home/oinkv/oinkfarm && python3 -m pytest tests/test_a10_merge.py -q
```

Result:
- **27 / 27 passed**

Coverage includes the specific Round 1 concerns:
- `test_unknown_string_server_id_causes_error`
- `test_import_errors_fatal_on_unmapped_fk`
- `test_stale_closed_at_uses_runtime_timestamp`
- plus happy-path integration and FK/schema/overlap paths

### 3. Fresh isolated replay on temp production copy
**VERIFIED ✅**

I ran Round 2 script from commit `50b23834` against a fresh copy of production DB at `/tmp/oinkfarm-a10-r2-guardian-test.db`.

Commands executed:
```bash
python3 /tmp/a10_merge_databases_r2.py --old /home/m/data/oinkfarm-old.db --target /tmp/oinkfarm-a10-r2-guardian-test.db --dry-run --json-out /tmp/a10-r2-dryrun.json
python3 /tmp/a10_merge_databases_r2.py --old /home/m/data/oinkfarm-old.db --target /tmp/oinkfarm-a10-r2-guardian-test.db --json-out /tmp/a10-r2-live.json
```

Observed result:
- old DB rows: **1165**
- internal old-side dedup: **989 unique dmids**, **176 dropped duplicates**
- overlap: **77** shared dmids
- imported: **912**
- post-merge total: **1406 / 1406 expected**
- merge-introduced duplicate dmid groups: **0**
- orphan trader ids: **0**
- orphan server ids: **0**
- NULL `remaining_pct`: **0**
- NULL `sl_type`: **0**
- `CLOSED_MANUAL` count after replay: **8**

### 4. Production DB remains untouched pre-deploy
**VERIFIED ✅**

Current production checks:
- total signals: **494**
- tagged A10 imports: **0**
- NULL `remaining_pct`: **0**
- NULL `sl_type`: **0**
- orphan trader ids: **0**
- orphan server ids: **0**

This remains a review of merge safety, not authorization to execute production merge.

### 5. FET #1159 reference case
**VERIFIED ✅**

| id | ticker | sl_type | remaining_pct | stop_loss | final_roi |
|---:|---|---|---:|---:|---:|
| 1159 | FET | FIXED | 100.0 | 0.2285 | 3.37 |

Reference integrity remains intact.

## Issues Found

No blocking data issues remain in Round 2.

Residual note:
- This is still a one-shot CRITICAL production migration and should only run after Mike's explicit ship approval and with the verified backup/rollback path intact.

## What’s Done Well

- The Round 1 silent-skip validation hole is closed at the correct safety boundary.
- Test coverage is now real and directly exercises the previously unguarded failure modes.
- The readonly WAL bug was caught and fixed before production use.
- Fresh isolated replay reproduced the expected 912-row import cleanly.
- Production remains untouched pending approval, which is exactly the correct operating posture.

## Delta Table

| Dimension | Round 1 | Round 2 | Delta | Notes |
|---|---:|---:|---:|---|
| Schema | 10 | 10 | 0 | Unchanged, still correct |
| Formula | 10 | 10 | 0 | Unchanged, FET #1159 intact |
| Migration | 4 | 10 | +6 | Fatal import-error gate added |
| Performance | 9 | 9 | 0 | Unchanged |
| Regression | 6 | 9 | +3 | 27 tests added, readonly bug fixed |
| **OVERALL** | **7.90** | **9.80** | **+1.90** | |

## Verdict

**PASS ✅**
- Overall score: **9.80 / 10**
- 🔴 CRITICAL threshold: **≥ 9.5**
- A10 now clears GUARDIAN's production safety bar.

## Post-Deploy Validation Queries

When Mike gives explicit ship approval and the merge is executed, validate production with:

```sql
SELECT COUNT(*) FROM signals;  -- Expected: 1406
SELECT COUNT(*) FROM signals WHERE notes LIKE '%A10: imported%';  -- Expected: 912
SELECT COUNT(*) FROM signals WHERE remaining_pct IS NULL;  -- Expected: 0
SELECT COUNT(*) FROM signals WHERE sl_type IS NULL;  -- Expected: 0
SELECT COUNT(*) FROM signals WHERE trader_id NOT IN (SELECT id FROM traders);  -- Expected: 0
SELECT COUNT(*) FROM signals WHERE server_id NOT IN (SELECT id FROM servers);  -- Expected: 0
```

---
*🛡️ GUARDIAN — Data Safety / Formula Accuracy / Migration / Performance / Regression Review*