# 🛡️ GUARDIAN Canary Report — Task A3: Auto filled_at for MARKET Orders

| Field | Value |
|-------|-------|
| **Task** | A3 — Auto filled_at for MARKET orders |
| **Merge Commit** | `3b5453b7` (PR #125) |
| **Deployed** | 2026-04-18T22:06Z |
| **Canary Started** | 2026-04-18T22:08Z |
| **Report Date** | 2026-04-18T22:15Z |

---

## 1. Backfill Execution

### Pre-Backfill Verification
- **Target rows:** 8 MARKET/FILLED signals with NULL `filled_at`
- **Target IDs:** 1599, 1600, 1601, 1602, 1603, 1604, 1606, 1607
- **Pre-backfill count confirmed:** 8 (exact match — no investigation needed)

### Backfill SQL Executed
```sql
UPDATE signals
SET filled_at = posted_at
WHERE order_type = 'MARKET'
  AND fill_status = 'FILLED'
  AND filled_at IS NULL;
```

### Result
- **Rows affected:** 8 ✅ (exact match to pre-backfill audit)

### Post-Backfill Verification
All 8 rows verified `filled_at = posted_at` (exact string match):

| ID | Ticker | posted_at | filled_at | Match |
|----|--------|-----------|-----------|-------|
| 1599 | B3 | 2026-04-18T14:29:19.900157+00:00 | 2026-04-18T14:29:19.900157+00:00 | ✅ |
| 1600 | LIGHT | 2026-04-18T17:31:21.928912+00:00 | 2026-04-18T17:31:21.928912+00:00 | ✅ |
| 1601 | BTC | 2026-04-18T18:04:41.620285+00:00 | 2026-04-18T18:04:41.620285+00:00 | ✅ |
| 1602 | PHA | 2026-04-18T18:08:06.958711+00:00 | 2026-04-18T18:08:06.958711+00:00 | ✅ |
| 1603 | ALCH | 2026-04-18T18:24:49.155847+00:00 | 2026-04-18T18:24:49.155847+00:00 | ✅ |
| 1604 | AVAX | 2026-04-18T19:03:03.683845+00:00 | 2026-04-18T19:03:03.683845+00:00 | ✅ |
| 1606 | SOL | 2026-04-18T20:04:15.642490+00:00 | 2026-04-18T20:04:15.642490+00:00 | ✅ |
| 1607 | ZEC | 2026-04-18T21:05:48.703761+00:00 | 2026-04-18T21:05:48.703761+00:00 | ✅ |

**Backfill verdict: ✅ PASS** — 8/8 rows correct.

---

## 2. Post-Deploy Metric Comparison

| Metric | Pre-Deploy Baseline | Post-Backfill Value | Delta | Status |
|--------|--------------------|--------------------|-------|--------|
| SC-4 (Signal count) | 490 | 490 | 0 | ✅ Unchanged |
| SC-2 (False closures 30d) | 41/333 (12.3%) | 41/333 (12.3%) | 0 | ✅ Unchanged |
| KPI-R1 (Breakeven % 7d) | 22.86% | 22.86% | 0 | ✅ Unchanged |
| KPI-R4 (NULL leverage %) | 80.00% | 80.00% | 0 | ✅ Unchanged |
| KPI-R5 (NULL filled_at MARKET) | **8** | **0** | **−8** | ✅ **Expected improvement** |
| NULL filled_at total (FILLED) | 17 | 9 | −8 | ✅ Expected (9 LIMIT remain) |
| Total filled_at set | 415 | 423 | +8 | ✅ Expected |
| FET #1159 final_roi | 3.37 | 3.37 | 0 | ✅ Unchanged |

**Metric verdict: ✅ PASS** — zero regression, KPI-R5 improved as expected.

---

## 3. Live Signal Canary (First 10 MARKET INSERTs)

### 24h Checkpoint — 2026-04-19T22:06Z

**Status: ✅ PASS** — 4 new MARKET FILLED signals, all with `filled_at = posted_at`.

**New signals since deploy (id > 1607, posted after 2026-04-18T22:06Z):**

| ID | Ticker | Order Type | Fill Status | posted_at | filled_at | Canary |
|----|--------|------------|-------------|-----------|-----------|--------|
| 1608 | DEXE | MARKET | FILLED | 2026-04-19T07:08:05Z | 2026-04-19T07:08:05Z | ✅ OK |
| 1609 | BTC | LIMIT | FILLED | 2026-04-19T08:00:32Z | 2026-04-19T17:51:36Z | — LIMIT (N/A) |
| 1610 | VVV | MARKET | FILLED | 2026-04-19T11:54:49Z | 2026-04-19T11:54:49Z | ✅ OK |
| 1611 | BTC | MARKET | FILLED | 2026-04-19T14:27:52Z | 2026-04-19T14:27:52Z | ✅ OK |
| 2524 | PIEVERSE | MARKET | FILLED | 2026-04-19T19:11:01Z | 2026-04-19T19:11:01Z | ✅ OK |

**MARKET canary: 4/4 correct** — All `filled_at = posted_at` (exact string match).
**LIMIT canary:** BTC #1609 correctly has `filled_at ≠ posted_at` (filled ~10h after posting — expected LIMIT behavior).
**Zero FAIL signals.** The auto-`filled_at` logic in oink-sync is working correctly for live ingestion.

**Note:** Signal #2524 (PIEVERSE) has a high ID because it was inserted via WG reconciler (confirmed legitimate close for trader Tareeq). The `filled_at = posted_at` behavior is correct for this MARKET order.

### Canary window status:
- ✅ **24h checkpoint: PASS** (4 MARKET signals, all clean)
- ⏳ **48h checkpoint (2026-04-20T22:06Z):** Scheduled — extended metric comparison

---

## 4. 24h Metric Comparison

| Metric | Pre-Deploy Baseline (T0) | Post-Backfill (T+0h) | 24h Checkpoint (T+24h) | Delta (T0→T+24h) | Status |
|--------|--------------------------|----------------------|----------------------|-------------------|--------|
| SC-4 (Signal count) | 490 | 490 | 1,407 | +917 | ✅ Expected (DB merge + new signals) |
| SC-2 (False closures 30d) | 41/333 (12.3%) | 41/333 (12.3%) | 56/860 (6.5%) | −5.8pp | ✅ Improved (larger denominator from merged data) |
| KPI-R1 (Breakeven % 7d) | 22.86% | 22.86% | 19.17% | −3.69pp | ✅ Within tolerance |
| KPI-R4 (NULL leverage %) | 80.00% | 80.00% | 67.02% | −12.98pp | ✅ Improved (merged signals have leverage data) |
| KPI-R5 (NULL filled_at MARKET) | **8** | **0** | **0** | −8 from baseline | ✅ **Sustained fix** |
| NULL filled_at total (FILLED) | 17 | 9 | 68 | +51 | ⚠️ See note below |
| Total filled_at set | 415 | 423 | 1,104 | +689 | ✅ Expected (merged data) |
| FET #1159 final_roi | 3.37 | 3.37 | 3.37 | 0 | ✅ Unchanged |
| KPI-R3 (Duplicate msg IDs) | — | — | 14 groups | — | ℹ️ Pre-existing (historical) |

### Notes on metric changes since initial baseline:

**SC-4 jump (490 → 1,407):** The signal count increased significantly because the DB merge (Task 1.2 / historical unification) has been deployed between the A3 deploy and this checkpoint, bringing in ~917 historical signals from the old database. This is expected and aligns with SC-4 target of 1,400+ signals — **now met** (1,407 ≥ 1,400).

**NULL filled_at total (9 → 68):** The increase is due to the merged historical signals from oinkfarm-old.db, which predominantly used LIMIT orders and had NULL `filled_at` values. This does NOT indicate A3 regression — KPI-R5 (MARKET-specific) remains at 0. The 68 NULL `filled_at` values are all LIMIT orders from historical data.

**KPI-R4 improvement (80% → 67%):** The merged historical data has better leverage coverage than the recent signals-only dataset, pulling the NULL leverage percentage down.

---

## 5. Canary Verdict (24h)

| Check | Result |
|-------|--------|
| Backfill row count | ✅ 8/8 exact |
| Backfill correctness | ✅ 8/8 filled_at = posted_at |
| KPI-R5 regression | ✅ 8 → 0 → 0 (sustained) |
| Live MARKET canary (4 signals) | ✅ 4/4 filled_at = posted_at |
| LIMIT order behavior | ✅ BTC #1609 correctly different |
| SC metrics | ✅ No regression (improvements from DB merge) |
| FET #1159 untouched | ✅ final_roi = 3.37 |
| New regressions | ✅ None detected |

### Verdict: ✅ CANARY PASS (24h)

The A3 auto-`filled_at` logic is working correctly in live production. 4 new MARKET FILLED signals have been processed since deployment — all with `filled_at = posted_at` as expected. No regressions detected in any monitored metric. The metric shifts between baselines are fully explained by the concurrent DB merge deployment (Task 1.2) and are non-regressive.

**No P0/P1/P2 alerts generated.** All metrics within expected ranges.

---

## 6. Scheduled Follow-Up

- ✅ **24h checkpoint (2026-04-19T22:06Z):** COMPLETE — PASS
- ⏳ **48h checkpoint (2026-04-20T22:06Z):** Scheduled — Final canary verdict with extended metric comparison
- **If any new MARKET signal has `filled_at IS NULL`:** Immediate P1 alert

---

*🛡️ GUARDIAN — Post-Deploy Canary Protocol*
*Report updated: 2026-04-19T22:06Z (24h checkpoint)*
*Initial report: 2026-04-18T22:15Z*
