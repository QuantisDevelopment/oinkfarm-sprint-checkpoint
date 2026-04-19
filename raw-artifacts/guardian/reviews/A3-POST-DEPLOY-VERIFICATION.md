# 🛡️ GUARDIAN Post-Deploy Verification — Task A3

**Task:** A3 — Auto filled_at for MARKET Orders
**Deploy Time:** 2026-04-18T22:06Z (commit 3b5453b7, PR #125)
**Verified At:** 2026-04-18T22:08Z (immediate window)

---

## Backfill Verification: ✅ CONFIRMED

All 8 target rows independently verified:

| ID | Ticker | posted_at | filled_at | Match |
|----|--------|-----------|-----------|-------|
| 1599 | B3 | 2026-04-18T14:29:19.900157+00:00 | ✅ exact match | 1 |
| 1600 | LIGHT | 2026-04-18T17:31:21.928912+00:00 | ✅ exact match | 1 |
| 1601 | BTC | 2026-04-18T18:04:41.620285+00:00 | ✅ exact match | 1 |
| 1602 | PHA | 2026-04-18T18:08:06.958711+00:00 | ✅ exact match | 1 |
| 1603 | ALCH | 2026-04-18T18:24:49.155847+00:00 | ✅ exact match | 1 |
| 1604 | AVAX | 2026-04-18T19:03:03.683845+00:00 | ✅ exact match | 1 |
| 1606 | SOL | 2026-04-18T20:04:15.642490+00:00 | ✅ exact match | 1 |
| 1607 | ZEC | 2026-04-18T21:05:48.703761+00:00 | ✅ exact match | 1 |

**KPI-R5 (NULL filled_at MARKET):** 8 → **0** ✅

---

## Metric Comparison: Pre-Deploy vs Post-Deploy

| Metric | Pre-Deploy | Post-Deploy | Delta | Status |
|--------|-----------|-------------|-------|--------|
| SC-4 (Signal count) | 490 | 490 | 0 | ✅ |
| SC-2 (False closures 30d) | 41/333 | 41/333 | 0 | ✅ |
| KPI-R1 (Breakeven 7d) | 22.8571% | 22.8571% | 0 | ✅ |
| KPI-R4 (NULL leverage %) | 80.0% | 80.0% | 0 | ✅ |
| KPI-R5 (NULL filled_at MARKET) | 8 | **0** | **-8** | ✅ IMPROVED |
| Total NULL filled_at (FILLED) | 17 | **9** | **-8** | ✅ IMPROVED |
| FET #1159 final_roi | 3.37 | 3.37 | 0 | ✅ |

**All non-target metrics unchanged. Target metric (KPI-R5) improved exactly as predicted.**

---

## Canary Status: ⏳ PENDING

- Signals validated: **0**/10
- No new signals since deploy (id > 1607 is empty)
- Canary window: **OPEN** — monitoring next 10 MARKET order INSERTs
- 24h checkpoint: 2026-04-19T22:06Z
- 48h checkpoint: 2026-04-20T22:06Z

### Canary Criteria (per signal)
1. `filled_at IS NOT NULL` for MARKET orders
2. `filled_at = posted_at` for MARKET orders
3. `filled_at IS NULL` for LIMIT orders (behavior preserved)

---

## Known Pre-Existing Issues (Not Introduced by A3)

- **KPI-R3 (Duplicate discord_message_id):** 14 duplicate groups detected — pre-existing, not caused by A3
- **9 LIMIT/FILLED with NULL filled_at:** Tracked separately at `/home/oinkv/anvil-workspace/followups/LIMIT-FILLED-AT-NULLS.md`
- **FET #1159 ROI discrepancy:** `final_roi = 3.37` vs computed 0.0% — known blended PnL issue (A2 scope)

---

## Verdict: ✅ BACKFILL CLEAN — CANARY PENDING

- Backfill: **8/8 rows verified, exact match, zero collateral impact**
- Metrics: **All stable, target improved as expected**
- Canary: **Awaiting new MARKET signals** (will report at 24h checkpoint or when 10 signals collected, whichever comes first)

---

*🛡️ GUARDIAN — Post-Deploy Verification (Immediate Window)*
*Verified: 2026-04-18T22:08Z*
