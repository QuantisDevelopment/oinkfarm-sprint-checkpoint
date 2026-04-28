# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 7/17 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 22, 05:53 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | ✅ DONE | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 28, 08:08 CEST · `ARTIFACT_PUBLISHED` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | 🛑 BLOCKED | — | — | Apr 28, 08:08 CEST · `BLOCKED` | anvil · forge · guardian · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 27, 08:06 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 22, 10:07 CEST · `SPRINT_NOTE` | anvil · forge · guardian · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 09:49 CEST · `TASK_PLANNED` | anvil · forge · guardian |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 01:03 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⚙️ CODING | — | — | Apr 22, 01:06 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 27, 00:57 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian · hermes |
| [B14](../tasks/B14-b14.md) | 🟡 STANDARD | 👀 PR REVIEW | — | [signal-gateway#76](https://github.com/QuantisDevelopment/signal-gateway/pull/76) | Apr 28, 07:59 CEST · `REVIEW_POSTED` | vigil |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 27, 02:06 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian |
| [B277](../tasks/B277-b277.md) | 🟡 STANDARD | 👀 PR REVIEW | — | [oinkfarm#281](https://github.com/QuantisDevelopment/oinkfarm/pull/281) | Apr 28, 11:34 CEST · `REVIEW_POSTED` | vigil |
| [B280](../tasks/B280-b280.md) | 🟡 STANDARD | 👀 PR REVIEW | — | [oinkfarm#282](https://github.com/QuantisDevelopment/oinkfarm/pull/282) | Apr 28, 11:34 CEST · `REVIEW_POSTED` | vigil |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 28, 20:52 CEST | `REVIEW_POSTED` | `M319` | vigil | M319 review by vigil — REVISE (9.6) |
| Apr 28, 20:52 CEST | `REVIEW_POSTED` | `M312` | vigil | M312 review by vigil — PASS (10.0) |
| Apr 28, 20:52 CEST | `REVIEW_POSTED` | `M312` | vigil | M312 review by vigil — REVISE (8.65) |
| Apr 28, 20:52 CEST | `REVIEW_POSTED` | `M311` | vigil | M311 review by vigil — PASS (9.0) |
| Apr 28, 20:01 CEST | `REVIEW_POSTED` | `M320` | vigil | M320 review by vigil — PASS (9.85) |
| Apr 28, 20:01 CEST | `REVIEW_POSTED` | `M325` | vigil | M325 review by vigil — PASS (9.3) |
| Apr 28, 20:01 CEST | `REVIEW_POSTED` | `M305` | vigil | M305 review by vigil — PASS (9.85) |
| Apr 28, 19:56 CEST | `REVIEW_POSTED` | `M292` | vigil | M292 review by vigil — PASS (9.7) |
| Apr 28, 16:12 CEST | `REVIEW_POSTED` | `M313` | vigil | M313 review by vigil — PASS (9.85) |
| Apr 28, 16:12 CEST | `REVIEW_POSTED` | `M312` | vigil | M312 review by vigil — PASS (9.7) |
| Apr 28, 15:55 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (9.3) |
| Apr 28, 15:15 CEST | `REVIEW_POSTED` | `—` | guardian | — review by guardian — REVISE (8.6) |
| Apr 28, 14:42 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — REVISE (0.0) |
| Apr 28, 14:42 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — REVISE (0.0) |
| Apr 28, 14:39 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — REVISE (7.95) |
| Apr 28, 13:44 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (9.55) |
| Apr 28, 13:13 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (0) |
| Apr 28, 13:13 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — REVISE (9.0) |
| Apr 28, 12:35 CEST | `REVIEW_POSTED` | `—` | vigil | — review by vigil — PASS (0) |
| Apr 28, 11:34 CEST | `REVIEW_POSTED` | `B280` | vigil | B280 review by vigil — PASS (0.0) |
| Apr 28, 11:34 CEST | `REVIEW_POSTED` | `B277` | vigil | B277 review by vigil — PASS (0.0) |
| Apr 28, 09:13 CEST | `PROPOSAL_APPROVED` | `M189` | vigil | M189 proposal approved by vigil |
| Apr 28, 09:13 CEST | `REVIEW_POSTED` | `M189` | vigil | M189 review by vigil — PASS (9.7) |
| Apr 28, 08:08 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-28.md |
| Apr 28, 08:08 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 28, 07:59 CEST | `REVIEW_POSTED` | `M195` | guardian | M195 review by guardian — PASS (9.4) |
| Apr 28, 07:59 CEST | `REVIEW_POSTED` | `B14` | vigil | B14 review by vigil — PASS (9.0) |
| Apr 28, 05:40 CEST | `REVIEW_POSTED` | `M291` | vigil | M291 review by vigil — PASS (9.6) |
| Apr 28, 05:38 CEST | `REVIEW_POSTED` | `M187` | guardian | M187 review by guardian — REVISE (9.45) |
| Apr 28, 05:15 CEST | `DECISION_NEEDED` | `M189` | forge | M189 Mike gate: Q-189-2 was formally resolved on 2026-04-22 with binding text: BE_TOLERANCE_FRAC=0.0001 shared constant across Artifacts A/B |

## Needs Mike (open gates)

_No open DECISION_NEEDED for this phase._

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
