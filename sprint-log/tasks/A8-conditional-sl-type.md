# Task A8 — Conditional SL Type Field

**Tier:** 🟡 STANDARD  
**Wave:** 3  
**Status:** 🧪 CANARY — Merged, canary in flight  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134)  
**Merge commit:** —

## In plain English

A8 added a conditional SL type column (NONE / NUMERIC / MANUAL / BE / CONDITIONAL) so we can classify stop-loss origin at INSERT-time. This lets us tell Mike's context-dependent SLs apart from explicit numeric ones.

## One-liner

Add a `sl_type` column (`NONE` / `NUMERIC` / `MANUAL` / `BE` / `CONDITIONAL`) to classify stop-loss origin at INSERT-time.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 15:28 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A8.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A8.md) |
| 2 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 17:06 CEST on 19 Apr 2026 | [A8-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE0-REVIEW.md) |
| 3 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 17:06 CEST on 19 Apr 2026 | [A8-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A8-PHASE0-APPROVED.marker) |
| 4 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134) |
| 5 | Backfill | ⚒️ ANVIL | executed | 17:30 CEST on 19 Apr 2026 | [A8-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A8-BACKFILL-LOG.md) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE3-A8.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A8.md) — 13.3 KB
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE0-REVIEW.md)
- **Backfill log:** [A8-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A8-BACKFILL-LOG.md)
- **PR(s):** [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
