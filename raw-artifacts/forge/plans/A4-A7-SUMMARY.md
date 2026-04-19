# A4/A5/A7 Plan Summary — Wave 2

**Author:** FORGE 🔥  
**Date:** 2026-04-19  
**Status:** Ready for Mike approval  
**Base commit:** signal-gateway 38eb8e8, oink-sync 6b21a20

---

## Recommended Execution Order

| Order | Task | Name | Tier | Rationale |
|-------|------|------|------|-----------|
| 1 | **A4** | PARTIALLY_CLOSED status | 🟡 STANDARD | Enables A7's status check to include partial closes. Small, focused change in lifecycle.py. |
| 2 | **A7** | UPDATE→NEW detection | 🔴 CRITICAL | Phantom trades are the most damaging data quality issue. Depends on A4 for complete status coverage. |
| 3 | **A5** | Confidence scoring per parser | 🟡 STANDARD | Improves metadata quality but doesn't affect data integrity. Independent of A4/A7. |

### Why A4 → A7 → A5 (not the original A4/A5/A7)

A7 needs to check for existing ACTIVE, PENDING, **and PARTIALLY_CLOSED** signals. If A7 ships before A4, partially-closed signals would be invisible to the phantom-trade guard — a gap that could let duplicates through. A4 is a small change (lifecycle.py only) that should ship first.

A5 is fully independent and can ship at any point. Placed last because it has the lowest data-integrity impact.

---

## Plan Files

| File | Lines | Size | Key Changes |
|------|-------|------|-------------|
| [TASK-A4-plan.md](TASK-A4-plan.md) | 368 | 17KB | Add PARTIALLY_CLOSED status to oink-sync lifecycle.py when 0 < remaining_pct < 100 |
| [TASK-A7-plan.md](TASK-A7-plan.md) | ~280 | 16KB | Pre-INSERT check in micro-gate for existing active position (5% entry threshold) |
| [TASK-A5-plan.md](TASK-A5-plan.md) | 265 | 14KB | Map extraction_method to confidence score in micro-gate |

---

## Cross-Task Dependencies

```
A1 (signal_events) ──────────────────► A4 (PARTIALLY_CLOSED) ──► A7 (UPDATE→NEW)
                    └──► A2 (remaining_pct) ──► A4
                                                                  A5 (confidence) — independent
```

A4 depends on both A1 (event_store for STATUS_CHANGED events) and A2 (remaining_pct tracking). Both shipped.
A7 depends on A4 (to include PARTIALLY_CLOSED in status check).
A5 has no dependencies beyond A1 (shipped).

---

## Scope Summary

### A4: PARTIALLY_CLOSED Status
- **Repo:** oink-sync
- **Files:** lifecycle.py (3 locations), tests/test_partially_closed.py (new)
- **Schema:** No migration — PARTIALLY_CLOSED passes the existing CHECK (status = UPPER(status)) constraint
- **Risk:** LOW — additive status value, existing data unchanged
- **Key insight:** The _check_sl_tp main query (line 388) must include PARTIALLY_CLOSED in its WHERE clause, otherwise partially-closed signals stop getting price updates and SL checks

### A7: UPDATE→NEW Detection  
- **Repo:** signal-gateway (micro-gate-v3.py)
- **Files:** micro-gate-v3.py (1 new block), tests/test_a7_update_detection.py (new)
- **Schema:** No migration
- **Risk:** MEDIUM — false positives could suppress legitimate signals. 5% entry threshold + 48h monitoring mitigates
- **Key insight:** Reuses existing `_match_active()` function. The guard goes between step 14 (trader_id resolved) and step 16 (INSERT). Same pattern as B14 SL guard.
- **Open question Q-A7-1:** Include `ticker_only` matches in suppression set? Recommended yes, with 48h monitoring.

### A5: Confidence Scoring
- **Repo:** signal-gateway (micro-gate-v3.py)  
- **Files:** micro-gate-v3.py (confidence logic), tests/test_a5_confidence.py (new)
- **Schema:** No migration — confidence column already exists (FLOAT NOT NULL DEFAULT 0.8)
- **Risk:** LOW — metadata improvement, doesn't affect pipeline flow
- **Key insight:** Extraction method is already in the notes field (`[extracted: llm_nl]`). A5 just maps it to a confidence score instead of hardcoding 0.8.

---

## A2 Follow-Up Tracking

**Provider-alert close_pct extraction** was flagged in A2 as a future improvement. Currently, A2 uses `alloc_source: "assumed"` with default close fractions from a fixed table. The actual percentages from WG alert text (e.g., "TP1 (25%)") are not yet extracted.

**Status:** Deferred. The reconciler's `_PARTIAL_TP_RE` regex (reconciler.py:28) detects partial TP patterns but doesn't capture the percentage number. Enhancement would require:
1. Named capture group in `_PARTIAL_TP_RE` for the percentage
2. `_state_from_alert()` to include `close_pct` in the detail dict
3. Propagation through the reconciler → micro-gate UPDATE path → event_store

**Recommendation:** Track as A12 (or next available task number). Not blocking A4/A5/A7. Ship after the current wave.

---

## Estimated Effort (for Mike's planning only)

These are FORGE's estimates based on codebase complexity, not requirements:

| Task | Estimated Effort | Confidence |
|------|-----------------|------------|
| A4 | 0.5 days | High — focused change in one function |
| A7 | 1 day | Medium — requires careful threshold tuning and monitoring |
| A5 | 0.5 days | High — simple mapping table |
| **Total** | **2 days** | |

---

*Forge 🔥 — "A4 sets the stage. A7 closes the gap. A5 adds the metadata. Ship in that order."*
