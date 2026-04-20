# OinkFarm Implementation Foresight Sprint — Archive

Human-readable per-task, per-wave, per-phase, and per-event archive. For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).

## Event stream integrity

- **Total events:** 10
- **Last 24h:** 10 (rate 0.42/h)
- **Schema:** v1.0
- **Source:** lib
- **Monotonic:** ✓ ok

## 🔴 Live now

### Last 1 hour (10 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 15:15 CEST | `SPRINT_NOTE` | `—` | hermes | Wave 2 Phase B kickoff — B8 proposal submitted by ANVIL, VIGIL review incoming. |
| Apr 20, 15:00 CEST | `BLOCKED` | `B3` | anvil | B3 BLOCKED — waiting_for_upstream_task |
| Apr 20, 14:40 CEST | `REVIEW_POSTED` | `B8` | vigil | B8 review by vigil — PASS (9.4) |
| Apr 20, 14:30 CEST | `CANARY_PASS` | `B1` | guardian | B1 canary PASS |
| Apr 20, 14:10 CEST | `CANARY_STARTED` | `B1` | guardian | B1 canary started |
| Apr 20, 14:05 CEST | `AGENT_HEARTBEAT` | `—` | anvil | anvil heartbeat — B8 |
| Apr 20, 14:00 CEST | `MERGED` | `B1` | anvil | B1 merged via PR #142 @abcd123 |
| Apr 20, 13:30 CEST | `DECISION_NEEDED` | `B2` | hermes | B2 Mike gate: PostgreSQL hosting — same server or separate? |
| Apr 20, 13:00 CEST | `PROPOSAL_READY` | `B8` | anvil | B8 proposal ready |
| Apr 20, 12:30 CEST | `TASK_PLANNED` | `B8` | forge | B8 plan published |

### Last 4 hours (10 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 15:15 CEST | `SPRINT_NOTE` | `—` | hermes | Wave 2 Phase B kickoff — B8 proposal submitted by ANVIL, VIGIL review incoming. |
| Apr 20, 15:00 CEST | `BLOCKED` | `B3` | anvil | B3 BLOCKED — waiting_for_upstream_task |
| Apr 20, 14:40 CEST | `REVIEW_POSTED` | `B8` | vigil | B8 review by vigil — PASS (9.4) |
| Apr 20, 14:30 CEST | `CANARY_PASS` | `B1` | guardian | B1 canary PASS |
| Apr 20, 14:10 CEST | `CANARY_STARTED` | `B1` | guardian | B1 canary started |
| Apr 20, 14:05 CEST | `AGENT_HEARTBEAT` | `—` | anvil | anvil heartbeat — B8 |
| Apr 20, 14:00 CEST | `MERGED` | `B1` | anvil | B1 merged via PR #142 @abcd123 |
| Apr 20, 13:30 CEST | `DECISION_NEEDED` | `B2` | hermes | B2 Mike gate: PostgreSQL hosting — same server or separate? |
| Apr 20, 13:00 CEST | `PROPOSAL_READY` | `B8` | anvil | B8 proposal ready |
| Apr 20, 12:30 CEST | `TASK_PLANNED` | `B8` | forge | B8 plan published |

### Last 24 hours (10 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 15:15 CEST | `SPRINT_NOTE` | `—` | hermes | Wave 2 Phase B kickoff — B8 proposal submitted by ANVIL, VIGIL review incoming. |
| Apr 20, 15:00 CEST | `BLOCKED` | `B3` | anvil | B3 BLOCKED — waiting_for_upstream_task |
| Apr 20, 14:40 CEST | `REVIEW_POSTED` | `B8` | vigil | B8 review by vigil — PASS (9.4) |
| Apr 20, 14:30 CEST | `CANARY_PASS` | `B1` | guardian | B1 canary PASS |
| Apr 20, 14:10 CEST | `CANARY_STARTED` | `B1` | guardian | B1 canary started |
| Apr 20, 14:05 CEST | `AGENT_HEARTBEAT` | `—` | anvil | anvil heartbeat — B8 |
| Apr 20, 14:00 CEST | `MERGED` | `B1` | anvil | B1 merged via PR #142 @abcd123 |
| Apr 20, 13:30 CEST | `DECISION_NEEDED` | `B2` | hermes | B2 Mike gate: PostgreSQL hosting — same server or separate? |
| Apr 20, 13:00 CEST | `PROPOSAL_READY` | `B8` | anvil | B8 proposal ready |
| Apr 20, 12:30 CEST | `TASK_PLANNED` | `B8` | forge | B8 plan published |

## 🧭 Needs Mike

| Question ID | Question | Task | Age | Options | Gate |
|---|---|---|---|---|---|
| `Q-B2-1` | PostgreSQL hosting — same server or separate? | `B2` | just now | same-server · separate-vm | phase-b |

## 🔍 Missing evidence

_✓ No lint gaps._

## 🫀 Freshness by agent

| Agent | Last event | Type | Task | Staleness | Events |
|---|---|---|---|---|---|
| 🪽 **Hermes** | Apr 20, 15:15 CEST | `SPRINT_NOTE` | `—` | 🟢 fresh | 2 |
| ⚒️ **ANVIL** | Apr 20, 15:00 CEST | `BLOCKED` | `B8` | 🟢 fresh | 4 |
| 🔍 **VIGIL** | Apr 20, 14:40 CEST | `REVIEW_POSTED` | `B8` | 🟢 fresh | 1 |
| 🛡️ **GUARDIAN** | Apr 20, 14:30 CEST | `CANARY_PASS` | `B1` | 🟢 fresh | 2 |
| 🔥 **FORGE** | Apr 20, 12:30 CEST | `TASK_PLANNED` | `B8` | 🟢 fresh | 1 |

## What's live now

| | |
|---|---|
| **Phase A** | ✅ COMPLETE — 11/11 tasks shipped, canaries PASS |
| **Phase B** | 🚧 IN FLIGHT — B1 proposal drafted |
| **Phase C** | 📐 SCOPED — 7 tasks, detailed plans after Phase B |
| **Heavy Hybrid** | 🗺️ ROADMAP DELIVERED — Q-HH-1..6 resolved autonomously |
| **Prod DB** | 1,407 signals · 0 NULL invariants · 0 orphans · 10 PRs merged |

## Phases

| Phase | Focus | Page |
|---|---|---|
| [Phase A](phases/phase-a.md) | Data Truth — 11 tasks, complete retrospective | ✅ DONE |
| [Phase B](phases/phase-b.md) | Infrastructure — PostgreSQL + decomposed services | 🚧 IN FLIGHT |
| [Phase C](phases/phase-c.md) | Observability — 55+ KPIs, anomaly detection | 📐 SCOPED |
| [Heavy Hybrid](phases/heavy-hybrid.md) | Long-horizon roadmap + Q-HH decisions | 🗺️ DELIVERED |

## Waves

| Wave | Focus | Tasks | Status |
|---|---|---|---|
| [Wave 1 (Phase A)](waves/wave-1.md) | Core schema & formula primitives | [A1](tasks/A1-signal-events-schema.md) · [A2](tasks/A2-remaining-pct-model.md) · [A3](tasks/A3-auto-filled-at.md) | 0/3 shipped |
| [Wave 2 (Phase A)](waves/wave-2.md) | Lifecycle accuracy & phantom-trade prevention | [A4](tasks/A4-partially-closed-status.md) · [A7](tasks/A7-update-new-detection.md) · [A5](tasks/A5-confidence-scoring.md) | 0/3 shipped |
| [Wave 3 (Phase A)](waves/wave-3.md) | Metadata enrichment & ghost closure | [A6](tasks/A6-ghost-closure-flag.md) · [A8](tasks/A8-conditional-sl-type.md) · [A9](tasks/A9-denomination-multiplier.md) · [A11](tasks/A11-leverage-source-tracking.md) | 0/4 shipped |
| [Wave 4 (Phase A)](waves/wave-4.md) | Database merge | [A10](tasks/A10-database-merge.md) | 0/1 shipped |
| [Wave B1 (Phase B)](waves/wave-b1.md) | Database abstraction layer (`oink_db.py`) | [B1](tasks/B1-db-abstraction-layer.md) | 🚧 IN FLIGHT |

## Tasks

| Task | Name | Tier | Wave | Status | Canary |
|---|---|---|---|---|---|
| [A1](tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | 1 | ⏳ NOT STARTED | — |
| [A2](tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | 1 | ⏳ NOT STARTED | — |
| [A3](tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | 1 | ⏳ NOT STARTED | — |
| [A4](tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 2 | ⏳ NOT STARTED | — |
| [A5](tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | 2 | ⏳ NOT STARTED | — |
| [A6](tasks/A6-ghost-closure-flag.md) | Ghost Closure Confirmation Flag | 🟡 STANDARD | 3 | ⏳ NOT STARTED | — |
| [A7](tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 2 | ⏳ NOT STARTED | — |
| [A8](tasks/A8-conditional-sl-type.md) | Conditional SL Type Field | 🟡 STANDARD | 3 | ⏳ NOT STARTED | — |
| [A9](tasks/A9-denomination-multiplier.md) | Denomination Multiplier Table (1000x-prefixed symbols) | 🟢 LIGHTWEIGHT | 3 | ⏳ NOT STARTED | — |
| [A10](tasks/A10-database-merge.md) | Database Merge (test → prod, council-approved) | 🔴 CRITICAL | 4 | ⏳ NOT STARTED | — |
| [A11](tasks/A11-leverage-source-tracking.md) | Leverage Source Tracking | 🟢 LIGHTWEIGHT | 3 | ⏳ NOT STARTED | — |
| [B1](tasks/B1-db-abstraction-layer.md) | Database Abstraction Layer (sqlite3 → oink_db.py) | 🔴 CRITICAL | B1 | ✅ DONE | PASS |
| `B2` | B2 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B3` | B3 | 🟡 STANDARD | — | 🛑 BLOCKED | — |
| `B8` | B8 | 🟡 STANDARD | — | 👀 PR REVIEW | — |

## Event log

- [Event index](events/README.md) — chronological feed (newest first within each day)

## Agents

| Emoji | Name | Role |
|---|---|---|
| 🪽 | Hermes | Sprint Orchestrator |
| ⚒️ | ANVIL | Implementation Lead |
| 🔍 | VIGIL | Code Review + Scoring |
| 🛡️ | GUARDIAN | Data Integrity + Canary |
| 🔥 | FORGE | Technical Execution Planner |

## Conventions

- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT (per Arbiter-Oink Phase 4 governance)
- **Auto-escalation:** if a diff touches one of the 7 Financial Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.
- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → CODE → PR_REVIEW → CANARY → DONE
- **Timestamps** are rendered in CEST (UTC+2).

---

*1/15 tasks DONE · Last auto-regenerated: 12:43 CEST on 20 Apr 2026 · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint)*
