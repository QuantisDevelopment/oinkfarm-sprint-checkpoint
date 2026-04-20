# Task A6 — Ghost Closure Confirmation Flag

**Tier:** 🟡 STANDARD  
**Wave:** 3  
**Status:** 🛑 BLOCKED — Blocked on decision or dependency  
**Repo target:** signal-gateway  
**Branch:** —  
**PR:** [signal-gateway#20](https://github.com/QuantisDevelopment/signal-gateway/pull/20)  
**Merge commit:** —

## In plain English

A6 emits a GHOST_CLOSURE event + note tag whenever the reconciler soft-closes a signal on board-absent. Purely additive, no financial writes — gives us an audit trail for closures that previously happened silently.

## One-liner

Emit a `GHOST_CLOSURE` lifecycle event + additive note tag whenever the reconciler soft-closes a signal on `board_absent`; purely additive, no financial field writes.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 14:45 CEST on 19 Apr 2026 | [A6-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE0-REVIEW.md) |
| 2 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 14:55 CEST on 19 Apr 2026 | [A6-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A6-PHASE0-APPROVED.marker) |
| 3 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [signal-gateway#20](https://github.com/QuantisDevelopment/signal-gateway/pull/20) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE0-REVIEW.md)
- **PR(s):** [signal-gateway#20](https://github.com/QuantisDevelopment/signal-gateway/pull/20)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
