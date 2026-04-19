# Phase C — Mature Observability — Scoped

**Status:** 📐 SCOPED — detailed task plans after Phase B quality gate passes  
**Goal:** Build measurement, monitoring, and operational sophistication on the trusted substrate established by Phase A (data truth) and Phase B (PostgreSQL + decomposed services + Redis Streams).  
**Source:** [`PHASE-C-SUMMARY.md`](../../raw-artifacts/forge/plans/PHASE-C-SUMMARY.md)

Phase C does NOT introduce new data flows or infrastructure — it adds intelligence on top of existing flows.

## Phase C Prerequisites (Phase B Quality Gate)

| Gate | Verification | From |
|---|---|---|
| PostgreSQL is authoritative | All reads/writes via PostgreSQL | B4 |
| W1 immutable records exist | Origin records INSERT-only | B9 |
| W3 reproduces correct PnL | `calculate_blended_pnl()` parity | B10 |
| Redis Streams operational | Inter-service messages w/ replay | B12 |
| Service boundaries established | `signal_router.py` ≤ 2,800 LOC | B5-B8 |
| W4 trace layer expanded | 18 timestamps beyond Phase A's 4 | B11 |
| Data retention operational | `price_history` partitioned w/ retention | B14 |

## C-Task Inventory (7 tasks)

| Task | Name | Tier | Depends On | Est. |
|---|---|---|---|---|
| **C1** | KPI expansion to ~55-65 | 🟡 STANDARD | B4, B11 | 3-4d |
| **C2** | Confidence-based routing (provisional path) | 🟡 STANDARD | B12, B8 | 2-3d |
| **C3** | Urgency classification (SCALP/DAYTRADE/SWING/POSITION) | 🟡 STANDARD | C2 | 1-2d |
| **C4** | Differentiated SLA monitoring | 🟡 STANDARD | C3, B11 | 2-3d |
| **C5** | Full anomaly detection (Z-score + pattern) | 🟡 STANDARD | C1 + 30d data | 2-3d |
| **C6** | Per-trader metrics (Bayesian shrinkage) | 🟡 STANDARD | C1, B10 | 2-3d |
| **C7** | Chaos testing suite | 🟢 LIGHTWEIGHT | B13, C1 | 1-2d |

**Total estimated effort:** 14-22 days of dev work (not all sequential)

## C1 — KPI Expansion (Lead Task)

### Current State (Phase A)
~15-20 KPIs from DOC7: signals/hour, parse success rate, gate rejection rate, SL/TP detection events, active signal count, false closure rate, gateway uptime, DB write success rate.

### C1 Target (~55-65 KPIs)
- **Per-provider (20+):** signals/day, extraction accuracy, latency, error rate, confidence distribution — all by provider (Cornix, WG Bot, Chroma, LLM).
- **Per-trader (15+):** win rate w/ Bayesian CI, average ROI, hold duration, signal frequency, TP-hit rate by level.
- **Infrastructure (10+):** PostgreSQL query latency (p50/p95/p99), Redis consumer lag, event store throughput, W1 immutability violations, service restart count.
- **Data quality (10+):** NULL rate per column, event coverage, PnL accuracy (derived vs stored), duplicate detection rate, quarantine resolution rate.

## Mike Gates in Phase C

- **Q-HH-5:** Confidence routing — hard reject below threshold, or soft flag? **DECIDED (Hermes):** soft flag in Phase B, hard reject in Phase C.

## Next

→ Phase C detailed plans will be drafted once Phase B's B11 (W4 trace) and B4 (PostgreSQL cutover) ship.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
