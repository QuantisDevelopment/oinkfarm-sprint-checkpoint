# 🛡️ GUARDIAN Canary Report — Task A3: Auto filled_at for MARKET Orders

| Field | Value |
|-------|-------|
| **Task** | A3 — Auto filled_at for MARKET orders |
| **Merge Commit** | `3b5453b7` (PR #125) |
| **Deployed** | 2026-04-18T22:06Z |
| **Canary Started** | 2026-04-18T22:08Z |
| **Report Date** | 2026-04-18T22:15Z |
| **Final Verdict Date** | 2026-04-20T22:06Z |

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

**Note:** Signal #2524 (PIEVERSE) has a high ID because it was inserted via WG reconciler (confirmed legitimate close for trader Tareeq). The `filled_at = posted_at` behavior is correct for this MARKET order.

---

### 48h Checkpoint — 2026-04-20T22:06Z (FINAL)

**Status: ✅ PASS** — 42 new live MARKET FILLED signals, ALL with `filled_at = posted_at`.

**Full live MARKET FILLED signals since deploy (id > 1607, posted after 2026-04-18T22:06Z):**

| ID | Ticker | posted_at | filled_at | Canary |
|----|--------|-----------|-----------|--------|
| 1608 | DEXE | 2026-04-19T07:08:05Z | 2026-04-19T07:08:05Z | ✅ |
| 1610 | VVV | 2026-04-19T11:54:49Z | 2026-04-19T11:54:49Z | ✅ |
| 1611 | BTC | 2026-04-19T14:27:52Z | 2026-04-19T14:27:52Z | ✅ |
| 2524 | PIEVERSE | 2026-04-19T19:11:01Z | 2026-04-19T19:11:01Z | ✅ |
| 2525 | PIEVERSE | 2026-04-19T22:23:57Z | 2026-04-19T22:23:57Z | ✅ |
| 2526 | EIGEN | 2026-04-19T22:26:47Z | 2026-04-19T22:26:47Z | ✅ |
| 2529 | PIEVERSE | 2026-04-20T10:01:23Z | 2026-04-20T10:01:23Z | ✅ |
| 2530 | HYPE | 2026-04-20T10:04:05Z | 2026-04-20T10:04:05Z | ✅ |
| 2531 | BTC | 2026-04-20T10:06:03Z | 2026-04-20T10:06:03Z | ✅ |
| 2532 | RAVE | 2026-04-20T10:10:31Z | 2026-04-20T10:10:31Z | ✅ |
| 2533 | EDGE | 2026-04-20T12:12:25Z | 2026-04-20T12:12:25Z | ✅ |
| 2534 | LZMH | 2026-04-20T12:36:57Z | 2026-04-20T12:36:57Z | ✅ |
| 2535 | PIPPIN | 2026-04-20T12:38:03Z | 2026-04-20T12:38:03Z | ✅ |
| 2536 | ENJ | 2026-04-20T12:43:58Z | 2026-04-20T12:43:58Z | ✅ |
| 2537 | CHILL | 2026-04-20T12:48:07Z | 2026-04-20T12:48:07Z | ✅ |
| 2538 | AERO | 2026-04-20T12:50:51Z | 2026-04-20T12:50:51Z | ✅ |
| 2539 | MON | 2026-04-20T12:53:44Z | 2026-04-20T12:53:44Z | ✅ |
| 2540 | BTC | 2026-04-20T13:05:35Z | 2026-04-20T13:05:35Z | ✅ |
| 2541 | WLDS | 2026-04-20T13:27:21Z | 2026-04-20T13:27:21Z | ✅ |
| 2542 | IRYS | 2026-04-20T13:28:59Z | 2026-04-20T13:28:59Z | ✅ |
| 2543 | CMND | 2026-04-20T13:45:25Z | 2026-04-20T13:45:25Z | ✅ |
| 2544 | LUNR | 2026-04-20T13:48:29Z | 2026-04-20T13:48:29Z | ✅ |
| 2545 | MOODENG | 2026-04-20T14:06:17Z | 2026-04-20T14:06:17Z | ✅ |
| 2546 | MON | 2026-04-20T14:19:25Z | 2026-04-20T14:19:25Z | ✅ |
| 2547 | NAORIS | 2026-04-20T15:02:47Z | 2026-04-20T15:02:47Z | ✅ |
| 2548 | HYPE | 2026-04-20T15:08:03Z | 2026-04-20T15:08:03Z | ✅ |
| 2549 | NBIS | 2026-04-20T15:21:30Z | 2026-04-20T15:21:30Z | ✅ |
| 2550 | EDGE | 2026-04-20T16:25:37Z | 2026-04-20T16:25:37Z | ✅ |
| 2551 | HIGH | 2026-04-20T16:33:55Z | 2026-04-20T16:33:55Z | ✅ |
| 2552 | HYPE | 2026-04-20T16:41:10Z | 2026-04-20T16:41:10Z | ✅ |
| 2553 | ETH | 2026-04-20T16:50:03Z | 2026-04-20T16:50:03Z | ✅ |
| 2554 | GUN | 2026-04-20T17:18:23Z | 2026-04-20T17:18:23Z | ✅ |
| 2555 | ZEC | 2026-04-20T17:45:51Z | 2026-04-20T17:45:51Z | ✅ |
| 2556 | PORTAL | 2026-04-20T17:45:54Z | 2026-04-20T17:45:54Z | ✅ |
| 2557 | LIT | 2026-04-20T18:03:10Z | 2026-04-20T18:03:10Z | ✅ |
| 2558 | APT | 2026-04-20T18:03:51Z | 2026-04-20T18:03:51Z | ✅ |
| 2559 | HYPE | 2026-04-20T18:17:33Z | 2026-04-20T18:17:33Z | ✅ |
| 2560 | ARM | 2026-04-20T19:05:02Z | 2026-04-20T19:05:02Z | ✅ |
| 2561 | ORDI | 2026-04-20T19:06:10Z | 2026-04-20T19:06:10Z | ✅ |
| 2562 | BSB | 2026-04-20T19:26:07Z | 2026-04-20T19:26:07Z | ✅ |
| 2563 | NAORIS | 2026-04-20T19:55:05Z | 2026-04-20T19:55:05Z | ✅ |
| 2564 | BNB | 2026-04-20T20:38:24Z | 2026-04-20T20:38:24Z | ✅ |

**MARKET canary: 42/42 correct** — 100% `filled_at = posted_at` match rate across all live MARKET FILLED signals.

**Mismatched filled_at investigation (3 records from aggregate count):**
All 3 are **historical records** from the DB merge (posted pre-deployment), NOT live ingestion:

| ID | Ticker | Origin | Explanation |
|----|--------|--------|-------------|
| 2047 | BTC | HISTORICAL (2026-03-28) | Timezone format mismatch (`+00:00` vs bare) — same timestamp, string comparison artifact |
| 2048 | BTC | HISTORICAL (2026-03-28) | Same timezone format mismatch as 2047 |
| 2359 | PEPE | HISTORICAL (2026-03-24) | `filled_at` is ~10min after `posted_at` — pre-existing historical data, not an A3 regression |

These are pre-existing historical artifacts from merged data, not A3 regressions. Zero live MARKET signals have mismatched `filled_at`.

---

## 4. 48h Metric Comparison (FINAL)

| Metric | Pre-Deploy (T0) | Post-Backfill (T+0h) | 24h (T+24h) | 48h (T+48h) | Delta (T0→T+48h) | Status |
|--------|-----------------|----------------------|-------------|-------------|-------------------|--------|
| SC-4 (Signal count) | 490 | 490 | 1,407 | 1,447 | +957 | ✅ Expected (DB merge + new signals) |
| SC-2 (False closures 30d) | 41/333 (12.3%) | 41/333 (12.3%) | 56/860 (6.5%) | 53/860 (6.16%) | −6.14pp | ✅ Improved (larger denominator) |
| KPI-R1 (Breakeven % 7d) | 22.86% | 22.86% | 19.17% | 15.57% (33/212) | −7.29pp | ✅ Improved trend |
| KPI-R4 (NULL leverage %) | 80.00% | 80.00% | 67.02% | 67.86% | −12.14pp | ✅ Improved (merged data) |
| KPI-R5 (NULL filled_at MARKET) | **8** | **0** | **0** | **0** | −8 | ✅ **Sustained fix — 48h clean** |
| NULL filled_at total (FILLED) | 17 | 9 | 68 | 68 | +51 | ℹ️ Historical LIMIT orders from merge |
| FET #1159 final_roi | 3.37 | 3.37 | 3.37 | 3.37 | 0 | ✅ Unchanged |
| KPI-R3 (Duplicate msg IDs) | — | — | 14 groups | 14 groups | — | ℹ️ Pre-existing historical |
| KPI-R6 (Ingestion rate) | — | — | — | 45 last 24h / 41.1 avg | — | ✅ Healthy (above average) |

### Notes on metric evolution (24h → 48h):

**SC-4 (1,407 → 1,447):** +40 new signals ingested in the second 24h window. Healthy ingestion rate continues.

**SC-2 (6.5% → 6.16%):** False closure rate continues to improve slightly as new clean closures enter the 30-day window.

**KPI-R1 (19.17% → 15.57%):** Breakeven proportion decreased further in the 7-day rolling window — normal variation, trending positively.

**KPI-R4 (67.02% → 67.86%):** Marginal increase (+0.84pp) — within normal variance as new signals with varying leverage data are ingested.

**KPI-R5: 0 for 48 consecutive hours.** The A3 fix is fully sustained.

---

## 5. Final Canary Verdict

| Check | Result |
|-------|--------|
| Backfill row count | ✅ 8/8 exact |
| Backfill correctness | ✅ 8/8 filled_at = posted_at |
| KPI-R5 regression | ✅ 8 → 0 → 0 → 0 (sustained 48h) |
| Live MARKET canary (42 signals) | ✅ 42/42 filled_at = posted_at |
| LIMIT order behavior | ✅ Correctly divergent (filled_at ≠ posted_at) |
| SC metrics | ✅ No regression (improvements from DB merge) |
| FET #1159 untouched | ✅ final_roi = 3.37 |
| Historical mismatch investigation | ✅ 3 records explained (pre-existing, not A3) |
| New regressions | ✅ None detected |
| Ingestion health | ✅ 45 signals/24h vs 41.1 avg — above average |

### 🟢 FINAL VERDICT: CANARY PASS

**The A3 auto-`filled_at` logic is confirmed working correctly in production after 48 hours of continuous monitoring.**

- **42 live MARKET FILLED signals** processed since deployment — **100% correct** (`filled_at = posted_at`)
- **KPI-R5 sustained at 0** for the full 48h canary window (down from 8 pre-deploy)
- **Zero regressions** detected in any monitored metric
- **Zero P0/P1/P2 alerts** generated during the canary period
- All metric shifts are fully attributed to the concurrent DB merge (Task 1.2) and are non-regressive

**A3 canary is now CLOSED. No further monitoring checkpoints required for this task.**

---

## 6. Checkpoint History

| Checkpoint | Time | Status | Live MARKET Signals | Details |
|------------|------|--------|---------------------|---------|
| T+0h (Backfill) | 2026-04-18T22:08Z | ✅ PASS | 0 (backfill only) | 8/8 backfilled correctly |
| T+24h | 2026-04-19T22:06Z | ✅ PASS | 4 | 4/4 correct |
| T+48h (FINAL) | 2026-04-20T22:06Z | ✅ PASS | 42 | 42/42 correct |

---

*🛡️ GUARDIAN — Post-Deploy Canary Protocol*
*Final report: 2026-04-20T22:06Z (48h checkpoint — CANARY CLOSED)*
*Initial report: 2026-04-18T22:15Z*
