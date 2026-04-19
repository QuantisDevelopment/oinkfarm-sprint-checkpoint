# Task A3 — Auto filled_at for MARKET Orders

**Tier:** 🟡 STANDARD  
**Wave:** 1  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** anvil/A3-filled-at  
**PR:** [oinkfarm#125](https://github.com/QuantisDevelopment/oinkfarm/pull/125)  
**Merge commit:** [3b5453b7](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7)

## One-liner

MARKET orders are filled immediately at insertion, but the `filled_at` timestamp is never set in the INSERT path.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 23:28 CEST on 18 Apr 2026 | [TASK-A3-plan.md](../../raw-artifacts/forge/plans/TASK-A3-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | FINDINGS | 23:23 CEST on 18 Apr 2026 | [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 23:32 CEST on 18 Apr 2026 | [A3-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A3-PHASE0-PROPOSAL.md) |
| 4 | Phase 0 review | 🛡️ GUARDIAN | ✅ APPROVE | 23:58 CEST on 18 Apr 2026 | [A3-GUARDIAN-REVIEW.md](../../raw-artifacts/guardian/reviews/A3-GUARDIAN-REVIEW.md) |
| 5 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 23:44 CEST on 18 Apr 2026 | [A3-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A3-PHASE0-APPROVED.marker) |
| 6 | Phase 1 code | ⚒️ ANVIL | MERGED | 00:06 CEST on 19 Apr 2026 | [oinkfarm#125](https://github.com/QuantisDevelopment/oinkfarm/pull/125) |
| 7 | Phase 1 review | 🔍 VIGIL | 9.85/10 | 23:54 CEST on 18 Apr 2026 | [A3-VIGIL-REVIEW.md](../../raw-artifacts/vigil/reviews/A3-VIGIL-REVIEW.md) |
| 8 | Phase 1 review | 🛡️ GUARDIAN | 10.00/10 | 00:00 CEST on 19 Apr 2026 | [A3-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A3-GUARDIAN-PHASE1-REVIEW.md) |
| 9 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 00:05 CEST on 19 Apr 2026 | [A3-HERMES-REVIEW.md](../../raw-artifacts/hermes/A3-HERMES-REVIEW.md) |
| 10 | Merged | ⚒️ ANVIL | MERGED [3b5453b](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7) | 00:06 CEST on 19 Apr 2026 | [A3-MERGED.marker](../../raw-artifacts/anvil/markers/A3-MERGED.marker) |
| 11 | Backfill | ⚒️ ANVIL | executed | 00:08 CEST on 19 Apr 2026 | [A3-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A3-BACKFILL-LOG.md) |
| 12 | Canary | 🛡️ GUARDIAN | ✅ PASS | 00:08 CEST on 19 Apr 2026 | [A3-CANARY.md](../../raw-artifacts/guardian/canary-reports/A3-CANARY.md) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A3-plan.md](../../raw-artifacts/forge/plans/TASK-A3-plan.md) — 12.8 KB
- **OinkV audit:** [OINKV-AUDIT.md](../../raw-artifacts/forge/plans/OINKV-AUDIT.md) — 23.4 KB
- **ANVIL proposal:** [A3-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A3-PHASE0-PROPOSAL.md) — 5.9 KB
- **VIGIL reviews:** [Phase 1](../../raw-artifacts/vigil/reviews/A3-VIGIL-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A3-GUARDIAN-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A3-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A3-HERMES-REVIEW.md](../../raw-artifacts/hermes/A3-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A3-CANARY.md](../../raw-artifacts/guardian/canary-reports/A3-CANARY.md) — PASS
- **Backfill log:** [A3-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A3-BACKFILL-LOG.md)
- **Merge commit:** [`3b5453b7`](https://github.com/QuantisDevelopment/oinkfarm/commit/3b5453b7) (oinkfarm PR #125)
- **PR(s):** [oinkfarm#125](https://github.com/QuantisDevelopment/oinkfarm/pull/125)

## Lessons Learned

- **Backfill pre-SELECT + abort-if-rowcount guard** caught a data-quality anomaly without failing the migration.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
