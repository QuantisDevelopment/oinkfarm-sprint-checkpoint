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
| Apr 24, 22:34 CEST | `REVIEW_POSTED` | `M43` | vigil | M43 review by vigil — REVISE (8.35) |
| Apr 24, 22:32 CEST | `SPRINT_NOTE` | `M201` | anvil | GUARDIAN R2 PASS 9.55 acknowledged (review posted 20:14:02Z, evt_20260424T201402Z_000001). Dimensions: schema=9, formula=10, migration=10, p |
| Apr 24, 22:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 22:21 CEST | `REVIEW_POSTED` | `M219` | vigil | M219 review by vigil — REVISE (6.2) |
| Apr 24, 22:13 CEST | `REVIEW_POSTED` | `M46` | vigil | M46 review by vigil — PASS (9.85) |
| Apr 24, 22:13 CEST | `SPRINT_NOTE` | `M201` | anvil | VIGIL R3 PASS 9.95 acknowledged (review posted 20:08:02Z, evt_20260424T200802Z_000001). Delta +0.35 vs R2 9.60. Carry-forward: Spec 10/10, R |
| Apr 24, 22:13 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 22:08 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — PASS (9.95) |
| Apr 24, 21:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 21:52 CEST | `SPRINT_NOTE` | `M201` | anvil | 19:52Z cron tick. Window 19:32Z→19:52Z: guardian heartbeat 19:33Z + hermes artifact 19:40Z, zero reviewer verdicts on my track. M201 R3 @f89 |
| Apr 24, 21:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 21:32 CEST | `SPRINT_NOTE` | `M201` | anvil | 19:32Z cron tick. Clean window 19:12Z→19:32Z: zero events on any track. M201 R3 @f89b2ecc now 288min post-push (≈4h48m), 159min post-nudge.  |
| Apr 24, 21:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 21:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 19:12Z cron tick. Clean window 18:53Z→19:12Z: guardian heartbeat 18:58Z + hermes artifact 19:03Z, zero reviewer verdicts on my track. M201 R |
| Apr 24, 20:53 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 20:53 CEST | `SPRINT_NOTE` | `M201` | anvil | 18:52Z cron tick. Clean window 18:32Z→18:52Z: zero new events on any track. M201 R3 @f89b2ecc now 248min post-push, 119min (≈2h) post-nudge. |
| Apr 24, 20:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 20:32 CEST | `SPRINT_NOTE` | `M201` | anvil | 18:32Z cron tick. Clean window — guardian heartbeat 18:28Z but no verdict. M201 R3 228min post-push, 99min post-nudge. Friday freeze gates M |
| Apr 24, 20:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 20:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 18:12Z cron tick. Scan window 17:53Z→18:12Z clean: 0 reviewer verdicts on my track. M201 R3 at f89b2ecc 208min post-push, 79min post-nudge.  |
| Apr 24, 19:52 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 19:52 CEST | `SPRINT_NOTE` | `M201` | anvil | 17:52Z cron tick. Scan window 17:33Z→17:52Z clean: 0 reviewer verdicts. M201 R3 at f89b2ecc now 188min post-push, 59min post-nudge. No re-nu |
| Apr 24, 19:32 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 19:32 CEST | `SPRINT_NOTE` | `M201` | anvil | 17:32Z cron tick. Scan window 17:12Z→17:32Z clean on my track. M201 R3 at f89b2ecc now 168min post-push, 39min post-nudge (SPRINT_NOTE evt_2 |
| Apr 24, 19:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 19:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 17:12Z cron tick. Scan window 16:53Z→17:12Z clean on my track (0 REVIEW_POSTED, 0 PROPOSAL_APPROVED, 0 DECISION_NEEDED, 0 BLOCKED for M201). |
| Apr 24, 18:53 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 18:53 CEST | `SPRINT_NOTE` | `M201` | anvil | 16:52Z cron tick + POLITE NUDGE to VIGIL R3 / GUARDIAN R2 on M201. Scan window 16:13Z→16:52Z: 0 reviewer verdicts on my track. Unrelated in- |
| Apr 24, 18:12 CEST | `AGENT_HEARTBEAT` | `M201` | anvil | anvil heartbeat — M201 |
| Apr 24, 18:12 CEST | `SPRINT_NOTE` | `M201` | anvil | 16:12Z cron tick. Scan window 15:52Z→16:12Z clean: 0 REVIEW_POSTED, 0 PROPOSAL_APPROVED, 0 DECISION_NEEDED, 0 BLOCKED. M201 R3 awaiting VIGI |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-OF214-REGISTRY-1` | VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calculate_blended_pnl (SOUL.md §1 row 1, CRITICAL) actually lives. Detector reports clean on PnL-calc commits = false-negative in safety net. FORGE cross-check AGREES with VIGIL verdict. Two valid fix paths; Mike decides which. | `M214` | 19.9h | add_kraken_sync_path — add scripts/kraken-sync.py to registry files[] with registry_id:1, keep 'canonical SOUL.md §1 mirror' wording, full coverage (recommended; mechanically small; closes false-negative class) · narrow_contract_wording — leave registry as-is but rewrite PR body + docs to explicitly scope detector to {micro-gate-v3.py, lifecycle.py} only, open tracking issue for full SOUL.md §1 parity (smaller Round 2 diff but leaves known gap open) |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
