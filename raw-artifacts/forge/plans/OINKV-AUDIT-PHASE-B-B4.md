# OinkV Engineering Audit — FORGE Plan B4 (Hermes fallback)

⚠️ **Provenance:** Hermes Agent (Hermes-subagent fallback; OinkV main lane LLM-timed-out @ 04:38 CEST today, FailoverError after 306s). Dispatched 2026-04-20 04:55 CEST per `oinkfarm-sprint-orchestrator` skill "Hermes-Subagent Fallback" pattern. Subagent hit `exit_reason=max_iterations=50` after evidence gathering; orchestrator recovered full audit from subagent summary per "Iteration-cap recovery for OinkV audits" protocol.

**Auditor:** Hermes Agent
**Date:** 2026-04-20 05:15 CEST
**Scope:** TASK-B4-plan.md — PostgreSQL Cutover (authoritative-store switch)
**Tier:** 🔴 CRITICAL — irreversible production transition (30-day SQLite rollback window)

---

## 0. Audit Header

| Item | Value |
|------|-------|
| Plan under review | `/home/oinkv/forge-workspace/plans/TASK-B4-plan.md` |
| Size | 8,361 bytes (215 lines) |
| mtime | 2026-04-19 18:06 CEST (drafted BEFORE B1 v2 / B2 / B3 merges) |
| Revision | v1 (no v2 yet) |
| Downstream consumers | ANVIL (execution), Mike (approval gate) |

### Canonical commits verified (live `git log -1`)

| Repo | Live HEAD | Plan §10 claim | Verdict |
|------|-----------|----------------|---------|
| `/home/oinkv/oinkfarm` (QuantisDevelopment, canonical) | `6af042f7` — *Merge B3: Parallel write verification layer* | — | ⚠️ plan has no HEAD cite for canonical |
| `/home/oinkv/.openclaw/workspace` (bandtincorporated8 mirror) | `0fbcbf1b` — *fix(B1): add sys.path for oink_db import* | — | ⚠️ plan has no HEAD cite |
| `/home/oinkv/oink-sync` | `73d074f` — *Merge B3: Re-vendor oink_db.py (DualWriteConnection + executemany fix)* | `e9be741` | 🔴 STALE — hash is 3-4 merges behind (pre-B1) |
| `/home/oinkv/signal-gateway` | `cc70e5b` — *Merge B3: Re-vendor oink_db.py + ghost closure fix* | `c6cb99e` | 🔴 STALE — hash is 4+ merges behind (pre-B1) |
| (micro-gate label) | (lives inside oinkfarm) | `46154543` | 🔴 STALE — that is the **A8 feature commit**, not a HEAD (pre-B1) |

Plan's §10 "Evidence" block cites three **feature commits from Wave 2/3** (A8, A4, A6) — all pre-Phase B. These were valid HEADs on **2026-04-19 18:06** when the plan was drafted but are now rendered meaningless by the full B1→B2→B3 merge cascade.

---

## 1. Summary

| Severity | Count |
|----------|------:|
| 🔴 SHOWSTOPPER | **3** |
| 🔴 CRITICAL | **2** |
| 🟡 MAJOR | **1** |
| 🟠 MINOR | **2** |
| 🟢 CONFIRMED-OK | 4 |

### Headline

> Plan is **directionally correct** (config-flip, rollback window, verification cadence) but has **three hard blockers** against the live runtime: (1) `systemctl --user restart micro-gate` targets a nonexistent unit, (2) `systemctl --user restart signal-gateway` targets a **DISABLED** unit file — signal-gateway runs as a manually-launched process, (3) `reconcile_stores.py --full` passes an unrecognized argparse flag. The plan also omits `OINK_PG_URL` from the env-flip recipe (without it, `OINK_DB_ENGINE=postgresql` raises `EnvironmentError` at module-import time) and has zero test evidence that PostgreSQL is actually provisioned on this host (`psql`/`psycopg` are **not installed**).

### Verdict

**🔴 REWRITE-REQUIRED** — see §12.

B4's v1 is in roughly the same shape B2-v1 and B3-v1 were: the prose & structure are right but the operational commands are stale against live systemd reality and depend on un-shipped B2 migration artifacts. Lineage precedent says a v2 will clear the bar after these fixes.

---

## 2. Critical & Showstopper Findings

### 🔴 SS1 — `systemctl --user restart micro-gate` targets a nonexistent unit

- Plan §1 table and §4a cutover procedure command: `systemctl --user restart micro-gate`
- **Live evidence:**
  - `systemctl --user list-unit-files | grep -i micro-gate` → **zero results**
  - `ls ~/.config/systemd/user/ | grep -i micro` → **zero results**
  - `find /home/oinkv -maxdepth 3 -iname '*micro-gate*'` shows `micro-gate-v3.py` as a **script** (embedded), not a service
  - Signal-gateway service env: `USE_INLINE_GATE=1` → micro-gate-v3.py is invoked **inline inside the signal-gateway process**, it has no independent systemd unit
- **Impact:** The cutover command will fail with `Failed to restart micro-gate.service: Unit micro-gate.service not found.` The rollback command has the same bug.
- **Fix:** remove `systemctl --user restart micro-gate` from §4a and §7. A signal-gateway restart already covers the inline micro-gate.

### 🔴 SS2 — `signal-gateway.service` is DISABLED

- Plan §1 row / §4a: `systemctl --user restart signal-gateway`
- **Live evidence:**
  - `ls ~/.config/systemd/user/` shows `signal-gateway.service.DISABLED` (renamed)
  - `systemctl --user list-units --type=service --all` shows `signal-gateway.service … not-found inactive dead`
  - The active signal-gateway is PID 193712: `/usr/bin/python3 -u -m scripts.signal_gateway.gateway` launched manually in `/home/oinkv/signal-gateway`
  - B3-MERGED.marker confirms: "signal-gateway.service: restarted 04:24:51 CEST" was done **manually** (kill+nohup), not via systemd — the .DISABLED rename has been in effect since before Wave 2
- **Impact:** `systemctl --user restart signal-gateway` returns `Unit signal-gateway.service not found.` — cutover will not actually restart the process carrying 90% of write traffic. Worst-case, operator believes cutover succeeded while signal-gateway continues writing to SQLite only.
- **Fix:** replace with the actual restart pattern (`pkill -f 'scripts.signal_gateway.gateway' && cd /home/oinkv/signal-gateway && nohup … &`), or rename `.DISABLED` back and re-enable before cutover. Either decision needs Mike.

### 🔴 SS3 — `reconcile_stores.py --full` flag does not exist

- Plan §4a: `python3 scripts/reconcile_stores.py --full`
- **Live evidence** (`/home/oinkv/oinkfarm/scripts/reconcile_stores.py` lines 547-561): argparse registers **only** `--output-dir`, `--day`, `--db`. No `--full` option.
- `argparse` default behavior is `error: unrecognized arguments: --full` → exit code 2 → operator aborts at T-60min thinking reconciliation failed.
- **Impact:** T-60min "final reconciliation" step of the cutover dies on the first command.
- **Fix:** drop `--full` (the reconciler is already full-by-default), or add `--full` as a no-op alias in a pre-B4 micro-PR.

### 🔴 C1 — `OINK_PG_URL` missing from env-flip recipe

- Plan §4a T-0 sets only: `export OINK_DB_ENGINE=postgresql; export OINK_DB_DUAL_WRITE=false`.
- **Live evidence** (`/home/oinkv/oinkfarm/scripts/oink_db.py` line 104-108):
  ```python
  if not _pg_url:
      raise EnvironmentError(
          "OINK_DB_ENGINE='postgresql' requires OINK_PG_URL environment variable. …")
  ```
- Module raises at **import time** when `OINK_DB_ENGINE=postgresql` but `OINK_PG_URL` is unset → every consumer crashes on next start.
- Also missing: `OINK_PG_URL` needs to be in each service's systemd `Environment=` directive (or a sourced EnvironmentFile), not just the operator's shell, since systemd restarts don't inherit the shell env.
- **Fix:** add explicit step adding `OINK_PG_URL=postgresql://oinkv@localhost/oinkfarm` to:
  - `~/.config/systemd/user/oink-sync.service` (already has `Environment=` block)
  - `~/.config/systemd/user/oinkfarm-dashboard.service`
  - `~/.config/systemd/user/oinkdb-api.service`
  - signal-gateway startup wrapper (now manual)
  - then `systemctl --user daemon-reload` before restarts.

### 🔴 C2 — PostgreSQL is not provisioned on this host, and B2 migration has not been run

- **Live evidence:**
  - `which psql` → not found
  - `dpkg -l | grep postgres` → only `libpq5` client library, **no server, no psql client**
  - `pip show psycopg` → not installed
  - `/home/oinkv/anvil-workspace/reconciliation/` directory → **does not exist**
  - B2-MERGED.marker: *"NOT shipped: Migration execution against production SQLite — gated on Q-B2-4 / Q-B2-5 / GUARDIAN's live pre-migration verification. Phase 1 ships the migration TOOLING. Migration RUN is a separate Mike-gated operation."*
  - B3-MERGED.marker: *"⚠️ ACTIVATION GATE — DO NOT ENABLE YET. OINK_DB_DUAL_WRITE remains FALSE in production."*
- **Plan §0** asserts "Both SQLite and PostgreSQL have identical data (verified by B3 reconciliation)" and "Dual-write has been running for 7-14 days with zero discrepancies." **As of 2026-04-20 04:55 CEST, zero of those prerequisites hold.**
- **Impact:** T-30min `pg_dump oinkfarm > …` fails (no pg_dump); T+5min `psql -U oinkv oinkfarm -c …` fails (no psql); post-cutover verification impossible.
- **Fix:** plan must add an explicit prerequisite block:
  1. Install postgresql-server + postgresql-client (apt)
  2. `pip install 'psycopg[binary]>=3.1'` into all three service Python envs
  3. Run B2 `migrate_sqlite_to_pg.py` against the live DB with GUARDIAN sign-off (Q-B2-4, Q-B2-5 resolved by Mike)
  4. Activate `OINK_DB_DUAL_WRITE=true` per B3 activation sequence
  5. Accumulate **7+ reconcile_stores.py CLEAN reports** (B3 first-72h uses 6-hour cadence per reconciler S1 comment → 7 reports ≈ 42 hours, not 7 days as plan §0 implies)
  6. Only then schedule B4.
  Plan §10 Evidence mentions "7+ days clean reconciliation required" but that is under-emphasised — it deserves to be §0 row 1, not a §10 footnote.

---

## 3. Major Findings

### 🟡 M1 — Plan §2 "No Code Changes Required" is true but masks a deployment action

Plan says B4 is purely config. Mechanically correct, but:

- The `.openclaw/workspace` copy of `oink_db.py` is **272 lines / 9,940 bytes** (B1 + 2 fixes only)
- The canonical `/home/oinkv/oinkfarm/scripts/oink_db.py` is **618 lines / 22,771 bytes** (B1+B2+B3)
- These are **two different repos** (bandtincorporated8 fork vs QuantisDevelopment canonical) — `oinkdb-api.service` WorkingDirectory is `.openclaw/workspace`, which means **oinkdb-api is currently running against the B1-only oink_db.py and doesn't have PG support wired in**.

Unless that fork is synced before B4 (or oinkdb-api is re-pointed at `/home/oinkv/oinkfarm/scripts/oink_db.py`), B4 cutover leaves oinkdb-api reading a **nonexistent** SQLite path after the primary store moves.

**Fix:** plan must explicitly address fork-sync state of `.openclaw/workspace`, OR change oinkdb-api.service's WorkingDirectory / PYTHONPATH.

---

## 4. Minor Findings

### 🟠 m1 — §0 says "7+ days" but reconciler cadence is 6h

Plan §0: *"7+ consecutive clean reconciliation reports"* — ambiguous. Reconciler code S1 comment: *"First 72h on 6-hour cadence, then relax to daily."* 7 **reports** on 6h cadence = 42h not 7 days. Plan should disambiguate: "7 consecutive CLEAN reports on the 6h cadence (≈42h wall-clock) then 4 daily CLEAN reports" — or state "7 daily CLEAN reports after 72h bootstrap."

### 🟠 m2 — SQLite rollback backup filename uses local date, cutover likely crosses UTC midnight

Plan §4a: `cp /home/m/data/oinkfarm.db /home/m/data/oinkfarm-pre-cutover-$(date +%Y%m%d).db` with Sunday 02:00 UTC timing. Plan's timezone isn't specified; operator in CEST/CET will produce a different `%Y%m%d` than `date -u +%Y%m%d`. Cosmetic, non-blocking. Suggest `$(date -u +%Y%m%dT%H%M%SZ)` for unambiguity.

---

## 5. Confirmed-OK

| Item | Verdict |
|------|---------|
| Plan cites B1 API (`connect()` from oink_db.py) — no ORM regression | ✅ |
| Env var names `OINK_DB_ENGINE`, `OINK_DB_DUAL_WRITE` match live oink_db.py (lines 75-76) | ✅ |
| Rollback steering (`OINK_DB_ENGINE=sqlite` flip + restart) is mechanically correct | ✅ |
| Dependency chain B1→B2→B3→B4 correctly declared in header | ✅ |

---

## 6. Write-Site / API Verification

| Plan assertion | Live check | Verdict |
|----------------|-----------|---------|
| "`scripts/oink_db.py connect()` already supports engine=postgresql from B2" | `/home/oinkv/oinkfarm/scripts/oink_db.py:166-175` — engine-gated PG branch + SQLite default | ✅ EXACT (canonical) |
| "PostgreSQL connections require OINK_PG_URL" | lines 104-108 raise EnvironmentError when unset | ✅ EXACT |
| "Dual-write can be disabled by OINK_DB_DUAL_WRITE=false" | line 76: `_DB_DUAL_WRITE = os.environ.get("OINK_DB_DUAL_WRITE", "false").lower() == "true"` | ✅ EXACT |
| "`reconcile_stores.py --full` verifies stores in sync" | `--full` flag **does not exist** in argparse (§547-561) | 🔴 SS3 |
| "`systemctl --user restart micro-gate`" | unit does not exist | 🔴 SS1 |
| "`systemctl --user restart signal-gateway`" | unit file is `.DISABLED` | 🔴 SS2 |
| "`systemctl --user restart oink-sync`" | unit exists, running (PID 143574) | ✅ OK |
| "`systemctl --user restart oinkfarm-dashboard`" | unit file exists, currently inactive (runs as manual nohup PID 193812 after B3 hot-restart) | 🟡 partial — systemd restart will work but won't touch the live nohup'd process |

---

## 7. Env-Var Matrix vs Live oink_db.py

| Plan-referenced var | Live reader | Where | Verdict |
|---------------------|-------------|-------|---------|
| `OINK_DB_ENGINE` | `os.environ.get("OINK_DB_ENGINE", "sqlite")` | line 75 | ✅ |
| `OINK_DB_DUAL_WRITE` | line 76 | ✅ |
| `OINK_PG_URL` | lines 91 / 112 | ⚠️ **not set in plan's env-flip recipe** — C1 |
| (implicit) `OINK_DB` / `OINKFARM_DB` / `OINK_DB_PATH` | live code reads **`OINK_DB`** (line 73 of all 3 copies) | ✅ live reads OINK_DB consistently. (Task context note about "signal-gateway uses OINKFARM_DB not OINK_DB_PATH" appears stale — all three current oink_db.py copies uniformly read `OINK_DB`. However, `oinkdb-api.service` sets `OINKDB_PATH=/home/m/data/oinkfarm.db` in its systemd unit — separate service, separate env var, irrelevant to B4.) |

**Action for plan v2:** add a dedicated §4a.0 "Env-var matrix" block spelling out all four variables across all service units.

---

## 8. Systemd Reality vs Plan

| Plan's service list | Live state | Action for v2 |
|---------------------|-----------|----------------|
| `micro-gate` systemd unit | ❌ does not exist | **Delete from plan** — runs inline inside signal-gateway |
| `oink-sync` systemd unit | ✅ active (PID 143574) | Keep. Ensure `OINK_PG_URL` added to `Environment=` |
| `signal-gateway` systemd unit | ❌ file is `.DISABLED`; process runs as manual nohup | **Decide with Mike**: either re-enable unit pre-B4 or replace command with `pkill && nohup` |
| `oinkfarm-dashboard` systemd unit | ⚠️ unit exists but current instance is a post-B3 manual nohup | Restart path must kill PID 193812 first, then `systemctl --user start` OR re-nohup — plan must pick one |
| `oinkdb-api` (not in plan) | ✅ running, points at `.openclaw/workspace` fork (B1-only oink_db.py) | **Add to plan** — oinkdb-api IS a production consumer and must be restarted + possibly re-based on canonical fork |
| `portfolio-webhook.py` (not in plan) | ✅ running, uses `oink_db` directly | **Add to plan** if it writes (check `/home/oinkv/oinkfarm/scripts/portfolio-webhook.py`) |

---

## 9. Reconciliation Prerequisite Status

| Prereq (from plan §0) | Live status 2026-04-20 05:15 CEST | Block? |
|----------------------|------------------------------------|--------|
| B1 merged | ✅ all 3 repos | no |
| B2 merged | ✅ all 3 repos (schema + migration tooling) | no |
| B2 migration **executed** against production SQLite | ❌ **not run** (per B2-MERGED.marker) | **YES** |
| B3 merged | ✅ all 3 repos (04:25 CEST today) | no |
| Dual-write **activated** | ❌ **OFF** (per B3-MERGED.marker) | **YES** |
| 7+ clean reconcile reports | ❌ **0** exist (reconciliation dir missing) | **YES** |
| GUARDIAN pre-migration canary PASS | ❌ not run | **YES** |
| psql/psycopg installed | ❌ both missing | **YES** |

**Plan correctly lists the 7+ reports as a prerequisite (§0, §10). What it does NOT do** is mark them as unmet blockers. Plan §1 "Current State Analysis (Pre-B4)" asserts all prereqs are complete as if they were: *"At this point, after B1+B2+B3: All modules use oink_db.connect() ✓, Both SQLite and PostgreSQL have identical data ✓, Dual-write has been running for 7-14 days ✓"*. This framing is counterfactual-future, not current-state — operator reading §1 could infer the prereqs are done. §1 should have a clear "**🚨 NONE OF THE BELOW IS TRUE YET — see §0 gate**" banner.

---

## 10. Rollback Viability

Plan §4b and §7 correctly prescribe `export OINK_DB_ENGINE=sqlite; systemctl --user restart …`. Mechanics of the flip-and-restart are **sound**. Problems:
- Inherits the same SS1/SS2 systemd-unit-not-found bugs → rollback itself will partial-fail
- Does not mention `unset OINK_PG_URL` (harmless but cleaner)
- Does not describe what to do if post-rollback SQLite is **behind** PG (24h of PG-only writes need to be manually replayed — plan §4b admits this but doesn't give a tool)
- 30-day retention window is appropriate; **pg_dump cadence during retention is not specified** (should be daily pg_dump to cold storage)
- Plan §4b's "Note: Any data written ONLY to PostgreSQL after cutover would be lost on rollback" is exactly the right honest disclosure — ✅

**Verdict on rollback §:** structurally adequate, operationally broken until SS1/SS2 fixed.

---

## 11. Risk Assessment vs Live Reality

Plan §8 risks are correctly identified but **severely underweighted** given current prereq gap:

| Plan risk | Plan probability | My re-rating | Rationale |
|-----------|------------------|--------------|-----------|
| Service fails to connect to PostgreSQL | Low | **HIGH** | psycopg not installed on host; no verified PG server |
| PostgreSQL performance worse than SQLite | Low | Low-Med | untested — no B3 benchmark exists |
| Missing data after cutover | Very Low | **HIGH** until dual-write runs 7+ CLEAN days | Zero reconcile reports exist today |
| oink-sync SQLite code paths break | Low | Low | B2 kept SQLite path byte-identical — well-verified |
| **NEW — systemd unit missing** | not listed | **HIGH** | SS1/SS2 directly block the cutover + rollback commands |
| **NEW — `.openclaw/workspace` fork is B1-only** | not listed | Medium | oinkdb-api reads from stale oink_db.py (M1) |

---

## 12. Verdict

### 🔴 REWRITE-REQUIRED (v2 needed)

**Rationale:**

- **3 SHOWSTOPPERS** (SS1 micro-gate unit nonexistent, SS2 signal-gateway unit DISABLED, SS3 `--full` flag doesn't exist) will cause cutover or rollback to fail at the command level on first execution.
- **2 CRITICALS** (C1 missing `OINK_PG_URL` in env-flip, C2 PostgreSQL + psycopg not installed and B2 migration not run) mean plan presupposes a host state that does not exist.
- Plan §1 "Current State Analysis" asserts prereqs as if done; they are not. Language must flip to future-conditional.
- Plan §10 cites pre-Phase-B feature commits (`46154543`, `e9be741`, `c6cb99e`) as "Evidence" — these hashes have no B1/B2/B3 code in them.

**Lineage context:** B2 v1 and B3 v1 were both REJECTED by Hermes-fallback audit and re-shipped as v2 in the same week. B4 is currently in the same shape: directionally correct, operationally wrong. A focused v2 revision should resolve all findings without redesign:

1. Fix service-restart commands (SS1, SS2)
2. Fix `reconcile_stores.py` invocation (SS3)
3. Add `OINK_PG_URL` to env-flip recipe + systemd EnvironmentFiles (C1)
4. Add explicit "🚨 PREREQUISITES NOT MET" banner enumerating B2 migration run, dual-write activation, 7+ CLEAN reports, psycopg install, PG provisioning (C2)
5. Address `.openclaw/workspace` fork's B1-only oink_db.py OR add oinkdb-api re-basing (M1)
6. Reconcile the "7 days" vs "7 reports @ 6h" vocabulary (m1)
7. Use UTC timestamp in backup filename (m2)

**Recommendation for Mike:** Do NOT approve v1. Return to FORGE with this audit attached. B4 should not be scheduled until after:
(a) Mike resolves Q-B2-4/Q-B2-5 → migration runs with GUARDIAN pre-deploy + canary PASS
(b) `OINK_DB_DUAL_WRITE=true` activation (per B3 gate)
(c) 7+ CLEAN reconciliation reports accumulate
(d) Plan v2 addresses the 8 findings above

Once prereqs are met and v2 lands, B4's core design (config flip with 30-day rollback window) is **fundamentally sound** and should audit SHIP-READY in v2.

---

*Audit complete. Hermes Agent fallback, 2026-04-20 05:15 CEST.*
*Provenance: OinkV main lane FailoverError @ 04:38 CEST today (306s timeout). Dispatched per oinkfarm-sprint-orchestrator skill "Hermes-Subagent Fallback" pattern. Subagent exited on max_iterations=50 after evidence gathering; orchestrator recovered full audit content from subagent summary per "Iteration-cap recovery for OinkV audits" protocol.*
