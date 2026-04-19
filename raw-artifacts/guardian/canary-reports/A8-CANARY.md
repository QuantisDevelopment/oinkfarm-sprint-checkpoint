# 🛡️ GUARDIAN Canary Report — Task A8

## Deploy Info
| Field | Value |
|-------|-------|
| **Task** | A8 — Conditional SL Type Field |
| **PR** | #134 |
| **Merge commit** | `46154543` |
| **Merged at** | 2026-04-19T15:27:19Z |
| **Deployed + backfilled at** | 2026-04-19T15:28:00Z |
| **Canary started** | 2026-04-19T15:43:00Z |
| **Target** | First 10 organic post-deploy signals |
| **24h checkpoint** | 2026-04-20T15:28:00Z |
| **48h checkpoint** | 2026-04-21T15:28:00Z |

## Canary Protocol
For each qualifying organic post-deploy signal:
1. `sl_type IS NOT NULL`
2. If `stop_loss IS NOT NULL` → `sl_type IN ('FIXED','CONDITIONAL','MANUAL')`
3. If `stop_loss IS NULL` and `notes NOT LIKE '%SL:CONDITIONAL%'` → `sl_type='NONE'`
4. If `notes LIKE '%SL:CONDITIONAL%'` → `sl_type='CONDITIONAL'`
5. Update-path check: `sl_type='MANUAL'` only when SL numeric value actually changes

Verdicts:
- **10/10 clean** → PASS
- **1-2 issues** → WARNING (P2)
- **3+ issues** → FAIL (P1)
- **<3 qualifying signals in 48h** → INCONCLUSIVE

## Pre-Deploy / Deploy Baseline
From deploy artifacts already on disk:
- pre-migration signal count: **494**
- backfill totals: **FIXED=466, NONE=28, CONDITIONAL=0, MANUAL=0, NULL=0**
- deploy anomaly count: **0**
- FET #1159 baseline: `stop_loss=0.2285`, `sl_type=FIXED` ✅

## Initial Production Snapshot
Live DB snapshot captured after deploy:

### A8-specific distribution
| sl_type | Count |
|---------|------:|
| FIXED | 466 |
| NONE | 28 |
| CONDITIONAL | 0 |
| MANUAL | 0 |
| NULL | 0 |

### Post-deploy signal flow
- signals with `posted_at >= 2026-04-19T15:28:00Z`: **0**
- qualifying canary samples observed: **0 / 10**
- gateway ingest health proxy, last 24h signals: **26**

### FET #1159 reference case
| id | ticker | stop_loss | sl_type | entry_price | exit_price | final_roi | Verdict |
|----|--------|-----------|---------|-------------|------------|-----------|---------|
| 1159 | FET | 0.2285 | FIXED | 0.2285 | 0.2285 | 3.37 | ✅ unchanged |

## SC / KPI Snapshot at Canary Start
| Metric | Value |
|--------|------:|
| SC-1 distinct signal_ids in event log | 27 |
| SC-1 total signal_events rows | 352 |
| SC-2 false closure rate (30d) | 11.8841% |
| SC-4 total signals | 494 |
| KPI-R1 breakeven 7d | 20.4167% |
| KPI-R4 NULL leverage | 80.1619% |
| KPI-R5 MARKET/FILLED with NULL filled_at | 0 |

## First-10 Signal Scan
No organic post-deploy rows have landed yet, so the first-10 sample table is still pending.

| # | Signal ID | posted_at | stop_loss | notes evidence | expected sl_type | observed sl_type | Verdict |
|---|-----------|-----------|-----------|----------------|------------------|------------------|---------|
| 1 | — | — | — | — | — | — | Awaiting |
| 2 | — | — | — | — | — | — | Awaiting |
| 3 | — | — | — | — | — | — | Awaiting |
| 4 | — | — | — | — | — | — | Awaiting |
| 5 | — | — | — | — | — | — | Awaiting |
| 6 | — | — | — | — | — | — | Awaiting |
| 7 | — | — | — | — | — | — | Awaiting |
| 8 | — | — | — | — | — | — | Awaiting |
| 9 | — | — | — | — | — | — | Awaiting |
| 10 | — | — | — | — | — | — | Awaiting |

## Current Verdict
**PENDING, CLEAN INITIAL CAPTURE**

What is verified now:
- `sl_type` exists in production and is fully populated
- backfill distribution matches deploy logs exactly
- no `NULL` regression is visible
- FET #1159 remains intact
- ingest is active overall, but no post-deploy A8 sample has landed yet

What is still pending:
- first live INSERT classifications after deploy
- first live `CONDITIONAL` sample, if one arrives
- update-path validation for `MANUAL`

## Next Checks
1. capture first 10 organic signals with `posted_at >= 2026-04-19T15:28:00Z`
2. validate classification semantics row-by-row
3. check whether any update-path row flips to `MANUAL` only on true SL change
4. refresh SC/KPI snapshot at 24h and 48h checkpoints
5. if <3 qualifying signals by 48h, mark **INCONCLUSIVE** and escalate to Mike

---
*🛡️ GUARDIAN — A8 Canary Active*
*Last updated: 2026-04-19T15:44:00Z*
