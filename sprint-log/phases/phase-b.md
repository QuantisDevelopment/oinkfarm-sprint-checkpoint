# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 5/14 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🔴 CRITICAL | 🧪 CANARY | PENDING | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 21, 17:27 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | 🧪 CANARY | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 21, 21:16 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 21, 16:35 CEST · `ARTIFACT_PUBLISHED` | anvil · forge · guardian · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 21, 17:51 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🔴 CRITICAL | 📝 PROPOSAL REVIEW | — | — | Apr 21, 18:00 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 21, 19:12 CEST · `SPRINT_NOTE` | anvil · forge |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 21, 22:52 CEST · `DECISION_NEEDED` | anvil · forge |
| [B12](../tasks/B12-b12.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 21, 20:18 CEST · `AGENT_HEARTBEAT` | anvil · forge · guardian · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 21, 22:53 CEST | `AGENT_HEARTBEAT` | `—` | guardian | guardian heartbeat — Sprint poke 20:50Z — all MERGED covered, B2 canary open, ISSUE-189 audit shipped |
| Apr 21, 22:52 CEST | `TASK_PLANNED` | `B11` | forge | B11 plan published |
| Apr 21, 22:52 CEST | `DECISION_NEEDED` | `B11` | forge | B11 Mike gate: Track 2 event-walk close_source flip from dual-compute to authoritative: fixed date vs SLO (<=0.1% divergence for 7 consecuti |
| Apr 21, 22:52 CEST | `DECISION_NEEDED` | `B11` | forge | B11 Mike gate: Where to store MICRO_GATE_DECISION rows for pre-INSERT rejections (no signal_id yet)? |
| Apr 21, 22:51 CEST | `AGENT_HEARTBEAT` | `—` | guardian | guardian heartbeat — ISSUE-189: Full backfill candidate scan — 143 candidates found (10.7x Hermes preliminary) |
| Apr 21, 22:48 CEST | `SPRINT_NOTE` | `—` | hermes | Issue #189 filed: SL-to-BE moves rejected by micro-gate B14, causing 11+ trades to log as CLOSED_LOSS when actually stopped flat. Forensic c |
| Apr 21, 21:16 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — Sprint poke 19:15Z — delta check, no new activity |
| Apr 21, 20:18 CEST | `AGENT_HEARTBEAT` | `B12` | anvil | anvil heartbeat — B12 |
| Apr 21, 19:41 CEST | `AGENT_HEARTBEAT` | `B3` | guardian | guardian heartbeat — Sprint poke — B3 daily reconciliation + B2/B3 canary tracking |
| Apr 21, 19:12 CEST | `SPRINT_NOTE` | `B10` | anvil | SPRINT_NOTE: All 5 Mike checklist items complete. No REVISE verdicts. B2 canary dispatched. B4 runbook done. B9 R2 submitted. B10+B11 Phase  |
| Apr 21, 19:12 CEST | `PROPOSAL_READY` | `B10` | anvil | B10 proposal ready |
| Apr 21, 19:12 CEST | `PROPOSAL_READY` | `B11` | anvil | B11 proposal ready |
| Apr 21, 19:10 CEST | `PROPOSAL_READY` | `B10` | anvil | B10 proposal ready |
| Apr 21, 18:00 CEST | `AGENT_HEARTBEAT` | `B9` | guardian | guardian heartbeat — B9 R2 Phase 0 APPROVED; awaiting VIGIL R2 review |
| Apr 21, 18:00 CEST | `PROPOSAL_APPROVED` | `B9` | guardian | B9 proposal approved by guardian |
| Apr 21, 17:59 CEST | `REVIEW_POSTED` | `M154` | vigil | M154 review by vigil — PASS (9.0) |
| Apr 21, 17:59 CEST | `REVIEW_POSTED` | `M165` | vigil | M165 review by vigil — PASS (0.0) |
| Apr 21, 17:59 CEST | `REVIEW_POSTED` | `M181` | vigil | M181 review by vigil — PASS (9.0) |
| Apr 21, 17:52 CEST | `SPRINT_NOTE` | `B9` | anvil | SPRINT STATUS — All pipeline items shipped, B9 R2 revision complete.

COMPLETED THIS SESSION:
- B9 Phase 0 R2 submitted: Fixed both blocking |
| Apr 21, 17:51 CEST | `PROPOSAL_READY` | `B9` | anvil | B9 proposal ready |
| Apr 21, 17:51 CEST | `REVIEW_POSTED` | `B6` | vigil | B6 review by vigil — PASS (9.85) |
| Apr 21, 17:51 CEST | `REVIEW_POSTED` | `M179` | vigil | M179 review by vigil — PASS (0.0) |
| Apr 21, 17:45 CEST | `PROPOSAL_REJECTED` | `B9` | vigil | B9 proposal rejected — Incomplete mutation inventory (engine.py/kraken-sync/validate-data-quality missing) and no automated Phase 1→2 reconc |
| Apr 21, 17:27 CEST | `AGENT_HEARTBEAT` | `B2` | guardian | guardian heartbeat — Priority correction ack — Heavy Hybrid remains P0 |
| Apr 21, 17:25 CEST | `SPRINT_NOTE` | `—` | hermes | CORRECTION: Heavy Hybrid is top priority. Data purity is the endgame. Dashboard :8484 is the WINDOW we use to SEE the data, NOT a competing  |
| Apr 21, 17:12 CEST | `AGENT_HEARTBEAT` | `B9` | guardian | guardian heartbeat — Priority pivot ack + canary schedule maintenance |
| Apr 21, 17:03 CEST | `AGENT_HEARTBEAT` | `B9` | guardian | guardian heartbeat — B9 + B12 Phase 0 reviews |
| Apr 21, 17:03 CEST | `PROPOSAL_REJECTED` | `B9` | guardian | B9 proposal rejected — REQUEST CHANGES: 2 blocking items — (1) engine.py ephemeral column whitelist missing from W1 guard design, blanket UP |
| Apr 21, 17:03 CEST | `PROPOSAL_APPROVED` | `B12` | guardian | B12 proposal approved by guardian |
| Apr 21, 16:40 CEST | `ARTIFACT_PUBLISHED` | `B10` | anvil | B10 published design_notes:  |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-B11-4` | Track 2 event-walk close_source flip from dual-compute to authoritative: fixed date vs SLO (<=0.1% divergence for 7 consecutive days)? | `B11` | 0m | fixed_date · slo_gated_7day |
| `Q-B11-5` | Where to store MICRO_GATE_DECISION rows for pre-INSERT rejections (no signal_id yet)? | `B11` | 0m | signal_events_with_null_signal_id · separate_micro_gate_rejections_table |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
