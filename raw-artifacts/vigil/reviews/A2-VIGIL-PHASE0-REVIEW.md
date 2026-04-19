# VIGIL Proposal Review — Task A2

## remaining_pct Model + Partial-Close PnL Accuracy

**Verdict:** APPROVE

---

## Spec Alignment

The proposed approach aligns with Phase 4 §1 ("remaining_pct implementation specification") on all 5 spec points:

1. ✅ **Capture close_pct on TP_HIT** — Proposal implements this via `_process_tp_hits()` with close_pct in the TP_HIT event payload. A2 uses default table values (Source 2); provider text extraction (Source 1) is explicitly deferred. This is a valid scoping decision: Phase 4 step 1 says "capture close_pct from alert text" but the spec's own step 5 says "Fallback: when close_pct is not extractable, use existing fixed allocation with `alloc_source: 'assumed'` flag." A2 builds the infrastructure and uses the fallback path. Source 1 extraction plugs in later without touching `calculate_blended_pnl()`.

2. ✅ **Update remaining_pct on signal** — `remaining_pct = remaining_pct - close_pct` with clamping to 0.0. Correct.

3. ✅ **TP_HIT event payload** — Spec requires `{"tp_level": 1, "close_pct": 25, "remaining_pct": 75, "alloc_source": "extracted|assumed"}`. Proposal includes all four fields. Matches exactly.

4. ✅ **calculate_blended_pnl() rewrite** — New params `remaining_pct` and `tp_close_pcts` with backward-compatible fallback when both are None. This preserves zero-regression for existing signals.

5. ✅ **Fallback with alloc_source flag** — All A2 allocations will be `alloc_source: "assumed"`. Correct for the scoped implementation.

**Spec verification claim:** Phase 4 says "FET #1159 scenario: stored 3.37% ROI vs actual 1.68%. After remaining_pct fix, ROI must match actual." The proposal's test strategy tests `remaining_pct=75.0 → 1.68%`, which proves the math is correct *when the data is available*. With A2's default table (50/50 for 2-TP signals), FET #1159 will still get 3.37% — this is expected and correct because the default allocation happens to be 50%. The accuracy improvement for FET #1159 specifically depends on the follow-up extraction task providing the actual 25% close percentage. The proposal is transparent about this.

---

## Acceptance Criteria Coverage

All 8 acceptance criteria (AC1–AC8) have corresponding test descriptions in §6:

| AC | Test Coverage | Assessment |
|----|--------------|------------|
| AC1 | Schema check | ✅ Straightforward PRAGMA verification |
| AC2 | SELECT after simulated TP hit | ✅ Covered in §6B multi-TP scenarios |
| AC3 | Event payload check | ✅ Covered in §6E integration tests |
| AC4 | FET #1159 with remaining_pct=None → 3.37% | ✅ Explicit in §6A |
| AC5 | FET #1159 with remaining_pct=75 → 1.68% | ✅ Explicit in §6A |
| AC6 | remaining_pct never below 0.0 | ✅ Covered in §6C edge cases |
| AC7 | alloc_source = "assumed" for all A2 | ✅ Covered in §6E |
| AC8 | No regression in existing tests | ✅ Full suite pass requirement |

**One gap noted:** AC4/AC5 test the function directly with explicit remaining_pct values. There should also be an **integration test** that runs the full lifecycle (TP hit → remaining_pct update → SL closure → blended PnL computation) and verifies the end-to-end ROI. §6B describes multi-TP scenarios but doesn't explicitly mention verifying the final PnL through the full lifecycle path. Recommend adding one integration test that traces from TP hit through to `final_roi` on the closed signal row.

---

## Concerns

1. **Default close_pct table discrepancy (§5):** The proposal's default table for 3 TPs uses **50/25/25**, matching current behavior. However, the proposal notes that Phase 4's example uses 25%, suggesting equal-split (33/33/34) may be intended. The proposal recommends keeping 50/25/25 as default and adding a config option for alternative splits. **This is the correct decision for A2** — changing the default would alter PnL for future signals before extraction is available, creating unnecessary churn. The config option provides a clean path to change later if Mike/Dominik decide. No action needed from ANVIL on this point.

2. **Transaction scope for remaining_pct UPDATE (§11):** The proposal states remaining_pct UPDATE is "in the same transaction as tp_hit_at UPDATE" and is NOT wrapped in the event try/except. Good — this is the correct lesson from A1's zero-event root cause. The remaining_pct mutation is part of the signal state change, not an audit log entry. If it fails, the TP hit should also fail. Verify this is implemented correctly in Phase 1.

3. **No backfill for ACTIVE signals:** The proposal defers backfilling `remaining_pct=100.0` on existing ACTIVE signals. Since the column has `DEFAULT 100.0`, new inserts will have 100.0, but existing ACTIVE rows will have NULL. The `_process_tp_hits()` code reads "current remaining_pct from the signal row (or 100.0 if NULL)" — this NULL coalescing is essential. Verify the COALESCE/fallback is implemented in Phase 1.

---

## Suggestions

1. **Add an end-to-end lifecycle integration test** that runs: insert signal → TP1 hit (remaining_pct drops) → SL closure → verify `final_roi` on the signals row matches the expected blended PnL. This closes the gap between unit-testing `calculate_blended_pnl()` in isolation and verifying the full pipeline produces correct results.

2. **Consider testing the boundary where remaining_pct reaches exactly 0.0** after the last TP hit. When all TPs are hit and position is fully closed, the signal should not be closeable again by SL hit (remaining_pct = 0 means nothing left to close). Verify the lifecycle handles this correctly — does it skip the SL check, or does it produce a 0-size closure?

3. **Document the expected behavior for tp_close_pcts parameter** — the proposal mentions a dict like `{1: 25.0, 2: 25.0}` but doesn't specify what happens when tp_close_pcts has entries for TPs that weren't hit. Defensive handling (ignore unhit TP entries) should be explicit in the test strategy.

---

*Reviewed against: Phase 4 §1 (remaining_pct implementation specification), Phase 4 critical path steps 3–5, Phase A gate criteria.*
