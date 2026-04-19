# Task A4 — PARTIALLY_CLOSED Status for Partial TP Signals

**Tier:** 🟡 STANDARD — auto-escalated to 🔴 CRITICAL in Phase 1 (Financial Hotpath)  
**Wave:** 2  
**Status:** 🧪 CANARY — Merged, canary in flight  
**Repo target:** oink-sync  
**Branch:** anvil/A4-partially-closed-status  
**PR:** [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7)  
**Merge commit:** [e9be741a7a0c](https://github.com/QuantisDevelopment/oink-sync/commit/e9be741a7a0c0d779b259c9e1813e3aeac59ca0a)

## One-liner

After Task A2, `remaining_pct` is correctly decremented on every TP hit.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 02:47 CEST on 19 Apr 2026 | [TASK-A4-plan.md](../../raw-artifacts/forge/plans/TASK-A4-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | FINDINGS | 12:10 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE2-A4.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A4.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED (R1) | 12:05 CEST on 19 Apr 2026 | [A4-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A4-PROPOSAL.md) |
| 4 | Phase 0 review | 🔍 VIGIL | ✅ APPROVE | 11:50 CEST on 19 Apr 2026 | [A4-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A4-VIGIL-PHASE0-REVIEW.md) |
| 5 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 11:51 CEST on 19 Apr 2026 | [A4-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW.md) |
| 6 | Phase 0 review (R1) | 🛡️ GUARDIAN | ❌ CHANGES (4 blockers) (R1) | 12:08 CEST on 19 Apr 2026 | [A4-GUARDIAN-PHASE0-REVIEW-R1.md](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW-R1.md) |
| 7 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 12:17 CEST on 19 Apr 2026 | [A4-PHASE1-APPROVED.marker](../../raw-artifacts/anvil/proposals/A4-PHASE1-APPROVED.marker) |
| 8 | Phase 1 code | ⚒️ ANVIL | MERGED | 12:41 CEST on 19 Apr 2026 | [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7) |
| 9 | Phase 1 review | 🔍 VIGIL | 9.60/10 | 12:29 CEST on 19 Apr 2026 | [A4-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A4-VIGIL-PHASE1-REVIEW.md) |
| 10 | Phase 1 review | 🛡️ GUARDIAN | 9.90/10 | 12:36 CEST on 19 Apr 2026 | [A4-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE1-REVIEW.md) |
| 11 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 12:40 CEST on 19 Apr 2026 | [A4-HERMES-REVIEW.md](../../raw-artifacts/hermes/A4-HERMES-REVIEW.md) |
| 12 | Merged | ⚒️ ANVIL | MERGED [e9be741](https://github.com/QuantisDevelopment/oink-sync/commit/e9be741a7a0c0d779b259c9e1813e3aeac59ca0a) | 12:41 CEST on 19 Apr 2026 | [A4-MERGED.marker](../../raw-artifacts/anvil/markers/A4-MERGED.marker) |
| 13 | Backfill | ⚒️ ANVIL | executed | 12:45 CEST on 19 Apr 2026 | [A4-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A4-BACKFILL-LOG.md) |
| 14 | Canary | 🛡️ GUARDIAN | ⏳ PENDING | 12:48 CEST on 19 Apr 2026 | [A4-CANARY.md](../../raw-artifacts/guardian/canary-reports/A4-CANARY.md) |

## Key Decisions

- Implement all **5 lifecycle.py sites** (L1–L5) AND all **5 engine.py sites** (E1–E5). E5 is the most critical — it's the silent-PnL-zero risk
- Same-cycle closure path: when `remaining_pct == 0.0` after a TP-hit cycle, call `calculate_blended_pnl()` inside `_process_tp_hits()` and set `status='CLOSED_WIN' + final_roi + closed_at` in the same UPDATE. No PARTIALLY_CLOSED limbo
- Backfill SQL must be in PR description with: pre-SELECT showing IDs 1561/1602, abort-if-rowcount-gt-4 guard, `BEGIN`/`COMMIT` transaction, anomaly handler for #1602
- Test `test_gap_past_all_tps_same_cycle_close` must verify `final_roi == expected_blended_pnl` (not just `status=='CLOSED_WIN'`) — per GUARDIAN advisory #2
- Add `STATUS_CHANGED` to `LIFECYCLE_EVENTS` set in `event_store.py:53` for documentation parity (hygiene, not runtime)

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A4-plan.md](../../raw-artifacts/forge/plans/TASK-A4-plan.md) — 17.0 KB
- **OinkV audit:** [OINKV-AUDIT-WAVE2-A4.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE2-A4.md) — 13.1 KB
- **ANVIL proposal:** [A4-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A4-PROPOSAL.md) — 19.1 KB (R1)
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A4-VIGIL-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/vigil/reviews/A4-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW.md) · [Phase 0 R1](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE0-REVIEW-R1.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A4-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A4-HERMES-REVIEW.md](../../raw-artifacts/hermes/A4-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A4-CANARY.md](../../raw-artifacts/guardian/canary-reports/A4-CANARY.md) — PENDING
- **Backfill log:** [A4-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A4-BACKFILL-LOG.md)
- **Merge commit:** [`e9be741a7a0c`](https://github.com/QuantisDevelopment/oink-sync/commit/e9be741a7a0c0d779b259c9e1813e3aeac59ca0a) (oink-sync PR #7)
- **PR(s):** [oink-sync#7](https://github.com/QuantisDevelopment/oink-sync/pull/7)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
