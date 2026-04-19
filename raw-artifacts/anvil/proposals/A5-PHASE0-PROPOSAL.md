# A5 Phase 0 — Technical Proposal
# Parser-Type Confidence Scoring

**Task:** A5 — Parser-Type Confidence Scoring
**Tier:** 🟡 STANDARD
**Phase 4 Ref:** §3 Signal Metadata Quality, Phase 3 §ADAPT/confidence-model
**Plan:** `/home/oinkv/forge-workspace/plans/TASK-A5-plan.md` (v1.1)
**OinkV Audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A5.md`
**Revision:** 0
**Date:** 2026-04-19

---

## 1. Problem

The `signals.confidence` column stores a float derived from the extraction payload. When the extractor does not supply an explicit confidence value (which is the case for 99.4% of signals — 489 of 492), micro-gate defaults to `0.8` regardless of which parser produced the signal. This is inaccurate: a Cornix regex parse is structurally deterministic and should score higher (0.95), while an LLM-based NL parse is probabilistic and should score lower (0.70). The catch-all 0.8 default obscures extraction quality and makes downstream confidence-based filtering meaningless.

## 2. Approach

Add a module-level `PARSER_CONFIDENCE_MAP` dict to the canonical micro-gate (`/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py`, 1407 LOC). In `_process_signal()`, after the existing confidence normalization block (lines 797–801), check whether the extractor supplied an explicit confidence value (`ext.get("confidence") is None`). If not supplied, override with the parser-type score from the map keyed on `extraction_method`. If supplied, preserve the extractor's explicit value unchanged.

## 3. PARSER_CONFIDENCE_MAP (7 keys, verified against source code)

All keys verified against current producers in `signal_router.py`, `oinxtractor_client.py`, and `signal-extract-v3.py`:

| Key | Score | Rationale |
|-----|-------|-----------|
| `cornix_regex` | 0.95 | Machine-generated Cornix format, structural regex (signal_router.py:3043) |
| `telegram_direct` | 0.92 | Cornix-format via MTProto, reliable but less rigid (signal_router.py:2000) |
| `chroma_regex` | 0.90 | Semi-structured Chroma feed regex (signal_router.py:3191) |
| `oinxtractor_agent` | 0.75 | Image-first Qwen 35B MoE extraction (signal_router.py:3297) — ⚠️ needs data-backed validation from Mike |
| `llm_nl` | 0.70 | Probabilistic text-NL Gemma 4 extraction (signal_router.py:3407) |
| `inline_fallback` | 0.70 | Fallback extraction path before LLM (signal_router.py:3272) |
| `qwen_v3` | 0.70 | Legacy Qwen extraction script (signal-extract-v3.py:492) |
| (any other / `unknown`) | 0.80 | Existing default retained via `PARSER_CONFIDENCE_MAP.get(method, 0.8)` |

**Removed from earlier plan versions (no current producer in code):** `board_reconciler`, `oinkdb_opus`, `manual`. These three keys were phantom — no `.py` file sets `extraction_method` to any of them.

## 4. Key Decisions

1. **Option 1 for None detection:** Capture `ext.get("confidence") is None` *before* the normalization block applies the 0.8 default. This is the safe path — it distinguishes "extractor didn't supply confidence" from "extractor explicitly supplied 0.8". The `_safe_float(ext.get("confidence"), 0.8)` call on line 798 makes post-hoc detection impossible since both cases produce 0.8.

2. **No schema changes:** The `signals.confidence` column already exists as `FLOAT NOT NULL DEFAULT 0.8`. No ALTER TABLE, no migration, no backfill.

3. **No event logging:** Confidence assignment happens at INSERT time and is stored in the signal row. The `[extracted: METHOD]` notes tag (line 822–823) already provides the audit trail. GUARDIAN can query confidence distributions by extraction method via SQL.

4. **No backfill of historical data:** All 489 signals at confidence=0.8 remain unchanged. The improvement is forward-looking only. This is acceptable because confidence is metadata — no financial calculations depend on it (verified: 0 references in lifecycle.py, engine.py, portfolio_stats.py, dashboard).

5. **`oinxtractor_agent` at 0.75 — flagged for Mike:** This is a FORGE estimate based on image-LLM risk being between text-NL (0.70) and structured regex (0.90). If production accuracy data suggests a different value, Mike should override.

## 5. Files Changed

| File | Change |
|------|--------|
| `scripts/micro-gate-v3.py` | `PARSER_CONFIDENCE_MAP` constant (module-level); confidence override logic in `_process_signal()` (~8 lines) |
| `tests/test_a5_confidence.py` | 12 tests: 9 MUST + 3 SHOULD (new file) |

## 6. Test Strategy

12 tests covering:
- Each of the 7 map keys → correct confidence stored in DB (7 tests)
- Unknown/missing method → 0.80 fallback (2 tests)
- Explicit extractor confidence preserved (not overridden by map) (1 test)
- Explicit high confidence (>1.0) normalization path unchanged (1 test)
- Regression: `>1.0 / 10.0` normalization still works (1 test)

## 7. Acceptance Criteria

1. New `cornix_regex` signals have `confidence = 0.95` in DB
2. Explicit `ext.confidence = 0.73` preserved as 0.73 (not overridden)
3. Unknown/missing extraction_method → `confidence = 0.80`
4. `>1.0 / 10.0` normalization path unaffected
5. All existing tests pass without modification
6. `[extracted: METHOD]` notes tag continues to appear

## 8. Rollback

`git revert <commit>` — no schema changes, no data modifications. Signals inserted during A5-active retain their parser-type scores (acceptable — confidence is metadata, not financial).

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Extractor-provided confidence overridden | Low | Medium | `is None` check before map application |
| Future parser not in map | Medium | Very Low | Fallback to 0.8 via dict.get() |
| Confidence used downstream | Low | Low | Verified: 0 consumers in lifecycle.py, engine.py, dashboard, PnL |
| Dedup uses confidence | No | None | Dedup uses trader_id+ticker+direction+entry_price, not confidence |

## 10. For GUARDIAN Specifically

- **No data writes beyond existing INSERT:** Confidence is set at INSERT time, same column, same row. No new tables, no new columns.
- **No formula changes:** No financial calculations reference `signals.confidence`.
- **Verification query (post-deploy):**
  ```sql
  SELECT 
    CASE
      WHEN notes LIKE '%[extracted: cornix_regex]%' THEN 'cornix_regex'
      WHEN notes LIKE '%[extracted: llm_nl]%' THEN 'llm_nl'
      WHEN notes LIKE '%[extracted: oinxtractor_agent]%' THEN 'oinxtractor_agent'
      ELSE 'other'
    END as method,
    ROUND(confidence, 2) as conf,
    COUNT(*) as cnt
  FROM signals
  WHERE id > (SELECT MAX(id) - 50 FROM signals)
  GROUP BY method, conf
  ORDER BY method, conf;
  ```
- **No canary needed:** Metadata-only change, no lifecycle/PnL impact. Standard post-deploy verification via the query above is sufficient.
