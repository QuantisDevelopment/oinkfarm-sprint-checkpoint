# OinkV Engineering Audit — FORGE Plan B6 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback, OinkV LLM timeout)
**Date:** 2026-04-20
**Scope:** Staleness and line-citation accuracy audit of `TASK-B6-plan.md` (Cornix + Chroma deterministic-parser extraction from `signal_router.py`)
**Verdict (preview):** B6 is **architecturally sound** and technically straightforward. The extraction targets (`_try_cornix_parse`, `_try_chroma_parse` + their regex constants) still exist, are still pure functions, and have NOT been disturbed by the B1/B2/B3/B5 merges that landed after the plan was drafted. However, the plan has **one 🔴 CRITICAL factual error** (wrong call-site attribution — Cornix is NOT called from `_route_passthrough`) and several 🟡 line-number drift items stemming from the plan pinning commit `c6cb99e` while current `main` is `2e345bb` (7 merges ahead). None of the drift blocks implementation, but the call-site error will confuse ANVIL.

**Provenance:** OinkV `main` agent hitting LLM timeouts on Phase B plan audits; Mike dispatched Hermes subagent via `delegate_task` per sprint-orchestrator "Hermes-Subagent Fallback" section.

---

## 🟢 What B6 Got Right (credit to FORGE)

- **CONFIRMED-B6-1:** Canonical file path `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` ✓ — file exists, 4230 LOC (post-B5). **No DRIFT copy** at `/home/oinkv/.openclaw/workspace/scripts/signal_gateway/signal_router.py` — that directory does not exist on the VM. The signal-gateway repo is the sole canonical for this file (confirmed prior in OINKV-AUDIT-PHASE-B-B1.md §CONFIRMED-B1-4 via systemctl inspection).
- **CONFIRMED-B6-2:** Function `_try_cornix_parse(text: str) -> str | None` exists at `signal_router.py:254` with the exact signature the plan claims (plan §1 line 27).
- **CONFIRMED-B6-3:** Function `_try_chroma_parse(text: str, author_name: str = "") -> str | None` exists at `signal_router.py:311` with the exact signature the plan claims (plan §1 line 41).
- **CONFIRMED-B6-4:** Cornix regex constant count is **3** — `_CORNIX_TICKER_RE` (line 244), `_CORNIX_TARGET_RE` (line 248), `_CORNIX_SL_RE` (line 249). Matches plan §1 lines 29-31. ✓
- **CONFIRMED-B6-5:** Chroma regex constant count is **8** — `_CHROMA_HEADER_RE` (293), `_CHROMA_CC_RE` (297), `_CHROMA_ENTRY_RE` (298), `_CHROMA_TP_RE` (299), `_CHROMA_SL_RE` (300), `_CHROMA_CLOSED_AT_RE` (301), `_CHROMA_CLOSE_REASON_RE` (302), `_CHROMA_UPDATE_RE` (305). Matches plan §1 line 43 exactly. ✓
- **CONFIRMED-B6-6:** Both parsers ARE pure functions today. No DB access, no network, no class-instance access, no logging. Plan §4a "pure function guarantee" claim is accurate and already true. ✓
- **CONFIRMED-B6-7:** B6 target paths that SHOULD NOT yet exist:
  - `/home/oinkv/signal-gateway/scripts/signal_gateway/parsers/` — ❌ absent (correct; B6 will create).
  - `/home/oinkv/signal-gateway/tests/test_parsers_cornix.py` — ❌ absent (correct; B6 will create).
  - `/home/oinkv/signal-gateway/tests/test_parsers_chroma.py` — ❌ absent (correct; B6 will create).
- **CONFIRMED-B6-8:** B5 extracted `SignalEmitter` into `scripts/signal_gateway/emitter.py` (commit `2e345bb`, 2026-04-20 06:55). `emitter.py` contains **zero references** to `cornix`, `chroma`, `_CORNIX`, `_CHROMA`, or `try_parse` — confirmed via `grep -E "cornix|chroma|try_parse|_CORNIX|_CHROMA" emitter.py` → 0 matches. **No B5/B6 overlap**. B6 is free to proceed.
- **CONFIRMED-B6-9:** B5 dependency noted in plan line 5 ("B5 emitter extraction — establishes extraction pattern") is already satisfied — B5 merged 2026-04-20 06:55. The import precedent in `signal_router.py:34` (`from .emitter import SignalEmitter`) gives ANVIL a stylistic template for parsers.
- **CONFIRMED-B6-10:** Plan §4d grep claim is substantively correct — external consumers of `_try_cornix_parse` / `_try_chroma_parse` are zero outside `signal_router.py`. Only stray reference is `tests/test_passthrough.py:4` — **a comment**, not a live import: `# Import the router module to access _try_cornix_parse for comparison`. No live external consumer breakage. ✓
- **CONFIRMED-B6-11:** Current call sites inside `signal_router.py` (the ones B6 will preserve via alias import):
  - Line **2783**: `cornix_summary = _try_cornix_parse(raw_content)` — inside `_route_text_extract` (def at line 2765).
  - Line **2923**: `chroma_summary = _try_chroma_parse(raw_content, _author)` — inside `_route_text_extract`.
  - These are the only two call sites. Plan's aliasing strategy (`import … as _try_cornix_parse`) preserves them without rewrites. ✓
- **CONFIRMED-B6-12:** Plan §4c "regex constants remain module-private with `_` prefix" is the right call — matches Python convention and B5's emitter-extraction style.
- **CONFIRMED-B6-13:** Plan §7 (Rollback) is realistic — B6 is a pure refactor of stateless text transformations; a single `git revert` of the B6 merge commit fully restores prior state, unlike B1's cross-repo reverts.
- **CONFIRMED-B6-14:** Plan §5 test matrix covers the four Chroma action branches (`closed`, `opened`, `updated`, `cancelled`) and the two Cornix direction paths (long-below-SL, short-above-SL). Matches the branch structure of the actual code in `_try_chroma_parse` (lines 325, 351, 367, 386) and `_try_cornix_parse` (lines 270-273). ✓

---

## 🔴 CRITICAL Findings

### STALE-B6-1: Plan §1 "Call Sites" attributes the Cornix call to `_route_passthrough` — this is FACTUALLY WRONG in both the pinned commit AND current main

**File:** `TASK-B6-plan.md` lines 51-63 ("Call Sites" subsection)

**Plan asserts (line 56):**
> `# In _route_passthrough (~line 2050-2070):`
> `cornix_summary = _try_cornix_parse(content)`

**Evidence (current main `2e345bb`, signal_router.py):**
- `_route_passthrough` is defined at line **1814**, not 2050. The function body runs from 1814 to ~2198.
- Lines 2050-2070 (the plan's claimed range) contain the `_embeds_have_signal_data` / `_extract_embed_text` fallback logic **inside `_route_passthrough`**, but **no call to `_try_cornix_parse`**. Verified:
  ```
  awk 'NR>=1814 && NR<=2199' signal_router.py | grep -E 'cornix|chroma|_try_'
  → 1 hit: comment only ("Used for WG Cornix-format channels …")
  ```
- The real Cornix call site is line **2783** — inside `_route_text_extract` (def at 2765), not `_route_passthrough`.

**Verified against the plan's pinned commit too (`c6cb99e`):**
- At c6cb99e, `_route_passthrough` was at line 2035 and `_route_text_extract` at 2994. `_try_cornix_parse(raw_content)` was called at line 3012 inside `_route_text_extract`. **No cornix call existed in `_route_passthrough` at c6cb99e either.**
- So this error is not staleness — it's a factual mistake that was wrong the day FORGE wrote the plan.

**Impact:** **Medium-to-high.** ANVIL reads plan §1 to understand the extraction scope and verify that the post-refactor behavior preserves call-site contracts. If ANVIL trusts the plan and searches `_route_passthrough` for the parser hook, ANVIL will spend cycles chasing a ghost and may mis-wire the alias import. More dangerously, §5 acceptance test "test_signal_router_uses_extracted — Run `_route_passthrough` with Cornix text" (plan line 195) will **never hit the extracted parser** because `_route_passthrough` does not invoke it. That integration test as written is a false-positive guarantee.

**Fix:** Rewrite §1 "Call Sites":
```
Call Sites (both inside _route_text_extract):
- signal_router.py:2783 → cornix_summary = _try_cornix_parse(raw_content)
- signal_router.py:2923 → chroma_summary = _try_chroma_parse(raw_content, _author)
_route_text_extract is defined at line 2765; _route_passthrough (line 1814) does NOT call these parsers.
```
And rewrite §5 integration test to exercise `_route_text_extract`, not `_route_passthrough`.

---

## 🟡 MINOR Findings

### STALE-B6-2: Plan pins HEAD `c6cb99e` (4,460 LOC); current main is `2e345bb` (4,230 LOC) — 7 merges stale

**File:** `TASK-B6-plan.md` line 6 (`Canonical file: ... 4,460 LOC, HEAD c6cb99e`) and line 234.

**Evidence:**
- `cd /home/oinkv/signal-gateway && git rev-parse HEAD` → `2e345bb6c14b4a02057e56218b038cb0da0cb2e5`.
- `wc -l scripts/signal_gateway/signal_router.py` → **4230 lines** (not 4460).
- Commits merged since c6cb99e (the plan's pinned commit):
  1. `f1dca60` feat(B1): database abstraction layer + 5 migrations
  2. `963fa3e` fix(B1): derive busy_timeout (R1 patch)
  3. `b0f0254` Merge anvil/B1-db-abstraction
  4. `df8112d` Task B2: re-vendor oink_db.py with PostgreSQL backend
  5. `07940ce` B3: Re-vendor oink_db.py + ghost closure fix
  6. `c75fb92` B3 R2: executemany generator fix
  7. `cc70e5b` Merge B3
  8. `2e345bb` **B5: extract SignalEmitter from signal_router** ← current HEAD

- B5 removed ~230 LOC from signal_router.py (SignalEmitter class + forwarding/dedup/dispatch logic). B1/B2/B3 only touched the 7 `with _sq3.connect(...)` blocks (line numbers shifted around ingest methods but regex/parser region 240-396 was unchanged).

**Impact:** Low for the extraction correctness (Cornix/Chroma region is untouched by the 8 intervening merges), but medium for ANVIL's confidence when it opens the file and sees line 251 is a blank line rather than a regex constant. All B6 line-number citations in §1 and §3 are anchored to the stale commit and will not match ANVIL's working copy.

**Fix:** Update line 6 to `HEAD 2e345bb, 4,230 LOC (post-B5)`. Re-run `grep -n` on all function/regex names (see CONFIRMED-B6-2..5 for current numbers). Revised §1 line citations should be:
- Cornix regexes: `signal_router.py:244-251` (was ~240-250 in plan).
- `_try_cornix_parse`: `signal_router.py:254-285` (plan said 251-307).
- Chroma regexes: `signal_router.py:293-308` (was ~290-308 in plan).
- `_try_chroma_parse`: `signal_router.py:311-396` (plan said 308-452).

---

### STALE-B6-3: Plan's end-of-function line numbers overshoot the real range by 20-56 LOC

**File:** `TASK-B6-plan.md` lines 26, 40, 88, 101.

**Evidence:**
- Plan line 26: "Location: signal_router.py lines 251-307" for `_try_cornix_parse`. Actual span: **def line 254 → last `return` line 285**. Plan's endpoint (307) overshoots by **22 lines**.
- Plan line 40: "Location: signal_router.py lines 308-452" for `_try_chroma_parse`. Actual span: **def line 311 → last `return None` line 396**. Plan's endpoint (452) overshoots by **56 lines**. Lines 397-420 in the current file are the `_FORCE_BLOCK_BASES` block-list frozenset and B3/B4 asset-gate code (section comment at line 399: "── B3/B4: Live Kraken asset-universe gate ──").
- At c6cb99e the same holds: `_try_chroma_parse` ended at line 393 (`return None`), not 452. The plan's 452 endpoint was wrong the day it was written.

**Impact:** Low. ANVIL will locate both functions by name via grep and identify the true boundaries in seconds. But if ANVIL trusts the line ranges literally for an automated extraction script (e.g., `sed -n '251,307p'`), it would under-capture Cornix (miss lines 285-307 of comments/whitespace, which is fine) and — more seriously — **over-capture Chroma by ~56 LOC** and drag the `_FORCE_BLOCK_BASES` frozenset + asset-gate section into `parsers/chroma.py`, breaking the "pure function, no asset-gate dependencies" guarantee. Mechanical extraction risk is real here.

**Fix:** Tighten §1 and §3 line ranges to the real function boundaries (254-285 and 311-396), OR replace line numbers with name-based anchors ("from `def _try_cornix_parse` through its sole `return \"\\n\".join(lines)`").

---

### STALE-B6-4: Plan's claimed call-site line numbers (~2050 for cornix, ~3100-3120 for chroma) don't match either c6cb99e OR current main

**File:** `TASK-B6-plan.md` lines 56, 61.

**Evidence:**
| Parser | Plan claim | c6cb99e actual | 2e345bb actual |
|--------|------------|----------------|-----------------|
| cornix | `_route_passthrough ~2050-2070` | `_route_text_extract:3012` | `_route_text_extract:2783` |
| chroma | `_route_text_extract ~3100-3120` | `_route_text_extract:3154` | `_route_text_extract:2923` |

The chroma line number is off by ~50 in BOTH directions depending on which commit you anchor to. The cornix attribution is wrong regardless of commit (see STALE-B6-1).

**Impact:** Low in isolation (ANVIL will grep), but compounds with STALE-B6-1. The overall §1 "Call Sites" subsection has zero trustworthy line numbers.

**Fix:** Merge with STALE-B6-1 fix — replace the whole "Call Sites" block with accurate function-containing names and current line numbers.

---

### STALE-B6-5: "LOC reduction target: ~250" in plan §0 is optimistic by ~60-90 LOC

**File:** `TASK-B6-plan.md` line 16 ("LOC reduction target: ~250 LOC from signal_router.py").

**Evidence:** Realistic count of extractable lines from current `signal_router.py`:
- Cornix section (comment header at 242 + regexes at 244-251 + function at 254-285 + trailing blank) ≈ **45 LOC**.
- Chroma section (comment header at 288-291 + regexes at 293-308 + function at 311-396 + trailing blanks) ≈ **110 LOC**.
- **Total extraction ≈ 155 LOC**. Then B6 *adds back* 2 import lines (`from signal_gateway.parsers import ...`). **Net reduction ≈ 150-155 LOC.**

Plan's "~250" is ~60-90 LOC too optimistic. Matches neither the c6cb99e view nor current main.

**Impact:** Cosmetic. ANVIL won't fail the PR over LOC-target mismatch, but Mike's sprint-level LOC-reduction dashboard (God-Object decomposition tracker) will show B6 delivering less than advertised.

**Fix:** Update §0 line 16 to `LOC reduction target: ~150 LOC from signal_router.py`.

---

### STALE-B6-6: Import style in §3d diverges from B5 precedent (absolute vs relative)

**File:** `TASK-B6-plan.md` §3d lines 125-128.

**Plan proposes:**
```python
from signal_gateway.parsers import try_cornix_parse as _try_cornix_parse
from signal_gateway.parsers import try_chroma_parse as _try_chroma_parse
```

**B5 precedent (current signal_router.py line 34):**
```python
from .emitter import SignalEmitter
```

All four sibling-package imports in the current file use the relative `.` form (lines 32-35: `from .alert_channel …`, `from .board_parser …`, `from .emitter …`, `from .reconciler …`). Plan's absolute `signal_gateway.parsers` form is valid but stylistically inconsistent with the module's own convention.

**Impact:** Cosmetic / code-style. Imports will work either way. VIGIL may flag inconsistency at review time.

**Fix:** Either (a) change §3d to `from .parsers import try_cornix_parse as _try_cornix_parse, try_chroma_parse as _try_chroma_parse` to match siblings, or (b) note explicitly in §3d that absolute is preferred here and explain why.

---

### STALE-B6-7: §9 "Evidence" line-range claims repeat the overshoots

**File:** `TASK-B6-plan.md` §9 Evidence lines 235-237.
- Line 235: "Cornix parser: lines 240-307 (pure function, 3 regexes)" — actual 242-285, see STALE-B6-3.
- Line 236: "Chroma parser: lines 285-452 (pure function, 8 regexes)" — actual 288-396, see STALE-B6-3.
- Line 237: "Call sites: _route_passthrough (~line 2050), _route_text_extract (~line 3100)" — see STALE-B6-1, STALE-B6-4.

**Impact:** Evidence section cross-references the §1 errors. If §1 is corrected, §9 must be updated in lockstep for the plan to be internally consistent.

---

## 🟢 Additional Confirmations

- **CONFIRMED-B6-15:** Plan's rename of public API from `_try_*_parse` → `try_parse` (plan §3a, §3b) is idiomatic Python (module name `parsers.cornix` + function name `try_parse` avoids the redundancy `parsers.cornix.try_cornix_parse`). ✓
- **CONFIRMED-B6-16:** `parsers/__init__.py` design (plan §3c) is a clean re-export pattern matching Python stdlib conventions. ✓
- **CONFIRMED-B6-17:** Plan §2 file-modify table is complete for this scope (6 files: 3 CREATE parser, 2 CREATE test, 1 MODIFY router). No missing files for the narrow extraction scope. ✓
- **CONFIRMED-B6-18:** Plan §8 risk assessment is honest — pure-function extraction is genuinely LOW risk. Zero schema touches, zero financial-hotpath touches, zero DB writes. ✓
- **CONFIRMED-B6-19:** Dependencies section correctly names B5 as the precedent. B5 is already merged (2e345bb), so B6 is unblocked from a dependency standpoint; plan §10 "DRAFT — pending OinkV audit + agent council" is the only gate remaining.
- **CONFIRMED-B6-20:** B6's plan does NOT claim to extract anything B5 already extracted. SignalEmitter extraction and parser extraction are orthogonal — confirmed by reading `emitter.py:1-30` (owns background-task dispatch, forwarding dedup, pre-emit filter — no text-parsing).

---

## Tally

| Category | Count |
|----------|-------|
| 🔴 CRITICAL | 1 (STALE-B6-1 — wrong call-site attribution for Cornix) |
| 🟡 MINOR | 6 (stale commit pin, function-range overshoots, call-site line-num drift, inflated LOC target, import-style drift, evidence §9 mirror errors) |
| 🟢 CONFIRMED | 20 |

---

## Top blockers before ANVIL starts

1. **🔴 STALE-B6-1 — Rewrite §1 "Call Sites" subsection.** Both parsers are called from `_route_text_extract`, NOT `_route_passthrough`. The integration-test design in §5 also inherits this error. FORGE must correct both §1 (the factual claim) and §5 (the test target) before ANVIL begins.
2. **🟡 STALE-B6-2 — Re-pin the plan to `2e345bb` and update the 4,460 → 4,230 LOC figure.** Run a re-grep of all line citations in §1, §3, and §9 against current main. 10-minute fix. Without this, ANVIL sees mismatches in every code-pointer in the plan.
3. **🟡 STALE-B6-3 — Tighten function-end line numbers.** The +56-LOC overshoot on `_try_chroma_parse` (plan claims ends at line 452, actual 396) is actively dangerous if ANVIL uses line-range extraction mechanically — it would pull the `_FORCE_BLOCK_BASES` asset-gate frozenset into `parsers/chroma.py`, which is absolutely not pure-function content. FORGE should replace numeric line ranges with name-based anchors ("from `def` through the last `return`").

---

## Ship-readiness

**Ship-readiness: 🟡 REVISE MINOR — plan needs 3 corrections before ANVIL starts.**

The corrections are:
1. Fix §1 "Call Sites" — Cornix + Chroma are BOTH called from `_route_text_extract`, not `_route_passthrough`; update §5 integration test accordingly. *(STALE-B6-1, CRITICAL in content but 5-minute textual fix.)*
2. Re-anchor the plan to HEAD `2e345bb` / 4,230 LOC and refresh all numeric line citations in §1, §3, and §9. *(STALE-B6-2, STALE-B6-4, STALE-B6-7.)*
3. Tighten the Cornix (254-285) and Chroma (311-396) function-end line numbers, or replace with name-based anchors, to prevent mechanical over-extraction. *(STALE-B6-3.)*

Everything else in the plan is sound: the parsers genuinely are pure functions, the regex-constant inventory is exact (3 + 8 = 11 constants), B5 did not extract any parser code, no external consumers exist, target files legitimately don't yet exist, dependency ordering is satisfied (B5 merged 2026-04-20), and the rollback plan is realistic for a pure-refactor task. Estimated FORGE revision time: **15-20 minutes**. The core design needs no change.

Recommended action: FORGE amends the plan in-place, bumps version from v1 to v1.1 with a "Post-B5 re-anchor + call-site correction" changelog entry, then ANVIL proceeds. This is by far the cleanest plan in the Phase B queue once §1 is corrected.
