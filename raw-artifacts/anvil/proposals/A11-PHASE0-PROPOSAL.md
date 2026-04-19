# A11 Phase 0 Proposal — Leverage Source Tracking

**Task:** A11 — Leverage Source Tracking  
**Tier:** 🟢 LIGHTWEIGHT  
**Target:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (canonical oinkfarm copy)  
**Spec:** FORGE plan at `/home/oinkv/forge-workspace/plans/TASK-A11-plan.md`  
**OinkV Audit:** `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A11.md` — 🟢 READY-WITH-MINOR-EDITS  
**Date:** 2026-04-19

---

## Problem

395 of 493 signals (80.1%) have `leverage = NULL`. When leverage IS present (98 signals), there's no record of whether the trader stated it explicitly or whether it was inferred/hallucinated by the LLM. Per the FORGE plan, the correct approach is to track provenance rather than manufacture defaults — NULL is informationally correct.

## Approach

Add a `leverage_source VARCHAR(20) DEFAULT NULL` column to signals. At INSERT time in `_process_signal()` (after the existing leverage normalization block at line 874–882), set `leverage_source = 'EXPLICIT'` when the extraction payload provides a leverage value, or leave NULL otherwise. This is a 2-value implementation today (`EXPLICIT` / `NULL`); `EXTRACTED` and `DEFAULT` are reserved for future enhancements per FORGE §4a.

**Schema change:**
```sql
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
```

**Backfill** (one-shot, 98 rows):
```sql
UPDATE signals SET leverage_source = 'EXPLICIT' WHERE leverage IS NOT NULL;
```

This is correct because all 98 non-NULL leverage values in production today came from extractor-supplied payloads.

**INSERT modification** (line 966–988): Add `leverage_source` column + binding (29 columns → 29 placeholders).

## Key Decisions

1. **Only EXPLICIT or NULL today** — no EXTRACTED/DEFAULT until future tasks add those code paths.
2. **Canonical file only** — edits to `.openclaw/workspace/scripts/micro-gate-v3.py` (oinkfarm repo). The `signal-gateway/scripts/micro-gate-v3.py` is a divergent legacy mirror and will NOT be modified (per OinkV §6).
3. **No event logging** — leverage_source is INSERT-time metadata, not a lifecycle event.
4. **Forward-compatible** — VARCHAR(20) accommodates all 4 planned enum values.
5. **Deploy via cp + restart** — same pattern as A5/A9.

## Test Strategy

5 tests in `tests/test_a11_leverage_source.py`:
- MUST: explicit numeric leverage → EXPLICIT
- MUST: no leverage → NULL
- MUST: string "10x" leverage → EXPLICIT (parse succeeds)
- MUST: unparseable "5x-10x" → NULL (parse fails, leverage=NULL → source=NULL)
- SHOULD: backfill correctness (98 rows get EXPLICIT, 395 stay NULL)

## Rollback

```sql
ALTER TABLE signals DROP COLUMN leverage_source;
```
SQLite ≥3.35 supports this natively. No data loss — leverage column is untouched.

## Acceptance Criteria

1. New signals with explicit leverage → `leverage_source = 'EXPLICIT'`
2. New signals without leverage → `leverage_source = NULL`
3. Backfill sets 98 existing non-NULL leverage signals to `'EXPLICIT'`
4. No regression in leverage parsing or existing tests
5. INSERT column count = 29 (was 28)
