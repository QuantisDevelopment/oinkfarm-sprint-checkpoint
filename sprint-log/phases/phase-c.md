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
| [C1](../tasks/C1-c1.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 26, 08:53 CEST · `TASK_PLANNED` | forge |
| [C2](../tasks/C2-c2.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 22, 13:34 CEST · `TASK_PLANNED` | forge · hermes |
| [C3](../tasks/C3-c3.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 24, 18:15 CEST · `DECISION_NEEDED` | forge |
| [C4](../tasks/C4-c4.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 26, 08:53 CEST · `TASK_PLANNED` | forge |
| [C6](../tasks/C6-c6.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 26, 08:53 CEST · `TASK_PLANNED` | forge |

## Waves

_No waves yet for this phase._

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 26, 08:53 CEST | `DECISION_NEEDED` | `C1` | forge | C1 Mike gate: How should Phase C dispose of the 21 already-existing terminal-incoherent rows on the live substrate (resolved status with NUL |
| Apr 26, 08:53 CEST | `TASK_PLANNED` | `C1` | forge | C1 plan published |
| Apr 26, 08:53 CEST | `TASK_PLANNED` | `C4` | forge | C4 plan published |
| Apr 26, 08:53 CEST | `TASK_PLANNED` | `C6` | forge | C6 plan published |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-C3-2` | C3 backfill urgency_source semantics: when backfill uses the identical deterministic classifier as write-time, should backfilled rows stamp the natural evidence source (e.g. 'text_keyword' or 'tp_distance') with a separate backfill flag, or stamp a blanket 'backfill_heuristic' to distinguish post-hoc classification from write-time? Currently C3 §3 lists 'backfill_heuristic' as an allowed enum value, but §5.5.3 mandates the identical classifier is used for both paths. These two statements are in tension for audit/drift semantics downstream (C4/C6 breach history, KPI segmentation). | `C3` | 39.3h | A: keep 'backfill_heuristic' as the stamped urgency_source for all backfilled rows, dropping natural-source fidelity for those rows (simple audit flag, but loses evidence chain) · B: backfilled rows stamp the natural evidence source (e.g. 'text_keyword'), and 'backfill_heuristic' is removed from the enum; a separate immutable 'classified_at_backfill' boolean column distinguishes post-hoc rows (preserves evidence chain, adds one column) · C: backfilled rows stamp the natural evidence source AND backfill adds a second companion column 'urgency_classified_phase' ∈ {ingest, backfill} — keeps enum pure, makes provenance explicit at the row level |
| `Q-C1-INC-1` | How should Phase C dispose of the 21 already-existing terminal-incoherent rows on the live substrate (resolved status with NULL exit_price/final_roi)? Live count: 17 wg_march_audit, 3 legacy_backfill, 1 trader_close. INV-18 read-side rule (do not silently include in resolved cohorts) holds regardless; this gate is purely about upstream disposition of the existing 21. | `C1` | 41m | A: repair upstream before C1/C4/C6 ship · B: ship Phase C with INV-18 fail-closed warning, dashboards visibly carry terminal_incoherent_total>0 until separate repair lands (FORGE recommends) · C: quarantine the 21 rows permanently into unresolved_due_to_missing_terminal_fields analytical bucket as legacy debt |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
