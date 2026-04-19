# OinkV Engineering Audit — FORGE Plans A1/A2/A3

**Auditor:** OinkV 👁️🐷 (current code authority)
**Date:** 2026-04-19
**Scope:** Staleness, architectural drift, missing integrations, merge diffs
**Verdict:** All 3 plans have a **CRITICAL** misidentification of the lifecycle engine. A3 is least affected.

---

## ⛔ SHOWSTOPPER: Plans Target Dead Code

All 3 plans reference `scripts/kraken-sync.py` (1,840 LOC) as the "main lifecycle engine."

**Reality:**
- `kraken-sync` service has been **INACTIVE since 2026-04-07** (`DISABLE_KRAKEN_SYNC=1`)
- The active lifecycle engine is **`oink-sync`** — a standalone Python package at `/home/oinkv/oink-sync/`
- Service: `oink-sync.service` (user-level), port 8889, confirmed `active`
- Lifecycle code: `/home/oinkv/oink-sync/oink_sync/lifecycle.py` (811 LOC) — `LifecycleManager` class
- Price engine: `/home/oinkv/oink-sync/oink_sync/engine.py` (548 LOC) — `PriceEngine` class
- `scripts/kraken-sync.py` is legacy code preserved for rollback. It does not run. Instrumenting it does nothing.

**This affects every plan.** All function references, line numbers, import patterns, and rollback procedures that mention kraken-sync must be redirected to oink-sync.

### Architectural Differences (kraken-sync → oink-sync)

| Aspect | kraken-sync (dead) | oink-sync (live) |
|--------|-------------------|------------------|
| Architecture | Module-level functions | `LifecycleManager` class with methods |
| `check_sl_tp()` | `check_sl_tp(conn, prices)` at line ~540 | `LifecycleManager._check_sl_tp(conn, prices)` at line ~259 |
| `check_limit_fills()` | `check_limit_fills(conn, prices)` at line ~712 | `LifecycleManager._check_limit_fills(conn, prices)` at line ~428 |
| `expire_stale_limits()` | `expire_stale_limits(conn, prices)` at line ~790 | `LifecycleManager._expire_stale_limits(conn, prices)` at line ~475 |
| `check_active_sl_proximity()` | at line ~873 | `LifecycleManager._check_sl_proximity(conn, prices)` at line ~550 |
| `calculate_blended_pnl()` | `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit_at, tp2_hit_at, tp3_hit_at, leverage=None)` | `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit)` — **no leverage param, booleans not timestamps** |
| TP hit handling | Inline in `check_sl_tp()` | Separate method `_process_tp_hits()` at line ~358 |
| EventStore | None | None (same gap — needs adding) |
| Repo | `/home/oinkv/.openclaw/workspace/scripts/` (oinkfarm) | `/home/oinkv/oink-sync/` (standalone package) |
| Service restart | ~~`sudo systemctl restart kraken-sync`~~ | `systemctl --user restart oink-sync` |

### Cross-Repo Dependency (NEW — plans don't address this)

`event_store.py` lives in the **oinkfarm** repo (`/home/oinkv/.openclaw/workspace/scripts/event_store.py`).
`lifecycle.py` lives in the **oink-sync** repo (`/home/oinkv/oink-sync/oink_sync/lifecycle.py`).

These are **different repos with different Python environments**. You can't just `from event_store import EventStore` in oink-sync — the import path doesn't exist. Options:
1. Copy `event_store.py` into oink-sync as a vendored module
2. Make event_store a shared package installable by both
3. Have oink-sync do raw SQLite inserts into signal_events without the EventStore class
4. Move event_store.py into oink-sync and have micro-gate import from there

**ANVIL must resolve this before A1 implementation.**

---

## Plan A1: signal_events + Instrumentation

### Issues Found: 8 stale references, 3 architectural drifts, 1 missing integration

#### STALE-A1-1: All kraken-sync.py file references (CRITICAL)

Every reference to `scripts/kraken-sync.py` must become `oink_sync/lifecycle.py` (in the oink-sync repo).

```
FILE: TASK-A1-plan.md
ORIGINAL:
| kraken-sync.py | scripts/kraken-sync.py | 1,840 | Main lifecycle engine — needs full event instrumentation |

REPLACEMENT:
| lifecycle.py | oink-sync repo: oink_sync/lifecycle.py | 811 | Main lifecycle engine (LifecycleManager class) — needs full event instrumentation |

RATIONALE:
kraken-sync.py is inactive since 2026-04-07. oink-sync/oink_sync/lifecycle.py is the live lifecycle engine.
```

#### STALE-A1-2: Function names and line numbers in §1 "Key Functions" table

```
FILE: TASK-A1-plan.md
ORIGINAL:
| `check_sl_tp()` | kraken-sync.py (line ~540) | Detects SL/TP hits, trails SL, closes trades | TP_HIT, SL_UPDATED (trail), TRADE_CLOSED_SL/TP/BE |
| `check_limit_fills()` | kraken-sync.py (line ~712) | Detects PENDING→ACTIVE transitions | LIMIT_FILLED (ORDER_FILLED) |
| `expire_stale_limits()` | kraken-sync.py (line ~790) | Auto-cancels stale limits | LIMIT_EXPIRED |
| `check_active_sl_proximity()` | kraken-sync.py (line ~873) | Near-SL/TP price alerts | PRICE_ALERT |

REPLACEMENT:
| `LifecycleManager._check_sl_tp()` | oink_sync/lifecycle.py (line ~259) | Detects SL/TP hits, trails SL, closes trades | TP_HIT, SL_UPDATED (trail), TRADE_CLOSED_SL/TP/BE |
| `LifecycleManager._check_limit_fills()` | oink_sync/lifecycle.py (line ~428) | Detects PENDING→ACTIVE transitions | LIMIT_FILLED (ORDER_FILLED) |
| `LifecycleManager._expire_stale_limits()` | oink_sync/lifecycle.py (line ~475) | Auto-cancels stale limits | LIMIT_EXPIRED |
| `LifecycleManager._check_sl_proximity()` | oink_sync/lifecycle.py (line ~550) | Near-SL/TP price alerts | PRICE_ALERT |

RATIONALE:
Functions are methods on LifecycleManager class in oink-sync, not module-level functions. Line numbers differ.
```

#### STALE-A1-3: Files to Modify table — kraken-sync entries

```
FILE: TASK-A1-plan.md
ORIGINAL:
| scripts/kraken-sync.py | top-level imports | MODIFY | Add `from event_store import EventStore` import with graceful fallback |
| scripts/kraken-sync.py | `get_db()` | MODIFY | Initialize EventStore on DB connection |
| scripts/kraken-sync.py | `check_sl_tp()` | MODIFY | Emit TP_HIT, SL_UPDATED (trail), TRADE_CLOSED events |
| scripts/kraken-sync.py | `check_limit_fills()` | MODIFY | Emit ORDER_FILLED events |
| scripts/kraken-sync.py | `expire_stale_limits()` | MODIFY | Emit LIMIT_EXPIRED events |
| scripts/kraken-sync.py | `check_active_sl_proximity()` | MODIFY | Emit PRICE_ALERT events |
...
| tests/test_kraken_sync_events.py | — | CREATE | Unit tests for kraken-sync event emission |

REPLACEMENT:
| oink_sync/lifecycle.py | LifecycleManager.__init__() | MODIFY | Initialize EventStore on construction (or lazy-init pattern) |
| oink_sync/lifecycle.py | LifecycleManager._check_sl_tp() | MODIFY | Emit TP_HIT, SL_UPDATED (trail), TRADE_CLOSED events |
| oink_sync/lifecycle.py | LifecycleManager._check_limit_fills() | MODIFY | Emit ORDER_FILLED events |
| oink_sync/lifecycle.py | LifecycleManager._expire_stale_limits() | MODIFY | Emit LIMIT_EXPIRED events |
| oink_sync/lifecycle.py | LifecycleManager._check_sl_proximity() | MODIFY | Emit PRICE_ALERT events |
| oink-sync repo: event_store integration | — | CREATE or VENDOR | event_store.py must be made importable from oink-sync (see cross-repo note above) |
...
| oink-sync/tests/test_lifecycle_events.py | — | CREATE | Unit tests for lifecycle event emission |

RATIONALE:
oink-sync is a separate repo/package. No `get_db()` exists — LifecycleManager receives `conn` via `run_cycle()`. Import path for event_store.py needs solving.
```

#### STALE-A1-4: Integration pattern in §4b

The module-level singleton pattern doesn't fit oink-sync's class architecture.

```
FILE: TASK-A1-plan.md
ORIGINAL:
# At module level (same pattern as micro-gate-v3.py):
try:
    from event_store import EventStore
    _EVENT_STORE_AVAILABLE = True
except ImportError:
    _EVENT_STORE_AVAILABLE = False
    EventStore = None

_event_store = None

def _get_event_store(conn):
    global _event_store
    if not _EVENT_STORE_AVAILABLE:
        return None
    if _event_store is None or _event_store.conn is not conn:
        try:
            _event_store = EventStore(conn)
            _event_store.ensure_schema()
        except Exception:
            return None
    return _event_store

def _log_event(conn, event_type, signal_id, payload=None, source="kraken-sync"):
    try:
        es = _get_event_store(conn)
        if es:
            es.log(event_type, signal_id, payload, source)
    except Exception:
        pass  # Non-fatal

REPLACEMENT:
# In LifecycleManager.__init__() or as a lazy property:
# EventStore must be vendored or installed in oink-sync's Python environment
# (it lives in oinkfarm repo — cross-repo dependency, see audit note)
#
# Option A — vendor event_store.py into oink-sync:
#   Copy scripts/event_store.py → oink_sync/event_store.py
#
# Option B — raw SQL inserts (no EventStore class dependency):
#   Write directly to signal_events table from lifecycle.py
#
# Integration pattern (class-based, not module-level):
class LifecycleManager:
    def __init__(self, cfg=None):
        self.cfg = cfg or LifecycleConfig()
        self._event_store = None  # lazy-init on first run_cycle

    def _get_event_store(self, conn):
        if self._event_store is None or self._event_store.conn is not conn:
            try:
                self._event_store = EventStore(conn)
                self._event_store.ensure_schema()
            except Exception:
                self._event_store = None
        return self._event_store

    def _log_event(self, conn, event_type, signal_id, payload=None):
        try:
            es = self._get_event_store(conn)
            if es:
                es.log(event_type, signal_id, payload, source="oink-sync")
        except Exception:
            pass  # Non-fatal

RATIONALE:
oink-sync uses class-based architecture. Module-level globals don't fit. Source should be "oink-sync" not "kraken-sync".
```

#### STALE-A1-5: §4c Event emission point line references

```
FILE: TASK-A1-plan.md
ORIGINAL:
The `check_sl_tp()` function (line ~540) has two main paths:

**TP Hit Path** (partial close — trails SL, does NOT close trade):
...
- Located at approximately line ~630-650 (the `conn.execute(f"UPDATE signals SET {hit_col}=?..."` block)

**Closure Path** (SL hit — closes trade with blended PnL):
...
- Located at approximately line ~660-710 (the `conn.execute("UPDATE signals SET status=?..."` block)

REPLACEMENT:
The `LifecycleManager._check_sl_tp()` method (line ~259) delegates TP handling to `_process_tp_hits()` (line ~358):

**TP Hit Path** (partial close — trails SL, does NOT close trade):
- Handled in `_process_tp_hits()` at line ~358-425
- The `conn.execute(f"UPDATE signals SET {hit_col}=?..."` is at approximately line ~406

**Closure Path** (SL hit — closes trade with blended PnL):
- Handled inline in `_check_sl_tp()` at approximately line ~318-354
- The `conn.execute("UPDATE signals SET status=?..."` is at approximately line ~328

RATIONALE:
Line numbers and method structure differ. TP hits are in a separate method in oink-sync.
```

#### STALE-A1-6: Reconciler location claim is WRONG

```
FILE: TASK-A1-plan.md
ORIGINAL:
**Question for Mike:** Should GHOST_CLOSURE events be emitted from within micro-gate's `_process_closure()` path when the closure source is reconciler-originated? Or is there a separate reconciler process that FORGE hasn't located?

REPLACEMENT:
**Note:** A standalone reconciler DOES exist at `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py`. It handles board/alert reconciliation for WealthGroup lifecycle signals, with state persisted to `/home/oinkv/signal-gateway/status/reconciler-state.json`. GHOST_CLOSURE events should be emitted from this reconciler's close path (CLOSE_ACTIONS set includes CLOSE, CLOSE_WIN, CLOSE_LOSS, SL_HIT, etc.) AND from micro-gate's `_process_closure()` which handles closure webhooks.

RATIONALE:
FORGE missed the reconciler. It exists in signal-gateway repo, not oinkfarm. signal-gateway is OinkV's repo.
```

#### STALE-A1-7: Rollback plan references wrong service

```
FILE: TASK-A1-plan.md
ORIGINAL:
3. **Service restart:**
   - `sudo systemctl restart kraken-sync` (ANVIL permission required)

REPLACEMENT:
3. **Service restart:**
   - `systemctl --user restart oink-sync` (user-level service, no sudo needed)

RATIONALE:
kraken-sync service is inactive. oink-sync is a user-level systemd service, not system-level.
```

#### STALE-A1-8: §4e Transaction Safety — auto-commit claim

```
FILE: TASK-A1-plan.md
ORIGINAL:
kraken-sync.py already calls `conn.execute()` without explicit transaction management (SQLite auto-commit). Event logging should be within the same implicit transaction as the signal UPDATE to ensure atomicity.

REPLACEMENT:
oink-sync's lifecycle methods use explicit `conn.commit()` calls (see `_check_sl_tp()` line ~354: `if events: conn.commit()`). Event logging should be inserted BEFORE the `conn.commit()` call to ensure the event row is in the same transaction as the signal UPDATE.

RATIONALE:
oink-sync uses explicit commits, not SQLite auto-commit.
```

#### DRIFT-A1-1: Cross-repo dependency (NEW — not in plan)

See showstopper section above. event_store.py is in oinkfarm, lifecycle.py is in oink-sync. The plan assumes they're in the same repo.

#### DRIFT-A1-2: Summary table references (A1-A3-SUMMARY.md)

```
FILE: A1-A3-SUMMARY.md
ORIGINAL:
| `lifecycle.py` | `scripts/kraken-sync.py` | **Different name.** All lifecycle/PnL/SL/TP logic is in kraken-sync.py |
| `engine.py` | `scripts/kraken-sync.py` | **Same file.** Report treats these as separate; they're the same |

REPLACEMENT:
| `lifecycle.py` | `oink-sync/oink_sync/lifecycle.py` | **Exists as named** in the oink-sync standalone package (ported from kraken-sync.py on 2026-04-07) |
| `engine.py` | `oink-sync/oink_sync/engine.py` | **Exists as named** in the oink-sync standalone package (price polling + DB writes) |

RATIONALE:
Arbiter-Oink report's file names (lifecycle.py, engine.py) actually DO exist — just in oink-sync, not in oinkfarm/scripts/. The report was more correct than FORGE realized.
```

#### DRIFT-A1-3: "Critical discovery" section in A1 Evidence

```
FILE: TASK-A1-plan.md
ORIGINAL:
**Critical discovery — Arbiter-Oink report file name discrepancies:**
- Report references `lifecycle.py` → actual file is `kraken-sync.py`
- Report references `engine.py` → actual file is `kraken-sync.py` (same file)

REPLACEMENT:
**Critical discovery — Arbiter-Oink report file name mapping:**
- Report references `lifecycle.py` → actual file is `oink-sync/oink_sync/lifecycle.py` (ported from kraken-sync.py, 811 LOC)
- Report references `engine.py` → actual file is `oink-sync/oink_sync/engine.py` (price polling + DB writes, 548 LOC)
- `scripts/kraken-sync.py` is LEGACY CODE (inactive since 2026-04-07, kept for rollback)

RATIONALE:
The Arbiter-Oink report names were actually correct for the oink-sync codebase. FORGE looked only in oinkfarm/scripts/ and missed the oink-sync standalone package.
```

#### MISSING-A1-1: oink-sync already has event-like returns

oink-sync's `_check_sl_tp()` already returns a list of event dicts (`events.append({...})`) and `_process_tp_hits()` writes to an alerts JSONL file. These existing event structures can be leveraged — instrument by extending the existing `events` list items with signal_events DB writes alongside the alert file writes.

---

## Plan A2: remaining_pct + Blended PnL

### Issues Found: 5 stale references, 1 architectural drift

#### STALE-A2-1: All kraken-sync.py references (CRITICAL)

Same as A1. Every reference to `scripts/kraken-sync.py` must become oink-sync lifecycle.py.

```
FILE: TASK-A2-plan.md
ORIGINAL:
**Function:** `calculate_blended_pnl()` in `scripts/kraken-sync.py` (line ~316)

REPLACEMENT:
**Function:** `calculate_blended_pnl()` in `oink-sync/oink_sync/lifecycle.py` (line ~102, module-level function)

RATIONALE:
Active code is in oink-sync, not kraken-sync.
```

#### STALE-A2-2: calculate_blended_pnl() signature is wrong

```
FILE: TASK-A2-plan.md
ORIGINAL:
```python
def calculate_blended_pnl(entry, exit_price, direction, tp1, tp2, tp3,
                          tp1_hit_at, tp2_hit_at, tp3_hit_at, leverage=None):
```

**Current behavior:**
- Fixed weight map based on how many TPs are *defined* (not how many hit):

REPLACEMENT:
```python
def calculate_blended_pnl(
    entry: float, exit_price: float, direction: str,
    tp1, tp2, tp3,
    tp1_hit, tp2_hit, tp3_hit,   # ← booleans (truthy/falsy), NOT timestamps
) -> float:
```

**Current behavior:**
- No `leverage` parameter (removed in oink-sync port — Mike directive enforced at the type level)
- `tp*_hit` params are booleans (truthy = hit), not timestamp strings
- Fixed weight map based on how many TPs are *defined* (not how many hit):

RATIONALE:
oink-sync's version drops the leverage param entirely and uses booleans for TP hit status, not timestamps.
```

#### STALE-A2-3: Key Files table

```
FILE: TASK-A2-plan.md
ORIGINAL:
| kraken-sync.py | scripts/kraken-sync.py | 1,840 | Contains `calculate_blended_pnl()`, `check_sl_tp()` |

REPLACEMENT:
| lifecycle.py | oink-sync: oink_sync/lifecycle.py | 811 | Contains `calculate_blended_pnl()` (line ~102), `LifecycleManager._check_sl_tp()` (line ~259), `_process_tp_hits()` (line ~358) |

RATIONALE:
Active lifecycle code is in oink-sync.
```

#### STALE-A2-4: Key Functions table

```
FILE: TASK-A2-plan.md
ORIGINAL:
| `calculate_blended_pnl()` | kraken-sync.py | ~316 | `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit_at, tp2_hit_at, tp3_hit_at, leverage=None)` | Rewrite to use event-sourced close percentages |
| `check_sl_tp()` | kraken-sync.py | ~540 | `(conn, prices)` | Add remaining_pct tracking on TP hits |

REPLACEMENT:
| `calculate_blended_pnl()` | oink_sync/lifecycle.py | ~102 | `(entry, exit_price, direction, tp1, tp2, tp3, tp1_hit, tp2_hit, tp3_hit)` | Rewrite to use event-sourced close percentages |
| `LifecycleManager._check_sl_tp()` | oink_sync/lifecycle.py | ~259 | `(self, conn, prices)` | Add remaining_pct tracking on TP hits |
| `LifecycleManager._process_tp_hits()` | oink_sync/lifecycle.py | ~358 | `(self, conn, sig_id, ticker, ...)` | Decrement remaining_pct, store close_pct in event |

RATIONALE:
Correct file, correct signatures, note the separate _process_tp_hits method.
```

#### STALE-A2-5: Rollback plan

```
FILE: TASK-A2-plan.md
ORIGINAL:
4. **Service restart:**
   - `sudo systemctl restart kraken-sync`

REPLACEMENT:
4. **Service restart:**
   - `systemctl --user restart oink-sync`

RATIONALE:
User-level service, no sudo.
```

#### DRIFT-A2-1: TP hit flow description omits _process_tp_hits()

```
FILE: TASK-A2-plan.md
ORIGINAL:
### 4b. TP Hit Flow (Modified)

Current flow in `check_sl_tp()`:
1. TP level hit detected → UPDATE tp*_hit_at, trail SL → log to alert file

REPLACEMENT:
### 4b. TP Hit Flow (Modified)

Current flow: `_check_sl_tp()` delegates TP handling to `_process_tp_hits()` (separate method):
1. `_check_sl_tp()` detects SL breach → closes trade
2. If no SL breach → calls `_process_tp_hits()` which:
   - Iterates TP1→TP2→TP3 ascending
   - On hit: trails SL to previous TP level (or entry), writes alert to JSONL file
   - Returns events list

RATIONALE:
oink-sync splits TP handling into a dedicated method. The remaining_pct decrement should go in _process_tp_hits(), not _check_sl_tp().
```

---

## Plan A3: Auto filled_at for MARKET Orders

### Issues Found: 2 stale references, 0 architectural drifts

A3 is the **least affected** plan because the actual code change targets `micro-gate-v3.py` (correctly identified) — not kraken-sync.

#### STALE-A3-1: kraken-sync interaction references

```
FILE: TASK-A3-plan.md
ORIGINAL:
### 4c. Interaction with kraken-sync.py

`kraken-sync.py` uses `filled_at` in two places:
1. **Grace period** (line ~566): `ref_ts = row["filled_at"] or row["posted_at"]`
2. **Limit fill detection** (line ~736): Sets `filled_at` when PENDING→ACTIVE.

REPLACEMENT:
### 4c. Interaction with oink-sync lifecycle.py

`oink_sync/lifecycle.py` uses `filled_at` in two places:
1. **Grace period** (line ~280): `ref_ts = row[16] or row[15]  # filled_at or posted_at`
2. **Limit fill detection** (`_check_limit_fills()` line ~451): Sets `filled_at` when PENDING→ACTIVE.

RATIONALE:
Active code is in oink-sync, not kraken-sync. Line numbers differ.
```

#### STALE-A3-2: Key Files table

```
FILE: TASK-A3-plan.md
ORIGINAL:
| kraken-sync.py | scripts/kraken-sync.py | 1,840 | `check_limit_fills()` already sets filled_at on LIMIT→FILLED transitions |

REPLACEMENT:
| lifecycle.py | oink-sync: oink_sync/lifecycle.py | 811 | `LifecycleManager._check_limit_fills()` already sets filled_at on LIMIT→FILLED transitions |

RATIONALE:
Active lifecycle code is in oink-sync.
```

**A3 core logic is correct.** The INSERT change in micro-gate-v3.py is properly targeted. The backfill SQL is sound. Only the contextual references to kraken-sync need updating.

---

## Summary — A1-A3-SUMMARY.md Issues

#### STALE-SUMMARY-1: Dependency graph description

```
FILE: A1-A3-SUMMARY.md
ORIGINAL:
A1: signal_events schema extension + kraken-sync instrumentation
...
    │   Instruments kraken-sync.py (0 events currently!)
...
    │         Rewrites calculate_blended_pnl() in kraken-sync.py

REPLACEMENT:
A1: signal_events schema extension + oink-sync lifecycle instrumentation
...
    │   Instruments oink_sync/lifecycle.py (0 events currently!)
...
    │         Rewrites calculate_blended_pnl() in oink_sync/lifecycle.py

RATIONALE:
Active code is in oink-sync.
```

#### STALE-SUMMARY-2: File divergence table (IRONIC — see DRIFT-A1-3)

The summary says lifecycle.py and engine.py don't exist and everything is kraken-sync.py. In reality, lifecycle.py and engine.py DO exist — in oink-sync. The Arbiter-Oink report was closer to reality than FORGE's analysis.

(See DRIFT-A1-2 merge diff above.)

---

## Tally

| Plan | Stale Refs | Arch Drift | Missing Integration | Total |
|------|-----------|------------|-------------------|-------|
| **A1** | 8 | 3 | 1 (cross-repo event_store) | 12 |
| **A2** | 5 | 1 | 0 | 6 |
| **A3** | 2 | 0 | 0 | 2 |
| **Summary** | 2 | 0 | 0 | 2 |
| **TOTAL** | **17** | **4** | **1** | **22** |

## Top 3 Blockers

1. **🔴 BLOCKER: Plans instrument dead code.** Every lifecycle instrumentation target (A1, A2) points at `scripts/kraken-sync.py` which hasn't run since 2026-04-07. Must redirect to `oink-sync/oink_sync/lifecycle.py`. Without this fix, ANVIL ships code that does nothing in production.

2. **🔴 BLOCKER: Cross-repo event_store dependency.** `event_store.py` (oinkfarm repo) needs to be importable from `oink-sync` (separate standalone repo). The plans assume a single-repo layout. ANVIL needs a concrete strategy (vendor, shared package, or raw SQL) before writing code.

3. **🟡 HIGH: calculate_blended_pnl() signature mismatch.** The A2 plan's rewrite targets the kraken-sync signature (`tp1_hit_at` timestamps, `leverage` param). The oink-sync version uses booleans and has no leverage param. The rewrite approach is the same but the starting code differs.

---

## What's Correct (credit to FORGE)

- **micro-gate-v3.py analysis**: INSERT statement, column list, line numbers — all verified correct
- **event_store.py analysis**: schema, 0-row diagnosis, quarantine counts — all correct
- **oinkdb-api.py**: correctly identified as needing event instrumentation
- **DB schema queries**: signal counts, fill_status distribution — all verified
- **A3 core logic**: filled_at = posted_at for MARKET orders is the right fix
- **Test specifications**: comprehensive and well-structured across all 3 plans
- **Risk assessments**: accurate (especially PnL regression risk for A2)
- **Design questions**: all reasonable and well-framed
- **Reconciler in micro-gate**: `_process_closure()` is correctly identified (line 1029)
- **However**: the standalone `reconciler.py` at `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` was missed

---

*Audit complete. Path: `/home/oinkv/forge-workspace/plans/OINKV-AUDIT.md`*
*OinkV 👁️🐷 — 2026-04-19*
