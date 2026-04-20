# Task A5 — Parser-Type Confidence Scoring

**Tier:** 🟡 STANDARD  
**Wave:** 2  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** signal-gateway  
**Branch:** —  
**PR:** [oinkfarm#131](https://github.com/QuantisDevelopment/oinkfarm/pull/131) + [signal-gateway#131](https://github.com/QuantisDevelopment/signal-gateway/pull/131)  
**Merge commit:** [69d6840a792a](https://github.com/QuantisDevelopment/oinkfarm/commit/69d6840a792ad685ad606c74d098180b8ccd5b71)

## In plain English

A5 introduced parser-type confidence scoring (regex / board / LLM weights) so we can tell which parser produced a signal and how much to trust it. This is the foundation for Phase C confidence routing.

## One-liner

Parser-Type Confidence Scoring — see plan for details.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 11:32 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE2-A5.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A5.md) |
| 2 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 13:32 CEST on 19 Apr 2026 | [A5-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A5-GUARDIAN-PHASE0-REVIEW.md) |
| 3 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 13:41 CEST on 19 Apr 2026 | [A5-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A5-PHASE0-APPROVED.marker) |
| 4 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oinkfarm#131](https://github.com/QuantisDevelopment/oinkfarm/pull/131) + [signal-gateway#131](https://github.com/QuantisDevelopment/signal-gateway/pull/131) |
| 5 | Phase 1 review | 🔍 VIGIL | 9.85/10 | 14:01 CEST on 19 Apr 2026 | [A5-VIGIL-PHASE1-REVIEW-R2.md](../../raw-artifacts/vigil/reviews/A5-VIGIL-PHASE1-REVIEW-R2.md) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE2-A5.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A5.md) — 18.9 KB
- **VIGIL reviews:** [Phase 1](../../raw-artifacts/vigil/reviews/A5-VIGIL-PHASE1-REVIEW-R2.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A5-GUARDIAN-PHASE0-REVIEW.md)
- **Merge commit:** [`69d6840a792a`](https://github.com/QuantisDevelopment/oinkfarm/commit/69d6840a792ad685ad606c74d098180b8ccd5b71) (oinkfarm PR #131)
- **PR(s):** [oinkfarm#131](https://github.com/QuantisDevelopment/oinkfarm/pull/131) · [signal-gateway#131](https://github.com/QuantisDevelopment/signal-gateway/pull/131)

## Lessons Learned

_(Lessons distilled at wave close.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
