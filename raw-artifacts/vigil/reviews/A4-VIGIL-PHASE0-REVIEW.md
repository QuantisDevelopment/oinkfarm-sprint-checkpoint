# VIGIL Proposal Review — A4: PARTIALLY_CLOSED Status for Partial TP Signals

**Verdict:** ✅ **APPROVE**

**Task:** A4 — PARTIALLY_CLOSED Status for Partial TP Signals
**Proposal:** `/home/oinkv/anvil-workspace/proposals/A4-PROPOSAL.md`
**FORGE plan:** `/home/oinkv/forge-workspace/plans/TASK-A4-plan.md`
**OinkV audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A4.md`
**Mike approval marker:** `/home/oinkv/anvil-workspace/proposals/A4-PHASE0-APPROVED.marker`
**Reviewer:** VIGIL 🔍
**Review date:** 2026-04-19 11:48 CEST
**Dependencies verified:** A1 ✅ shipped, A2 ✅ shipped, A3 ✅ shipped

---

## Spec Alignment

**Assessment: ALIGNED** ✅

The proposal correctly implements the Phase 4 §2 (Signal Lifecycle Accuracy) and §ADAPT/status-model prescription for a `PARTIALLY_CLOSED` intermediate status. Specific alignment points:

1. **Status transition rules (§2A):** The four-row transition table maps cleanly to Phase 4's lifecycle model. `ACTIVE → PARTIALLY_CLOSED` on first TP hit when `0 < remaining_pct < 100`, with direct `CLOSED_WIN` for gap-past-all-TPs (DQ-A4-2), is correct.

2. **No schema migration required:** ANVIL correctly identifies that `VARCHAR(20) CHECK (status = UPPER(status))` accepts `'PARTIALLY_CLOSED'` (15 chars, all-uppercase). This is additive — no DDL, no migration script, no backward compatibility risk. Verified against actual schema.

3. **5 modification sites (§2B):** ANVIL's audit found **5 sites** needing broadening, not the 3 FORGE originally identified. I verified all 5 against `lifecycle.py` at commit `6b21a20`:

   | # | Function | Line | Current predicate | Verified |
   |---|----------|------|-------------------|----------|
   | 1 | `_check_sl_tp()` — main SELECT | 389 | `WHERE status='ACTIVE' AND exchange_matched=1` | ✅ Must broaden |
   | 2 | `_check_sl_tp()` — closure UPDATE | 473 | `AND status='ACTIVE' AND fill_status='FILLED'` | ✅ Must broaden |
   | 3 | `_process_tp_hits()` — UPDATE | 606–616 | No status reference; needs `status='PARTIALLY_CLOSED'` added | ✅ Must add |
   | 4 | `_check_sl_proximity()` — SELECT | 811 | `WHERE status='ACTIVE' AND fill_status='FILLED'` | ✅ Must broaden |
   | 5 | `_write_price_history()` — SELECT | 988 | `WHERE status='ACTIVE' AND exchange_matched=1` | ✅ Must broaden |

   **Sites correctly excluded:**
   - `_check_limit_fills()` line 689: Sets `status='ACTIVE'` FROM `'PENDING'` — this is the PENDING→ACTIVE fill transition, unrelated to partial closes. ✅ Correct exclusion.

   ANVIL's identification of sites #4 and #5 is **genuinely needed** and a valuable catch beyond FORGE's plan. `PARTIALLY_CLOSED` signals absolutely need continued SL-proximity alerting (site #4) and price history writes (site #5) — without these, partially-closed signals would silently lose monitoring coverage. This would be a HIGH-impact gap.

4. **DQ-A4-2 (gap-past-all-TPs):** The proposal correctly implements FORGE's recommendation to skip `PARTIALLY_CLOSED` limbo when `remaining_pct = 0.0`. The signal remains `ACTIVE` until the next cycle's SL check closes it as `CLOSED_WIN` — this is pre-existing behavior and is acceptable.

5. **A7 cross-reference:** The proposal correctly notes that `micro-gate-v3.py::_match_active()` will need `PARTIALLY_CLOSED` in its status set, deferred to A7. This is forward-compatible.

---

## Acceptance Criteria Coverage

**Assessment: WELL COVERED** ✅

The proposal lists **8 acceptance criteria** (§5), not 7 as stated in the review request — the 8th is a status-value validation query. All 8 are covered by the 13-test strategy (§3):

| AC # | Criterion | Test(s) Covering It | Adequate? |
|------|-----------|-------------------|-----------|
| 1 | TP hit → `PARTIALLY_CLOSED` when `0 < remaining_pct < 100` | `test_tp1_hit_sets_partially_closed`, `test_tp2_hit_on_partially_closed_signal` | ✅ |
| 2 | `PARTIALLY_CLOSED` included in `_check_sl_tp()`, `_check_sl_proximity()`, `_write_price_history()` | `test_partially_closed_monitored_in_next_cycle`, `test_sl_proximity_includes_partially_closed`, `test_price_history_includes_partially_closed` | ✅ |
| 3 | SL closure works on `PARTIALLY_CLOSED` with correct `final_roi` | `test_sl_hit_closes_partially_closed_signal` | ✅ |
| 4 | `STATUS_CHANGED` event on `ACTIVE → PARTIALLY_CLOSED` | `test_status_changed_event_emitted` | ✅ |
| 5 | No duplicate `STATUS_CHANGED` on subsequent TP hits | `test_no_duplicate_status_event_on_second_tp` | ✅ |
| 6 | `_check_limit_fills()` excludes `PARTIALLY_CLOSED` | `test_limit_fills_ignores_partially_closed` | ✅ |
| 7 | All existing tests pass unmodified | Regression gate (29 + 8 + 8 existing tests) | ✅ |
| 8 | Status value validation query | Implicitly covered by all status-setting tests | ✅ |

**Test for DQ-A4-2 (gap-past-all-TPs):** `test_gap_past_all_tps_closes_directly` covers this. ✅

---

## Concerns

### ⚠️ Phase 1 Tier Escalation Required — CRITICAL, Not STANDARD

The proposal is filed as 🟡 STANDARD, but this **must auto-escalate to 🔴 CRITICAL** for Phase 1 code review. Per SOUL.md §1 Financial Hotpath Registry:

- **Hotpath #2** (`_check_sl_tp()`) — directly modified (sites #1 and #2)
- **Hotpath #5** (`lifecycle.py` SL/TP write paths) — the closure UPDATE at line 473 is an SL/TP write path

Both are in the 7-function Financial Hotpath Registry. **Any PR touching these paths triggers automatic CRITICAL designation — full 5-dimension scoring, 4-hour SLA, ≥9.5 threshold. No exceptions.**

This does NOT block Phase 0 approval — the proposal itself is sound. But ANVIL must be aware that Phase 1 review will be scored at CRITICAL tier (≥9.5), not STANDARD (≥9.0).

### Minor: STATUS_CHANGED Dedup Implementation Clarity

§2D describes two dedup approaches:
1. A separate UPDATE with `AND status='ACTIVE'` guard + rowcount check
2. A pre-read from the already-fetched row data

The proposal settles on approach #2 (pre-read), which is correct for the merged single-UPDATE design in §2C. However, the text mentions approach #1 before pivoting to #2, which could cause implementation confusion. **For Phase 1: ANVIL should use the pre-read approach consistently** — the row data passed into `_process_tp_hits()` already contains the current status, and the single-threaded SQLite execution model guarantees no race between SELECT and UPDATE within a cycle.

### Minor: Backfill Gate — Correctly Pre-Approved

The proposal (§2E) acknowledges Mike's pre-approval for ~2 rows (signals #1561, #1602) and raises the threshold to pause at >4 rows. This is correct per the approval marker's MUST-FIX #1. ✅

### Minor: `test_gap_past_all_tps_closes_directly` Timing Semantics

The test name suggests same-cycle closure, but the actual behavior is: all TPs hit → `remaining_pct = 0.0` → status stays `ACTIVE` → SL closure fires on *next cycle*. This is a naming nit — the test assertions will be correct if they verify the post-TP-processing state (status still ACTIVE, remaining_pct=0.0, no PARTIALLY_CLOSED limbo) rather than final closure in the same call. ANVIL should clarify whether the test covers one cycle or two — if one cycle, it tests the "no PARTIALLY_CLOSED limbo" property; if two cycles, it tests end-to-end closure. Either is valid, but the scope should be explicit.

---

## Suggestions

1. **Add `STATUS_CHANGED` to `LIFECYCLE_EVENTS` set** in `event_store.py` as documented hygiene. The set is informational-only (no runtime validation), but every other emitted event type is in the set — maintaining pattern consistency matters for future developers. (Already noted in proposal §2D as SHOULD-FIX — endorsed.)

2. **Consider an explicit safety guard on the backfill SQL** for deployment: `AND id IN (1561, 1602)` as an additional predicate. This is belt-and-suspenders given the pre-deploy SELECT + >4 row threshold is already there, but explicit ID pinning eliminates any surprise from signals created between now and deployment.

3. **For Phase 1 implementation:** When writing the pre-read dedup, pass the current `status` value from the row dict through to `_process_tp_hits()`. The function signature already accepts `remaining_pct` as a kwarg (A2 addition) — adding `current_status` as another kwarg keeps the pattern clean. This is an implementation suggestion, not a spec requirement.

---

## Phase 1 Notes for VIGIL

When reviewing the Phase 1 code submission on branch `anvil/A4-partially-closed-status`:

- **Tier:** 🔴 CRITICAL (auto-escalated per Financial Hotpath Registry — touches Hotpath #2 and #5)
- **Threshold:** ≥9.5 overall from both VIGIL and GUARDIAN
- **SLA:** 4 hours from branch submission
- **Key verification points:**
  - All 5 modification sites broadened (not just 3)
  - Single-UPDATE atomicity in `_process_tp_hits()` (§2C)
  - STATUS_CHANGED dedup via pre-read, not rowcount (§2D)
  - `test_gap_past_all_tps_closes_directly` scope clarity
  - All 29 + 8 + 8 existing tests pass unmodified
  - Backfill SQL matches pre-deploy check expectations

---

**Verdict: ✅ APPROVE**

The proposal demonstrates thorough spec alignment with Phase 4 §2 and §ADAPT/status-model. ANVIL's identification of 5 modification sites (vs. FORGE's 3) is correct and critical — sites #4 (`_check_sl_proximity`) and #5 (`_write_price_history`) would cause HIGH-impact monitoring gaps if missed. The test strategy covers all 8 acceptance criteria including the DQ-A4-2 gap-past-all-TPs edge case. The atomic single-UPDATE approach is sound, and the STATUS_CHANGED dedup logic is implementable via pre-read. The backfill is Mike-pre-approved for ~2 rows.

**One mandatory note for Phase 1:** This proposal auto-escalates to 🔴 CRITICAL tier for code review due to Financial Hotpath #2 (`_check_sl_tp()`) and #5 (lifecycle.py SL/TP write paths). ANVIL should plan for the ≥9.5 threshold and 4-hour SLA accordingly.

Proceed to Phase 1 implementation.

---

*VIGIL 🔍 — Phase 0 Review*
*2026-04-19 11:48 CEST*
