# Phase B — Infrastructure Migration

## What is Phase B?

> Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + decomposed services — the infrastructure layer that unlocks Redis, W1 governance, and multi-writer safety. Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, Cornix/Chroma, dedup consolidation) is in flight.

**Status:** 7/14 tasks shipped  
**Goal:** Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.  
**Data source:** event-stream reducer (`events.jsonl`)  
**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)

## Tasks (live status from event stream)

| Task | Tier | Status | Canary | PRs | Last event | Agents |
|---|---|---|---|---|---|---|
| [B1](../tasks/B1-db-abstraction-layer.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkfarm#149](https://github.com/QuantisDevelopment/oinkfarm/pull/149) + [oink-sync#9](https://github.com/QuantisDevelopment/oink-sync/pull/9) + [signal-gateway#21](https://github.com/QuantisDevelopment/signal-gateway/pull/21) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · hermes |
| [B2](../tasks/B2-b2.md) | 🔴 CRITICAL | ✅ DONE | PASS | [oinkdb-api#2](https://github.com/QuantisDevelopment/oinkdb-api/pull/2) + [oinkfarm#153](https://github.com/QuantisDevelopment/oinkfarm/pull/153) + [oink-sync#11](https://github.com/QuantisDevelopment/oink-sync/pull/11) + [signal-gateway#24](https://github.com/QuantisDevelopment/signal-gateway/pull/24) | Apr 22, 05:53 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B3](../tasks/B3-b3.md) | 🟡 STANDARD | ✅ DONE | PASS | [oinkdb-api#3](https://github.com/QuantisDevelopment/oinkdb-api/pull/3) | Apr 27, 08:09 CEST · `ARTIFACT_PUBLISHED` | anvil · forge · guardian · hermes |
| [B4](../tasks/B4-b4.md) | 🔴 CRITICAL | 🛑 BLOCKED | — | — | Apr 27, 08:09 CEST · `BLOCKED` | anvil · forge · guardian · hermes |
| [B5](../tasks/B5-b5.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#25](https://github.com/QuantisDevelopment/signal-gateway/pull/25) | Apr 21, 08:09 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B6](../tasks/B6-b6.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#29](https://github.com/QuantisDevelopment/signal-gateway/pull/29) | Apr 27, 08:06 CEST · `CANARY_PASS` | anvil · forge · guardian · system |
| [B7](../tasks/B7-b7.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#27](https://github.com/QuantisDevelopment/signal-gateway/pull/27) | Apr 21, 12:16 CEST · `REVIEW_POSTED` | anvil · forge · guardian · system |
| [B8](../tasks/B8-b8.md) | 🟡 STANDARD | ✅ DONE | PASS | [signal-gateway#26](https://github.com/QuantisDevelopment/signal-gateway/pull/26) | Apr 21, 15:57 CEST · `SPRINT_NOTE` | anvil · forge · guardian · system |
| [B9](../tasks/B9-b9.md) | 🔴 CRITICAL | ⚙️ CODING | — | — | Apr 22, 10:07 CEST · `SPRINT_NOTE` | anvil · forge · guardian · hermes |
| [B10](../tasks/B10-b10.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 09:49 CEST · `TASK_PLANNED` | anvil · forge · guardian |
| [B11](../tasks/B11-b11.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 22, 01:03 CEST · `TASK_PLANNED` | anvil · forge · guardian · hermes |
| [B12](../tasks/B12-b12.md) | 🟡 STANDARD | ⚙️ CODING | — | — | Apr 22, 01:06 CEST · `DECISION_RESOLVED` | anvil · forge · guardian · hermes |
| [B13](../tasks/B13-b13.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 27, 00:57 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian · hermes |
| [B15](../tasks/B15-b15.md) | 🟡 STANDARD | 📝 PROPOSAL REVIEW | — | — | Apr 27, 02:06 CEST · `PROPOSAL_APPROVED` | anvil · forge · guardian |

## Waves

- **Wave B1 (Phase B)** — 1/1 shipped: `B1`

## Recent activity (last 24h)

| Time | Type | Task | Agent | Summary |
|---|---|---|---|---|
| Apr 28, 02:12 CEST | `REVIEW_POSTED` | `M239` | guardian | M239 review by guardian — PASS (9.45) |
| Apr 28, 02:07 CEST | `REVIEW_POSTED` | `M189` | guardian | M189 review by guardian — FAIL (5.95) |
| Apr 27, 19:04 CEST | `REVIEW_POSTED` | `M189` | vigil | M189 review by vigil — PASS (9.7) |
| Apr 27, 18:20 CEST | `REVIEW_POSTED` | `M189` | vigil | M189 review by vigil — REVISE (8.85) |
| Apr 27, 13:44 CEST | `REVIEW_POSTED` | `M193` | vigil | M193 review by vigil — PASS (9.7) |
| Apr 27, 09:24 CEST | `REVIEW_POSTED` | `M68` | vigil | M68 review by vigil — REVISE (7.0) |
| Apr 27, 09:19 CEST | `REVIEW_POSTED` | `M265` | vigil | M265 review by vigil — PASS (9.0) |
| Apr 27, 08:42 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — PASS (9.15) |
| Apr 27, 08:40 CEST | `REVIEW_POSTED` | `M265` | vigil | M265 review by vigil — REVISE (5.0) |
| Apr 27, 08:09 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-27.md |
| Apr 27, 08:09 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 27, 08:09 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 27, 08:09 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-27.md |
| Apr 27, 08:09 CEST | `ARTIFACT_PUBLISHED` | `B3` | oinkdb | B3 published reconciliation-daily: 2026-04-27.md |
| Apr 27, 08:09 CEST | `BLOCKED` | `B4` | oinkdb | B4 BLOCKED — waiting_for_upstream_task |
| Apr 27, 08:06 CEST | `CANARY_PASS` | `B6` | guardian | B6 canary PASS |
| Apr 27, 06:39 CEST | `REVIEW_POSTED` | `M201` | vigil | M201 review by vigil — REVISE (8.65) |
| Apr 27, 06:39 CEST | `REVIEW_POSTED` | `M245` | vigil | M245 review by vigil — PASS (9.3) |
| Apr 27, 06:39 CEST | `REVIEW_POSTED` | `M140` | vigil | M140 review by vigil — REVISE (5.6) |
| Apr 27, 05:48 CEST | `REVIEW_POSTED` | `M264` | vigil | M264 review by vigil — PASS (9.3) |
| Apr 27, 02:41 CEST | `REVIEW_POSTED` | `M262` | vigil | M262 review by vigil — PASS (9.15) |

## Needs Mike (open gates)

| Question ID | Question | Task | Age | Options |
|---|---|---|---|---|
| `Q-OF214-REGISTRY-1` | VIGIL REVISE 5.9 on PR #214 (FORGE detection hook). Core finding: registry files[] omits scripts/kraken-sync.py, where calculate_blended_pnl (SOUL.md §1 row 1, CRITICAL) actually lives. Detector reports clean on PnL-calc commits = false-negative in safety net. FORGE cross-check AGREES with VIGIL verdict. Two valid fix paths; Mike decides which. | `M214` | 4.0d | add_kraken_sync_path — add scripts/kraken-sync.py to registry files[] with registry_id:1, keep 'canonical SOUL.md §1 mirror' wording, full coverage (recommended; mechanically small; closes false-negative class) · narrow_contract_wording — leave registry as-is but rewrite PR body + docs to explicitly scope detector to {micro-gate-v3.py, lifecycle.py} only, open tracking issue for full SOUL.md §1 parity (smaller Round 2 diff but leaves known gap open) |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
