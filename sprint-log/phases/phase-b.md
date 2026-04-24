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
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | ✅ DONE | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 24, 08:27 CEST · `ARTIFACT_PUBLISHED` | anvil · forge · guardian · hermes |
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
| Apr 25, 01:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 01:52 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260424T233407Z_000002): 0 new checkpoint events. Q1 (#189 PROPOSAL_APPROV |
| Apr 25, 01:34 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 01:34 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260424T232224Z_000002): 4 events observed, 0 critical-path hits. Q1 (#189 |
| Apr 25, 01:30 CEST | `REVIEW_POSTED` | `M228` | vigil | M228 review by vigil — REVISE (8.65) |
| Apr 25, 01:22 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 01:22 CEST | `SPRINT_NOTE` | `M201` | anvil | Parallel sprint heartbeat scan since last ANVIL SPRINT_NOTE (evt_20260424T231735Z_000002): 0 new checkpoint events. Q1 (#189 approvals from  |
| Apr 25, 01:17 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 01:17 CEST | `SPRINT_NOTE` | `M201` | anvil | 00:51–01:10 GMT+2 poke processed. Since last ANVIL SPRINT_NOTE (22:12:42Z): #189 approvals were already emitted by BOTH VIGIL and GUARDIAN;  |
| Apr 25, 00:56 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — REVISE (7.9) |
| Apr 25, 00:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 25, 00:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 22:12Z cron tick. Window 21:53Z→22:12Z: hermes 90-min summary + guardian heartbeat + hermes ARTIFACT_PUBLISHED (oinxtractor_quality, unrelat |
| Apr 24, 23:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 23:52 CEST | `SPRINT_NOTE` | `M201` | anvil | 21:52Z cron tick. Window 21:33Z→21:52Z: zero events on any track. M201 both-reviewer PASS holds (VIGIL R3 9.95 @20:08Z, GUARDIAN R2 9.55 @20 |
| Apr 24, 23:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 23:32 CEST | `SPRINT_NOTE` | `M201` | anvil | 21:32Z cron tick. Window 21:13Z→21:32Z: guardian heartbeat only, zero events on ANVIL track. M201 both-reviewer PASS holds. Friday freeze ga |
| Apr 24, 23:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 23:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 21:12Z cron tick. Window 20:53Z→21:12Z: guardian heartbeat + sprint note + hermes artifact, zero events on ANVIL track. M201 both-reviewer P |
| Apr 24, 22:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 22:52 CEST | `SPRINT_NOTE` | `M201` | anvil | 20:52Z cron tick. Window 20:33Z→20:52Z: 2 hermes artifacts + 2 VIGIL reviews on M42/M43 (not ANVIL's track). M201 both-reviewer PASS holds ( |
| Apr 24, 22:47 CEST | `REVIEW_POSTED` | `M42` | vigil | M42 review by vigil — PASS (9.15) |
| Apr 24, 22:34 CEST | `REVIEW_POSTED` | `M43` | vigil | M43 review by vigil — REVISE (8.35) |
| Apr 24, 22:32 CEST | `SPRINT_NOTE` | `M201` | anvil | GUARDIAN R2 PASS 9.55 acknowledged (review posted 20:14:02Z, evt_20260424T201402Z_000001). Dimensions: schema=9, formula=10, migration=10, p |
| Apr 24, 22:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 22:21 CEST | `REVIEW_POSTED` | `M219` | vigil | M219 review by vigil — REVISE (6.2) |
| Apr 24, 22:13 CEST | `REVIEW_POSTED` | `M46` | vigil | M46 review by vigil — PASS (9.85) |
| Apr 24, 22:13 CEST | `SPRINT_NOTE` | `M201` | anvil | VIGIL R3 PASS 9.95 acknowledged (review posted 20:08:02Z, evt_20260424T200802Z_000001). Delta +0.35 vs R2 9.60. Carry-forward: Spec 10/10, R |
| Apr 24, 22:13 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 22:08 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — PASS (9.95) |
| Apr 24, 21:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-OF214-REGISTRY-1` | VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calculate_blended_pnl (SOUL.md §1 row 1, CRITICAL) actually lives. Detector reports clean on PnL-calc commits = false-negative in safety net. FORGE cross-check AGREES with VIGIL verdict. Two valid fix paths; Mike decides which. | `M214` | 23.0h | add_kraken_sync_path — add scripts/kraken-sync.py to registry files[] with registry_id:1, keep 'canonical SOUL.md §1 mirror' wording, full coverage (recommended; mechanically small; closes false-negative class) · narrow_contract_wording — leave registry as-is but rewrite PR body + docs to explicitly scope detector to {micro-gate-v3.py, lifecycle.py} only, open tracking issue for full SOUL.md §1 parity (smaller Round 2 diff but leaves known gap open) |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
