# OinkV Engineering Audit — FORGE Plan B8 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback, OinkV LLM timeout)
**Date:** 2026-04-20
**Scope:** Staleness, line-number drift, function-existence verification, dependency-order sanity on TASK-B8-plan.md
**Verdict:** 🔴 **REVISE MAJOR** — 5 of the 10 target functions no longer exist in `signal_router.py` (moved to `emitter.py` by B5, which merged after the plan was drafted). The remaining 5 have line-number drift of ~221–234 lines. The plan's entire §1 "Current State Analysis" table is obsolete and must be rewritten against post-B5 HEAD. The extraction *concept* (router module for classification/dedup/lifecycle policy) is still coherent but its target set has shrunk dramatically.

**Provenance:** Scheduled cron audit. Plan drafted 2026-04-19T19:28 against pre-B5 HEAD `c6cb99e` (4,460 LOC). B5 merged 2026-04-20T06:55 as commit `2e345bb`, moving 5 of this plan's 10 target functions into a new `SignalEmitter` class. B6 and B7 (plan's stated prerequisites) have NOT merged.

---

## 🟢 What B8 Got Right (credit to FORGE)

- **CONFIRMED-B8-1:** `signal_router.py` canonical path `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` ✓ (matches B1 audit §CONFIRMED-B1-4).
- **CONFIRMED-B8-2:** `_is_commentary_only_channel()` still exists in `signal_router.py` as an instance method — it was NOT moved in B5 (confirmed by `grep` and by the comment block in `signal_router.py:1434-1435` that explicitly lists which functions moved; `_is_commentary_only_channel` is not in that list). Still a valid extraction target.
- **CONFIRMED-B8-3:** `_dedup_key()` and `_mark_seen()` still exist in `signal_router.py`. Still valid extraction targets.
- **CONFIRMED-B8-4:** `_alert_content_dedup()` and `_tg_content_dedup()` still exist in `signal_router.py`. The plan's own §4a correctly flags that these stay with SignalRouter instance state (deque + set), which is a good architectural call — but then §3e step 1 lists `_alert_content_dedup` among "functions to remove from signal_router.py", which is an internal contradiction (see MINOR-B8-3 below).
- **CONFIRMED-B8-5:** The general strategy — **"decision functions extract, cache mutators stay"** — is sound and consistent with how B5 split the emitter (pre-emit filter decisions moved, state management stays in router for lifecycle reasons).
- **CONFIRMED-B8-6:** §2 target file path `scripts/signal_gateway/router.py` is a valid new module. No conflict with existing files in `/home/oinkv/signal-gateway/scripts/signal_gateway/` (confirmed: `alert_channel.py, board_parser.py, board_state.py, discord_notify.py, discord_ws.py, emitter.py, extractor.py, gateway.py, health.py, kraken_sync_wrapper.py, oinxtractor_client.py, reconciler.py, replay_consumer.py, rest_poller.py, signal_router.py, supervisor.py, telegram_client.py, utils.py`).
- **CONFIRMED-B8-7:** Design principle §4b "DB connection injection pattern" aligns with the already-merged B1/B2/B3 oink_db abstraction — the plan is forward-compatible with the current `from scripts.oink_db import connect, connect_readonly` pattern (now in use at signal_router.py line 30).
- **CONFIRMED-B8-8:** §4a "memory caches stay in SignalRouter class" reasoning is correct and matches B5's precedent (B5 moved `_forwarded_signals` cache with its mutators; it would be inconsistent to split cache from mutators for the content-dedup caches now).
- **CONFIRMED-B8-9:** Rollback plan §7 is trivial (single-repo revert of a net-additive change) — appropriately minimal.
- **CONFIRMED-B8-10:** §4c "what remains in signal_router.py after B5-B8" ~2,600-2,800 LOC estimate is directionally reasonable, though specific numbers are speculative until B6+B7 land.

---

## 🔴 CRITICAL Findings

### STALE-B8-1: 5 of 10 target functions have been moved out of `signal_router.py` by B5

**File:** `TASK-B8-plan.md` §1 (lines 27-46), §3e (line 169)
**Evidence:**

B5 merged 2026-04-20T06:55 as commit `2e345bb` ("B5: extract SignalEmitter from signal_router (#25)"). The commit moved 5 of this plan's 10 target functions into a new `SignalEmitter` class at `/home/oinkv/signal-gateway/scripts/signal_gateway/emitter.py`. The comment block at `signal_router.py:1434-1435` makes the move explicit:

```python
    # _mark_forwarded, _is_recently_forwarded, _check_signal_state,
    # _should_suppress_lifecycle, _classify_lifecycle_action → moved to SignalEmitter (B5)
```

| B8 target | B8 plan location (router) | Actual location post-B5 | Impact |
|-----------|---------------------------|-------------------------|--------|
| `_classify_lifecycle_action()` | router 1617-1657 | **`emitter.py:284`** as `classify_lifecycle_action` (staticmethod) | 🔴 Gone from router |
| `_check_signal_state()` | router 1493-1543 | **`emitter.py:162`** as `check_signal_state` | 🔴 Gone from router |
| `_should_suppress_lifecycle()` | router 1544-1616 | **`emitter.py:211`** as `should_suppress_lifecycle` | 🔴 Gone from router |
| `_mark_forwarded()` | router 1464-1479 | **`emitter.py:131`** as `mark_forwarded` | 🔴 Gone from router |
| `_is_recently_forwarded()` | router 1480-1492 | **`emitter.py:147`** as `is_recently_forwarded` | 🔴 Gone from router |

Call-site proof (signal_router.py post-B5):
- `self._emitter.is_recently_forwarded(...)` at lines 2116, 3412, 3696
- `self._emitter.classify_lifecycle_action(...)` at lines 2130, 2334, 3503
- `self._emitter.should_suppress_lifecycle(...)` at lines 2135, 2336, 2441, 3504
- `self._emitter.mark_forwarded(...)` at lines 2155, 3534, 3724

**Impact:** Plan §1's "Classification / Routing Functions" table is 75% wrong — 3 of the 4 rows point to functions that no longer exist in signal_router.py. §1's "Dedup Functions" table is 33% wrong (2 of 6 rows point to relocated functions). §3e's "Remove these functions from signal_router.py" list includes 5 names that are already gone. ANVIL reading this plan would either (a) `git grep` and discover the drift then stall awaiting revised plan, or (b) attempt to modify `emitter.py` instead, which was NOT the stated scope of B8.

**Fix:** FORGE must rescope B8 to one of three options:
1. **Cancel the emitter-resident functions from B8's target set.** The 5 B5-moved functions are already in a dedicated module — extracting them again to `router.py` is pure churn and creates an emitter↔router circular dependency. B8's remaining scope becomes: `_is_commentary_only_channel`, `_dedup_key`, `_mark_seen` (policy-level question — see MINOR-B8-3), and the 5–6 inline DB dedup queries. LOC reduction target should drop from ~600 to ~150-200.
2. **Merge router.py into emitter.py.** If the architectural intent is "one module for pre-emit decisions," rename `emitter.py` to `pre_emit.py` or `router.py`, relocate the 3 remaining router-resident decisions there. Net-zero new file.
3. **Split emitter.py into emitter.py + router.py.** Keep emitter.py as dispatch-only (emit_signal, emit_alert_signal, etc.), move classification/dedup/lifecycle decisions from emitter.py to router.py. This is the most-work option and contradicts B5's stated rationale (§4d of B5 plan: "pre-emit filter chain intact: should_suppress_lifecycle + check_signal_state + classify_lifecycle_action all in emitter, no callback to router").

Recommended: **Option 1.** B5 already did what B8 §1's first 5 rows wanted to do. FORGE should mark those rows ✅ DONE-IN-B5 and shrink B8 scope accordingly.

---

### STALE-B8-2: Inline sqlite3 dedup sites are wrong in both count and coordinates

**File:** `TASK-B8-plan.md` §1 line 46, §3d line 156, §9 lines 295 + 302-305
**Evidence:**

Plan claims "7 inline sqlite3 query sites" at lines **1516, 2235, 2312, 3062, 3606, 3907, 3979**.

Current post-B5 reality (`grep -nE "connect_readonly|sqlite3|oink_db"` on signal_router.py):

| Actual location | Type | Purpose |
|-----------------|------|---------|
| line 30 | `from scripts.oink_db import connect, connect_readonly` | import |
| **line 2014** | `with connect_readonly(timeout=2)` | passthrough ticker+entry trader resolution |
| **line 2089** | `with connect_readonly(timeout=2)` | passthrough cross-channel dedup |
| **line 2833** | `with connect_readonly(timeout=2)` | Cornix text cross-channel dedup |
| **line 3375** | `with connect_readonly(timeout=2)` | text-extract cross-channel dedup |
| **line 3674** | `with connect_readonly(timeout=2)` | board INSERT cross-channel dedup |
| **line 3747** | `with connect(timeout=2)` | A6 ghost closure (read+write; changed from `connect_readonly` by B3/Q-B3-4) |

Count is **6, not 7**. The plan's count of 7 came from the pre-B5 enumeration (which counted the dedup block *inside* `_check_signal_state` at 1516 — that block has since moved into `emitter.py` as part of B5). Plan line 1516 claim: no longer in signal_router.py at all.

Additionally, the plan's §9 line 295 "7 inline sqlite3 query sites" and the plan's §1 line 46 "~2235, ~2315, ~3065, ~3609, ~3910" are all shifted by ~200 lines due to B5 extraction (~230 LOC removed). The only correspondences:
- 2235 → 2089 (passthrough dedup)
- 2315 → 2833 (Cornix dedup)
- 3065 → 3375 (text-extract dedup)  
- 3609 → 3674 (board INSERT dedup)
- 3910 → 3747 (A6 ghost closure)

Plus one site in the plan at "line 1516" is now INSIDE `emitter.check_signal_state()` (not a router concern anymore). The 2312 site from B1 audit was a Cornix passthrough variant that appears to have merged with 2235.

Further: the plan describes these as raw `sqlite3` with `import sqlite3 as _sq3` inline. **That pattern no longer exists** — B1/B2/B3 migrated all signal_router.py DB access to `oink_db.connect/connect_readonly()`. `grep -c "import sqlite3" /home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` = **0**. The B1 audit's §CONFIRMED-B1-3 finding of "7 sqlite3 refs with `import sqlite3 as _sq3` inline" is now obsolete post-B1 merge.

**Impact:** The plan's §3d "DB Query Consolidation" strategy still makes architectural sense (consolidate 6 similar queries into `router.is_duplicate_signal()`), but:
- The LOC savings are smaller than claimed (6 sites, not 7, and the inline `import sqlite3` boilerplate is already gone — savings per site dropped from ~6 lines to ~3 lines).
- The plan's §3d "If B1 has shipped, pass oink_db connection; if not, raw sqlite3" bifurcation is moot — B1/B2/B3 all shipped. Only the oink_db path needs consideration.
- One of the 6 sites (A6 ghost closure, line 3747) is a **read+write** with nested logic (fetch candidate signals, entry-price match, conditional INSERT, conditional UPDATE). This is NOT a simple "is_duplicate_signal" query — it's a whole A6 protocol. The plan's §3d conflates it with the 5 plain dedup reads. Extracting this as a standalone `router.find_ghost_closure_target()` is plausible but not what the plan currently proposes.

**Fix:**
1. Rewrite §1 row "DB dedup queries (inline)" — set count to 6 (not 7), replace line numbers with current ones (2014, 2089, 2833, 3375, 3674, 3747).
2. Remove all language about "`import sqlite3 as _sq3`" and the "B1 shipped vs not" bifurcation — B1/B2/B3 shipped.
3. Split the A6 ghost closure site (3747) out of the consolidation target — it's a distinct protocol needing its own function signature.
4. Add the passthrough-trader-resolution site at line 2014 to the inventory (it's a DISTINCT-ON-trader query, not a dedup query — may deserve its own helper or be left inline).

---

### STALE-B8-3: Canonical-file header block is pre-B5; all line citations need a time-stamped refresh

**File:** `TASK-B8-plan.md` lines 6-7
**Evidence:** Plan line 6: "signal_router.py (4,460 LOC pre-extraction, target ~2,800-3,200 LOC post-B5/B6/B7)". Plan line 7: "Codebase Verified At: 2026-04-19T18:00Z (post-A8 merge 46154543)".

Current reality:
- `wc -l /home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` = **4,230** (post-B5)
- `git log --oneline -1 scripts/signal_gateway/signal_router.py` = **`2e345bb B5: extract SignalEmitter from signal_router (#25)`**, dated 2026-04-20T06:55
- Signal-gateway HEAD: `2e345bb` (B5 merge)

The plan is timestamped 2026-04-19T18:00Z and references HEAD `46154543`. Since then, B1 (f1dca60 + 963fa3e), B2 (df8112d), B3 (07940ce + c75fb92 + cc70e5b), and B5 (2e345bb) have all merged into signal-gateway — 7 commits, ~650 LOC of churn. Every line-number citation in the plan must be assumed stale.

**Impact:** Compounds STALE-B8-1 and STALE-B8-2. Without a freshness re-anchor, every citation in §1, §3e, §9 is unreliable. ANVIL will need to re-verify every line before extracting, which effectively regresses the plan to a starting point rather than a blueprint.

**Fix:**
1. Update line 6 LOC estimate: signal_router.py is currently **4,230 LOC** post-B5 (not 4,460).
2. Update line 7 `Codebase Verified At` timestamp and HEAD: `2026-04-20T07:00Z (post-B5 merge 2e345bb)`.
3. Re-run the line-number scan for every function cited in §1 and §9 against current HEAD. ~10-minute task using `git grep -n`.

---

### STALE-B8-4: Dependency claim "Dependencies: B6 + B7" is no longer tight

**File:** `TASK-B8-plan.md` line 5, §0 line 14
**Evidence:** Plan says "B8 operates on the signal_router.py that remains after parser extraction" and "After B5, B6, and B7 have extracted ~1,000-1,200 LOC, the remaining signal_router.py will be ~3,200-3,400 LOC. B8 extracts another ~600 LOC."

Current reality:
- B5 shipped (not stated as dependency because plan pre-dates B5 merge).
- B6 and B7 plans exist but have NOT merged.
- The 5 B5-moved functions were B8's largest targets (~235 LOC in emitter.py now). Without them, B8's remaining router scope is ~150-250 LOC, not ~600.

Logical question: Does B8 still depend on B6+B7? Plan's argument is "operate on what remains after parsers extract." But B8's targets (`_is_commentary_only_channel`, `_dedup_key`, `_mark_seen`, 5-6 dedup queries, A6 ghost closure) have **no overlap** with B6 (Cornix+Chroma parsers) or B7 (WG Bot parsers) — the parser extractions don't touch these functions. They could ship in any order.

**Impact:** B8 may be able to ship immediately (before B6/B7) if FORGE is comfortable with non-stable line numbers in the final signal_router.py. Alternatively, B8 could be deferred with no blocking cost. The "B6+B7 must ship first" claim imposes an artificial sequence.

**Fix:** §0 executive summary and §line-5 dependency list should be revised to:
- "Dependencies: B5 (shipped, extracted emitter — B8 targets the post-emitter residue)."
- Note: "Independent of B6/B7 — B8's target functions do not overlap with parser extraction scope. Can ship in parallel or before B6/B7. Ordering preference is cosmetic (post-B6/B7 signal_router.py will have cleaner line numbers for the dedup queries)."

---

## 🟡 MINOR Findings

### MINOR-B8-1: `_is_commentary_only_channel` line-number drift is -221

**File:** `TASK-B8-plan.md` §1 line 32
**Evidence:** Plan says lines 1658-1669. Actual: **1437-1447**. Drift: -221 lines (matches the ~230 LOC B5 extraction above it in the file).
**Impact:** Low. Function still exists, still extractable. ANVIL will `git grep` and find it.
**Fix:** Update §1 table.

---

### MINOR-B8-2: `_dedup_key` / `_mark_seen` line-number drift is -234

**File:** `TASK-B8-plan.md` §1 lines 40-41, §9 lines 299
**Evidence:** Plan says `_dedup_key` 4132-4172 and `_mark_seen` 4173-4183. Actual: **3898-3937** and **3939-3948**. Drift: -234 lines.
**Impact:** Low.
**Fix:** Update §1 and §9 tables.

---

### MINOR-B8-3: `_alert_content_dedup` / `_tg_content_dedup` — internal contradiction on whether they extract or stay

**File:** `TASK-B8-plan.md` §1 lines 42-43, §3e line 169, §4a line 189-193
**Evidence:**
- §1 lists both functions as dedup targets for extraction.
- §4a says "The `_mark_seen()`, `_alert_content_dedup()`, `_tg_content_dedup()` functions operate on instance-level caches (deque + set). These are tightly coupled to the SignalRouter class lifecycle (load/persist state, eviction). **They stay in signal_router.py.**"
- §3e line 169 then lists `_dedup_key` among functions to remove, but not `_alert_content_dedup`/`_tg_content_dedup` (it's not perfectly clear because the list isn't exhaustive — the sentence ends with a "..." implication).

The plan is inconsistent: §1 frames them as targets; §4a explicitly excludes them. If §4a is authoritative (recommended), §1 should re-label them as "inventory — NOT extracted (instance-state-bound)."

Also: **`_mark_seen` is bundled with `_alert_content_dedup`/`_tg_content_dedup` in §4a as "staying"**, but §1 and §3e seem to target it for extraction. Same ambiguity.

**Line drift verification for these:**
- `_alert_content_dedup` plan 1928-1947, actual **1707-1725** (drift -221)
- `_tg_content_dedup` plan 1948-1973, actual **1727-~1753** (drift -221)

**Impact:** Medium. This is an ambiguity ANVIL would have to resolve without guidance — do these functions extract with pure-decision versions (returning bool) and stay as mutator wrappers? Do they stay entirely? Do they extract whole? The plan cannot be implemented as-written.

**Fix:** FORGE must pick one policy for the three cache-mutator functions (`_mark_seen`, `_alert_content_dedup`, `_tg_content_dedup`) and state it unambiguously in §1, §3e, and §4a. Recommended: **keep all three in signal_router.py** per §4a's correct reasoning (cache state + TTL eviction + persistence are tightly coupled). Extract only `_dedup_key` (pure function, no state).

---

### MINOR-B8-4: `dedup_cache_size` config source not addressed

**File:** `TASK-B8-plan.md` §3b, §4a
**Evidence:** `_mark_seen` uses `self.cfg.dedup_cache_size` (signal_router.py:3942). If FORGE keeps `_mark_seen` in router per MINOR-B8-3 resolution, this is moot. If FORGE extracts it, the function needs the cache size injected as a parameter.
**Impact:** Low. One-line interface consideration.
**Fix:** Either explicitly keep `_mark_seen` in router, or specify the `dedup_cache_size` parameter in §3b's `make_dedup_key` signature.

---

### MINOR-B8-5: Plan §3a `classify_lifecycle_action` signature conflict with B5's already-shipped signature

**File:** `TASK-B8-plan.md` §3a line 94-96
**Evidence:** Plan proposes `def classify_lifecycle_action(summary_or_action: str) -> str` as top-level module function in `router.py`. B5 shipped `emitter.py:284` as `@staticmethod def classify_lifecycle_action(summary_or_action: str) -> str` inside `SignalEmitter`. Same signature, different location.

If B8 proceeds as plan-written, there will be TWO `classify_lifecycle_action` functions — one in `emitter.py` (currently called by all 3 router code paths) and one in `router.py` (unused duplicate). ANVIL would have to choose: delete emitter's version and re-route all 3 call sites, OR delete router.py's version before merging.

**Impact:** Medium. Symptom of STALE-B8-1. If FORGE adopts STALE-B8-1 Fix Option 1 (remove the 5 B5-moved functions from B8 scope), this contradiction disappears.

**Fix:** Implicit in STALE-B8-1 fix. Remove from §3a.

---

### MINOR-B8-6: Test file path `tests/test_router.py` may collide with existing conventions

**File:** `TASK-B8-plan.md` §2 line 83
**Evidence:** Current tests/ directory contains `test_b8_commentary_gate.py`, `test_preemit_filter.py`, `test_emitter.py` — the naming convention in this repo uses descriptive suffixes, not module-generic names. A file called `test_router.py` is ambiguous (which "router" — the decomposed module or the old SignalRouter class?).

Also note: `tests/test_b8_commentary_gate.py` **already exists** and covers the `_is_commentary_only_channel` function (per `tests/test_preemit_filter.py:122-147`). If FORGE's "CREATE tests/test_router.py" is intended to cover commentary gating, it would duplicate existing coverage.

**Impact:** Low. Naming nitpick plus potential test duplication.
**Fix:** §2 should either (a) rename to `tests/test_signal_router_extracted.py` or similar, and (b) either augment the existing `test_b8_commentary_gate.py` / `test_preemit_filter.py` for `_is_commentary_only_channel` coverage rather than duplicating it.

---

### MINOR-B8-7: Test spec §5 row `test_integration_dedup_via_router` under-specified

**File:** `TASK-B8-plan.md` §5 line 255
**Evidence:** "Full event through signal_router using router.py" — integration test with no fixtures, no input event shape, no expected DB state. ANVIL needs a concrete spec. Compare to the existing `tests/test_preemit_filter.py` pattern, which uses explicit fixtures and DB-ready mocks.
**Impact:** Low. FORGE's test specs have been integration-light across Phase B.
**Fix:** Specify: "Use in-memory sqlite3 with seeded ACTIVE signal row; fire a matching trader+ticker+direction event through `SignalRouter._route_*()`; assert the route returns `route='text_cross_channel_dedup'` (or equivalent) and no new INSERT occurred." Or explicitly defer to ANVIL with a note.

---

### MINOR-B8-8: Agent council §10 references "Meridian / Pilot" — not a current team member

**File:** `TASK-B8-plan.md` §10 line 315
**Evidence:** Per `/home/oinkv/forge-workspace/AGENTS.md`, FORGE's team is Anvil / Vigil / Guardian / OinkV / Mike. Meridian and Pilot are not listed. This appears to be a template artifact.
**Impact:** Low. Cosmetic.
**Fix:** Replace with "VIGIL / GUARDIAN" (for code-review and data-integrity sign-off after implementation) or remove the row entirely.

---

## 🟢 Additional Confirmations

- **CONFIRMED-B8-11:** B5 emitter extraction is a good architectural reference for B8 (clean module, no circular dependency, injected DB connection via `oink_db.connect_readonly`). B8 can follow the same pattern.
- **CONFIRMED-B8-12:** Inline DB dedup consolidation strategy (§3d) is sound for the 5 "simple" dedup query sites. All 5 follow the same pattern: `SELECT s.id FROM signals s JOIN traders t ... WHERE trader+ticker+direction+entry AND status IN ('ACTIVE', 'PENDING')`. Extracting as `router.is_duplicate_signal(conn, trader, ticker, direction, entry_price)` is legitimate DRY consolidation.
- **CONFIRMED-B8-13:** Connection-injection pattern §4b is correct and forward-compatible with oink_db's (already-merged) `.execute()/.fetchone()` duck-typed API.
- **CONFIRMED-B8-14:** §4d "post-B8 signal_router.py becomes thin orchestrator" is a valid end-state description, though specific LOC will depend on STALE-B8-1 resolution.
- **CONFIRMED-B8-15:** Rollback plan §7 is trivial (single-repo revert). Appropriate for this risk level.
- **CONFIRMED-B8-16:** Risk matrix §8 row "Consolidating 7 inline queries misses a variant: Medium probability" is well-calibrated — the A6 ghost closure site (3747) IS in fact a variant that the plan conflates. Risk item self-validating.

---

## Tally

| Category | Count |
|----------|-------|
| 🔴 CRITICAL | 4 (STALE-B8-1 five functions gone to emitter, STALE-B8-2 sqlite3 sites wrong, STALE-B8-3 pre-B5 header, STALE-B8-4 dependency claim) |
| 🟡 MINOR | 8 (MINOR-B8-1 `_is_commentary_only_channel` drift, MINOR-B8-2 `_dedup_key`/`_mark_seen` drift, MINOR-B8-3 cache-mutator internal contradiction, MINOR-B8-4 `dedup_cache_size` config, MINOR-B8-5 `classify_lifecycle_action` duplicate, MINOR-B8-6 test file naming, MINOR-B8-7 integration test under-spec, MINOR-B8-8 agent council template artifact) |
| 🟢 CONFIRMED | 16 |

---

## Top 3 Blockers

1. **🔴 STALE-B8-1: Five of ten B8 target functions are already in `emitter.py` (B5).** `_classify_lifecycle_action`, `_check_signal_state`, `_should_suppress_lifecycle`, `_mark_forwarded`, `_is_recently_forwarded` no longer exist in `signal_router.py`. The plan's §1 table misdirects ANVIL. **Fix:** Rewrite §1 + §3e to mark these ✅ DONE-IN-B5 and shrink B8 scope to `_is_commentary_only_channel`, `_dedup_key`, and the 6 inline DB dedup sites. LOC reduction target drops from ~600 to ~150-200.

2. **🔴 STALE-B8-2: "7 inline sqlite3 query sites" is wrong — there are 6, not 7; they now use oink_db (not raw sqlite3); and one is A6 ghost closure (read+write, not simple dedup).** Plan §1 line 46 and §9 enumerate pre-B1/pre-B5 coordinates that no longer apply. **Fix:** Re-grep against HEAD `2e345bb`; re-enumerate as 6 `with connect_readonly()/connect()` sites at lines 2014, 2089, 2833, 3375, 3674, 3747; split A6 ghost closure out as a distinct extraction target.

3. **🔴 STALE-B8-3: Plan header `Codebase Verified At: 2026-04-19T18:00Z (post-A8 merge 46154543)` is off by 7 commits and one major refactor (B5).** Every line-number citation in §1 and §9 drifted ~221–234 lines due to B5 alone. **Fix:** Re-anchor plan header to `2026-04-20T07:00Z (post-B5 merge 2e345bb)`, signal_router.py now 4,230 LOC (not 4,460), and re-scan line numbers.

---

## Ship-readiness

**NOT SHIP-READY — REVISE MAJOR.**

The plan's conceptual framing (extract decision-only functions, keep state mutators, consolidate DB dedup queries via connection injection) is architecturally sound and consistent with B5's already-shipped approach. However, the plan was drafted against a pre-B5 `signal_router.py` and has been overtaken by B5's own extraction, which moved 5 of B8's 10 target functions into a different module. The file inventory, LOC estimates, line numbers, and function-existence claims are all materially stale. ANVIL cannot implement B8 as written without first duplicating work B5 already did (if ANVIL follows the plan literally) or reverse-engineering which targets are still live (if ANVIL consults the codebase).

**Recommended action:** Revise B8 before ANVIL starts. Required fixes:
1. Re-anchor to HEAD `2e345bb` (post-B5).
2. Remove the 5 B5-moved functions from B8's target set; note them as ✅ DONE-IN-B5.
3. Resolve the `_mark_seen` / `_alert_content_dedup` / `_tg_content_dedup` internal contradiction (recommend: all three stay in router).
4. Re-enumerate the inline DB query sites (6, not 7; oink_db, not sqlite3; split A6 ghost closure out).
5. Recompute LOC reduction target (~150-200, not ~600).
6. Remove or soften the "B6+B7 dependency" claim — B8 targets are independent of parser extractions.

Once those six land, B8 is ship-ready. Estimated revision effort: 60-90 minutes of FORGE work. None require changing the core architectural intent of the plan.

---

*Hermes — OinkV fallback reviewer. "Half the scope is already done. The other half is where the real risk lives — the A6 ghost closure queries do not belong in a simple is_duplicate_signal() helper."*
