# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 4/14 tasks shipped  
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
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | 🧪 CANARY | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 22, 00:45 CEST · `CANARY_STARTED` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 22, 01:06 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 00:02 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 01:03 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⚙️ CODING | — | — | Apr 22, 01:06 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📋 PLANNED | — | — | Apr 20, 23:18 CEST · `TASK_PLANNED` | forge · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | ⏳ NOT STARTED | — | — | Apr 20, 11:55 CEST · `TASK_PLANNED` | forge |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 22, 01:07 CEST | `AGENT_HEARTBEAT` | `—` | guardian | guardian heartbeat — Heartbeat 23:07Z — 3 material events processed (B9 v2 REQUEST_CHANGES, B12-SHADOW APPROVE, B6 canary baseline) |
| Apr 22, 01:06 CEST | `DECISION_RESOLVED` | `B9` | hermes | B9 decision: expand_guard_block_phase1_until_proof |
| Apr 22, 01:06 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: constrain_shadow_to_2_topics_until_b15 |
| Apr 22, 01:06 CEST | `DECISION_RESOLVED` | `B12` | hermes | B12 decision: require_contract_valid_for_lifecycle_and_validation |
| Apr 22, 01:06 CEST | `DECISION_RESOLVED` | `—` | hermes | — decision: block_phase1_until_shared_helper |
| Apr 22, 01:06 CEST | `DECISION_RESOLVED` | `—` | hermes | — decision: require_immutable_corroboration_for_auto_backfill |
| Apr 22, 01:06 CEST | `PROPOSAL_APPROVED` | `B12` | guardian | B12 proposal approved by guardian |
| Apr 22, 01:06 CEST | `PROPOSAL_REJECTED` | `T189` | vigil | T189 proposal rejected — Q-189-1 pre-alignment not reflected: proposal still emits legacy SL_TO_BE + _log_rejection JSONL instead of B11-v2  |
| Apr 22, 01:06 CEST | `PROPOSAL_APPROVED` | `B9` | vigil | B9 proposal approved by vigil |
| Apr 22, 01:05 CEST | `PROPOSAL_REJECTED` | `B9` | guardian | B9 proposal rejected — v2 regresses from approved R2: 13 phantom IMMUTABLE columns, 5 phantom EPHEMERAL columns, METADATA tier dropped, 22 r |
| Apr 22, 01:03 CEST | `SPRINT_NOTE` | `—` | anvil | ANVIL decision-ack bundle: three Hermes rulings (Q-189-1, Q-B11-5, Q-B11-4) applied in TASK-189-proposal.md R2. |
| Apr 22, 01:03 CEST | `SPRINT_NOTE` | `—` | anvil | Sprint resume processed. (1) TASK-189-proposal.md -> R2 pre-aligned with B11 v2 event substrate per Hermes Q-189-1: MICRO_GATE_DECISION (rul |
| Apr 22, 01:03 CEST | `PROPOSAL_READY` | `M189` | anvil | M189 proposal ready |
| Apr 22, 01:03 CEST | `TASK_PLANNED` | `B11` | forge | B11 plan published |
| Apr 22, 01:03 CEST | `DECISION_NEEDED` | `B9` | forge | B9 Mike gate: Expand B9 mutation guard from OinkConnection.execute() only to all write surfaces (cursor.execute, executemany, wrapper/cursor |
| Apr 22, 01:03 CEST | `DECISION_NEEDED` | `B12` | forge | B12 Mike gate: B12 shadow-mode publishes 8 topics vs ratified B12 plan's 2 topics. Ratify scope expansion, or constrain shadow to 2 topics u |
| Apr 22, 01:03 CEST | `DECISION_NEEDED` | `B12` | forge | B12 Mike gate: Shadow publish_to_stream logs schema failure then publishes anyway. For topics informing B11/B12 consumer design (lifecycle.e |
| Apr 22, 00:59 CEST | `DECISION_RESOLVED` | `B11` | hermes | B11 decision: slo_gated_7day |
| Apr 22, 00:59 CEST | `DECISION_RESOLVED` | `B11` | hermes | B11 decision: signal_events_with_null_signal_id |
| Apr 22, 00:59 CEST | `DECISION_RESOLVED` | `—` | hermes | — decision: pre_align_phase1_with_b11_v2_schema |
| Apr 22, 00:46 CEST | `SPRINT_NOTE` | `—` | anvil | Sprint poke processed. State: (1) No REVISE on any anvil PR - checked last 8h of REVIEW_POSTED; only REVISE verdicts are against memory-wiki |
| Apr 22, 00:45 CEST | `MERGED` | `B6` | anvil | B6 merged via PR #None @ace226e |
| Apr 22, 00:45 CEST | `STATUS_CHANGED` | `B6` | anvil | B6 NOT_STARTED → CANARY |
| Apr 22, 00:45 CEST | `CANARY_STARTED` | `B6` | anvil | B6 canary started |
| Apr 22, 00:23 CEST | `AGENT_HEARTBEAT` | `—` | guardian | guardian heartbeat — Heartbeat 22:20Z — All 4 tasks dispatched |
| Apr 22, 00:22 CEST | `PROPOSAL_READY` | `B9` | anvil | B9 proposal ready |
| Apr 22, 00:22 CEST | `PROPOSAL_READY` | `B12` | anvil | B12 proposal ready |
| Apr 22, 00:22 CEST | `SPRINT_NOTE` | `—` | anvil | Parallel sprint checkpoint 1/4. TASK 1 B4 runbook v1.1 complete (rowcount baseline T-15min + pre/post verify T+5min + first-10-signal canary |
| Apr 22, 00:22 CEST | `AGENT_HEARTBEAT` | `—` | guardian | guardian heartbeat — Heartbeat 22:14Z — TASK-189 TIER-1 subset written, B2/B3 close-outs pending |
| Apr 22, 00:20 CEST | `DECISION_NEEDED` | `M189` | forge | M189 Mike gate: Should oinkfarm#189 Phase 1 Artifact A pre-align MICRO_GATE_DECISION / SL_UPDATE event payloads with B11 v2 schema (rule_id, |

## Needs Mike (open gates)

_No open DECISION_NEEDED for this phase._

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
