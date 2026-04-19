# 🛡️ GUARDIAN Phase 1 Review — A8: Conditional SL Type Field

| Field | Value |
|---|---|
| Branch | `anvil/A8-conditional-sl-type` |
| Commits | `19f475db` (rebased review target; A8 payload functionally matches prior `a3eaa87e`) |
| Change Tier | 🟡 STANDARD |
| Review Round | Round 1 |
| Review Date | 2026-04-19 |
| PR | `oinkfarm #134` |

## Scope Note

I reviewed the rebased branch tip (`19f475db`) after ANVIL dropped the orphan pre-squash A11 history from the review target.
A11-owned files present in earlier dirty-state diffs are not scored against A8.

## Dimension Scores

| # | Dimension | Weight | Score | Notes |
|---|---|---:|---:|---|
| 1 | Schema Correctness | 25% | 10 | Additive-only schema change: `ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED'`. INSERT path updated to include `sl_type`, and placeholder count matches bound values count at 30/30. |
| 2 | Formula Accuracy | 25% | 10 | No financial hotpath mutation. `calculate_blended_pnl()`, `_check_sl_tp()`, `close_signal()`, and lifecycle ROI logic remain untouched. |
| 3 | Data Migration Safety | 20% | 9 | Migration is deploy-order safe and standalone-safe: DDL first, then targeted backfill, then Python deploy. Rollback via `ALTER TABLE ... DROP COLUMN` is viable on SQLite `3.46.1`. Minor deduction: migration file includes post-run verification comments, but no explicit pre-count/assertion query block. |
| 4 | Query Performance | 10% | 9 | No new indexes or hot-query scans. Runtime impact is limited to one extra inserted/updated metadata field and constant-time classification logic. |
| 5 | Regression Risk | 20% | 9 | `_ALLOWED_UPDATE_COLS` includes `sl_type`; `_process_update()` sets `sl_type='MANUAL'` only when SL actually changes, and B14 still prevents erroneous BE-by-number overwrites. Test coverage is strong, but not every test is full end-to-end through `_process_signal()` because backfill and constant checks are necessarily narrower. |
|  | **OVERALL** | 100% | **9.50** | |

**Weighted score:** `(10×0.25) + (10×0.25) + (9×0.20) + (9×0.10) + (9×0.20) = 9.50`

## Pre-Deploy Baseline Snapshot

| Metric | Current Value |
|---|---:|
| SC-1 total signal_events | 345 |
| SC-1 distinct signals with events | 27 |
| SC-2 false closure rate | 11.8841% |
| SC-4 total signals | 494 |
| KPI-R1 breakeven 7d | 20.4167% |
| KPI-R4 NULL leverage | 80.1619% |
| NULL `stop_loss` rows | 28 |
| Existing conditional-note rows | 0 |
| SQLite version | 3.46.1 |

## Verification Against Phase 0 Concerns

### 1. Deploy order: DDL first, then code deploy
**VERIFIED ✅**

`scripts/migrations/a8_sl_type.sql` is safe to run before Python deploy:
- adds nullable-compatible additive column with `DEFAULT 'FIXED'`
- existing code does not read `sl_type`
- backfill is targeted and bounded
- current production DB does **not** yet have `sl_type`, which is consistent with additive-first rollout

### 2. UPDATE path safety
**VERIFIED ✅**

In `scripts/micro-gate-v3.py`:
- `_ALLOWED_UPDATE_COLS` includes `sl_type`
- `_process_update()` sets `sl_type = 'MANUAL'` for both:
  - explicit `BE/BREAKEVEN/B/E`
  - numeric stop-loss change
- when B14 blocks an SL≈entry overwrite, `sl_type` is **not** set to `MANUAL`
- non-SL updates leave `sl_type` unchanged

### 3. Backfill safety and row targeting
**VERIFIED ✅ with minor documentation gap**

Migration logic:
```sql
ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED';
UPDATE signals SET sl_type = 'CONDITIONAL'
WHERE notes LIKE '%SL:CONDITIONAL%'
  AND sl_type = 'FIXED';
UPDATE signals SET sl_type = 'NONE'
WHERE stop_loss IS NULL
  AND notes NOT LIKE '%SL:CONDITIONAL%'
  AND sl_type = 'FIXED';
```

Live baseline at review time:
- `stop_loss IS NULL`: **28** rows
- `notes LIKE '%SL:CONDITIONAL%'`: **0** rows

This is appropriately narrow and non-destructive. Minor issue: the migration file includes verification comments for post-run checks, but not an explicit pre-count block or hard assertion comments before each UPDATE.

### 4. Rollback viability
**VERIFIED ✅**

Live SQLite version is `3.46.1`, so:
```sql
ALTER TABLE signals DROP COLUMN sl_type;
```
is viable if rollback is needed.

### 5. Test coverage
**VERIFIED ✅ with scope note**

Targeted local run on rebased tip:
- `tests/test_a8_sl_type.py`
- `tests/test_a5_confidence.py`
- `tests/test_a7_update_detection.py`
- `tests/test_micro_gate_filled_at.py`
- `tests/test_denomination_gate.py`
- `tests/test_micro_gate_source_url.py`

**Result:** `68 / 68 passed`

Coverage observations:
- INSERT and UPDATE classification tests go through real `process_one()` / `_process_signal()` paths with in-memory DBs
- backfill correctness test executes the actual migration SQL logic against an in-memory schema
- constant test verifies the shared keyword source exists and avoids keyword drift

So the important runtime paths are covered, though not literally every test is full end-to-end through `_process_signal()`.

### 6. INSERT column count / placeholder count
**VERIFIED ✅**

Post-A11+A8 INSERT path is now:
- **30 columns**
- **30 placeholders**
- **30 bound values**

This is also enforced by the updated `test_insert_column_placeholder_count_matches` assertion.

### 7. FET #1159 integrity
**VERIFIED ✅**

Live reference row remains unchanged by A8 scope:

| id | ticker | entry_price | stop_loss | final_roi | status |
|---:|---|---:|---:|---:|---|
| 1159 | FET | 0.2285 | 0.2285 | 3.37 | CLOSED_WIN |

A8 does not alter stop-loss storage for existing rows, ROI calculation, or downstream close behavior.

## Test Evidence

### A8-specific code present
**VERIFIED ✅**

`micro-gate-v3.py` contains:
- shared `_CONDITIONAL_SL_KEYWORDS`
- conditional note tagging reusing the shared constant
- `sl_type` classification block after SL processing
- INSERT writes `sl_type`
- UPDATE writes `sl_type='MANUAL'` only on actual SL change

### Targeted test run
```bash
pytest -q \
  /home/oinkv/.openclaw/workspace/tests/test_a8_sl_type.py \
  /home/oinkv/.openclaw/workspace/tests/test_a5_confidence.py \
  /home/oinkv/.openclaw/workspace/tests/test_a7_update_detection.py \
  /home/oinkv/.openclaw/workspace/tests/test_micro_gate_filled_at.py \
  /home/oinkv/.openclaw/workspace/tests/test_denomination_gate.py \
  /home/oinkv/.openclaw/workspace/tests/test_micro_gate_source_url.py
```

Result:
- **68 / 68 passed**

## Issues Found

| # | Severity | Dimension | Description | Evidence |
|---|---|---|---|---|
| 1 | P3 | Migration | Migration file lacks explicit pre-count/assertion block before backfill UPDATEs | `a8_sl_type.sql` includes only post-run verification comments |
| 2 | P3 | Regression | Not every supporting test is full `_process_signal()` end-to-end, though key runtime paths are covered | `test_sl_type_backfill_query` and constant test are narrower by design |

Neither issue is blocking.

## What’s Done Well

- Schema is additive and deploy-order safe.
- Shared keyword constant removes classification drift between note tagging and `sl_type` assignment.
- UPDATE-path handling is correctly constrained to true SL changes.
- B14 protection remains intact, which avoids semantic corruption on board replays.
- INSERT statement and test schemas were updated consistently for the new column.
- Runtime and migration blast radius are both low.

## Verdict

**PASS ✅**

- Overall score: **9.50 / 10**
- Threshold for 🟡 STANDARD: **≥ 9.0**

A8 passes GUARDIAN Phase 1. I found no blocking data-safety, migration, formula, or regression issue in the rebased review target.

---

*🛡️ GUARDIAN — Data Safety / Formula Accuracy / Migration / Performance / Regression Review*
