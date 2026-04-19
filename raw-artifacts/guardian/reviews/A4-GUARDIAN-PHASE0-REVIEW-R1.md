# 🛡️ GUARDIAN Proposal Review — Task A4 (Revision 1)

**Verdict:** ✅ APPROVE

**Task:** A4 — PARTIALLY_CLOSED Status for Partial TP Signals
**Tier:** 🟡 STANDARD (auto-escalates to 🔴 CRITICAL in Phase 1)
**Review Date:** 2026-04-19
**Previous Verdict:** REQUEST CHANGES (4 blocking concerns)

---

## Concern Resolution

### Concern #1: Scope too narrow → ✅ RESOLVED

Revision 1 adds 5 engine.py sites (E1–E5) to the blast radius. The critical find is **E5** (`_calculate_pnl()` line 458): without this fix, `_write_prices_to_db()` would fetch PARTIALLY_CLOSED rows (after E3 broadening) but `_calculate_pnl()` would return `None`, silently zeroing out PnL tracking. This is exactly the kind of hidden data integrity gap my original concern targeted.

Deferrals are properly scoped:
- **oinkdb-api → A4-F1:** Read-only reporting. No data loss — signals still close correctly, PnL still calculated. Impact is UI underreporting only. ~12 SQL sites warrant their own review. ✅
- **signal-gateway → A4-F2:** Dedup queries. A7 explicitly addresses `_match_active()` broadening. The interim risk (new signal for same ticker not deduped against PARTIALLY_CLOSED) already exists today (dedup doesn't check remaining_pct). A4 does not make this worse. ✅

No hidden assumptions remain — every deferred site has a named follow-up with impact assessment.

### Concern #2: DQ-A4-2 all-TPs-hit limbo → ✅ RESOLVED

§2C is completely rewritten. When `remaining_pct = 0.0` after all TPs hit in one cycle: call `calculate_blended_pnl()` inside `_process_tp_hits()`, set `status='CLOSED_WIN'`, `final_roi`, and `closed_at` in the same UPDATE. No open limbo state. Unambiguous.

The new `calculate_blended_pnl()` callsite inside `_process_tp_hits()` is sound — the function already exists and is tested (A2). The `tp_close_pcts` dict is available from the current loop. `remaining_pct=0.0` means all allocation is consumed, so `final_roi` is fully determined at that point.

### Concern #3: Backfill procedure → ✅ RESOLVED

§2E now specifies:
- Pre-SELECT with full output pasted into PR description
- Explicit `BEGIN`/`COMMIT` transaction
- Abort threshold: rowcount > 4
- Anomaly check: `tp3_hit_at IS NOT NULL AND remaining_pct > 0` (signal #1602)
- #1602 documented as pre-existing data quality issue, not an A4 blocker

This is a properly guarded deployment step.

### Concern #4: Query plan regression → ✅ RESOLVED

§2G acknowledges the `ix_signal_exchange_active` partial index regression. At ~490 rows the fallback to `ix_signals_status` is negligible. Future optimization path noted for >10K rows. Acceptable.

---

## Data Safety

**Risk: LOW.** No schema migration. Additive status value. `calculate_blended_pnl()` reads `remaining_pct`, not status — zero PnL formula impact. FET #1159 is CLOSED_WIN, never enters partial-close state. E5 fix ensures PnL tracking continuity for PARTIALLY_CLOSED signals.

## Migration Risk

**Risk: NONE.** No DDL. Backfill is transaction-guarded with abort conditions. Rollback is `UPDATE + git revert`.

## Regression Risk

**Risk: LOW.** 10 sites across 2 files with MUST-priority integration tests for each. Sites correctly excluded are documented (limit fills, PENDING branch). Deferrals have named follow-ups. The test plan covers every modification site.

---

## Advisory Notes (Non-Blocking)

1. **Signal #1602 anomaly:** `tp3_hit_at` set while `remaining_pct=50.0` is a pre-existing data quality issue worth tracking separately. Consider adding to the daily monitoring spot-check rotation for Thursday (lifecycle consistency).

2. **Same-cycle closure testing:** The `test_gap_past_all_tps_same_cycle_close` test should verify that `final_roi` equals the expected blended PnL (not just that status=CLOSED_WIN). This ensures the new `calculate_blended_pnl()` callsite inside `_process_tp_hits()` produces correct values.

3. **Phase 1 auto-escalation:** Since this auto-escalates to 🔴 CRITICAL, the Phase 1 pass threshold is ≥9.5 from both GUARDIAN and VIGIL.

---

*🛡️ GUARDIAN — Phase 0 Proposal Re-Review (Revision 1)*
*Reviewed: 2026-04-19T10:05Z*
