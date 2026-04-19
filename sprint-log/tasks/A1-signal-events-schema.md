# Task A1 — signal_events Table + 12 Event Type Instrumentation

**Tier:** 🔴 CRITICAL  
**Wave:** 1  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) + [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4)  
**Merge commit:** [5b242c567d0d](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) + [3d60538acc0f](https://github.com/QuantisDevelopment/oink-sync/commit/3d60538acc0fb696b41da151d9062cd9896ad790)

## One-liner

The `signal_events` table and `EventStore` class already exist (GH#22, commit `387a8a4d`).

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 23:27 CEST on 18 Apr 2026 | [TASK-A1-plan.md](../../raw-artifacts/forge/plans/TASK-A1-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | FINDINGS | 23:23 CEST on 18 Apr 2026 | [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 00:10 CEST on 19 Apr 2026 | [A1-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A1-PHASE0-PROPOSAL.md) |
| 4 | Phase 0 review | 🔍 VIGIL | ❌ BLOCK | 00:13 CEST on 19 Apr 2026 | [A1-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A1-VIGIL-PHASE0-REVIEW.md) |
| 5 | Phase 0 review | 🛡️ GUARDIAN | ✅ APPROVE | 00:14 CEST on 19 Apr 2026 | [A1-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE0-REVIEW.md) |
| 6 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 00:20 CEST on 19 Apr 2026 | [A1-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A1-PHASE0-APPROVED.marker) |
| 7 | Phase 1 code | ⚒️ ANVIL | MERGED | 01:48 CEST on 19 Apr 2026 | [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) + [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4) |
| 8 | Phase 1 review | 🔍 VIGIL | 9.60/10 | 01:30 CEST on 19 Apr 2026 | [A1-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A1-VIGIL-PHASE1-REVIEW.md) |
| 9 | Phase 1 review | 🛡️ GUARDIAN | 9.80/10 | 01:19 CEST on 19 Apr 2026 | [A1-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE1-REVIEW.md) |
| 10 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 01:47 CEST on 19 Apr 2026 | [A1-HERMES-REVIEW.md](../../raw-artifacts/hermes/A1-HERMES-REVIEW.md) |
| 11 | Merged | ⚒️ ANVIL | MERGED [5b242c5](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) + [3d60538](https://github.com/QuantisDevelopment/oink-sync/commit/3d60538acc0fb696b41da151d9062cd9896ad790) | 01:48 CEST on 19 Apr 2026 | [A1-MERGED.marker](../../raw-artifacts/anvil/markers/A1-MERGED.marker) |
| 12 | Canary | 🛡️ GUARDIAN | ✅ PASS | 01:51 CEST on 19 Apr 2026 | [A1-CANARY.md](../../raw-artifacts/guardian/canary-reports/A1-CANARY.md) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

- [A1-DEFERRED-OINKDB-API.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-OINKDB-API.md) — Deferred: oinkdb-api.py Event Instrumentation
- [A1-DEFERRED-RECONCILER.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-RECONCILER.md) — Deferred: Reconciler GHOST_CLOSURE Instrumentation

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A1-plan.md](../../raw-artifacts/forge/plans/TASK-A1-plan.md) — 22.3 KB
- **OinkV audit:** [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) — 23.4 KB
- **ANVIL proposal:** [A1-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A1-PHASE0-PROPOSAL.md) — 14.2 KB
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A1-VIGIL-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/vigil/reviews/A1-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A1-HERMES-REVIEW.md](../../raw-artifacts/hermes/A1-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A1-CANARY.md](../../raw-artifacts/guardian/canary-reports/A1-CANARY.md) — PASS
- **Merge commit:** [`5b242c567d0d`](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) (oinkfarm PR #126)
- **Merge commit:** [`3d60538acc0f`](https://github.com/QuantisDevelopment/oink-sync/commit/3d60538acc0fb696b41da151d9062cd9896ad790) (oink-sync PR #4)
- **PR(s):** [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) · [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4)

## Lessons Learned

_(Lessons distilled at wave close.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
