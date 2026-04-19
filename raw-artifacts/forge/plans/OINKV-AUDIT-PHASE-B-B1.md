# OinkV Engineering Audit — FORGE Plan B1 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback, OinkV LLM timeout)
**Date:** 2026-04-19
**Scope:** Staleness, architectural drift, missing file inventory, schema-touch check on TASK-B1-plan.md
**Verdict:** B1 is **structurally sound** but has a **🔴 CRITICAL incomplete file inventory** — it undercounts sqlite3 consumers by ~10 files. The abstraction-layer design itself is correct.

**Provenance:** OinkV `main` agent LLM-timed-out on Phase B audit dispatch at 2026-04-19T19:23:36Z (`session file locked (timeout 10000ms)`). Per sprint-orchestrator skill "Hermes-Subagent Fallback" section, dispatched via `delegate_task`. Subagent hit 50-iteration cap; content recovered from subagent summary per "Hermes-Level Review via delegate_task — Iteration Budget Pitfall" fallback.

---

## 🟢 What B1 Got Right (credit to FORGE)

- **CONFIRMED-B1-1:** `micro-gate-v3.py` at `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` exists, `grep -c sqlite3` = **9** ✓ (matches plan §1)
- **CONFIRMED-B1-2:** `engine.py` at `/home/oinkv/oink-sync/oink_sync/engine.py` — 5 direct `sqlite3` refs, 14 total when including `.execute()`/`.commit()` ✓ (plan claims 14)
- **CONFIRMED-B1-3:** `signal_router.py` at `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` — 7 sqlite3 refs ✓ (matches plan's "7 refs, inline import, timeout=2"). Seven `import sqlite3 as _sq3` / `with _sq3.connect(_DB, timeout=2)` blocks at lines **1516, 2235, 2312, 3062, 3606, 3907, 3979**.
- **CONFIRMED-B1-4:** `signal-gateway` production clone IS `/home/oinkv/signal-gateway/` — verified from `systemctl cat signal-gateway.service`: `WorkingDirectory=/home/oinkv/signal-gateway`, `ExecStart=/usr/local/bin/signal-gateway-wrapper` → `cd /home/oinkv/signal-gateway && python3 -m scripts.signal_gateway.gateway`. No drift pattern here (unlike Phase A audits that flagged signal-gateway/scripts/ as non-canonical for *micro-gate*, signal_router genuinely is canonical here).
- **CONFIRMED-B1-5:** `oink_config.py` "0 direct" claim verified — the 3 `sqlite3` mentions (lines 25, 31, 32) are all inside the module docstring examples, not real code.
- **CONFIRMED-B1-6:** Canonical commits: signal-gateway `c6cb99e1` ✓, oink-sync `e9be741a` ✓.
- **CONFIRMED-B1-7:** §3 "No Schema Migration Required" is correct. B1 touches no schema. DB state drift (A8 sl_type, A11 leverage_source, 52-column signals table) is orthogonal to B1.
- **CONFIRMED-B1-8:** Acceptance criterion §6.2 "No direct sqlite3 imports in the 8 modified files" is the right invariant for a refactor of this type.

---

## 🔴 CRITICAL Findings

### STALE-B1-1: Canonical micro-gate commit is `50b23834`, not `46154543`

**File:** `TASK-B1-plan.md` line 7
**Evidence:** `cd /home/oinkv/.openclaw/workspace && git rev-parse HEAD` → `50b238349ba9ff8322448110a88ee7a9e49300a3`. `46154543` is 4 commits back (it's the A8 sl_type merge). Since then: A11 leverage_source (45a6931d), A10 merge script (81ba4463), and A10 R1 review fixes (50b23834).

**Impact:** Plan was drafted against pre-A10/pre-A11 state. A10 introduced `scripts/merge_databases.py` which is a **new sqlite3-using script that B1 doesn't list** (see MISSING-B1-1). A11 added `leverage_source` column (irrelevant to B1, but shows plan freshness is off by ~3 merges).

**Fix:** Update line 7 to `HEAD 50b23834` and re-scan for new sqlite3 consumers landed after 46154543.

---

### MISSING-B1-1: File inventory omits ~10 sqlite3 consumers

**File:** `TASK-B1-plan.md` §1 "sqlite3 Usage Inventory" (lines 31–40) and §2 "Files to Modify" (lines 87–96)

**Evidence:** `grep -lE "^import sqlite3|^from sqlite3"` across canonical workspace and signal-gateway:

| File | Path | sqlite3/execute refs | In plan? |
|------|------|---------------------|----------|
| **oinkdb-api.py** | `/home/oinkv/.openclaw/workspace/api/oinkdb-api.py` | **38** | ❌ MISSING |
| **trader_resolver.py** | `/home/oinkv/.openclaw/workspace/scripts/trader_resolver.py` | 9 | ❌ MISSING |
| **trader_score.py** | `/home/oinkv/.openclaw/workspace/scripts/trader_score.py` | 7 | ❌ MISSING |
| **validate-data-quality.py** | `/home/oinkv/.openclaw/workspace/scripts/validate-data-quality.py` | 17 | ❌ MISSING |
| **portfolio-webhook.py** | `/home/oinkv/.openclaw/workspace/scripts/portfolio-webhook.py` | 7 | ❌ MISSING |
| **backfill_opened_price.py** | `/home/oinkv/.openclaw/workspace/scripts/backfill_opened_price.py` | >0 | ❌ MISSING |
| **backfill_opened_price_v2.py** | `/home/oinkv/.openclaw/workspace/scripts/backfill_opened_price_v2.py` | >0 | ❌ MISSING |
| **merge_databases.py** | `/home/oinkv/.openclaw/workspace/scripts/merge_databases.py` (A10, new) | >0 | ❌ MISSING (post-plan-draft) |
| **event_store.py (canonical)** | `/home/oinkv/.openclaw/workspace/scripts/event_store.py` | 17 | ⚠️ Only the vendored oink-sync copy is listed |
| **kraken-sync.py** | canonical (DEAD, `DISABLE_KRAKEN_SYNC=1`) | 8 | ❌ Not listed — fine to skip as dead |
| **camofox_worker/thread_state.py** | signal-gateway | >0 | ❌ MISSING |
| **camofox_worker/replay_queue.py** | signal-gateway | >0 | ❌ MISSING |
| **trader_resolver.py (signal-gateway copy)** | `/home/oinkv/signal-gateway/scripts/trader_resolver.py` | >0 | ❌ MISSING |

**Most critical omission: `oinkdb-api.py`** — this is the **production read API** for dashboards/oinkfarm, with 38 sqlite3/execute references. If B1 ships without migrating it, the PostgreSQL cutover in B2 will either break oinkdb-api or force a mid-phase scramble.

**Impact:** Plan §0 claims "Scope: 8 files need updating" — actual scope is **~13–15 files** plus a decision on 3 backfill/utility scripts and one dead module (kraken-sync.py). ANVIL will discover this during implementation and either (a) widen scope unilaterally or (b) ship a B1 that leaves half the codebase still using raw sqlite3, defeating the abstraction-layer goal.

**Fix:** Expand §1 inventory and §2 "Files to Modify" to include at minimum: `oinkdb-api.py`, `trader_resolver.py` (both copies), `trader_score.py`, `validate-data-quality.py`, `portfolio-webhook.py`, `event_store.py` (canonical, not just vendored), `camofox_worker/thread_state.py`, `camofox_worker/replay_queue.py`. Decide policy for backfill/one-shot scripts (`backfill_*.py`, `merge_databases.py`): either migrate or explicitly document "one-shot, pre-cutover only".

---

### DRIFT-B1-1: event_store.py dual-location not addressed

**File:** `TASK-B1-plan.md` §2 line 93 lists only `oink_sync/event_store.py`

**Evidence:** `diff /home/oinkv/.openclaw/workspace/scripts/event_store.py /home/oinkv/oink-sync/oink_sync/event_store.py` → two distinct copies exist. The vendored oink-sync copy (header: "Vendored from oinkfarm commit 3b5453b7") was created by A1's cross-repo resolution. Both have ~17 execute/sqlite3 refs.

**Impact:** If B1 migrates only `oink_sync/event_store.py`, the canonical copy at `scripts/event_store.py` (used by **micro-gate-v3.py** via `from event_store import EventStore` at line ~46) still does `sqlite3.connect(db_path)` at line 109. Mixed state = PostgreSQL cutover breaks micro-gate's EventStore init.

**Fix:** §2 must list **both** `scripts/event_store.py` (canonical) AND `oink_sync/event_store.py` (vendored). The Phase A audit (OINKV-AUDIT.md lines 41–50) explicitly flagged this cross-repo dependency. B1 is the first plan where both must be touched symmetrically.

---

## 🟡 MINOR Findings

### STALE-B1-2: lifecycle.py ref count is 20 in plan, actual is ~26

**File:** `TASK-B1-plan.md` §1 line 35
**Evidence:** `grep -cE "\.execute\(|\.commit\(|\.rollback\(|sqlite3" /home/oinkv/oink-sync/oink_sync/lifecycle.py` → **26**. Only 2 lines contain the literal `sqlite3` (lines 328, 1100, both in comments/docstrings). The 20-figure is close enough to signal intent (plan correctly says "passed conn, ? params") but is imprecise.

**Impact:** Low. Abstraction target is the `.execute()` call sites, and there are more of them than the plan implies. ANVIL will find them by grep.

---

### STALE-B1-3: event_store.py ref count off

**File:** `TASK-B1-plan.md` §1 line 36 says "12 refs"
**Evidence:** Actual count: 17 `.execute()`/sqlite3 refs in vendored copy (`grep -cE "conn\.execute|sqlite3" /home/oinkv/oink-sync/oink_sync/event_store.py` = 17). The 12-figure may be an older snapshot or different counting method.

**Impact:** Same as STALE-B1-2. Advisory count, not a blocker.

---

### DRIFT-B1-2: "Passed-in conn" vs "sqlite3.connect inside class" — event_store behavior subtle

**File:** `TASK-B1-plan.md` §2 line 93, §4c lines 169–171
**Evidence:** `/home/oinkv/oink-sync/oink_sync/event_store.py` line 103: `def __init__(self, conn: sqlite3.Connection)` — takes conn. But line 109 inside `from_path()` classmethod: `conn = sqlite3.connect(db_path)` — creates its own. Plan §4c correctly mentions `from_path()` but focuses on PRAGMA wrapping and doesn't call out that EventStore has **two entry paths** (constructor-with-conn vs from_path) that both need abstraction-layer integration.

**Impact:** Low. ANVIL will notice when reading the file. Mention the dual entry pattern in §4c to save a round trip.

---

### STALE-B1-4: §7 "Rollback Plan" is silent on vendored event_store.py sync

**File:** `TASK-B1-plan.md` §7 lines 240–245
**Evidence:** Plan says "Revert all file changes (git revert)" — but changes span three separate git repos (oinkfarm, oink-sync, signal-gateway). The rollback is three reverts, not one, and they may need ordering (e.g., revert oink-sync first so it still imports the canonical event_store shape).

**Impact:** Low but non-zero. ANVIL's Phase 0 proposal will need to spell out per-repo rollback order.

**Fix:** Split §7 into "rollback for each of the 3 repos" with dependency ordering.

---

### DRIFT-B1-3: Design Q-B1-2 (oink_db.py location) ignores oink-sync's import path

**File:** `TASK-B1-plan.md` §9 lines 265–266
**Evidence:** Plan recommends `oink_db.py` live at `/home/oinkv/.openclaw/workspace/scripts/` next to `oink_config.py`. But **oink-sync is a separate repo** (`/home/oinkv/oink-sync/`) — it cannot import from the oinkfarm `scripts/` directory. This is the exact cross-repo problem A1 hit with event_store.py, and the audit (OINKV-AUDIT.md lines 39–50) spelled out the 4 options (vendor, shared package, raw SQL, move).

**Impact:** Medium. If ANVIL follows FORGE's recommendation literally, oink-sync's lifecycle.py/engine.py/event_store.py can't import `oink_db`. The resolution precedent from A1 was "vendor" — B1 must make the same choice, OR consolidate by making oink_db.py a pip-installable mini-package, OR move oink-sync code into oinkfarm.

**Fix:** Q-B1-2 must be re-framed to include the cross-repo import problem. Recommended resolution: vendor `oink_db.py` into oink-sync the same way A1 vendored `event_store.py`, AND into signal-gateway. Three copies, manually kept in sync, flagged with the same vendoring header A1 used. OR escalate: "Mike, should we consolidate the three repos before B2?"

---

### MISSING-B1-2: No mention of psycopg2 row dict semantics vs sqlite3.Row

**File:** `TASK-B1-plan.md` §4a line 132, §4c line 167
**Evidence:** Plan says "abstraction sets dict-like row factory automatically" — but `sqlite3.Row` supports **both** `row[0]` (index) and `row["col"]` (name), while `psycopg.rows.dict_row` only supports name access. The `lifecycle.py` code at line 280 (per OINKV-AUDIT.md) does `ref_ts = row[16] or row[15]` — positional indexing. This will **break** under dict_row.

**Impact:** Medium — not a B1 blocker (B1 is SQLite-only), but §5 test `test_row_factory` should explicitly verify **both** access patterns work, so that when B2 adds PostgreSQL the regression is caught immediately rather than in production. Or the abstraction layer should provide a hybrid row type that supports both.

**Fix:** Expand §5 test spec with explicit row-access-by-index test. Add an §4a note: "Hybrid row type required — lifecycle.py uses positional indexing".

---

### MISSING-B1-3: timeout parameter semantics not specified

**File:** `TASK-B1-plan.md` §4a line 128
**Evidence:** signal_router.py uses `timeout=2` (lines 1518, 2237, 2314, 3064, 3608, 3909, 3981); engine.py uses `timeout=10` (line 257); event_store PRAGMA sets `busy_timeout=5000`. Plan's `connect(timeout=10)` signature exposes the value but doesn't specify that for PostgreSQL this maps to `connect_timeout` (connection establishment) which is semantically different from SQLite's `timeout` (lock acquisition retry window).

**Impact:** Low for B1 (SQLite only). Will bite in B2. Document in §4d or §4a that the semantic split is intentional and that PostgreSQL's `busy_timeout` analog is a server config, not a client parameter.

---

## 🟢 Additional Confirmations

- **CONFIRMED-B1-9:** §4a parameter translation regex `re.sub(r'\?', '%s', sql)` — scanned `lifecycle.py`, `engine.py`, `event_store.py`, `signal_router.py`, `micro-gate-v3.py` for `?` inside string literals (LIKE patterns, JSON operators). Did not find any. The regex translation is safe for current codebase.
- **CONFIRMED-B1-10:** §4e "What B1 Does NOT Do" boundary is correct and honest — no ORM, no schema change, no async, no pooling. This keeps B1 tractable.
- **CONFIRMED-B1-11:** A10 merge script (merge_databases.py) at commit 81ba4463 is orthogonal to B1 (one-shot migration tool). Not a blocker but should be explicitly de-scoped in §2 with rationale.

---

## Tally

| Category | Count |
|----------|-------|
| 🔴 CRITICAL | 3 (STALE-B1-1 stale commit, MISSING-B1-1 ~10 missing files, DRIFT-B1-1 event_store dual-location) |
| 🟡 MINOR | 7 (count drift ×2, rollback cross-repo, design Q cross-repo, row factory semantics, timeout semantics, EventStore dual-entry) |
| 🟢 CONFIRMED | 11 |

---

## Top 3 Blockers

1. **🔴 MISSING-B1-1: Incomplete file inventory (especially oinkdb-api.py with 38 sqlite3 refs).** B1's §0 claims "8 files" — reality is 13-15. If shipped as-written, the abstraction layer leaves half the codebase on raw sqlite3, making B2's PostgreSQL cutover either incomplete or forcing an emergency scope widening mid-phase. **Fix:** Re-grep all three repos for sqlite3 usage, update §1 and §2 with full list, add policy line for one-shot scripts (merge_databases, backfill_*).

2. **🔴 DRIFT-B1-1: event_store.py exists in two locations (canonical oinkfarm + vendored oink-sync) and plan lists only one.** micro-gate-v3.py imports from the canonical copy; oink-sync's lifecycle imports from the vendored copy. Both must be migrated symmetrically or the cutover breaks. **Fix:** §2 must list both paths explicitly.

3. **🟡 DRIFT-B1-3: Q-B1-2 (oink_db.py location) reproduces the exact cross-repo import problem A1 already hit with event_store.py.** oink-sync is a separate repo and cannot `from oink_config import cfg` — look at oink-sync's code, it has its own config. FORGE's recommendation "put it next to oink_config.py" won't work for 3 of the 8 target files. **Fix:** Re-frame Q-B1-2 to choose between (a) vendor into each of 3 repos, (b) pip-install a shared `oink_common` package, (c) repo consolidation. A1's precedent was (a) vendoring.

---

## Ship-readiness

**NOT SHIP-READY.** B1's abstraction-layer design is fundamentally sound (thin wrapper, parameter translation, PRAGMA guarding, SQLite-only first) and the acceptance criteria are the right ones. But the **file inventory is materially incomplete** and the **cross-repo import problem is unresolved**. ANVIL would need either a revised plan from FORGE or three unilateral scope decisions to ship this, and the second option risks leaving the PostgreSQL migration half-done.

**Recommended action:** Revise B1 before ANVIL starts. Three required fixes:
1. Re-grep and expand §1/§2 inventory (~10 files missed).
2. List event_store.py in **both** locations (canonical + vendored).
3. Resolve Q-B1-2 as a concrete plan (not just "ask Mike"): recommend vendoring per A1 precedent.

Once those three land, B1 is ready. Estimated revision effort: 30-60 minutes of FORGE work. All three are additive — the core design needs no change.
