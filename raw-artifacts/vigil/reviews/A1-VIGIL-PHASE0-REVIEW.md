# VIGIL Proposal Review — Task A1

## signal_events Table Extension + Lifecycle Instrumentation

**Verdict:** ✅ APPROVE

**Tier:** 🔴 CRITICAL (confirmed — touches Financial Hotpath #2 `_check_sl_tp()` and #5 lifecycle SL/TP write paths)

---

## Spec Alignment

The proposal aligns with the Phase 4 spec. Specific verification:

1. **Schema extension:** The 4 columns (`field`, `old_value`, `new_value`, `source_msg_id`) match Phase 4 §1's event log schema exactly. Types and nullability are correct. The ALTER TABLE approach on a 0-row table is sound — lower risk than DROP/RECREATE.

2. **Event types:** ANVIL proposes 6 lifecycle event types for oink-sync instrumentation: `TP_HIT`, `SL_MODIFIED` (trail), `TRADE_CLOSED_SL/TP/BE`, `ORDER_FILLED`, `LIMIT_EXPIRED`, `PRICE_ALERT`. These map correctly to the `LIFECYCLE_EVENTS` set already defined in `event_store.py` (18 types). The proposal uses existing type names where they exist — no naming drift.

3. **EventStore vendoring:** The cross-repo resolution (vendor `event_store.py` into `oink_sync/event_store.py`) matches FORGE's recommended path and correctly addresses the import boundary that OINKV-AUDIT flagged. Both copies share the same DB schema via the same `_SCHEMA_SQL`, which is the right invariant to maintain.

4. **`source NOT NULL` gap:** Phase 4 spec says `source TEXT NOT NULL`. Current schema allows NULL. ANVIL proposes enforcing at application level (not schema level) — this is a pragmatic deferral. SQLite cannot ALTER COLUMN constraints, so schema-level enforcement requires a table recreate. Application-level enforcement in `EventStore.log()` is acceptable for Phase A as long as the enforcement is tested. **Note:** Ensure the test suite includes a test that verifies `source=None` is rejected or defaulted.

5. **Phase A quality gate coverage:** Phase 4 §1 says *"Event history exists: `SELECT COUNT(*) FROM signal_events` > 0 after 1 day of operation; >95% of field changes have corresponding events."* ANVIL's instrumentation of oink-sync covers the majority of field changes (SL trail, TP hits, closures, fills, expiry). The 3 deferred oinkdb-api types (ENTRY_CORRECTED, FIELD_CORRECTED, NOTE_ADDED) are low-frequency correction events — deferring them won't block the >95% gate.

6. **Index naming discrepancy (minor):** Phase 4 uses `ix_events_signal`, `ix_events_type`, `ix_events_ts`. The existing schema (from GH#22) uses `idx_events_signal`, `idx_events_time`, `idx_events_type`. ANVIL's proposal preserves the existing names. This is a cosmetic divergence — functionally equivalent. Not a blocker.

---

## Acceptance Criteria Coverage

| Phase 4 Criterion | Proposal Coverage | Assessment |
|---|---|---|
| `SELECT COUNT(*) FROM signal_events` > 0 after 1 day | Zero-event diagnostic + fix (§2C) + oink-sync instrumentation (§2D) | ✅ Covered — both the existing micro-gate bug AND the missing oink-sync integration are addressed |
| >95% of field changes have corresponding events | 6 event types in lifecycle.py + existing micro-gate types | ✅ Covered — oink-sync handles the majority of lifecycle transitions |
| Schema matches Phase 4 | ALTER TABLE for 4 missing columns (§2A) | ✅ Covered |
| Non-fatal event logging | try/except wrapper pattern (§2D, §4e) | ✅ Covered — test_event_store_failure_non_fatal in test plan |
| Quarantine functional | Regression test (§5) | ✅ Covered |
| Zero existing test regressions | All 6 existing tests must pass (AC-5 in proposal) | ✅ Covered |

**Test strategy assessment:** 12 tests proposed (5 unit, 5 integration, 2 regression). Coverage is comprehensive. The `test_event_store_failure_non_fatal` test is particularly important for a CRITICAL-tier change — it validates the core mitigation (non-fatal wrapper) for the Financial Hotpath risk.

---

## Concerns

1. **Transaction placement — verify "WITHIN" semantics.** The proposal states event logging occurs "WITHIN the existing transaction — lifecycle operations are never blocked by event store failures." This is the correct design, but the implementation must be precise: the `_log_event()` call must be BEFORE `conn.commit()`, and the try/except must be tight (wrapping only the event INSERT, not the entire transaction including the signal UPDATE). If the try/except is too broad, a failure in the event INSERT could swallow an exception from the signal UPDATE. **ANVIL should ensure the try/except scope is minimally around the event INSERT only, not around the lifecycle UPDATE + event INSERT together.**

2. **Two-copy divergence risk.** Vendoring `event_store.py` means two independent copies. The proposal acknowledges this but has no convergence mechanism. This is acceptable for Phase A (both copies are small, 209 LOC, and share the same schema). Flag for Phase B: the PostgreSQL migration should consolidate to a single source. Not a blocker.

3. **PRICE_ALERT event volume.** The proposal estimates 0-10 PRICE_ALERT events per cycle (~60s). At 10/cycle × 1440 cycles/day = up to 14,400 events/day. This is still fine for SQLite but significantly higher than the 50-200/day estimate for other event types. ANVIL should consider whether PRICE_ALERT needs deduplication (e.g., don't emit if the same signal already had a PRICE_ALERT within the last N minutes). Not a blocker for the proposal — can be tuned during Phase 1 review.

4. **Zero-event diagnostic is hypothesis-driven.** ANVIL's hypothesis (transaction/connection issue) is reasonable but unconfirmed. The proposal correctly includes diagnostic logging as a first step. If the root cause is different from the hypothesis (e.g., deployment version mismatch), the fix may differ from what's described. This is fine — the proposal acknowledges the diagnostic is the first action and the fix depends on findings.

---

## Suggestions

1. **Consider a simple version marker in the vendored `event_store.py`.** A comment like `# Vendored from oinkfarm commit <hash>, date <date>` at the top of `oink_sync/event_store.py` would make divergence tracking trivial. No code change needed — just a comment.

2. **The oinkdb-api.py deferral is sound.** FastAPI's async connection pooling is a genuinely different integration pattern. Keeping A1 focused on the synchronous oink-sync path is the right scoping decision.

3. **DQ-1 (Schema Extension vs JSON-only):** VIGIL concurs with FORGE and ANVIL — Option A (ALTER TABLE) is correct per Phase 4 spec and provides structured query capability. No design question escalation needed.

4. **DQ-2 (oinkdb-api.py scope) and DQ-3 (Reconciler):** Both deferrals are reasonable. However, these should be tracked as follow-up tasks (A1b or similar) to avoid losing them. ANVIL should create followup tracking files similar to the LIMIT-FILLED-AT-NULLS.md pattern from A3.

---

## Summary

This is a well-structured proposal for a CRITICAL-tier task. The approach is sound: extend the existing schema (low risk on a 0-row table), diagnose the zero-event production bug before adding more instrumentation, vendor the cross-repo dependency (proven pattern), and instrument the live lifecycle engine with non-fatal event logging. The test strategy covers all acceptance criteria and includes the essential non-fatal failure test.

The scoping decisions (defer oinkdb-api.py and reconciler instrumentation) are pragmatic and won't block the Phase A quality gate.

ANVIL may proceed to Phase 1 (implementation on feature branch).
