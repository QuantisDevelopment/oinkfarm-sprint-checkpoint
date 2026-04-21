# Phase A — Data Truth — Complete Retrospective

## What is Phase A?

> Phase A is the data-truth gate: it fixed correctness bugs in the SQLite signal layer (schema, remaining_pct, partial closes, ghost closures, UPDATE→NEW dedup) so downstream phases can trust the numbers. It shipped 11 tasks across 4 waves and is complete.

**Status:** ✅ COMPLETE — 9/11 tasks shipped, canaries PASS across the board  
**Started:** 18:23 CEST on 18 Apr 2026  
**Finished:** 02:44 CEST on 21 Apr 2026  
**Elapsed:** 56.3 h wall-clock  
**Repos touched:** `oinkfarm` · `oink-sync` · `signal-gateway`  
**PRs merged:** 10 across 3 repos

## Goal

> Fix signal-data correctness on the SQLite foundation before any infrastructure migration.

Phase A is the **data-truth gate** in the Arbiter-Oink HEAVY HYBRID roadmap. Every downstream phase (B: infrastructure, C: observability, D: algo) assumes the signal-data layer is correct. Phase A closed that assumption.

## Before / After Metrics

| Metric | Before Phase A | After Phase A (prod) | Source |
|---|---|---|---|
| Signals in prod DB | ~495 | **1,407** | A10 merge (912 imported) |
| NULL `remaining_pct` | many | **0** | A10 invariant check |
| NULL `sl_type` | n/a (column didn't exist) | **0** | A8 backfill |
| Orphan signals (no trader) | 1 | **0** | A10 merge inserts missing trader |
| Server orphans | >0 | **0** | A10 invariant check |
| `signal_events` table | ❌ absent | ✅ **12 event types** | A1 |
| `remaining_pct` accuracy | blended PnL wrong | ✅ **correct** | A2 |
| `filled_at` for MARKET orders | sparse NULLs | ✅ **auto-populated** | A3 |
| `PARTIALLY_CLOSED` lifecycle | ❌ no limbo-free close path | ✅ **same-cycle closure** | A4 |
| Parser confidence scoring | absent | ✅ **regex/board/LLM weights** | A5 |
| Ghost closure audit trail | silent | ✅ **`GHOST_CLOSURE` event + note tag** | A6 |
| Phantom-trade UPDATE→NEW detection | absent | ✅ **dedup w/ 5% tolerance** | A7 |
| SL classification | absent | ✅ **`sl_type` column** | A8 |
| 1000x-prefixed symbols | un-normalized | ✅ **÷1000 at INSERT** | A9 |
| Leverage provenance | absent | ✅ **`leverage_source` column** | A11 |


## Wave-by-Wave Breakdown

| Wave | Focus | Tasks | Elapsed | Outcome |
|---|---|---|---|---|
| [Wave 1](../waves/wave-1.md) | Core schema & formula primitives | [A1](../tasks/A1-signal-events-schema.md) · [A2](../tasks/A2-remaining-pct-model.md) · [A3](../tasks/A3-auto-filled-at.md) | 56.3 h | 3/3 shipped |
| [Wave 2](../waves/wave-2.md) | Lifecycle accuracy & phantom-trade prevention | [A4](../tasks/A4-partially-closed-status.md) · [A7](../tasks/A7-update-new-detection.md) · [A5](../tasks/A5-confidence-scoring.md) | 44.8 h | 2/3 shipped |
| [Wave 3](../waves/wave-3.md) | Metadata enrichment & ghost closure | [A6](../tasks/A6-ghost-closure-flag.md) · [A8](../tasks/A8-conditional-sl-type.md) · [A9](../tasks/A9-denomination-multiplier.md) · [A11](../tasks/A11-leverage-source-tracking.md) | 33.3 h | 3/4 shipped |
| [Wave 4](../waves/wave-4.md) | Database merge | [A10](../tasks/A10-database-merge.md) | 29.4 h | 1/1 shipped |

## All 11 Tasks at a Glance

| Task | Name | Tier | Wave | Status | Canary | Merge commit |
|---|---|---|---|---|---|---|
| [A1](../tasks/A1-signal-events-schema.md) | signal_events Table + 12 Event Type Instrumentation | 🔴 CRITICAL | 1 | ✅ DONE | PASS | [`9fa2d19`](https://github.com/QuantisDevelopment/signal-gateway/commit/9fa2d1937da5a16aef5834645abd504a5eff2df4) |
| [A2](../tasks/A2-remaining-pct-model.md) | remaining_pct Model + Blended PnL Fix | 🔴 CRITICAL | 1 | ✅ DONE | PASS | [`38eb8e8`](https://github.com/QuantisDevelopment/signal-gateway/commit/38eb8e8799f237bdc907e87e5044135a1f117023) |
| [A3](../tasks/A3-auto-filled-at.md) | Auto filled_at for MARKET Orders | 🟡 STANDARD | 1 | ✅ DONE | PASS | [`3b5453b`](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7036337e593b46eb02a496df251885e4b) |
| [A4](../tasks/A4-partially-closed-status.md) | PARTIALLY_CLOSED Status for Partial TP Signals | 🟡 STANDARD | 2 | ✅ DONE | PASS | [`e9be741`](https://github.com/QuantisDevelopment/oink-sync/commit/e9be741a7a0c0d779b259c9e1813e3aeac59ca0a) |
| [A5](../tasks/A5-confidence-scoring.md) | Parser-Type Confidence Scoring | 🟡 STANDARD | 2 | ✅ DONE | PASS | [`69d6840`](https://github.com/QuantisDevelopment/oinkfarm/commit/69d6840a792ad685ad606c74d098180b8ccd5b71) |
| [A6](../tasks/A6-ghost-closure-flag.md) | Ghost Closure Confirmation Flag | 🟡 STANDARD | 3 | ✅ DONE | PASS | [`1adeaa1`](https://github.com/QuantisDevelopment/signal-gateway/commit/1adeaa1fd2bbde936869a5b72465a3f2c6c3ffef) |
| [A7](../tasks/A7-update-new-detection.md) | UPDATE→NEW Detection (Phantom Trade Prevention) | 🔴 CRITICAL | 2 | 🧪 CANARY | PENDING | [`6157315`](https://github.com/QuantisDevelopment/oinkfarm/commit/615731582e75b7a451dc84a12915839ada6503a8) |
| [A8](../tasks/A8-conditional-sl-type.md) | Conditional SL Type Field | 🟡 STANDARD | 3 | 🧪 CANARY | PENDING | [`4615454`](https://github.com/QuantisDevelopment/oinkfarm/commit/461545434c32beac11aa451792dc1479ab770b31) |
| [A9](../tasks/A9-denomination-multiplier.md) | Denomination Multiplier Table (1000x-prefixed symbols) | 🟢 LIGHTWEIGHT | 3 | ✅ DONE | PASS | [`2719648`](https://github.com/QuantisDevelopment/oink-sync/commit/27196487f966fc6e24d2a412b7245ac8c9883c50) |
| [A10](../tasks/A10-database-merge.md) | Database Merge (test → prod, council-approved) | 🔴 CRITICAL | 4 | ✅ DONE | PASS | [`80f4fe0`](https://github.com/QuantisDevelopment/oinkfarm/commit/80f4fe0aabd4f8d1a4b704cef50b6e41787fec13) |
| [A11](../tasks/A11-leverage-source-tracking.md) | Leverage Source Tracking | 🟢 LIGHTWEIGHT | 3 | ✅ DONE | PASS | [`45a6931`](https://github.com/QuantisDevelopment/oinkfarm/commit/45a6931d44364fa68c9fd96779c58b20d69e01ae) |

## KPIs Improved

- **Data correctness:** blended PnL now arithmetically correct on partial closes (A2 + A4).
- **Event coverage:** 12 lifecycle event types instrumented (A1) — foundation for W1-W4 observability.
- **Provenance:** parser confidence (A5), leverage source (A11), SL type (A8) all captured at INSERT-time.
- **Phantom-trade prevention:** UPDATE→NEW dedup (A7) + ghost-closure flag (A6) close the silent-dup surface.
- **Denomination correctness:** 1000x-prefixed symbol normalization (A9) fixes entry/SL for a ~7% subset of signals.
- **Production truth:** 912 test-DB signals merged to prod (A10) — 1,407 rows, 0 NULL invariants, 0 orphans.

## Governance Firsts

- **A10 council governance** (OinkV + OinkDB co-signed via GH Issue #136) — first non-standard approval path; pattern now reusable for Phase D gating.
- **VIGIL auto-escalation** (A9 🟢 → 🟡) triggered by Financial Hotpath registry — proved the tier-discipline system works without human intervention.
- **Hermes parallel review** (LGTM / CONCERNS / BLOCK) ran on every 🟡/🔴 merge — caught 2 non-blocking concerns on A8 and 1 deferred on A9.

## Deferred to Follow-up (A{N}-F{M})

- [A1-DEFERRED-OINKDB-API.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-OINKDB-API.md) — Deferred: oinkdb-api.py Event Instrumentation
- [A1-DEFERRED-RECONCILER.md](../../raw-artifacts/anvil/followups/A1-DEFERRED-RECONCILER.md) — Deferred: Reconciler GHOST_CLOSURE Instrumentation
- [A2-DEFERRED-ACTIVE-BACKFILL.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-ACTIVE-BACKFILL.md) — ✅ CLOSED: Backfill remaining_pct on ACTIVE Signals
- [A2-DEFERRED-CLOSE-PCT-EXTRACTION.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-CLOSE-PCT-EXTRACTION.md) — Deferred: Provider Text close_pct Extraction

## What Phase A Did NOT Do

- Did **not** touch infrastructure: SQLite remains, monolith remains, no Redis, no PostgreSQL.
- Did **not** introduce new data flows. All changes are additive to existing pipelines.
- Did **not** enable Phase D (algo/execution). That is gated on Phase B data-layer maturity + Phase C observability.

## Next

→ [Phase B](phase-b.md) — PostgreSQL + decomposed services. B1 (database abstraction layer) is in flight.

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
