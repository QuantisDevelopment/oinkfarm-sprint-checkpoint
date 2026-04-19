# OINKV-AUDIT-WAVE3-A10 — Database Merge (Old + New)

**Plan:** `/home/oinkv/forge-workspace/plans/TASK-A10-plan.md` (v?, 288 lines, 12KB)
**Tier:** 🔴 CRITICAL — Mike-approval-gated, irreversible data migration
**Task:** A10 — Merge `/home/m/data/oinkfarm-old.db` (1,165 signals) into `/home/m/data/oinkfarm.db` (493/494 signals) via standalone `scripts/merge_databases.py`
**Audit Timestamp:** 2026-04-19 (Wave 3, post-A8 merge at 17:27Z)
**Audit Method:** Hermes fallback (OinkV LLM-timeout avoidance) — direct tool-driven schema, git-log, and arithmetic cross-check

**Base commits verified:**
- oinkfarm canonical at `/home/oinkv/.openclaw/workspace/` HEAD = **`46154543`** (feat(A8) merge #134, 2026-04-19 17:27:19 +0200)
- oink-sync at `/home/oinkv/oink-sync/` HEAD = **`e9be741`** (A4 merge #7); `ab5d941` is the **underlying squashed commit** for A4 sitting on branch `anvil/A4-partially-closed-status` (both resolve to the same A4 change surface)
- signal-gateway HEAD contains **`c6cb99e`** (A6 ghost closure, 2026-04-19 15:02) — affects runtime behavior but not oinkfarm.db schema
- Production DB `/home/oinkv/.openclaw/workspace/data/oinkfarm.db` → `/home/m/data/oinkfarm.db`: **494 signals, 52 columns, SQLite 3.46.1**

**⚠ Staleness indicator** — Plan header says "Codebase Verified At: 2026-04-19" but does NOT cite a base SHA. Between plan-draft time and this audit, four Wave-3 tickets merged:

| Ticket | Merged at | DB surface change |
|---|---|---|
| A1 (signal_events extension) | 2026-04-19 01:48 | signal_events schema widened; already in new DB |
| A9 (denomination normalization) | 2026-04-19 16:22 | Entry/SL/TP stored values normalized for 1000* tickers — **no column added** |
| A11 (leverage_source) | 2026-04-19 16:51 | **new column: `leverage_source VARCHAR(20) DEFAULT NULL`** (cid=50) |
| A8 (sl_type) | 2026-04-19 17:27 | **new column: `sl_type VARCHAR(15) DEFAULT 'FIXED'`** (cid=51) |
| A6 (ghost closure) | 2026-04-19 15:02 | No schema change; emits event + note tag + `close_source='board_absent'` |

**The plan's schema model is stale by two columns.** See "Schema Delta Analysis" below.

---

## Headline

The A10 plan is **architecturally sound** — the merge algorithm, dedup policy, stale-signal override, and rollback strategy are defensible — but it was drafted against a 50-column snapshot of the new DB. Since then, **A8 and A11 each added a column** (now 52), and **A9 retroactively normalized BONK/SHIB/PEPE/FLOKI prices** in the new DB. The plan must be revised to (a) align the old-DB schema to 52 columns, (b) apply A9 normalization to the old-DB copy before dedup, and (c) backfill `sl_type` / `leverage_source` semantics for imported rows. Several smaller issues (atomicity of the swap, PENDING→CLOSED_MANUAL semantics, server FK match key) also need tightening before ANVIL implements.

## Overall Verdict

## **REVISE-REQUIRED**

The plan cannot be executed as-written because the target schema has moved under it. Three revisions block implementation (🔴 CRITICAL-A10-1/2/3); the remaining 🟡 MINOR items are polish.

---

## 🔴 CRITICAL (blocks implementation)

### CRITICAL-A10-1: Schema model is stale — 52 columns, not 50

Plan §1 "Database Comparison" table and §3 Pre-Merge Schema Alignment both assert new DB = 50 columns and the only old↔new delta is `remaining_pct`. Reality at HEAD `46154543`:

```
PRAGMA table_info(signals) → 52 columns:
  ...
  49 | remaining_pct     | REAL        | DEFAULT 100.0
  50 | leverage_source   | VARCHAR(20) | DEFAULT NULL
  51 | sl_type           | VARCHAR(15) | DEFAULT 'FIXED'
```

Live sanity:
```sql
SELECT COUNT(*) FROM signals;                           -- 494  (plan says 493)
SELECT sl_type, COUNT(*) FROM signals GROUP BY sl_type; -- FIXED|466, NONE|28
SELECT leverage_source, COUNT(*)
  FROM signals GROUP BY leverage_source;                -- NULL|396, EXPLICIT|98
```

The plan's `ALTER TABLE signals ADD COLUMN remaining_pct REAL DEFAULT 100.0;` (§3 on old-DB copy) is **necessary but not sufficient**. The merge script must add **three** columns to the old-DB copy (or omit those columns from the INSERT column list and let the new DB's DEFAULTs take over). Recommended SQL delta for the schema-alignment step on the old-DB copy:

```sql
ALTER TABLE signals ADD COLUMN remaining_pct   REAL        DEFAULT 100.0;
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
ALTER TABLE signals ADD COLUMN sl_type         VARCHAR(15) DEFAULT 'FIXED';

-- A8-consistent backfill for imported rows
UPDATE signals SET sl_type='CONDITIONAL'
  WHERE notes LIKE '%SL:CONDITIONAL%';
UPDATE signals SET sl_type='NONE'
  WHERE stop_loss IS NULL AND sl_type='FIXED';
-- MANUAL backfill only if the plan adds a heuristic; safe to leave default for historical rows
```

Without this, either:
- The merge INSERT fails (if ANVIL enumerates all 52 target columns and reads only 49 from old DB), or
- Imported old rows get NULL/default values that are inconsistent with A8 classification and A11 provenance semantics.

**Blocker because:** the plan currently directs ANVIL to add only one column; the actual schema divergence is three columns plus the A8 backfill rules — these aren't mentioned anywhere in A10.

### CRITICAL-A10-2: A9 denomination normalization not applied to old-DB values

A9 (merged 16:22 today) normalizes stored `entry_price`, `stop_loss`, `take_profit_*` values at micro-gate INSERT time for 1000* denominated tickers (e.g. `1000BONK`, `1000PEPE`, `1000SHIB`, `1000FLOKI`) by dividing by 1000 and storing base-ticker prices. The new DB already reflects normalization (verified: DB contains only `PEPE` / `FLOKI` rows — no `1000PEPE` / `1000BONK` — with base-unit prices such as `PEPE|3.657e-06`).

The old DB (1,165 signals, Feb 8 → Apr 9) was populated **before** A9 shipped. Its 1000* rows will be stored with either:
- Pre-A9 raw prices (`1000PEPE entry = 0.008` ⇔ `PEPE entry = 8e-06`), **or**
- Whatever informal handling existed (kraken-sync has had a partial 1000x guard since `52aea619` but micro-gate hadn't).

Consequences if plan is executed as-written:
1. **Dedup breakage:** Plan §4a STEP 4 dedups by `discord_message_id` only, so dedup itself survives. But …
2. **Post-merge query inconsistency:** `SELECT AVG(entry_price) FROM signals WHERE ticker='PEPE'` will mix normalized (post-Mar-18, new DB) and un-normalized (pre-Mar-18, old DB imported) values, producing garbage analytics.
3. **Ticker label inconsistency:** If old DB has tickers labeled `1000PEPE` while new DB has `PEPE`, analytics will report them as two instruments.

The plan has **no treatment of this issue** — "remaining_pct" is the only delta acknowledged. Before the dedup step, the merge script must either (a) apply A9's normalizer function to old-DB rows with `ticker LIKE '1000%'` (preferred), or (b) explicitly exclude/quarantine them and flag for Mike.

**Blocker because:** without A9-consistent handling, the merged DB produces wrong aggregate statistics for memecoin tickers — which is the *primary analytics use case* cited in §0 executive summary.

### CRITICAL-A10-3: §4d Step 8 uses `cp`, not an atomic rename

§4d execution sequence:
```
7. systemctl --user stop oink-sync
8. cp /home/m/data/oinkfarm-merge-test.db /home/m/data/oinkfarm.db
9. systemctl --user start oink-sync
```

Problems:
- `cp` is **not atomic**. If step 8 is interrupted (power loss, disk-full, signal), `/home/m/data/oinkfarm.db` is left in a torn state with no rollback window. The plan's §7 rollback assumes the backup still exists and oinkfarm.db is readable for the cp-back; it doesn't cover the window where step 8 fails mid-write.
- `cp` does not handle SQLite's **WAL side-files** (`-wal`, `-shm`). If oink-sync was stopped cleanly, the WAL should be checkpointed, but the plan does not explicitly checkpoint before step 8. If residual `-wal`/`-shm` files remain pointing at the old DB's page cache, post-cp startup may see mixed state.
- The canonical path is `/home/m/data/oinkfarm.db`. The workspace symlink at `/home/oinkv/.openclaw/workspace/data/oinkfarm.db` must be verified to still resolve post-swap (cp preserves the target of the resolved path if the destination exists, so the symlink should survive; still worth an explicit verification step).

Required fix:
```bash
# Ensure WAL is checkpointed and clean on both source and target
sqlite3 /home/m/data/oinkfarm.db "PRAGMA wal_checkpoint(TRUNCATE);"
# Write to a sibling temp file, fsync, then atomic rename
cp /home/m/data/oinkfarm-merge-test.db /home/m/data/oinkfarm.db.new
sync
mv /home/m/data/oinkfarm.db.new /home/m/data/oinkfarm.db   # atomic on same fs
# Verify symlink resolution
sqlite3 /home/oinkv/.openclaw/workspace/data/oinkfarm.db "SELECT COUNT(*) FROM signals;"
```

**Blocker because:** for a 🔴 CRITICAL, irreversible, Mike-approval-gated migration, the swap step must be unambiguously atomic. This is a trivial fix but the current wording invites a footgun.

---

## 🟡 MINOR (nice-to-fix, non-blocking)

### MINOR-A10-1: PENDING → CLOSED_MANUAL is semantically wrong

§3 Stale Signal Override:
```sql
UPDATE signals SET status='CLOSED_MANUAL', ... , auto_closed=1, close_source='db_merge_a10'
WHERE status IN ('ACTIVE', 'PENDING');
```

An `ACTIVE` signal that went stale did enter the market and could plausibly be called "closed manually." A `PENDING` signal never filled — it's a limit order that expired unfilled. The correct terminal status for those 23 PENDING rows is **`CANCELLED`** (already a live value in production — 57 CANCELLED rows exist). Mixing them into CLOSED_MANUAL pollutes win/loss analytics because CLOSED_MANUAL participates in PnL rollups whereas CANCELLED does not.

Recommend splitting:
```sql
UPDATE signals SET status='CLOSED_MANUAL',
       auto_closed=1, close_source='db_merge_a10_stale_active',
       closed_at='2026-04-19T00:00:00Z'
  WHERE status='ACTIVE';
UPDATE signals SET status='CANCELLED',
       auto_closed=1, close_source='db_merge_a10_stale_pending',
       closed_at='2026-04-19T00:00:00Z'
  WHERE status='PENDING';
```

Impact if unfixed: 23 never-filled limit orders appear as closed manual trades in trader stats. Not catastrophic but semantically incorrect and GUARDIAN-visible.

### MINOR-A10-2: Server FK match key should be `discord_id`, not `server_id`

§4a STEP 3: *"For each old server: if server_id matches → keep; if no match → INSERT into new DB servers table."*

The servers table has `id INTEGER PRIMARY KEY` (auto-increment) and `discord_id VARCHAR(20) NOT NULL UNIQUE`. The matching key across two independently-grown DBs must be the **natural key (`discord_id`)**, not the synthetic auto-increment `server_id`. Otherwise, if old DB has server_id=3 for "TraderX Discord" and new DB has server_id=3 for "TraderY Discord", the plan's literal match-on-id logic would incorrectly identify them as the same server.

The plan's STEP 2 correctly uses `name+server` for traders (natural key). STEP 3 should use `discord_id` for symmetry.

Traders table has `UNIQUE(name, server_id)` — correct per plan. Servers table has `UNIQUE(discord_id)` — needs matching on that.

### MINOR-A10-3: Signal-count drift (493 → 494) since plan draft

Plan cites 493 current signals. Live count at audit time: **494**. The delta is one signal posted during today's Wave-3 sprint window. The §6 acceptance tolerance is ±10 so this is within slack, but the hard-coded "493" in §1, §4e, §6, §7, §9 and the expected-merged total (`493 + ~651 ≈ 1,144`) will all drift further before Mike approves. Recommend parameterizing the pre-merge count as a script output rather than a hard-coded literal.

### MINOR-A10-4: Missing tests for A8 / A11 / A9 backfill behavior

§5 test matrix (10 tests) covers remaining_pct, trader remap, dedup, stale-signal closure, FK validity. It does **not** cover:
- `sl_type` default/backfill for imported rows (per A8 rules: FIXED|CONDITIONAL|NONE)
- `leverage_source` default for imported rows (NULL is the natural value; A11's backfill heuristic does not apply to historical unknown provenance)
- A9 denomination normalization applied during import (essential after CRITICAL-A10-2 fix)
- Ticker rename/remap for 1000* → base-ticker if that's the chosen A9 handling

Recommend adding: `test_imported_sl_type_backfill`, `test_imported_leverage_source_null`, `test_a9_normalization_1000pepe`, `test_ticker_aliased_to_base`.

### MINOR-A10-5: Dependencies list omits A6, A8, A9, A11

§0 header: *"Dependencies: A1 (signal_events — shipped), A2 (remaining_pct — shipped), A4 (PARTIALLY_CLOSED — shipped)"*

Reality: A6, A8, A9, A11 are all merged to main today. The plan's "Dependencies" line should be updated so ANVIL understands the full set of prior Wave-3 changes that must be replayed against imported data. This is the most visible surface symptom of the staleness that produces CRITICAL-A10-1 / -2.

### MINOR-A10-6: No explicit handling of `signal_events` for imported rows

§4c "What NOT to Merge" correctly states old DB has no signal_events. But the new DB currently has **355 events** for the 494 live signals. After merge, the ~651 imported old rows will have *zero* events. Any query that assumes "every closed signal has at least a CLOSE event" will break for historical rows.

This is arguably acceptable (historical gaps are inherent to the merge), but the plan should state the invariant explicitly and either (a) tell GUARDIAN to skip historical rows in event-completeness checks, or (b) synthesize a single `IMPORTED` event per imported row for bookkeeping.

### MINOR-A10-7: WAL checkpoint step missing from backup protocol

§4e "Backup Verification" does `sqlite3 ... COUNT(*)` and `md5sum`. It does not `PRAGMA wal_checkpoint(TRUNCATE)` on the source before copying. If the backup is taken while the database has a non-empty WAL file, the md5sum is stable but any SQLite reader that needs the WAL still has a dependency on side files. Low probability of trouble given oink-sync is stopped, but worth making explicit.

### MINOR-A10-8: `close_source='db_merge_a10'` length and uniqueness

Field is `VARCHAR(50)`. `db_merge_a10` is 12 chars — fine. But suggest using `db_merge_a10_stale_active` / `db_merge_a10_stale_pending` / `db_merge_a10_import` to make post-merge audit queries tractable (ties into MINOR-A10-1).

---

## 🟢 CONFIRMED (verified accurate)

### Row-count arithmetic is correct

Plan §1 claims: 1,165 old + 493 new, 514 overlap, 712 old-in-overlap-window, ~66 new-in-overlap-window, 1,165 − 712 = 453 unique pre-overlap from old, net new ≈ 453 + (712 − 514) = 651. Final merged ≈ 493 + 651 = **1,144** (≈ §6 acceptance). Cross-check:

- 1,165 + 493 − 514 = 1,144 ✓ (matches the exclusion-principle shortcut)
- The 651 figure = 453 + 198, where 198 = 712 − 514 = old signals inside overlap window that are *not* duplicated in new DB. Arithmetic checks.

(Note: the subagent task brief mentioned "1,644 merged" as the plan's claim — that appears to be a typo in the brief; the plan itself says 1,144 and the math resolves to 1,144.)

### Dedup policy is well-specified and defensible

§4a STEP 4 + §10 Gate 1 both state: **new DB wins on `discord_message_id` collision**. This is correct because (a) the new DB has the post-A1/A2/A4/A6/A8/A9/A11 schema already applied; (b) the new DB has `signal_events` history; (c) the new DB's lifecycle state is authoritative for the overlap window (Mar 18 – Apr 9). Old-DB rows in the overlap window only contribute uniqueness where they have a dmid missing from new DB, which is the intended capture.

### Rollback plan is complete and clean

§7: stop oink-sync → cp backup → start → verify 493. Straightforward and reproducible. Only caveat is CRITICAL-A10-3 (use atomic mv, not cp) — once that fix is applied, rollback is strong.

### "What NOT to Merge" decisions (§4c) are reasonable

Skipping `price_history` (high volume, low analytical value given the 22-day gap is fillable from current sources) and `audit_log` (schema drift, operator-facing only) are defensible calls. Mike's Q-A10-1 and Q-A10-2 correctly flag these for explicit sign-off.

### Mike-approval gating structure is correct

§10 defines two gates (plan approval → execute on test-copy → validation report → production swap). This is the right shape for an irreversible data migration. The two-gate pattern matches how A4 and the #22 event-store dual-write landed.

### No cross-repo import hazards

A10 creates standalone `scripts/merge_databases.py`. It does not touch micro-gate-v3.py, lifecycle.py, or engine.py, so the cross-repo import snags that bit Wave-1 A1 do not apply. ✓

### Foreign-key structure is understood correctly

Plan correctly identifies that `trader_id` and `server_id` are FKs requiring remap. Live schema confirms:
```
traders.id INTEGER PRIMARY KEY (autoinc)
traders.UNIQUE(name, server_id)
servers.id INTEGER PRIMARY KEY (autoinc)
servers.discord_id VARCHAR(20) NOT NULL UNIQUE
signals.server_id NOT NULL REFERENCES servers(id)
signals.trader_id NOT NULL REFERENCES traders(id)
```
Plus a `trg_signals_server_id_check` trigger that ABORTs INSERTs with unknown server_id. The plan's §4a STEP 2/3 + "Validate all FKs" in §5 `test_all_fks_valid` correctly anticipates this. (See MINOR-A10-2 for the server-match-key nit.)

---

## Schema Delta Analysis (A10's Most Likely Issue)

This is the finding that most needs ANVIL/Mike attention.

### What the plan assumed (drafted early Wave 3)

| DB | Columns | Delta |
|---|---|---|
| Old | 49 | baseline |
| New | 50 | +`remaining_pct` |

### What is actually true at HEAD `46154543` (post-A8 merge)

| Column (by cid) | Old DB | New DB | Plan aware? |
|---|---|---|---|
| 0–48 (base set) | ✅ | ✅ | ✓ |
| 49 `remaining_pct` REAL DEFAULT 100.0 | ❌ | ✅ (A2) | ✓ (called out) |
| 50 `leverage_source` VARCHAR(20) DEFAULT NULL | ❌ | ✅ (A11, 16:51 today) | ❌ **MISSING from plan** |
| 51 `sl_type` VARCHAR(15) DEFAULT 'FIXED' | ❌ | ✅ (A8, 17:27 today) | ❌ **MISSING from plan** |

Live proof (PRAGMA excerpt):
```
48|opened_price|FLOAT|0||0
49|remaining_pct|REAL|0|100.0|0
50|leverage_source|VARCHAR(20)|0|NULL|0
51|sl_type|VARCHAR(15)|0|'FIXED'|0
```

### Non-column deltas that also affect A10

| Change | Plan aware? | Required action in merge |
|---|---|---|
| A1: `signal_events` table exists in new DB with extended schema | ✓ (§4c correctly excludes from merge) | None beyond current §4c |
| A6: `close_source='board_absent'` + GHOST_CLOSURE event for ghost closures | ❌ not mentioned | None required — old DB has no ghost closures (feature didn't exist); confirm imported rows don't have a stale close_source meaning |
| A9: denomination normalization of stored entry/SL/TP for 1000* tickers | ❌ not mentioned | **See CRITICAL-A10-2** — must normalize or quarantine old 1000* rows |
| A11: `leverage_source` backfill populated NULL/EXPLICIT for existing 494 rows | ❌ not mentioned | Imported old rows should default to NULL (no provenance) |
| A8: `sl_type` backfill populated FIXED/NONE for existing rows | ❌ not mentioned | Imported old rows need matching backfill: FIXED default, NONE if SL NULL, CONDITIONAL if notes match |

### Why this matters for Mike's decision

1. The plan as written would produce a **52-column new DB with ~651 imported rows that silently rely on column DEFAULTs** — which on its face is fine (DEFAULTs are set to safe values). But this means imported rows get `sl_type='FIXED'` uniformly even when the underlying signal had a conditional SL — that's a classification regression for ~1.5 months of historical data.
2. The 1000* ticker issue under A9 is the more serious one — without remediation, PEPE/BONK/SHIB/FLOKI analytics over the merged DB will be arithmetically wrong because the same ticker's prices will live on different scales depending on which source DB contributed the row.
3. Both issues are **fixable during the merge** — just add the backfill SQL and the A9 normalizer call to the script. ANVIL has the canonical A8 backfill queries in the A8 plan (§3) and the A9 normalizer in `micro-gate-v3.py` §3b / §8a-A9. Reuse them.

---

## Recommendations for ANVIL (pre-Mike-approval)

ANVIL cannot start until Mike approves, but these are the edits FORGE should make to the plan file before approval so Mike is signing off on the corrected version:

1. **§0 Dependencies** — replace with: `A1 ✅, A2 ✅, A4 ✅, A6 ✅, A8 ✅, A9 ✅, A11 ✅ — all shipped 2026-04-19. Base commit: oinkfarm 46154543, oink-sync e9be741, signal-gateway c6cb99e.`
2. **§1 Database Comparison table** — update "New DB" to 52 columns; add rows for `leverage_source` and `sl_type` in the "Schema Differences" subtable; note A9 normalization impact on 1000* tickers.
3. **§3 SQL Changes** — add the three-column ALTER on the old-DB copy + the A8 `sl_type` backfill UPDATEs (copy from A8 plan §3); add an explicit A9 normalization step for 1000* rows.
4. **§3 Stale Signal Override** — split into two UPDATEs: ACTIVE → CLOSED_MANUAL, PENDING → CANCELLED (MINOR-A10-1).
5. **§4a STEP 3** — clarify server FK match key is `discord_id` (MINOR-A10-2).
6. **§4a STEP 5 Validation** — add: "Every imported old row has `sl_type` populated consistently with A8 rules, and `leverage_source` is NULL. Every imported old row with `ticker LIKE '1000%'` OR `ticker IN (base-set)` has normalized prices per A9."
7. **§4d Execution Sequence** — rewrite step 8 to checkpoint WAL, cp to `.new`, `sync`, then atomic `mv` (CRITICAL-A10-3).
8. **§5 Test Specification** — add 4 tests for sl_type, leverage_source, A9 normalization, and ticker alias consistency (MINOR-A10-4).
9. **§6 Acceptance Criteria** — add: "All 52 columns present; `sl_type` distribution post-merge is explainable; `leverage_source` distribution post-merge shows ~651 new NULL rows; no rows with `ticker LIKE '1000%'` in merged DB."
10. **§9 Evidence** — refresh the row counts (494 in new DB as of audit time) and note that counts will drift; direct ANVIL to capture live counts at execution time.

Post-revision, FORGE may re-dispatch a re-audit, but the revisions above are mechanical and the plan's architecture doesn't require rethinking.

---

## Recommendations for Mike (decision context)

Before approving A10 for ANVIL dispatch, the following are the genuinely decision-worthy items — everything else is mechanical:

1. **A9 1000* ticker handling (CRITICAL-A10-2):** Do you want the merge script to apply A9 normalization to imported pre-A9 rows (preferred — produces coherent memecoin analytics), or to quarantine/flag those rows for manual review? The plan currently does neither. FORGE's recommendation: apply normalization automatically; it's the same function already in production at micro-gate-v3.py.

2. **Stale PENDING handling (MINOR-A10-1):** Is it acceptable that 23 never-filled limit orders would enter the merged DB as `CLOSED_MANUAL` (contributing to PnL statistics), or should they be `CANCELLED`? FORGE's strong recommendation: CANCELLED.

3. **price_history / audit_log (plan §§4c, Q-A10-1, Q-A10-2):** Plan's author defers these. FORGE agrees — but note that *if* price_history is ever backfilled separately, the old-DB rows will still need `opened_price` / `closed_at` hydration, which is a separate follow-up task.

4. **Atomicity of the swap (CRITICAL-A10-3):** This is a mechanical fix but worth confirming you accept the revised `mv`-based procedure. The current `cp`-based step has a small but real torn-write window.

5. **The core merge strategy is sound.** Dedup-on-dmid-with-new-wins is the right call; two-gate approval (algo approval, then post-dry-run validation) is the right structure; the rollback plan is clean; the validation test matrix (with the 4 additions above) is adequate.

6. **Timing:** Plan §10 Q-A10-3 asks whether to run during a quiet window. With the A8 and A11 merges landing today and ongoing audit coverage from VIGIL / GUARDIAN, a Sunday-night / pre-dawn execution is advisable — oink-sync downtime is short (≤5 min) but the post-merge canary needs daylight for review.

**Bottom line for Mike:** the plan is not yet safe to execute, but the fixes required are all mechanical (apply a schema delta that's already in production, apply a normalizer that's already in production, change one `cp` to a `mv`, split one UPDATE into two). No architectural rethink needed. FORGE can revise the plan in ≤30 minutes of edit work; ANVIL can then implement with confidence.

---

## Evidence Log

**Files & commits inspected:**
- `/home/oinkv/forge-workspace/plans/TASK-A10-plan.md` (288 lines — fully read)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A8.md` (format reference)
- `/home/oinkv/forge-workspace/plans/TASK-A6-plan.md` (A6 schema-impact cross-ref, first 40 lines)
- `/home/oinkv/.openclaw/workspace/` git log (HEAD `46154543`, A8 merge)
- `/home/oinkv/oink-sync/` git log (HEAD `e9be741`; `ab5d941` resolves to A4 branch tip)
- `/home/oinkv/signal-gateway/` git log (A6 `c6cb99e` inspection)

**Database queries (`/home/oinkv/.openclaw/workspace/data/oinkfarm.db` → `/home/m/data/oinkfarm.db`):**
```sql
SELECT COUNT(*) FROM signals;                              -- 494
SELECT MIN(posted_at), MAX(posted_at) FROM signals;        -- 2026-03-18 → 2026-04-19
PRAGMA table_info(signals);                                -- 52 columns (see above)
SELECT sl_type, COUNT(*) FROM signals GROUP BY sl_type;    -- FIXED|466, NONE|28
SELECT leverage_source, COUNT(*) FROM signals
  GROUP BY leverage_source;                                -- NULL|396, EXPLICIT|98
SELECT status, COUNT(*) FROM signals GROUP BY status;
-- ACTIVE|79 CANCELLED|57 CLOSED_BREAKEVEN|69 CLOSED_LOSS|176
-- CLOSED_MANUAL|7 CLOSED_WIN|93 PARTIALLY_CLOSED|2 PENDING|11
SELECT COUNT(*) FROM signals WHERE ticker LIKE '1000%';    -- 0
SELECT DISTINCT ticker FROM signals
  WHERE ticker IN ('PEPE','FLOKI','SHIB','BONK');          -- FLOKI, PEPE (normalized)
SELECT COUNT(*) FROM signal_events;                         -- 355
SELECT COUNT(*) FROM traders;                               -- 99
SELECT COUNT(*) FROM servers;                               -- 11
```

**Wave-3 merge timeline (2026-04-19, from git):**
```
01:11  A1 (extract)                 09e0f94b
01:48  A1 merged            #126    5b242c56
13:05  A7                            8a78d900
13:27  A7 merged            #130    61573158
13:47  A5                            f74109fa
14:02  A5 merged            #131    69d6840a
15:02  A6 (signal-gateway)           c6cb99e  (ghost closure)
15:28  A9                            890afce1
16:03  A9 GUARDIAN R1 fixes          b9086018
16:22  A9 merged            #132    e7cfdb8e
16:42  A11                           2945ada0
16:51  A11 merged           #133    45a6931d  (← adds leverage_source)
17:15  A8                            19f475db
17:27  A8 merged            #134    46154543  (← adds sl_type; HEAD at audit time)
```

**Oinkfarm signals schema (signals table, non-index/trigger lines, live):**
```
52 columns, SQLite 3.46.1, final three cols:
  remaining_pct   REAL        DEFAULT 100.0
  leverage_source VARCHAR(20) DEFAULT NULL
  sl_type         VARCHAR(15) DEFAULT 'FIXED'
Indexes: 10 (unchanged from A8 audit)
Triggers: 5 (entry_price insert/update, status UPPERCASE insert/update, server_id reference check)
```

**Arithmetic verification (plan §1):**
- 1,165 − 712 = 453 (old pre-overlap unique) ✓
- 712 − 514 = 198 (old-in-overlap but unique to old DB) ✓
- 453 + 198 = 651 (net new from old) ✓
- 1,165 + 493 − 514 = 1,144 (merged expected, matches §6) ✓

**SQLite version:** 3.46.1 2024-08-13 — supports DROP COLUMN / WAL / atomic renames on same filesystem. ✓

**Production DB path resolution:**
```
/home/oinkv/.openclaw/workspace/data/oinkfarm.db → /home/m/data/oinkfarm.db
```
Symlink intact; target readable; 494 rows; 52 columns.

---

*Hermes subagent audit — Plan-Stage, Wave 3, Hermes fallback — 2026-04-19T18:0XZ.*
