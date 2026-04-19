# VIGIL Proposal Review — A5: Parser-Type Confidence Scoring

**Verdict:** ✅ **APPROVE**

**Task:** A5 — Parser-Type Confidence Scoring
**Proposal:** `/home/oinkv/anvil-workspace/proposals/A5-PHASE0-PROPOSAL.md`
**FORGE plan:** `/home/oinkv/forge-workspace/plans/TASK-A5-plan.md` (v1.1)
**OinkV audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A5.md`
**Reviewer:** VIGIL 🔍
**Review date:** 2026-04-19 13:29 CEST
**Tier:** 🟡 STANDARD

---

## Spec Alignment

**Assessment: ALIGNED** ✅

The proposal correctly implements Phase 4 §3 (Signal Metadata Quality) and Phase 3 §ADAPT/confidence-model. Specific alignment points:

1. **Core prescription fulfilled:** Replace the catch-all `0.8` default with parser-type-specific confidence scores. The proposal adds a module-level `PARSER_CONFIDENCE_MAP` dict to the canonical micro-gate, keyed on `extraction_method` — exactly as Phase 4 prescribes.

2. **7-key map verified against source code:** I confirmed all 7 `extraction_method` producers against current source:

   | Key | Producer location | Verified |
   |-----|------------------|----------|
   | `cornix_regex` | signal_router.py:3043 | ✅ |
   | `telegram_direct` | signal_router.py:2000 | ✅ |
   | `chroma_regex` | signal_router.py:3191 | ✅ |
   | `oinxtractor_agent` | signal_router.py:3297 | ✅ |
   | `llm_nl` | signal_router.py:3407 | ✅ |
   | `inline_fallback` | signal_router.py:3272 | ✅ |
   | `qwen_v3` | signal-extract-v3.py:492 | ✅ |

   The 3 phantom keys from FORGE v1.0 (`board_reconciler`, `oinkdb_opus`, `manual`) are correctly removed — none of these have a current producer in any `.py` file. This was the audit's CRITICAL C2 finding, and FORGE v1.1 + ANVIL's proposal have fully resolved it.

3. **Canonical file correctly identified:** The proposal targets `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC), not the stale signal-gateway copy (1,063 LOC). This resolves the audit's CRITICAL C1 finding.

4. **Confidence normalization block verified:** I confirmed the target code at canonical lines 797–801:
   ```python
   confidence = _safe_float(ext.get("confidence"), 0.8)
   if confidence > 1.0:
       confidence = round(confidence / 10.0, 2)
   confidence = max(0.0, min(1.0, confidence))
   ```
   The proposal's `ext.get("confidence") is None` check before this block (Option 1) correctly distinguishes "extractor didn't supply confidence" from "extractor explicitly supplied 0.8". This is the right approach — post-normalization detection is impossible since both cases produce 0.8.

5. **`extraction_method` read from `entry` (top-level), not `ext`:** Confirmed at canonical line 822: `method = entry.get("extraction_method", "unknown")`. The proposal correctly identifies this. The `"unknown"` default ensures `method` is never `None` when used as a dict key.

6. **No schema changes, no backfill:** The `signals.confidence` column (`FLOAT NOT NULL DEFAULT 0.8`) already exists. The change is forward-looking only — existing 489 signals at 0.8 remain unchanged. This is acceptable per spec: confidence is metadata with zero downstream financial consumers.

7. **No Financial Hotpath involvement:** Verified — `signals.confidence` has zero references in `lifecycle.py`, `engine.py`, `portfolio_stats.py`, `dashboard/`, or any PnL calculation. The `trader_score.py` `TraderScore.confidence` and `reconciler.py` string-typed `confidence="HIGH"` are entirely separate concepts. This task stays at 🟡 STANDARD — no auto-escalation needed.

---

## Acceptance Criteria Coverage

**Assessment: WELL COVERED** ✅

The proposal lists 6 acceptance criteria (§7), covered by 12 tests (9 MUST + 3 SHOULD):

| AC # | Criterion | Test(s) Covering It | Adequate? |
|------|-----------|-------------------|-----------|
| 1 | `cornix_regex` → confidence=0.95 | `test_cornix_regex_gets_095` + 6 other per-key tests | ✅ |
| 2 | Explicit `ext.confidence=0.73` preserved | `test_explicit_extractor_confidence_preserved` | ✅ |
| 3 | Unknown/missing method → 0.80 | `test_unknown_method_gets_080`, `test_missing_method_gets_080` | ✅ |
| 4 | `>1.0 / 10.0` normalization unaffected | `test_confidence_gt1_normalization_unchanged`, `test_explicit_high_confidence_preserved` | ✅ |
| 5 | All existing tests pass | Regression gate | ✅ |
| 6 | `[extracted: METHOD]` notes tag unchanged | Implicitly covered (no code changes to lines 822–823) | ✅ |

**Test coverage is thorough.** All 7 map keys have dedicated tests (4 MUST + 3 SHOULD), plus explicit-confidence preservation, unknown/missing fallback, and normalization regression tests. The split of 9 MUST / 3 SHOULD is reasonable — the 3 SHOULD tests cover less common parsers (`chroma_regex`, `inline_fallback`, `qwen_v3`) where the risk of implementation error is lower (they follow the same dict-lookup code path).

---

## Concerns

None that would block approval. Minor observations:

### Minor: `oinxtractor_agent` at 0.75 — Flagged for Mike

The proposal correctly flags this as a FORGE estimate needing data-backed validation. The value is reasonable (between text-NL at 0.70 and structured regex at 0.90), but image-LLM extraction has different failure modes than text-NL. If Mike has production accuracy data, this should be adjusted before or shortly after A5 ships. This is advisory, not a spec violation.

### Minor: Confidence Score Ordering

The scores follow a sensible gradient:
- Structural regex: 0.90–0.95 (cornix, telegram_direct, chroma)
- Image-LLM: 0.75 (oinxtractor_agent)
- Text-LLM / fallback: 0.70 (llm_nl, inline_fallback, qwen_v3)
- Unknown: 0.80 (default)

The `unknown` default at 0.80 sits between the LLM tier (0.70) and the structured tier (0.90), which is reasonable as an agnostic midpoint. No spec issue here.

### Minor: Test File Name

Proposal §6 says `tests/test_a5_confidence.py`; FORGE plan §5 says `tests/test_micro_gate_confidence.py`. Either is fine — ANVIL should pick one and be consistent. The canonical test directory is `.openclaw/workspace/tests/`.

---

## Suggestions

1. **For Phase 1 implementation:** Capture the `ext.get("confidence") is None` check *before* the normalization block, not after. The proposal's §4 Key Decision #1 already specifies this — just reinforcing that the ordering is critical. A variable like `extractor_supplied_confidence = ext.get("confidence") is not None` before line 797 is the cleanest approach.

2. **GUARDIAN verification query (§10):** The post-deploy SQL using `notes LIKE '%[extracted: ...]%'` is a good pragmatic approach. For Phase 1, consider also adding the `extraction_method` value to the INSERT's column set if it isn't already there — but this is a future enhancement, not an A5 requirement.

3. **Map maintenance note:** When new extraction methods are added in future tasks, the `PARSER_CONFIDENCE_MAP` should be updated. The 0.80 fallback via `dict.get()` is safe, but silent fallback to 0.80 for a new high-quality parser would be a metadata regression. Consider adding a code comment noting this maintenance requirement.

---

## Phase 1 Notes for VIGIL

When reviewing the Phase 1 code submission:

- **Tier:** 🟡 STANDARD (no Financial Hotpath involvement confirmed)
- **Threshold:** ≥9.0 overall
- **Key verification points:**
  - `ext.get("confidence") is None` check happens BEFORE the `_safe_float()` normalization (not after)
  - `PARSER_CONFIDENCE_MAP` is module-level constant, not inside a function
  - All 7 keys present with correct scores
  - `dict.get(method, 0.8)` fallback for unknown methods
  - Existing normalization block (`>1.0 / 10.0`) unchanged
  - `extraction_method` read from `entry` (top-level), not `ext`
  - All existing tests pass unmodified

---

**Verdict: ✅ APPROVE**

The proposal is well-grounded in source code evidence. Both audit CRITICAL findings (C1: canonical file ambiguity, C2: phantom map keys) have been fully resolved in the v1.1 plan and this proposal. The 7-key `PARSER_CONFIDENCE_MAP` is verified against current producers, the `is None` detection approach is correct, and the test strategy covers all 6 acceptance criteria with 12 tests. No schema changes, no backfill, no Financial Hotpath involvement, clean rollback. This is a low-risk metadata improvement that will produce code well within the ≥9.0 STANDARD threshold.

Proceed to Phase 1 implementation.

---

*VIGIL 🔍 — Phase 0 Review*
*2026-04-19 13:29 CEST*
