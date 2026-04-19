# VIGIL Review — Task A3: Auto filled_at for MARKET Orders

**Branch:** anvil/A3-filled-at
**Commits:** d4428eab
**Change Tier:** 🔴 CRITICAL (auto-escalated — see §Tier Escalation below)
**Review Round:** 1
**Review Date:** 2026-04-18 23:55 UTC

---

## ⚠️ Tier Escalation: STANDARD → CRITICAL

ANVIL submitted this as 🟡 STANDARD. However, the diff modifies the INSERT statement in `micro-gate-v3.py` `_process_signal()` — this is **Financial Hotpath item #6** ("micro-gate INSERT logic — Signal creation — data integrity at ingestion").

Per SOUL.md Financial Hotpath Registry:
> If `git diff` shows ANY of the above in a commit's changed files/functions, the review is CRITICAL — full 5-dimension scoring, 4-hour SLA, ≥9.5 threshold. No exceptions, even for "trivial" changes.

This review applies the **🔴 CRITICAL threshold: ≥9.5 required.**

---

## Dimension Scores

| Dimension | Score | Weight | Weighted | Evidence |
|-----------|-------|--------|----------|----------|
| Spec Compliance | 10/10 | 0.30 | 3.00 | INSERT adds `filled_at` as 28th column. MARKET → `posted_at`, LIMIT → `None`. Matches Phase 4 §1 and TASK-A3-plan §3a exactly. Bonus: `filled_at` logged in SIGNAL_CREATED event payload (not required by spec, but adds observability). Backfill SQL in test matches plan §3b. |
| Test Coverage | 10/10 | 0.25 | 2.50 | All 5 acceptance criteria covered: AC-1 (backfill test), AC-2 (MARKET INSERT), AC-3 (LIMIT INSERT), AC-4 (existing test_micro_gate_source_url updated and passing), AC-5 (hold-time integration test — adopted from VIGIL Phase 0 suggestion). 8 tests total, 6 MUST + 1 SHOULD + 1 dry-run safety. Parameter count validation test (MUST-5) directly mitigates the highest-identified risk. All 8 pass. |
| Code Quality | 10/10 | 0.15 | 1.50 | 10 lines changed in production code. Clear `# ── A3: filled_at for MARKET orders ──` comment. Conditional is readable and minimal: `filled_at = posted_at if order_type == "MARKET" else None`. Column appended at end of INSERT (minimal disruption). Test file well-structured: independent connections per test, clear docstrings, schema as module constant, backfill SQL as constant for reuse. |
| Rollback Safety | 9/10 | 0.15 | 1.35 | `git revert d4428eab` cleanly removes filled_at from INSERT. Downstream fallback (`filled_at or posted_at`) handles NULL gracefully — zero functional regression on rollback. No service restart needed (micro-gate is per-batch). Pre-backfill signal IDs documented (8 rows). Backfill data is harmless to leave in place. One minor gap: backfill SQL lives only in the test file, not as a tracked migration script — acceptable for a one-time 8-row UPDATE, but worth noting. |
| Data Integrity Impact | 10/10 | 0.15 | 1.50 | Purely additive — populates a previously-NULL column with the correct value. No existing data modified or deleted by the code change. Backfill WHERE clause is precise (`order_type='MARKET' AND fill_status='FILLED' AND filled_at IS NULL`). Correctly scoped: excludes 9 LIMIT-order NULLs (separate root cause, logged as follow-up). INSERT OR IGNORE pattern unchanged — parameter mismatch would raise ProgrammingError before SQL execution, not silently ignore. Column-value alignment verified: 28 columns, 28 placeholders, positional mapping correct. |
| **OVERALL** | | | **9.85** | |

---

## Issues Found

**MUST-FIX (blocks PASS):**
None.

**SHOULD-FIX (advisory, improves score):**
1. **Backfill script traceability:** The backfill SQL (`UPDATE signals SET filled_at = posted_at WHERE ...`) exists only as a test constant (`_BACKFILL_SQL` in test_micro_gate_filled_at.py). Consider adding a standalone `scripts/backfill-a3-filled-at.sql` (or equivalent) to the commit so the exact SQL run in production is version-controlled alongside the code change. This is a traceability improvement, not a correctness issue.

**SUGGESTION (no score impact):**
1. The `dry_run=True` path returns before `filled_at` is computed (line ~837). The dry_run result dict could include `"filled_at": posted_at if order_type == "MARKET" else None` for parity with the real INSERT path — useful for dry-run inspection but not required.
2. The LIMIT-order NULL follow-up (`/home/oinkv/anvil-workspace/followups/LIMIT-FILLED-AT-NULLS.md`) should be promoted to a tracked task to avoid losing it.

---

## What's Done Well

- **Adopted VIGIL Phase 0 feedback:** The AC-5 hold-time integration test was a VIGIL suggestion — ANVIL included it. Good responsiveness to review feedback.
- **Parameter count validation test (MUST-5):** This directly targets the highest-risk failure mode (column/placeholder mismatch causing all INSERTs to fail). Smart risk mitigation.
- **Existing test fixture updated:** `test_micro_gate_source_url.py` schema updated to include `filled_at` — prevents silent test breakage from the 27→28 column change.
- **SIGNAL_CREATED event enrichment:** Adding `filled_at` to the event payload provides observability beyond what the spec required. Good engineering instinct.
- **Pre-backfill audit documented:** 8 specific signal IDs listed in the review request for rollback traceability.
- **Follow-up logged:** The 9 LIMIT-order NULLs are tracked separately rather than scope-creeping A3.

---

## Verdict: ✅ PASS

**Overall score: 9.85 / 10** — exceeds 🔴 CRITICAL threshold of ≥9.5.

Clean, minimal, spec-compliant change. 10 production lines changed, 380 lines of tests. All 5 acceptance criteria covered with meaningful assertions. No data integrity risk. Rollback is trivial with zero functional regression.

**Note for ANVIL:** This review auto-escalated from 🟡 STANDARD to 🔴 CRITICAL because the diff modifies micro-gate INSERT logic (Financial Hotpath #6). Future PRs touching the INSERT path in `_process_signal()` should be submitted as CRITICAL tier. The code passed the higher threshold regardless.

Forwarding to GUARDIAN for data-focused review.
