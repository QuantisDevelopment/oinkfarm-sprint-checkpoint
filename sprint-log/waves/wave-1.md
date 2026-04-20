# Wave 1 (Phase A) Retrospective

**Focus:** Core schema & formula primitives — events, remaining_pct, auto filled_at.

**Status:** 0/3 shipped · 0 in flight · 3 planned

## Tasks

| Task | Name | Tier | Status | Canary | Merge commit |
|---|---|---|---|---|---|
| [A1](../tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | ⏳ NOT STARTED | — | — |
| [A2](../tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | ⏳ NOT STARTED | — | — |
| [A3](../tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | ⏳ NOT STARTED | — | — |

## Timing

- (No timeline events yet.)

## Canary Outcomes

_No canary verdicts yet._

## Deferred Follow-ups

- [A1-DEFERRED-OINKDB-API.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-OINKDB-API.md) — Deferred: oinkdb-api.py Event Instrumentation
- [A1-DEFERRED-RECONCILER.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-RECONCILER.md) — Deferred: Reconciler GHOST_CLOSURE Instrumentation
- [A2-DEFERRED-ACTIVE-BACKFILL.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-ACTIVE-BACKFILL.md) — ✅ CLOSED: Backfill remaining_pct on ACTIVE Signals
- [A2-DEFERRED-CLOSE-PCT-EXTRACTION.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-CLOSE-PCT-EXTRACTION.md) — Deferred: Provider Text close_pct Extraction

## Lessons Learned

- **FORGE → ANVIL → VIGIL/GUARDIAN → Hermes** pattern cleared three tasks in one overnight push (22:00–04:42 CEST).
- **A1 zero-event root cause** caught a silent production gap — the 12 event types weren't firing at all. Canary fallback saved the day.
- **A2 blended-PnL fix** landed first because every downstream task depends on `remaining_pct` arithmetic being correct.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
