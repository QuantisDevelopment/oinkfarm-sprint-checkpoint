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

**Status: PENDING** — No new signals ingested since deploy (22:06Z).

This is expected: deployment occurred late Saturday night (00:06 local / 22:06 UTC). Crypto signals typically resume during active trading hours.

**Canary windows:**
- **24h checkpoint (2026-04-19T22:06Z):** If <3 new MARKET signals → extend to 48h
- **48h checkpoint (2026-04-20T22:06Z):** If still <3 → report INCONCLUSIVE to Mike

**Monitoring query (to run at checkpoints):**
```sql
SELECT id, ticker, order_type, fill_status, posted_at, filled_at,
  CASE WHEN order_type='MARKET' AND filled_at IS NOT NULL AND filled_at = posted_at THEN 'OK'
       WHEN order_type='MARKET' AND (filled_at IS NULL OR filled_at != posted_at) THEN 'FAIL'
       WHEN order_type='LIMIT' AND filled_at IS NULL THEN 'OK_LIMIT'
       ELSE 'CHECK'
  END as canary_status
FROM signals WHERE id > 1607 ORDER BY id;
```

---

## 4. Canary Verdict (Initial)

| Check | Result |
|-------|--------|
| Backfill row count | ✅ 8/8 exact |
| Backfill correctness | ✅ 8/8 filled_at = posted_at |
| KPI-R5 regression | ✅ 8 → 0 (expected) |
| SC metrics unchanged | ✅ All stable |
| FET #1159 untouched | ✅ final_roi = 3.37 |
| Live signal canary | ⏳ PENDING (no traffic yet) |

### Verdict: ✅ BACKFILL PASS — ⏳ LIVE CANARY PENDING

The backfill component of Task A3 is fully verified and clean. The live-ingestion canary requires new MARKET signal traffic, which will be checked at the 24h and 48h windows.

**No P0/P1/P2 alerts generated.** All metrics within expected ranges.

---

## 5. Scheduled Follow-Up

- **24h checkpoint:** 2026-04-19T22:06Z — Run live canary query, compare SC/KPI metrics
- **48h checkpoint:** 2026-04-20T22:06Z — Final canary verdict, extended metric comparison
- **If any new MARKET signal has `filled_at IS NULL`:** Immediate P1 alert

---

*🛡️ GUARDIAN — Post-Deploy Canary Protocol*
*Report generated: 2026-04-18T22:15Z*
