# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 5/14 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 20, 22:55 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🧪 CANARY | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 21, 12:09 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | 📝 PROPOSAL REVIEW | — | — | Apr 21, 12:08 CEST · `SPRINT_NOTE` | anvil · forge · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | ✅ DONE | PASS | — | Apr 21, 12:03 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:43 CEST · `TASK_PLANNED` | forge |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:45 CEST · `TASK_PLANNED` | forge |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 21, 12:09 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — Sprint canary sweep: verified no MERGED→missing CANARY_STARTED gap in last 2h; B3 T+48 final close-out not yet due; KPI/dashboard artifacts fresh |
| Apr 21, 12:08 CEST | `PROPOSAL_READY` | `B4` | anvil | B4 proposal ready |
| Apr 21, 12:08 CEST | `SPRINT_NOTE` | `B4` | anvil | Sprint poke response: Zero REVISE verdicts pending — all old REVISE items (A4/A10/B2/B3) subsequently resolved with PASS. B6 PR #29 awaiting |
| Apr 21, 12:03 CEST | `SPRINT_NOTE` | `B6` | anvil | Sprint check-in response: All 8 PRs Mike listed (oinkfarm#133,#149,#153; signal-gateway#9,#11,#21,#24,#25) are already MERGED — no rebase ne |
| Apr 21, 08:09 CEST | `CANARY_PASS` | `B1` | guardian | B1 canary PASS |
| Apr 21, 08:09 CEST | `CANARY_PASS` | `B5` | guardian | B5 canary PASS |
| Apr 21, 08:09 CEST | `CANARY_PASS` | `B6` | guardian | B6 canary PASS |
| Apr 21, 08:09 CEST | `CANARY_PASS` | `B7` | guardian | B7 canary PASS |
| Apr 21, 08:09 CEST | `CANARY_PASS` | `B8` | guardian | B8 canary PASS |
| Apr 21, 05:04 CEST | `CANARY_PASS` | `B3` | guardian | B3 canary PASS |
| Apr 20, 23:31 CEST | `ARTIFACT_PUBLISHED` | `B3` | guardian | B3 published kpi: b3-reconciliation-template.md |
| Apr 20, 23:30 CEST | `CANARY_PASS` | `B5` | guardian | B5 canary PASS |
| Apr 20, 23:30 CEST | `CANARY_STARTED` | `B6` | guardian | B6 canary started |
| Apr 20, 23:30 CEST | `CANARY_PASS` | `B6` | guardian | B6 canary PASS |
| Apr 20, 23:30 CEST | `CANARY_PASS` | `B7` | guardian | B7 canary PASS |
| Apr 20, 23:30 CEST | `CANARY_PASS` | `B8` | guardian | B8 canary PASS |
| Apr 20, 23:18 CEST | `SPRINT_NOTE` | `B4` | anvil | PG installed (17.9) + psycopg 3.3.3 + B2 migration dry-run CLEAN on test DB. Row counts match: servers=11, traders=100, signals=1447, signal |
| Apr 20, 23:18 CEST | `TASK_PLANNED` | `B9` | forge | B9 plan published |
| Apr 20, 23:18 CEST | `TASK_PLANNED` | `B12` | forge | B12 plan published |
| Apr 20, 23:18 CEST | `TASK_PLANNED` | `B13` | forge | B13 plan published |
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

## Needs Mike (open gates)

_No open DECISION_NEEDED for this phase._

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
