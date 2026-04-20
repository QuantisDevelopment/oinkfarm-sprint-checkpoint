# Phase B — Infrastructure Migration

**Status:** 1/4 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#142](https://github.com/QuantisDevelopment/oinkfarm/pull/142) | Apr 20, 14:30 CEST · `CANARY_PASS` | anvil · guardian |
| [B2](../tasks/B2-b2.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 13:30 CEST · `DECISION_NEEDED` | hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🛑 BLOCKED | — | — | Apr 20, 15:00 CEST · `BLOCKED` | anvil |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | 👀 PR REVIEW | — | — | Apr 20, 14:40 CEST · `REVIEW_POSTED` | anvil · forge · vigil |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 15:00 CEST | `BLOCKED` | `B3` | anvil | B3 BLOCKED — waiting_for_upstream_task |
| Apr 20, 14:40 CEST | `REVIEW_POSTED` | `B8` | vigil | B8 review by vigil — PASS (9.4) |
| Apr 20, 14:30 CEST | `CANARY_PASS` | `B1` | guardian | B1 canary PASS |
| Apr 20, 14:10 CEST | `CANARY_STARTED` | `B1` | guardian | B1 canary started |
| Apr 20, 14:05 CEST | `AGENT_HEARTBEAT` | `—` | anvil | anvil heartbeat — B8 |
| Apr 20, 14:00 CEST | `MERGED` | `B1` | anvil | B1 merged via PR #142 @abcd123 |
| Apr 20, 13:30 CEST | `DECISION_NEEDED` | `B2` | hermes | B2 Mike gate: PostgreSQL hosting — same server or separate? |
| Apr 20, 13:00 CEST | `PROPOSAL_READY` | `B8` | anvil | B8 proposal ready |
| Apr 20, 12:30 CEST | `TASK_PLANNED` | `B8` | forge | B8 plan published |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-B2-1` | PostgreSQL hosting — same server or separate? | `B2` | just now | same-server · separate-vm |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
