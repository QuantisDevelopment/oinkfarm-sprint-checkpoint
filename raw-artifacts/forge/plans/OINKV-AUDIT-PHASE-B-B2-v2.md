# OinkV Engineering Audit — FORGE Plan B2 v2 (Hermes fallback)

**Auditor:** Hermes subagent (fallback; OinkV main lane LLM-timing-out per journalctl 2026-04-20T01:57 / 02:01 / 02:12)
**Date:** 2026-04-20 02:17 CEST
**Plan:** `/home/oinkv/forge-workspace/plans/TASK-B2-plan.md`
- Size: **32,808 bytes** (556 lines)
- mtime: **2026-04-20 01:43 CEST**
- Revision: **v2** (response to audit OINKV-AUDIT-PHASE-B-B2.md REJECT verdict)
**Tier:** 🔴 CRITICAL — Core infra migration, data-safety sensitive
**Canonical commits verified 2026-04-20 02:13 UTC:**
- oinkfarm `/home/oinkv/.openclaw/workspace` @ **`0fbcbf1b`** (B1 merged + 2 post-merge fixes) ✅ cited in plan §0
- oink-sync `/home/oinkv/oink-sync` @ **`ecd2622`** ✅ cited in plan §0
- signal-gateway `/home/oinkv/signal-gateway` @ **`b0f0254`** ✅ cited in plan §0
- Stale v1 hashes (`50b23834`, `e9be741`, `c6cb99e`) — **absent** ✅
- Historical hash `46154543` (A8 sl_type provenance) — retained intentionally in §1 as a citation of when A8 landed; not a staleness issue. ✅

**DB row counts verified `sqlite3 /home/m/data/oinkfarm.db` 2026-04-20 02:15 CEST:**

| Table | Live | Plan cites | Drift | Status |
|-------|------|-----------|-------|--------|
| signals | 1,409 | 1,409 | 0 | ✅ exact |
| signal_events | 565 | 549 | +16 | ⚠️ acceptable (~45 min old snapshot; events grow ~0.4/min) |
| traders | 100 | 100 | 0 | ✅ exact |
| servers | 11 | 11 | 0 | ✅ exact |
| price_history | 284,736 | 284,112 | +624 | ⚠️ acceptable (~25 min @ ~1.5k/hr growth, plan explicitly says "growing ~1.5k/hour") |
| quarantine | 23 | 23 | 0 | ✅ exact |
| audit_log | 0 | 0 | 0 | ✅ exact |

**Live schema verified:** 52 columns on signals (incl. A8 `sl_type` + A11 `leverage_source`), 10 columns on signal_events (incl. A1 `field`/`old_value`/`new_value`/`source_msg_id`), 7 tables total, 21 explicit indexes (non-autoindex), 6 CHECK constraints, 5 triggers, 2 auto-indexes for UNIQUE on `servers.discord_id` + `traders(name, server_id)`.

---

## Summary

- **Findings:** 0 critical · 0 major · 2 minor · 14 confirmed-fixed
- **Verdict:** **✅ SHIP-READY**
- **Headline:** FORGE v2 has comprehensively addressed every finding from the v1 REJECT audit. All five fabricated table DDLs have been regenerated from live `.schema` output and independently match the current SQLite schema column-for-column. All 6 CHECK constraints are translated 1:1. The 5 triggers are correctly analyzed (4 fully redundant with CHECKs/FK, 1 `REJECTED_AUDIT` edge case escalated as Q-B2-5 decision). All 21 explicit indexes are present with correct partial-index syntax. Row counts are refreshed and within expected drift. The NULL `filled_at` data-quality debt is correctly surfaced with a pre-migration gate (Q-B2-4). The only remaining issues are two cosmetic inconsistencies that do not affect correctness.

---

## Critical Findings

**None.** All 6 v1 CRITICAL findings are fixed. See §Audit Disposition for evidence per finding.

---

## Major Findings

**None.** All 5 v1 MAJOR findings are fixed.

---

## Minor Findings

### MINOR-B2v2-1 — Disposition table row says "22 production indexes" but body/§6/§10 correctly say 21

- **Plan line 28:** `| MAJOR-B2-5 (5/11 indexes) | ✅ FIXED — all 22 production indexes translated 1:1 |`
- **Plan §3 DDL body:** contains exactly **21** `CREATE INDEX` statements (verified via grep: lines 171, 249, 250, 252, 253, 254, 255, 256, 257, 258, 259, 260, 280, 281, 282, 296, 297, 315, 316, 331, 332).
- **Plan §3 header (line 142):** `-- Tables: 7 | Indexes: 21 | CHECK constraints: 6 | Sequences: 7` ✅
- **Plan §6 acceptance (line 489):** `all 21 indexes, all 6 CHECK constraints` ✅
- **Plan §10 evidence (line 542):** `21 indexes (11 signals, 3 signal_events, 2 price_history, 2 quarantine, 2 audit_log, 1 traders) + UNIQUE(name, server_id) implicit index on traders` ✅
- **Live verified:** `SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'` → **21** (+ 2 autoindexes for UNIQUE constraints on servers.discord_id + traders(name, server_id), which PostgreSQL auto-creates from the `UNIQUE` clauses in the DDL).
- **Impact:** Cosmetic. The "22" in the disposition row could be read as counting the implicit traders UNIQUE index, but it contradicts the rest of the document. No effect on DDL correctness.
- **Suggested fix:** Change disposition line 28 to "all 21 production indexes translated 1:1 (plus 2 implicit UNIQUE indexes auto-created by CREATE TABLE)".

### MINOR-B2v2-2 — signal_events row count mildly stale (549 cited vs 565 live)

- **Plan cites:** 549 signal_events rows (captured 2026-04-20 01:32 CEST per §0 line 12).
- **Live count at 02:15:** 565 (+16 events in ~43 minutes = ~0.37/min, consistent with typical event-log write rate).
- **Impact:** Acceptable drift per the task's "Allow minor drift" instruction. The plan's §3 baseline-count block is explicitly labelled `"(to be re-verified at migration time)"` at line 352, so the stale figure is not an acceptance gate. Test spec §5 correctly says `"PG event count = 549 (or current SQLite count)"`.
- **Suggested fix:** None required; a pre-migration re-baseline is already in the plan.

---

## Confirmed Fixes

All items below have been cross-checked against live `sqlite3 /home/m/data/oinkfarm.db '.schema <table>'` output and verified 1:1.

1. ✅ **signals DDL (52 cols)** — every column in the live schema appears in plan DDL lines 177–230 with the correct type mapping (`FLOAT` → `DOUBLE PRECISION`, `DATETIME` → `TIMESTAMPTZ`, `BOOLEAN DEFAULT 0` → `BOOLEAN DEFAULT FALSE`). A8 `sl_type VARCHAR(15) DEFAULT 'FIXED'` and A11 `leverage_source VARCHAR(20) DEFAULT NULL` both present.
2. ✅ **signal_events DDL (10 cols)** — includes `field, old_value, new_value, source_msg_id` (the A1 diff columns that v1 dropped) and preserves `payload TEXT NOT NULL DEFAULT '{}'`. `BIGSERIAL` correctly chosen (maps SQLite `INTEGER PRIMARY KEY AUTOINCREMENT`).
3. ✅ **traders DDL (6 cols)** — `id, discord_id, name, server_id REFERENCES servers(id), first_seen, last_seen` + `UNIQUE(name, server_id)` + `ix_traders_name`. The v1-fabricated `confidence/aliases/notes/created_at/updated_at/platform` columns are removed.
4. ✅ **servers DDL (6 cols)** — `id, discord_id VARCHAR(20) NOT NULL UNIQUE` (not the v1-fabricated `discord_server_id`), `name VARCHAR(100) NOT NULL`, `enabled BOOLEAN NOT NULL DEFAULT TRUE`, `signal_channel_ids TEXT NOT NULL DEFAULT '[]'` (restored — this is routing-critical), `added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
5. ✅ **price_history DDL (5 cols)** — unchanged from v1 (v1 got this right); confirmed still correct.
6. ✅ **quarantine DDL (9 cols)** — completely regenerated: `id BIGSERIAL, signal_id TEXT (not INTEGER — matches SQLite's TEXT typing), error_code TEXT NOT NULL, error_detail, raw_payload TEXT NOT NULL DEFAULT '', source, created_at, resolved_at, resolution`. The 2 partial + regular indexes both present.
7. ✅ **audit_log DDL (6 cols + FK restored)** — `signal_id INTEGER NOT NULL REFERENCES signals(id)` restored. The v1-fabricated `table_name/record_id/actor` removed.
8. ✅ **All 6 CHECK constraints translated 1:1:**
   | CHECK | Live SQLite | Plan DDL | Line |
   |-------|-------------|----------|------|
   | `direction IN ('LONG','SHORT')` | ✅ | ✅ | 186 |
   | `order_type IN ('MARKET','LIMIT')` | ✅ | ✅ | 187 |
   | `entry_price > 0` | ✅ | ✅ | 188 |
   | `confidence >= 0 AND confidence <= 1` | ✅ | ✅ | 195 |
   | `exchange_matched IN (0, 1)` | ✅ | ✅ | 198 |
   | `status = UPPER(status)` | ✅ | ✅ | 202 |
9. ✅ **All 5 triggers analyzed with correct disposition:**
   | Trigger | Live behaviour | Plan disposition | Correct? |
   |---------|----------------|------------------|----------|
   | `trg_entry_price_insert` | RAISE if `entry_price <= 0` on INSERT | Redundant with CHECK | ✅ (CHECKs fire on both INSERT and UPDATE in PG) |
   | `trg_entry_price_update` | RAISE if `entry_price <= 0` on UPDATE **unless `status='REJECTED_AUDIT'`** | Redundant with CHECK *modulo* REJECTED_AUDIT exception — flagged as **Q-B2-5** for Mike | ✅ correctly surfaced |
   | `trg_status_upper_insert` | RAISE if `status != UPPER(status)` on INSERT | Redundant with CHECK | ✅ |
   | `trg_status_upper_update` | RAISE if `status != UPPER(status)` on UPDATE | Redundant with CHECK | ✅ |
   | `trg_signals_server_id_check` | RAISE if `server_id NOT IN (SELECT id FROM servers)` | Replaced by `REFERENCES servers(id)` FK | ✅ (proper FK is strictly stronger) |
10. ✅ **21 indexes all translated 1:1** (verified by enumerating `sqlite_master` indexes against grep of `CREATE INDEX` in plan). Partial indexes preserved with identical syntax (`WHERE status='ACTIVE' AND exchange_matched=1`, `WHERE fill_status='PENDING'`, `WHERE resolved_at IS NULL`).
11. ✅ **"50 columns" eradicated** — `grep -n "50 column\|50-column"` on plan returns zero matches. The string "52" appears in 9 distinct contexts (disposition, §0, §1, §3 header, §3 comment, §5 tests, §6 acceptance) consistently.
12. ✅ **Row counts refreshed** (see header table; all 7 tables cited, within drift).
13. ✅ **MAJOR-B2-3 (NULL filled_at) addressed** — Plan §3 line 365–378 adds the pre-migration data-quality gate, Q-B2-4 in §9 line 533 explicitly asks Mike to decide (backfill / accept / block). P1 MARKET-FILLED figure verified: live count = **0** (matches plan's claim "count is now 0"). Closed-signal NULL count verified: **84** (matches plan exactly).
14. ✅ **MINOR fixes:** FLOAT→DOUBLE risk re-framed as "no precision change" in §8 (line 515) ✅; explicit column lists mandated in §4c ("NOT `SELECT *`", line 417) ✅; `DEFAULT '{}'` preserved on `signal_events.payload` (line 270) ✅.

**Pre-migration violation scan (live):** I independently ran the CHECK-violation pre-scan queries against the live DB:
- `direction NOT IN ('LONG','SHORT')` → 0
- `status != UPPER(status)` → 0
- `entry_price <= 0` → 0
- `confidence < 0 OR confidence > 1` → 0
- `exchange_matched NOT IN (0,1)` → 0
- `order_type NOT IN ('MARKET','LIMIT')` → 0

Migration will not reject any existing row. FK scan: zero orphan `signal_id`/`server_id`/`trader_id` references. Schema is clean for cutover once Q-B2-4 is resolved.

---

## Audit Disposition Table (v1 findings → v2 status)

| Finding | v1 Severity | v2 Disposition | Evidence |
|---------|-------------|----------------|----------|
| **CRITICAL-B2-1** signal_events DDL fabricated (4 cols missing, 2 invented) | 🔴 | ✅ **FIXED** | Plan lines 266–277 contain all 10 real columns; `schema_version`/`actor` removed; `DEFAULT '{}'` preserved. Matches live `.schema signal_events`. |
| **CRITICAL-B2-2** traders DDL invents 6 cols, omits 2 | 🔴 | ✅ **FIXED** | Plan lines 161–169 match live (6 cols + `UNIQUE(name, server_id)` + `discord_id`). Fabricated cols gone. |
| **CRITICAL-B2-3** servers DDL wrong column names | 🔴 | ✅ **FIXED** | Plan lines 148–155 use `discord_id` (not `discord_server_id`), restore `enabled`, `signal_channel_ids`, `added_at`. Matches live. |
| **CRITICAL-B2-4** quarantine DDL completely wrong | 🔴 | ✅ **FIXED** | Plan lines 303–313 use real columns (`signal_id TEXT`, `error_code`, `error_detail`, `raw_payload DEFAULT ''`, `source`, `resolved_at`, `resolution`). Matches live. |
| **CRITICAL-B2-5** audit_log drops FK + invents 3 cols | 🔴 | ✅ **FIXED** | Plan lines 322–329 restore `signal_id INTEGER NOT NULL REFERENCES signals(id)`; `table_name/record_id/actor` removed. Matches live. |
| **CRITICAL-B2-6** 5 CHECKs + 5 triggers dropped | 🔴 | ✅ **FIXED** | All 6 CHECKs translated 1:1 (see Confirmed #8). Triggers correctly analyzed as redundant-with-CHECK-or-FK except `trg_entry_price_update` REJECTED_AUDIT exception → escalated as Q-B2-5. |
| **MAJOR-B2-1** "50 columns" → 52 | 🟡 | ✅ **FIXED** | `grep "50 column\|50-column"` returns 0 matches; "52" appears consistently in 9 contexts. |
| **MAJOR-B2-2** Row counts wrong (plan said 1144; actual was 1407) | 🟡 | ✅ **FIXED** | Plan cites 1,409 signals (matches live exactly). Other counts within acceptable drift. |
| **MAJOR-B2-3** A10 NULL filled_at not addressed | 🟡 | ✅ **FIXED** | Pre-migration gate §3 lines 365–378; Q-B2-4 decision flag §9 line 533; P1 (0 MARKET-FILLED NULLs) and broader (84 closed) counts both independently verified. |
| **MAJOR-B2-4** price_history batch undersized | 🟡 | ✅ **FIXED** | Plan §4c line 432 quotes 284,112 rows + explicit COPY recommendation + wall-clock estimate (5–15s COPY / 30–60s INSERT). Test `test_price_history_count_match` added (§5). |
| **MAJOR-B2-5** 5/11 indexes, 2 invented | 🟡 | ✅ **FIXED** | All 21 explicit indexes present; partial-index syntax preserved; v1-fabricated `idx_signals_discord_msg`/`idx_signals_trader` absent. |
| **MINOR-B2-1** FLOAT→DOUBLE risk mis-framed | 🟢 | ✅ **FIXED** | Plan §8 line 515: `"FLOAT → DOUBLE PRECISION | None | No precision change (both are IEEE-754 double)"`. |
| **MINOR-B2-2** Column order drift | 🟢 | ✅ **FIXED** | Plan §4c line 417: `"explicit column list (NOT SELECT *)"`. Schema Translation Summary (§3) documents the policy. |
| **MINOR-B2-3** signal_events.payload default lost | 🟢 | ✅ **FIXED** | Plan line 270: `payload TEXT NOT NULL DEFAULT '{}'`. |

---

## New Findings Introduced by v2

**No new CRITICAL or MAJOR findings.** Two minor items (see §Minor Findings):

- **MINOR-B2v2-1:** disposition table line 28 claims "22 production indexes" while body + acceptance + evidence sections consistently say 21. Cosmetic inconsistency.
- **MINOR-B2v2-2:** `signal_events` count cited as 549; live is 565 (+16 in ~45 min). Within acceptable drift; plan's pre-migration re-baseline step (§3 line 352) covers this.

**No fabrications detected.** The DDL in §3 reproduces the live `.schema` output faithfully. The two new design questions (Q-B2-4 NULL filled_at, Q-B2-5 REJECTED_AUDIT trigger exception) are legitimate Mike-level decisions raised correctly.

**Additional positive observations:**
- Plan §4d correctly notes SQLite stores datetimes as TEXT in two formats (ISO-8601 with microseconds, and without timezone) and that PostgreSQL TIMESTAMPTZ parses both. This matches the actual data in the DB.
- Plan §4e ID preservation + sequence reset via `setval()` is the correct pattern.
- Plan §4f correctly states SQLite `BOOLEAN DEFAULT 0/1` is accepted by PG `BOOLEAN` natively; no transformation required.
- Plan §7 Rollback is simple and correct: drop DB, set `OINK_DB_ENGINE=sqlite`. SQLite is never modified by B2, so rollback is zero-data-loss.
- All 23 tests in §5 are concrete and measurable. CHECK-violation tests cover all 6 constraints individually. FK-integrity + sequence-correctness + datetime-preservation + NULL-preservation + partial-index-used all included.

---

## Verdict

**✅ SHIP-READY**

All 6 v1 CRITICAL findings and all 5 v1 MAJOR findings are verifiably fixed against live schema. No new fabrications introduced. The two MINOR issues are cosmetic and do not affect migration correctness. Mike decisions Q-B2-4 (NULL filled_at gate) and Q-B2-5 (REJECTED_AUDIT trigger edge case) are legitimate and must be resolved before ANVIL executes the migration against production — but the plan itself is safe to implement and tests.

**Recommended next steps:**
1. FORGE may optionally patch MINOR-B2v2-1 (change "22" → "21" on line 28) — 30-second edit, not blocking.
2. ANVIL can begin implementation of `001_pg_schema.sql` and `migrate_sqlite_to_pg.py` per §3–§4.
3. GUARDIAN to weigh in on Q-B2-4 data-quality recommendation before migration is run against production (plan drafting unblocked).
4. Mike to approve Q-B2-4 and Q-B2-5 before migration execution.

---

## Audit Coverage Notes

**DB queries run (read-only, via `sqlite3 /home/m/data/oinkfarm.db`):**
- `.schema signals/signal_events/traders/servers/price_history/quarantine/audit_log` (all 7 tables)
- Row counts via `COUNT(*)` on every table
- `sqlite_master` enumeration of indexes (21 non-autoindex + 2 autoindex)
- FK-orphan scans: signal_events→signals, price_history→signals, traders→servers, signals→servers, signals→traders (all 0 orphans)
- CHECK-violation scans: direction, status, entry_price, confidence, exchange_matched, order_type (all 0 violations)
- NULL filled_at scans: MARKET-FILLED (0) and all-closed (84) — both match plan claims

**Files read:**
- `/home/oinkv/forge-workspace/plans/TASK-B2-plan.md` (full, 556 lines)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B2.md` (v1 audit — for disposition reference)
- `/home/oinkv/forge-workspace/plans/PHASE-B-WAVE1-REVISION-v2.md` (delta summary)

**Safety rails honored:**
- Read-only DB access (SELECT, PRAGMA, .schema only). No writes to `/home/m/data/oinkfarm.db`.
- No source file modifications.
- No `openclaw agent` dispatch.
- No git commits/pushes.
- No long-running processes started.
- `/home/oinkv/.openclaw/workspace` untouched.
- Only write: this audit file at `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B2-v2.md`.
