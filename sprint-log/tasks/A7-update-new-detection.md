# Task A7 — UPDATE→NEW Detection (Phantom Trade Prevention)

**Tier:** 🔴 CRITICAL — Financial Hotpath from inception  
**Wave:** 2  
**Status:** 🧪 CANARY — Merged, canary in flight  
**Repo target:** signal-gateway  
**Branch:** —  
**PR:** [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130)  
**Merge commit:** [61573158](https://github.com/QuantisDevelopment/oinkfarm/commit/61573158)

## One-liner

When an LLM extraction classifies a trader UPDATE message (e.g., "SL moved to 0.48") as a NEW signal, the current INSERT path creates a phantom duplicate — a second signal for the same trader/ticker/direction alongside the real one.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 11:40 CEST on 19 Apr 2026 | [TASK-A7-plan.md](../../raw-artifacts/forge/plans/TASK-A7-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | PASS | 11:31 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE2-A7.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A7.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 12:48 CEST on 19 Apr 2026 | [A7-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A7-PHASE0-PROPOSAL.md) |
| 4 | Phase 0 review | 🔍 VIGIL | ❌ BLOCK | 12:52 CEST on 19 Apr 2026 | [A7-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A7-VIGIL-PHASE0-REVIEW.md) |
| 5 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 12:50 CEST on 19 Apr 2026 | [A7-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE0-REVIEW.md) |
| 6 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 12:55 CEST on 19 Apr 2026 | [A7-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A7-PHASE0-APPROVED.marker) |
| 7 | Phase 1 code | ⚒️ ANVIL | MERGED | 13:27 CEST on 19 Apr 2026 | [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130) |
| 8 | Phase 1 review | 🔍 VIGIL | 10.00/10 | 13:11 CEST on 19 Apr 2026 | [A7-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A7-VIGIL-PHASE1-REVIEW.md) |
| 9 | Phase 1 review | 🛡️ GUARDIAN | 10.00/10 | 13:09 CEST on 19 Apr 2026 | [A7-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE1-REVIEW.md) |
| 10 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 13:26 CEST on 19 Apr 2026 | [A7-HERMES-REVIEW.md](../../raw-artifacts/hermes/A7-HERMES-REVIEW.md) |
| 11 | Merged | ⚒️ ANVIL | MERGED [6157315](https://github.com/QuantisDevelopment/oinkfarm/commit/61573158) | 13:27 CEST on 19 Apr 2026 | [A7-MERGED.marker](../../raw-artifacts/anvil/markers/A7-MERGED.marker) |
| 12 | Canary | 🛡️ GUARDIAN | ⏳ PENDING | 22:38 CEST on 19 Apr 2026 | [A7-CANARY.md](../../raw-artifacts/guardian/canary-reports/A7-CANARY.md) |

## Key Decisions

- diff **≤ 5.0%** → `else` branch → suppress ✅
- diff **> 5.0%** → allow ✅

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A7-plan.md](../../raw-artifacts/forge/plans/TASK-A7-plan.md) — 22.1 KB
- **OinkV audit:** [OINKV-AUDIT-WAVE2-A7.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A7.md) — 21.8 KB
- **ANVIL proposal:** [A7-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A7-PHASE0-PROPOSAL.md) — 14.7 KB
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A7-VIGIL-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/vigil/reviews/A7-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A7-HERMES-REVIEW.md](../../raw-artifacts/hermes/A7-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A7-CANARY.md](../../raw-artifacts/guardian/canary-reports/A7-CANARY.md) — PENDING
- **Merge commit:** [`61573158`](https://github.com/QuantisDevelopment/oinkfarm/commit/61573158) (oinkfarm PR #130)
- **PR(s):** [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
