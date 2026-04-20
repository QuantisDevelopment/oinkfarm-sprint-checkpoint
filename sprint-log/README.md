# OinkFarm Implementation Foresight Sprint — Archive

Human-readable per-task, per-wave, per-phase, and per-event archive. For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).

## Event stream integrity

- **Total events:** 283
- **Last 24h:** 156 (rate 6.5/h)
- **Schema:** v1.0
- **Source:** lib
- **Monotonic:** ✓ ok

## 🔴 Live now

### Last 1 hour (12 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 22:57 CEST | `SPRINT_NOTE` | `A171` | oinkv | Schema diag: no per-agent session-history cap key found. Per-agent contextPruning rejected; runtime only reads agents.defaults.contextPrunin |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Accept NULL filled_at on 84 historical closed signals as-is. No backfill. B2 PG migration preserves NULLs. No Phase A KPI uses  |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `A10` | hermes | A10 decision: A10 database merge shipped as PR #135 (commit 80f4fe0a) on 2026-04-19. Canary subsequently re-ran by GUARDIAN on 2026-04-20 pe |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: RECLASSIFIED as scheduled gate, not live blocker. B4 cutover approval will re-surface as a fresh DECISION_NEEDED when (a) B3 du |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: CHECK-only constraint (entry_price > 0). No PL/pgSQL trigger — REJECTED_AUDIT code path is dead. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Defer TimescaleDB to B14 (dedicated task). PG first, Timescale bolts on non-destructively when workload justifies. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at  |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B13` | hermes | B13 decision: Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B9` | hermes | B9 decision: signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFO |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `C2` | hermes | C2 decision: Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |
| Apr 20, 22:54 CEST | `BLOCKER_RESOLVED` | `A171` | hermes | A171 blocker cleared |
| Apr 20, 22:20 CEST | `SPRINT_NOTE` | `—` | hermes | Still quiet. The OinXtractor Task 171 design blocker OinkV raised at 17:58 UTC is now ~2h20m old and unresolved — OpenClaw won't accept the  |

### Last 4 hours (17 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 22:57 CEST | `SPRINT_NOTE` | `A171` | oinkv | Schema diag: no per-agent session-history cap key found. Per-agent contextPruning rejected; runtime only reads agents.defaults.contextPrunin |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Accept NULL filled_at on 84 historical closed signals as-is. No backfill. B2 PG migration preserves NULLs. No Phase A KPI uses  |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `A10` | hermes | A10 decision: A10 database merge shipped as PR #135 (commit 80f4fe0a) on 2026-04-19. Canary subsequently re-ran by GUARDIAN on 2026-04-20 pe |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: RECLASSIFIED as scheduled gate, not live blocker. B4 cutover approval will re-surface as a fresh DECISION_NEEDED when (a) B3 du |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: CHECK-only constraint (entry_price > 0). No PL/pgSQL trigger — REJECTED_AUDIT code path is dead. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Defer TimescaleDB to B14 (dedicated task). PG first, Timescale bolts on non-destructively when workload justifies. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at  |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B13` | hermes | B13 decision: Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B9` | hermes | B9 decision: signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFO |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `C2` | hermes | C2 decision: Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |
| Apr 20, 22:54 CEST | `BLOCKER_RESOLVED` | `A171` | hermes | A171 blocker cleared |
| Apr 20, 22:20 CEST | `SPRINT_NOTE` | `—` | hermes | Still quiet. The OinXtractor Task 171 design blocker OinkV raised at 17:58 UTC is now ~2h20m old and unresolved — OpenClaw won't accept the  |
| Apr 20, 21:43 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 20:37 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | hermes | OinkV just hit a blocker on Task 171 (the OinXtractor stateful retrieval-learning agent you approved for parallel execution this afternoon). |

### Last 24 hours (156 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 22:57 CEST | `SPRINT_NOTE` | `A171` | oinkv | Schema diag: no per-agent session-history cap key found. Per-agent contextPruning rejected; runtime only reads agents.defaults.contextPrunin |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Accept NULL filled_at on 84 historical closed signals as-is. No backfill. B2 PG migration preserves NULLs. No Phase A KPI uses  |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `A10` | hermes | A10 decision: A10 database merge shipped as PR #135 (commit 80f4fe0a) on 2026-04-19. Canary subsequently re-ran by GUARDIAN on 2026-04-20 pe |
| Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: RECLASSIFIED as scheduled gate, not live blocker. B4 cutover approval will re-surface as a fresh DECISION_NEEDED when (a) B3 du |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: CHECK-only constraint (entry_price > 0). No PL/pgSQL trigger — REJECTED_AUDIT code path is dead. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Defer TimescaleDB to B14 (dedicated task). PG first, Timescale bolts on non-destructively when workload justifies. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at  |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B13` | hermes | B13 decision: Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `B9` | hermes | B9 decision: signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFO |
| Apr 20, 22:54 CEST | `DECISION_RESOLVED` | `C2` | hermes | C2 decision: Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |
| Apr 20, 22:54 CEST | `BLOCKER_RESOLVED` | `A171` | hermes | A171 blocker cleared |
| Apr 20, 22:20 CEST | `SPRINT_NOTE` | `—` | hermes | Still quiet. The OinXtractor Task 171 design blocker OinkV raised at 17:58 UTC is now ~2h20m old and unresolved — OpenClaw won't accept the  |
| Apr 20, 21:43 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 20:37 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | hermes | OinkV just hit a blocker on Task 171 (the OinXtractor stateful retrieval-learning agent you approved for parallel execution this afternoon). |

## 🧭 Needs Mike

_No open DECISION_NEEDED events._

## 🔍 Missing evidence

| Severity | Task | Issue |
|---|---|---|
| 🟠 WARN | `A2` | PR_OPENED (pr=5) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A4` | PR_OPENED (pr=7) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A7` | PR_OPENED (pr=130) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A5` | PR_OPENED (pr=131) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A6` | PR_OPENED (pr=20) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A9` | PR_OPENED (pr=8) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A9` | PR_OPENED (pr=132) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A11` | PR_OPENED (pr=133) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A8` | PR_OPENED (pr=134) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A10` | PR_OPENED (pr=135) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B6` | MERGED with no CANARY_STARTED within 2h |

## 🫀 Freshness by agent

| Agent | Last event | Type | Task | Staleness | Events |
|---|---|---|---|---|---|
| 🐷 **OinkV** | Apr 20, 22:57 CEST | `SPRINT_NOTE` | `A171` | 🟢 fresh | 2 |
| 🪽 **Hermes** | Apr 20, 22:55 CEST | `DECISION_RESOLVED` | `B4` | 🟢 fresh | 26 |
| 🛡️ **GUARDIAN** | Apr 20, 18:02 CEST | `ARTIFACT_PUBLISHED` | `—` | 🔴 stale | 66 |
| 🔥 **FORGE** | Apr 20, 17:53 CEST | `TASK_PLANNED` | `—` | 🔴 stale | 52 |
| • **mike** | Apr 20, 13:32 CEST | `DECISION_RESOLVED` | `—` | 🔴 stale | 2 |
| ⚒️ **ANVIL** | Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | 🔴 stale | 88 |
| • **SYSTEM** | Apr 20, 09:40 CEST | `PROPOSAL_APPROVED` | `B8` | 🔴 stale | 16 |
| 🔍 **VIGIL** | Apr 20, 09:36 CEST | `REVIEW_POSTED` | `B8` | 🔴 stale | 31 |

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
| [Wave 1 (Phase A)](waves/wave-1.md) | Core schema & formula primitives | [A1](tasks/A1-signal-events-schema.md) · [A2](tasks/A2-remaining-pct-model.md) · [A3](tasks/A3-auto-filled-at.md) | 3/3 shipped |
| [Wave 2 (Phase A)](waves/wave-2.md) | Lifecycle accuracy & phantom-trade prevention | [A4](tasks/A4-partially-closed-status.md) · [A7](tasks/A7-update-new-detection.md) · [A5](tasks/A5-confidence-scoring.md) | 2/3 shipped |
| [Wave 3 (Phase A)](waves/wave-3.md) | Metadata enrichment & ghost closure | [A6](tasks/A6-ghost-closure-flag.md) · [A8](tasks/A8-conditional-sl-type.md) · [A9](tasks/A9-denomination-multiplier.md) · [A11](tasks/A11-leverage-source-tracking.md) | 3/4 shipped |
| [Wave 4 (Phase A)](waves/wave-4.md) | Database merge | [A10](tasks/A10-database-merge.md) | 1/1 shipped |
| [Wave B1 (Phase B)](waves/wave-b1.md) | Database abstraction layer (`oink_db.py`) | [B1](tasks/B1-db-abstraction-layer.md) | 🚧 IN FLIGHT |

## Tasks

| Task | Name | Tier | Wave | Status | Canary |
|---|---|---|---|---|---|
| [A1](tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A2](tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A3](tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | 1 | ✅ DONE | PASS |
| [A4](tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 2 | ✅ DONE | PASS |
| [A5](tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | 2 | ✅ DONE | PASS |
| [A6](tasks/A6-ghost-closure-flag.md) | Ghost Closure Confirmation Flag | 🟡 STANDARD | 3 | ✅ DONE | PASS |
| [A7](tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 2 | 🧪 CANARY | PENDING |
| [A8](tasks/A8-conditional-sl-type.md) | Conditional SL Type Field | 🟡 STANDARD | 3 | 🧪 CANARY | PENDING |
| [A9](tasks/A9-denomination-multiplier.md) | Denomination Multiplier Table (1000x-prefixed symbols) | 🟢 LIGHTWEIGHT | 3 | ✅ DONE | PASS |
| [A10](tasks/A10-database-merge.md) | Database Merge (test → prod, council-approved) | 🔴 CRITICAL | 4 | ✅ DONE | PASS |
| [A11](tasks/A11-leverage-source-tracking.md) | Leverage Source Tracking | 🟢 LIGHTWEIGHT | 3 | ✅ DONE | PASS |
| `A171` | A171 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| [B1](tasks/B1-db-abstraction-layer.md) | Database Abstraction Layer (sqlite3 → oink_db.py) | 🔴 CRITICAL | B1 | 🧪 CANARY | PENDING |
| `B2` | B2 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B3` | B3 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B4` | B4 | 🟡 STANDARD | — | 📋 PLANNED | — |
| `B5` | B5 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B6` | B6 | 🟡 STANDARD | — | MERGED | — |
| `B7` | B7 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B8` | B8 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B9` | B9 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B10` | B10 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B11` | B11 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B12` | B12 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B13` | B13 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B15` | B15 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `C2` | C2 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |

## Event log

- [Event index](events/README.md) — chronological feed (newest first within each day)

## Agents

| Emoji | Name | Role |
|---|---|---|
| 🐷 | OinkV | Plan Auditor |
| 🪽 | Hermes | Sprint Orchestrator |
| 🛡️ | GUARDIAN | Data Integrity + Canary |
| 🔥 | FORGE | Technical Execution Planner |
| • | mike |  |
| ⚒️ | ANVIL | Implementation Lead |
| • | SYSTEM |  |
| 🔍 | VIGIL | Code Review + Scoring |

## Conventions

- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT (per Arbiter-Oink Phase 4 governance)
- **Auto-escalation:** if a diff touches one of the 7 Financial Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.
- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → CODE → PR_REVIEW → CANARY → DONE
- **Timestamps** are rendered in CEST (UTC+2).

---

*9/27 tasks DONE · Last auto-regenerated: 23:13 CEST on 20 Apr 2026 · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint)*
