# Task A11: Leverage Source Tracking (NOT Leverage Defaults)

**Source:** Arbiter-Oink Phase 4 V2, Phase A; Phase 3 §ADAPT/leverage-model  
**Tier:** 🟢 LIGHTWEIGHT  
**Dependencies:** None  
**Canonical file:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, HEAD `69d6840a`)  
**Codebase Verified At:** micro-gate `69d6840a`, oink-sync `ab5d941` (2026-04-19)

---

## 0. Executive Summary

### FORGE Decision: Do NOT Default Leverage — Track Its Source Instead

**Problem statement:** 395 of 493 signals (80.1%) have `leverage = NULL`. The Arbiter-Oink report suggests "leverage defaults by asset class."

**FORGE argues against defaulting leverage.** Here's why:

1. **NULL is informationally correct.** A crypto signal that says "BUY SOL" without specifying leverage genuinely has unknown leverage. Defaulting to 10x (or any number) manufactures false precision. PnL calculations that use leverage will produce wrong results.

2. **Leverage varies enormously.** Crypto traders use 2x–125x. There is no "typical" default. Even within a single trader's signals, leverage ranges from 5x to 50x.

3. **Dashboard already handles NULL.** The OinkFarm dashboard displays "—" for NULL leverage. No UI fix needed.

4. **The real problem is provenance.** When leverage IS present (98 signals), we don't know if the trader stated it explicitly ("20x leverage") or if the LLM hallucinated it from context ("I'll use 20x" in a general message). This distinction matters for analytics.

**FORGE's alternative:** Add `leverage_source` to track WHERE the leverage value came from:
- `EXPLICIT` — trader stated leverage in the signal message
- `EXTRACTED` — LLM extracted from context (lower confidence)
- `DEFAULT` — system-assigned default (if Mike later decides to add defaults)
- `NULL` — not provided (current state for 80.1% of signals)

This lets analytics filter by provenance without manufacturing false data.

---

## 1. Current State Analysis

### Leverage Column (verified)

```sql
PRAGMA table_info(signals);
-- 15|leverage|FLOAT|0||0    (nullable, no default)
```

### Leverage Distribution

```sql
SELECT leverage, COUNT(*) FROM signals GROUP BY leverage ORDER BY COUNT(*) DESC LIMIT 10;
```

| leverage | count | Notes |
|----------|-------|-------|
| NULL | 395 | 80.1% — not provided |
| 10.0 | 27 | Explicitly stated (likely) |
| 20.0 | 22 | Explicitly stated (likely) |
| 5.0 | 14 | Explicitly stated |
| 15.0 | 11 | Explicitly stated |
| 50.0 | 8 | High leverage |
| 25.0 | 6 | |
| 3.0 | 3 | |
| 100.0 | 2 | Very high |
| 75.0 | 2 | |

### Current Leverage Handling (micro-gate line 830-840)

```python
leverage = ext.get("leverage")
if isinstance(leverage, (int, float)):
    leverage = float(leverage)
elif isinstance(leverage, str):
    try:
        leverage = float(leverage.replace("x", "").replace("X", ""))
    except (ValueError, TypeError):
        leverage = None  # "2x-10x" stays as None; preserved in notes
```

Leverage comes from the extraction payload. If the LLM provides it, it's used. If not, it stays NULL. No source tracking.

### Leverage in oink-sync

```
grep -rn "leverage" oink_sync/lifecycle.py → 0 hits
```

oink-sync does NOT use leverage for any calculation. It's purely metadata stored in the signals table and displayed on the dashboard.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_signal()` | MODIFY | Set `leverage_source` based on extraction payload |
| `.openclaw/workspace/scripts/micro-gate-v3.py` | INSERT statement (line 855) | MODIFY | Add `leverage_source` to INSERT |
| `.openclaw/workspace/tests/test_a11_leverage_source.py` | — | CREATE | Test leverage_source assignment |

---

## 3. SQL Changes

### Schema Migration

```sql
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
```

### Backfill (optional, low priority)

```sql
-- Set leverage_source for existing signals based on current data
UPDATE signals SET leverage_source = 'EXPLICIT' WHERE leverage IS NOT NULL;
-- NULL leverage → leave leverage_source as NULL (equivalent to "not provided")
```

---

## 4. Implementation Notes

### 4a. leverage_source Logic

After the existing leverage normalization block (line 830-840), add:

```python
# A11: Track leverage provenance
if ext.get("leverage") is not None:
    leverage_source = "EXPLICIT"  # Extraction payload had leverage
else:
    leverage_source = None  # Not provided
```

**Future enhancement:** If Mike later adds defaults, the logic would become:
```python
if ext.get("leverage") is not None:
    leverage_source = "EXPLICIT"
elif asset_class in LEVERAGE_DEFAULTS:
    leverage = LEVERAGE_DEFAULTS[asset_class]
    leverage_source = "DEFAULT"
else:
    leverage_source = None
```

### 4b. No Event Logging Required

leverage_source is metadata set at INSERT time. No lifecycle event needed.

---

## 5. Test Specification

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| test_explicit_leverage | ext.leverage=20 | leverage=20.0, leverage_source="EXPLICIT" | unit | MUST |
| test_no_leverage | ext.leverage=None | leverage=NULL, leverage_source=NULL | unit | MUST |
| test_string_leverage | ext.leverage="10x" | leverage=10.0, leverage_source="EXPLICIT" | unit | MUST |
| test_range_leverage | ext.leverage="5x-10x" | leverage=NULL (parse fails), leverage_source=NULL | unit | MUST |
| test_backfill | Existing signal with leverage=20 | leverage_source="EXPLICIT" after backfill | integration | SHOULD |

---

## 6. Acceptance Criteria

1. New signals with explicit leverage have `leverage_source = 'EXPLICIT'`
2. New signals without leverage have `leverage_source = NULL`
3. Backfill sets `leverage_source = 'EXPLICIT'` for 98 existing signals with non-NULL leverage
4. No regression in leverage parsing (existing tests pass)

---

## 7. Rollback Plan

1. `ALTER TABLE signals DROP COLUMN leverage_source;`
2. Revert micro-gate code changes
3. No data loss — leverage column is untouched

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Column added but never queried | Low | Wasted storage (negligible) | Dashboard/analytics team can query it |
| LLM-hallucinated leverage marked as EXPLICIT | Medium | Misleading source tracking | Future: add EXTRACTED source for LLM-inferred leverage |

---

## 9. Evidence

- 395/493 (80.1%) signals have NULL leverage — confirmed
- oink-sync does NOT use leverage for PnL — confirmed (0 grep hits)
- Leverage ranges from 3x to 100x — no sensible default exists
- No downstream consumer reads leverage programmatically — it's display-only

**Commits:** micro-gate `69d6840a`, oink-sync `ab5d941`
