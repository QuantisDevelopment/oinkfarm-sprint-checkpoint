# 🛡️ GUARDIAN Canary Report — Task A10

## Deploy Info
| Field | Value |
|-------|-------|
| **Task** | A10 — Database Merge Script |
| **PR** | #135 |
| **Issue** | #136 |
| **Deploy variant** | append-only production merge |
| **Merged into prod DB at** | 2026-04-19T18:29:23Z |
| **Imported rows** | 912 signals (`id=1612–2523`) |
| **Auxiliary inserts** | 1 missing trader (`id=130`) |
| **Expected post-merge total** | 1406 signals |
| **Canary started** | 2026-04-19T18:31:00Z |
| **Target** | Immediate spot-checks + first 10 organic post-merge signals (`id > 2523`) |
| **Rollback backup** | `/home/m/data/oinkfarm.db.a10-predrift-backup-20260419T182923Z` |

## Canary Protocol
Immediate checks:
1. Prod row counts and imported ID range are correct
2. No FK orphans introduced
3. No `NULL remaining_pct` or `NULL sl_type` regressions
4. API `:8888` resolves across old and imported IDs
5. Trader/server join paths render for imported historical data
6. No immediate schema/constraint errors visible after restart

Ongoing checks:
1. First 10 organic post-merge signals (`id > 2523`) insert cleanly
2. No FK orphans appear after subsequent inserts
3. No schema/constraint aborts appear in gateway logs
4. Report PASS / FAIL once enough post-merge organic flow is observed or a real regression is detected

## Immediate Spot-Check Results

### 1) Production DB integrity
| Check | Result |
|------|--------|
| total signals | **1406** ✅ |
| total traders | **100** ✅ |
| total servers | **11** ✅ |
| imported range rows (`1612–2523`) | **912** ✅ |
| imported range distinct trader_ids | **60** ✅ |
| imported range distinct server_ids | **11** ✅ |
| min/max signal id | **499 / 2523** ✅ |
| orphan trader refs | **0** ✅ |
| orphan server refs | **0** ✅ |
| `remaining_pct IS NULL` | **0** ✅ |
| `sl_type IS NULL` | **0** ✅ |

Representative spot-check rows:

| id | expected role | status | ticker | trader_id | server_id | posted_at | Result |
|---:|---|---|---|---:|---:|---|---|
| 1599 | pre-merge prod row | CLOSED_LOSS | B3 | 86 | 1 | 2026-04-18T14:29:19.900157+00:00 | ✅ present |
| 1612 | imported lowest | CLOSED_WIN | ORDI | 61 | 4 | 2026-02-12T12:44:00Z | ✅ present |
| 2523 | imported highest | CLOSED_WIN | CRV | 79 | 8 | 2026-03-15T17:54:31.736456+00:00 | ✅ present |

### 2) API spot-checks on `:8888`
| Endpoint | Result |
|---------|--------|
| `GET /signals/active` | **200 OK**, returned **77** active signals ✅ |
| `GET /signals/1599` | **200 OK** ✅ |
| `GET /signals/1612` | **200 OK** ✅ |
| `GET /signals/2523` | **200 OK** ✅ |

Observations:
- Imported historical IDs resolve cleanly through the live API.
- `GET /signals/active` currently shows **77** active rows, all from the existing prod-active set.
- Imported range currently contributes **0 ACTIVE** rows, so the endpoint does not yet show a mixed active old+imported sample.

### 3) Trader summary coverage for imported data
Validation run across all imported trader IDs:
- imported trader_id count: **60**
- `GET /traders/{id}` success count: **60 / 60** ✅
- failures: **0**

Representative join-path spot-checks:
- `GET /traders/61` returned `name=Sharp`, `server_name=Stock VIP`, populated stats and recent signals ✅
- `GET /traders/79` returned `name=Wolfxsignals`, `server_name=WolfxSignals`, populated stats and recent signals ✅

### 4) Post-restart ingest health
| Check | Result |
|------|--------|
| new rows with `id > 2523` | **1** observed so far (`id=2524`) ✅ |
| new ACTIVE rows in imported range | **0** |
| gateway / service errors checked since deploy | **none observed in available log tail / journal output** ✅ |

First observed post-merge organic insert:
- `id=2524`, `ticker=PIEVERSE`, `status=ACTIVE`, `order_type=MARKET`, `fill_status=FILLED`
- `filled_at=2026-04-19T19:11:01.849705+00:00` populated correctly ✅
- trader/server joins resolve: `Tareeq` / `Wealth Group` ✅
- `GET /signals/2524` returns `200 OK` ✅
- `GET /signals/active` now includes this new row and returns **78** active signals ✅

## First-N Organic Post-Merge Signals Log
Target population: first 10 organic signals with `id > 2523` and `posted_at >= 2026-04-19T18:29:23Z`

| # | Signal ID | posted_at | ticker | trader/server join | schema/FK result | API result | Verdict |
|---|-----------|-----------|--------|--------------------|------------------|------------|---------|
| 1 | 2524 | 2026-04-19T19:11:01.849705+00:00 | PIEVERSE | Tareeq / Wealth Group ✅ | clean insert, no FK or schema issue ✅ | `/signals/2524` and `/signals/active` both clean ✅ | Clean |
| 2 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 3 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 4 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 5 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 6 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 7 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 8 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 9 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
| 10 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |

## Anomalies
**Confirmed regression:** KPI-R5 is now **104** after A10 merge.

Evidence split:
- pre-merge prod rows (`id < 1612`) with `fill_status='FILLED' AND order_type='MARKET' AND filled_at IS NULL`: **0**
- imported A10 rows (`id 1612–2523`) matching that condition: **104**
- first live post-merge organic row (`id=2524`, PIEVERSE): `filled_at` populated correctly ✅

Interpretation:
- the current live insert path appears healthy
- the A10 imported historical dataset introduced 104 rows that violate the existing KPI-R5 invariant
- this is therefore a **real post-merge data-quality regression**, even though it is concentrated in imported historical rows rather than new organic inserts

Additional note:
- SC-3 heuristic flag count also increased after merge (`75` imported flags + `18` legacy flags), which is expected from expanded historical coverage and is not the primary fail condition here

## Current Verdict
**FAIL — KPI-R5 REGRESSION INTRODUCED BY IMPORTED HISTORICAL ROWS**

What is still verified despite the fail:
- merge counts are correct
- imported historical rows are live through `:8888`
- imported trader summaries resolve for all 60 referenced trader IDs
- no orphan FK regression exists
- no `NULL remaining_pct` / `NULL sl_type` regression exists
- first live post-merge organic insert landed cleanly
- no immediate post-restart service failure is visible

Why this is still a FAIL:
- production KPI-R5 moved from **0** to **104** immediately after merge
- violating rows are in the A10 imported range
- rollback criteria supplied by ANVIL were met because this is a real production regression

Recommended disposition:
- rollback A10, or
- explicitly accept and remediate the imported historical `filled_at` gaps before keeping the merge live

## Failure Trigger
If a real regression is detected, raise:
- `/tmp/a10_canary_fail.flag`
with reproduction details and notify ANVIL for rollback handling.

---
*🛡️ GUARDIAN — A10 Canary Active*
*Last updated: 2026-04-19T18:41:00Z*
