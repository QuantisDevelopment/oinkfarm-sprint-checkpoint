# Task A7 — UPDATE→NEW Detection (Phantom Trade Prevention)

**Tier:** 🔴 CRITICAL — Financial Hotpath from inception  
**Wave:** 2  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** signal-gateway  
**Branch:** —  
**PR:** [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130) + [signal-gateway#130](https://github.com/QuantisDevelopment/signal-gateway/pull/130)  
**Merge commit:** [615731582e75](https://github.com/QuantisDevelopment/oinkfarm/commit/615731582e75b7a451dc84a12915839ada6503a8)

## In plain English

A7 added UPDATE→NEW dedup with 5% tolerance to prevent phantom trades. Without this, a stream re-broadcast or tiny price wiggle could create a duplicate signal and fire a real order twice.

## One-liner

UPDATE→NEW Detection (Phantom Trade Prevention) — see plan for details.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 11:31 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE2-A7.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A7.md) |
| 2 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 12:50 CEST on 19 Apr 2026 | [A7-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE0-REVIEW.md) |
| 3 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 12:55 CEST on 19 Apr 2026 | [A7-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A7-PHASE0-APPROVED.marker) |
| 4 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130) + [signal-gateway#130](https://github.com/QuantisDevelopment/signal-gateway/pull/130) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE2-A7.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A7.md) — 21.8 KB
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A7-GUARDIAN-PHASE0-REVIEW.md)
- **Merge commit:** [`615731582e75`](https://github.com/QuantisDevelopment/oinkfarm/commit/615731582e75b7a451dc84a12915839ada6503a8) (oinkfarm PR #130)
- **PR(s):** [oinkfarm#130](https://github.com/QuantisDevelopment/oinkfarm/pull/130) · [signal-gateway#130](https://github.com/QuantisDevelopment/signal-gateway/pull/130)

## Lessons Learned

_(Lessons distilled at wave close.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
