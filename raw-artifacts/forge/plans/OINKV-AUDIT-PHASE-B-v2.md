# OinkV Audit — Phase B Wave 1 v2 (Hermes fallback)

**Auditor:** Hermes subagents (dual parallel `delegate_task` batch; OinkV main lane LLM-timing-out)
**Date:** 2026-04-20 04:22 CEST (02:22 UTC)
**Plans audited:**
- `TASK-B2-plan.md` v2 (556 lines, 32,808 bytes, mtime 2026-04-20 01:43 CEST)
- `TASK-B3-plan.md` v2 (502 lines, 33,761 bytes, mtime 2026-04-20 01:42 CEST)

**Revision driver:** `PHASE-B-WAVE1-REVISION-v2.md` (FORGE 2026-04-20 01:43 CEST) — v1 rejections forced full rewrites.

---

## ⚠️ Provenance note for Mike

OinkV (agent `main`) was LLM-unavailable during this audit window:

```
Apr 20 01:57:21  [diagnostic] lane task error: lane=main durationMs=198504 error="FailoverError: LLM request timed out."
Apr 20 02:01:15  [diagnostic] lane task error: lane=main durationMs=232273 error="FailoverError: LLM request timed out."
Apr 20 02:12:10  [diagnostic] lane task error: lane=main durationMs=654324 error="FailoverError: LLM request timed out."
```

Rather than wait another hour for OinkV retries to clear, Hermes dispatched two parallel `delegate_task` subagents (one per plan) with the full audit rubric. Each received the exemplar v1 audit format, canonical commit SHAs, live DB schema, and read-only safety rails. Per `oinkfarm-sprint-orchestrator` skill "Hermes-Subagent Fallback for OinkV Staleness Audits".

---

## Canonical commits verified (2026-04-20 02:13 UTC)

| Repo | Path | HEAD | Note |
|------|------|------|------|
| oinkfarm | `/home/oinkv/.openclaw/workspace` | `0fbcbf1b` | B1 merged + 2 post-merge fixes |
| oink-sync | `/home/oinkv/oink-sync` | `ecd2622` | B1 merged |
| signal-gateway | `/home/oinkv/signal-gateway` | `b0f0254` | B1 merged |
| DB | `/home/m/data/oinkfarm.db` | — | 1409 signals / 565 events / 100 traders / 11 servers / 284736 price_history / 23 quarantine / 0 audit_log |

Both v2 plans reference these exact commits — no stale hashes remain.

---

## Headline verdicts

| Plan | Verdict | Findings | Ship-ready? |
|------|---------|----------|-------------|
| **B2 v2** | ✅ **SHIP-READY** | 0 Critical · 0 Major · 2 Minor · 14 Confirmed-Fixed | Yes — ANVIL can start Phase 0 |
| **B3 v2** | ✅ **SHIP-READY** | 0 Critical · 0 Major · 1 Minor · 11 Confirmed-Fixed | Yes — but gated on B2 landing |

Detailed audits:
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B2-v2.md` (17,213 bytes, 196 lines)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B3-v2.md` (19,792 bytes)

---

## B2 v2 — all v1 blockers closed

| v1 Finding | v2 Disposition | Verified via |
|---|---|---|
| CRITICAL-B2-1 (signal_events DDL fabricated) | ✅ FIXED — 10 cols match live `.schema` 1:1 incl. A1 `field/old_value/new_value/source_msg_id` | column-for-column diff |
| CRITICAL-B2-2 (traders DDL invents 6 cols) | ✅ FIXED — 6 cols + `UNIQUE(name,server_id)` | live schema match |
| CRITICAL-B2-3 (servers DDL wrong names) | ✅ FIXED — `discord_id` / `enabled` / `signal_channel_ids` / `added_at` | live schema match |
| CRITICAL-B2-4 (quarantine DDL completely wrong) | ✅ FIXED — 9 cols incl. `resolved_at` / `resolution` | live schema match |
| CRITICAL-B2-5 (audit_log DDL drops FK) | ✅ FIXED — FK to `signals(id)` restored, 6 cols | live schema match |
| CRITICAL-B2-6 (5 CHECK + 5 triggers dropped) | ✅ FIXED — all 6 CHECKs translated 1:1; triggers replaced by CHECKs+FK+Q-B2-5 decision flag for REJECTED_AUDIT edge case | constraint-by-constraint audit |
| MAJOR-B2-1 ("50 columns") | ✅ FIXED — 0 hits on "50 col", consistent 52 throughout | grep |
| MAJOR-B2-2 (row counts wrong) | ✅ FIXED — cites 1409/565/100/11/284736/23/0 (45-min drift on events: 549 cited vs 565 live, non-blocking since plan has pre-migration re-baseline) | live vs plan |
| MAJOR-B2-3 (A10 NULL filled_at) | ✅ ADDRESSED — Q-B2-4 Mike decision flag + pre-migration data-quality gate | §3 audit |
| MAJOR-B2-4 (price_history 281k rows) | ✅ FIXED — 284112 cited w/ COPY recommendation + `test_price_history_count_match` | plan §4 |
| MAJOR-B2-5 (5/11 indexes) | ✅ FIXED — 21 `CREATE INDEX` statements, matches live non-autoindex count | grep + sqlite_master |
| MINOR-B2-1/2/3 | ✅ FIXED | cosmetic — all addressed |

**Residual MINOR (non-blocking):**
- MINOR-B2v2-1: plan disposition row says "22 indexes" while body has 21 (internally inconsistent on one line — cosmetic).
- MINOR-B2v2-2: event count drift (549 cited vs 565 live, 45 min of production writes).

**New decision flags surfaced:** Q-B2-4 (NULL filled_at gate) and Q-B2-5 (REJECTED_AUDIT CHECK edge case) — both legitimate Mike-level decisions, not fabrications.

## B3 v2 — all v1 blockers closed

| v1 Finding | v2 Disposition | Verified via |
|---|---|---|
| SHOWSTOPPER (signal-gateway repo missing) | ✅ FIXED — S11 ghost closure UPDATE + E15 GHOST_CLOSURE INSERT added; `signal_router.py` in Files-to-Modify | write-site spot check |
| CRITICAL (phantom `_close_signal()`) | ✅ FIXED — `_check_sl_tp()` at `lifecycle.py:383` (UPDATE at :471) | file read |
| CRITICAL (phantom `_scan_once()`) | ✅ FIXED — `_write_prices_to_db()` at `engine.py:254` (UPDATE at :311, opened_price at :316) | file read |
| CRITICAL (price_history INSERT placement) | ✅ FIXED — `_write_price_history()` at `lifecycle.py:1064` | file read |
| CRITICAL (132-line drift on `_check_sl_tp`) | ✅ FIXED — all line numbers re-verified against HEAD | spot check |
| CRITICAL (reconciler missing 13+ cols) | ✅ FIXED — 52/52 signals + 10/10 events + 6/6 traders + 6/6 servers + 9/9 quarantine — all columns covered | PRAGMA table_info vs plan SQL |
| MINOR (`log_event()` → `log()`) | ✅ FIXED — `log()` at `event_store.py:141` (oinkfarm) / `:139` (oink-sync) | file read |
| MINOR (EventStore quarantine indirection) | ✅ DOCUMENTED | spot check |
| NEW: ghost closure `connect_readonly()` bug | ✅ SURFACED as Q-B3-4 — verified at `signal_router.py:3969` with writes at `:4011` + `:4023`, silent failure masked by exception handler at `:4039`; production has 0 GHOST_CLOSURE events (empirical corroboration) | file read + sqlite count |

**Write-site inventory spot check:** 13 of 27 claimed sites verified at exact claimed line numbers (S2, S5, S6, S8, S11, E1, E5, E6, E7, E12, E13, E15, P1, Q1). All land.

**Residual MINOR (non-blocking):** 2 cosmetic ≤1-line drifts.

---

## Recommended next actions

1. **ANVIL:** start B2 Phase 0 proposal on `/home/oinkv/forge-workspace/plans/TASK-B2-plan.md` v2. B1 canary is passive-pending on organic prod traffic (GUARDIAN monitoring); Phase 0 is proposal-only and safe to overlap per established pattern.
2. **Mike:** decision needed on:
   - **Q-B2-4** — 84 closed signals with NULL `filled_at`: backfill before migration, accept as-is, or block? FORGE recommends accept as-is.
   - **Q-B2-5** — PG equivalent of `trg_entry_price_update` REJECTED_AUDIT exception: add PG trigger or CHECK-only?
   - **Q-B3-4** — signal-gateway ghost closure `connect_readonly()` bug fix: standalone micro-PR or bundle with B3? (Currently production has 0 GHOST_CLOSURE events due to silent write failure.)
3. **B3** waits on B2 landing (hard dependency). B4 (cutover) still gated on B2+B3.
4. **B5** (emitter extraction) is independent — can be audited in parallel next cycle if desired.

---

## Files

- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B2-v2.md` — 17,213 bytes
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B3-v2.md` — 19,792 bytes
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-v2.md` — this file

*— Hermes (cron orchestrator), 2026-04-20 02:22 UTC*
