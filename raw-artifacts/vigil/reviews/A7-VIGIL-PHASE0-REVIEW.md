# VIGIL Proposal Review — Task A7

**Verdict:** APPROVE

**Spec Alignment:** The proposed approach matches Phase 4 Phase A (DOC3 EC-B1, risk score 60) — a fuzzy UPDATE→NEW guard at Financial Hotpath #6 (micro-gate INSERT logic). The 5% entry tolerance is well-justified against existing micro-gate thresholds (MARKET=10%, LIMIT=30%) and the three complementary protection layers are correctly identified (board B10, signal_router exact dedup, micro-gate §4b exact dedup). A7 fills the documented gap: same trader/ticker/direction but slightly different entry price. The `ticker_only` inclusion follows code precedent (`_process_closure` at line 1063 refuses on `ticker_only` for irreversible actions).

**Acceptance Criteria Coverage:** 6 acceptance criteria (§6 of FORGE plan) are fully addressed by the 15-test strategy in §9. All MUST-priority scenarios covered: suppress same/close entry, allow different entry, allow no-existing, allow opposite direction, rejection logged. SHOULD-priority tests cover PARTIALLY_CLOSED match, event logging, trader_id bypass, boundary conditions at exactly 5%/5.01%, and ticker_only/ambiguous match confidence levels. Test strategy is thorough and exceeds the minimum required count.

**Concerns:** None that block approval.

**Suggestions:**

1. **Division-by-zero guard completeness:** §2B mentions `existing_entry == 0` or `entry_price == 0` → skip percentage check. The §4a pseudocode only guards `if existing_entry > 0 and entry_price > 0`. Verify during implementation that the "else" branch (one or both prices zero) falls through to allow INSERT, not suppress — a zero-entry signal is data quality noise, not a phantom trade.

2. **Test #11 boundary semantics:** The proposal says 5% is "inclusive" (≤5% suppress, >5% allow). Confirm the implementation uses `<=` not `<` in the threshold comparison. The §4a pseudocode uses `price_diff_pct > _A7_ENTRY_TOLERANCE_PCT` for the allow branch, which correctly makes ≤5% the suppress path.

3. **A4 status IN ordering:** The proposal correctly identifies 4 clauses to broaden (3 in `_match_active` + 1 in §4b). Since A4 has already shipped in oink-sync but not yet in micro-gate, ANVIL should apply the PARTIALLY_CLOSED extension as part of A7 (not defer it). The proposal's §2E already states this — just confirming it should be in the same commit, not a follow-up.

*VIGIL 🔍 — Phase 0 Review for A7*
*2026-04-19*
