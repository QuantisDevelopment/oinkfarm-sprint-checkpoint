# Task A.5: Parser-Type Confidence Scoring

**Source:** Arbiter-Oink Phase 4 §3 (Signal Metadata Quality), Phase 3 §ADAPT/confidence-model
**Tier:** 🟡 STANDARD
**Dependencies:** None for the core confidence-map change.
**Estimated Effort:** 0.5 day
**Plan Version:** 1.1 (revised per Wave 2 audit)
**Canonical file:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, HEAD `498d8b28`)  
**Note:** The signal-gateway copy at `scripts/micro-gate-v3.py` (1,063 LOC) is stale — do NOT use it as the implementation target.

---

## 0. Executive Summary

The `signals.confidence` column currently stores a float derived from the extraction payload. When the extractor does not supply a confidence value, micro-gate defaults to `0.8` regardless of which parser produced the signal. This is inaccurate: a Cornix regex parse is structurally deterministic (should score 0.95), while an LLM-based NL parse is probabilistic (should score 0.70).

This plan replaces the catch-all `0.8` default with a parser-type confidence map keyed on `extraction_method`. The extraction_method is already present in the incoming payload and is already stored in signal notes (as `[extracted: cornix_regex]`). No new columns are required.

**Design question resolved:** FORGE recommends tracking `extraction_method` confidence in the `signals` table directly (via the existing `confidence` column) rather than adding a new column, since the column already exists with the correct semantics.

---

## 1. Current State Analysis

### Confidence Column (Verified)

```sql
PRAGMA table_info(signals);
-- 17|confidence|FLOAT|1|0.8|0
-- Column DEFAULT is 0.8 — but micro-gate always provides an explicit value.
-- The DB-level default is a safety net only.
```

### Current Confidence Logic (canonical micro-gate lines 797–801)

```python
# ── 10. Confidence normalization ──
confidence = _safe_float(ext.get("confidence"), 0.8)  # default = 0.8
if confidence > 1.0:
    confidence = round(confidence / 10.0, 2)
confidence = max(0.0, min(1.0, confidence))
```

This block reads `confidence` from the extraction payload (set by signal_router/extractor). If the extraction set a confidence value, it's used. If not (or if the field is missing), the default 0.8 is applied without considering what parser produced the signal.

### Current Extraction Method Usage (canonical lines 822-823, 314)

```python
# Line 822-823 in _process_signal():
method = entry.get("extraction_method", "unknown")
notes_parts.append(f"[extracted: {method}]")

# Line 314 in _log_rejection():
"extraction_method": entry.get("extraction_method"),
```

`extraction_method` is already read from the `entry` dict (top-level, not nested in `ext`). It is added to notes but never used to influence `confidence`. This is the gap this task fills.

### Known Parser Types in Production (verified against source code)

Producers verified by `grep -rn 'extraction_method.*=' scripts/signal_gateway/` and `.openclaw/workspace/scripts/`:

| extraction_method | Where Set | Expected Confidence | Rationale |
|-------------------|-----------|---------------------|-----------|
| `cornix_regex` | signal_router.py:3043 | 0.95 | Cornix format is machine-generated, highly structured |
| `chroma_regex` | signal_router.py:3191 | 0.90 | Chroma feed is semi-structured, high reliability |
| `llm_nl` | signal_router.py:3407 | 0.70 | Probabilistic text-NL parsing via Gemma 4, highest hallucination risk |
| `oinxtractor_agent` | signal_router.py:3297, oinxtractor_client.py:190 | 0.75 | Image-first LLM extraction (Qwen 35B MoE) — better than blind text NL but still probabilistic. ⚠️ *Value needs data-backed validation — flagged for Mike* |
| `telegram_direct` | signal_router.py:2000 | 0.92 | Structured Cornix-format via MTProto, reliable but not as rigid as direct regex |
| `inline_fallback` | signal_router.py:3272 | 0.70 | Fallback extraction path before oinxtractor/llm — lower reliability |
| `qwen_v3` | signal-extract-v3.py:492 (.openclaw) | 0.70 | Legacy Qwen extraction script, same tier as llm_nl |
| Any other / `unknown` | Fallback | 0.80 | Existing default retained |

**Removed from v1.0 map (no current producer in code):**
- ~~`board_reconciler`~~ — reconciler events flow through as `wg_reconciler` in payloads but do NOT set `extraction_method = "board_reconciler"` in any current code path
- ~~`oinkdb_opus`~~ — not produced by any current `.py` file
- ~~`manual`~~ — not produced as an extraction_method value by any current `.py` file

**⚠️ Decision needed from Mike:** The `oinxtractor_agent` confidence (0.75) is a FORGE estimate based on image-LLM risk profile being between text-NL (0.70) and structured regex (0.90). If production accuracy data becomes available, this should be data-backed.

### Current Confidence Distribution in DB

```sql
SELECT ROUND(confidence, 1) as conf, COUNT(*) FROM signals GROUP BY conf ORDER BY conf;
```
Most signals will cluster around 0.8 (the legacy default) plus any extractor-provided values. The task improves metadata quality for new signals without requiring backfill of historical data.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_signal()` | MODIFY | After existing confidence normalization (canonical lines 797–801), apply `PARSER_CONFIDENCE_MAP` override when payload confidence is absent/default |
| `.openclaw/workspace/scripts/micro-gate-v3.py` | Module level (after imports) | ADD | `PARSER_CONFIDENCE_MAP` dict constant |
| `.openclaw/workspace/tests/test_a5_confidence.py` | — | CREATE | Unit tests for confidence map behavior |

**Canonical file:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, HEAD `498d8b28`). The signal-gateway copy is stale (1,063 LOC, Apr 15).

**Note:** The canonical micro-gate already has `EventStore` import and `_log_event()` helper (lines 36–78). A5 does not need event logging, but ANVIL should be aware this import exists (unlike the stale signal-gateway copy).

---

## 3. SQL Changes

None required. The `signals.confidence` column already exists as `FLOAT NOT NULL DEFAULT 0.8`. No schema migration needed.

---

## 4. Implementation Notes

### 4a. PARSER_CONFIDENCE_MAP Constant

Place after imports / before first `def` in `micro-gate-v3.py`:

```python
# A5: Parser-type confidence scoring
# Keys match extraction_method values from signal_router / OinkDB
# Fallback (unknown/missing) = 0.8 (existing default)
PARSER_CONFIDENCE_MAP = {
    "cornix_regex":       0.95,  # structured Cornix bot regex (signal_router.py:3043)
    "chroma_regex":       0.90,  # structured Chroma feed regex (signal_router.py:3191)
    "telegram_direct":    0.92,  # Cornix-format via MTProto (signal_router.py:2000)
    "oinxtractor_agent":  0.75,  # image-first Qwen 35B MoE (signal_router.py:3297) — ⚠️ needs data validation
    "llm_nl":             0.70,  # text-NL Gemma 4 extraction (signal_router.py:3407)
    "inline_fallback":    0.70,  # fallback before LLM (signal_router.py:3272)
    "qwen_v3":            0.70,  # legacy Qwen extraction (signal-extract-v3.py:492)
}
```

### 4b. Logic Change in `_process_signal()`

**Current logic (canonical lines 797–801):**

```python
confidence = _safe_float(ext.get("confidence"), 0.8)
if confidence > 1.0:
    confidence = round(confidence / 10.0, 2)
confidence = max(0.0, min(1.0, confidence))
```

**A5 change (pseudocode — ANVIL implements):**

After the existing normalization block, check if confidence came from the payload (was explicitly set by the extractor) vs. fell back to the 0.8 default. If it's the default, override with the parser-type score:

```
# Note: extraction_method is on `entry` (top-level), not `ext` (extraction sub-dict)
method = entry.get("extraction_method", "unknown")

# Only apply map override if the extractor did NOT supply an explicit confidence value
# (i.e., confidence came from the default 0.8 fallback)
if ext.get("confidence") is None:
    confidence = PARSER_CONFIDENCE_MAP.get(method, 0.8)
# else: keep the extractor-supplied value (already normalized above)
```

**ANVIL decision:** The exact mechanism for detecting "extractor did not supply confidence" vs. "extractor supplied 0.8 explicitly" is subtle. Options:
1. Check `ext.get("confidence") is None` before the normalization block (recommended by FORGE — explicit None check before any default is applied)
2. Check if the original value equals 0.8 after normalization (fragile — extractor could legitimately supply 0.8)

**FORGE recommendation: Option 1.** Capture whether the extractor supplied a confidence value before normalization. If not supplied, use PARSER_CONFIDENCE_MAP. If supplied (even if 0.8), respect the extractor's explicit value.

### 4c. Preservation of Existing Extractor Confidence

Some signals already arrive with confidence values set by signal_router's LLM extractions (e.g., Gemma outputs a logprob-derived confidence of 0.73). These should be respected. The map only applies when the extractor did not provide a confidence value.

### 4d. No Event Logging Required

This task changes a field value at INSERT time, so no lifecycle event is required for the core implementation. The `confidence` value is stored in the signal row itself, and the extraction method is already in the `notes` field. GUARDIAN can audit `confidence` distributions via SQL queries.

If Mike later wants explicit confidence-assignment events, that should be tracked as a follow-up after the event-store path is verified in the signal-gateway codebase.

**Exception:** If a future audit reveals systematic confidence drift (e.g., llm_nl signals consistently underperforming 0.70 threshold), FORGE recommends adding a `CONFIDENCE_ASSIGNED` event type in a follow-up task. Not required for A5.

### 4e. Notes Field Already Tags extraction_method

Line 597–598 already writes `[extracted: cornix_regex]` into notes. A5 does not need to change this — it provides the audit trail for understanding confidence values.

---

## 5. Test Specification

New test file: `tests/test_micro_gate_confidence.py`

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_cornix_regex_gets_095` | `entry = {extraction_method: "cornix_regex"}`, no `confidence` in ext | `confidence = 0.95` stored in DB | unit | MUST |
| `test_llm_nl_gets_070` | `entry = {extraction_method: "llm_nl"}`, no `confidence` in ext | `confidence = 0.70` stored in DB | unit | MUST |
| `test_oinxtractor_agent_gets_075` | `entry = {extraction_method: "oinxtractor_agent"}`, no `confidence` in ext | `confidence = 0.75` stored in DB | unit | MUST |
| `test_telegram_direct_gets_092` | `entry = {extraction_method: "telegram_direct"}`, no `confidence` in ext | `confidence = 0.92` stored in DB | unit | MUST |
| `test_unknown_method_gets_080` | `entry = {extraction_method: "mystery_parser"}`, no `confidence` in ext | `confidence = 0.80` stored in DB | unit | MUST |
| `test_missing_method_gets_080` | `entry = {}` (no extraction_method), no `confidence` in ext | `confidence = 0.80` stored in DB | unit | MUST |
| `test_explicit_extractor_confidence_preserved` | `entry = {extraction_method: "llm_nl"}`, `ext.confidence = 0.62` | `confidence = 0.62` (extractor value respected, NOT overridden by map) | unit | MUST |
| `test_explicit_high_confidence_preserved` | `entry = {extraction_method: "cornix_regex"}`, `ext.confidence = 8.5` (raw scale) | `confidence = 0.85` (divided by 10, normalized — extractor value respected) | unit | MUST |
| `test_confidence_gt1_normalization_unchanged` | `ext.confidence = 9.5` | `confidence = 0.95` (existing normalization unchanged) | regression | MUST |
| `test_chroma_regex_gets_090` | `entry = {extraction_method: "chroma_regex"}`, no `confidence` in ext | `confidence = 0.90` stored in DB | unit | SHOULD |
| `test_inline_fallback_gets_070` | `entry = {extraction_method: "inline_fallback"}`, no `confidence` in ext | `confidence = 0.70` stored in DB | unit | SHOULD |
| `test_qwen_v3_gets_070` | `entry = {extraction_method: "qwen_v3"}`, no `confidence` in ext | `confidence = 0.70` stored in DB | unit | SHOULD |

---

## 6. Acceptance Criteria

1. **Map applied:** After A5 deployment, new signals inserted via `cornix_regex` have `confidence = 0.95` in the DB (verified by direct query)
2. **Extractor values preserved:** A signal with explicit `ext.confidence = 0.73` has `confidence = 0.73` in DB (not overridden by map)
3. **Unknown methods fall back to 0.8:** A signal with `extraction_method = "unknown"` or missing has `confidence = 0.80`
4. **No regression in normalization:** The existing `> 1.0 → divide by 10` normalization path is unaffected
5. **All existing tests pass:** All tests in `.openclaw/workspace/tests/` pass without modification
6. **Notes field unchanged:** `[extracted: cornix_regex]` tag continues to appear in signal notes (no change to lines 597–598)

---

## 7. Rollback Plan

1. **Code rollback:** `git revert <A5-commit-hash>` in signal-gateway repo
2. **Data impact:** Confidence values for signals already inserted with A5 active will retain their parser-type scores (e.g., 0.95, 0.70). Rolling back code does not change existing DB rows — this is acceptable. Confidence is metadata; no financial calculations depend on it.
3. **Service restart:** Signal-gateway processes signals via batch runs — no persistent service to restart. Changes take effect on next batch run.
4. **Verification:**
   ```sql
   SELECT extraction_method_tag, confidence
   FROM (
     SELECT
       CASE
         WHEN notes LIKE '%[extracted: cornix_regex]%' THEN 'cornix_regex'
         WHEN notes LIKE '%[extracted: llm_nl]%' THEN 'llm_nl'
         ELSE 'other'
       END as extraction_method_tag,
       confidence
     FROM signals ORDER BY id DESC LIMIT 50
   );
   -- After rollback: cornix_regex signals will show 0.80 again (if inserted post-rollback)
   ```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Extractor-provided confidence values overridden by map | Low | Medium — incorrect metadata | `ext.get("confidence") is None` check before applying map ensures explicit values are preserved |
| New extraction_method values (future parsers) not in map | Medium | Very Low — falls back to 0.8 | `PARSER_CONFIDENCE_MAP.get(method, 0.8)` fallback handles unknown methods gracefully |
| Confidence column used in downstream ML/scoring logic | Low | Low | Verified: no references to `confidence` in lifecycle.py, engine.py, portfolio_stats.py, portfolio-webhook.py, dashboard, or any PnL calculation. `trader_score.py` uses a separate `TraderScore.confidence` concept (Bayesian sample-size), unrelated to `signals.confidence`. |
| Signal dedup (cross-channel) uses confidence | No | None | Dedup logic uses trader_id+ticker+direction+entry_price, not confidence |

---

## 9. Evidence

**Canonical file verified:**
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, HEAD `498d8b28`)
- Confidence normalization: canonical lines 797–801
- extraction_method read: canonical lines 822–823
- `_log_event()` helper at line 61 (exists in canonical but NOT in signal-gateway copy)

**Production DB verified against:** `/home/m/data/oinkfarm.db` (NOT `/home/oinkv/oink-sync/oink.db` which is 0-byte)

**Database queries run:**
```sql
-- Confidence column definition
PRAGMA table_info(signals);
-- 17|confidence|FLOAT|1|0.8|0

-- Current confidence distribution
SELECT ROUND(confidence, 2) as conf, COUNT(*) as cnt
FROM signals GROUP BY conf ORDER BY cnt DESC;
-- 0.8 → 489, 0.85 → 2, 0.9 → 1
```

**Downstream consumer audit (CF5 from audit):**
- `oink_sync/lifecycle.py`: 0 hits for `confidence` ✅
- `oink_sync/engine.py`: 0 hits ✅
- `portfolio_stats.py`, `portfolio-webhook.py`: 0 hits ✅
- `dashboard/`: 0 hits ✅
- `trader_score.py`: uses `TraderScore.confidence` (Bayesian sample-size) — **different concept**, unrelated ✅
- `reconciler.py`, `discord_notify.py`: use string-typed `confidence="HIGH"|"MEDIUM"|"LOW"` — **different concept** ✅

**Extraction method producers verified:**
- `cornix_regex` → signal_router.py:3043 ✅
- `chroma_regex` → signal_router.py:3191 ✅
- `llm_nl` → signal_router.py:3407 ✅
- `oinxtractor_agent` → signal_router.py:3297 ✅
- `telegram_direct` → signal_router.py:2000 ✅
- `inline_fallback` → signal_router.py:3272 ✅
- `qwen_v3` → signal-extract-v3.py:492 (.openclaw) ✅
- ~~board_reconciler~~ → not found in any .py file ❌ removed from map
- ~~oinkdb_opus~~ → not found ❌ removed
- ~~manual~~ → not found ❌ removed

**Git commits reviewed:**
- `498d8b28` — oinkfarm canonical HEAD
- `38eb8e8` — signal-gateway HEAD (extraction_method producers)

---

## Revisions — 2026-04-19 (Wave 2 audit)

Applied based on Hermes fallback audit (`OINKV-AUDIT-WAVE2-A5.md`). All changes are surgical — plan structure and rationale preserved.

| Audit Code | What Changed |
|---|---|
| C1 | Canonical file clarified as `.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC). All line numbers remapped (573→797, 597→822, 250→314). |
| C2 | PARSER_CONFIDENCE_MAP rebuilt from verified source-code producers. Removed 3 phantom keys (`board_reconciler`, `oinkdb_opus`, `manual`). Added 4 real producers (`oinxtractor_agent` 0.75, `telegram_direct` 0.92, `inline_fallback` 0.70, `qwen_v3` 0.70). |
| M1 | (Absorbed into C2) |
| M2 | Evidence section now uses `/home/m/data/oinkfarm.db` (live DB). |
| M3 | Evidence section notes canonical micro-gate HAS EventStore import (lines 36-78), unlike stale signal-gateway copy. |
| M4 | Test file target clarified as `.openclaw/workspace/tests/test_a5_confidence.py`. |
| CF5 | Risk table "Confidence used in downstream ML/scoring" downgraded from Unknown/Unknown to Low/Low with evidence. |
| NEW | `oinxtractor_agent` confidence (0.75) flagged as needing data-backed validation from Mike. |
