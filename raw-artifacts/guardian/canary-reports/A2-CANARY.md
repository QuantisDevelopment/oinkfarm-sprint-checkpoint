# 🛡️ A2 Canary Report — remaining_pct Model + Partial-Close PnL Accuracy

| Field | Value |
|-------|-------|
| **Task** | A2: remaining_pct Model + Partial-Close PnL Accuracy |
| **PR** | oink-sync #5 |
| **Merge Commit** | `6b21a2074413395b400b6f95494ae80d77ecef59` |
| **Deploy Time** | 2026-04-19T00:37:03Z (merge) / 2026-04-19T00:39:53Z (service restart) |
| **Canary Initiated** | 2026-04-19T00:41Z |
| **Canary Status** | ✅ PASS — FINAL VERDICT |
| **Final Verdict Issued** | 2026-04-21T00:40Z (T+48h) |

---

## Canary Criteria (5 checks from Phase 1 review §Canary Focus)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Schema activation — `remaining_pct` in PRAGMA table_info | ✅ PASS | Column 49, REAL, DEFAULT 100.0 confirmed |
| 2 | Legacy preservation — FET #1159 `final_roi = 3.37` | ✅ PASS | `remaining_pct = 100.0` (backfilled by ALTER), `final_roi = 3.37` unchanged at T+48h |
| 3 | First natural TP-hit — `remaining_pct` decrements + event payload enriched | ✅ PASS | 10 TP_HIT events observed with enriched payloads (close_pct, remaining_pct, alloc_source) |
| 4 | Gap-past-multiple-TP — sequential remaining_pct stepping | ✅ PASS | 3 multi-TP sequences validated: `#1564 LZM` (TP1→TP2→SL close), `#1462 MWH` (TP1→TP2→SL close), `#1602 PHA` (TP2→TP3 sequence) |
| 5 | Baselines — SC-2, KPI-R1, KPI-R4 stable post-deploy | ✅ PASS | All metrics stable; shifts attributable to A10 merge denominator change, not A2 |

---

## FINAL VERDICT: ✅ PASS (10/10 clean)

### Decisive evidence at T+48h:
1. **Blended PnL path naturally exercised and validated.** 3 signals completed the full cycle: TP_HIT → remaining_pct < 100 → final closure with blended PnL. All 3 computed ROIs match DB values within rounding tolerance (max deviation: 0.0047pp). This was the open caveat at T+24h — now resolved.
2. **10 natural TP_HIT events** processed with fully enriched payloads — 2.5× the volume seen at T+24h.
3. **Zero A2-attributable baseline regression** across the full 48h window.
4. **FET #1159 remains at 3.37** — legacy data integrity preserved.

---

## T+48h Baseline Comparison

| Metric | Pre-Deploy | T+24h | T+48h | Delta (pre→48h) | A2-Attributable? | Status |
|--------|-----------|-------|-------|-----------------|------------------|--------|
| SC-2 (False closure %) | 12.24% | 6.28% | 6.17% | -6.07pp | ❌ A10 denominator | ✅ No regression |
| SC-4 (Signal count) | 490 | 1409 | 1447 | +957 | ❌ A10 merge + new signals | ✅ Expected |
| KPI-R1 (Breakeven %) | 21.79% | 18.43% | 15.08% | -6.71pp | ❌ A10 denominator + normal churn | ✅ No regression |
| KPI-R4 (NULL leverage %) | 80.0% | 67.07% | 67.86% | -12.14pp | ❌ A10 merged data | ✅ No regression |
| FET #1159 final_roi | 3.37 | 3.37 | 3.37 | 0 | N/A | ✅ Unchanged |
| FET #1159 remaining_pct | 100.0 | 100.0 | 100.0 | 0 | N/A | ✅ Preserved |

### A2-Isolated Metric Assessment

T+~4h window (pre-A10 merge) remains the cleanest A2 isolation point:

| Metric | Pre-Deploy | T+~4h | Delta | Verdict |
|--------|-----------|--------|-------|---------|
| SC-2 | 12.24% | 12.09% | -0.15pp | ✅ Stable (noise) |
| KPI-R1 | 21.79% | 20.76% | -1.03pp | ✅ Stable (noise) |
| KPI-R4 | 80.0% | 80.0% | 0 | ✅ Unchanged |
| SC-4 | 490 | 490 | 0 | ✅ Unchanged |

---

## Blended PnL Validation — A2 Core Feature (NEW at T+48h)

### 3 signals closed with remaining_pct < 100 — blended PnL path fully exercised

#### Signal #1564 LZM (LONG) — TP1 → TP2 → SL close

| Step | Event | close_pct | remaining_pct | Exit Price | ROI at Exit |
|------|-------|-----------|---------------|------------|-------------|
| 1 | TP1 hit (09:41Z) | 50.0% | 50.0 | 5.7 | 5.5556% |
| 2 | TP2 hit (12:24Z) | 25.0% | 25.0 | 6.0 | 11.1111% |
| 3 | SL hit (13:24Z) | 25.0% (final) | 0 | 5.7 | 5.5556% |

**Blended ROI** = (0.50 × 5.5556) + (0.25 × 11.1111) + (0.25 × 5.5556) = **6.9444%**
**DB final_roi** = **6.94** → ✅ Match (Δ = 0.0044pp)

#### Signal #1561 BTC (SHORT) — TP2 → SL close (TP1 was pre-A2)

| Step | Event | close_pct | remaining_pct | Exit Price | ROI at Exit |
|------|-------|-----------|---------------|------------|-------------|
| 1 | TP1 hit (pre-A2) | N/A | N/A | 75739.4 | Not event-sourced |
| 2 | TP2 hit (07:23Z) | 50.0% | 50.0 | 74939.0 | 2.3204% |
| 3 | SL hit (17:19Z) | 50.0% (final) | 0 | 75739.4 | 1.2771% |

**Blended ROI** = (0.50 × 2.3204) + (0.50 × 1.2771) = **1.7988%**
**DB final_roi** = **1.8** → ✅ Match (Δ = 0.0012pp)

*Note: TP1 was pre-A2 and not event-sourced. A2 correctly used "assumed" allocation for TP2, treating the remaining 100% → 50% transition. The blended PnL is based only on event-sourced TP2 and final SL close.*

#### Signal #1462 MWH (LONG) — TP1 → TP2 → SL close

| Step | Event | close_pct | remaining_pct | Exit Price | ROI at Exit |
|------|-------|-----------|---------------|------------|-------------|
| 1 | TP1 hit (18:14Z) | 50.0% | 50.0 | 35.0 | 2.3392% |
| 2 | TP2 hit (20:17Z) | 25.0% | 25.0 | 35.5 | 3.8012% |
| 3 | SL hit (21:03Z) | 25.0% (final) | 0 | 35.0 | 2.3392% |

**Blended ROI** = (0.50 × 2.3392) + (0.25 × 3.8012) + (0.25 × 2.3392) = **2.7047%**
**DB final_roi** = **2.7** → ✅ Match (Δ = 0.0047pp)

### Blended PnL Summary

| Signal | Computed ROI | DB final_roi | Delta | Verdict |
|--------|-------------|-------------|-------|---------|
| #1564 LZM (LONG) | 6.9444% | 6.94 | 0.0044pp | ✅ |
| #1561 BTC (SHORT) | 1.7988% | 1.8 | 0.0012pp | ✅ |
| #1462 MWH (LONG) | 2.7047% | 2.7 | 0.0047pp | ✅ |

All deviations are within rounding precision (< 0.005pp). **Blended PnL calculation is mathematically correct.**

---

## Post-Deploy TP_HIT Event Validation (T+48h: 10 events)

| # | Event ID | Signal | Ticker | TP Level | close_pct | remaining_pct | alloc_source | Timestamp (UTC) |
|---|----------|--------|--------|----------|-----------|---------------|--------------|-----------------|
| 1 | 47 | #1602 | PHA | TP2 | 25.0 | 75.0 | assumed | 2026-04-19T02:34:50Z |
| 2 | 87 | #1602 | PHA | TP3 | 25.0 | 50.0 | assumed | 2026-04-19T03:53:49Z |
| 3 | 181 | #1561 | BTC | TP2 | 50.0 | 50.0 | assumed | 2026-04-19T07:23:26Z |
| 4 | 477 | #1604 | AVAX | TP1 | 50.0 | 50.0 | assumed | 2026-04-19T21:54:54Z |
| 5 | 768 | #1564 | LZM | TP1 | 50.0 | 50.0 | assumed | 2026-04-20T09:41:20Z |
| 6 | 825 | #1564 | LZM | TP2 | 25.0 | 25.0 | assumed | 2026-04-20T12:24:07Z |
| 7 | 880 | #2544 | LUNR | TP2 | 25.0 | 75.0 | assumed | 2026-04-20T14:02:32Z |
| 8 | 960 | #1462 | MWH | TP1 | 50.0 | 50.0 | assumed | 2026-04-20T18:14:35Z |
| 9 | 1009 | #1462 | MWH | TP2 | 25.0 | 25.0 | assumed | 2026-04-20T20:17:34Z |
| 10 | 1041 | #2560 | ARM | TP1 | 50.0 | 50.0 | assumed | 2026-04-20T21:47:20Z |

**10/10 events contain enriched payloads** with `close_pct`, `remaining_pct`, and `alloc_source`. All `alloc_source` = "assumed" (no explicit allocation from raw_text — expected behavior).

### Signal coverage:
- **6 unique signals** processed TP_HIT events
- **3 multi-TP sequences** completed (LZM, MWH full TP1→TP2→close; PHA TP2→TP3)
- **1 cross-boundary signal** (BTC #1561: TP1 pre-A2, TP2 post-A2)
- **2 single-TP signals** still active (LUNR, ARM)

---

## Post-Deploy Closure Analysis (32 closures in 48h)

| Category | Count | Details |
|----------|-------|---------|
| SL closures (remaining_pct=100) | 22 | Standard SL hits, no TP exits — A2 pass-through |
| TP closures (remaining_pct=100) | 4 | #875 BTC, #1403 ALB, #2558 APT, #2554 GUN — full position closes at TP |
| **Blended PnL closures (remaining_pct<100)** | **3** | **#1564 LZM (25%), #1561 BTC (50%), #1462 MWH (25%) — ALL VALIDATED ✅** |
| Pilot closures | 2 | #2533 EDGE, #2561 ORDI — breakeven/manual |
| WG alert closures | 1 | #2529 PIEVERSE — external closure |

### Key observations:
- **All 32 closures processed cleanly** — no errors, no unexpected status transitions
- **3 blended PnL closures** (the T+24h open caveat) — all mathematically verified ✅
- **SL trailing** worked correctly on multi-TP signals (SL moved to TP level on TP hit)
- **remaining_pct tracking** consistent across all closures: 100.0 for no-TP, <100 for partial exits

---

## Additional KPI Checks at T+48h

| KPI | T+24h | T+48h | Status | Notes |
|-----|-------|-------|--------|-------|
| KPI-R2 (Direction/SL consistency) | 4 pre-existing | 0 | ✅ Improved | All 4 trailing-stop signals from T+24h have now closed. No new inconsistencies. |
| KPI-R3 (Duplicate discord_message_id) | 14 groups | 14 groups | ⚠️ Pre-existing (A10) | A10 merge artifact. Not A2-related. |
| KPI-R5 (NULL filled_at for FILLED MARKET) | 0 | 0 | ✅ Clean | No regression |
| KPI-R6 (Ingestion rate) | — | 45 (24h) vs 37.9 avg | ✅ Normal | Above average — healthy pipeline |

---

## Event Store Health (T+48h)

| Event Type | Count (post-A2) | Assessment |
|------------|-----------------|------------|
| PRICE_ALERT | 962 | ✅ Normal operational volume |
| SIGNAL_CREATED | 45 | ✅ Healthy ingestion |
| TRADE_CLOSED_SL | 22 | ✅ Matches SL closures |
| UPDATE_DETECTED | 17 | ✅ Signal update processing |
| SL_MODIFIED | 11 | ✅ SL trailing on TP hits + manual |
| TP_HIT | 10 | ✅ A2 core feature — enriched payloads |
| TRADE_CLOSED_TP | 7 | ✅ TP-based closures |
| STATUS_CHANGED | 5 | ✅ PARTIALLY_CLOSED transitions |
| GHOST_CLOSURE | 2 | ⚠️ Worth monitoring (not A2-related) |
| TRADE_CLOSED_MANUAL | 2 | ✅ Pilot closures |
| LIMIT_EXPIRED | 1 | ✅ Normal |
| ORDER_FILLED | 1 | ✅ Normal |
| **Total** | **1085** | ✅ Healthy event generation (1.9× T+24h volume) |

---

## Signal Status Distribution at T+48h

| Status | T+24h | T+48h | Delta | Notes |
|--------|-------|-------|-------|-------|
| CLOSED_WIN | 471 | 479 | +8 | Normal closure flow |
| CLOSED_LOSS | 467 | 478 | +11 | Normal closure flow |
| CANCELLED | 221 | 221 | 0 | Stable |
| CLOSED_BREAKEVEN | 154 | 156 | +2 | Normal |
| ACTIVE | 75 | 89 | +14 | New signals ingested |
| PENDING | 10 | 12 | +2 | Normal |
| CLOSED_MANUAL | 8 | 8 | 0 | Stable |
| **PARTIALLY_CLOSED** | **3** | **4** | **+1** | **ARM #2560 entered PARTIALLY_CLOSED (TP1 hit)** |
| **Total** | **1409** | **1447** | **+38** | Healthy growth |

---

## Monitoring Schedule

| Checkpoint | Time (UTC) | What | Status |
|------------|-----------|------|--------|
| **T+1h18m** | 2026-04-19T01:57Z | First post-restart closure reviewed, baselines refreshed | ✅ Complete |
| **T+~4h** | 2026-04-19T02:40Z | Natural TP_HIT validated on `#1602 PHA`, FET #1159 unchanged | ✅ Complete |
| **T+24h** | 2026-04-20T00:40Z | Full SC/KPI comparison, 4 TP_HIT events validated, A10 overlap documented | ✅ Complete |
| **T+48h** | 2026-04-21T00:40Z | **FINAL: 10 TP_HITs, 3 blended PnL closures validated, PASS verdict** | ✅ **COMPLETE** |

---

## Final Verdict

### ✅ PASS — 10/10 Clean

**A2 (remaining_pct model + partial-close PnL accuracy) has passed all canary criteria with full evidence.**

### Evidence summary:
| # | Criterion | Result | Key Evidence |
|---|-----------|--------|--------------|
| 1 | Schema activation | ✅ | `remaining_pct` column active, DEFAULT 100.0, no NULLs |
| 2 | Legacy preservation | ✅ | FET #1159 = 3.37, unchanged across 48h |
| 3 | TP_HIT payload enrichment | ✅ | 10/10 events with close_pct, remaining_pct, alloc_source |
| 4 | Sequential TP stepping | ✅ | 3 multi-TP sequences validated (LZM, MWH, PHA) |
| 5 | Baseline stability | ✅ | Zero A2-attributable regression across all SC/KPI metrics |
| 6 | Blended PnL accuracy | ✅ | 3 closures with remaining_pct < 100 — all within 0.005pp of computed ROI |
| 7 | Cross-boundary handling | ✅ | BTC #1561 (pre-A2 TP1, post-A2 TP2) handled correctly |
| 8 | SL trailing after TP | ✅ | SL_MODIFIED events emitted on TP hits, SL moved to expected levels |
| 9 | PARTIALLY_CLOSED status | ✅ | 4 signals currently in PARTIALLY_CLOSED — status transitions clean |
| 10 | Event store integrity | ✅ | 1085 events, all types accounted for, no orphaned events |

### Resolved caveats:
- **T+24h open item:** "Blended PnL closure path not yet naturally exercised" → **RESOLVED.** 3 signals completed the full TP → partial-close → final-close cycle with mathematically verified blended PnL.

### Outstanding items (NOT blocking PASS):
- **KPI-R3 duplicate discord_message_ids** (14 groups, 147+ signals) — A10 merge artifact, tracked under A10 canary
- **GHOST_CLOSURE events** (2 occurrences) — worth monitoring in daily checks, not A2-related

---

*🛡️ GUARDIAN — A2 Canary Protocol*
*Final verdict issued: 2026-04-21T00:40Z (T+48h)*
*Canary CLOSED — no further checkpoints scheduled for A2*
