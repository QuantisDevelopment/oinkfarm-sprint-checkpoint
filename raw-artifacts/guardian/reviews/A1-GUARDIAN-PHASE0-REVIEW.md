# 🛡️ GUARDIAN Proposal Review — Task A1 (🔴 CRITICAL)

**Task:** A1 — signal_events Table Extension + Lifecycle Instrumentation
**Tier:** 🔴 CRITICAL
**Reviewed:** 2026-04-19T00:15Z
**Proposal Version:** 1.0

---

## Verdict: ✅ APPROVE

---

## Data Safety

**Risk: NEGLIGIBLE**

The `signal_events` table has **0 rows** in production — independently verified. Adding 4 nullable TEXT columns via ALTER TABLE on an empty table carries zero data corruption risk. No existing data is read, modified, or deleted.

The `signals` table (490 rows) and `quarantine` table (11 rows) are explicitly untouched. Event logging is INSERT-only into `signal_events` — no UPDATE or DELETE operations on any existing table.

The transaction model is sound: event INSERTs occur within the same transaction as the lifecycle UPDATE, ensuring atomicity. The non-fatal try/except wrapper correctly prioritizes the lifecycle operation — if event logging fails, the UPDATE still commits. This means the worst case is a missed event, never a blocked trade operation.

## Migration Risk

**Risk: NEGLIGIBLE**

- ALTER TABLE ADD COLUMN on a 0-row table is the safest possible migration
- Columns are nullable with implicit NULL default — no constraint violations possible
- `ensure_schema()` wraps ALTERs in try/except for idempotency (duplicate column errors handled)
- No destructive operations — purely additive
- Schema rollback plan is documented (CREATE-AS-SELECT + DROP + RENAME), though SQLite's lack of DROP COLUMN makes it multi-step. Acceptable for a 0-row table.

**One observation:** The rollback SQL recreates the table without the new columns but does not explicitly recreate the AUTOINCREMENT behavior (CREATE TABLE ... AS SELECT doesn't preserve it). For a 0-row table this is inconsequential, but ANVIL should note this for the Phase 1 rollback script if row count grows before any hypothetical rollback.

## Query Performance

**Risk: NEGLIGIBLE**

Estimated 50-200 events/day is well within SQLite's capabilities. The existing indexes (signal_id+event_type, created_at, event_type) cover the expected query patterns. No new indexes are proposed or needed at this volume.

No SQLITE_BUSY risk: event INSERTs happen within the existing lifecycle transaction — no additional connection or lock acquisition required. The vendored EventStore in oink-sync shares the same DB connection as lifecycle operations, so no cross-connection contention.

WAL mode (if enabled) would handle the concurrent micro-gate + oink-sync writes cleanly. If not enabled, the existing serialization pattern (each service holds the connection during its cycle) prevents contention.

## Regression Risk

**Risk: LOW — adequately mitigated**

The primary risk surface is the instrumentation of Financial Hotpath functions (`_check_sl_tp()`, `_process_tp_hits()`). ANVIL correctly identifies this and mitigates with:

1. **Non-fatal wrapper** — event logging failure doesn't block the lifecycle UPDATE
2. **Same-transaction model** — no orphaned state possible
3. **INSERT-only** — event logging cannot corrupt existing signal data

The blast radius if event logging has a bug: missed events (audit trail gap), NOT corrupted signals. This is the correct failure mode — acceptable degradation rather than data corruption.

**Vendoring concern:** Two copies of `event_store.py` (oinkfarm + oink-sync) sharing the same schema is a maintenance risk long-term, but for Phase A it's pragmatic. The shared `_SCHEMA_SQL` ensures schema compatibility. This is acceptable for now; the PostgreSQL migration (Phase B) will consolidate.

## Rollback Viability

**ADEQUATE**

- Code rollback: `git revert` + service restart — clean
- Schema rollback: Documented multi-step process (CREATE-AS-SELECT → DROP → RENAME). For a 0-row table, trivial. For a populated table (post-deploy), ANVIL should capture the event count before rollback to document data loss.
- No downstream dependencies read from signal_events — rollback has no cascading effects

## Concerns

1. **Zero-event diagnostic is critical path.** The proposal acknowledges 0 events are being written despite 13 `_log_event` call sites in micro-gate. The diagnostic and fix must be completed and verified BEFORE oink-sync instrumentation makes sense. If the root cause is a DB connection/transaction pattern issue, the same pattern could affect oink-sync's vendored EventStore. ANVIL's Day 1 ordering (diagnose first) is correct.

2. **oinkdb-api.py deferral is acceptable.** The FastAPI async context is genuinely different from the synchronous lifecycle.py pattern. Separate review makes sense.

3. **Reconciler deferral is acceptable.** micro-gate's existing `_log_event` calls in the closure path should capture most closure events once the zero-event bug is fixed.

## Suggestions

1. **Canary criterion #1 should have a fallback:** "SELECT COUNT(*) > 0 within 1 hour" depends on signal volume. During low-activity periods (weekend nights), this may take longer. Consider a manual test signal injection as a backup verification method.

2. **Consider logging the zero-event root cause fix** as a documented finding — future instrumentation efforts (oinkdb-api, reconciler) may hit similar patterns.

3. **Design Questions:** I concur with ANVIL's recommendations on DQ-1 (ALTER TABLE over JSON-only), DQ-2 (defer oinkdb-api.py), and DQ-3 (defer reconciler). All three are sound from a data safety perspective.

---

*🛡️ GUARDIAN — Phase 0 Proposal Review*
*Reviewed: 2026-04-19T00:15Z*
