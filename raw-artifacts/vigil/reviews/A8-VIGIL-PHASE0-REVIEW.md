# VIGIL Proposal Review — A8: Conditional SL Type Field

**Verdict:** APPROVE

**Tier:** 🟡 STANDARD
**Review Date:** 2026-04-19

---

**Spec Alignment:** The approach matches Phase 4 §3 (Signal Metadata Enrichment) and Phase 5 §BS-6 (Stop-Loss Semantics Tracking). The 4-value taxonomy (FIXED/CONDITIONAL/MANUAL/NONE) covers the complete SL provenance space identified in the spec. The shared `_CONDITIONAL_SL_KEYWORDS` constant (FORGE §4d) correctly eliminates the keyword-list duplication risk — both the existing notes-tag block (line 743) and the new sl_type block will reference the same tuple. Schema is additive (`ADD COLUMN ... DEFAULT 'FIXED'`), non-destructive, and backward-compatible.

**Acceptance Criteria Coverage:** 8 tests (6 MUST, 2 SHOULD) mapped to all 6 acceptance criteria:
1. FIXED classification → `test_fixed_sl_type_on_numeric_sl` ✅
2. NONE classification → `test_none_sl_type_on_missing_sl` ✅
3. CONDITIONAL (no numeric) → `test_conditional_sl_type_on_keyword_note` ✅
4. CONDITIONAL (with extracted numeric) → `test_conditional_sl_type_with_extracted_numeric` ✅
5. MANUAL via UPDATE → `test_manual_sl_type_on_update` ✅
6. No NULLs invariant → `test_sl_type_null_never_occurs` ✅
7. UPDATE without SL preserves sl_type → regression SHOULD ✅
8. Backfill correctness → SHOULD ✅

Test strategy covers all four code paths plus the UPDATE path plus the null-invariant. Adequate for STANDARD.

**Concerns:** None blocking.

**Financial Hotpath Assessment:** The proposal modifies `_process_update()` to add `sl_type = 'MANUAL'` alongside stop_loss changes and adds `"sl_type"` to `_ALLOWED_UPDATE_COLS`. This is **classification metadata tagging** — the actual SL modification logic (`update_sl()` in lifecycle.py, Financial Hotpath #4) is not touched. The micro-gate `_process_update()` handles inbound UPDATE-type Discord messages; it is not the same function as `update_sl()`. No Financial Hotpath escalation required.

**Suggestions:**
1. OinkV MINOR-A8-3 correctly identifies that the FORGE plan's "after line 799" insertion anchor is imprecise — the proposal's stated placement "after Section 8c (A15 guard) / before Section 9 (TP safety check)" is the right interpretation. During Phase 1, ensure sl_type reads the **final** `stop_loss` and `sl_note` values after all SL processing (numeric extraction, A15 NULL-clearing) is complete.
2. The FORGE plan was written against `69d6840a` (pre-A11, 28 columns). Proposal correctly states INSERT goes 29→30 columns (post-A11 baseline with `leverage_source`). Confirm column count and placeholder count match during implementation.
3. The `test_lifecycle_events.py` schema update is marked correctly as optional (OinkV MINOR-A8-4). Include it for forward-compatibility but don't block on it.
