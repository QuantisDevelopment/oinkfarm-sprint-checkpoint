# Hermes Review — B1 Phase 1: Database Abstraction Layer

**Task:** B1 / 1.3
**Tier:** 🔴 CRITICAL (threshold ≥9.5)
**PRs:** oinkfarm #149 (`12b87356`) · oink-sync #9 (`a07c800`) · signal-gateway #21 (`f1dca60`)
**Branch (all three):** `anvil/B1-db-abstraction`
**Reviewed:** 2026-04-20
**Phase 0 status:** VIGIL R2 APPROVE · GUARDIAN R1 APPROVE (R2 carried forward)

## Verdict: ✅ LGTM

All 5 GUARDIAN MUST-preserve items and all VIGIL carry-forwards hold up under independent verification. B1 is a well-scoped, purely behavioral-parity refactor that correctly lands across all three repos with matching canonical/vendored semantics, clean readonly/write separation, and a new 37-test suite that covers exactly the right surface. The only risks are operational and low-probability (vendored-drift without CI enforcement, psycopg absence blocking premature B2 misconfig), and neither is a B1 blocker.

---

## Summary

B1 introduces `oink_db.py` as a thin SQLite wrapper (canonical in oinkfarm, vendored per-repo in oink-sync and signal-gateway) and replaces 17 production call sites with `connect()` / `connect_readonly()` / `connect_path()`. The abstraction preserves WAL, `busy_timeout=5000`, `sqlite3.Row` factory, and the readonly URI (`mode=ro`). Postgres branches `raise NotImplementedError` — no psycopg import present in any repo.

**Stats verified:**
- oinkfarm: 12 files, 661+/61- (incl. 437-line test file)
- oink-sync: 3 files, 106+/11-
- signal-gateway: 8 files, 144+/56-
- Tests on canonical oinkfarm: `test_b1_oink_db.py` → **37 passed in 0.04s** ✅
- signal-gateway full suite (excluding telethon-missing test_registry_guard): **276 passed in 29.88s** ✅
- oink-sync full suite: **85 passed, 4 failed** — all 4 failures are `yfinance/pandas ModuleNotFoundError` (environment-only, unrelated to B1) ✅
- canonical oinkfarm full suite: **163 passed, 5 failed** — the 5 failures (`test_micro_gate_mutation_guard` ×3, `test_micro_gate_wg_alert_override` ×2) reproduce on parent commit `80f4fe0a` (A10) in a fresh clone → **confirmed pre-existing, B1 introduces zero new failures**.

---

## VIGIL / GUARDIAN Cross-Reference

### VIGIL Phase 0 R2 (APPROVE)
The three R1 required changes — (1) file inventory 8→17, (2) cross-repo import strategy via vendoring, (3) `event_store.py` dual-location — were all resolved in R2 and are reflected in the Phase 1 delivery. VIGIL's two forward-looking concerns (kraken-sync.py accidental modification; oinkdb-api.py 38-ref migration completeness) are both addressed by the implementation — see items [e] and [f] below.

### GUARDIAN Phase 0 R1 + R2 (APPROVE)
GUARDIAN explicitly carried 5 MUST-preserve items into Phase 1. All 5 are verified individually below.

### Alignment
No contradictions between the Phase 0 reviews and no divergence between Phase 0 concerns and Phase 1 implementation. The vendoring header discipline VIGIL required is present on both vendored copies (`# Vendored from oinkfarm canonical workspace. Do not edit in-place.` + source path + vendor date + changes-from-canonical note).

---

## 5 GUARDIAN MUST-Preserve Verification

### [1] ✅ Readonly lookup + timeout behavior in `signal_router.py` preserved
**Evidence:**
- Pre-B1 pattern: 7 inline `import sqlite3 as _sq3 ... _sq3.connect(_DB, timeout=2)` blocks at lines 1516/2235/2312/3062/3606/3907/3979.
- Post-B1 (commit `f1dca60`): module-level `from scripts.oink_db import connect_readonly` at line 30; each of the 7 blocks replaced with `with connect_readonly(timeout=2) as _conn:` at lines 1518/2235/2310/3058/3600/3899/3969.
- `grep -c 'connect_readonly(timeout=2)' signal_router.py` = **7** (matches).
- Vendored `signal-gateway/scripts/oink_db.py::connect_readonly()` uses `sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=timeout)` — preserves URI-mode-ro + caller-supplied timeout.
- Default `_DEFAULT_DB_PATH` in signal-gateway vendored copy resolves via `OINKFARM_DB` env var first, exactly matching the pre-B1 inline pattern `_DB = os.environ.get("OINKFARM_DB", ...)`.

### [2] ✅ PRAGMA handling SQLite-only and OFF readonly paths
**Evidence:**
- `connect_readonly()` in all 3 copies: sets `PRAGMA busy_timeout=5000`, does NOT set `PRAGMA journal_mode=WAL` (correct — readonly connections cannot change journal mode).
- `connect()` sets `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000`.
- `connect_path(readonly=True)`: skips WAL (same pattern).
- `connect_path(readonly=False)`: sets WAL (correct for camofox separate DBs).
- Post-B1 grep of all PRAGMA sites in production code: only appear in `oink_db.py`, `micro-gate-v3.py` (`PRAGMA foreign_keys=ON` preserved inline at canonical:1439/1513, signal-gateway:964/1037 — write paths only), `validate-data-quality.py` (explicit `PRAGMA busy_timeout=30000` override after `connect()`, correctly preserving the pre-B1 longer-timeout semantics), and `oink-sync/engine.py` (`busy_timeout=5000` + `foreign_keys=ON` on a `connect()`-opened write connection — fine).
- **Zero PRAGMA calls on readonly paths.** ✅

### [3] ✅ No missed direct `sqlite3` call sites in production
**Evidence:** Full repo grep after filtering tests, archive, and explicitly de-scoped files:
- **oinkfarm canonical:** `grep -rn 'import sqlite3\|sqlite3\.connect(' scripts/ api/ | grep -v oink_db.py | grep -v archive | grep -v backfill_ | grep -v merge_databases | grep -v kraken-sync` → only hit is `scripts/price-verify-trades.py.deprecated` (suffix `.deprecated` → not loaded by anything) ✅
- **oink-sync:** `grep -rn 'import sqlite3\|sqlite3\.connect(' oink_sync/ | grep -v oink_db.py` → **zero matches** ✅
- **signal-gateway:** `grep -rn 'import sqlite3\|sqlite3\.connect(' scripts/ | grep -v oink_db.py | grep -v kraken-sync` → **zero matches** ✅
- `oinkdb-api.py` specifically: **0** occurrences of `sqlite3` post-B1 (was 38 per Phase 0 audit). The heaviest migration in the set is clean.
- The grep-based test `TestNoDirectSqlite3Imports` in `test_b1_oink_db.py` enforces this automatically for all 17 modified files.

### [4] ✅ Vendored `oink_db.py` copies behave identically
**Evidence:**
- All three copies have the same public API (`connect`, `connect_readonly`, `connect_path`, `get_engine`, `get_default_db_path`) and the same re-exports (`IntegrityError`, `OperationalError`, `DatabaseError`, `Row`, `OinkConnection`) — enforced by `TestVendoredCopiesConsistent` in the test suite.
- Byte-level `diff` between canonical and each vendored copy shows differences are limited to:
  - Docstring stripping (vendored copies are trimmed) — **semantically inert**.
  - Config source bootstrap (the intentional per-repo variation):
    - canonical: `from oink_config import cfg as _cfg; _DEFAULT_DB_PATH = _cfg.db_path`
    - oink-sync: `from .config import config as _sync_config; _DEFAULT_DB_PATH = _sync_config.db_path`
    - signal-gateway: `os.environ.get("OINKFARM_DB", os.environ.get("OINK_DB", "/home/m/data/oinkfarm.db"))`
  - Header comments on the vendored copies (standard vendoring discipline).
- Body of `connect()`, `connect_readonly()`, `connect_path()` is **byte-identical** across all three copies (verified by diff: the only non-docstring/config differences are whitespace).
- MD5 checksums differ (expected due to docstring + config differences): canonical `41a450b4...`, oink-sync `f804bce7...`, signal-gateway `f85d05b2...` — this is the documented variation, not drift.

**Concern (non-blocking):** There is no CI-level enforcement that vendored copies stay in sync when canonical changes. The test suite's `TestVendoredCopiesConsistent` checks shape (functions exist, re-exports present) but not body equivalence. For B2, suggest adding a body-diff assertion keyed off normalized (config-stripped, docstring-stripped) text. Tracking this as an H-finding below, not a blocker.

### [5] ✅ Postgres scaffolding dormant; no psycopg import
**Evidence:**
- All 3 copies: `if _DB_ENGINE != "sqlite": raise NotImplementedError(...)` guard at the top of both `connect()` and `connect_readonly()`.
- `connect_path()` deliberately ignores the engine flag (correct — camofox separate DBs stay SQLite even in B2). This is tested (`test_connect_path_ignores_engine`).
- `grep -rn 'psycopg'` across all three repos (excluding archives): **zero matches** anywhere. Only mention of "postgresql" in any production file is a docstring line in `scripts/oink_db.py:163`.
- Engine guard is tested twice (`test_pg_engine_not_implemented`, `test_pg_readonly_not_implemented`).

---

## VIGIL Carry-Forward Verification

### [a] ✅ Vendoring header discipline present
Both vendored copies carry the 4-line provenance header required by VIGIL R2:
- Source path (`/home/oinkv/.openclaw/workspace/scripts/oink_db.py`)
- Vendor date (`2026-04-20 (B1 implementation)`)
- Changes-from-canonical note (config source)
- Do-not-edit-in-place warning

### [b] ✅ `event_store.py` dual-location migrated symmetrically
- Canonical `scripts/event_store.py` diff: `sqlite3.connect(db_path) + PRAGMA journal_mode=WAL + PRAGMA busy_timeout=5000` → `connect(db_path)` (PRAGMAs absorbed); `sqlite3.OperationalError` → `OperationalError` re-export.
- Vendored `oink_sync/event_store.py` diff: same pattern, uses `from .oink_db import connect, OperationalError`.
- Both constructors (`__init__(conn)` and `from_path(db_path)`) migrated correctly. The regression test `TestEventStoreRegression::test_canonical_event_store` exercises the canonical copy end-to-end through the new abstraction.

### [c] ✅ `oinkdb-api.py` migration complete (VIGIL's 38-ref concern)
As noted in [3]: `grep -c 'sqlite3' api/oinkdb-api.py` = **0** post-B1 (was 38 pre-B1). All three DB-producing functions (`get_db()`, `get_old_db()`, the `get_trader_win_rates(db)` annotation stripping) migrate cleanly. `get_old_db()` correctly uses `connect_readonly(OLD_DB_PATH)` so the frozen v1 DB path continues to work.

### [d] ✅ Row factory supports both dict and positional access
Tested explicitly (`test_row_positional_access`, `test_row_both_access_patterns`, `test_readonly_row_factory`, `test_connect_path_row_factory`). All 3 vendored copies use `sqlite3.Row` which natively supports both — so when B2 introduces PostgreSQL, the existing positional-access sites (e.g., `lifecycle.py::row[16] or row[15]`) will flag immediately rather than silently drift. Good B2 preparation.

### [e] ✅ `kraken-sync.py` (signal-gateway) NOT modified
- `git log --oneline 1adeaa1..f1dca60 -- scripts/kraken-sync.py` → **empty** (untouched by B1).
- `git diff --stat` for signal-gateway confirms `kraken-sync.py` is not in the B1 delta.
- File still contains its own `import sqlite3` at line 37 — intentional per de-scope policy (kraken-sync is dead: `DISABLE_KRAKEN_SYNC=1`).
- Canonical oinkfarm's `scripts/kraken-sync.py` is likewise untouched by commit `12b87356`.

### [f] ✅ Financial Hotpath #6 `micro-gate-v3.py` INSERT logic preserved
- `git diff 80f4fe0a..12b87356 -- scripts/micro-gate-v3.py | grep -E '^[+-].*INSERT'` → **zero hits**. Same for `UPDATE`.
- The only changes are: (1) `import sqlite3` → `from oink_db import connect, DatabaseError`; (2) three `except sqlite3.Error` → `except DatabaseError`; (3) two `sqlite3.connect(DB_PATH) + row_factory + WAL + busy_timeout` → `connect(DB_PATH)` (PRAGMAs absorbed). The subsequent `conn.execute("PRAGMA foreign_keys=ON")` is preserved inline at lines 1439 and 1513 on the canonical copy (and 964/1037 on signal-gateway copy). `INSERT OR IGNORE INTO signals` at canonical:985 and signal-gateway:623 is untouched.
- Diff numerics on canonical micro-gate-v3.py: 14 lines removed, 11 lines added — net −3, consistent with mechanical connect-swap only.

---

## Downstream Consumer Check

1. **micro-gate-v3.py**: used by signal-gateway cron + canonical cron. `conn` is created once per `run_batch()` and passed down to `_process_signal / _process_update / _process_closure`. Those three functions consume `conn.execute(...).fetchone()` / `.execute(INSERT...)` / `.commit()` / `.rollback()` — all methods sqlite3.Connection exposes natively, so the type change from `sqlite3.Connection` to the now-untyped wrapper (which IS `sqlite3.Connection` in B1) is transparent. ✅
2. **EventStore consumers (canonical `scripts/event_store.py` + vendored `oink_sync/event_store.py`)**: both migrated in lockstep per [b]. Both expose the same `EventStore(conn)` / `EventStore.from_path(db)` constructor shape. `micro-gate-v3.py::_get_event_store(conn)` at canonical:47 now accepts an untyped conn — still a valid `sqlite3.Connection` object. ✅
3. **oinkdb-api.py FastAPI handlers**: each `Depends(get_db)` now returns a `connect_readonly` result. All downstream `db.execute(...)` / `db.commit()` calls still work because the return type is still `sqlite3.Connection`. ✅
4. **oink-sync Engine** (`engine.py::_write_prices_to_db`): uses `with connect(config.db_path, timeout=10) as conn:` which works because sqlite3.Connection is itself a context manager. The `with` statement correctly commits on clean exit and rolls back on exception — tested (`test_context_manager_commits`, `test_context_manager_rollback_on_exception`). ✅
5. **camofox workers (thread_state, replay_queue)**: both use `connect_path(..., timeout=10, isolation_level=None)` — `**kwargs` passthrough verified in `connect_path()`. Test `test_connect_path_isolation_level_none` exercises exactly this pattern. ✅
6. **tests/test_preemit_filter.py** (signal-gateway): correctly updated from `patch.dict("sys.modules", {"sqlite3": ...})` to `patch("scripts.signal_gateway.signal_router.connect_readonly", ...)` — this is the right way to mock the new abstraction. ✅

---

## New Findings

### 🟢 H1 — No CI enforcement of vendored-body equivalence
The test suite's `TestVendoredCopiesConsistent` verifies that each copy defines the required functions and re-exports, but does not verify that the **function bodies** are byte-equivalent (modulo the intentional config source and docstring differences). If a future fix to `connect()` lands in canonical without being propagated to oink-sync / signal-gateway, the test suite will not catch it.

**Suggested (non-blocking):** in B2 or a B1.1 follow-up, add a normalized-body diff test that strips the config block + docstrings, then asserts byte equality of the `connect / connect_readonly / connect_path` function bodies across all three copies.

### 🟢 H2 — Import order of `from oink_db import connect_readonly` mid-module in a few files
- `scripts/dashboard/serve.py`: the new `from oink_db import connect_readonly` sits between `import subprocess` and `import sys` (not at top of stdlib group). Cosmetic PEP8 nit only.
- `scripts/portfolio_stats.py`, `scripts/trader_score.py`: same minor layout (new import inserted between stdlib imports).

Not behavioral, not a blocker. Might trigger ruff/isort in a future lint pass.

### 🟢 H3 — `bybit-suite/backend/src/bybit_suite/store.py` still uses `import sqlite3`
This file is **not** in B1's scope (it's a separate FastAPI backend for the bybit suite, not part of the OinkFarm DB migration path — it manages its own registry SQLite file). It's correctly excluded from B1 and doesn't invalidate the "zero direct sqlite3 in oinkfarm production" claim because the proposal's scope is "OinkFarm DB consumers". Surfacing it here as a transparency note in case B2 wants to extend scope.

### 🟢 H4 — `scripts/kraken-sync.py` is in the canonical oinkfarm workspace with a live `import sqlite3`
The canonical copy at `/home/oinkv/.openclaw/workspace/scripts/kraken-sync.py` still has `import sqlite3` at line 37. This matches the explicit de-scope per the proposal ("dead, `DISABLE_KRAKEN_SYNC=1`"). The signal-gateway copy is the one that was verified untouched in [e]. No action required; logged for audit trail.

### 🟢 H5 — `scripts/price-verify-trades.py.deprecated`
The `.deprecated` suffix file in the canonical oinkfarm workspace still contains `import sqlite3` / `sqlite3.connect(...)`. Python will not import a `.deprecated` file, so this is inert — but a future grep-based CI rule that forgot to filter `.deprecated` could false-positive. Tag as informational.

---

## What's Done Well
- **Scope discipline.** All 17 production files landed in one atomic set of 3 branches, each with its own rollback point. No scope creep into backfill or merge scripts.
- **Vendoring hygiene.** Each vendored copy has a clear provenance header, so future maintainers know where canonical lives.
- **Config-source flexibility.** Each vendored copy gets its DB path from the repo's existing config pattern (oink-sync's Config dataclass, signal-gateway's OINKFARM_DB env), not from a shared singleton — this avoids tight coupling between the three repos.
- **B2 readiness.** Postgres branches are `NotImplementedError` rather than silent fallthroughs, positional row access is tested, and `connect_path()` is carved out for the camofox separate-DB case that should NOT migrate to Postgres.
- **Test coverage depth.** 37 tests cover connect/readonly/path, row factory (both patterns), context manager (commit + rollback), PRAGMA assertions, engine guard (3 variants), timeout passthrough, re-exports, helper functions, grep invariants for all 17 files, vendored-copy shape equivalence, and an end-to-end EventStore regression.
- **Readonly semantics preservation.** The 7 signal_router blocks are the single highest-risk area in the PR and are mechanically replaced with matching semantics (URI-mode-ro, timeout=2).
- **PRAGMA precision.** `validate-data-quality.py` explicitly re-applies `busy_timeout=30000` after `connect()` because the default is 5000 — the diff shows thoughtful preservation of per-script overrides rather than a lossy mechanical replacement.

---

## Final Verdict: ✅ LGTM

All Phase 0 carry-forwards are satisfied. All 5 GUARDIAN MUST-preserves verify on independent inspection. No new failures introduced in any of the 3 test suites. `oinkdb-api.py` (the heaviest migration) is fully clean. `kraken-sync.py` (signal-gateway) is untouched. Financial Hotpath #6 (`micro-gate-v3.py` INSERT logic) is preserved with only the connect-swap changing. The abstraction cleanly prepares for B2 without leaking psycopg or Postgres semantics into B1.

B1 meets the 🔴 CRITICAL threshold. Merge-safe across all three repos, assuming orchestrator merges in a sane order (canonical first so oink-sync / signal-gateway imports still resolve, though the vendored copies mean repo order doesn't actually matter — it's a pure-vendor drop-in).

**Mergeable.** Recommend shipping.

**MUST-FIX items:** None.
**SHOULD-FIX items:** None for B1. H1 (vendored-body CI enforcement) is suggested for B1.1 or B2 groundwork.
