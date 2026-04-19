# HEAVY HYBRID — Long-Horizon Roadmap

**Status:** 🗺️ ROADMAP DELIVERED — all Phase A/B/C planning scoped  
**Source:** [`HEAVY-HYBRID-ROADMAP.md`](../../raw-artifacts/forge/plans/HEAVY-HYBRID-ROADMAP.md)  
**Authorization:** Mike — continuous execution Phase A → Phase B → Heavy Hybrid (autonomous, "full authority, push till done")

## Master Architecture

```
Phase A (Data Truth)     — Fix signal-data correctness on SQLite foundation ✅ DONE
Phase B (Infrastructure) — PostgreSQL + decompose God Object + Redis Streams 🚧 IN FLIGHT
Phase C (Observability)  — Mature KPI, anomaly detection, SLA monitoring 📐 SCOPED
Phase D (Algo/Execution) — DEFERRED until data-trust + scale-architecture gates pass
```

## Current Status

| Phase | Tasks | Planned | Merged | Status |
|---|---|---|---|---|
| **A** | A1-A11 | 11/11 | 11/11 ✅ | **COMPLETE** |
| **B Wave 1** | B1-B5 | 5/5 | 0/5 (B1 in flight) | **ACTIVE** |
| **B Wave 2** | B6-B8 | 3/3 | 0/3 | **PLANNED** |
| **B Wave 3** | B9-B11 | 3/3 | 0/3 | **PLANNED** |
| **B Wave 4** | B12-B15 | 4/4 | 0/4 | **PLANNED** |
| **C** | C1-C7 | Summary scoped | 0/7 | **SCOPED** |
| **D** | — | — | — | **DEFERRED** |

## Phase D Gate Prerequisites

Phase D does not begin until ALL prerequisites are met:

| Prerequisite | Threshold | From |
|---|---|---|
| Event history authoritative | W1-W2 on PostgreSQL, >99% event coverage | B9 |
| Partial-close accounting correct | ROI error <0.5pp on 100-signal audit | A2 ✅ |
| filled_at reliable | <5% NULL for FILLED signals | A3 ✅ |
| Extraction accuracy measured | System false positive rate <5% | A5, C1 |
| Write verification exists | Every write has verification | A (events) ✅ |
| Trace layer exists | W4 on PostgreSQL with SLA monitoring | B11, C4 |
| Statistical monitoring stable | 55+ KPIs with anomaly detection, 90+ day history | C1, C5 |

## Parallelism Map

| Time period | Track 1 (PostgreSQL) | Track 2 (Decomposition) | Track 3 (Data Layer) |
|---|---|---|---|
| Week 1-2 | B1 → B2 | B5 (emitter) | — |
| Week 2-4 | B3 (7-14d verification) | B6 → B7 → B8 | — |
| Week 4-5 | B4 (cutover + Mike gate) | — | — |
| Week 5-7 | B14 (TimescaleDB) | B12 (Redis Streams) | B9 → B10 |
| Week 7-8 | — | B13 (Docker), B15 (DLQ) | B11 (W4 trace) |
| Week 8+ | — | — | C1-C7 (observability) |

**Estimated total elapsed:** 8-12 weeks for Phase B + Phase C start  
**Critical path:** B1→B2→B3→B4→B9→B10 (PostgreSQL track)  
**Parallelism saves ~3-4 weeks** by running decomposition during B3 verification

## Hermes Autonomous Decisions (Q-HH-1 through Q-HH-6)

Mike granted Hermes "full authority, push till done" — the following long-horizon questions were resolved without blocking on human approval:

| ID | Question | Decision | Rationale |
|---|---|---|---|
| **Q-HH-1** | Redis hosting — same server or separate? | **Same server initially** | Lowest-friction start; separate once QPS > 5k or RAM pressure appears. |
| **Q-HH-2** | Redis Streams retention policy | **48h retention + AOF everysec** | Covers 24h canary windows + 1 day replay, AOF bounds data loss to <1s. |
| **Q-HH-3** | Docker Compose — single host or multi-host? | **Single-host Compose initially** | Multi-host prep deferred to B13+. Matches "same server" Redis choice. |
| **Q-HH-4** | W1 enforcement level | **DB-level REVOKE UPDATE on origin table** | Stronger guarantee than application-level guard; matches Arbiter W1 intent. |
| **Q-HH-5** | Confidence routing rigor | **Soft flag in Phase B, hard reject in Phase C** | Phase B preserves existing flow; Phase C has the 30d KPI history to set thresholds safely. |
| **Q-HH-6** | Phase D entry gate authority | **Hermes + 2-council (OinkV + GUARDIAN)** | Mirrors A10 council pattern (OinkV + OinkDB) which already shipped cleanly. |

## Organizational Commitments

- **No Phase D planning** before Phase C quality gate passes.
- **No scope creep** — Arbiter-Oink V3 spec is the source of truth.
- **All merges continue to require Hermes parallel review + GUARDIAN canary** for 🔴/🟡 tasks.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
