## GUARDIAN Proposal Review — A4

**Verdict:** REQUEST CHANGES

**Data Safety:**
The core idea is directionally correct: `PARTIALLY_CLOSED` is an additive status value, no table migration is required, the existing uppercase constraint accepts it, and there are no `signals` table business triggers that would make a combined `remaining_pct + status` UPDATE unsafe. FET #1159 is not at risk from the status addition, it is already `CLOSED_WIN` with `remaining_pct=100.0` in production and never enters the partial-close state. However, proposal §2C is internally inconsistent on the all-TPs-hit edge case. It first says `remaining_pct=0.0` should close directly as `CLOSED_WIN`, then says the signal can remain open until a later SL cycle and that this is acceptable. That limbo state is not data-safe.

**Migration Risk:**
The proposed backfill (`ACTIVE -> PARTIALLY_CLOSED` where `0 < remaining_pct < 100`) is additive, non-destructive, and idempotent because re-running it will skip rows already flipped out of `ACTIVE`. Mike's rowcount guard is the right safety valve, and the deployment must abort if the qualifying population grows beyond the expected small set. That said, the proposal does not specify an explicit transaction or a hard pre-check/abort step in the migration procedure. It should. Also, live data already shows that the backfill population is not purely trivial: signal `#1602` currently has TP timestamps through `tp3_hit_at` while still `status='ACTIVE'`, so the proposal needs to treat pre-existing partial/open rows as potentially anomalous, not just routine.

**Query Performance:**
At current scale, the change is unlikely to create a meaningful SQLite performance problem. The `signals` table still has general indexes on `status` and `status, posted_at`. However, broadening `WHERE status='ACTIVE'` to `WHERE status IN ('ACTIVE','PARTIALLY_CLOSED')` means the planner no longer uses the current covering partial index `ix_signal_exchange_active` (`WHERE status='ACTIVE' AND exchange_matched=1`). It falls back to a broader status index instead. That is acceptable today on a ~490-row table, but it is a real plan change and should be acknowledged in the proposal.

**Regression Risk:**
This is the blocking issue. The proposal scopes the behavioral change to 5 `lifecycle.py` sites, but the live blast radius is wider.

High-risk downstream consumers that currently filter on `ACTIVE` or `ACTIVE/PENDING` and would silently drop `PARTIALLY_CLOSED` rows include:

- `oink_sync/engine.py`
  - `_load_tracked_tickers()` loads tracked symbols from `status IN ('ACTIVE','PENDING')`
  - `_write_prices_to_db()` writes prices only for `status IN ('ACTIVE','PENDING')`
  - `_repair_exchange_matched_flags()` repairs only `status IN ('ACTIVE','PENDING')`
- `oinkdb-api/oinkdb-api.py`
  - `/signals/open`
  - `/signals/active`
  - `/market/sentiment`
  - `/alerts/divergence`
  - trader summary counters that treat only `ACTIVE` as open exposure
- `signal-gateway`
  - `micro-gate-v3.py` active/pending dedup/match queries
  - `signal_router.py` active/pending signal match queries

The most serious data-path risk is `oink_sync/engine.py`, not reporting. If PARTIALLY_CLOSED rows fall out of tracked tickers / price-write selection there, broadening only `lifecycle.py` is insufficient. Those signals may stop receiving price/PnL updates even if SL/TP scan logic is widened. That is too much hidden blast radius for a Phase 0 APPROVE.

**Rollback Viability:**
Operational rollback is viable: revert the code, then run `UPDATE signals SET status='ACTIVE' WHERE status='PARTIALLY_CLOSED';`. That restores pre-A4 monitoring semantics without data loss. The rollback is not perfectly lossless because appended `STATUS_CHANGED` events remain in `signal_events`, but that is acceptable and consistent with append-only audit logging.

**Concerns:**
1. The proposal's scope is too narrow. It must explicitly cover or defer-with-rationale the additional `ACTIVE` / `ACTIVE,PENDING` consumers, especially `oink_sync/engine.py`.
2. DQ-A4-2 is not resolved cleanly. `remaining_pct = 0.0` must not leave a signal in an open limbo state waiting for a later SL cycle.
3. The backfill procedure must be written as a guarded deployment step: pre-SELECT with pasted IDs, abort threshold, explicit transaction, and explicit handling of anomalous candidates.
4. The proposal should acknowledge the partial-index plan regression from `status='ACTIVE'` to `status IN (...)`.

**Suggestions:**
- Revise the proposal so A4 includes every production consumer that must continue treating partially-open exposure as open, or split that into an explicit staged rollout plan with no hidden assumptions.
- Require same-cycle final close when all TPs are hit and `remaining_pct` reaches `0.0`.
- Keep the atomic `remaining_pct + status` UPDATE, that part is sound.
- Add `STATUS_CHANGED` to `LIFECYCLE_EVENTS` for documentation parity, but describe it correctly as hygiene, not a runtime blocker.
- Preserve Mike's guard: re-run the qualifying-row SELECT before deploy, paste the IDs into the PR, and abort if rowcount exceeds 4.

Phase 0 can be approved after the proposal is revised to close the engine/downstream blast radius and the all-TPs-hit limbo ambiguity.
