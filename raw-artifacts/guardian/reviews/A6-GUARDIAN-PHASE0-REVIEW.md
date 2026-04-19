## GUARDIAN Proposal Review — A6

**Verdict:** APPROVE

**Data Safety:** R1 resolves the two R0 blockers. The signal lookup is now keyed by `(trader, ticker, direction, status)` and then narrowed by reconciler-provided `entry` proximity, which aligns the DB write target with the reconciler's multi-position model instead of blindly taking the newest row. The note append is now coupled to successful first-insert semantics via `changes()`, so repeated absent cycles will not keep mutating the same signal row. This keeps the audit trail additive and prevents wrong-row or duplicate-note corruption.

**Migration Risk:** Low. No DDL, no backfill, and no destructive mutation of financial fields. Rollback remains straightforward because the change only adds `GHOST_CLOSURE` metadata and a guarded notes tag.

**Query Performance:** Low risk. The revised lookup is still cheap at expected volume, and the write path remains a small inline sqlite transaction. I do not see a new SQLITE_BUSY or scan-risk concern at the proposal level.

**Regression Risk:** Low to moderate, but acceptable for Phase 0. The main risk remains audit-path misattribution if entry tolerance is implemented incorrectly in code, but the proposal now includes the right discriminator and explicit skip-on-no-match behavior. That is sufficient to proceed to Phase 1 review.

**Concerns:**
- No remaining Phase 0 blockers.
- Phase 1 should verify that the 5% entry tolerance is applied exactly as proposed and that the tests cover both the multi-match and no-match branches.

**Suggestions:**
- Keep the event INSERT and note UPDATE inside one transaction exactly as proposed.
- In Phase 1, verify WARNING-path observability for no-match cases so silent audit gaps do not accumulate.
- Preserve `close_source` unchanged for provisional ghost closures, that design remains correct.
