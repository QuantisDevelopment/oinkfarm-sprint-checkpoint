# Wave 2 (Phase A) Retrospective

**Focus:** Lifecycle accuracy & phantom-trade prevention — partial closes, confidence scoring, UPDATE→NEW dedup.

**Status:** 1/3 shipped · 2 in flight · 0 planned

## Tasks

| Task | Name | Tier | Status | Canary | Merge commit |
|---|---|---|---|---|---|
| [A4](../tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 🛑 BLOCKED | FAIL | — |
| [A7](../tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 🧪 CANARY | PENDING | — |
| [A5](../tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | ✅ DONE | PASS | — |

## Timing

- Wave start: 02:47 CEST on 19 Apr 2026
- Last activity: 22:38 CEST on 19 Apr 2026
- Elapsed: 19.9 h

## Canary Outcomes

- **A4**: ❌ FAIL
- **A7**: ⏳ PENDING
- **A5**: ✅ PASS

## Deferred Follow-ups

_None._

## Lessons Learned

- **Same-cycle closure** (A4) is the canonical example of avoiding partial-state limbo — atomic UPDATE carries the whole transition.
- **A7 UPDATE→NEW detection** uses the same entry-price discriminator (5% tolerance) that A6 later reused for ghost closure — good pattern emerging.
- **A5 confidence scoring** came out of Phase 0 clean — additive column + INSERT-time logic, zero blast radius.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
