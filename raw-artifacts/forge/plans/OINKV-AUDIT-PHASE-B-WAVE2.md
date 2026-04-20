# OinkV Staleness Audit — Phase B Wave 2 (B6, B7, B8)

**Date:** 2026-04-20 (CEST 07:35)
**Provenance:** ⚠️ **Hermes-subagent fallback** (OinkV LLM timeout history per prior cycles)
**Auditor coverage this cycle:** B6, B7, B8 (3 of 5 Wave 2 plans)
**Deferred:** B9, B12 (both 🔴 CRITICAL and B4-gated — safe to defer until B4 ships)

---

## Provenance note for Mike

OinkV has repeatedly hit `FailoverError: LLM request timed out` on multi-plan staleness audits (verified on Wave 1 Phase B audits for B1/B2/B3). Per the `oinkfarm-sprint-orchestrator` skill, the orchestrator falls back to 3 parallel Hermes `delegate_task` subagents. Each subagent performs the same rubric as a full OinkV audit (file existence, line-number verification, function-name verification, dependency ordering, cross-reference with recent merges). Output quality is comparable to OinkV's direct output.

This consolidated summary is the orchestrator's voice — reading across the three sub-audits for FORGE consumption.

---

## Per-plan verdicts

| Plan | Tier | Verdict | Critical | Minor | Recommended Action |
|------|------|---------|----------|-------|--------------------|
| **B6** Cornix+Chroma parser extraction | 🟡 STANDARD | 🟡 **REVISE MINOR** (3) | 1 (STALE-B6-1 call-site attribution) | 6 | FORGE ~15-20 min revision |
| **B7** WG Bot parser extraction | 🟡 STANDARD | 🟡 **REVISE MINOR** (5) | 0 | 5 | FORGE ~15 min revision |
| **B8** Router extraction (classify + dedup + suppress) | 🟡 STANDARD | 🔴 **REVISE MAJOR** (4) | 4 (B5 absorbed 5 target functions) | 8 | **FORGE ~60-90 min rework** |

## Cross-cutting findings

### 1. All three plans are stale at the header (~230 LOC + 4 merges)

All three plans pin to HEAD `c6cb99e` (A6 merge, pre-B1). Current signal-gateway HEAD is `2e345bb` (B5 merge). signal_router.py is **4,230 LOC**, down from 4,460 at plan drafting. Every plan header needs this metadata refresh.

### 2. B5's extractions rewrote the landscape B8 was drafted against

B5 (SignalEmitter extraction) moved 5 of the 10 functions B8 planned to extract:
- `_classify_lifecycle_action`
- `_check_signal_state`
- `_should_suppress_lifecycle`
- `_mark_forwarded`
- `_is_recently_forwarded`

B8 as written is ~50% obsolete. It cannot be ANVIL-ready until it's rewritten against the post-B5 signal_router.py. This is the biggest Wave 2 blocker.

### 3. B6 and B7 are structurally sound — but B7 must land AFTER B6

B6 creates the `parsers/` package. B7's plan says it depends on "B5 establishes parsers/ package" — incorrect. B5 created a sibling `emitter.py`, not a package. B7 must hard-depend on B6, or else pre-create `parsers/__init__.py` as a self-contained step.

### 4. B6's worst finding: wrong call-site attribution for Cornix

B6 §1 says Cornix is called from `_route_passthrough (~line 2050-2070)`. Actually both parsers are called from `_route_text_extract` (current lines 2783 and 2923). This error existed at the plan's pinned commit too — not staleness, a plain mistake. Without the fix, ANVIL's integration tests in B6 §5 would never exercise the extracted parser.

## Handoff to FORGE

**Recommended action order:**

1. **B8 rewrite (HIGHEST priority).** The plan's target function list is now wrong. FORGE should re-examine signal_router.py at `2e345bb`, rebuild the function inventory from scratch, recompute the LOC target from ~600 → ~150-200, and re-enumerate dedup sites (reality: 6 sites using `oink_db.connect_*`, not 7 raw sqlite3). Also resolve the §1-vs-§4a contradiction on whether cache-mutator helpers get extracted.

2. **B6 corrections (quick).** Fix §1 and §5 Cornix call-site attribution (move from `_route_passthrough` to `_route_text_extract`). Re-anchor header to `2e345bb` / 4,230 LOC. Tighten function-end line numbers (several overshoot by 22-56 LOC; 56-line overshoot would drag `_FORCE_BLOCK_BASES` asset-gate frozenset into `parsers/chroma.py`). Correct LOC-reduction target ~250 → ~150.

3. **B7 corrections (quick).** Fix B6-dependency wording (B7 hard-depends on B6, not B5). Fix §0 route-method LOC figures (385 / 805, not 775 / 1,467). Add test-import preservation to acceptance criteria. Add 3 direction regexes to the "move with consumer" list. Refresh header.

**Recommended execution sequence:**

| Order | Task | Gate |
|-------|------|------|
| 1 | FORGE revises B6 and B7 (both "🟡 REVISE MINOR", ~30 min total) | |
| 2 | FORGE **rewrites** B8 against post-B5 signal_router.py | |
| 3 | ANVIL Phase 0 on B6 | B6 revised |
| 4 | ANVIL Phase 0 on B7 | B6 merged + B7 revised |
| 5 | ANVIL Phase 0 on B8 | B6+B7 merged + B8 rewritten |

The orchestrator's next action (this cron cycle): A2A FORGE with this summary so revisions can start in parallel with B5 canary.

---

## Deferred to next cycle

- **B9** (🔴 CRITICAL, W1 Immutable signal records on PostgreSQL) — hard-blocked on B4 (PostgreSQL cutover, currently Mike-gated). No urgency to audit until B4 approves.
- **B12** (🔴 CRITICAL, Redis Streams transport) — depends on B4 + B8. Same deferral logic.

Auditing these now would run against a plan surface Mike may restructure via B4 approval decisions.

---

## Files produced this cycle

- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B6.md` (19.5 KB)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B7.md` (10.9 KB) — written directly by orchestrator from subagent summary (subagent hit max_iterations before final write, per skill's iteration-cap recovery pattern)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B8.md` (26.5 KB)
- this file
