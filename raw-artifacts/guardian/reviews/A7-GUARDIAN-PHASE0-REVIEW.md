# 🛡️ GUARDIAN Proposal Review — Task A7

## GUARDIAN Proposal Review — A7

**Verdict:** APPROVE

**Task:** A7 — UPDATE→NEW Detection (Phantom Trade Prevention)
**Tier:** 🔴 CRITICAL (Financial Hotpath #6)
**Revision:** 0 (initial)
**Review Date:** 2026-04-19

---

### Data Safety

A7 is purely defensive — it only **prevents** INSERTs, never modifies existing signal data. This is the safest category of change: the worst outcome of a bug is that a legitimate signal gets blocked (recoverable via manual re-entry), not that existing data gets corrupted or lost.

Data writes are limited to:
- `signal_events`: UPDATE_DETECTED event per suppression (best-effort via `_log_event`, commit=True). Append-only, non-destructive. ✅
- `quarantine` table: One entry per suppression (via `_log_rejection(conn=conn)`). Append-only. ✅
- `gate-rejections.jsonl`: One line per suppression. Append-only. ✅
- `signals.notes`: A7 annotation on **allowed** INSERTs only (genuine new positions). Annotation appends to the already-joined `notes` string after line 824. Non-destructive. ✅

**Existing signals are never modified by the A7 guard path.** The only signal modification is the `notes` annotation on signals that *pass* the guard and proceed to INSERT — which is a new signal being created, not an existing one being altered.

**Assessment: No risk to existing data.** ✅

---

### Migration Risk

**Zero.** No schema changes. No ALTER TABLE, no new tables, no new columns. The only SQL changes are 4 WHERE clause broadenings (adding `'PARTIALLY_CLOSED'` to status IN). These are read-only query changes that expand the search scope, consistent with A4.

**Assessment: No migration risk.** ✅

---

### Query Performance Risk

The `_match_active()` function is **already called** in the INSERT path (indirectly via §4b guard at line 669 which does an exact-match query). A7 reuses the same `_match_active()` result, adding only a Python-side percentage comparison. No new database queries are added to the INSERT hot path.

The 4 status IN clause broadenings add one more value to existing IN lists. At 492 rows (77 ACTIVE + 2 PARTIALLY_CLOSED + 11 PENDING = 90 qualifying rows), the performance impact is unmeasurable.

**Assessment: No performance risk.** ✅

---

### Regression Risk

**Blast radius is narrow and well-contained:**

1. **_match_active() broadening** (3 clauses) — affects UPDATE handler (line 916) and CLOSURE handler (line 1059) in addition to the new A7 guard. Both handlers **benefit** from seeing PARTIALLY_CLOSED signals: UPDATE handler would flag `LOW_CONFIDENCE_UPDATE` (line 927) rather than miss the match; CLOSURE handler would find the signal rather than reporting `NO_ACTIVE_SIGNAL`. This is a strict improvement, consistent with A4.

2. **§4b guard broadening** (1 clause) — the CROSS_CHANNEL_DUPLICATE check already requires exact entry_price match. Adding PARTIALLY_CLOSED means it now catches duplicates of partial-close signals too. Strictly beneficial.

3. **A7 guard block** (~25 new lines) — fires only when `_match_active` returns a match with `exact` or `ticker_only` confidence AND entry prices are within 5%. This is a new code path with no side effects on existing paths. If the guard doesn't fire (no match, ambiguous, or >5% difference), execution proceeds to INSERT exactly as before.

**`ticker_only` inclusion (§2C) — GUARDIAN concurs.** Verified against codebase:
- UPDATE handler (line 927): REFUSES `ticker_only` as `LOW_CONFIDENCE_UPDATE`
- CLOSURE handler (line 1063): REFUSES `ticker_only` as `LOW_CONFIDENCE_CLOSURE`
- A7 (proposed): SUPPRESSES `ticker_only` as `A7_UPDATE_DETECTED`

All three handlers apply the same principle: don't act destructively/irreversibly on weak matches. INSERT suppression is irreversible (the phantom trade is never created), so SUPPRESS is the correct default. The 48h monitoring plan provides a safety valve.

**One advisory note:** The `_match_active()` broadening means the UPDATE handler at line 927 will now see PARTIALLY_CLOSED signals on `ticker_only` matches. Currently it flags these as `LOW_CONFIDENCE_UPDATE` and returns without acting — so the behavior is safe. But ANVIL should verify this in tests (a PARTIALLY_CLOSED signal should still trigger the `LOW_CONFIDENCE_UPDATE` flag, not silently succeed).

---

### Rollback Viability

Trivial: `git revert` + service restart. No data to migrate back. Suppressed signals were never inserted, so no cleanup needed. The only risk of rollback is resuming pre-A7 behavior (phantom duplicates). ✅

---

### Concerns

**None blocking.**

---

### Suggestions (Advisory, Non-Blocking)

1. **Test the UPDATE handler with PARTIALLY_CLOSED signals** — verify that an UPDATE message targeting a PARTIALLY_CLOSED signal with `ticker_only` confidence still flags as `LOW_CONFIDENCE_UPDATE` (not silently applied). This is a side effect of the `_match_active` broadening, not the A7 guard itself.

2. **Consider logging the suppression count in the daily summary** — once deployed, GUARDIAN's daily checks could include a count of A7_UPDATE_DETECTED rejections for trend monitoring.

---

*🛡️ GUARDIAN — Phase 0 Proposal Review*
*Reviewed: 2026-04-19T10:49Z*
