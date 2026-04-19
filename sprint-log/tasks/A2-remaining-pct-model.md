# Task A2 — remaining_pct Model + Blended PnL Fix

**Tier:** 🔴 CRITICAL  
**Wave:** 1  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oink-sync  
**Branch:** —  
**PR:** [oink-sync#5](https://github.com/QuantisDevelopment/oink-sync/pull/5)  
**Merge commit:** [6b21a2074413](https://github.com/QuantisDevelopment/oink-sync/commit/6b21a2074413395b400b6f95494ae80d77ecef59)

## One-liner

The current `calculate_blended_pnl()` function in `kraken-sync.py` (line ~316) uses **fixed allocation weights** (TP1=50%, TP2=25%, TP3=25%) regardless of what the trader's actual partial-close percentages are.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 23:28 CEST on 18 Apr 2026 | [TASK-A2-plan.md](../../raw-artifacts/forge/plans/TASK-A2-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | FINDINGS | 23:23 CEST on 18 Apr 2026 | [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 01:52 CEST on 19 Apr 2026 | [A2-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A2-PHASE0-PROPOSAL.md) |
| 4 | Phase 0 review | 🔍 VIGIL | ❌ CONCERNS | 01:54 CEST on 19 Apr 2026 | [A2-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A2-VIGIL-PHASE0-REVIEW.md) |
| 5 | Phase 0 review | 🛡️ GUARDIAN | ✅ APPROVE | 01:56 CEST on 19 Apr 2026 | [A2-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A2-GUARDIAN-PHASE0-REVIEW.md) |
| 6 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 02:04 CEST on 19 Apr 2026 | [A2-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A2-PHASE0-APPROVED.marker) |
| 7 | Phase 1 code | ⚒️ ANVIL | MERGED | 02:40 CEST on 19 Apr 2026 | [oink-sync#5](https://github.com/QuantisDevelopment/oink-sync/pull/5) |
| 8 | Phase 1 review | 🔍 VIGIL | 9.85/10 | 02:19 CEST on 19 Apr 2026 | [A2-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A2-VIGIL-PHASE1-REVIEW.md) |
| 9 | Phase 1 review | 🛡️ GUARDIAN | 9.50/10 | 02:26 CEST on 19 Apr 2026 | [A2-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A2-GUARDIAN-PHASE1-REVIEW.md) |
| 10 | Merged | ⚒️ ANVIL | MERGED [6b21a20](https://github.com/QuantisDevelopment/oink-sync/commit/6b21a2074413395b400b6f95494ae80d77ecef59) | 02:40 CEST on 19 Apr 2026 | [A2-MERGED.marker](../../raw-artifacts/anvil/markers/A2-MERGED.marker) |
| 11 | Canary | 🛡️ GUARDIAN | ✅ PASS | 04:42 CEST on 19 Apr 2026 | [A2-CANARY.md](../../raw-artifacts/guardian/canary-reports/A2-CANARY.md) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

- [A2-DEFERRED-ACTIVE-BACKFILL.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-ACTIVE-BACKFILL.md) — ✅ CLOSED: Backfill remaining_pct on ACTIVE Signals
- [A2-DEFERRED-CLOSE-PCT-EXTRACTION.md](../../raw-artifacts/anvil/followups/A2-DEFERRED-CLOSE-PCT-EXTRACTION.md) — Deferred: Provider Text close_pct Extraction

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A2-plan.md](../../raw-artifacts/forge/plans/TASK-A2-plan.md) — 20.0 KB
- **OinkV audit:** [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) — 23.4 KB
- **ANVIL proposal:** [A2-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A2-PHASE0-PROPOSAL.md) — 13.6 KB
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A2-VIGIL-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/vigil/reviews/A2-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A2-GUARDIAN-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A2-GUARDIAN-PHASE1-REVIEW.md)
- **Canary report:** [A2-CANARY.md](../../raw-artifacts/guardian/canary-reports/A2-CANARY.md) — PASS
- **Merge commit:** [`6b21a2074413`](https://github.com/QuantisDevelopment/oink-sync/commit/6b21a2074413395b400b6f95494ae80d77ecef59) (oink-sync PR #5)
- **PR(s):** [oink-sync#5](https://github.com/QuantisDevelopment/oink-sync/pull/5)

## Lessons Learned

- **Auto-escalation to 🔴 CRITICAL** via Financial Hotpath rule — Phase 1 used the stricter ≥9.5 threshold.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
