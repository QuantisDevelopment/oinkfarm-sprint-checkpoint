# Wave 1 (Phase A) Retrospective

**Focus:** Core schema & formula primitives — events, remaining_pct, auto filled_at.

**Status:** 3/3 shipped · 0 in flight · 0 planned

## Tasks

| Task | Name | Tier | Status | Canary | Merge commit |
|---|---|---|---|---|---|
| [A1](../tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | ✅ DONE | PASS | [`9fa2d19`](https://github.com/QuantisDevelopment/signal-gateway/commit/9fa2d1937da5a16aef5834645abd504a5eff2df4) |
| [A2](../tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | ✅ DONE | PASS | [`38eb8e8`](https://github.com/QuantisDevelopment/signal-gateway/commit/38eb8e8799f237bdc907e87e5044135a1f117023) |
| [A3](../tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | ✅ DONE | PASS | [`3b5453b`](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7036337e593b46eb02a496df251885e4b) |

## Timing

- Wave start: 18:23 CEST on 18 Apr 2026
- Last activity: 00:09 CEST on 21 Apr 2026
- Elapsed: 53.8 h

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
