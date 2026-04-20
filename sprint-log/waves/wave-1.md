# Wave 1 (Phase A) Retrospective

**Focus:** Core schema & formula primitives — events, remaining_pct, auto filled_at.

**Status:** 3/3 shipped · 0 in flight · 0 planned

## Tasks

| Task | Name | Tier | Status | Canary | Merge commit |
|---|---|---|---|---|---|
| [A1](../tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | ✅ DONE | PASS | [`5b242c5`](https://github.com/QuantisDevelopment/oinkfarm/commit/5b242c567d0df4b8b25d3866e711f15d772e685a) |
| [A2](../tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | ✅ DONE | PASS | [`6b21a20`](https://github.com/QuantisDevelopment/oink-sync/commit/6b21a2074413395b400b6f95494ae80d77ecef59) |
| [A3](../tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | ✅ DONE | PASS | [`3b5453b`](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7) |

## Timing

- Wave start: 23:27 CEST on 18 Apr 2026
- Last activity: 02:43 CEST on 20 Apr 2026
- Elapsed: 27.3 h

## Canary Outcomes

- **A1**: ✅ PASS
- **A2**: ✅ PASS
- **A3**: ✅ PASS

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
