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
| new rows with `id > 2523` | **0** at initial capture |
| new ACTIVE rows in imported range | **0** |
| gateway / service errors checked since deploy | **none observed in available log tail / journal output** ✅ |

## First-N Organic Post-Merge Signals Log
Target population: first 10 organic signals with `id > 2523` and `posted_at >= 2026-04-19T18:29:23Z`

| # | Signal ID | posted_at | ticker | trader/server join | schema/FK result | API result | Verdict |
|---|-----------|-----------|--------|--------------------|------------------|------------|---------|
| 1 | — | — | — | Awaiting | Awaiting | Awaiting | Pending |
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
**None confirmed at initial capture.**

Notes:
- No post-merge organic signal rows have landed yet, so insert-path validation is still pending.
- No immediate FK, schema-population, or API-range regression was detected.
- Current evidence supports a clean append-only merge with live API visibility across the expanded ID range.

## Current Verdict
**ACTIVE, INITIAL SPOT-CHECK PASS**

This is not a final canary PASS yet because the first 10 organic post-merge signals have not arrived.
What is already verified:
- merge counts are correct
- imported historical rows are live through `:8888`
- imported trader summaries resolve for all 60 referenced trader IDs
- no orphan FK regression exists
- no `NULL remaining_pct` / `NULL sl_type` regression exists
- no immediate post-restart failure is visible

What remains pending:
- first 10 organic post-merge inserts
- continued no-error observation during live ingestion
- post-insert orphan re-check after new rows arrive

## Failure Trigger
If a real regression is detected, raise:
- `/tmp/a10_canary_fail.flag`
with reproduction details and notify ANVIL for rollback handling.

---
*🛡️ GUARDIAN — A10 Canary Active*
*Last updated: 2026-04-19T18:41:00Z*
