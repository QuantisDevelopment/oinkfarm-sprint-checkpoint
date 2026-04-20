# Phase B — Infrastructure Migration

**Status:** 0/15 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | 🧪 CANARY | PENDING | [oinkfarm#121](https://github.com/QuantisDevelopment/oinkfarm/pull/121) + [oinkdb-api#1](https://github.com/QuantisDevelopment/oinkdb-api/pull/1) + [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 20, 11:55 CEST · `DECISION_NEEDED` | anvil · forge · guardian · system |
| [B2](../tasks/B2-b2.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 20, 11:55 CEST · `DECISION_NEEDED` | anvil · forge · guardian · system |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 20, 11:55 CEST · `DECISION_NEEDED` | anvil · forge · guardian · system |
| [B4](../tasks/B4-b4.md) | 🟡 STANDARD | MERGED | — | [oinkdb-api#4](https://github.com/QuantisDevelopment/oinkdb-api/pull/4) | Apr 20, 11:55 CEST · `DECISION_NEEDED` | anvil · forge |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 20, 09:02 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | MERGED | — | — | Apr 20, 08:46 CEST · `MERGED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 20, 12:26 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | 🧪 CANARY | PENDING | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 20, 12:10 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `DECISION_NEEDED` | forge |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:43 CEST · `TASK_PLANNED` | forge |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:45 CEST · `TASK_PLANNED` | forge |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `DECISION_NEEDED` | forge |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | MERGED | — | [signal-gateway#3](https://github.com/QuantisDevelopment/signal-gateway/pull/3) + [signal-gateway#5](https://github.com/QuantisDevelopment/signal-gateway/pull/5) | Apr 20, 11:55 CEST · `DECISION_NEEDED` | anvil · forge |
| [B14](../tasks/B14-b14.md) | 🟡 STANDARD | MERGED | — | [signal-gateway#4](https://github.com/QuantisDevelopment/signal-gateway/pull/4) + [oinkfarm#63](https://github.com/QuantisDevelopment/oinkfarm/pull/63) | Apr 17, 11:46 CEST · `MERGED` | anvil |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 0/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | guardian | B7 canary started |
| Apr 20, 12:17 CEST | `MERGED` | `B7` | anvil | B7 merged via PR #27 @3f85c12 |
| Apr 20, 12:10 CEST | `CANARY_STARTED` | `B8` | guardian | B8 canary started |
| Apr 20, 11:57 CEST | `MERGED` | `B8` | anvil | B8 merged via PR #26 @6879e25 |
| Apr 20, 11:56 CEST | `PR_OPENED` | `B7` | anvil | B7 PR #27 opened — feat(B7): extract WG Bot parsers to parsers/wg_bot.py |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: Cutover requires Mike's explicit go-ahead |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B1` | forge | B1 Mike gate: PostgreSQL driver: psycopg3 vs psycopg2? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B1` | forge | B1 Mike gate: oink_db.py location? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: PostgreSQL hosting: same server or separate? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: TimescaleDB now or later (B14)? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: 84 closed signals with NULL filled_at — backfill/accept/block? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: trg_entry_price_update REJECTED_AUDIT exception handling |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B3` | forge | B3 Mike gate: Minimum verification period: 7 or 14 days? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: signal-gateway.service systemd re-enable or keep manual? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: .openclaw/workspace fork-sync or re-point to canonical? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B12` | forge | B12 Mike gate: Redis hosting: same server or separate? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B12` | forge | B12 Mike gate: Redis Streams retention policy: MAXLEN or time-based? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B13` | forge | B13 Mike gate: Docker Compose: single host or multi-host? |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B9` | forge | B9 Mike gate: W1 enforcement level: DB REVOKE UPDATE, or app-level guard? |
| Apr 20, 11:55 CEST | `TASK_PLANNED` | `B15` | forge | B15 plan published |
| Apr 20, 11:54 CEST | `PR_OPENED` | `B8` | anvil | B8 PR #26 opened — feat(B8): cross-channel dedup consolidation — extract dedup.py |
| Apr 20, 11:53 CEST | `TASK_PLANNED` | `B13` | forge | B13 plan published |
| Apr 20, 11:52 CEST | `REVIEW_POSTED` | `B7` | guardian | B7 review by guardian — PASS (9.8) |
| Apr 20, 11:46 CEST | `MERGED` | `B7` | anvil | B7 merged via PR #None @ef09652 |
| Apr 20, 11:45 CEST | `TASK_PLANNED` | `B11` | forge | B11 plan published |
| Apr 20, 11:43 CEST | `TASK_PLANNED` | `B10` | forge | B10 plan published |
| Apr 20, 11:36 CEST | `REVIEW_POSTED` | `B8` | guardian | B8 review by guardian — PASS (9.8) |
| Apr 20, 11:29 CEST | `MERGED` | `B8` | anvil | B8 merged via PR #None @39447d1 |
| Apr 20, 09:40 CEST | `PROPOSAL_APPROVED` | `B8` | system | B8 proposal approved by vigil+guardian |
| Apr 20, 09:36 CEST | `REVIEW_POSTED` | `B8` | guardian | B8 review by guardian — PASS (9.5) |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `B4-APPROVE` | Cutover requires Mike's explicit go-ahead | `B4` | 51m | APPROVE · DEFER |
| `Q-B1-1` | PostgreSQL driver: psycopg3 vs psycopg2? | `B1` | 51m | psycopg3 · psycopg2 |
| `Q-B1-2` | oink_db.py location? | `B1` | 51m | canonical · other |
| `Q-B2-1` | PostgreSQL hosting: same server or separate? | `B2` | 51m | same · separate |
| `Q-B2-3` | TimescaleDB now or later (B14)? | `B2` | 51m | now · later |
| `Q-B2-4` | 84 closed signals with NULL filled_at — backfill/accept/block? | `B2` | 51m | backfill · accept · block |
| `Q-B2-5` | trg_entry_price_update REJECTED_AUDIT exception handling | `B2` | 51m | pg_trigger · check_only |
| `Q-B3-2` | Minimum verification period: 7 or 14 days? | `B3` | 51m | 7d · 14d |
| `Q-B4-4` | signal-gateway.service systemd re-enable or keep manual? | `B4` | 51m | re-enable · keep_manual |
| `Q-B4-5` | .openclaw/workspace fork-sync or re-point to canonical? | `B4` | 51m | fork_sync · repoint |
| `Q-HH-1` | Redis hosting: same server or separate? | `B12` | 51m | same · separate |
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | `B12` | 51m | maxlen · time_based |
| `Q-HH-3` | Docker Compose: single host or multi-host? | `B13` | 51m | single · multi |
| `Q-HH-4` | W1 enforcement level: DB REVOKE UPDATE, or app-level guard? | `B9` | 51m | db_revoke · app_guard |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
