# Task A1 — signal_events Table + 12 Event Type Instrumentation

**Tier:** 🔴 CRITICAL  
**Wave:** 1  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [signal-gateway#17](https://github.com/QuantisDevelopment/signal-gateway/pull/17) + [signal-gateway#18](https://github.com/QuantisDevelopment/signal-gateway/pull/18) + [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) + [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4)  
**Merge commit:** [9fa2d1937da5](https://github.com/QuantisDevelopment/signal-gateway/commit/9fa2d1937da5a16aef5834645abd504a5eff2df4) + [5b242c567d0d](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) + [3d60538acc0f](https://github.com/QuantisDevelopment/oink-sync/commit/3d60538acc0fb696b41da151d9062cd9896ad790)

## One-liner

signal_events Table + 12 Event Type Instrumentation — see plan for details.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | FINDINGS | 23:23 CEST on 18 Apr 2026 | [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) |
| 2 | Phase 0 review | 🛡️ GUARDIAN | ✅ APPROVE | 00:14 CEST on 19 Apr 2026 | [A1-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE0-REVIEW.md) |
| 3 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 00:20 CEST on 19 Apr 2026 | [A1-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A1-PHASE0-APPROVED.marker) |
| 4 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [signal-gateway#17](https://github.com/QuantisDevelopment/signal-gateway/pull/17) + [signal-gateway#18](https://github.com/QuantisDevelopment/signal-gateway/pull/18) + [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) + [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

- [A1-DEFERRED-OINKDB-API.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-OINKDB-API.md) — Deferred: oinkdb-api.py Event Instrumentation
- [A1-DEFERRED-RECONCILER.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-RECONCILER.md) — Deferred: Reconciler GHOST_CLOSURE Instrumentation

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) — 23.4 KB
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A1-GUARDIAN-PHASE0-REVIEW.md)
- **Merge commit:** [`9fa2d1937da5`](https://github.com/QuantisDevelopment/signal-gateway/commit/9fa2d1937da5a16aef5834645abd504a5eff2df4) (signal-gateway PR #18)
- **Merge commit:** [`5b242c567d0d`](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) (oinkfarm PR #126)
- **Merge commit:** [`3d60538acc0f`](https://github.com/QuantisDevelopment/oink-sync/commit/3d60538acc0fb696b41da151d9062cd9896ad790) (oink-sync PR #4)
- **PR(s):** [signal-gateway#17](https://github.com/QuantisDevelopment/signal-gateway/pull/17) · [signal-gateway#18](https://github.com/QuantisDevelopment/signal-gateway/pull/18) · [oinkfarm#126](https://github.com/QuantisDevelopment/oinkfarm/pull/126) · [oink-sync#4](https://github.com/QuantisDevelopment/oink-sync/pull/4)

## Lessons Learned

_(Lessons distilled at wave close.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
