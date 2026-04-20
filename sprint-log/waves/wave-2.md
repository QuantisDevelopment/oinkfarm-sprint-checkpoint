# Wave 2 (Phase A) Retrospective

**Focus:** Lifecycle accuracy & phantom-trade prevention — partial closes, confidence scoring, UPDATE→NEW dedup.

**Status:** 2/3 shipped · 1 in flight · 0 planned

## Tasks

| Task | Name | Tier | Status | Canary | Merge commit |
|---|---|---|---|---|---|
| [A4](../tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | ✅ DONE | PASS | [`e9be741`](https://github.com/QuantisDevelopment/oink-sync/commit/e9be741a7a0c0d779b259c9e1813e3aeac59ca0a) |
| [A7](../tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 🧪 CANARY | PENDING | [`6157315`](https://github.com/QuantisDevelopment/oinkfarm/commit/615731582e75b7a451dc84a12915839ada6503a8) |
| [A5](../tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | ✅ DONE | PASS | [`69d6840`](https://github.com/QuantisDevelopment/oinkfarm/commit/69d6840a792ad685ad606c74d098180b8ccd5b71) |

## Timing

- Wave start: 02:47 CEST on 19 Apr 2026
- Last activity: 23:32 CEST on 20 Apr 2026
- Elapsed: 44.8 h

## Canary Outcomes

- **A4**: ✅ PASS
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
