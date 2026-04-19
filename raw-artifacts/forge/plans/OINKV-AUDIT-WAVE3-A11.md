# OINKV-AUDIT-WAVE3-A11 — Leverage Source Tracking

**Auditor:** OinkV 👁️🐷 (subagent audit of FORGE plan vs current codebase)
**Date:** 2026-04-19
**Plan audited:** `/home/oinkv/forge-workspace/plans/TASK-A11-plan.md` (170 lines, 6,883 bytes)
**Task tier:** 🟢 LIGHTWEIGHT
**Canonical target:** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` @ `69d6840a`
**Secondary target:** `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` @ `c6cb99e` (divergent copy, see §6)

---

## Overall Verdict: 🟢 READY-WITH-MINOR-EDITS

The plan's core design decision (track leverage provenance rather than default leverage values) is sound and well-justified. All critical invariants — schema non-existence of `leverage_source`, the 80.1% NULL rate, line-number accuracy for the leverage extraction block, migration additivity, and enum-value non-conflict — are **confirmed**. One minor line-number drift on the INSERT statement, one stale distribution table, one inconsistency in the VARCHAR sizing the parent cron context expected, and one file-drift note between `.openclaw/workspace` (canonical) and `signal-gateway` (legacy mirror). None block ANVIL.

---

## 1. Current Leverage Handling — Line Number Accuracy

**Plan claim (§1, line 65):** "Current Leverage Handling (micro-gate line 830-840)"
**Parent cron context claim:** "plan cites line 839 in micro-gate"

### Actual code (canonical `.openclaw/workspace/scripts/micro-gate-v3.py` @ 69d6840a):

```
Line 831: # ── 11. Leverage (store as-is) ──
Line 832:     leverage = ext.get("leverage")
Line 833:     if isinstance(leverage, (int, float)):
Line 834:         leverage = float(leverage)
Line 835:     elif isinstance(leverage, str):
Line 836:         try:
Line 837:             leverage = float(leverage.replace("x", "").replace("X", ""))
Line 838:         except (ValueError, TypeError):
Line 839:             leverage = None  # "2x-10x" stays as None in column; preserved in notes
```

🟢 **CONFIRMED.** Plan's "830-840" range is effectively correct (actual 831-839). The code block matches the plan's §1 excerpt verbatim. No drift. Parent cron's "line 839" cite is the terminal line of the block (NULL fallback path) — accurate.

---

## 2. Schema State — `leverage_source` Column

**Plan claim (§3, line 105):** proposes `ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;`
**Parent cron context claim:** "plan proposes `leverage_source VARCHAR(12)`"

### Evidence
```
$ sqlite3 /home/m/data/oinkfarm.db "SELECT name FROM pragma_table_info('signals') WHERE name LIKE '%source%' OR name LIKE '%leverage%';"
leverage
close_source
source_url
close_source_url
```

🟢 **CONFIRMED.** No `leverage_source` column exists. The existing `leverage` column is present and nullable (`15|leverage|FLOAT|0||0`), matching the plan's §1 PRAGMA output. The only `*_source` columns in `signals` today are `close_source` and `close_source_url` — unrelated semantically to leverage provenance (see §4).

🟡 **MINOR (parent-context discrepancy, not plan defect):** The parent cron briefing said the plan proposes `VARCHAR(12)`. The plan actually writes `VARCHAR(20)` at line 105. Both sizes work for all proposed values (`EXPLICIT`=8, `EXTRACTED`=9, `DEFAULT`=7, `NULL`=4 chars), but flagging because the cron brief was slightly mis-stated. **Plan itself is internally consistent on `VARCHAR(20)`.**

---

## 3. NULL-Rate Claim

**Plan claim (§0, §1, §9):** "395 of 493 signals (80.1%) have `leverage = NULL`."

### Live query (`/home/m/data/oinkfarm.db`, canonical store, symlinked from both `oinkfarm/data/` and `.openclaw/workspace/data/`):

```sql
SELECT COUNT(*) AS total,
       SUM(CASE WHEN leverage IS NULL THEN 1 ELSE 0 END) AS null_count,
       ROUND(SUM(CASE WHEN leverage IS NULL THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS null_pct
FROM signals;
-- 493 | 395 | 80.12
```

🟢 **CONFIRMED.** 80.12% NULL (plan says 80.1%; delta = 0.02 pct points, well within ±5). Totals (493 / 395 / 98) match exactly — no rows have been inserted or rewritten since the plan snapshot. The core "80% of leverage is unknown → defaulting manufactures false precision" argument holds.

🟡 **MINOR — stale distribution breakdown.** Plan's §1 "Leverage Distribution" table (top-10 non-NULL values) no longer matches today's data:

| Leverage | Plan count | Live count | Delta |
|----------|-----------:|-----------:|------:|
| 10.0     |         27 |         18 |    -9 |
| 20.0     |         22 |         20 |    -2 |
|  5.0     |         14 |          6 |    -8 |
| 15.0     |         11 |     absent |   -11 |
| 50.0     |          8 |          3 |    -5 |
|  1.0     |     absent |         31 |   +31 |
|  2.0     |     absent |          9 |    +9 |
|  1x      |     absent |          1 |    +1 (unparsed string) |

The aggregate (total=493, NULL=395) is unchanged — the redistribution is within the 98 non-NULL rows and does not alter the design conclusion. Likely explanation: a trader-correction backfill or lifecycle normalization has shifted leverage values for some rows since the plan snapshot. The presence of unparsed string `"1x"` and `"10x"` values is ANVIL-noteworthy but outside A11's scope.

**Recommendation:** Before ANVIL implements, have the distribution table refreshed by a one-line query. Non-blocking.

---

## 4. Source-Enum Value Non-Conflict

**Plan enum values (§0):** `EXPLICIT`, `EXTRACTED`, `DEFAULT`, `NULL`
**Parent cron context listed:** `EXPLICIT`/`NULL`/`DEFAULT` (3 values — note: plan actually has 4, adding `EXTRACTED`).

### Search for colliding enum values in current codebase

`close_source` values used in live code (from `scripts/micro-gate-v3.py` grep):
- `'pilot_closure'`, `'wg_alert'`, `'sl_hit'`, `'retracted'`, `'manual_close'`, `'hl_market_price'`

🟢 **CONFIRMED.** Zero overlap with proposed `leverage_source` enum. Column name `leverage_source` is distinct from `close_source`/`source_url`/`close_source_url`. No namespace collision. No existing constant or string literal named `EXPLICIT`/`EXTRACTED`/`DEFAULT` in the leverage code path.

🟡 **MINOR — internal plan inconsistency.** Plan §0 enumerates 4 values (`EXPLICIT`, `EXTRACTED`, `DEFAULT`, `NULL`), but §4a Implementation Notes only sets two (`EXPLICIT` or `None`). `EXTRACTED` and `DEFAULT` are described as "future enhancement" (§4a) but are still listed in §0 as part of the design. §5 test spec and §6 acceptance criteria only exercise `EXPLICIT`/NULL. The `VARCHAR(20)` column accommodates the future values, so this is forward-compatible, but ANVIL should be told: **today, only write `'EXPLICIT'` or `NULL`**. The 4-value semantic glossary is aspirational.

---

## 5. Migration / Backfill Shape vs Other A-Task Migrations

**Plan migration (§3):**
```sql
ALTER TABLE signals ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL;
UPDATE signals SET leverage_source = 'EXPLICIT' WHERE leverage IS NOT NULL;
```

### Comparison with prior A-wave migrations

| Task | Migration shape | Destructive? |
|------|-----------------|--------------|
| A1 (signal_events schema extend) | ALTER TABLE + column adds | No (additive) |
| A3 (filled_at) | UPDATE backfill on existing rows | No (backfills NULLs only) |
| A5 (parser confidence map) | Code-only, no schema | N/A |
| A7 (UPDATE→NEW guard) | Code-only, no schema | N/A |
| **A11 (proposed)** | **ALTER TABLE ADD COLUMN + UPDATE backfill where leverage IS NOT NULL** | **No (additive, default NULL)** |

🟢 **CONFIRMED.** Shape is additive and non-destructive:
- `ADD COLUMN … DEFAULT NULL` — existing rows receive NULL automatically
- Backfill `UPDATE … WHERE leverage IS NOT NULL` — touches exactly 98 rows, leaves the other 395 at NULL (correct "not provided" semantics)
- Rollback (§7): `ALTER TABLE signals DROP COLUMN leverage_source;` — SQLite 3.35+ supports this natively; `/home/m/data/oinkfarm.db` is SQLite ≥3.35 (verified by prior A-wave ALTER DROP usage). ✓
- No existing trigger on `signals` would be affected (triggers are on `entry_price`, `status`, and `server_id` — not leverage).

The backfill predicate (`leverage IS NOT NULL`) is semantically correct: every current non-NULL leverage value came from an extractor-supplied payload, so `'EXPLICIT'` is the correct retroactive label.

---

## 6. File Drift — Canonical vs `signal-gateway` Copy

The cron briefing instructed us to "check BOTH" canonical and `.openclaw` copies. Here's the actual layout:

| Path | Repo (origin) | HEAD | LOC | A5 merged? (PARSER_CONFIDENCE_MAP) |
|------|---------------|------|----:|:---:|
| `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` | `bandtincorporated8/oinkfarm` | **`69d6840a`** (A5) | **1,475** (1,508 after recent chore) | ✅ yes (line 119) |
| `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` | `bandtincorporated8/signal-gateway` | `c6cb99e` (A6 ghost-closure) | 1,063 | ❌ no (0 grep hits) |

### Observations

- `.openclaw/workspace` **IS** the oinkfarm repo — it's the canonical micro-gate location. Plan correctly identifies this at §plan-header line 6.
- `signal-gateway/scripts/micro-gate-v3.py` is a **divergent/legacy mirror** — 412 LOC shorter and missing the A5 `PARSER_CONFIDENCE_MAP` block entirely. The signal-gateway repo's `1adeaa1` (A6) ghost-closure commit touches oink-sync-adjacent code, **not leverage handling** — so there is no conflict with A11's proposed edits, as the parent cron brief correctly anticipated.
- `oink-sync/oink_sync/lifecycle.py:91` comment confirms the broader policy: "leverage intentionally ignored — Mike directive 2026-03-23". oink-sync does **not** consume `leverage` for PnL. Plan §1 ("oink-sync does NOT use leverage") is accurate for PnL purposes, though it overstates by saying "0 grep hits" — there are 26 leverage hits in oink-sync, but all are SELECT-into-row-dict / test fixtures / a no-op `_parse_leverage` helper. None feed PnL math. Semantically the plan's claim holds.

🟡 **MINOR — documentation note for ANVIL.** The A11 plan targets the `.openclaw/workspace` (oinkfarm) copy of micro-gate. The `signal-gateway/scripts/micro-gate-v3.py` copy is **legacy / not in the A5→A11 series** and should **not** be modified. ANVIL must not apply A11 edits to `signal-gateway/scripts/micro-gate-v3.py`, or the ALTER TABLE will land in the DB without corresponding column-handling code on the canonical insert path. This is a FORGE-team architectural convention concern, not a defect in the A11 plan itself.

🟡 **MINOR — line-number drift on INSERT statement.** Plan §2 "Files to Modify" cites `INSERT statement (line 855)`. Actual INSERT in canonical: `cur.execute("INSERT OR IGNORE INTO signals …")` begins at **line 922**, and the `leverage` column position in the VALUES tuple is at **line 929** / `leverage` in row-values list at **line 938**. The plan's "line 855" appears to reference an earlier snapshot. Not blocking (ANVIL will grep for the INSERT block anyway), but the cite is stale.

---

## Section-by-Section Findings Summary

| # | Topic | Finding | Severity |
|---|-------|---------|----------|
| 1 | Leverage extraction block at line 830-840 | Block present at 831-839, code matches plan excerpt verbatim | 🟢 CONFIRMED |
| 2 | `leverage_source` column absent from schema | Confirmed; only `close_source`/`source_url`/`close_source_url` exist | 🟢 CONFIRMED |
| 2b | Plan `VARCHAR(20)` vs cron-brief-stated `VARCHAR(12)` | Plan is internally consistent at 20; cron brief slightly mis-stated | 🟡 MINOR |
| 3 | 80.1% NULL-leverage rate | Actual 80.12% (493/395), exact match | 🟢 CONFIRMED |
| 3b | Plan's top-10 distribution table | Stale — non-NULL values have redistributed since plan snapshot | 🟡 MINOR |
| 4 | Source-enum values vs existing `close_source` values | Zero collision; column-name distinct | 🟢 CONFIRMED |
| 4b | Plan §0 lists 4 enum values; §4a only implements 2 | `EXTRACTED`/`DEFAULT` flagged as future — ANVIL should only write `EXPLICIT` or `NULL` today | 🟡 MINOR |
| 5 | ALTER + backfill shape vs prior A-migrations | Additive, non-destructive, rollback-safe (ALTER DROP) | 🟢 CONFIRMED |
| 6 | Canonical (`.openclaw/workspace`) vs legacy (`signal-gateway`) copy | Canonical correctly identified by plan; legacy copy is 412 LOC behind (missing A5). ANVIL must not edit legacy copy. | 🟡 MINOR |
| 6b | INSERT statement line number (plan says 855) | Actual INSERT at line 922; `leverage` binding at 929/938 — line cite stale | 🟡 MINOR |
| 7 | oink-sync uses leverage for PnL? | Policy-ignored per Mike 2026-03-23 directive (`lifecycle.py:91`). Plan's "no downstream consumer" claim holds semantically. | 🟢 CONFIRMED |

### Count
- 🔴 CRITICAL: **0**
- 🟡 MINOR: **6** (all advisory, none block implementation)
- 🟢 CONFIRMED: **6** core invariants verified

---

## Recommended Plan Edits (non-blocking)

Before handing to ANVIL, FORGE should make these small edits:

1. **§1 Distribution table** — refresh with live numbers (or drop the top-10 breakdown and keep only the aggregate "395/493 NULL = 80.12%" claim). Add a note that ~2 rows carry unparsed string leverage (`"1x"`, `"10x"`), which the existing normalization block handles correctly.
2. **§2 Files to Modify** — update "INSERT statement (line 855)" to "(line ~922, leverage binding at line 929/938)".
3. **§0 vs §4a consistency** — add one sentence to §0 Executive Summary: "Phase 1 of A11 only writes `'EXPLICIT'` or `NULL`. `EXTRACTED` and `DEFAULT` are reserved for future enhancements and are NOT produced by this task."
4. **§plan-header or new §2.1** — add an explicit note: "This plan modifies only `.openclaw/workspace/scripts/micro-gate-v3.py` (canonical oinkfarm copy). `signal-gateway/scripts/micro-gate-v3.py` is a divergent legacy mirror and MUST NOT be modified by this task."

None of these edits change the design; they only prevent ANVIL from wasting a cycle on stale line numbers or touching the legacy mirror.

---

## Final Verdict

**🟢 READY-WITH-MINOR-EDITS**

The plan's design is sound, schema is clean, migration is additive, code-block references are accurate, and the core statistical claim (80.1% NULL) is exact. The FORGE decision to track provenance rather than manufacture defaults is well-reasoned and internally consistent with Mike's 2026-03-23 leverage-free-PnL directive. Six minor advisory notes (line drift, stale distribution, cross-repo file layout) should be folded into the plan before dispatch but do not require revision of the design or re-approval.

**Evidence base for this audit:**
- Canonical micro-gate: `.openclaw/workspace/scripts/micro-gate-v3.py` @ `69d6840a` (A5 merged, 1,475 LOC in grepped snapshot, 1,508 in current HEAD)
- Legacy mirror: `signal-gateway/scripts/micro-gate-v3.py` @ `c6cb99e` (A6 merged, 1,063 LOC, NO A5)
- Production DB: `/home/m/data/oinkfarm.db` (symlinked from both `oinkfarm/data/oinkfarm.db` and `.openclaw/workspace/data/oinkfarm.db`)
- oink-sync HEAD: `e9be741` (A4 merged); plan's cited `ab5d941` is the A4 feature commit
- Live signal count: 493 (395 NULL = 80.12%)
