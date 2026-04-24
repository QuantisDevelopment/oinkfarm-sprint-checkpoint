# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 6/14 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 22, 05:53 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | ✅ DONE | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 23, 09:58 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | 🛑 BLOCKED | — | — | Apr 23, 08:11 CEST · `BLOCKED` | anvil · forge · guardian · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | 🧪 CANARY | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 22, 00:45 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 22, 10:07 CEST · `SPRINT_NOTE` | anvil · forge · guardian · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 09:49 CEST · `TASK_PLANNED` | anvil · forge · guardian |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 01:03 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⚙️ CODING | — | — | Apr 22, 01:06 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 24, 05:39 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — REVISE (6.2) |
| Apr 24, 02:52 CEST | `DECISION_NEEDED` | `M214` | forge | M214 Mike gate: VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calcu |
| Apr 24, 02:23 CEST | `REVIEW_POSTED` | `M214` | vigil | M214 review by vigil — REVISE (5.9) |
| Apr 23, 23:30 CEST | `REVIEW_POSTED` | `M202` | vigil | M202 review by vigil — PASS (9.7) |
| Apr 23, 23:26 CEST | `REVIEW_POSTED` | `M154` | guardian | M154 review by guardian — PASS (9.65) |
| Apr 23, 23:08 CEST | `REVIEW_POSTED` | `M154` | vigil | M154 review by vigil — PASS (9.55) |
| Apr 23, 21:15 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (9.0) |
| Apr 23, 20:23 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (10.0) |
| Apr 23, 20:23 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (10.0) |
| Apr 23, 19:49 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (10.0) |
| Apr 23, 19:49 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — REVISE (6.8) |
| Apr 23, 09:58 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — cron heartbeat 09:57 GMT+2 |
| Apr 23, 09:47 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 09:45 GMT+2 sweep |
| Apr 23, 09:18 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 09:17 GMT+2 sweep |
| Apr 23, 08:44 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 08:42 GMT+2 sweep |
| Apr 23, 08:11 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-23.md |
| Apr 23, 08:11 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 23, 08:11 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-23.md |
| Apr 23, 08:11 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 23, 07:58 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — heartbeat 07:57 GMT+2 sweep |
| Apr 23, 07:37 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 07:37 GMT+2 sweep |
| Apr 23, 07:10 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 07:09 GMT+2 sweep |
| Apr 23, 06:39 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — sprint-poke 06:38 GMT+2 sweep |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-OF214-REGISTRY-1` | VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calculate_blended_pnl (SOUL.md §1 row 1, CRITICAL) actually lives. Detector reports clean on PnL-calc commits = false-negative in safety net. FORGE cross-check AGREES with VIGIL verdict. Two valid fix paths; Mike decides which. | `M214` | 3.7h | add_kraken_sync_path — add scripts/kraken-sync.py to registry files[] with registry_id:1, keep 'canonical SOUL.md §1 mirror' wording, full coverage (recommended; mechanically small; closes false-negative class) · narrow_contract_wording — leave registry as-is but rewrite PR body + docs to explicitly scope detector to {micro-gate-v3.py, lifecycle.py} only, open tracking issue for full SOUL.md §1 parity (smaller Round 2 diff but leaves known gap open) |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
