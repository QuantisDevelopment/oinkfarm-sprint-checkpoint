# Phase C — Mature Observability

## What is Phase C?

> Phase C builds mature observability on top of Phase A+B — dashboards, alerting, SLOs, and confidence-routing so the trading loop can be measured and tuned. Scoped but not yet started.

**Status:** 0/5 tasks shipped  
**Goal:** Build measurement, monitoring, and operational sophistication on top of Phase A+B.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [C1](../tasks/C1-c1.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 21, 17:05 CEST · `TASK_PLANNED` | forge |
| [C2](../tasks/C2-c2.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 21, 17:05 CEST · `DECISION_NEEDED` | forge · hermes |
| [C3](../tasks/C3-c3.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 21, 17:05 CEST · `TASK_PLANNED` | forge |
| [C4](../tasks/C4-c4.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 21, 17:05 CEST · `TASK_PLANNED` | forge |
| [C6](../tasks/C6-c6.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 21, 17:05 CEST · `TASK_PLANNED` | forge |

## Waves

_No waves yet for this phase._

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 21, 17:27 CEST | `SPRINT_NOTE` | `—` | forge | Priority correction applied: Mike's 2026-04-21 18:00 UTC instruction supersedes the 17:05 background-mode pivot. Heavy Hybrid restored to fu |
| Apr 21, 17:13 CEST | `AGENT_HEARTBEAT` | `—` | forge | forge heartbeat — Heavy Hybrid background mode after C1/C2/C3/C4/C6 plan completion |
| Apr 21, 17:07 CEST | `SPRINT_NOTE` | `—` | forge | AGGRESSIVE scope C-plans delivered (C1, C2, C3, C4, C6 v1). C5 and C7 deferred post-launch per 2026-04-21 14:35 UTC scope lock. Q-HH-5 re-fl |
| Apr 21, 17:05 CEST | `TASK_PLANNED` | `C1` | forge | C1 plan published |
| Apr 21, 17:05 CEST | `TASK_PLANNED` | `C2` | forge | C2 plan published |
| Apr 21, 17:05 CEST | `TASK_PLANNED` | `C3` | forge | C3 plan published |
| Apr 21, 17:05 CEST | `TASK_PLANNED` | `C4` | forge | C4 plan published |
| Apr 21, 17:05 CEST | `TASK_PLANNED` | `C6` | forge | C6 plan published |
| Apr 21, 17:05 CEST | `DECISION_NEEDED` | `C2` | forge | C2 Mike gate: For signals below the configured confidence threshold, should the system hard_reject them from the live lifecycle, or soft_fla |
| Apr 20, 23:18 CEST | `TASK_PLANNED` | `C2` | forge | C2 plan published |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `C2` | hermes | C2 decision: Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-HH-5` | For signals below the configured confidence threshold, should the system hard_reject them from the live lifecycle, or soft_flag_provisional them into a review queue? | `C2` | 23m | hard_reject · soft_flag_provisional |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
