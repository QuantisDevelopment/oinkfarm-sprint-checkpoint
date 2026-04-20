# OinkV Audit — Phase B Wave 1 B4/B5 (Hermes fallback batch)

**Auditor:** Hermes subagents (dual parallel `delegate_task` batch; OinkV main lane LLM-timing-out)
**Date:** 2026-04-20 05:09 CEST (03:09 UTC)
**Plans audited:**
- `TASK-B4-plan.md` (215 lines, 8,361 bytes, mtime 2026-04-19 18:06 CEST) — 🔴 CRITICAL PostgreSQL cutover
- `TASK-B5-plan.md` (247 lines, 11,258 bytes, mtime 2026-04-19 18:08 CEST) — 🟡 STANDARD emitter extraction

**Dispatch driver:** B2 v2 + B3 v2 both shipped (2026-04-20 03:22 / 04:25 CEST). Per `PHASE-B-WAVE1-REVISION-v2.md` §"Next Steps": "B4 audit dispatched after B2+B3 v2 pass; B5 audit dispatched in parallel." Orchestrator dispatched both in a single Hermes-fallback batch while B3 canary runs passively.

---

## ⚠️ Provenance note for Mike

OinkV (agent `main`) was LLM-unavailable in the dispatch window:

```
Apr 20 04:38:19 barn node[…]: [diagnostic] lane task error: lane=main durationMs=306426 error="FailoverError: LLM request timed out."
Apr 20 04:38:19 barn node[…]: [diagnostic] lane task error: lane=session:agent:guardian:main durationMs=306427 error="FailoverError: LLM request timed out."
```

Rather than wait for OinkV retries, Hermes dispatched two parallel `delegate_task` subagents (one per plan) with the full audit rubric + read-only safety rails. Per `oinkfarm-sprint-orchestrator` skill "Hermes-Subagent Fallback for OinkV Staleness Audits". B4's subagent exited on `max_iterations=50` after full evidence gathering; the orchestrator recovered the complete audit from the subagent summary per the documented iteration-cap recovery protocol. B5's subagent completed within budget (41 calls, well-scoped).

---

## Canonical commits verified (2026-04-20 04:55 CEST)

| Repo | Path | HEAD | Note |
|------|------|------|------|
| oinkfarm | `/home/oinkv/.openclaw/workspace` | `0fbcbf1b` | B1 merged + 2 post-merge fixes (bandtincorporated8 mirror) |
| oinkfarm (canonical) | `/home/oinkv/oinkfarm` | `6af042f7` | Merge B3 (QuantisDevelopment canonical) |
| oink-sync | `/home/oinkv/oink-sync` | `73d074f` | Merge B3 |
| signal-gateway | `/home/oinkv/signal-gateway` | `cc70e5b` | Merge B3 + ghost closure fix |
| DB | `/home/m/data/oinkfarm.db` | — | 1409 signals / 622 events / 100 traders / 11 servers / 286686 price_history / 23 quarantine / 0 audit_log |

Both plans reference pre-Phase-B Wave 2/3 feature commits (`46154543`, `e9be741`, `c6cb99e`) that are now stale.

---

## Headline verdicts

| Plan | Verdict | Category counts | Next step |
|------|---------|-----------------|-----------|
| **B4** (Postgres cutover) | 🔴 **REWRITE-REQUIRED** | 3 SHOWSTOPPER / 2 CRITICAL / 1 MAJOR / 2 minor / 4 OK | Return to FORGE for v2 revision; do NOT schedule cutover until prereqs land |
| **B5** (emitter extraction) | 🟡 **MINOR-REVISION** | 0 SS / 2 CRITICAL / 3 MAJOR / 5 minor / 7 OK | Return to FORGE for v2 revision OR let ANVIL self-correct in Phase 0 |

---

## B4 critical findings (REWRITE-REQUIRED)

Full report: `OINKV-AUDIT-PHASE-B-B4.md`

1. **🔴 SS1** — `systemctl --user restart micro-gate` targets a **nonexistent unit**. micro-gate-v3.py runs inline inside signal-gateway (`USE_INLINE_GATE=1`), no systemd unit exists.
2. **🔴 SS2** — `systemctl --user restart signal-gateway` targets `signal-gateway.service.DISABLED`. The live process is a manually-launched `python3 -m scripts.signal_gateway.gateway` (PID 193712). Cutover command will silently leave signal-gateway writing to SQLite only.
3. **🔴 SS3** — `reconcile_stores.py --full` flag does not exist in argparse; will `exit 2` at T-60min "final reconciliation" step.
4. **🔴 C1** — `OINK_PG_URL` missing from env-flip recipe. Without it, `OINK_DB_ENGINE=postgresql` raises `EnvironmentError` at import time in every service.
5. **🔴 C2** — **PostgreSQL not provisioned on this host**: `psql` not installed, `psycopg` not installed, B2 migration not executed, dual-write disabled, zero CLEAN reconcile reports exist. Plan §1 asserts all prereqs as done — counterfactual-future language.
6. **🟡 M1** — `.openclaw/workspace` fork has B1-only `oink_db.py` (272 lines), canonical has 618 lines. oinkdb-api reads from the fork, so B4 cutover leaves it pointing at the wrong SQLite.

**Verdict rationale:** Same shape as B2-v1 and B3-v1 when they were first audited; directionally sound, operationally wrong. A focused v2 without redesign clears the bar.

---

## B5 critical findings (MINOR-REVISION)

Full report: `OINKV-AUDIT-PHASE-B-B5.md`

1. **🔴 C1** — Phantom function `_forward_raw_to_signals()` at line 2036 — real name is `_route_passthrough()` at line 2035.
2. **🔴 C2** — Emitter API trinity (`emit_signal` / `emit_lifecycle` / `emit_raw`) covers only 11 of 37 live notifier dispatch sites. 24 `log_pipeline_event`, 1 `notify_alert_signal`, 1 `notify_reconciler_action` sites are unmapped.
3. **🟡 M1** — `oinxtractor_client.py` cited at ~150 LOC; live is **479 LOC** (3.2× undercount).
4. **🟡 M2** — §4d splits `_check_signal_state` / `_should_suppress_lifecycle` across modules but the latter calls the former — violates the plan's own "router → emitter, no reverse" rule.
5. **🟡 M3** — "400-600 LOC savings" is ~2× overestimated; realistic is 150-250 LOC (HTTP POSTs already live in discord_notify.py, not signal_router.py).
6. **🟠 Min1-5** — Line drifts within ±10 tolerance; stale HEAD cite `c6cb99e`→`cc70e5b`.

**Verdict rationale:** Architecturally sound; 2-3 paragraphs of net additions + 5-6 line-number corrections produce a clean v2.

---

## Coverage

This batch covers B4 + B5 (last 2 of Wave 1). B1/B2/B3 v2 already audited and shipped. No remaining Wave 1 audit backlog.

## Next actions

1. **A2A FORGE (this orchestrator cycle):** deliver both audit findings so FORGE can revise B4 → REWRITE (v2) and B5 → minor v2 patch.
2. **B3 canary passive wait:** GUARDIAN self-started at merge (04:25 CEST), T+0 CLEAN, T+1h/24h/48h checkpoints follow organic traffic. No orchestrator action needed.
3. **Do NOT dispatch B4 Phase 0 to ANVIL** — B4 v1 will fail at the first cutover command. Wait for B4 v2 + Mike's green light on the prereq chain (B2 migration run + dual-write activation + 7+ clean reports + psycopg install).
4. **B5 can proceed to ANVIL Phase 0 after FORGE v2** (MINOR-REVISION, not blocking) — OR Mike authorizes ANVIL to self-correct C1/C2 inline during Phase 0 and let VIGIL catch residuals.

---

*Audit batch complete. Hermes Agent fallback, 2026-04-20 05:09 CEST.*
