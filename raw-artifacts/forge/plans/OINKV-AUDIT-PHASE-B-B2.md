# OinkV Engineering Audit — FORGE Plan B2 (Hermes fallback)

**Auditor:** Hermes subagent (fallback; OinkV main lane unavailable)
**Date:** 2026-04-19
**Plan:** `/home/oinkv/forge-workspace/plans/TASK-B2-plan.md` (16,498 bytes, mtime 2026-04-19 18:04 CEST)
**Tier:** 🔴 CRITICAL
**Base DB verified:** `/home/m/data/oinkfarm.db` (post-A10 merge 2026-04-19T18:29:23Z, **1407 signals**)
**Canonical commits:** oinkfarm `50b23834`, oink-sync `e9be741`, signal-gateway `c6cb99e`

---

## Summary

- **Findings:** 6 critical · 5 major · 3 minor · 2 confirmed
- **Verdict:** **REJECT — REWRITE REQUIRED**
- **Headline:** The plan's PostgreSQL DDL for **five of the seven tables (`signal_events`, `traders`, `servers`, `quarantine`, `audit_log`)** is fabricated — it does not match the actual SQLite schema at all. Running this migration as written would silently lose real production columns (e.g. `signal_events.field/old_value/new_value/source_msg_id` — the entire A1 diff/audit payload), invent columns that do not exist (e.g. `traders.confidence/aliases/notes`, `audit_log.table_name/record_id`), and break foreign keys (e.g. `audit_log.signal_id` is dropped). The `signals` table DDL is mostly correct (52 columns, matches actual) but the prose around it repeatedly says **"50 columns"**, the spot-check test says "All 50 columns match", and 7 of 11 production indexes plus all 5 triggers and 5 CHECK constraints are absent. Row-count expectations are also wrong (plan says ~1144 or ~493; actual is 1407).

This is not a staleness drift — it is a planning error where FORGE appears to have hallucinated schemas for 5 tables rather than reading them.

---

## Critical Staleness / Fabrication

### CRITICAL-B2-1 — `signal_events` DDL is wrong (missing 4 columns, invents 2)
- **Plan §3 DDL (lines 217–226):**
  ```sql
  CREATE TABLE IF NOT EXISTS signal_events (
      id SERIAL PRIMARY KEY,
      signal_id INTEGER NOT NULL REFERENCES signals(id),
      event_type VARCHAR(30) NOT NULL,
      payload TEXT,
      source VARCHAR(50) DEFAULT 'system',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      schema_version INTEGER DEFAULT 1,
      actor VARCHAR(50) DEFAULT 'system'
  );
  ```
- **Actual SQLite (`PRAGMA table_info(signal_events)`):** 10 columns
  ```
  id, signal_id, event_type,
  payload TEXT NOT NULL DEFAULT '{}',          -- plan says TEXT (nullable, no default)
  source TEXT,                                  -- plan VARCHAR(50) DEFAULT 'system'
  created_at TEXT DEFAULT strftime(...),        -- plan TIMESTAMPTZ DEFAULT NOW()
  field TEXT,                                   -- MISSING FROM PLAN (A1 diff column)
  old_value TEXT,                               -- MISSING FROM PLAN (A1 diff column)
  new_value TEXT,                               -- MISSING FROM PLAN (A1 diff column)
  source_msg_id TEXT                            -- MISSING FROM PLAN (A1 provenance column)
  ```
- **Plan invents:** `schema_version INTEGER DEFAULT 1`, `actor VARCHAR(50) DEFAULT 'system'` — **neither column exists in the SQLite DB**.
- **Impact:** Migration as written drops the four A1-era diff/audit columns entirely. `signal_events` is the Phase 4 event-log backbone; losing `field/old_value/new_value/source_msg_id` means every STATUS_CHANGED, TP_HIT, SL_MODIFIED row loses its audit payload. This is **silent data loss of the feature A1 just shipped.** Any dashboard that filters `WHERE field='status'` stops working.
- **Suggested fix:** Replace the DDL with:
  ```sql
  CREATE TABLE signal_events (
      id BIGSERIAL PRIMARY KEY,
      signal_id INTEGER NOT NULL REFERENCES signals(id),
      event_type TEXT NOT NULL,
      payload TEXT NOT NULL DEFAULT '{}',
      source TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      field TEXT,
      old_value TEXT,
      new_value TEXT,
      source_msg_id TEXT
  );
  CREATE INDEX idx_events_signal ON signal_events(signal_id, event_type);  -- composite, not two singles
  CREATE INDEX idx_events_time   ON signal_events(created_at);
  CREATE INDEX idx_events_type   ON signal_events(event_type);
  ```

### CRITICAL-B2-2 — `traders` DDL invents 6 columns, omits 2
- **Plan §1 line 94:** `traders — id, name, server_id, confidence, aliases, last_seen, notes, created_at, updated_at, platform`
- **Plan §3 DDL (lines 142–153):** 10 columns including `confidence FLOAT, aliases TEXT, notes TEXT, created_at, updated_at, platform`
- **Actual (`PRAGMA table_info(traders)`):** 6 columns only
  ```
  id, discord_id VARCHAR(20), name VARCHAR(50) NOT NULL,
  server_id INTEGER NOT NULL REFERENCES servers(id),
  first_seen DATETIME NOT NULL DEFAULT (datetime('now')),
  last_seen  DATETIME NOT NULL DEFAULT (datetime('now'))
  UNIQUE(name, server_id)
  ```
- **Missing from plan:** `discord_id`, `first_seen`, `UNIQUE(name, server_id)` constraint.
- **Fabricated by plan:** `confidence`, `aliases`, `notes`, `created_at`, `updated_at`, `platform`. None of these columns exist in production. 100 trader rows will fail to migrate because the INSERT won't provide values for the invented NOT-NULL-able-looking columns, OR (worse) the migration script will silently write NULL/default into invented columns and drop `discord_id` on the floor.
- **Suggested fix:** DDL must match:
  ```sql
  CREATE TABLE traders (
      id SERIAL PRIMARY KEY,
      discord_id VARCHAR(20),
      name VARCHAR(50) NOT NULL,
      server_id INTEGER NOT NULL REFERENCES servers(id),
      first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      last_seen  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(name, server_id)
  );
  CREATE INDEX ix_traders_name ON traders(name);
  ```

### CRITICAL-B2-3 — `servers` DDL column names/shape do not match
- **Plan §3 DDL (lines 132–140):**
  ```sql
  id, discord_server_id VARCHAR(20) UNIQUE, name VARCHAR(200),
  platform VARCHAR(20) DEFAULT 'discord',
  category VARCHAR(50),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
  ```
- **Actual:**
  ```sql
  id, discord_id VARCHAR(20) NOT NULL UNIQUE,  -- NOT "discord_server_id"
  name VARCHAR(100) NOT NULL,                   -- not NULLable, VARCHAR(100) not 200
  enabled BOOLEAN NOT NULL DEFAULT 1,
  signal_channel_ids TEXT NOT NULL DEFAULT '[]',
  added_at DATETIME NOT NULL DEFAULT (datetime('now'))
  ```
- **Renamed:** `discord_id` → `discord_server_id` (column simply doesn't exist under plan's name).
- **Fabricated:** `platform`, `category`, `status`.
- **Dropped:** `enabled`, `signal_channel_ids`, `added_at`. `signal_channel_ids` is operationally critical — it's the JSON list of channel IDs per server used by the Discord ingest; losing it breaks signal routing.
- **Impact:** Migration cannot succeed with this DDL. Even if the script tries `INSERT INTO servers (id, discord_id, ...)`, the `discord_id` column doesn't exist. If the script uses `SELECT * FROM servers` SQLite-side then positional inserts PG-side, the 11 rows land in totally wrong columns.

### CRITICAL-B2-4 — `quarantine` DDL is a completely different table
- **Plan §3 DDL (lines 243–253):**
  ```sql
  id, discord_message_id VARCHAR(20), channel_id VARCHAR(20), server_id INTEGER,
  raw_text TEXT, reason_code VARCHAR(50), reason_detail TEXT, extra_json TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
  ```
- **Actual:**
  ```sql
  id, signal_id TEXT,
  error_code TEXT NOT NULL, error_detail TEXT,
  raw_payload TEXT NOT NULL DEFAULT '',
  source TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
  resolved_at TEXT, resolution TEXT
  ```
- **Every column name differs:** `discord_message_id/channel_id/server_id/raw_text/reason_code/reason_detail/extra_json` do not exist. Actual uses `signal_id/error_code/error_detail/raw_payload/source/resolved_at/resolution`.
- **Impact:** Migration of the 20 quarantine rows will either blow up on schema mismatch or silently misalign columns. Quarantine is the error-audit trail — corrupting it during migration hides any data-quality regression that happens during cutover.

### CRITICAL-B2-5 — `audit_log` DDL drops FK and invents 3 columns
- **Plan §3 DDL (lines 255–264):** `id, action, table_name, record_id, old_value, new_value, timestamp, actor`
- **Actual:** `id, signal_id INTEGER NOT NULL REFERENCES signals(id), action VARCHAR(20), old_value, new_value, timestamp`
- **Dropped by plan:** `signal_id` (the FK to signals — this is the *entire purpose* of audit_log).
- **Fabricated:** `table_name`, `record_id`, `actor`.
- **Impact:** `audit_log` currently has 0 rows, so no data is lost today, but the plan bakes in a schema that has no FK to signals — meaning post-cutover audit writes from the existing code (which writes `signal_id`) will fail with "column does not exist", while fabricated `table_name/record_id/actor` will be unfilled.
- **Suggested fix:** `signal_id INTEGER NOT NULL REFERENCES signals(id)` restored, `table_name/record_id/actor` removed, or if a broader audit model is intended it needs to be a separate design doc, not a silent shape change inside a migration.

### CRITICAL-B2-6 — `signals` DDL drops 5 CHECK constraints and 5 triggers
- **Plan §3 signals DDL (lines 155–208):** column set is correct (52 cols — see CONFIRMED-B2-1), but it carries **no** CHECK constraints and no triggers.
- **Actual signals table carries these integrity guards that are all erased by the plan:**
  ```sql
  CHECK (direction IN ('LONG','SHORT'))
  CHECK (order_type IN ('MARKET','LIMIT'))
  CHECK (entry_price > 0)
  CHECK (confidence >= 0 AND confidence <= 1)
  CHECK (exchange_matched IN (0,1))
  CHECK (status = UPPER(status))
  ```
  Plus triggers:
  ```
  trg_entry_price_insert / trg_entry_price_update     (entry_price > 0)
  trg_status_upper_insert / trg_status_upper_update   (status = UPPER(status))
  trg_signals_server_id_check                         (server_id must exist in servers)
  ```
- **Impact:** Post-cutover, any future code regression that tries to write `direction='long'` or `entry_price=0` or `status='active'` will now succeed in PostgreSQL where SQLite would have raised. This is a silent downgrade of data-integrity protection — the micro-gate contract assumes these constraints hold. The `ix_signal_status` index + `status = UPPER(status)` check pair is load-bearing for Guardian's SC-1 / KPI-R5 canary queries, which use `status IN ('ACTIVE',...)` uppercase literals.
- **Suggested fix:** Translate each CHECK 1:1 (PostgreSQL supports all of them unchanged). Replace SQLite triggers with equivalent PL/pgSQL BEFORE INSERT/UPDATE triggers OR just keep the CHECKs (CHECKs cover the same ground for entry_price and status; the server_id trigger is a poor-man's FK and can become a proper `REFERENCES servers(id)` — which the plan already has).

---

## Major Staleness

### MAJOR-B2-1 — "50 columns" label is wrong; should be 52 (A8 + A11 landed before plan mtime)
- **Plan §0 line 15:** *"signals: 50 columns, signal_events, traders, servers, price_history, quarantine, audit_log"*
- **Plan §1 line 25:** *"**signals** — 50 columns:"*
- **Plan §9 line 433:** *"Schema verified: `PRAGMA table_info(signals)` — 50 columns confirmed"*
- **Plan §5 test line 376:** *"All 50 columns match between SQLite and PostgreSQL"*
- **Plan §6 acceptance line 390:** *"Schema matches SQLite exactly (50 signal columns, all tables, all indexes)"*
- **Actual:** `PRAGMA table_info(signals) | wc -l` → **52**. The two added columns are:
  - `leverage_source VARCHAR(20) DEFAULT NULL` — shipped by **A11** at 2026-04-19 16:54 CEST (commit `45a6931d`), **70 minutes before plan mtime 18:04 CEST**.
  - `sl_type VARCHAR(15) DEFAULT 'FIXED'` — shipped by **A8** at 2026-04-19 15:52 CEST (commit `46154543`, which the plan explicitly cites in §0 line 7 as the micro-gate HEAD), **132 minutes before plan mtime**.
- **Important nuance:** The plan's signals **DDL body does include both columns** (lines 206–207 — `sl_type VARCHAR(15) DEFAULT 'FIXED'` and `leverage_source VARCHAR(20)`). So the DDL itself is correct for columns. Only the **label** and **test spec** and **acceptance criteria** still say "50". This is cosmetic staleness in five places but it will mislead the reviewer into believing the plan missed A8/A11 when in fact it caught them in the DDL.
- **Impact:** Moderate. The count label and acceptance gate ("50 columns match") will fail verification if taken literally. ANVIL or Guardian running the acceptance check against `wc -l` of `PRAGMA table_info` will report FAIL on a working migration.
- **Suggested fix:** Replace every occurrence of "50 columns" with "52 columns", and cite A8 (`46154543`) + A11 (`45a6931d`) in §1 as the reason.

### MAJOR-B2-2 — Row-count expectations are both wrong (post-A10 is 1407, not 1144)
- **Plan §3 line 272:** *"expected: ~1144 (post A10 merge) or ~493 (pre-merge)"*
- **Actual:**
  ```
  SELECT COUNT(*) FROM signals;           -- 1407   (not 1144, not 493)
  SELECT COUNT(*) FROM signals WHERE id BETWEEN 1612 AND 2523;  -- 912   (A10 import range)
  SELECT COUNT(*) FROM signals WHERE id < 1612;                  -- 494  (plan said "493")
  SELECT MIN(id), MAX(id) FROM signals;   -- 499 ... 2524
  ```
- **The pre-A10 figure:** The plan's "~493" is off by one; actual pre-A10 count is **494** (A10 was a pure append of 912 new IDs 1612–2523 + 1 organic post-merge insert at id=2524).
- **The post-A10 figure:** The plan's "~1144" is nowhere close to actual **1407**. There is no moment in the DB's history at which it had 1144 signals. FORGE appears to have guessed, or confused a different count.
- **A10 merged at 2026-04-19T18:29:23Z, 25 minutes AFTER the plan mtime (18:04 CEST = 16:04Z).** So FORGE did not see A10 at the time of writing. The plan does attempt to address A10 anyway ("~1144 (post A10 merge)") — but the number it chose is wrong. This is worse than silence: it signals FORGE was aware of A10 but never verified.
- **Impact:** The `test_signal_count_match` (§5, line 374) will fail regardless of how the migration behaves because the baseline expectation is wrong. ANVIL / Guardian will need to re-derive the numbers themselves.
- **Suggested fix:** Change §3 pre-migration block to:
  ```
  SELECT COUNT(*) FROM signals;           -- 1407 (as of 2026-04-19 post-A10)
  SELECT COUNT(*) FROM signal_events;    -- 442
  SELECT COUNT(*) FROM traders;          -- 100
  SELECT COUNT(*) FROM servers;          -- 11
  SELECT COUNT(*) FROM price_history;    -- 280,732   <-- plan did NOT estimate this
  SELECT COUNT(*) FROM quarantine;       -- 20
  SELECT COUNT(*) FROM audit_log;        -- 0
  ```
  And re-cost the 1000-row batch assumption against **~281k** price_history rows (see MAJOR-B2-4).

### MAJOR-B2-3 — A10's NULL-`filled_at` P1 regression is not addressed
- **Background:** Guardian currently holds an **open P1 alert** (`2026-04-19-P1-a10-filled-at-regression.md`): 104 of the 912 A10-imported signals have `fill_status='FILLED' AND filled_at IS NULL AND order_type='MARKET'`. Zero such rows exist outside the A10 range. This violates KPI-R5.
- **Broader picture:** 187 rows across the DB have `filled_at IS NULL AND status IN ('CLOSED_WIN','CLOSED_LOSS','CLOSED_BREAKEVEN','CLOSED_MANUAL')` (i.e., closed trades without a fill timestamp). All 187 are in the A10 import range — the pre-existing 494 rows are clean.
- **Plan §3 line 279:** Post-migration check only asserts `SELECT COUNT(*) FROM signals` matches. No mention of `filled_at` integrity, no preservation guarantee for NULL-vs-value patterns, no acknowledgement that PostgreSQL `TIMESTAMPTZ` columns will accept these 187 NULL values (they will — the column is nullable — but that means the KPI-R5 violation silently survives the migration).
- **Additionally:** Plan §4d line 358 claims *"PostgreSQL TIMESTAMPTZ parses both formats. The migration script does NOT need to transform datetime values — PostgreSQL handles the parsing."* This is true but only for non-null rows. The NULL pattern is preserved, which is exactly the problem: the plan's implicit assumption is that "byte-identical migration" is sufficient, but if Mike / Guardian decide to rollback A10 as the remediation, Phase B2 will have already cemented those NULLs in a second store.
- **Impact:** B2 must either (a) explicitly accept the 187-row data-quality debt and declare that cutover is frozen until the P1 is resolved, or (b) include a remediation step (backfill `filled_at` for the 104 MARKET-FILLED rows) as a migration prerequisite.
- **Suggested fix:** Add §4f "Pre-migration data-quality gate":
  ```sql
  -- Must be 0 before migration proceeds:
  SELECT COUNT(*) FROM signals
   WHERE fill_status='FILLED' AND filled_at IS NULL AND order_type='MARKET';
  ```
  and a reference to the P1 alert for remediation authority.

### MAJOR-B2-4 — `price_history` at ~281k rows, 1000-row batch is undersized for the test specification
- **Plan §4c line 347:** *"Batch INSERT into PostgreSQL (1000 rows per batch)"*
- **Plan §8 risk line 415:** *"Migration script OOM on large tables | Low | price_history could be large | Batch processing (1000 rows/batch)"*
- **Actual:** `SELECT COUNT(*) FROM price_history` → **280,732 rows** today, growing daily (this is the per-signal price tick history). That is **281 batches at 1000 rows each** for one table alone. At 50ms/batch for a single-statement copy, that's manageable (~15s), but the plan does not budget runtime or quote a tested wall-clock.
- The plan mentions TimescaleDB deferral (§9 Q-B2-3) without noting that a plain PG table at 281k rows growing linearly is exactly the shape TimescaleDB is designed for. FORGE's recommendation to defer is reasonable; the risk budget just needs to reflect actual size.
- **Impact:** Not a bug, but the risk table under-specifies. The `test_signal_count_match` etc. table in §5 omits `price_history` from its "MUST" checks — there's no `test_price_history_count_match`.
- **Suggested fix:** Add `test_price_history_count_match` to §5; update §8 "price_history could be large" to "price_history is 281k rows today (2026-04-19), ~1.5k/hour growth; batched `COPY` or 1000-row INSERT both viable".

### MAJOR-B2-5 — Index coverage is ~40% of production (5 plan vs 11 actual on signals)
- **Plan §3 lines 211–215:** Creates 5 indexes on signals: `idx_signals_discord_msg, idx_signals_trader, idx_signals_status, idx_signals_ticker, idx_signals_posted_at`.
- **Actual signals indexes (11):**
  ```
  ix_signal_dedup           (trader_id, ticker, direction, posted_at)   [COMPOSITE — critical for dedup]
  ix_signal_exchange_active (status, exchange_matched, exchange_ticker) [PARTIAL: WHERE status='ACTIVE' AND exchange_matched=1]
  ix_signal_fill_status     (fill_status)                               [PARTIAL: WHERE fill_status='PENDING']
  ix_signal_last_update     (last_trader_update)
  ix_signal_parent          (parent_signal_id)
  ix_signal_server_posted   (server_id, posted_at DESC)
  ix_signal_status          (status)
  ix_signal_status_posted   (status, posted_at DESC)
  ix_signal_ticker_trader   (ticker, trader_id)
  ix_signals_posted_at      (posted_at)
  ix_signals_ticker         (ticker)
  ```
- **Missing from plan:** `ix_signal_dedup` (composite dedup — used by micro-gate), `ix_signal_exchange_active` (partial — used by oink-sync engine for price tracking, see OINKV-AUDIT-WAVE2-A4.md CRITICAL-A4-1), `ix_signal_fill_status` (partial — PENDING fills), `ix_signal_last_update`, `ix_signal_parent`, `ix_signal_server_posted`, `ix_signal_status_posted`, `ix_signal_ticker_trader`. That's **7 of 11 missing** plus the composite shape of `idx_events_signal` (see CRITICAL-B2-1). Plan's singletons (`idx_signals_trader`, `idx_signals_discord_msg`) do not exist in production — FORGE invented them.
- **Impact:** Every query that oink-sync's `engine.py` runs (see the existing Wave-2 A4 audit) hits `WHERE status='ACTIVE' AND exchange_matched=1` — that's a partial-index query. Without the partial index, PostgreSQL falls back to a sequential scan across 1407 rows per price tick (every 30–60s). At current scale that's fine; at 10×, it's a P2 perf regression.
- **Suggested fix:** Translate all 11 existing indexes 1:1. PostgreSQL supports partial indexes with identical syntax (`CREATE INDEX ... WHERE ...`).

---

## Minor Staleness

### MINOR-B2-1 — `current_price / leverage / entry_price` type widening is undocumented
Plan uses `DOUBLE PRECISION` throughout where actual uses `FLOAT`. In PostgreSQL, `FLOAT` without precision is `DOUBLE PRECISION` anyway, so this is a no-op — but §8 risk line 414 flags "FLOAT → DOUBLE PRECISION precision loss | Low | PnL rounding differences". It's the **other direction** (SQLite `FLOAT` is already IEEE-754 double-precision-ish, PostgreSQL `DOUBLE PRECISION` is identical). The risk is incorrectly framed as loss; if anything there's no change. Cosmetic.

### MINOR-B2-2 — Column order drift between plan DDL and actual
Actual `PRAGMA table_info` on signals lists `leverage_source` at position 50 and `sl_type` at position 51. Plan DDL lines 206–207 list them in the opposite order. Since B2 uses `SERIAL` with explicit column lists on INSERT (per §4c), column order doesn't affect correctness — but `SELECT *` comparisons in the spot-check test (§5 test_spot_check_signals) will fail on column order even when data is identical. Cosmetic but noted.

### MINOR-B2-3 — `signal_events.payload` default lost
Plan drops `DEFAULT '{}'` on `signal_events.payload`. Actual SQLite has `payload TEXT NOT NULL DEFAULT '{}'`. Any code path that relies on the default ('{}' as valid JSON) will break — the oink-sync `EventStore.log()` calls pass an explicit `payload=json.dumps(...)`, so it's defensive only, but it is a behavior change.

---

## Confirmed Accurate

1. ✅ **signals DDL column set is 52 columns and matches actual.** Spot-check: plan lists the same 52 column names (id … leverage_source) as `PRAGMA table_info(signals)` including `sl_type` and `leverage_source`. FORGE did catch A8 and A11 in the DDL body despite the "50 columns" label drift in the prose.
2. ✅ **price_history DDL is structurally correct.** Actual: `id, signal_id, price, pnl_percent, timestamp`. Plan: same five columns, types compatible. FK to signals preserved. This is the one non-signals table the plan got right.

---

## Open Questions

### OQ-B2-1 — Scope: can this plan be fixed in-place, or does it need a rewrite?
Five of seven tables have DDL that does not correspond to the production schema (CRITICAL-B2-1 through -5). The signals DDL has the right columns but missing constraints / indexes / triggers (CRITICAL-B2-6). The counts and batch sizing are wrong. At that level of drift, patching introduces more risk than starting from `.schema` dumps of every table. **Recommendation for Mike: reject and require FORGE to regenerate §3 and §5 from live `sqlite3 .schema` output, not from memory.**

### OQ-B2-2 — Should B2 block on the A10 P1 alert?
CRITICAL-B2-3 flags that the migration silently preserves 104 KPI-R5-violating rows (NULL `filled_at` on imported MARKET-FILLED). If Mike accepts the A10 import as-is, the P1 remains in PostgreSQL and B2 is fine. If Mike rolls A10 back (per Guardian's recommendation), B2 must not run until that is decided. **Recommendation for Mike: sequence — resolve A10 P1 first, then re-baseline B2's pre-migration counts, then proceed.**

### OQ-B2-3 — Triggers: translate to PL/pgSQL or drop?
CRITICAL-B2-6 flags that 5 SQLite triggers are absent. The `CHECK` constraints cover most of the ground (entry_price > 0, status=UPPER(status)). The `trg_signals_server_id_check` trigger is redundant with the `REFERENCES servers(id)` FK, which the plan already has. The status-uppercase and entry-price-positive triggers are redundant with the CHECKs. So if the CHECKs are restored, the triggers are provably redundant and can be dropped. **Recommendation for Mike: accept dropping the triggers, require restoring the 6 CHECKs.**

---

## Audit Coverage Notes

- **DB queries run (read-only, via `sqlite3 /home/m/data/oinkfarm.db`):**
  - `PRAGMA table_info` for all 7 tables (signals, signal_events, traders, servers, price_history, quarantine, audit_log)
  - `.schema` for all 7 tables (captures CHECKs, triggers, indexes, defaults)
  - `COUNT(*)` + `MIN/MAX(id)` on signals; counts on all other tables
  - Breakdown of A10 range `WHERE id BETWEEN 1612 AND 2523` by status and fill_status
  - Cross-check of `filled_at IS NULL` population (187 total, 104 MARKET-FILLED, 0 outside A10 range)
  - Index and trigger inventories from `sqlite_master`
- **Files read:**
  - `/home/oinkv/forge-workspace/plans/TASK-B2-plan.md` (full)
  - `/home/oinkv/forge-workspace/plans/OINKV-AUDIT.md` (for format — first 100 lines)
  - `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE2-A4.md` (for format — full)
  - `/home/oinkv/guardian-workspace/reports/alerts/2026-04-19-P1-a10-filled-at-regression.md`
- **Not audited (out of scope for B2):**
  - B1's `oink_db.py` abstraction layer — plan assumes it exists; not verified in this audit.
  - The migration-script Python code — plan's §4c is a design sketch, not source.
  - TimescaleDB planning — plan defers to a later phase; out of scope.
  - Connection pooling / PgBouncer — deferred per §9 Q-B2-2.
- **Safety rails honored:** Read-only DB access (PRAGMA + SELECT + .schema only). No writes to `/home/m/data/oinkfarm.db`. No commits, pushes, or dispatches. Only output is this audit file.
