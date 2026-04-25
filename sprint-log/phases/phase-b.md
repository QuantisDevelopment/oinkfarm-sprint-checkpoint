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
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | ✅ DONE | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 25, 03:41 CEST · `ARTIFACT_PUBLISHED` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | 🛑 BLOCKED | — | — | Apr 24, 08:26 CEST · `BLOCKED` | anvil · forge · guardian · hermes |
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
| Apr 25, 05:25 CEST | `REVIEW_POSTED` | `M219` | vigil | M219 review by vigil — REVISE (7.5) |
| Apr 25, 05:25 CEST | `REVIEW_POSTED` | `M43` | vigil | M43 review by vigil — PASS (9.45) |
| Apr 25, 05:11 CEST | `BLOCKER_RESOLVED` | `M201` | guardian | M201 blocker cleared |
| Apr 25, 05:11 CEST | `REVIEW_POSTED` | `M201` | guardian | M201 review by guardian — PASS (9.4) |
| Apr 25, 05:04 CEST | `REVIEW_POSTED` | `—` | guardian | — review by guardian — PASS (9.8) |
| Apr 25, 05:04 CEST | `REVIEW_POSTED` | `—` | guardian | — review by guardian — PASS (9.4) |
| Apr 25, 05:01 CEST | `SPRINT_NOTE` | `M201` | anvil | HEARTBEAT.md updated for sg#38 VIGIL R2 PASS: cleared waiting_for_vigil_review and set sg38-specific wait state for GUARDIAN review. Checkpo |
| Apr 25, 04:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 04:52 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T024419Z_000001): 3 checkpoint events observed. Q1 explicit #189 PR |
| Apr 25, 04:50 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — PASS (9.3) |
| Apr 25, 04:44 CEST | `SPRINT_NOTE` | `M201` | anvil | sg#38 R2 fix turn complete at 1135d7d after rebase onto quantis/main@81345a2. Closed VIGIL MF-2 (stale base) and MF-1 with 6 producer-side p |
| Apr 25, 04:33 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 04:33 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T023238Z_000002): 1 checkpoint events observed; no new critical-pat |
| Apr 25, 04:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 04:32 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T021330Z_000002): 5 checkpoint events observed; no new critical-pat |
| Apr 25, 04:13 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 04:13 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T015243Z_000002): 4 checkpoint events observed; no new critical-pat |
| Apr 25, 03:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 03:52 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T013256Z_000002): 5 checkpoint events observed, no critical-path de |
| Apr 25, 03:41 CEST | `ARTIFACT_PUBLISHED` | `B3` | guardian | B3 published B3-daily-reconciliation:  |
| Apr 25, 03:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 03:32 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T011335Z_000002): 4 checkpoint events observed, 0 critical-path hit |
| Apr 25, 03:13 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 03:13 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T005251Z_000002): 5 checkpoint events observed, 0 critical-path hit |
| Apr 25, 02:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 02:52 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T003341Z_000002): 6 checkpoint events observed, 0 critical-path hit |
| Apr 25, 02:33 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 02:33 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260425T001342Z_000002): 2 checkpoint events observed, 0 critical-path hit |
| Apr 25, 02:13 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 02:13 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260424T235255Z_000002): 4 checkpoint events observed, 0 critical-path hit |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-OF214-REGISTRY-1` | VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calculate_blended_pnl (SOUL.md §1 row 1, CRITICAL) actually lives. Detector reports clean on PnL-calc commits = false-negative in safety net. FORGE cross-check AGREES with VIGIL verdict. Two valid fix paths; Mike decides which. | `M214` | 27.4h | add_kraken_sync_path — add scripts/kraken-sync.py to registry files[] with registry_id:1, keep 'canonical SOUL.md §1 mirror' wording, full coverage (recommended; mechanically small; closes false-negative class) · narrow_contract_wording — leave registry as-is but rewrite PR body + docs to explicitly scope detector to {micro-gate-v3.py, lifecycle.py} only, open tracking issue for full SOUL.md §1 parity (smaller Round 2 diff but leaves known gap open) |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
