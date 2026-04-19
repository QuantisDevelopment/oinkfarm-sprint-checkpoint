# Task A9 — Denomination Multiplier Table (1000x-prefixed symbols)

**Tier:** 🟢 LIGHTWEIGHT  
**Wave:** 3  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/bandtincorporated8/oinkfarm/pull/132)  
**Merge commit:** [2719648](https://github.com/QuantisDevelopment/oink-sync/commit/2719648) + [2719648](https://github.com/QuantisDevelopment/oinkfarm/commit/2719648)

## One-liner

Some crypto venues list micro-cap assets using prefixed contract symbols like `1000PEPEUSDT`, `1000FLOKIUSDT`, and `1000SHIBUSDT`.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 14:23 CEST on 19 Apr 2026 | [TASK-A9-plan.md](../../raw-artifacts/forge/plans/TASK-A9-plan.md) |
| 2 | OinkV audit | 👁️ OinkV | PASS | 15:29 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) |
| 3 | Phase 1 code | ⚒️ ANVIL | MERGED | 16:22 CEST on 19 Apr 2026 | [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/bandtincorporated8/oinkfarm/pull/132) |
| 4 | Phase 1 review | 🔍 VIGIL | 9.40/10 | 16:06 CEST on 19 Apr 2026 | [A9-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A9-VIGIL-PHASE1-REVIEW.md) |
| 5 | Phase 1 review | 🛡️ GUARDIAN | 9.80/10 | 16:12 CEST on 19 Apr 2026 | [A9-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A9-GUARDIAN-PHASE1-REVIEW.md) |
| 6 | Hermes parallel review | 🪽 Hermes | ⚠️ CONCERNS | 15:57 CEST on 19 Apr 2026 | [A9-HERMES-REVIEW.md](../../raw-artifacts/hermes/A9-HERMES-REVIEW.md) |
| 7 | Merged | ⚒️ ANVIL | MERGED [2719648](https://github.com/QuantisDevelopment/oink-sync/commit/2719648) + [2719648](https://github.com/QuantisDevelopment/oinkfarm/commit/2719648) | 16:22 CEST on 19 Apr 2026 | [A9-MERGED.marker](../../raw-artifacts/anvil/markers/A9-MERGED.marker) |
| 8 | Canary | 🛡️ GUARDIAN | ✅ PASS | 22:38 CEST on 19 Apr 2026 | [A9-CANARY.md](../../raw-artifacts/guardian/canary-reports/A9-CANARY.md) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A9-plan.md](../../raw-artifacts/forge/plans/TASK-A9-plan.md) — 14.9 KB
- **OinkV audit:** [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) — 21.6 KB
- **VIGIL reviews:** [Phase 1](../../raw-artifacts/vigil/reviews/A9-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 1](../../raw-artifacts/guardian/reviews/A9-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A9-HERMES-REVIEW.md](../../raw-artifacts/hermes/A9-HERMES-REVIEW.md) — CONCERNS
- **Canary report:** [A9-CANARY.md](../../raw-artifacts/guardian/canary-reports/A9-CANARY.md) — PASS
- **Merge commit:** [`2719648`](https://github.com/QuantisDevelopment/oink-sync/commit/2719648) (oink-sync PR #8)
- **Merge commit:** [`2719648`](https://github.com/QuantisDevelopment/oinkfarm/commit/2719648) (oinkfarm PR #132)
- **PR(s):** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) · [oinkfarm#132](https://github.com/bandtincorporated8/oinkfarm/pull/132)

## Lessons Learned

- **Normalize early, dedup after** — entry-price normalization had to move to §3b (before all guards) so the snowflake dedup probe at §4 + §4b matched stored values (GUARDIAN P2 fix).
- **SL normalization in §8a-A9** (before B11 deviation guard) prevented valid 1000x signals with SL from being rejected by the SL_DEVIATION guard (GUARDIAN P1 fix).
- **R2 delta review** converged all three reviewers (VIGIL 9.40 · GUARDIAN 9.80 · Hermes LGTM) after 2 rounds.
- **INSERT-time-only scope** deliberately left UPDATE and CLOSURE normalization for A9.1 follow-up — avoided blast-radius creep.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
