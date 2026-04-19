# Wave 3 Plan Summary — A6/A8/A9/A10/A11

**Author:** FORGE 🔥  
**Date:** 2026-04-19  
**Status:** Ready for Mike approval  
**Base commits:** oink-sync `ab5d941`, micro-gate `69d6840a`, signal-gateway `38eb8e8`

---

## Recommended Execution Order

| Order | Task | Name | Tier | Est. Effort | Rationale |
|-------|------|------|------|-------------|-----------|
| 1a | **A9** | Denomination multiplier | 🟢 LIGHTWEIGHT | 0.5 day | Independent, small scope, fixes 1 known bad signal |
| 1b | **A11** | Leverage source tracking | 🟢 LIGHTWEIGHT | 0.5 day | Independent, can ship in parallel with A9 |
| 2a | **A8** | Conditional SL type | 🟡 STANDARD | 0.5 day | Independent, new column + logic |
| 2b | **A6** | Ghost closure flag | 🟡 STANDARD | 0.5 day | Depends on A1 (shipped), can parallel with A8 |
| 3 | **A10** | DB merge | 🔴 CRITICAL | 1-2 days | **Mike approval required.** Depends on all other tasks completing first so the merge captures the latest schema. |

**Total estimated effort:** 3-4 days

### Why This Order

- **A9 + A11 first:** Both are lightweight, independent, and can ship in parallel. Quick wins.
- **A8 + A6 second:** Both are standard tier. A8 adds a new column; A6 instruments ghost closures. Neither depends on the other.
- **A10 last:** The DB merge should happen AFTER all schema changes (A8's `sl_type`, A11's `leverage_source`) are in production, so the merge script accounts for the final schema shape. Also needs Mike's explicit approval.

---

## Dependency Graph

```
A1 (shipped) ──► A6 (ghost closure events use event_store)
                  
A9 ─────────────────────────────────────────────┐
A11 ────────────────────────────────────────────┤
A8 ─────────────────────────────────────────────┤
A6 ─────────────────────────────────────────────┤
                                                 ▼
                                          A10 (DB merge)
                                          [Mike approval gate]
```

A10 should be last because it captures the final schema state.

---

## Plan Files

| File | Lines | Size | Key Changes |
|------|-------|------|-------------|
| TASK-A6-plan.md | ~340 | 17KB | Ghost closure event instrumentation in signal_router.py |
| TASK-A8-plan.md | ~310 | 15KB | `sl_type` column + classification logic in micro-gate |
| TASK-A9-plan.md | ~180 | 8KB | `DENOMINATION_MULTIPLIERS` dict in resolver.py |
| TASK-A10-plan.md | ~260 | 12KB | Merge script + validation + Mike approval gates |
| TASK-A11-plan.md | ~170 | 7KB | `leverage_source` column + source tracking |

---

## FORGE Design Decisions

### A11: No Leverage Defaults
FORGE argues AGAINST defaulting leverage. 80.1% of signals have NULL leverage because the trader didn't specify it. Defaulting to any number manufactures false precision. Instead, A11 adds `leverage_source` tracking (`EXPLICIT` vs `NULL`) so analytics can filter by provenance. Mike can add defaults later via the `DEFAULT` source value.

### A6: No ghost_confirmed Column
The `close_source` field already exists on signals. When a ghost closure occurs, `close_source='board_absent'` is set. Combined with the `GHOST_CLOSURE` event in signal_events, this provides full audit trail without a redundant boolean column.

### A9: Normalize at Comparison Time, Not INSERT Time
Entry prices should be stored as extracted (raw denomination) because that's what the trader sees. The 1000x multiplier is applied only during PnL/SL/TP calculations in lifecycle.py. This preserves the original signal data.

### A10: New DB Wins for Overlaps
When both DBs have a signal with the same discord_message_id, the new DB version is kept. Rationale: the new DB has had A1/A2/A3/A4/A5/A7 improvements applied; old DB versions lack event instrumentation, remaining_pct, etc.

---

## Mike Approval Flags

| Flag | Task | Decision Needed |
|------|------|----------------|
| **A10-APPROVE** | A10 | 🔴 Must approve merge algorithm + dedup strategy before ANVIL begins |
| **A10-DEPLOY** | A10 | 🔴 Must approve validation report before production deployment |
| Q-A10-1 | A10 | Merge price_history? FORGE recommends defer |
| Q-A10-2 | A10 | Merge audit_log? FORGE recommends skip |
| Q-A10-3 | A10 | Schedule merge during quiet window? |
| A11-DECISION | A11 | FORGE chose leverage_source tracking over defaults. Mike can override. |

---

## A2 Follow-Up Status

Provider-alert close_pct extraction (flagged in A2, recommended as A12) remains deferred. Not blocking Wave 3. Can be planned after Phase A completes.

---

*Forge 🔥 — "Lightweight tasks first, CRITICAL last. A10 needs Mike's eyes before ANVIL touches production data."*
