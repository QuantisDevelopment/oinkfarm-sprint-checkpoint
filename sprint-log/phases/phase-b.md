# Phase B — Infrastructure Migration — Overview

**Status:** 🚧 IN FLIGHT — B1 Phase 0 proposal drafted  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Source:** [`PHASE-B-SUMMARY.md`](../../raw-artifacts/forge/plans/PHASE-B-SUMMARY.md) · [`HEAVY-HYBRID-ROADMAP.md`](../../raw-artifacts/forge/plans/HEAVY-HYBRID-ROADMAP.md)

## Scope

Phase B has 15 Arbiter elements. FORGE has planned all 15 across 4 waves. Wave 1 (B1-B5) is the critical path; B1 in flight, B2-B5 planned.

## All 15 Planned B-Tasks

| Task | Name | Tier | Wave | Depends On | Status |
|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | DB abstraction layer (oink_db.py) | 🔴 CRITICAL | B1 | A-complete | 🧪 CANARY |
| B2 | PostgreSQL schema + migration | 🔴 CRITICAL | B1 | B1 | 📋 PLANNED |
| B3 | Parallel-write verification | 🔴 CRITICAL | B1 | B2 | 📋 PLANNED |
| B4 | PostgreSQL cutover (Mike gate) | 🔴 CRITICAL | B1 | B3 + Mike | 📋 PLANNED |
| B5 | Emitter extraction | 🟡 STANDARD | B1 | None (parallel w/ B3) | 📋 PLANNED |
| B6 | Cornix + Chroma parser extraction | 🟡 STANDARD | B2 | B5 | 📋 PLANNED |
| B7 | WG Bot parser extraction | 🟡 STANDARD | B2 | B5 | 📋 PLANNED |
| B8 | Router extraction (classify, dedup) | 🟡 STANDARD | B2 | B6, B7 | 📋 PLANNED |
| B9 | W1 Immutable signal records | 🔴 CRITICAL | B3 | B4 | ⏳ DEFERRED |
| B10 | W3 Materialized views + PnL continuity | 🟡 STANDARD | B3 | B9 | ⏳ DEFERRED |
| B11 | W4 Full trace layer (18 timestamps) | 🟡 STANDARD | B3 | B4 | ⏳ DEFERRED |
| B12 | Redis Streams transport (8 topics) | 🔴 CRITICAL | B4 | B4, B8 | ⏳ DEFERRED |
| B13 | Docker Compose deployment | 🟡 STANDARD | B4 | B8, B12 | ⏳ DEFERRED |
| B14 | TimescaleDB for price_history | 🟢 LIGHTWEIGHT | B4 | B4 | ⏳ DEFERRED |
| B15 | Schema versioning + DLQ/replay | 🟡 STANDARD | B4 | B12 | ⏳ DEFERRED |

## Dependency Graph

```
B1 → B2 → B3 (7-14d elapsed) → B4 (Mike gate)
                                  │
B5 (emitter) ── parallel w/ B3 ───┘
                                  │
B5 → B6, B7 → B8 ────────────────┤
                                  │
B4 → B9 → B10 ───────────────────┤
B4 → B11 ────────────────────────┤
B4 + B8 → B12 → B15 ─────────────┤
B8 + B12 → B13 ──────────────────┤
B4 → B14 ────────────────────────┘
```

## Estimated Timeline

- **Wave 1 (B1-B5):** ~13-23 days elapsed (B3 dominates the timeline)
- **Wave 2 (B6-B8):** ~5-8 days, parallel with B3
- **Wave 3 (B9-B11):** ~7-10 days after B4 cutover
- **Wave 4 (B12-B15):** ~8-13 days, parallel tracks
- **Critical path:** B1→B2→B3→B4→B9→B10 (~6-9 weeks)

## Mike Gates

- **Q-B1-1:** PostgreSQL driver — psycopg3 vs psycopg2
- **Q-B1-2:** `oink_db.py` location — canonical vs per-repo
- **Q-B2-1:** PostgreSQL hosting — same server or separate?
- **Q-B2-3:** TimescaleDB now or later (B14)?
- **Q-B3-2:** Minimum verification window — 7 or 14 days?
- **B4-APPROVE:** Cutover requires Mike's explicit go-ahead

## Next

→ [B1 task page](../tasks/B1-db-abstraction-layer.md) — DB abstraction layer, proposal in review.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
