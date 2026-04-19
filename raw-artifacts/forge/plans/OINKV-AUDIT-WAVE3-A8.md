# OINKV-AUDIT-WAVE3-A8 — Conditional SL Type Field

**Plan:** `/home/oinkv/forge-workspace/plans/TASK-A8-plan.md` (v1.0, 328 lines)
**Tier:** 🟡 STANDARD
**Task:** A8 — Add `sl_type VARCHAR(15)` column + 4-way classification logic in micro-gate
**Audit Timestamp:** 2026-04-19 (Wave 3)
**Audit Method:** Hermes fallback (direct tool-driven code + schema inspection)

**Base commits verified:**
- micro-gate / oinkfarm canonical at `/home/oinkv/.openclaw/workspace/` HEAD = **`69d6840a`** ✅ matches plan header
- oink-sync at `/home/oinkv/oink-sync/` HEAD = `e9be741` (A4) — tests verified against this
- Production DB: `/home/oinkv/.openclaw/workspace/data/oinkfarm.db` → `/home/m/data/oinkfarm.db` (symlink), **493 rows** ✅

**⚠ Note on working tree drift:** `.openclaw/workspace` is currently on branch `anvil/A9-denomination-multiplier` with ~43 lines of uncommitted changes in `scripts/micro-gate-v3.py`. All audit line numbers below are verified against **committed HEAD** (`69d6840a`), which matches the plan. The working-tree-only offset is informational; ANVIL will implement A8 on a fresh branch from `69d6840a`.

---

## 🟢 CONFIRMED — Plan is accurate

### §1 Current State — line numbers match HEAD exactly

| Plan citation | HEAD (69d6840a) reality | Verdict |
|---|---|---|
| lines 725–746 (SL processing + CONDITIONAL tag) | Lines 725–746 exactly: `stop_loss = _safe_float(...)`, `sl_note = ...`, numeric regex extraction, `notes_parts.append(f"[SL:CONDITIONAL {sl_note}]")` | 🟢 |
| line 839 (`leverage = None` comment "2x-10x stays as None") | Line 839 literally: `leverage = None  # "2x-10x" stays as None in column; preserved in notes` | 🟢 |
| lines 925–940 (INSERT column list + VALUES) | Lines 922–940: `cur.execute("""INSERT OR IGNORE INTO signals (discord_message_id, channel_id, ..., fill_status, message_type, filled_at) VALUES (?, ?, ..., ?)"""` 28 columns, 28 placeholders | 🟢 |
| lines 1003–1095 (`_ALLOWED_UPDATE_COLS`) | Line 1003 is a blank line but line 1003–1004 in context holds `_ALLOWED_UPDATE_COLS = {"stop_loss", "take_profit_1", ... "leverage", "notes", "exit_price", "status", "fill_status"}` — plan's "line 1003" (§4b, "Add to line 1003") is ±1 off due to the blank vs assignment line but the set is unambiguously identified | 🟢 (trivially close) |
| `_process_update()` location | HEAD line 968: `def _process_update(entry, ext, conn, dry_run):` — matches plan's 1003–1095 span | 🟢 |

### §1 Current State — keyword list verified

Plan quotes the CONDITIONAL keyword tuple: `("close below", "close above", "4h", "1d", "daily", "weekly", "h2", "h4", "d1", "5m", "15m", "1h")`.
Verified at HEAD lines 743–745 — matches character-for-character. 🟢

### §1 Current DB state — counts match exactly

| Plan claim | sqlite3 result | Verdict |
|---|---|---|
| `COUNT(*) WHERE notes LIKE '%SL:CONDITIONAL%'` = 0 | **0** | 🟢 |
| `COUNT(*) WHERE stop_loss IS NULL` = 28 | **28** | 🟢 |
| No `sl_type` column exists | Confirmed — PRAGMA shows 50 columns, none named `sl_type` | 🟢 |
| Plan says "column index 50 would be next" | After `ALTER TABLE ADD COLUMN sl_type`, the new `cid` is exactly **50** | 🟢 |

### §2 Files to Modify — all paths exist

| File | Exists? | Notes |
|---|---|---|
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | ✅ | 65,645 bytes, 1475 lines at HEAD |
| `/home/oinkv/oink-sync/tests/test_lifecycle_events.py` | ✅ | 13,638 bytes; `_SIGNALS_SCHEMA` constant at line 32 (plan-cited) verified, current schema does NOT include `sl_type` so the proposed `sl_type TEXT DEFAULT 'FIXED'` addition is correctly required |
| `oinkfarm.db` (signals table) | ✅ | /home/oinkv/.openclaw/workspace/data/oinkfarm.db → /home/m/data/oinkfarm.db, 493 rows, 50 cols |

### §3 SQL Changes — fully validated in sandbox

Ran the exact plan migration + backfill on a copy of the production DB:

```
ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED';
-- PRAGMA table_info → (50, 'sl_type', 'VARCHAR(15)', 0, "'FIXED'", 0)   ✅ cid=50 as plan predicts
SELECT sl_type, COUNT(*) FROM signals GROUP BY sl_type;
-- FIXED|493    ✅ all 493 get DEFAULT

UPDATE signals SET sl_type='CONDITIONAL' WHERE notes LIKE '%SL:CONDITIONAL%' AND sl_type='FIXED';
-- changes()=0    ✅ matches plan "Expected rows affected: 0"

UPDATE signals SET sl_type='NONE' WHERE stop_loss IS NULL AND notes NOT LIKE '%SL:CONDITIONAL%' AND sl_type='FIXED';
-- changes()=28    ✅ matches plan "Expected rows affected: 28"

-- Final: FIXED|465, NONE|28    ✅ matches plan §3c "Expected: FIXED (465), NONE (28), CONDITIONAL (0), MANUAL (0)"
```

🟢 Every SQL claim is reproducible.

### §6 Acceptance Criteria — achievable with plan's steps

- **Schema**: verified `cid=50` post-ALTER. 🟢
- **No NULLs**: DEFAULT 'FIXED' guarantees this for existing + future rows. 🟢
- **SQLite version**: runtime is `3.46.1` — DROP COLUMN (≥3.35.0) works (verified in sandbox). 🟢
- **Rollback script**: `ALTER TABLE signals DROP COLUMN sl_type;` executed cleanly on copy. 🟢

### §7 Rollback Plan — safe on production SQLite version

SQLite 3.46.1 ≫ 3.35.0, so `ALTER TABLE DROP COLUMN` is available. Verified with round-trip on DB copy. 🟢

---

## 🟡 MINOR — Cosmetic / drift (non-blocking)

### MINOR-A8-1: Test location convention drift (§2, §5)

Plan §2 directs `oink-sync/tests/test_lifecycle_events.py` modification, and §5 creates **`signal-gateway/tests/test_sl_type.py`**.

Reality: Wave-3 micro-gate tests follow the pattern used by A5/A7 — they live in **`/home/oinkv/.openclaw/workspace/tests/`** (oinkfarm repo), not signal-gateway:
- `tests/test_a5_confidence.py` — imports `micro-gate-v3.py` via `Path(__file__).resolve().parents[1] / "scripts" / "micro-gate-v3.py"`
- `tests/test_a7_update_detection.py`
- `tests/test_micro_gate_filled_at.py`
- `tests/test_micro_gate_mutation_guard.py`
- `tests/test_event_store_a1.py` (Wave-3 A1)

`signal-gateway/tests/` contains gateway-layer tests (B14, discord, board-state) — micro-gate classification logic is NOT tested there historically. The plan's path is **inconsistent with A5/A7 precedent**.

**Recommendation:** ANVIL should place new tests at `/home/oinkv/.openclaw/workspace/tests/test_a8_sl_type.py` (following A5/A7 naming) or `test_micro_gate_sl_type.py`. Not blocking — pytest will pick up either location, but consistency helps maintenance.

### MINOR-A8-2: `_ALLOWED_UPDATE_COLS` line number off-by-one (§4b)

Plan §4b says: *"Add `\"sl_type\"` to `_ALLOWED_UPDATE_COLS` set (line 1003)."* HEAD line 1003 is actually a blank line; the set literal spans 1003→1004. This is a trivial off-by-one — the textual anchor `_ALLOWED_UPDATE_COLS = {"stop_loss", ...` is unique in the file so ANVIL will find it regardless.

### MINOR-A8-3: §4a insertion-point guidance ambiguous

Plan §4a says *"After the existing stop_loss and sl_note processing block (**after line 799** in current micro-gate), add: ..."* — but HEAD line 799 is inside the A15 NULL-clearing branch (`stop_loss = None`). Adding immediately after line 799 would drop the new block mid-A15 guard. The correct insertion point is *after* the `# ── 8c. A15: ...` block ends (HEAD line 800) and before `# ── 9. TP safety check ──` (HEAD line 801). The plan's intent is clear but literal "after line 799" is imprecise. ANVIL should interpret as "after Section 8c / before Section 9".

### MINOR-A8-4: Plan §4e misleads about test impact scope

Plan §4e states: *"oink-sync tests construct their own DB (`:memory:`) with their own schema and do not run micro-gate INSERT statements — they insert signals directly with known values. Therefore **oink-sync tests are NOT affected**."*

This is correct — verified that `_SIGNALS_SCHEMA` in `test_lifecycle_events.py` and `test_partially_closed.py` are independent hand-rolled schemas with their own `_insert_signal(conn, **overrides)` helpers. No micro-gate INSERT path is exercised.

However, §2 still lists `test_lifecycle_events.py` as MODIFY target (for "forward compatibility"). This is voluntary belt-and-suspenders — **not required for the plan to succeed**. Recommend marking this as OPTIONAL in §2 to reduce ambiguity; otherwise ANVIL might think it's a mandatory test-breaking dependency.

### MINOR-A8-5: Risk matrix row about INSERT failure overstates severity

§8 Risk: *"INSERT fails because sl_type not in schema yet (deployment timing) — Low probability, High impact"*. With `DEFAULT 'FIXED'` applied in the ALTER, even if ANVIL forgets to add `sl_type` to the INSERT column list the INSERT still succeeds and `sl_type` gets 'FIXED' via DEFAULT. So the impact is actually **Medium** (MANUAL/CONDITIONAL/NONE misclassified as FIXED at insert time, not "all INSERTs fail"). Cosmetic; does not change mitigation.

---

## 🔴 CRITICAL — Blocks implementation

**None.** The plan is unusually clean:

- Canonical repo path (`/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py`) correctly identified — plan does NOT repeat the Wave-1 kraken-sync-vs-oink-sync error because A8 touches micro-gate (INSERT path), which is unambiguously oinkfarm-located.
- Base commit (`69d6840a`) matches HEAD in the canonical repo.
- All DB numbers reproduce exactly.
- All code line numbers verified against committed HEAD.
- Schema change is additive, DEFAULT-safe, non-destructive, SQLite-compatible.
- Rollback path validated end-to-end on a DB copy.
- No cross-repo import hazards (unlike Wave-1 A1's event_store crisis).
- No dead-code target issues (unlike Wave-1 A1/A2).

---

## Cross-Reference with OINKV-AUDIT.md (Wave 1)

Wave 1 flagged two classes of showstopper that **do not apply** to A8:

1. **"Plans target dead code (kraken-sync)"** — A8 touches `micro-gate-v3.py`, which is live and running. ✅ Not affected.
2. **"Cross-repo event_store dependency"** — A8 does **not** emit events (plan §0 explicitly states *"No dedicated event is emitted for sl_type changes"*). ✅ Not affected.

Wave 1 also credited FORGE for *"micro-gate-v3.py analysis: INSERT statement, column list, line numbers — all verified correct"*. A8 continues that track record: the INSERT-path analysis in §1 and §2 is again fully accurate against the current codebase.

One adjacent Wave-1 item worth noting (not a blocker for A8):
- Wave 1 DRIFT-A1-3 discussion of `.openclaw/workspace` being the live location is consistent with A8's targeting. 🟢

---

## Overall Verdict

## **READY-WITH-MINOR-EDITS**

The plan is technically sound, line-accurate against committed HEAD (`69d6840a`), schema-correct, and SQL-validated end-to-end on a copy of the production DB. All four canonical sl_type values (FIXED/CONDITIONAL/MANUAL/NONE), the detection logic, the backfill counts (465 FIXED + 28 NONE + 0 CONDITIONAL + 0 MANUAL = 493), and the rollback strategy are all reproducible.

Recommended pre-implementation edits (all MINOR):
1. Move new test file to `.openclaw/workspace/tests/test_a8_sl_type.py` (A5/A7 convention) — MINOR-A8-1.
2. Correct §4a insertion anchor from "after line 799" to "after Section 8c (A15 guard) / before Section 9 (TP safety check)" — MINOR-A8-3.
3. Mark §2 row for `test_lifecycle_events.py` as OPTIONAL — MINOR-A8-4.
4. Clarify §4b line anchor to refer to `_ALLOWED_UPDATE_COLS` literal, not "line 1003" — MINOR-A8-2.
5. (Optional) Revise §8 risk row about INSERT failure — DEFAULT makes this Medium-impact, not High — MINOR-A8-5.

None of these block ANVIL from starting implementation. A8 can proceed immediately if FORGE incorporates the test-location correction before ANVIL is dispatched; the other four items are cosmetic polish.

---

## Evidence Log

**Files read (HEAD `69d6840a`, committed):**
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` lines 720–810, 830–845, 910–990, 990–1110
- `/home/oinkv/oink-sync/tests/test_lifecycle_events.py` lines 25–95
- `/home/oinkv/oink-sync/tests/test_partially_closed.py` (schema confirm)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT.md` (Wave 1 cross-ref)

**Database queries (against `/home/oinkv/.openclaw/workspace/data/oinkfarm.db`):**
```sql
SELECT COUNT(*) FROM signals;                                       -- 493
SELECT COUNT(*) FROM signals WHERE notes LIKE '%SL:CONDITIONAL%';   -- 0
SELECT COUNT(*) FROM signals WHERE stop_loss IS NULL;               -- 28
PRAGMA table_info(signals);                                         -- 50 cols, no sl_type
```

**Sandbox migration round-trip (on DB copy):**
```sql
ALTER TABLE signals ADD COLUMN sl_type VARCHAR(15) DEFAULT 'FIXED'; -- OK, cid=50
-- FIXED|493 after DEFAULT
UPDATE signals SET sl_type='CONDITIONAL' WHERE notes LIKE '%SL:CONDITIONAL%' AND sl_type='FIXED';  -- 0 rows
UPDATE signals SET sl_type='NONE' WHERE stop_loss IS NULL AND notes NOT LIKE '%SL:CONDITIONAL%' AND sl_type='FIXED';  -- 28 rows
-- Final: FIXED|465, NONE|28 (exact plan match)
ALTER TABLE signals DROP COLUMN sl_type;                            -- rollback OK
```

**SQLite version:** `3.46.1 2024-08-13` (supports DROP COLUMN natively).

**Git state:**
- oinkfarm repo HEAD: `69d6840a feat(A5): parser-type confidence scoring via PARSER_CONFIDENCE_MAP (#131)` — matches plan header
- oink-sync repo HEAD: `e9be741 A4: PARTIALLY_CLOSED status for partial TP signals (#7)`

**Related tests confirming A5/A7 convention:**
- `/home/oinkv/.openclaw/workspace/tests/test_a5_confidence.py`
- `/home/oinkv/.openclaw/workspace/tests/test_a7_update_detection.py`
- `/home/oinkv/.openclaw/workspace/tests/test_event_store_a1.py` (Wave-3 A1)
