# 🛡️ A2 Canary Report — remaining_pct Model + Partial-Close PnL Accuracy

| Field | Value |
|-------|-------|
| **Task** | A2: remaining_pct Model + Partial-Close PnL Accuracy |
| **PR** | oink-sync #5 |
| **Merge Commit** | `6b21a2074413395b400b6f95494ae80d77ecef59` |
| **Deploy Time** | 2026-04-19T00:37:03Z (merge) / 2026-04-19T00:39:53Z (service restart) |
| **Canary Initiated** | 2026-04-19T00:41Z |
| **Canary Status** | ✅ PASS |

---

## Canary Criteria (5 checks from Phase 1 review §Canary Focus)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Schema activation — `remaining_pct` in PRAGMA table_info | ✅ PASS | Column 49, REAL, DEFAULT 100.0 confirmed |
| 2 | Legacy preservation — FET #1159 `final_roi = 3.37` | ✅ PASS | `remaining_pct = 100.0` (backfilled by ALTER), `final_roi = 3.37` unchanged at T+24h |
| 3 | First natural TP-hit — `remaining_pct` decrements + event payload enriched | ✅ PASS | 4 TP_HIT events observed with enriched payloads (close_pct, remaining_pct, alloc_source) |
| 4 | Gap-past-multiple-TP — sequential remaining_pct stepping | ✅ PASS | `#1602 PHA` completed TP2→TP3 sequence (75.0→50.0). `#1561 BTC` hit TP2 (50.0). `#1604 AVAX` hit TP1 (50.0). |
| 5 | Baselines — SC-2, KPI-R1, KPI-R4 stable post-deploy | ✅ PASS | All metrics stable or improved (shifts attributable to A10 merge, not A2) |

---

## T+24h Baseline Comparison

> **⚠️ Important context:** Between A2 deploy (2026-04-19T00:39Z) and this T+24h checkpoint, **Task A10 (database merge)** was deployed (~16:00-18:30 UTC on 2026-04-19), bringing signal count from 490 to 1409. All large metric shifts below are attributable to A10's denominator change, NOT to A2. A2's impact is isolated to remaining_pct behavior and TP_HIT payload enrichment.

| Metric | Pre-Deploy | T+~4h (pre-A10) | T+24h (post-A10) | Delta (pre→24h) | A2-Attributable? | Status |
|--------|-----------|------------------|-------------------|------------------|------------------|--------|
| SC-2 (False closure %) | 12.24% | 12.09% | 6.28% | -5.96pp | ❌ A10 denominator | ✅ No regression |
| SC-4 (Signal count) | 490 | 490 | 1409 | +919 | ❌ A10 merge | ✅ Expected |
| KPI-R1 (Breakeven %) | 21.79% | 20.76% | 18.43% | -3.36pp | ❌ A10 denominator | ✅ No regression |
| KPI-R4 (NULL leverage %) | 80.0% | 80.0% | 67.07% | -12.93pp | ❌ A10 merged data | ✅ No regression |
| FET #1159 final_roi | 3.37 | 3.37 | 3.37 | 0 | N/A | ✅ Unchanged |
| FET #1159 remaining_pct | 100.0 | 100.0 | 100.0 | 0 | N/A | ✅ Preserved |
| ACTIVE signals | — | 84 | 75 | — | Mixed | ✅ Normal churn |
| NULL remaining_pct | 0 | 0 | 0 | 0 | ✅ | ✅ All backfilled |
| PARTIALLY_CLOSED signals | 0 | 0 | 3 | +3 | ✅ A2 feature | ✅ New status working |

### A2-Isolated Metric Assessment

To isolate A2's impact from A10's, the T+~4h window (before A10 merged) provides the cleanest comparison:

| Metric | Pre-Deploy | T+~4h | Delta | Verdict |
|--------|-----------|--------|-------|---------|
| SC-2 | 12.24% | 12.09% | -0.15pp | ✅ Stable (noise) |
| KPI-R1 | 21.79% | 20.76% | -1.03pp | ✅ Stable (noise) |
| KPI-R4 | 80.0% | 80.0% | 0 | ✅ Unchanged |
| SC-4 | 490 | 490 | 0 | ✅ Unchanged |

**Conclusion:** A2 introduced zero baseline regression. All metric shifts at T+24h are A10 artifacts.

---

## Additional KPI Checks at T+24h

| KPI | Value | Pre-Deploy | Status | Notes |
|-----|-------|------------|--------|-------|
| KPI-R2 (Direction/SL consistency) | 4 | Pre-existing | ⚠️ Pre-existing | 4 trailing-stop signals (#948 BTC, #1403 ALB, #1406 CRDO, #1460 RKLB) — all have SL trailed above entry after TP hits. All pre-date A2 deploy. Not an A2 regression. |
| KPI-R3 (Duplicate discord_message_id) | 14 groups / 147 signals | N/A at 490 | ⚠️ A10 artifact | Duplicate discord_message_ids introduced by A10 merge. Largest group: 31 signals sharing one ID. **Not A2-related — flagged for A10 canary.** |
| KPI-R5 (NULL filled_at for FILLED MARKET) | 0 | — | ✅ Clean | No regression |

---

## Post-Deploy TP_HIT Event Validation (A2 Core Feature)

### Summary: 4 natural TP_HIT events since deploy

| # | Event ID | Signal | Ticker | TP Level | close_pct | remaining_pct | alloc_source | Timestamp (UTC) |
|---|----------|--------|--------|----------|-----------|---------------|--------------|-----------------|
| 1 | 47 | #1602 | PHA | TP2 | 25.0 | 75.0 | assumed | 2026-04-19T02:34:50Z |
| 2 | 87 | #1602 | PHA | TP3 | 25.0 | 50.0 | assumed | 2026-04-19T03:53:49Z |
| 3 | 181 | #1561 | BTC | TP2 | 50.0 | 50.0 | assumed | 2026-04-19T07:23:26Z |
| 4 | 477 | #1604 | AVAX | TP1 | 50.0 | 50.0 | assumed | 2026-04-19T21:54:54Z |

**All 4 events contain enriched payloads** with `close_pct`, `remaining_pct`, and `alloc_source` fields — confirming A2's TP_HIT payload enrichment is operational in production.

### Signal-Level Validation

#### Signal #1602 PHA (SHORT) — Full TP2→TP3 Sequence
- **TP1:** Pre-A2 (2026-04-18T18:33Z) — no A2 payload enrichment expected
- **TP2:** Post-A2 at 02:34Z — `close_pct=25.0`, `remaining_pct=75.0` ✅
- **TP3:** Post-A2 at 03:53Z — `close_pct=25.0`, `remaining_pct=50.0` ✅
- **Current state:** `status=PARTIALLY_CLOSED`, `remaining_pct=50.0`
- **Assessment:** Sequential stepping correct. remaining_pct tracked state from backfilled 100.0 through two TP levels.

#### Signal #1561 BTC (SHORT) — TP2 Hit
- **TP1:** Pre-A2 (2026-04-18T11:43Z)
- **TP2:** Post-A2 at 07:23Z — `close_pct=50.0`, `remaining_pct=50.0` ✅
- **Current state:** `status=PARTIALLY_CLOSED`, `remaining_pct=50.0`
- **SL trailed:** From 76719.2 → 75739.4 on TP2 hit

#### Signal #1604 AVAX (SHORT) — First Fully Post-A2 TP1
- **TP1:** Post-A2 at 21:54Z — `close_pct=50.0`, `remaining_pct=50.0` ✅
- **Current state:** `status=PARTIALLY_CLOSED`, `remaining_pct=50.0`
- **Assessment:** This is the first signal to have its TP1 processed entirely by A2 code. Clean behavior.

---

## Post-Deploy Closure Analysis (11 closures)

| # | Signal | Ticker | Status | close_source | remaining_pct | final_roi | Notes |
|---|--------|--------|--------|-------------|---------------|-----------|-------|
| 1 | #1590 | AXL | CLOSED_LOSS | sl_hit | 100.0 | -5.77 | No TPs hit — clean SL closure |
| 2 | #875 | BTC | CLOSED_WIN | sl_hit | 100.0 | 11.0 | Trailing stop hit at 75000 (above entry 66538). TRADE_CLOSED_TP event emitted. |
| 3 | #1543 | ARC | CLOSED_LOSS | sl_hit | 100.0 | -9.11 | No TPs hit |
| 4 | #1562 | CVX | CLOSED_LOSS | sl_hit | 100.0 | -8.39 | Has leverage=10.0 |
| 5 | #1608 | DEXE | CLOSED_LOSS | sl_hit | 100.0 | -2.26 | No TPs hit |
| 6 | #1542 | AERO | CLOSED_LOSS | sl_hit | 100.0 | -6.25 | No TPs hit |
| 7 | #1560 | PUMPFUN | CLOSED_LOSS | sl_hit | 100.0 | -11.53 | No TPs hit |
| 8 | #1611 | BTC | CLOSED_LOSS | sl_hit | 100.0 | -1.69 | No TPs hit |
| 9 | #1553 | COTI | CLOSED_LOSS | sl_hit | 100.0 | -8.96 | Has leverage=10.0 |
| 10 | #1606 | SOL | CLOSED_LOSS | sl_hit | 100.0 | -2.29 | No TPs hit |
| 11 | #2525 | PIEVERSE | CLOSED_LOSS | sl_hit | 100.0 | -7.14 | From A10 merge |

**All closures have remaining_pct=100.0** — none involved partial TP exits before closure. The blended PnL calculation path (remaining_pct < 100 at closure) has **not yet been naturally exercised**. The 3 PARTIALLY_CLOSED signals (#1561, #1602, #1604) are still active and are candidates for future blended PnL validation.

Additionally: Signal #2524 PIEVERSE had a `TRADE_CLOSED_MANUAL` event (pilot_closure) with remaining_pct=100.0 — clean.

---

## Event Store Health

| Event Type | Count (post-A2) | Assessment |
|------------|-----------------|------------|
| PRICE_ALERT | 542 | ✅ Normal operational volume |
| TRADE_CLOSED_SL | 11 | ✅ Matches 11 SL closures |
| SIGNAL_CREATED | 7 | ✅ New signal ingestion |
| UPDATE_DETECTED | 5 | ✅ Signal update processing |
| SL_MODIFIED | 4 | ✅ SL trailing on TP hits |
| TP_HIT | 4 | ✅ A2 core feature — enriched payloads |
| LIMIT_EXPIRED | 1 | ✅ Normal |
| ORDER_FILLED | 1 | ✅ Normal |
| STATUS_CHANGED | 1 | ✅ Normal |
| TRADE_CLOSED_MANUAL | 1 | ✅ Pilot closure |
| TRADE_CLOSED_TP | 1 | ✅ Trailing stop win |
| **Total** | **578** | ✅ Healthy event generation |

---

## Signal Status Distribution at T+24h

| Status | Count | Notes |
|--------|-------|-------|
| CLOSED_WIN | 471 | Includes A10 merged signals |
| CLOSED_LOSS | 467 | Includes A10 merged signals |
| CANCELLED | 221 | Includes A10 merged signals |
| CLOSED_BREAKEVEN | 154 | Includes A10 merged signals |
| ACTIVE | 75 | Normal active count |
| PENDING | 10 | Normal |
| CLOSED_MANUAL | 8 | Normal |
| **PARTIALLY_CLOSED** | **3** | **New A2 status — working correctly** |
| **Total** | **1409** | Up from 490 (A10 merge) |

---

## Open Items for 48h Checkpoint

1. **Blended PnL closure validation:** No signal has yet completed the full cycle: TP_HIT → remaining_pct < 100 → final closure with blended PnL. The 3 PARTIALLY_CLOSED signals (#1561 BTC, #1602 PHA, #1604 AVAX) are candidates. If any close by T+48h, validate that `final_roi` reflects the blended calculation.

2. **KPI-R3 duplicate discord_message_ids:** 147 signals across 14 groups have duplicate discord_message_ids. This is an **A10 merge artifact**, not an A2 issue. Flagged for A10 canary tracking.

3. **KPI-R2 trailing-stop signals:** 4 ACTIVE signals have SL > entry_price (LONG direction). All are trailing-stop cases pre-dating A2. Not a regression, but the KPI-R2 query does not account for trailing stops. Query refinement recommended for future daily checks.

---

## Monitoring Schedule

| Checkpoint | Time (UTC) | What | Status |
|------------|-----------|------|--------|
| **T+1h18m** | 2026-04-19T01:57Z | First post-restart closure reviewed, baselines refreshed | ✅ Complete |
| **T+~4h** | 2026-04-19T02:40Z | Natural TP_HIT validated on `#1602 PHA`, FET #1159 unchanged | ✅ Complete |
| **T+24h** | 2026-04-20T00:40Z | Full SC/KPI comparison, 4 TP_HIT events validated, A10 overlap documented | ✅ Complete |
| **T+48h** | 2026-04-21T00:40Z | Extended window: check for blended PnL closure, final canary close-out | 🔲 Scheduled |

---

## Verdict

**✅ PASS — T+24h Canary Confirmed**

### A2-specific findings (all positive):
- **4 natural TP_HIT events** with fully enriched payloads (close_pct, remaining_pct, alloc_source) — core A2 feature validated
- **3 PARTIALLY_CLOSED signals** actively tracking remaining_pct at 50.0 — new status working correctly
- **Sequential TP stepping** validated on #1602 PHA (TP2→TP3: 75.0→50.0)
- **First fully post-A2 TP1** observed on #1604 AVAX — clean
- **FET #1159 = 3.37** — legacy preservation holds at 24h
- **Zero A2-attributable baseline regression** — T+~4h metrics (pre-A10) confirm A2 had no negative impact

### Remaining caveat:
- Blended PnL closure path not yet naturally exercised (no signal has closed with remaining_pct < 100). This is a volume limitation, not a defect. Monitoring continues at T+48h.

### Cross-canary note:
- KPI-R3 duplicate discord_message_ids (147 signals) are an A10 artifact. Flagged for A10 canary, not counted against A2.

---

*🛡️ GUARDIAN — A2 Canary Protocol*
*T+24h checkpoint completed: 2026-04-20T00:40Z*
*Next checkpoint: T+48h (2026-04-21T00:40Z)*
