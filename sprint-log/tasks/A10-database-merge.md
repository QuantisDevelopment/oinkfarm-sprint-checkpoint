# Task A10 — Database Merge (test → prod, council-approved)

**Tier:** 🔴 CRITICAL  
**Wave:** 4  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oinkfarm#135](https://github.com/QuantisDevelopment/oinkfarm/pull/135)  
**Merge commit:** —

## One-liner

OinkFarm has two databases: the "old" DB (Feb 8 – Apr 9, 1,165 signals) and the "new" DB (Mar 18 – present, 494+ signals).

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 18:11 CEST on 19 Apr 2026 | [TASK-A10-plan.md](../../raw-artifacts/forge/plans/TASK-A10-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | FINDINGS | 18:05 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A10.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A10.md) |
| 3 | Phase 1 code | ⚒️ ANVIL | MERGED | 20:29 CEST on 19 Apr 2026 | [oinkfarm#135](https://github.com/QuantisDevelopment/oinkfarm/pull/135) |
| 4 | Phase 1 review | 🛡️ GUARDIAN | 9.80/10 | 18:29 CEST on 19 Apr 2026 | [A10-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A10-GUARDIAN-PHASE1-REVIEW.md) |
| 5 | Merged | ⚒️ ANVIL | MERGED [#135](https://github.com/QuantisDevelopment/oinkfarm/pull/135) | 20:29 CEST on 19 Apr 2026 | [A10-MERGED.marker](../../raw-artifacts/anvil/markers/A10-MERGED.marker) |
| 6 | Canary | 🛡️ GUARDIAN | ✅ PASS | 22:27 CEST on 19 Apr 2026 | [A10-CANARY.md](../../raw-artifacts/guardian/canary-reports/A10-CANARY.md) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A10-plan.md](../../raw-artifacts/forge/plans/TASK-A10-plan.md) — 20.9 KB
- **OinkV audit:** [OINKV-AUDIT-WAVE3-A10.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A10.md) — 27.5 KB
- **GUARDIAN reviews:** [Phase 1](../../raw-artifacts/guardian/reviews/A10-GUARDIAN-PHASE1-REVIEW.md)
- **Canary report:** [A10-CANARY.md](../../raw-artifacts/guardian/canary-reports/A10-CANARY.md) — PASS
- **PR(s):** [oinkfarm#135](https://github.com/QuantisDevelopment/oinkfarm/pull/135)

## Lessons Learned

- **Append-only beat cp-overwrite** — validated backup at 18:24Z had drifted (3 signals closed, 76 price updates) by merge time; append-only preserved live trader state while achieving identical council-validated end state.
- **Council governance** (OinkV + OinkDB ✅ via GH Issue #136) was the first non-standard approval path in the sprint — proved the Hermes+2-council pattern for Phase D gating.
- **Zero ID collisions by design** (prod max=1611, imports start=1612) made the append-only method SQL-safe without a preliminary ID rewrite.
- **Drift-inclusive backup** (`oinkfarm.db.a10-predrift-backup-20260419T182923Z`) gave a 2-step rollback: drift state OR pre-merge 494-row state.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
