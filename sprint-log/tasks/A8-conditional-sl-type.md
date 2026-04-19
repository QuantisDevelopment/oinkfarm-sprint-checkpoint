# Task A8 — Conditional SL Type Field

**Tier:** 🟡 STANDARD  
**Wave:** 3  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134)  
**Merge commit:** [46154543](https://github.com/QuantisDevelopment/oinkfarm/commit/46154543)

## One-liner

The `signals` table has a `stop_loss FLOAT` column, but there is no structured way to distinguish *why* `stop_loss` is NULL or what type of stop it is.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 14:17 CEST on 19 Apr 2026 | [TASK-A8-plan.md](../../raw-artifacts/forge/plans/TASK-A8-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | PASS | 15:28 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A8.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A8.md) |
| 3 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 16:56 CEST on 19 Apr 2026 | [A8-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A8-PHASE0-PROPOSAL.md) |
| 4 | Phase 0 review | 🔍 VIGIL | ❌ BLOCK | 16:58 CEST on 19 Apr 2026 | [A8-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A8-VIGIL-PHASE0-REVIEW.md) |
| 5 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 17:06 CEST on 19 Apr 2026 | [A8-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE0-REVIEW.md) |
| 6 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 17:06 CEST on 19 Apr 2026 | [A8-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A8-PHASE0-APPROVED.marker) |
| 7 | Phase 1 code | ⚒️ ANVIL | MERGED | 17:27 CEST on 19 Apr 2026 | [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134) |
| 8 | Phase 1 review | 🛡️ GUARDIAN | 9.50/10 | 17:25 CEST on 19 Apr 2026 | [A8-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE1-REVIEW.md) |
| 9 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 17:26 CEST on 19 Apr 2026 | [A8-HERMES-REVIEW.md](../../raw-artifacts/hermes/A8-HERMES-REVIEW.md) |
| 10 | Merged | ⚒️ ANVIL | MERGED [4615454](https://github.com/QuantisDevelopment/oinkfarm/commit/46154543) | 17:27 CEST on 19 Apr 2026 | [A8-MERGED.marker](../../raw-artifacts/anvil/markers/A8-MERGED.marker) |
| 11 | Backfill | ⚒️ ANVIL | executed | 17:30 CEST on 19 Apr 2026 | [A8-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A8-BACKFILL-LOG.md) |
| 12 | Canary | 🛡️ GUARDIAN | ✅ PASS | 22:41 CEST on 19 Apr 2026 | [A8-CANARY.md](../../raw-artifacts/guardian/canary-reports/A8-CANARY.md) |

## Key Decisions

- PR is now clean** after rebase: `git log origin/master..HEAD` shows a single commit `19f475db` on top of A11. The orphan `2945ada0` is gone. 9 files changed, +503/-9. All changed paths are A8-appropriate (no leaked A11 files).
- INSERT alignment is correct (30/30/30).**
- Columns in `INSERT INTO signals (...)`: **30** (explicit enumeration, verified)
- `?` placeholders in `VALUES (...)`: **30** (counted programmatically)
- Bound values in Python tuple: **30** (parsed programmatically, last element = `sl_type`)
- `test_insert_column_placeholder_count_matches` in `test_micro_gate_filled_at.py` updated from 29→30 and still passes.

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A8-plan.md](../../raw-artifacts/forge/plans/TASK-A8-plan.md) — 15.0 KB
- **OinkV audit:** [OINKV-AUDIT-WAVE3-A8.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A8.md) — 13.3 KB
- **ANVIL proposal:** [A8-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A8-PHASE0-PROPOSAL.md) — 6.0 KB
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A8-VIGIL-PHASE0-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A8-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A8-HERMES-REVIEW.md](../../raw-artifacts/hermes/A8-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A8-CANARY.md](../../raw-artifacts/guardian/canary-reports/A8-CANARY.md) — PASS
- **Backfill log:** [A8-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A8-BACKFILL-LOG.md)
- **Merge commit:** [`46154543`](https://github.com/QuantisDevelopment/oinkfarm/commit/46154543) (oinkfarm PR #134)
- **PR(s):** [oinkfarm#134](https://github.com/QuantisDevelopment/oinkfarm/pull/134)

## Lessons Learned

- **Additive DDL first, code deploy second** — migration SQL applied before the code that reads it, so a rollback is a simple code revert (the column is nullable).
- **CONDITIONAL classification** distinguishes Mike's context-dependent SL from explicit numeric SLs without breaking existing NUMERIC/MANUAL semantics.
- **Deferred dry_run_insert parity** (Hermes concern #2) as tech debt — low risk, not a Phase 1 blocker.
- **Backfill pre-SELECT + abort-if-rowcount guard** caught a data-quality anomaly without failing the migration.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
