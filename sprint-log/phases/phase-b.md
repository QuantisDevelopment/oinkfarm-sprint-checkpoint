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
| [B2](../tasks/B2-b2.md) | 🔴 CRITICAL | 🧪 CANARY | PENDING | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 21, 16:29 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🧪 CANARY | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 21, 14:40 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 21, 16:33 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 21, 16:11 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
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
| Apr 21, 16:33 CEST | `PROPOSAL_APPROVED` | `B4` | vigil | B4 proposal approved by vigil |
| Apr 21, 16:32 CEST | `SPRINT_NOTE` | `—` | hermes | AGGRESSIVE scope locked 2026-04-21 14:35 UTC by Mike. Target: Heavy Hybrid done 2026-05-30. Full Phase B + C1/C2/C3/C4/C6. C5+C7 deferred po |
| Apr 21, 16:29 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: NO DRIFT. Forge's fresh-eyes cross-check flagged apparent deltas between PR 17073d12 (B2) and live working tree at be2ff3b7, bu |
| Apr 21, 16:12 CEST | `AGENT_HEARTBEAT` | `B4` | guardian | guardian heartbeat — Heartbeat sweep 13:58–14:11 UTC: A6 48h canary DONE (CANARY_PASS), A9 48h canary DONE (INCONCLUSIVE_CODE_PASS), B4 Phase 0 R2 APPROVED (method-only), B6 Phase 1 PASS (10.00). Next due: A10 48h at 18:29 UTC, B2 T+48h at 01:22 UTC, B3 T+48h at 02:25 UTC. |
| Apr 21, 16:11 CEST | `REVIEW_POSTED` | `B6` | guardian | B6 review by guardian — PASS (10.0) |
| Apr 21, 16:09 CEST | `PROPOSAL_APPROVED` | `B4` | guardian | B4 proposal approved by guardian |
| Apr 21, 15:57 CEST | `SPRINT_NOTE` | `B8` | forge | Fresh-eyes poke complete. Cross-checked recent VIGIL REVIEW_POSTED items beyond the earlier B2 audit: B7 (cfb23fb, score 10.0 PASS) and B8 ( |
| Apr 21, 15:34 CEST | `SPRINT_NOTE` | `B4` | anvil | Sprint poke 15:33 CEST: No change from 14:22 poke. Zero REVISE verdicts on ANVIL PRs. Zero new REVIEW_POSTED events since last check. B4 Pha |
| Apr 21, 14:40 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — Sprint canary sweep: no MERGED tasks missing CANARY_STARTED in last 2h; B3 T+48 close-out not yet due; dashboard artifacts fresh, no republish needed |
| Apr 21, 14:24 CEST | `SPRINT_NOTE` | `B4` | anvil | Sprint poke 14:22 CEST: Zero REVISE verdicts on ANVIL PRs. B4 Phase 0 R2 submitted 11:21 UTC — no VIGIL or GUARDIAN review yet (2h wait). B6 |
| Apr 21, 14:11 CEST | `SPRINT_NOTE` | `B2` | forge | SPRINT POKE check-in complete. Fresh-eyes cross-check already shipped and findings stand: agree with VIGIL on A11, B1, and B5; partial disag |
| Apr 21, 13:21 CEST | `SPRINT_NOTE` | `B4` | anvil | Sprint poke R2: GUARDIAN rejected B4 Phase 0 R1 with REQUEST_CHANGES — all 5 concerns addressed in R2 proposal. VIGIL B4 Phase 0 review stil |
| Apr 21, 13:21 CEST | `PROPOSAL_READY` | `B4` | anvil | B4 proposal ready |
| Apr 21, 13:02 CEST | `PROPOSAL_REJECTED` | `B4` | guardian | B4 proposal rejected — REQUEST_CHANGES: P6-P8 prerequisites remain unmet, migration acceptance state is unresolved, and reconciliation/rollb |
| Apr 21, 13:02 CEST | `AGENT_HEARTBEAT` | `B4` | guardian | guardian heartbeat — Heartbeat sweep completed; B4 Phase 0 proposal reviewed with REQUEST_CHANGES; no fresh merged tasks missing CANARY_STARTED; KPI artifacts fresh |
| Apr 21, 12:25 CEST | `SPRINT_NOTE` | `B2` | forge | FORGE fresh-eyes cross-check complete. Agree with VIGIL on A11, B1, and B5. For B2, I agree the reviewed PR artifact (oinkfarm#153 / commit  |
| Apr 21, 12:25 CEST | `DECISION_NEEDED` | `B2` | forge | B2 Mike gate: Does existing B2 review approval still cover production migration from the current modified local candidate, or must the post- |
| Apr 21, 12:16 CEST | `REVIEW_POSTED` | `B2` | vigil | B2 review by vigil — PASS (9.6) |
| Apr 21, 12:16 CEST | `REVIEW_POSTED` | `B7` | vigil | B7 review by vigil — PASS (10.0) |
| Apr 21, 12:16 CEST | `REVIEW_POSTED` | `B8` | vigil | B8 review by vigil — PASS (9.85) |
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

## Needs Mike (open gates)

_No open DECISION_NEEDED for this phase._

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
