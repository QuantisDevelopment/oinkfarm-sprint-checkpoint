# OinkFarm Implementation Foresight Sprint — Archive

Human-readable per-task, per-wave, per-phase, and per-event archive. For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).

## Event stream integrity

- **Total events:** 293
- **Last 24h:** 158 (rate 6.58/h)
- **Schema:** v1.0
- **Source:** lib
- **Monotonic:** ✓ ok

## 🔴 Live now

### Last 1 hour (3 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | hermes | OinkV just hit a blocker on Task 171 (the OinXtractor stateful retrieval-learning agent you approved for parallel execution this afternoon). |
| Apr 20, 19:58 CEST | `BLOCKED` | `A171` | oinkv | A171 BLOCKED — design_clarification_needed |
| Apr 20, 19:49 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |

### Last 4 hours (7 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | hermes | OinkV just hit a blocker on Task 171 (the OinXtractor stateful retrieval-learning agent you approved for parallel execution this afternoon). |
| Apr 20, 19:58 CEST | `BLOCKED` | `A171` | oinkv | A171 BLOCKED — design_clarification_needed |
| Apr 20, 19:49 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 18:06 CEST | `SPRINT_NOTE` | `—` | hermes | FORGE opened a new parallel track this afternoon: Task 171 ("OinXtractor as a stateful retrieval-learning agent") — the plan is to give the  |
| Apr 20, 18:02 CEST | `ARTIFACT_PUBLISHED` | `—` | guardian | — published kpi-baseline: extraction-accuracy-baseline.md |
| Apr 20, 17:53 CEST | `TASK_PLANNED` | `—` | forge | — plan published |
| Apr 20, 17:52 CEST | `TASK_PLANNED` | `—` | forge | — plan published |

### Last 24 hours (158 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | hermes | OinkV just hit a blocker on Task 171 (the OinXtractor stateful retrieval-learning agent you approved for parallel execution this afternoon). |
| Apr 20, 19:58 CEST | `BLOCKED` | `A171` | oinkv | A171 BLOCKED — design_clarification_needed |
| Apr 20, 19:49 CEST | `ARTIFACT_PUBLISHED` | `—` | hermes | — published oinxtractor_quality: oinxtractor-quality.html |
| Apr 20, 18:06 CEST | `SPRINT_NOTE` | `—` | hermes | FORGE opened a new parallel track this afternoon: Task 171 ("OinXtractor as a stateful retrieval-learning agent") — the plan is to give the  |
| Apr 20, 18:02 CEST | `ARTIFACT_PUBLISHED` | `—` | guardian | — published kpi-baseline: extraction-accuracy-baseline.md |
| Apr 20, 17:53 CEST | `TASK_PLANNED` | `—` | forge | — plan published |
| Apr 20, 17:52 CEST | `TASK_PLANNED` | `—` | forge | — plan published |
| Apr 20, 15:47 CEST | `SPRINT_NOTE` | `—` | hermes | The four Phase A canary failures that were sitting red on the dashboard all morning are now green. GUARDIAN re-ran the battery at 13:08 UTC  |
| Apr 20, 15:15 CEST | `SPRINT_NOTE` | `B3` | hermes | B3 dual-write activation gap investigated. VERDICT: intentional gate, NOT an oversight. OINK_DB_DUAL_WRITE=false is the CORRECT state until  |
| Apr 20, 15:08 CEST | `CANARY_PASS` | `A4` | guardian | A4 canary PASS |
| Apr 20, 15:08 CEST | `CANARY_PASS` | `A6` | guardian | A6 canary PASS |
| Apr 20, 15:08 CEST | `CANARY_PASS` | `A9` | guardian | A9 canary PASS |
| Apr 20, 15:08 CEST | `CANARY_PASS` | `A10` | guardian | A10 canary PASS |
| Apr 20, 13:57 CEST | `SPRINT_NOTE` | `—` | hermes | 🔥 FORGE raised 4 Mike-gates: B2 TimescaleDB defer→B14, B13 single-host Compose, B9 W1 immutability phasing, C2 low-conf PROVISIONAL vs rejec |
| Apr 20, 13:35 CEST | `TASK_PLANNED` | `—` | forge | — plan published |

## 🧭 Needs Mike

| Question ID | Question | Task | Age | Options | Gate |
|---|---|---|---|---|---|
| `A10-APPROVE` | Approve A10 merge algorithm + dedup strategy | `A10` | 8.3h | APPROVE · REVISE | generic |
| `B4-APPROVE` | Cutover requires Mike's explicit go-ahead | `B4` | 8.3h | APPROVE · DEFER | generic |
| `Q-B2-4` | 84 closed signals with NULL filled_at — backfill/accept/block? | `B2` | 8.3h | backfill · accept · block | phase-b |
| `Q-B2-5` | trg_entry_price_update REJECTED_AUDIT exception handling | `B2` | 8.3h | pg_trigger · check_only | phase-b |
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | `B12` | 8.3h | maxlen · time_based | heavy-hybrid |
| `Q-B2-3` | Defer TimescaleDB introduction from B2 to B14? | `B2` | 6.9h | defer to B14 · introduce in B2 | phase-b |
| `Q-HH-3` | Single-host Docker Compose for B13, defer multi-host to Phase D+? | `B13` | 6.9h | single-host only · include multi-host preparation | heavy-hybrid |
| `Q-HH-4` | Enforce W1 immutability via phased app-level then DB REVOKE? | `B9` | 6.9h | phased app-level then DB REVOKE · immediate DB-level REVOKE | heavy-hybrid |
| `Q-HH-5` | Route low-confidence signals to PROVISIONAL state or hard-reject? | `C2` | 6.9h | PROVISIONAL soft-flag · hard reject | heavy-hybrid |

## 🔍 Missing evidence

| Severity | Task | Issue |
|---|---|---|
| 🟠 WARN | `B13` | MERGED with no CANARY_STARTED within 2h |
| 🟠 WARN | `B14` | PR_OPENED (pr=63) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B14` | MERGED with no CANARY_STARTED within 2h |
| 🟠 WARN | `B1` | PR_OPENED (pr=121) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A1` | PR_OPENED (pr=17) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A1` | PR_OPENED (pr=18) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A2` | PR_OPENED (pr=19) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B1` | PR_OPENED (pr=1) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B2` | PR_OPENED (pr=2) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B3` | PR_OPENED (pr=3) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `B4` | MERGED with no CANARY_STARTED within 2h |
| 🟠 WARN | `A3` | PR_OPENED (pr=125) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A1` | PR_OPENED (pr=126) with no REVIEW_POSTED within 24h |
| 🟠 WARN | `A1` | PR_OPENED (pr=4) with no REVIEW_POSTED within 24h |
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
| 🪽 **Hermes** | Apr 20, 20:12 CEST | `SPRINT_NOTE` | `—` | 🟢 fresh | 13 |
| 🐷 **OinkV** | Apr 20, 19:58 CEST | `BLOCKED` | `A171` | 🟢 fresh | 1 |
| 🛡️ **GUARDIAN** | Apr 20, 18:02 CEST | `ARTIFACT_PUBLISHED` | `—` | 🟡 1–3h | 66 |
| 🔥 **FORGE** | Apr 20, 17:53 CEST | `TASK_PLANNED` | `—` | 🟡 1–3h | 52 |
| • **mike** | Apr 20, 13:32 CEST | `DECISION_RESOLVED` | `—` | 🔴 stale | 2 |
| ⚒️ **ANVIL** | Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | 🔴 stale | 112 |
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
| `A171` | A171 | 🟡 STANDARD | — | 🛑 BLOCKED | — |
| [B1](tasks/B1-db-abstraction-layer.md) | Database Abstraction Layer (sqlite3 → oink_db.py) | 🔴 CRITICAL | B1 | 🧪 CANARY | PENDING |
| `B2` | B2 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B3` | B3 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B4` | B4 | 🟡 STANDARD | — | MERGED | — |
| `B5` | B5 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B6` | B6 | 🟡 STANDARD | — | MERGED | — |
| `B7` | B7 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B8` | B8 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| `B9` | B9 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B10` | B10 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B11` | B11 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B12` | B12 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `B13` | B13 | 🟡 STANDARD | — | MERGED | — |
| `B14` | B14 | 🟡 STANDARD | — | MERGED | — |
| `B15` | B15 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |
| `C2` | C2 | 🟡 STANDARD | — | ⏳ NOT STARTED | — |

## Event log

- [Event index](events/README.md) — chronological feed (newest first within each day)

## Agents

| Emoji | Name | Role |
|---|---|---|
| 🪽 | Hermes | Sprint Orchestrator |
| 🐷 | OinkV | Plan Auditor |
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

*9/28 tasks DONE · Last auto-regenerated: 20:14 CEST on 20 Apr 2026 · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint)*
