# A1-A3 Technical Execution Plan Summary

## ⚠️ POST-AUDIT REVISIONS

**Date:** 2026-04-19
**Auditor:** OinkV 👁️🐷

This summary has been revised after OinkV code audit (see `OINKV-AUDIT.md`). Key changes:

- **Dead-code showstopper resolved:** All three plans were redirected from `scripts/kraken-sync.py` (inactive since 2026-04-07) to the live engine at `oink-sync/oink_sync/lifecycle.py` (`LifecycleManager` class).
- **Cross-repo dependency decision added:** `event_store.py` lives in oinkfarm; `lifecycle.py` lives in the standalone `oink-sync` repo. RECOMMENDED PATH = vendor `event_store.py` into oink-sync as `oink_sync/event_store.py` (see Critical Audit Resolution below).
- **Signature mismatch flagged:** A2's `calculate_blended_pnl()` rewrite targets the oink-sync signature (booleans for TP hits, no leverage param).

---

**Prepared by:** 🔥 FORGE
**Date:** 2026-04-19
**Codebase Verified At:** `521d4411` (2026-04-18)

---

## ⚠️ CRITICAL AUDIT RESOLUTION

OinkV's audit (see `OINKV-AUDIT.md`) uncovered three blocking problems that are resolved here so ANVIL can proceed.

### 1. 🔴 Dead-Code Showstopper: kraken-sync → oink-sync

**Problem:** All three plans (and most of this summary's original file-divergence table) pointed at `scripts/kraken-sync.py` (1,840 LOC) as the "main lifecycle engine." That service has been **INACTIVE since 2026-04-07** (`DISABLE_KRAKEN_SYNC=1`). It does not run. Instrumenting it does nothing.

**Reality:** The active lifecycle engine is the standalone `oink-sync` package:
- Path: `/home/oinkv/oink-sync/oink_sync/lifecycle.py` (811 LOC)
- Class: `LifecycleManager` (methods, not module-level functions)
- Price engine: `/home/oinkv/oink-sync/oink_sync/engine.py` (548 LOC)
- Service: `oink-sync.service` (user-level, port 8889, confirmed `active`)
- Restart: `systemctl --user restart oink-sync` (no sudo)

**Resolution:** All three plan files have had every kraken-sync reference redirected to `oink_sync/lifecycle.py`, with method-on-class signatures (`LifecycleManager._check_sl_tp`, `_check_limit_fills`, `_expire_stale_limits`, `_check_sl_proximity`, `_process_tp_hits`) and corrected line numbers.

### 2. 🔴 Cross-Repo event_store Dependency — RESOLVED

**Problem:** `event_store.py` lives in the **oinkfarm** repo (`/home/oinkv/.openclaw/workspace/scripts/event_store.py`) but `lifecycle.py` lives in the **oink-sync** standalone repo. These are different repos with different Python environments; `from event_store import EventStore` does not resolve from inside oink-sync.

**Decision — RECOMMENDED PATH: vendor `event_store.py` into oink-sync as `oink_sync/event_store.py`.**

- Copy `scripts/event_store.py` into the oink-sync repo at `oink_sync/event_store.py` (keep the same schema, same public API — `EventStore`, `log()`, `ensure_schema()`, `LIFECYCLE_EVENTS`, `QUARANTINE_CODES`).
- `oink_sync/lifecycle.py` imports `from oink_sync.event_store import EventStore` — single import path, single Python env.
- The oinkfarm-side `scripts/event_store.py` **remains in place** — `scripts/micro-gate-v3.py` still imports it and still needs it.
- Both copies write to the same signal_events table via their respective `sqlite3.Connection` → schema is shared in the DB, not via a shared package.

**Rationale:**
- **Single source of truth in oink-sync** for the live lifecycle engine.
- **No shared-package complexity** (no pip-installable namespace package, no path hacks).
- **ANVIL writes exactly one import path** for the oink-sync side.
- If the two files ever diverge in behavior, GUARDIAN's canary will catch it because they write to the same table.

Rejected alternatives:
- *Shared installable package:* over-engineered for a 209-LOC file.
- *Raw SQL inserts from lifecycle.py:* loses `ensure_schema()` idempotent migration and quarantine helpers — regression risk.
- *Move event_store to oink-sync and have micro-gate reach in:* breaks oinkfarm's single-repo deployment model.

### 3. 🟡 calculate_blended_pnl() Signature Mismatch

**Problem:** The oink-sync version of `calculate_blended_pnl()` differs from the kraken-sync version:
- **No `leverage` parameter** (removed in the port — Mike's leverage-free zone rule enforced at the type level).
- **`tp*_hit` params are booleans** (truthy/falsy), not timestamp strings like `tp1_hit_at`.

**Resolution:** A2 plan rewrites the oink-sync version with its actual signature:
```python
def calculate_blended_pnl(
    entry: float, exit_price: float, direction: str,
    tp1, tp2, tp3,
    tp1_hit, tp2_hit, tp3_hit,   # booleans, not timestamps
) -> float:
```

The leverage-free zone rule applies regardless — do not re-introduce a leverage parameter during the rewrite. The `remaining_pct` decrement must live in `LifecycleManager._process_tp_hits()` (line ~358), not `_check_sl_tp()`.

---

## Dependency Graph

```
A1: signal_events schema extension + oink-sync lifecycle instrumentation
    │   🔴 CRITICAL | 1-2 days
    │   Extends existing event_store.py (GH#22)
    │   Instruments oink_sync/lifecycle.py (0 events currently!)
    │
    ├───► A2: remaining_pct model + blended PnL fix
    │         🔴 CRITICAL | 2-3 days
    │         Depends on A1 (TP_HIT events with close_pct)
    │         Rewrites calculate_blended_pnl() in oink_sync/lifecycle.py
    │
    └───► (A4, A6 depend on A1 — not yet planned)

A3: Auto filled_at for MARKET orders
        🟡 STANDARD | 0.5 days
        INDEPENDENT — no dependencies
        Can be executed in parallel with A1
```

**Recommended execution order:**
1. **A3** first — quick win (0.5 days), independent, improves data quality immediately
2. **A1** second — foundation task, enables A2/A4/A6
3. **A2** third — depends on A1 being complete

---

## Critical Discovery: Codebase Diverges from Arbiter-Oink Report

The Arbiter-Oink report references several files that **do not exist** in the current codebase:

| Report Reference | Actual File | Status |
|-----------------|-------------|--------|
| `lifecycle.py` | `oink-sync/oink_sync/lifecycle.py` | **Exists as named** in the oink-sync standalone package (ported from kraken-sync.py on 2026-04-07) |
| `engine.py` | `oink-sync/oink_sync/engine.py` | **Exists as named** in the oink-sync standalone package (price polling + DB writes) |
| `signal_router.py` (4,366 LOC God Object) | **Does not exist** | The God Object may have been refactored/removed before FORGE's analysis window |
| `reconciler` (separate file) | Logic embedded in `micro-gate-v3.py` `_process_closure()` + `api/signals_by_route.py` | **No standalone reconciler file** |
| `event_log.py` | `scripts/event_store.py` | **Different name** |

**Impact:** All three plans use verified actual file paths, not report-referenced paths. ANVIL should use the paths in the plans, not the Arbiter-Oink report.

---

## Critical Discovery: 0 Events in Production

The `signal_events` table exists (created by GH#22, commit `387a8a4d`) but contains **0 rows**. micro-gate-v3.py has instrumentation for `SIGNAL_CREATED`, `SL_MODIFIED`, `ORDER_FILLED`, and closure events, but nothing is being logged.

**Likely cause:** Production service may be running older code (pre-GH#22 deploy), or the EventStore import fails silently on production.

**Action required (ANVIL):** Before implementing A1 extensions:
1. Verify production is running commit `387a8a4d` or later
2. Verify `event_store.py` is importable from the production scripts directory
3. If events should already be logging, diagnose why they aren't

---

## Risk Flags

### 🔴 HIGH RISK: PnL Regression (A2)

Rewriting `calculate_blended_pnl()` affects every future trade closure. A bug here means incorrect ROI for all new closures.

**Mitigation:** 11 test vectors including FET #1159 reference case. Feature branch with thorough testing before merge.

### 🟡 MEDIUM RISK: Zero-Event Mystery (A1)

The event store infrastructure exists but isn't producing events. If the root cause is a deployment issue, A1's instrumentation of kraken-sync.py will also fail silently.

**Mitigation:** ANVIL must diagnose and fix the zero-event problem before or during A1 implementation.

### 🟢 LOW RISK: INSERT Parameter Count (A3)

Adding `filled_at` to the INSERT statement changes from 27 to 28 parameters. A miscount causes all INSERTs to fail.

**Mitigation:** Explicit dry-run test before deployment.

---

## Design Questions Requiring Mike's Resolution

### DQ-A1-1: Schema Extension Approach
Add `field`, `old_value`, `new_value`, `source_msg_id` columns to signal_events (Phase 4 spec) vs keep current minimal schema?
**FORGE recommends:** Add columns (zero-cost on empty table, enables structured queries).

### DQ-A1-2: Reconciler Event Source
Where should GHOST_CLOSURE events be emitted from? No standalone reconciler.py exists — reconciliation flows through micro-gate's closure processing.

### DQ-A2-1: Retroactive PnL Recalculation
Should existing closed signals' `final_roi` be recalculated with corrected close percentages?
**FORGE recommends:** No. Only new closures use improved calculation.

### DQ-A2-2: Per-Provider Close Percentages
Should we configure per-provider TP close splits (50/25/25 for WG, 33/33/34 for others)?
**FORGE recommends:** Start with current hard-coded fallback. Add per-provider config later based on audit data.

### DQ-A3-1: fill_price for MARKET Orders
Should A3 also set `fill_price = entry_price` for MARKET orders?
**FORGE recommends:** Keep A3 focused on `filled_at` only. Trivial follow-up if desired.

---

## Plan Artifacts

| Artifact | Path | Size |
|----------|------|------|
| A1 Technical Execution Plan | `/home/oinkv/forge-workspace/plans/TASK-A1-plan.md` | ~20KB |
| A2 Technical Execution Plan | `/home/oinkv/forge-workspace/plans/TASK-A2-plan.md` | ~18KB |
| A3 Technical Execution Plan | `/home/oinkv/forge-workspace/plans/TASK-A3-plan.md` | ~12KB |
| This Summary | `/home/oinkv/forge-workspace/plans/A1-A3-SUMMARY.md` | — |

---

## Next Plans

After Mike approves A1-A3, FORGE will produce plans for:
- **A7** (UPDATE→NEW detection) — 🔴 CRITICAL, independent
- **A5** (Confidence scoring) — 🟡 STANDARD, independent
- **A4** (PARTIALLY_CLOSED status) — 🟡 STANDARD, depends on A2
