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
| [C1](../tasks/C1-c1.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 22, 14:35 CEST · `TASK_PLANNED` | forge |
| [C2](../tasks/C2-c2.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 22, 13:34 CEST · `TASK_PLANNED` | forge · hermes |
| [C3](../tasks/C3-c3.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 24, 18:15 CEST · `DECISION_NEEDED` | forge |
| [C4](../tasks/C4-c4.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 22, 14:08 CEST · `TASK_PLANNED` | forge |
| [C6](../tasks/C6-c6.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 22, 13:03 CEST · `TASK_PLANNED` | forge |

## Waves

_No waves yet for this phase._

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 24, 18:15 CEST | `DECISION_NEEDED` | `C3` | forge | C3 Mike gate: C3 backfill urgency_source semantics: when backfill uses the identical deterministic classifier as write-time, should backfill |
| Apr 24, 07:14 CEST | `AGENT_HEARTBEAT` | `—` | forge | forge heartbeat — sprint_poke_response |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-C3-2` | C3 backfill urgency_source semantics: when backfill uses the identical deterministic classifier as write-time, should backfilled rows stamp the natural evidence source (e.g. 'text_keyword' or 'tp_distance') with a separate backfill flag, or stamp a blanket 'backfill_heuristic' to distinguish post-hoc classification from write-time? Currently C3 §3 lists 'backfill_heuristic' as an allowed enum value, but §5.5.3 mandates the identical classifier is used for both paths. These two statements are in tension for audit/drift semantics downstream (C4/C6 breach history, KPI segmentation). | `C3` | 12.6h | A: keep 'backfill_heuristic' as the stamped urgency_source for all backfilled rows, dropping natural-source fidelity for those rows (simple audit flag, but loses evidence chain) · B: backfilled rows stamp the natural evidence source (e.g. 'text_keyword'), and 'backfill_heuristic' is removed from the enum; a separate immutable 'classified_at_backfill' boolean column distinguishes post-hoc rows (preserves evidence chain, adds one column) · C: backfilled rows stamp the natural evidence source AND backfill adds a second companion column 'urgency_classified_phase' ∈ {ingest, backfill} — keeps enum pure, makes provenance explicit at the row level |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
