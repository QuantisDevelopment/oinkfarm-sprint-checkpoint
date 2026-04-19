# GUARDIAN Proposal Review — A8: Conditional SL Type Field

**Verdict:** APPROVE
**Tier:** 🟡 STANDARD
**Review Date:** 2026-04-19

> **Provenance note:** GUARDIAN produced this review verbatim to its webchat lane @ 16:59:30 CEST (runId `ae41c47e-ee25`), but the underlying LLM run hit a 600s failover timeout @ 17:01:53 (`FailoverError: LLM request timed out` on runId `a885fecf`) before the file-write tool call executed. Orchestrator (Hermes) recovered the verbatim text from `journalctl --user -u openclaw-gateway` channel=webchat output and wrote this file to preserve the review on disk without re-running GUARDIAN's 10-min review turn. No content changes — only formatting (added header + provenance block).

---

## GUARDIAN Proposal Review — A8

**Verdict:** APPROVE

**Data Safety:** Low risk. This is an additive metadata column (`sl_type`) with no formula or lifecycle hotpath impact. Existing financial fields remain untouched. The only data mutation is the targeted backfill of the 28 legitimate `stop_loss IS NULL` rows to `sl_type='NONE'`, which is analytically correct.

**Migration Risk:** Low. `ALTER TABLE ... ADD COLUMN ... DEFAULT 'FIXED'` is safe and non-destructive in SQLite. The backfill is narrow and reversible. Rollback via `DROP COLUMN` is viable on the confirmed SQLite version. I do want deployment order preserved: run DDL first, then code deploy.

**Query Performance:** Low risk. No table rebuild, no join expansion, no hot query path change. The backfill predicates are simple and bounded. I do not see a SQLITE_BUSY or scan-risk concern beyond the normal one-time migration write.

**Regression Risk:** Low to moderate, but acceptable for Phase 0. The main risk is semantic misclassification, not corruption:
- keeping the conditional-keyword list duplicated would invite drift
- insertion-point wording in the plan is slightly imprecise and should resolve to "after SL processing, before TP safety checks"

Neither is a blocker, and both are already acknowledged in the audit.

**Concerns:**
- Test location should follow current micro-gate convention in `.openclaw/workspace/tests/`, not `signal-gateway/tests/`.
- `_ALLOWED_UPDATE_COLS` and `sl_type='MANUAL'` handling must be included so operator SL edits do not leave stale classifications.
- Mark the oink-sync schema tweak as optional, not required.

**Suggestions:**
- Use a shared `_CONDITIONAL_SL_KEYWORDS` constant rather than duplicating the list.
- Keep the backfill verification queries exactly as proposed and record row counts before/after migration.
- Treat rollback as viable, but still prefer additive-first deployment discipline over relying on rollback.

Approved from a data-integrity standpoint.
