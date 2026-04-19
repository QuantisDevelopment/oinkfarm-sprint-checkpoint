# Task A6 — Ghost Closure Confirmation Flag

**Tier:** 🟡 STANDARD  
**Wave:** 3  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** signal-gateway  
**Branch:** —  
**PR:** [signal-gateway#20](https://github.com/bandtincorporated8/signal-gateway/pull/20)  
**Merge commit:** [1adeaa1fd2bb](https://github.com/QuantisDevelopment/signal-gateway/commit/1adeaa1fd2bbde936869a5b72465a3f2c6c3ffef)

## One-liner

The reconciler (`reconciler.py`) already detects ghost closures: when a position disappears from the board for `absent_count >= absent_threshold` (default: 3 snapshots), it emits a `CLOSE` action with `source='board_absent'` and `soft_close=True`.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | FORGE plan published | 🔥 FORGE | PUBLISHED | 14:16 CEST on 19 Apr 2026 | [TASK-A6-plan.md](../../raw-artifacts/forge/plans/TASK-A6-plan.md) |
| 2 | Phase 0 proposal drafted | ⚒️ ANVIL | DRAFTED | 14:43 CEST on 19 Apr 2026 | [A6-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A6-PHASE0-PROPOSAL.md) |
| 3 | Phase 0 review | 🔍 VIGIL | ✅ APPROVE | 14:29 CEST on 19 Apr 2026 | [A6-VIGIL-PHASE0-REVIEW.md](../../raw-artifacts/vigil/reviews/A6-VIGIL-PHASE0-REVIEW.md) |
| 4 | Phase 0 review | 🛡️ GUARDIAN | ❌ CHANGES | 14:45 CEST on 19 Apr 2026 | [A6-GUARDIAN-PHASE0-REVIEW.md](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE0-REVIEW.md) |
| 5 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 14:55 CEST on 19 Apr 2026 | [A6-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A6-PHASE0-APPROVED.marker) |
| 6 | Phase 1 code | ⚒️ ANVIL | MERGED | 15:18 CEST on 19 Apr 2026 | [signal-gateway#20](https://github.com/bandtincorporated8/signal-gateway/pull/20) |
| 7 | Phase 1 review | 🔍 VIGIL | 9.15/10 | 15:04 CEST on 19 Apr 2026 | [A6-VIGIL-PHASE1-REVIEW.md](../../raw-artifacts/vigil/reviews/A6-VIGIL-PHASE1-REVIEW.md) |
| 8 | Phase 1 review | 🛡️ GUARDIAN | 9.80/10 | 15:17 CEST on 19 Apr 2026 | [A6-GUARDIAN-PHASE1-REVIEW.md](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE1-REVIEW.md) |
| 9 | Hermes parallel review | 🪽 Hermes | ✅ LGTM | 15:16 CEST on 19 Apr 2026 | [A6-HERMES-REVIEW.md](../../raw-artifacts/hermes/A6-HERMES-REVIEW.md) |
| 10 | Merged | ⚒️ ANVIL | MERGED [1adeaa1](https://github.com/QuantisDevelopment/signal-gateway/commit/1adeaa1fd2bbde936869a5b72465a3f2c6c3ffef) | 15:18 CEST on 19 Apr 2026 | [A6-MERGED.marker](../../raw-artifacts/anvil/markers/A6-MERGED.marker) |
| 11 | Canary | 🛡️ GUARDIAN | ✅ PASS | 22:38 CEST on 19 Apr 2026 | [A6-CANARY.md](../../raw-artifacts/guardian/canary-reports/A6-CANARY.md) |

## Key Decisions

- Entry discriminator iteration** correctly walks rows in `ORDER BY id DESC` and **breaks on first match within tolerance**. This is correct because newer signals are more likely to be the live position; if both are within tolerance, the newest wins (sane default).
- Zero-entry edge case** (`elif _a6_action_entry == 0 and _a6_db_entry == 0`) is handled as exact-match-only — a sound choice since dividing by zero would be undefined and a non-zero side would be a real mismatch.
- Payload composition** uses `json.dumps(...)` with primitive types only (str, int, float). No datetime/Decimal/bytes that would need a `default=` handler. Round-trips cleanly.
- Logging tier discipline**: INFO for first write (operationally meaningful), DEBUG for idempotent skip (low-signal noise suppressed), WARNING for no-match and DB failure (audit-investigable). Matches the Phase 0 "WARNING-path observability for no-match cases" GUARDIAN concern.

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **FORGE plan:** [TASK-A6-plan.md](../../raw-artifacts/forge/plans/TASK-A6-plan.md) — 16.5 KB
- **ANVIL proposal:** [A6-PHASE0-PROPOSAL.md](../../raw-artifacts/anvil/proposals/A6-PHASE0-PROPOSAL.md) — 14.9 KB
- **VIGIL reviews:** [Phase 0](../../raw-artifacts/vigil/reviews/A6-VIGIL-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/vigil/reviews/A6-VIGIL-PHASE1-REVIEW.md)
- **GUARDIAN reviews:** [Phase 0](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE0-REVIEW.md) · [Phase 1](../../raw-artifacts/guardian/reviews/A6-GUARDIAN-PHASE1-REVIEW.md)
- **Hermes review:** [A6-HERMES-REVIEW.md](../../raw-artifacts/hermes/A6-HERMES-REVIEW.md) — LGTM
- **Canary report:** [A6-CANARY.md](../../raw-artifacts/guardian/canary-reports/A6-CANARY.md) — PASS
- **Merge commit:** [`1adeaa1fd2bb`](https://github.com/QuantisDevelopment/signal-gateway/commit/1adeaa1fd2bbde936869a5b72465a3f2c6c3ffef) (signal-gateway PR #20)
- **PR(s):** [signal-gateway#20](https://github.com/bandtincorporated8/signal-gateway/pull/20)

## Lessons Learned

- **Additive-metadata-only discipline** kept A6 out of the Financial Hotpath registry — no financial-field writes, no DDL, no close_source mutation.
- **`changes()` coupling** was the elegant TOCTOU fix: gate the note UPDATE on the actual rowcount of the INSERT within the same connection/transaction.
- **Entry-price discriminator with 5% tolerance** (mirroring A7) handles the multi-ACTIVE-signal-per-symbol edge case cleanly.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
