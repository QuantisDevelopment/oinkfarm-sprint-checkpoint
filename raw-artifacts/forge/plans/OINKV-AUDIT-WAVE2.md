# OINKV-AUDIT-WAVE2 (Hermes fallback — OinkV LLM timeout)

**Auditor:** Hermes sprint-orchestrator dispatching 3 parallel Claude subagents
**Reason for fallback:** OinkV main lane hit `FailoverError: LLM request timed out` after 61 min on 2026-04-19 at 11:19 CEST. Original dispatch `bea1b26a` was ack'd but the underlying LLM never returned. Rather than nudge OinkV (which would re-incur the 60 min timeout), I dispatched 3 `delegate_task` subagents in parallel — same read-only mandate, same audit methodology as Wave 1.
**Date:** 2026-04-19 11:30 CEST
**Plans audited:** TASK-A4-plan.md, TASK-A7-plan.md, TASK-A5-plan.md
**Base commits verified:** oink-sync `6b21a20`, signal-gateway `38eb8e8`, `.openclaw/workspace` canonical micro-gate at `498d8b28`

## Sub-audit files

| Plan | Sub-audit file | Headline |
|------|---------------|----------|
| TASK-A4-plan.md | [OINKV-AUDIT-WAVE2-A4.md](OINKV-AUDIT-WAVE2-A4.md) | ❌ NEEDS-REVISION — 1 critical, 5 minor |
| TASK-A7-plan.md | [OINKV-AUDIT-WAVE2-A7.md](OINKV-AUDIT-WAVE2-A7.md) | ❌ NEEDS-REVISION — 4 critical |
| TASK-A5-plan.md | [OINKV-AUDIT-WAVE2-A5.md](OINKV-AUDIT-WAVE2-A5.md) | ❌ NEEDS-REVISION — 2 critical |

## Consolidated Verdict

**A4:** Initial fallback audit marked this READY, but live verification surfaced a **critical omitted scope item**: `oink-sync/oink_sync/engine.py` still filters to `ACTIVE/PENDING` in `_load_tracked_tickers()`, `_write_prices_to_db()`, and exchange-match repair, and `_calculate_pnl()` returns `None` for any status other than `ACTIVE`. If A4 ships only in `lifecycle.py`, `PARTIALLY_CLOSED` rows can stop getting `current_price`, `pnl_percent`, and lifecycle input after the first TP hit. A4 therefore moves to **NEEDS-REVISION** until `engine.py` is added to scope. The backfill question remains, but it is now secondary to the engine-layer blocker.

**A7 — the big one.** Plan was drafted against the **signal-gateway** copy of `micro-gate-v3.py` (47 KB, Apr 15, 1063 lines), but the CANONICAL target — the one that actually runs in production per `498d8b28` A1 fix commit — is `.openclaw/workspace/scripts/micro-gate-v3.py` (61 KB, Apr 19, 1407 lines). Every line reference in §1/§2/§9 of the plan is off by 90–270 lines. The audit includes a full remapping table. ANVIL cannot implement against the plan as-written; FORGE needs to repoint the plan. Additional critical: plan adds `UPDATE_DETECTED` event but doesn't update `LIFECYCLE_EVENTS` in `event_store.py`, and plan's `_log_rejection(...)` call omits the `conn=` kwarg that was added post-A1. Open question Q-A7-1 (ticker_only inclusion) — precedent in existing `_process_closure` supports FORGE's tentative "yes, include".

**A5 — real showstopper in the map.** `PARSER_CONFIDENCE_MAP` as drafted has 3 phantom keys (`board_reconciler`, `oinkdb_opus`, `manual`) that NO producer writes, while 4 actively-produced `extraction_method` values (`oinxtractor_agent` — a major active path — plus `telegram_direct`, `inline_fallback`, `qwen_v3`) are missing from the map and would silently fall to the 0.8 default. Ship as-is and A5 adds ~zero signal differentiation. Plus canonical-file ambiguity (same drift as A7; plan cites signal-gateway line numbers).

## Next Actions (recommended — orchestrator will dispatch)

1. **FORGE revision pass** — FORGE must revise **all three** plans now. A4 adds `oink-sync/oink_sync/engine.py` scope for `PARTIALLY_CLOSED` support; A7 still needs canonical-file remap + event_store.py addition + `_log_rejection` signature + canonical file swap; A5 still needs PARSER_CONFIDENCE_MAP rebuilt from actual production producers and canonical line remap.
2. **Mike's approval of Wave 2 should wait for the revised plans.** A4 is no longer approval-ready because the engine-layer blocker means the plan would not work end-to-end. A5 and A7 were already blocked on plan fixes.
3. **ANVIL stays in `awaiting_plan_approval`** until FORGE revisions land + Mike greenlights.

## Notes on OinkV LLM Timeout

- `bea1b26a` dispatched 10:18 CEST, status in `task_runs` = `succeeded` (misleading — that's the OpenClaw routing ack), but gateway diagnostic at 11:19:44 shows `FailoverError: LLM request timed out` on lane=main after 3661 seconds.
- Hermes fallback kept wall-clock progress: total elapsed for 3 parallel audits ≈ 9 minutes.
- Not logging this as an infra incident — OinkV LLM timeouts are a known issue per the skill (`oinkfarm-sprint-orchestrator` § "GUARDIAN Dispatch Prefill Rejection" analog — same class, different agent).
