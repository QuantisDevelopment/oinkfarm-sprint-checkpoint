# OinkFarm Implementation Foresight Sprint — Archive

Human-readable per-task archive. For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).

## Waves

| Wave | Focus | Tasks | Status |
|---|---|---|---|
| [Wave 1 (Phase A)](waves/wave-0.md) | — | [A1](tasks/A1-signal-events-schema.md) · [A2](tasks/A2-remaining-pct-model.md) · [A3](tasks/A3-auto-filled-at.md) | 3/3 shipped |
| [Wave 2 (Phase A)](waves/wave-0.md) | — | [A4](tasks/A4-partially-closed-status.md) · [A7](tasks/A7-update-new-detection.md) · [A5](tasks/A5-confidence-scoring.md) | 2/3 shipped |
| [Wave 3 (Phase A)](waves/wave-0.md) | — | [A6](tasks/A6-a6.md) · [A8](tasks/A8-a8.md) · [A9](tasks/A9-a9.md) · [A11](tasks/A11-a11.md) | 3/4 shipped |
| [Wave 4 (Phase A)](waves/wave-0.md) | — | [A10](tasks/A10-a10.md) | 1/1 shipped |
| [Wave B1 (Phase B)](waves/wave-0.md) | — | [B1](tasks/B1-b1.md) | 0/1 shipped |

## Tasks

| Task | Name | Tier | Wave | Status | Canary |
|---|---|---|---|---|---|
| [A1](tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A2](tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | 1 | ✅ DONE | PASS |
| [A3](tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | 1 | ✅ DONE | PASS |
| [A4](tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 2 | ✅ DONE | PASS |
| [A7](tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 2 | 🧪 CANARY | PENDING |
| [A5](tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | 2 | ✅ DONE | PASS |
| [A6](tasks/A6-a6.md) | A6 | 🟡 STANDARD | — | ✅ DONE | PASS |
| [A8](tasks/A8-a8.md) | A8 | 🟡 STANDARD | — | 🧪 CANARY | PENDING |
| [A9](tasks/A9-a9.md) | A9 | 🟢 LIGHTWEIGHT | — | ✅ DONE | PASS |
| [A11](tasks/A11-a11.md) | A11 | 🟢 LIGHTWEIGHT | — | ✅ DONE | PASS |
| [A10](tasks/A10-a10.md) | A10 | 🔴 CRITICAL | — | ✅ DONE | PASS |
| [B1](tasks/B1-b1.md) | B1 | 🔴 CRITICAL | — | 📝 PROPOSAL | — |

## Agents

| Emoji | Name | Role |
|---|---|---|
| 🔥 | FORGE | Technical Execution Planner |
| ⚒️ | ANVIL | Implementation Lead |
| 🔍 | VIGIL | Code Review + Scoring |
| 🛡️ | GUARDIAN | Data Integrity + Canary |
| 🪽 | Hermes | Sprint Orchestrator |
| 🐷 | OinkV | Plan Auditor |

## Conventions

- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT (per Arbiter-Oink Phase 4 governance)
- **Auto-escalation:** if a diff touches one of the 7 Financial Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.
- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → CODE → PR_REVIEW → CANARY → DONE
- **Timestamps** are rendered in CEST (UTC+2).

---

*Last auto-regenerated: 22:38 CEST on 19 Apr 2026 · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint)*
