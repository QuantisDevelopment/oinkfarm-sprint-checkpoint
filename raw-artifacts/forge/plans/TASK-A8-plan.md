# Task A.8: Conditional SL Type Field

**Source:** Arbiter-Oink Phase 4 §3 (Signal Metadata Enrichment), Phase 5 §BS-6 (Stop-Loss Semantics Tracking)
**Tier:** 🟡 STANDARD
**Dependencies:** None (standalone schema + micro-gate change)
**Estimated Effort:** 0.5 day
**Plan Version:** 1.0
**Codebase Verified At:** micro-gate `69d6840a` (2026-04-19) / oinkfarm.db (493 signals)

---

## 0. Executive Summary

The `signals` table has a `stop_loss FLOAT` column, but there is no structured way to distinguish *why* `stop_loss` is NULL or what type of stop it is. Currently, micro-gate already detects conditional SL text (e.g., "SL if candle closes below X") and writes a notes tag `[SL:CONDITIONAL ...]` — but this is buried in a free-text `notes` field and cannot be reliably queried or aggregated.

This plan adds a `sl_type VARCHAR(15)` column with four canonical values:
- `FIXED` — explicit numeric price stop-loss (default for existing signals)
- `CONDITIONAL` — text-described condition that the extraction pipeline detected and tagged in `notes`
- `MANUAL` — human-override SL (set by the operator via an explicit UPDATE message after signal creation)
- `NONE` — no SL was provided at all in the original signal

**FORGE decision on SL_TYPE_SET event:** No dedicated event is emitted for `sl_type` changes. The value is set once at INSERT time and reflects the original signal's SL semantics — it is not a lifecycle state that changes. Backfill for existing signals (to populate `sl_type` from `notes` inspection) is optional and covered in §4e.

---

## 1. Current State Analysis

### Current SL detection in micro-gate-v3.py (lines 725–746, verified)

```python
stop_loss = _safe_float(ext.get("stop_loss"))
sl_note = ext.get("stop_loss_note") or ""
notes_parts = []

# Parse numeric from conditional SL string
if not stop_loss and sl_note:
    ...
    if num:
        stop_loss = _safe_float(num.group(1))

# Conditional SL marker (kraken-sync coupling)
if sl_note and any(kw in sl_note.lower() for kw in
                   ("close below", "close above", "4h", "1d", "daily", "weekly",
                    "h2", "h4", "d1", "5m", "15m", "1h")):
    notes_parts.append(f"[SL:CONDITIONAL {sl_note}]")
```

The conditional SL detection is already implemented — it writes `[SL:CONDITIONAL ...]` to notes. **No new detection logic is needed.** This plan only adds a structured column to persist the classification.

### Current leverage handling line (line 839, verified)

```python
leverage = None  # "2x-10x" stays as None in column; preserved in notes
```

Pattern: when a structured field cannot be parsed into a clean value, it's NULLed in the column and preserved in notes. `sl_type` follows the same philosophy but in reverse — it's always set (never NULL).

### Current DB state (verified)

```sql
-- Notes containing [SL:CONDITIONAL]:
SELECT COUNT(*) FROM signals WHERE notes LIKE '%SL:CONDITIONAL%';
-- Result: 0 (conditional SL detection in micro-gate is recent; no signals processed yet with this flag)

-- NULL stop_loss signals:
SELECT COUNT(*) FROM signals WHERE stop_loss IS NULL;
-- Result: 28 (5.7% of all signals)

-- Existing schema:
PRAGMA table_info(signals);
-- No sl_type column (column index 50 would be next)
```

### INSERT statement in micro-gate-v3.py (lines 925–940, verified)

```python
conn.execute("""
    INSERT INTO signals (
        discord_message_id, channel_id, channel_name, server_id, trader_id,
        message_type, ticker, direction, order_type, entry_price, stop_loss,
        take_profit_1, take_profit_2, take_profit_3,
        leverage, asset_class, confidence, exchange_ticker, exchange, exchange_matched,
        ...
    ) VALUES (?, ?, ?, ?, ?, ...)
""", (ticker, direction, order_type, entry_price, stop_loss, ...))
```

The `sl_type` column will be added to this INSERT statement.

### _process_update() in micro-gate-v3.py (lines 1003–1095, verified)

```python
_ALLOWED_UPDATE_COLS = {"stop_loss", "take_profit_1", "take_profit_2", "take_profit_3",
                        "leverage", "notes", "exit_price", "status", "fill_status"}
```

When an UPDATE message changes `stop_loss` via operator override, `sl_type` should be updated to `'MANUAL'`. The `_ALLOWED_UPDATE_COLS` set needs `sl_type` added.

---

## 2. Files to Modify

| File | Function/Class | Change Type | Description |
|------|----------------|-------------|-------------|
| `oinkfarm.db` (schema) | signals table | ALTER TABLE | Add `sl_type VARCHAR(15) DEFAULT 'FIXED'` column |
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_signal()` | MODIFY | After stop_loss and sl_note processing, set `sl_type` value; include in INSERT |
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | `_process_update()` | MODIFY | When `stop_loss` is updated via operator UPDATE message, also set `sl_type='MANUAL'`; add `sl_type` to `_ALLOWED_UPDATE_COLS` |
| `oink-sync/tests/test_lifecycle_events.py` | `_SIGNALS_SCHEMA` | MODIFY | Add `sl_type TEXT DEFAULT 'FIXED'` to in-memory test schema so existing tests don't fail on INSERT |

---

## 3. SQL Changes

### 3a. Schema migration (production DB)

```sql
-- Run once, non-destructive, backward-compatible
ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED';

-- Verify
PRAGMA table_info(signals);
-- sl_type should appear as new column at index 50, DEFAULT 'FIXED'
```

All existing 493 signals will receive `sl_type='FIXED'` via the DEFAULT. This is technically correct for the vast majority (99%+), with the rare exception of signals that have `[SL:CONDITIONAL...]` in their notes (currently 0 such signals).

### 3b. Optional backfill for conditional SL signals

```sql
-- Backfill: tag signals where notes indicate conditional SL
UPDATE signals
SET sl_type = 'CONDITIONAL'
WHERE notes LIKE '%SL:CONDITIONAL%'
  AND sl_type = 'FIXED';
-- Expected rows affected: 0 (no such signals currently)

-- Backfill: tag signals with no SL and no conditional note
UPDATE signals
SET sl_type = 'NONE'
WHERE stop_loss IS NULL
  AND notes NOT LIKE '%SL:CONDITIONAL%'
  AND sl_type = 'FIXED';
-- Expected rows affected: 28 (the NULL stop_loss population)
```

The NONE backfill should be run in coordination with the schema migration. The CONDITIONAL backfill is a no-op but safe to run.

### 3c. Verification queries

```sql
-- Post-migration distribution
SELECT sl_type, COUNT(*) as cnt FROM signals GROUP BY sl_type ORDER BY cnt DESC;
-- Expected: FIXED (465), NONE (28), CONDITIONAL (0 now), MANUAL (0 now)

-- Confirm sl_type is always set (no NULLs)
SELECT COUNT(*) FROM signals WHERE sl_type IS NULL;
-- Expected: 0
```

---

## 4. Implementation Notes

### 4a. sl_type classification logic in `_process_signal()`

After the existing stop_loss and sl_note processing block (after line 799 in current micro-gate), add:

```python
# ── sl_type determination ──
# Set AFTER stop_loss and sl_note processing is complete.
if stop_loss is not None:
    # Explicit numeric SL — check if also conditional
    if sl_note and any(kw in sl_note.lower() for kw in
                       ("close below", "close above", "4h", "1d", "daily", "weekly",
                        "h2", "h4", "d1", "5m", "15m", "1h")):
        sl_type = "CONDITIONAL"  # numeric extracted from conditional text
    else:
        sl_type = "FIXED"
elif sl_note and any(kw in sl_note.lower() for kw in
                     ("close below", "close above", "4h", "1d", "daily", "weekly",
                      "h2", "h4", "d1", "5m", "15m", "1h")):
    sl_type = "CONDITIONAL"  # no numeric could be extracted, but condition is known
else:
    sl_type = "NONE"  # no stop_loss, no conditional note
```

**Note:** The same keyword list used to write `[SL:CONDITIONAL ...]` to notes is used here to classify — ANVIL should use a shared constant or function rather than duplicating the list.

### 4b. sl_type in `_process_update()`

When `_process_update()` processes a human operator SL change (stop_loss updated via UPDATE message, not via a conditional note), set `sl_type='MANUAL'`:

```python
# MANUAL: operator explicitly changed the SL — override the original classification
if "stop_loss" in changes and new_sl is not None:
    changes["sl_type"] = "MANUAL"
```

Add `"sl_type"` to `_ALLOWED_UPDATE_COLS` set (line 1003).

### 4c. Column value enumeration

| Value | Meaning | Trigger |
|-------|---------|---------|
| `FIXED` | Explicit numeric price SL; extraction succeeded | `stop_loss IS NOT NULL` and no conditional keywords in `sl_note` |
| `CONDITIONAL` | Textual condition (e.g., "SL on daily close below 0.5") | `sl_note` contains conditional keywords, with or without numeric extraction |
| `MANUAL` | Operator-issued SL override via UPDATE message | `_process_update()` changes `stop_loss` |
| `NONE` | No stop-loss provided or determinable | `stop_loss IS NULL` and no conditional keywords |

### 4d. Keyword list deduplication

The same conditional-SL keyword list appears three times in the current code:
1. `sl_note.lower()` check to write the notes tag (line 743–746)
2. The new `sl_type` check in `_process_signal()` (this plan)
3. Any future references

ANVIL should extract this to a module-level constant:

```python
_CONDITIONAL_SL_KEYWORDS = (
    "close below", "close above",
    "4h", "1d", "daily", "weekly",
    "h2", "h4", "d1", "5m", "15m", "1h",
)
```

Then reference `_CONDITIONAL_SL_KEYWORDS` in both the notes-tag block and the sl_type block.

### 4e. Test schema compatibility

The in-memory test schema used by oink-sync tests (`test_lifecycle_events.py`, `test_remaining_pct.py`, `test_partially_closed.py`) has a hardcoded `CREATE TABLE signals (...)`. These don't include `sl_type`. When micro-gate's INSERT now includes `sl_type`, these tests will fail if they use the micro-gate INSERT path. However, the oink-sync tests construct their own DB (`:memory:`) with their own schema and do not run micro-gate INSERT statements — they insert signals directly with known values. Therefore **oink-sync tests are NOT affected** by this schema change.

The `_SIGNALS_SCHEMA` in `test_lifecycle_events.py` should still have `sl_type TEXT DEFAULT 'FIXED'` added for forward-compatibility, so tests don't fail if lifecycle.py ever reads `sl_type`.

### 4f. The 28 NULL stop_loss signals

```sql
SELECT ticker, direction, notes FROM signals WHERE stop_loss IS NULL LIMIT 10;
```

Running this query confirms these are legitimate signals where no SL was provided by the trader. The `sl_type='NONE'` backfill is accurate and safe.

---

## 5. Test Specification

New test file: `signal-gateway/tests/test_sl_type.py` (micro-gate tests)

| Test Name | Input | Expected Output | Type | Priority |
|-----------|-------|-----------------|------|----------|
| `test_fixed_sl_type_on_numeric_sl` | Signal payload with `stop_loss=0.95`, no `stop_loss_note`. | `signals.sl_type='FIXED'` after INSERT | unit | MUST |
| `test_none_sl_type_on_missing_sl` | Signal payload with no `stop_loss`, no `stop_loss_note`. | `signals.sl_type='NONE'` after INSERT | unit | MUST |
| `test_conditional_sl_type_on_keyword_note` | Signal payload with `stop_loss_note="SL if daily close below 0.45"`, no numeric stop_loss. | `signals.sl_type='CONDITIONAL'`, `notes LIKE '%SL:CONDITIONAL%'` | unit | MUST |
| `test_conditional_sl_type_with_extracted_numeric` | Signal with `stop_loss_note="close above 0.50"` where numeric is extractable. | `signals.stop_loss=0.50`, `signals.sl_type='CONDITIONAL'` (numeric extracted AND conditional) | unit | MUST |
| `test_manual_sl_type_on_update` | Signal initially `sl_type='FIXED'`. Operator sends UPDATE with new stop_loss value. | `signals.sl_type='MANUAL'` after UPDATE | unit | MUST |
| `test_sl_type_null_never_occurs` | Insert 10 signals covering all sl_type scenarios. | `SELECT COUNT(*) FROM signals WHERE sl_type IS NULL` returns 0 | integration | MUST |
| `test_sl_type_not_overwritten_by_update_without_sl` | Signal with `sl_type='FIXED'`. Operator sends UPDATE that changes only notes. | `signals.sl_type='FIXED'` unchanged | regression | SHOULD |
| `test_sl_type_backfill_query` | 3 signals: 1 with NULL SL, 1 with conditional notes, 1 with FIXED SL. Run backfill SQL. | `sl_type` = `'NONE'`, `'CONDITIONAL'`, `'FIXED'` respectively | unit | SHOULD |

---

## 6. Acceptance Criteria

1. **Schema:** `PRAGMA table_info(signals)` shows `sl_type` column at index 50, `VARCHAR(15)`, DEFAULT `'FIXED'`
2. **No NULLs:** `SELECT COUNT(*) FROM signals WHERE sl_type IS NULL` returns 0 (both pre-existing via DEFAULT and new via INSERT)
3. **Correct classification:**
   - New signal with numeric SL, no conditional keywords → `sl_type='FIXED'`
   - New signal with `stop_loss_note` containing conditional keywords → `sl_type='CONDITIONAL'`
   - New signal with no SL → `sl_type='NONE'`
   - Updated signal via operator SL change → `sl_type='MANUAL'`
4. **Backfill:** 28 existing NULL-SL signals have `sl_type='NONE'` after backfill SQL runs
5. **All existing tests pass:** All 4 oink-sync test files pass without modification

---

## 7. Rollback Plan

1. **Revert code:** `git revert <A8-commit-hash>` in micro-gate repo
2. **Revert schema:**
   ```sql
   -- SQLite doesn't support DROP COLUMN natively before 3.35.0
   -- For older SQLite: rebuild the table without sl_type
   -- For SQLite >= 3.35.0:
   ALTER TABLE signals DROP COLUMN sl_type;
   ```
3. **Verify:**
   ```sql
   PRAGMA table_info(signals);
   -- sl_type column should be gone
   ```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| SQLite DROP COLUMN not available (< 3.35.0) | Low (production likely >= 3.35) | Low — rollback requires table rebuild script | Check SQLite version before deploy: `sqlite3 --version` |
| INSERT fails because sl_type not in schema yet (deployment timing) | Low — migration runs before code deploy | High — all new INSERTs would fail | Migration order: 1) run DDL, 2) deploy code |
| sl_type column with `NOT NULL` breaks old schema paths | None — column has DEFAULT 'FIXED', no NOT NULL constraint | None | Design choice: allow DEFAULT so old code paths work without explicit set |
| Conditional keywords list mismatch between notes-tag and sl_type logic | Medium — if list is copied separately | Medium — misclassified sl_type | Use shared `_CONDITIONAL_SL_KEYWORDS` constant (§4d) |
| UPDATE path doesn't set MANUAL (code miss) | Low | Low — sl_type stays FIXED, analytically wrong but not blocking | `test_manual_sl_type_on_update` is MUST-PASS |

---

## 9. Evidence

**Files read:**
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (commit `69d6840a`) — lines 725–799: stop_loss processing, sl_note conditional detection, notes_parts assembly; lines 832–848: leverage handling pattern; lines 925–940: INSERT statement; lines 1003–1095: `_process_update()` and `_ALLOWED_UPDATE_COLS`

**Database queries run:**
```sql
-- Conditional SL count (current)
SELECT COUNT(*) FROM signals WHERE notes LIKE '%SL:CONDITIONAL%';
-- Result: 0

-- NULL stop_loss count
SELECT COUNT(*) FROM signals WHERE stop_loss IS NULL;
-- Result: 28

-- Schema check
PRAGMA table_info(signals);
-- No sl_type column confirmed
```

**Git commits reviewed:**
- `69d6840a` — micro-gate HEAD (A5 shipped)
