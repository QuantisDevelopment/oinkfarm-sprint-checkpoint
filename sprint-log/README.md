# OinkFarm Implementation Foresight Sprint — Archive

Human-readable per-task, per-wave, per-phase, and per-event archive. For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).

## Event stream integrity

- **Total events:** 270
- **Last 24h:** 192 (rate 8.0/h)
- **Schema:** v1.0
- **Source:** lib
- **Monotonic:** ✓ ok

## 🔴 Live now

### Last 1 hour (9 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 13:18 CEST | `SPRINT_NOTE` | `—` | hermes | 🪽 Hermes resolved 6 Phase B decisions (hermes_ops):
• B1: adopt psycopg3; canonical oink_db.py in oinkfarm/scripts + CI fork-sync to vendore |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Adopt psycopg3 (`psycopg[binary]`). It is the actively maintained upstream (psycopg2 is in maintenance mode), has a cleaner Con |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Canonical oink_db.py lives in oinkfarm scripts/ (/home/oinkv/oinkfarm/scripts/oink_db.py), with vendored copies in oink-sync/ a |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Same server (barn) initially, inside Docker Compose network. Matches Arbiter V3 PHASE-4 §2 topology exactly ('Container definit |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Re-enable the systemd unit before B4 cutover. Reasons: (1) Arbiter PHASE-0 §Resilience explicitly models signal-gateway supervi |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Fork-sync for B4; schedule re-point for B13 (Docker Compose). Rationale: (1) B4 is a CRITICAL cutover window — re-pointing serv |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-t |
| Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | anvil | ANVIL checkpoint-reporting integration self-test |
| Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | guardian | B7 canary started |

### Last 4 hours (45 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 13:18 CEST | `SPRINT_NOTE` | `—` | hermes | 🪽 Hermes resolved 6 Phase B decisions (hermes_ops):
• B1: adopt psycopg3; canonical oink_db.py in oinkfarm/scripts + CI fork-sync to vendore |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Adopt psycopg3 (`psycopg[binary]`). It is the actively maintained upstream (psycopg2 is in maintenance mode), has a cleaner Con |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Canonical oink_db.py lives in oinkfarm scripts/ (/home/oinkv/oinkfarm/scripts/oink_db.py), with vendored copies in oink-sync/ a |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Same server (barn) initially, inside Docker Compose network. Matches Arbiter V3 PHASE-4 §2 topology exactly ('Container definit |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Re-enable the systemd unit before B4 cutover. Reasons: (1) Arbiter PHASE-0 §Resilience explicitly models signal-gateway supervi |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Fork-sync for B4; schedule re-point for B13 (Docker Compose). Rationale: (1) B4 is a CRITICAL cutover window — re-pointing serv |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-t |
| Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | anvil | ANVIL checkpoint-reporting integration self-test |
| Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | guardian | B7 canary started |
| Apr 20, 12:17 CEST | `MERGED` | `B7` | anvil | B7 merged via PR #27 @3f85c12 |
| Apr 20, 12:10 CEST | `CANARY_STARTED` | `B8` | guardian | B8 canary started |
| Apr 20, 11:57 CEST | `MERGED` | `B8` | anvil | B8 merged via PR #26 @6879e25 |
| Apr 20, 11:56 CEST | `PR_OPENED` | `B7` | anvil | B7 PR #27 opened — feat(B7): extract WG Bot parsers to parsers/wg_bot.py |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `A10` | forge | A10 Mike gate: Approve A10 merge algorithm + dedup strategy |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: Cutover requires Mike's explicit go-ahead |

### Last 24 hours (192 events)
| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 20, 13:18 CEST | `SPRINT_NOTE` | `—` | hermes | 🪽 Hermes resolved 6 Phase B decisions (hermes_ops):
• B1: adopt psycopg3; canonical oink_db.py in oinkfarm/scripts + CI fork-sync to vendore |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Adopt psycopg3 (`psycopg[binary]`). It is the actively maintained upstream (psycopg2 is in maintenance mode), has a cleaner Con |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B1` | hermes | B1 decision: Canonical oink_db.py lives in oinkfarm scripts/ (/home/oinkv/oinkfarm/scripts/oink_db.py), with vendored copies in oink-sync/ a |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B2` | hermes | B2 decision: Same server (barn) initially, inside Docker Compose network. Matches Arbiter V3 PHASE-4 §2 topology exactly ('Container definit |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Re-enable the systemd unit before B4 cutover. Reasons: (1) Arbiter PHASE-0 §Resilience explicitly models signal-gateway supervi |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B4` | hermes | B4 decision: Fork-sync for B4; schedule re-point for B13 (Docker Compose). Rationale: (1) B4 is a CRITICAL cutover window — re-pointing serv |
| Apr 20, 13:15 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-t |
| Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | anvil | ANVIL checkpoint-reporting integration self-test |
| Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | guardian | B7 canary started |
| Apr 20, 12:17 CEST | `MERGED` | `B7` | anvil | B7 merged via PR #27 @3f85c12 |
| Apr 20, 12:10 CEST | `CANARY_STARTED` | `B8` | guardian | B8 canary started |
| Apr 20, 11:57 CEST | `MERGED` | `B8` | anvil | B8 merged via PR #26 @6879e25 |
| Apr 20, 11:56 CEST | `PR_OPENED` | `B7` | anvil | B7 PR #27 opened — feat(B7): extract WG Bot parsers to parsers/wg_bot.py |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `A10` | forge | A10 Mike gate: Approve A10 merge algorithm + dedup strategy |
| Apr 20, 11:55 CEST | `DECISION_NEEDED` | `B4` | forge | B4 Mike gate: Cutover requires Mike's explicit go-ahead |

## 🧭 Needs Mike

| Question ID | Question | Task | Age | Options | Gate |
|---|---|---|---|---|---|
| `A10-APPROVE` | Approve A10 merge algorithm + dedup strategy | `A10` | 1.4h | APPROVE · REVISE | generic |
| `B4-APPROVE` | Cutover requires Mike's explicit go-ahead | `B4` | 1.4h | APPROVE · DEFER | generic |
| `Q-B2-3` | TimescaleDB now or later (B14)? | `B2` | 1.4h | now · later | phase-b |
| `Q-B2-4` | 84 closed signals with NULL filled_at — backfill/accept/block? | `B2` | 1.4h | backfill · accept · block | phase-b |
| `Q-B2-5` | trg_entry_price_update REJECTED_AUDIT exception handling | `B2` | 1.4h | pg_trigger · check_only | phase-b |
| `Q-B3-2` | Minimum verification period: 7 or 14 days? | `B3` | 1.4h | 7d · 14d | phase-b |
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | `B12` | 1.4h | maxlen · time_based | heavy-hybrid |
| `Q-HH-3` | Docker Compose: single host or multi-host? | `B13` | 1.4h | single · multi | heavy-hybrid |
| `Q-HH-4` | W1 enforcement level: DB REVOKE UPDATE, or app-level guard? | `B9` | 1.4h | db_revoke · app_guard | heavy-hybrid |
| `Q-HH-5` | Confidence routing: hard reject or soft flag? | `C2` | 1.4h | hard_reject · soft_flag | heavy-hybrid |
| `Q-HH-6` | Phase D entry gate: who decides prerequisites are met? | `—` | 1.4h | mike_guardian_joint | heavy-hybrid |

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
| 🟠 WARN | `B6` | MERGED with no CANARY_STARTED within 2h |

## 🫀 Freshness by agent

| Agent | Last event | Type | Task | Staleness | Events |
|---|---|---|---|---|---|
| 🪽 **Hermes** | Apr 20, 13:18 CEST | `SPRINT_NOTE` | `—` | 🟢 fresh | 7 |
| ⚒️ **ANVIL** | Apr 20, 12:48 CEST | `SPRINT_NOTE` | `—` | 🟢 fresh | 112 |
| 🛡️ **GUARDIAN** | Apr 20, 12:26 CEST | `CANARY_STARTED` | `B7` | 🟢 fresh | 61 |
| 🔥 **FORGE** | Apr 20, 11:55 CEST | `DECISION_NEEDED` | `—` | 🟡 1–3h | 43 |
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
| [Wave 2 (Phase A)](waves/wave-2.md) | Lifecycle accuracy & phantom-trade prevention | [A4](tasks/A4-partially-closed-status.md) · [A7](tasks/A7-update-new-detection.md) · [A5](tasks/A5-confidence-scoring.md) | 1/3 shipped |
| [Wave 3 (Phase A)](waves/wave-3.md) | Metadata enrichment & ghost closure | [A6](tasks/A6-ghost-closure-flag.md) · [A8](tasks/A8-conditional-sl-type.md) · [A9](tasks/A9-denomination-multiplier.md) · [A11](tasks/A11-leverage-source-tracking.md) | 1/4 shipped |
| [Wave 4 (Phase A)](waves/wave-4.md) | Database merge | [A10](tasks/A10-database-merge.md) | 0/1 shipped |
| [Wave B1 (Phase B)](waves/wave-b1.md) | Database abstraction layer (`oink_db.py`) | [B1](tasks/B1-db-abstraction-layer.md) | 🚧 IN FLIGHT |

## Tasks

| Task | Name | Tier | Wave | Status | Canary |
|---|---|---|---|---|---|
| [A1](tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A2](tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A3](tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | 1 | ✅ DONE | PASS |
| [A4](tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 2 | 🛑 BLOCKED | FAIL |
| [A5](tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | 2 | ✅ DONE | PASS |
| [A6](tasks/A6-ghost-closure-flag.md) | Ghost Closure Confirmation Flag | 🟡 STANDARD | 3 | 🛑 BLOCKED | FAIL |
| [A7](tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 2 | 🧪 CANARY | PENDING |
| [A8](tasks/A8-conditional-sl-type.md) | Conditional SL Type Field | 🟡 STANDARD | 3 | 🧪 CANARY | PENDING |
| [A9](tasks/A9-denomination-multiplier.md) | Denomination Multiplier Table (1000x-prefixed symbols) | 🟢 LIGHTWEIGHT | 3 | 🛑 BLOCKED | FAIL |
| [A10](tasks/A10-database-merge.md) | Database Merge (test → prod, council-approved) | 🔴 CRITICAL | 4 | 🛑 BLOCKED | FAIL |
| [A11](tasks/A11-leverage-source-tracking.md) | Leverage Source Tracking | 🟢 LIGHTWEIGHT | 3 | ✅ DONE | PASS |
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
| ⚒️ | ANVIL | Implementation Lead |
| 🛡️ | GUARDIAN | Data Integrity + Canary |
| 🔥 | FORGE | Technical Execution Planner |
| • | SYSTEM |  |
| 🔍 | VIGIL | Code Review + Scoring |

## Conventions

- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT (per Arbiter-Oink Phase 4 governance)
- **Auto-escalation:** if a diff touches one of the 7 Financial Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.
- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → CODE → PR_REVIEW → CANARY → DONE
- **Timestamps** are rendered in CEST (UTC+2).

---

*5/27 tasks DONE · Last auto-regenerated: 13:20 CEST on 20 Apr 2026 · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint)*
