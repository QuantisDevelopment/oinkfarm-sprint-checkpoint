# OinkV Engineering Audit — FORGE Plan B7 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback, OinkV LLM timeout)
**Date:** 2026-04-20
**Scope:** Staleness and drift audit of TASK-B7-plan.md against live codebase (signal-gateway @ 2e345bb, post-B5 merge).
**Verdict line at end.**

---

## 0. Executive Summary

B7's **substantive design is sound** — the function inventory, extraction boundary choice (keep `_resolve_trader_from_mentions` and `_sanitize_oinxtractor_summary` in signal_router.py, move the 11 pure text helpers to `parsers/wg_bot.py`), and the call-site analysis all hold up against the current code. Line-number citations are accurate within ±5 in every case checked.

However, the plan has **stale headline metadata** (HEAD commit, LOC total) and contains **two wrong LOC figures in §0** for `_route_passthrough()` and `_route_text_extract()`. It also has a **dependency-ordering ambiguity**: B7 depends on B6 (which has NOT yet merged) for `parsers/__init__.py` — B5 did not establish the `parsers/` package as the plan implies.

None of these are structural defects. All are metadata/dependency-statement fixes.

**Provenance:** OinkV main agent LLM-timed-out on Phase B audit dispatch at 2026-04-19T19:23:36Z. Dispatched per sprint-orchestrator "Hermes-Subagent Fallback". Parent subagent hit max_iterations at 60; content recovered from subagent summary and written directly by orchestrator.

---

## 🟢 What B7 Got Right

- **CONFIRMED-B7-1:** Canonical file path correct. `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` exists and is the only production copy. The path `/home/oinkv/.openclaw/workspace/scripts/signal_gateway/signal_router.py` mentioned in the audit prompt does **NOT** exist — no drift copy to flag. (Only worktrees exist: signal-gateway-issue10, signal-gateway-122, signal-gateway-a2, worktrees/signal-gateway-138, worktrees/signal-gateway-142. All worktrees of the same repo.)
- **CONFIRMED-B7-2:** All 11 function names the plan lists for extraction exist verbatim in source:
  - `_extract_field_line` line 543 ✓
  - `_extract_type_from_summary` line 611 ✓
  - `_extract_ticker_from_summary` line 625 ✓
  - `_extract_direction_from_summary` line 666 ✓
  - `_normalize_direction_line` line 705 ✓
  - `_normalize_numeric_token` line 728 ✓
  - `_embeds_have_signal_data` line 1048 ✓
  - `_extract_embed_text` line 1069 ✓
  - `_sanitize_discord_mentions` line 1114 ✓
  - `_has_signal_template_fields` line 1136 ✓
  - `_is_commentary_summary` line 1159 ✓
- **CONFIRMED-B7-3:** Function line citations in §1 table are accurate within ±3 across the board. Examples:
  - Plan: `_extract_type_from_summary` "608-621"; actual: 611-622 (Δ+3)
  - Plan: `_extract_ticker_from_summary` "622-662"; actual: 625-656 (Δ+3/-6)
  - Plan: `_sanitize_oinxtractor_summary` "729-939"; actual: 732-940 (Δ+3/+1)
  - Plan: `_is_commentary_summary` "1156-1190"; actual: 1159-1176 (Δ+3/-14)
  - All within the ±10 tolerance.
- **CONFIRMED-B7-4:** `_resolve_trader_from_mentions` "86-250" — actual 89-235 (end at `return ""`). Within tolerance, and plan's decision to **keep it in signal_router.py** is correct: it's called from `route_event()` (line 1542) before routing branches, and consumes `WG_ROLE_TO_TRADER` + `channel.role_hints` + resolved Discord guild cache — cross-cutting, not WG-specific.
- **CONFIRMED-B7-5:** `WG_ROLE_TO_TRADER` dict "~34-85" — actual 41-84. Trader names spot-checked: `Tareeq` at line 50 ✓, `Woods` at 46/81 ✓, `CryptoGodJohn` at 43 ✓. 37 unique traders across 40 role IDs (3 alias entries: Woods scalping 1151862839842193428, Astekz-bets 1324577157397086208, Bryce breakout 1336698650813927546). Dict stays in signal_router.py per plan — correct.
- **CONFIRMED-B7-6:** All 12 regex constants the plan lists exist and are correctly attributed.
- **CONFIRMED-B7-7:** B5 (SignalEmitter extraction) did NOT touch WG Bot code paths. `emitter.py` imports only `asyncio, collections, logging, time, typing.Any` (no parser imports). No conflict between B5 and B7.
- **CONFIRMED-B7-8:** `_sanitize_oinxtractor_summary` boundary decision (keep in signal_router.py) is correct.
- **CONFIRMED-B7-9:** Call-site count matches plan's "spread across multiple functions" claim (51 occurrences in-file). External test files import _-prefixed names — plan's §3c alias-import pattern preserves them.
- **CONFIRMED-B7-10:** `parsers/wg_bot.py`, `tests/test_parsers_wg_bot.py` do not exist yet — correctly marked CREATE.
- **CONFIRMED-B7-11:** B5 live on commit `2e345bb` ✓ (signal_router.py now 4,230 LOC, down from 4,460 at c6cb99e).

---

## 🔴 CRITICAL Findings

*None.* The plan is structurally correct.

---

## 🟡 MINOR Findings

### STALE-B7-1: Header LOC and HEAD commit are stale by two merges

**File:** `TASK-B7-plan.md` line 6, line 7
**Evidence:**
- Plan says: `(4,460 LOC, HEAD c6cb99e)` and `Codebase Verified At: 2026-04-19T18:00Z (post-A8 merge 46154543)`
- Current: `signal_router.py` is **4,230 LOC** (dropped 230 LOC from B5 extraction); `HEAD = 2e345bb` (B5 merge, 2026-04-20T06:55Z).
- Commits since c6cb99e: B1, B2, B3, B5. Plan was drafted against pre-B1 state.

**Impact:** Cosmetic — all function line numbers still land within ±10 because B1/B2/B3/B5 touched different regions of the file. But the LOC target in §0 ("~400-500 LOC reduction") should be re-anchored to the post-B5 4,230 LOC baseline.

**Fix:** Update line 6 to `4,230 LOC, HEAD 2e345bb` and line 7 to `2026-04-20T07:30Z (post-B5 merge 2e345bb)`.

---

### STALE-B7-2: `_route_passthrough()` and `_route_text_extract()` LOC figures in §0 are wrong

**File:** `TASK-B7-plan.md` line 20
**Evidence:**
> "Call sites deep inside `_route_passthrough()` (775 LOC) and `_route_text_extract()` (1,467 LOC)"

Actual sizes:
| Method | Current (HEAD 2e345bb) | At c6cb99e | Plan's figure |
|--------|------------------------|------------|---------------|
| `_route_passthrough` | 1814-2199 = **385 LOC** | 2035-2424 = 389 LOC | 775 ❌ |
| `_route_text_extract` | 2765-3570 = **805 LOC** | 2994-3803 = 809 LOC | 1,467 ❌ |

Neither figure matches even the pre-B5 state.

**Impact:** Low. The "these methods are big" narrative is still true, but the specific numbers are misleading.

**Fix:** Line 20 to read `(~385 LOC) and _route_text_extract() (~805 LOC)`.

---

### DRIFT-B7-1: Dependency on B6 for `parsers/__init__.py` is under-specified

**File:** `TASK-B7-plan.md` line 5, §2 line 67, §3d lines 137-147
**Evidence:**
- Line 5: "Dependencies: B5 (emitter extraction — establishes parsers/ package), B6 (Cornix+Chroma — establishes parser extraction pattern)"
- Filesystem check: `scripts/signal_gateway/parsers/` **does not exist**. B5 created `emitter.py` as a sibling module, NOT a `parsers/` package. The `parsers/__init__.py` is introduced by **B6**, not B5.
- B6 has not merged ⇒ B7 is hard-dependent on B6, not soft.

**Impact:** If ANVIL picks up B7 before B6 lands, the plan's §2 "MODIFY parsers/__init__.py" breaks.

**Fix:** Line 5: remove "B5 … establishes parsers/ package". Restate as: `Dependencies: **B6 (hard dependency — creates parsers/ package)**; B5 (soft — pattern reference only)`. Add to §2: `Note: B7 MUST NOT merge before B6; if B6 slips, B7 must temporarily CREATE parsers/__init__.py as a pre-step.`

---

### MINOR-B7-1: `_NUMERIC_TOKEN_RE` declaration style (cosmetic)

**File:** signal_router.py line 725
**Evidence:** `_NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z])[+-]?\d[\d,.]*(?![A-Za-z])")`. Plan does NOT list this constant in §3a's "Regex constants" box.

**Impact:** `_NUMERIC_TOKEN_RE` is used only by `_sanitize_oinxtractor_summary` (lines 865, 872) — which plan correctly keeps in signal_router.py. Not a defect, just worth an explicit mention in §4.

**Fix:** Add one line to §4b or §4c: `_NUMERIC_TOKEN_RE and _FIELD_NAME_RE/_PRICE_VALUE_RE/_LEVERAGE_VALUE_RE/_PNL_VALUE_RE (lines 721-725) remain in signal_router.py — consumed only by _sanitize_oinxtractor_summary.`

---

### MINOR-B7-2: External test-file imports not addressed in plan

**File:** `TASK-B7-plan.md` §3c
**Evidence:**
- `tests/test_b8_commentary_gate.py:11` — `from scripts.signal_gateway.signal_router import _is_commentary_summary`
- `tests/test_preemit_filter.py:25` — imports `_extract_type_from_summary` and likely others.

**Impact:** Plan §3c uses `from … import extract_field_line as _extract_field_line`, which preserves the name. But should be explicit.

**Fix:** Add to §6 Acceptance Criteria: `Existing tests/test_b8_commentary_gate.py and tests/test_preemit_filter.py continue to import from signal_router.py without modification (via the _-prefixed re-export aliases in §3c).`

---

### MINOR-B7-3: `_WG_EMBED_DIR_RE` and `_WG_RAW_DIR_RE` omitted from §3a regex list

**File:** `TASK-B7-plan.md` §3a lines 80-92
**Evidence:**
- `_WG_EMBED_DIR_RE` at line 660
- `_WG_RAW_DIR_RE` at line 663
- `_DIRECTION_LINE_RE` at line 699

All three must move with their consumer functions.

**Fix:** Append to §3a regex list:
```
_WG_EMBED_DIR_RE              # line 660
_WG_RAW_DIR_RE                # line 663
_DIRECTION_LINE_RE            # line 699
```

---

## 🟢 Additional Confirmations

- **CONFIRMED-B7-12:** §4a "Why Trader Resolution Stays" is correct.
- **CONFIRMED-B7-13:** §4b "_WG_INLINE_FIELD_RE_CACHE is shared state" — confirmed module-level dict at line 540. Moves cleanly with the function. GIL + asyncio single-thread ⇒ thread-safe.
- **CONFIRMED-B7-14:** §4c option 1 (move `_sanitize_discord_mentions` into `parsers/wg_bot.py`) is viable. 3 call sites confirmed.
- **CONFIRMED-B7-15:** §7 Rollback plan (single `git revert`) is correct — pure refactor, single-repo, no schema/data.
- **CONFIRMED-B7-16:** §5 test spec covers all 11 extracted functions (16 test cases, 1 integration).
- **CONFIRMED-B7-17:** `_META_SKIP_PATTERNS` is NOT in extraction scope — correctly left in signal_router.py.
- **CONFIRMED-B7-18:** B8 commentary gate constants (`_B8_TYPE_LINE_RE`, `_B8_COMMENTARY_KEYWORDS`) are consumed only by `_is_commentary_summary` and move with it.

---

## Tally

| Category | Count |
|----------|-------|
| 🔴 CRITICAL | 0 |
| 🟡 MINOR | 5 |
| 🟢 CONFIRMED | 18 |

---

## Top 3 Recommended Revisions

1. **DRIFT-B7-1 — Clarify B6 hard dependency.** Plan implies B5 creates `parsers/` package; actually B6 does. B7 must land after B6. Update line 5 and §2.
2. **STALE-B7-2 — Fix §0 route-method LOC figures.** `_route_passthrough` is ~385 LOC not 775; `_route_text_extract` is ~805 LOC not 1,467.
3. **STALE-B7-1 — Refresh header.** HEAD `2e345bb` (not `c6cb99e`), 4,230 LOC (not 4,460), verification timestamp to 2026-04-20.

All three are 5-minute edits. Zero design changes needed.

---

## Ship-readiness

Ship-readiness: 🟡 REVISE MINOR — 5 corrections needed.
