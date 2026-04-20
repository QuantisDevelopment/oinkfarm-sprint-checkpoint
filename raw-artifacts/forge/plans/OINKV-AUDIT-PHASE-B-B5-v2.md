# OinkV Engineering Audit — FORGE Plan B5 v2

**Auditor:** OinkV  
**Date:** 2026-04-20 05:xx CEST  
**Scope:** `/home/oinkv/forge-workspace/plans/TASK-B5-plan.md`  
**Tier:** 🟡 STANDARD — signal_router emitter extraction / single-repo refactor

---

## 0. Audit Header

| Item | Value |
|------|-------|
| Plan under review | `/home/oinkv/forge-workspace/plans/TASK-B5-plan.md` |
| Size | 22,344 bytes |
| mtime | 2026-04-20 05:18 CEST |
| Revision | v2 |
| Canonical target | `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` |
| Verified HEAD | `cc70e5ba` |
| Verified LOC | signal_router 4,451, discord_notify 1,091, extractor 512, board_parser 352, oinxtractor_client 479 |
| Verified notifier inventory | 36 fire-and-forget dispatch sites across 6 notifier methods; 38 total notifier calls including `.stats` and `.close` |

### Re-audit summary

v2 resolves the prior phantom-reference and API-undercoverage problems. The decomposition boundary is now materially cleaner and implementable. I found one residual correctness issue in the acceptance criteria wording, but it does not require redesign.

---

## 1. Findings Map

| Prior finding | Prior severity | v2 verdict | Evidence |
|---|---:|---|---|
| Phantom `_forward_raw_to_signals()` | 🔴 CRITICAL | ✅ FIXED | v2 now references `_route_passthrough()` at line 2035; live grep confirms `_forward_raw_to_signals` does not exist |
| Emitter API covered only 3 of 6 notifier methods | 🔴 CRITICAL | ✅ FIXED | v2 expands to 6 `emit_*` methods covering signal, lifecycle, raw, alert, reconciler, pipeline-event surfaces |
| `oinxtractor_client.py` LOC undercount | 🟡 MAJOR | ✅ FIXED | v2 uses 479 LOC and recomputes extracted total to 2,434 |
| `_should_suppress_lifecycle` / `_check_signal_state` dependency inversion | 🟡 MAJOR | ✅ FIXED | v2 explicitly moves both into emitter together |
| LOC savings target unrealistic | 🟡 MAJOR | ✅ FIXED | v2 relaxes acceptance to 150-250 LOC |
| Minor line drifts / stale HEAD / architecture wording | 🟠 MINOR | ✅ FIXED | line numbers and HEAD updated to post-B3 state |

---

## 2. New findings in v2

### N1 — Acceptance criterion count mismatch: plan says 36 dispatch sites, summary still implies 37-site coverage
**Severity:** 🟠 MINOR

Live verification shows:
- 36 `self._fire_and_forget(self._notifier.X(...))` dispatch sites
- 38 total notifier calls if `.stats()` and `.close()` are included

v2 mostly reflects this correctly, but wording still oscillates between:
- "37 live dispatch sites" in header/audit summary lineage, and
- "36 dispatch sites" in the concrete B5 plan / acceptance criteria.

This is not a structural problem, but for a refactor plan it should be numerically crisp.

**Required fix:** normalize all wording to:
- `36 dispatch sites moved through emitter`, and
- `38 total notifier call references including .stats and .close which remain in router`.

---

### N2 — `persist_state()` integration is still underspecified at the implementation boundary
**Severity:** 🟠 MINOR

v2 correctly identifies emitter-owned state and adds `get_state()` / `load_state()` as the preferred design. Good fix.

What is still missing is an explicit implementation instruction tying that back to the existing router methods:
- `persist_state()` exists at line 2836
- `_load_state()` exists at line 4175

The plan says router should include emitter state, but does not explicitly require the two touchpoints where ANVIL must wire it.

**Recommended fix:** add one sentence in §4g or §6:
- `SignalRouter.persist_state()` must serialize `self._emitter.get_state()`, and `SignalRouter._load_state()` must call `self._emitter.load_state(...)` during startup hydration.`

This is minor because the design intent is already clear, but naming the exact integration points will reduce review churn.

---

## 3. Final Verdict

## ✅ SHIP-READY

### Why
The prior blockers are fixed:
- no phantom function reference remains,
- the emitter API now matches the real notifier surface,
- dependency direction is clean,
- the LOC expectations are realistic,
- B3 interaction is correctly scoped as disjoint.

The two new findings are minor polish items and do not undermine implementation safety.

### Ship-ready conditions
ANVIL can execute B5 v2 as written, with the recommendation to tidy the two minor wording / integration-spec issues during implementation or immediately before code review.

---

## 4. SLA

**SLA for B5 execution:** 24 hours  
Reason: STANDARD-tier refactor, single-repo blast radius, no schema or data risk.

---

## 5. Audit close note

B5 v2 is a good plan. The emitter boundary is now specific enough to implement without rediscovery, and the remaining issues are minor enough not to block execution.
