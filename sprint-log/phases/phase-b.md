# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 0/14 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | 🧪 CANARY | PENDING | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 20, 13:15 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 20, 22:55 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 20, 15:15 CEST · `SPRINT_NOTE` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 22:55 CEST · `DECISION_RESOLVED` | forge · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 20, 09:02 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | MERGED | — | — | Apr 20, 08:46 CEST · `MERGED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 20, 12:26 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 20, 12:10 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 22:54 CEST · `DECISION_RESOLVED` | forge · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:43 CEST · `TASK_PLANNED` | forge |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:45 CEST · `TASK_PLANNED` | forge |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 22:54 CEST · `DECISION_RESOLVED` | forge · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 22:54 CEST · `DECISION_RESOLVED` | forge · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 0/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Accept NULL filled_at on 84 historical closed signals as-is. No backfill. B2 PG migration preserves NULLs. No Phase A KPI uses  |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: RECLASSIFIED as scheduled gate, not live blocker. B4 cutover approval will re-surface as a fresh DECISION_NEEDED when (a) B3 du |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: CHECK-only constraint (entry_price > 0). No PL/pgSQL trigger — REJECTED_AUDIT code path is dead. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Defer TimescaleDB to B14 (dedicated task). PG first, Timescale bolts on non-destructively when workload justifies. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at  |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B13` | hermes | B13 decision: Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B9` | hermes | B9 decision: signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFO |
| Apr 20, 17:53 CEST | `TASK_PLANNED` | `—` | forge | — plan published |
| Apr 20, 17:52 CEST | `TASK_PLANNED` | `—` | forge | — plan published |
| Apr 20, 15:15 CEST | `SPRINT_NOTE` | `B3` | hermes | B3 dual-write activation gap investigated. VERDICT: intentional gate, NOT an oversight. OINK_DB_DUAL_WRITE=false is the CORRECT state until  |
| Apr 20, 13:35 CEST | `TASK_PLANNED` | `B3` | forge | B3 plan published |
| Apr 20, 13:35 CEST | `TASK_PLANNED` | `B4` | forge | B4 plan published |
| Apr 20, 13:32 CEST | `DECISION_RESOLVED` | `B3` | mike | B3 decision: 7 days minimum with reset rule: any reconciliation report showing >0 row-count or >0 event-count discrepancy resets the clock t |
| Apr 20, 13:21 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: Defer TimescaleDB introduction from B2 to B14? |
| Apr 20, 13:21 CEST | `DECISION_NEEDED` | `B13` | forge | B13 Mike gate: Single-host Docker Compose for B13, defer multi-host to Phase D+? |
| Apr 20, 13:21 CEST | `DECISION_NEEDED` | `B9` | forge | B9 Mike gate: Enforce W1 immutability via phased app-level then DB REVOKE? |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Adopt psycopg3 (`psycopg[binary]`). It is the actively maintained upstream (psycopg2 is in maintenance mode), has a cleaner Con |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Canonical oink_db.py lives in oinkfarm scripts/ (/home/oinkv/oinkfarm/scripts/oink_db.py), with vendored copies in oink-sync/ a |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Same server (barn) initially, inside Docker Compose network. Matches Arbiter V3 PHASE-4 §2 topology exactly ('Container definit |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Re-enable the systemd unit before B4 cutover. Reasons: (1) Arbiter PHASE-0 §Resilience explicitly models signal-gateway supervi |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Fork-sync for B4; schedule re-point for B13 (Docker Compose). Rationale: (1) B4 is a CRITICAL cutover window — re-pointing serv |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-t |
| Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | guardian | B7 canary started |
| Apr 20, 12:17 CEST | `MERGED` | `B7` | anvil | B7 merged via PR #27 @3f85c12 |
| Apr 20, 12:10 CEST | `CANARY_STARTED` | `B8` | guardian | B8 canary started |
| Apr 20, 11:57 CEST | `MERGED` | `B8` | anvil | B8 merged via PR #26 @6879e25 |
| Apr 20, 11:56 CEST | `PR_OPENED` | `B7` | anvil | B7 PR #27 opened — feat(B7): extract WG Bot parsers to parsers/wg_bot.py |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: Cutover requires Mike's explicit go-ahead |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B1` | forge | B1 Mike gate: PostgreSQL driver: psycopg3 vs psycopg2? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B1` | forge | B1 Mike gate: oink_db.py location? |

## Needs Mike (open gates)

_No open DECISION_NEEDED for this phase._

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
