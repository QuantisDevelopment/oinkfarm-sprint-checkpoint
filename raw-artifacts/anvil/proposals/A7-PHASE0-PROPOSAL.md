# A7 Phase 0 Technical Proposal — UPDATE→NEW Detection (Phantom Trade Prevention)

**Author:** ANVIL (⚒️)
**Task:** A7 — UPDATE→NEW Detection
**Tier:** 🔴 CRITICAL (Financial Hotpath #6 — micro-gate INSERT logic)
**Threshold:** ≥9.5 from VIGIL and GUARDIAN
**Date:** 2026-04-19
**Revision:** 0 (initial)
**Phase 4 Ref:** Phase A element; DOC3 EC-B1 (risk score 60)
**Dependencies:** A1 ✅ (event_store shipped), A4 ✅ (PARTIALLY_CLOSED merged in oink-sync)
**Repo:** bandtincorporated8/oinkfarm
**Canonical file:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, HEAD `498d8b28`)
**Reference:** FORGE plan v1.1 (`/home/oinkv/forge-workspace/plans/TASK-A7-plan.md`), OinkV audit (`/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A7.md`)

---

## §1 Problem Statement

When an LLM extraction classifies a trader UPDATE message (e.g., "SL moved to 0.48") as a NEW signal, the current INSERT path in `_process_signal()` creates a **phantom duplicate** — a second signal for the same trader/ticker/direction alongside the real one. This is the single most damaging extraction failure mode: it inflates signal counts, corrupts win rates, and creates irreconcilable PnL discrepancies. **15 phantom trades** were traced to this pattern in Q1.

### Existing Protection Layers (3 of 4 already deployed)

| # | Layer | Location | Mechanism | Gap |
|---|-------|----------|-----------|-----|
| 1 | Board reconciler B10 | signal-gateway `reconciler.py:141-146` | Flip-flop suppression + entry-correction detection | Board path only |
| 2 | signal_router cross-channel dedup | signal-gateway `signal_router.py:3589+` | Exact (trader, ticker, direction, entry_price) match | Exact entry_price only |
| 3 | micro-gate §4b CROSS_CHANNEL_DUPLICATE | canonical micro-gate lines 656-680 | Exact (trader_id, ticker, direction, entry_price) match | Exact entry_price only |
| 4 | **A7 (new)** | canonical micro-gate, between step 14 and step 16 | **Fuzzy (trader, ticker, direction) + 5% entry tolerance** | — |

**A7 is the fourth layer** — a fuzzier guard that catches the residual set: same trader/ticker/direction but entry price within 5% (UPDATE misclassified as NEW). The three existing layers all require exact entry_price match, missing cases where the LLM extracts a slightly different entry.

---

## §2 Proposed Approach

### §2A Core Mechanism

Insert an UPDATE→NEW guard in `_process_signal()` between **step 14** (trader FK resolution, line 832) and **step 16** (INSERT, line 855). The guard:

1. Calls existing `_match_active(conn, trader_name_raw, ticker, direction, server_id)` to search for ACTIVE/PENDING/PARTIALLY_CLOSED signals with matching (trader, ticker, direction)
2. If a match is found with confidence `"exact"` or `"ticker_only"`:
   - Compares entry prices. If diff ≤ 5% → **suppress INSERT** as `A7_UPDATE_DETECTED`
   - If diff > 5% → **allow INSERT** as genuine new position (annotate in notes)
3. If no match or confidence is `"ambiguous"` or `"no_match"` → proceed to INSERT normally

**Placement rationale:** After step 14 because `trader_id`, `trader_name_raw`, `ticker`, `direction`, and `entry_price` are all resolved. Before step 16 (INSERT) because we need to intercept before the phantom row is created.

### §2B The 5% Entry Tolerance

```python
_A7_ENTRY_TOLERANCE_PCT = 5.0
```

**Rationale:** Existing micro-gate thresholds — MARKET orders allow 10% deviation, LIMIT orders allow 30%. 5% is conservative enough to catch most misclassifications (LLM re-extracts market price or slightly different entry) while permitting genuine averaging-in positions at materially different levels.

**Edge cases handled:**
- **Same ticker, opposite direction:** Already handled — `_match_active` matches on direction, so LONG and SHORT are independent positions.
- **`existing_entry == 0` or `entry_price == 0`:** Skip the percentage check (division by zero), proceed to INSERT.
- **`trader_id is None`:** Skip A7 entirely — cannot meaningfully match without trader attribution.

### §2C `ticker_only` Match Confidence — INCLUDE in Suppression Set

**Decision:** Include `ticker_only` confidence in the suppression set (alongside `exact`).

**Code precedent:** `_process_closure` (canonical line 1063) **REFUSES** closure on `ticker_only` match with `LOW_CONFIDENCE_CLOSURE`. The established pattern for destructive/irreversible actions on weak matches is to refuse. An INSERT is irreversible (phantom trade), so by analogy, suppress.

**Monitoring plan:** Track `A7_UPDATE_DETECTED` rejections for first 48h. If any show different real traders being blocked, tighten to `exact` only.

### §2D Event and Rejection Logging

**On suppression:**
1. `_log_rejection(entry, "A7_UPDATE_DETECTED", ..., conn=conn)` — writes to gate-rejections.jsonl AND quarantine table (via `conn=conn` kwarg, post-A1 signature)
2. `_log_event(conn, "UPDATE_DETECTED", existing["id"], {...})` — writes to signal_events via existing module-level helper (line 61, 13+ existing call sites, best-effort, `commit=True`)

**On allow (genuine new position):**
- Append A7 note to `notes` string: `[A7: existing #ID at PRICE, new entry PRICE differs by X% — allowing INSERT]`
- Note: append to `notes` string directly, not `notes_parts` (already joined at line 824)

### §2E `_match_active()` Status Broadening

All three `WHERE s.status IN ('ACTIVE', 'PENDING')` clauses in `_match_active()` (lines 384, 394, 410) must add `PARTIALLY_CLOSED`:

```sql
WHERE s.status IN ('ACTIVE', 'PENDING', 'PARTIALLY_CLOSED')
```

Additionally, the §4b `CROSS_CHANNEL_DUPLICATE` guard (line 669) has a fourth status IN clause that should also be broadened for consistency.

**Total: 4 status IN clauses updated** (3 in `_match_active` + 1 in §4b guard).

### §2F Return Value

On suppression, return a dict with `"action": "a7_update_detected"` — the caller (`_dispatch`, line 599) passes this through. No special handling needed upstream.

---

## §3 Files to Modify

| File | Function/Location | Change | Reason |
|------|-------------------|--------|--------|
| `scripts/micro-gate-v3.py` | `_process_signal()` between lines 832-855 | ADD A7 guard block (~25 lines) | Core UPDATE→NEW detection |
| `scripts/micro-gate-v3.py` | `_match_active()` lines 384, 394, 410 | ADD `'PARTIALLY_CLOSED'` to status IN | A4 dependency: detect active partial positions |
| `scripts/micro-gate-v3.py` | §4b guard line 669 | ADD `'PARTIALLY_CLOSED'` to status IN | Consistency with _match_active broadening |
| `scripts/event_store.py` | `LIFECYCLE_EVENTS` set (line 53) | ADD `"UPDATE_DETECTED"` | Registry hygiene |
| `scripts/event_store.py` | `QUARANTINE_CODES` set (line 80) | ADD `"A7_UPDATE_DETECTED"` | Quarantine registry |
| `tests/test_a7_update_detection.py` | New file | CREATE test suite | 12+ tests |

### Files NOT Modified
- `signal_router.py` (signal-gateway repo) — cross-channel dedup is a separate layer
- `reconciler.py` (signal-gateway repo) — board path already has B10 protection
- `lifecycle.py` / `engine.py` (oink-sync repo) — no changes needed

---

## §4 SQL Changes

**No schema migration.** No new tables, no new columns, no ALTER TABLE.

The only SQL changes are the 4 `WHERE status IN` clause broadenings in micro-gate queries (§2E above).

---

## §5 Data Impact Assessment

### Signals Created
**None.** A7 only **prevents** INSERTs; it never creates data.

### Signals Updated
**None.** A7 does not UPDATE any existing rows.

### Data Written
- `signal_events` table: One `UPDATE_DETECTED` event per suppression (via `_log_event`, best-effort)
- `quarantine` table: One quarantine entry per suppression (via `_log_rejection` with `conn=conn`)
- `gate-rejections.jsonl`: One line per suppression
- `signals.notes` column: A7 annotation on genuine-new-position INSERTs

### Dedup Semantics
A7 is purely defensive — it blocks INSERTs that would create phantom duplicates. The suppressed signal is never created, so there's no data to reconcile or migrate.

### Production Impact Estimate
Based on Q1 data: ~15 phantom trades per quarter (≈1/week). A7 would suppress these. False positive rate is bounded by the 5% threshold — a legitimate new position at a price <5% different from an existing active position is extremely rare.

---

## §6 Alternatives Considered

### Alternative 1: Fix at LLM extraction layer
**Rejected.** The LLM misclassification is inherent to the extraction pipeline — UPDATE messages are ambiguous by nature. Even a perfect LLM will occasionally misclassify. A gate-level guard is a defense-in-depth measure that catches residual errors regardless of extraction quality.

### Alternative 2: Exact entry price match only (no fuzzy tolerance)
**Rejected.** This is what the existing §4b guard already does. A7 exists specifically to catch the fuzzy case where entry prices differ slightly.

### Alternative 3: 1% tolerance (tighter threshold)
**Rejected.** Too aggressive — would miss cases where the LLM extracts a market price that's 2-3% away from the original entry. 5% is the sweet spot based on existing price deviation thresholds (MARKET=10%, LIMIT=30%).

### Alternative 4: 10% tolerance (wider threshold)
**Rejected.** Too wide — would block legitimate averaging-in positions. A trader entering BTCUSD LONG at $100k with an existing position at $95k (5.3% diff) should be allowed.

### Alternative 5: Suppress `ticker_only` matches only with `exact` confidence
**Deferred — not initial.** Starting with both `exact` and `ticker_only` per code precedent (§2C). Can tighten to `exact` only after 48h monitoring if false positives observed.

---

## §7 Blast Radius

### oinkfarm (micro-gate-v3.py) — PRIMARY
- `_process_signal()`: New guard between steps 14-16. Only fires when `_match_active` returns a match. No impact on signals with no active duplicate.
- `_match_active()`: Status IN broadened (A4 alignment). Used by UPDATE handler (line 916) and CLOSURE handler (line 1059) — both benefit from seeing PARTIALLY_CLOSED signals.
- §4b guard: Status IN broadened for consistency.

### oink-sync — NONE
No changes. oink-sync's `_match_active` equivalent doesn't exist (lifecycle.py operates on signal IDs directly).

### signal-gateway — NONE
No changes. signal_router.py and reconciler.py protection layers are complementary, not modified.

### oinkdb-api — NONE
No changes. OinkDB sends signals to micro-gate; A7 operates inside micro-gate's decision logic.

---

## §8 Rollback Plan

A7 is purely defensive (prevents INSERTs, never modifies data). Rollback is trivial:

1. `git revert <A7-commit>` — removes the guard block
2. No data migration needed (no schema changes, no data modifications)
3. `systemctl restart signal-gateway` (or equivalent service restart)
4. **Risk of rollback:** Phantom duplicates that A7 would have caught will resume entering the DB (pre-A7 behavior)
5. **Signals suppressed during A7's operation** were never inserted — they cannot be recovered automatically. If a legitimate signal was false-positive suppressed, it needs manual re-entry via OinkDB.

---

## §9 Test Strategy

### Unit Tests (test_a7_update_detection.py)

| # | Test Name | Scenario | Expected | Priority |
|---|-----------|----------|----------|----------|
| 1 | `test_suppress_same_entry` | NEW signal, existing ACTIVE with identical entry | Suppress: `a7_update_detected` | MUST |
| 2 | `test_suppress_close_entry` | NEW entry 0.3% different from existing | Suppress: within 5% threshold | MUST |
| 3 | `test_allow_different_entry` | NEW entry 7.7% different from existing | Allow INSERT, A7 note in notes | MUST |
| 4 | `test_allow_no_existing` | No active position for this trader/ticker | Allow INSERT normally | MUST |
| 5 | `test_allow_opposite_direction` | Existing ACTIVE LONG, new SHORT same ticker | Allow INSERT | MUST |
| 6 | `test_partially_closed_match` | Existing PARTIALLY_CLOSED, new same trader/ticker/dir | Suppress: PARTIALLY_CLOSED is active | SHOULD |
| 7 | `test_event_logged` | Suppressed signal | UPDATE_DETECTED in signal_events | SHOULD |
| 8 | `test_rejection_logged` | Suppressed signal | A7_UPDATE_DETECTED in gate-rejections.jsonl | MUST |
| 9 | `test_no_trader_bypass` | trader_id=None | Skip A7, proceed to INSERT | SHOULD |
| 10 | `test_pending_match` | Existing PENDING signal, new same trader/ticker/dir | Suppress: PENDING is active position | MUST |
| 11 | `test_threshold_boundary_at_5pct` | Entry exactly 5.0% different | Suppress: ≤5% (inclusive) | SHOULD |
| 12 | `test_threshold_boundary_above_5pct` | Entry 5.01% different | Allow INSERT | SHOULD |
| 13 | `test_ticker_only_match_suppresses` | No trader_id match, ticker_only fallback matches | Suppress per §2C | SHOULD |
| 14 | `test_ambiguous_match_allows` | Multiple active signals for same ticker | Allow INSERT (ambiguous = no clear match) | SHOULD |
| 15 | `test_allow_insert_notes_annotation` | Genuine new position allowed | Notes contain A7 explanation | SHOULD |

**Target: ≥12 tests** (all MUST + majority of SHOULD).

### Regression Coverage
- All existing micro-gate tests must pass unchanged
- Run existing `test_micro_gate_source_url.py` to verify INSERT path not broken

---

## §10 Implementation Sequence

1. Add `UPDATE_DETECTED` to `LIFECYCLE_EVENTS` and `A7_UPDATE_DETECTED` to `QUARANTINE_CODES` in `event_store.py`
2. Broaden `_match_active()` status IN (3 clauses: lines 384, 394, 410) + §4b guard (line 669)
3. Insert A7 guard block in `_process_signal()` between steps 14 and 16
4. Write test suite
5. Run full test suite, verify no regressions
6. Push, open PR, request VIGIL + GUARDIAN review

---

## §11 Evidence — Line Number Verification (canonical micro-gate, 1,407 LOC)

All line numbers verified against `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` at HEAD `498d8b28`:

| What | Line | Verified |
|------|------|----------|
| `_log_event()` module-level helper | 61 | ✅ |
| `_log_rejection()` signature with `conn=` | 297 | ✅ |
| `_match_active()` function def | 368 | ✅ |
| `_match_active` status IN clause #1 (exact-trader) | 384 | ✅ |
| `_match_active` status IN clause #2 (canonical-name) | 394 | ✅ |
| `_match_active` status IN clause #3 (ticker-only) | 410 | ✅ |
| §4b CROSS_CHANNEL_DUPLICATE guard status IN | 669 | ✅ |
| `notes_parts = []` init | 708 | ✅ |
| `notes = " ".join(notes_parts)` (step 12) | 824 | ✅ |
| Step 14: trader FK resolution | 832 | ✅ |
| Step 16: INSERT | 855 | ✅ |
| `_log_event` call count in file | 13+ | ✅ |

---

## §12 Open Decision

**Q-A7-1: `ticker_only` inclusion — resolved in §2C.**

This proposal recommends INCLUDE with 48h monitoring. Code precedent (`_process_closure` at line 1063 REFUSES on `ticker_only`) supports this as the default for irreversible actions.

**If Mike disagrees:** Change the guard condition from `match_conf in ("exact", "ticker_only")` to `match_conf == "exact"`.

---

*ANVIL (⚒️) — Phase 0 Proposal, Revision 0*
*Submitted for VIGIL + GUARDIAN Phase 0 review*
