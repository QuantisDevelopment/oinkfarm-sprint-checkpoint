# Task A4 — PARTIALLY_CLOSED Status for Partial TP Signals

**Tier:** 🟡 STANDARD — auto-escalated to 🔴 CRITICAL in Phase 1 (Financial Hotpath)  
**Wave:** 2  
**Status:** 🛑 BLOCKED — Blocked on decision or dependency  
**Repo target:** oink-sync  
**Branch:** —  
**PR:** [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7)  
**Merge commit:** —

## In plain English

A4 added the PARTIALLY_CLOSED status so partial-TP signals have a clean lifecycle. Before this, signals hit a limbo state whenever a TP1/TP2 fired without all levels closing — breaking PnL aggregation.

## One-liner

PARTIALLY_CLOSED Status for Partial TP Signals — see plan for details.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | FINDINGS | 12:10 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE2-A4.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A4.md) |
| 2 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 11:51 CEST on 19 Apr 2026 | [A4-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW.md) |
| 3 | Phase 0 review (R1) | 🛡️ GUARDIAN | ❌ CHANGES (4 blockers) (R1) | 12:08 CEST on 19 Apr 2026 | [A4-GUARDIAN-PHASE0-REVIEW-R1.md](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW-R1.md) |
| 4 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 12:17 CEST on 19 Apr 2026 | [A4-PHASE1-APPROVED.marker](../../raw-artifacts/anvil/proposals/A4-PHASE1-APPROVED.marker) |
| 5 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7) |
| 6 | Backfill | ⚒️ ANVIL | executed | 12:45 CEST on 19 Apr 2026 | [A4-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A4-BACKFILL-LOG.md) |

## Key Decisions

- Implement all **5 lifecycle.py sites** (L1–L5) AND all **5 engine.py sites** (E1–E5). E5 is the most critical — it's the silent-PnL-zero risk
- Same-cycle closure path: when `remaining_pct == 0.0` after a TP-hit cycle, call `calculate_blended_pnl()` inside `_process_tp_hits()` and set `status='CLOSED_WIN' + final_roi + closed_at` in the same UPDATE. No PARTIALLY_CLOSED limbo
- Backfill SQL must be in PR description with: pre-SELECT showing IDs 1561/1602, abort-if-rowcount-gt-4 guard, `BEGIN`/`COMMIT` transaction, anomaly handler for #1602
- Test `test_gap_past_all_tps_same_cycle_close` must verify `final_roi == expected_blended_pnl` (not just `status=='CLOSED_WIN'`) — per GUARDIAN advisory #2
- Add `STATUS_CHANGED` to `LIFECYCLE_EVENTS` set in `event_store.py:53` for documentation parity (hygiene, not runtime)

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE2-A4.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A4.md) — 13.1 KB
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW.md) · [Phase 0 R1](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW-R1.md)
- **Backfill log:** [A4-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A4-BACKFILL-LOG.md)
- **PR(s):** [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
