# OinkV Engineering Audit — FORGE Phase B Wave 1 (Consolidated)

**Auditor:** Hermes Agent — **Hermes-subagent fallback** (OinkV LLM timeout)
**Date:** 2026-04-19
**Scope:** Phase B Wave 1 plans B1, B2, B3 (B4 + B5 deferred to next orchestrator cycle, see §Coverage below)
**Dispatch mode:** 3 parallel `delegate_task` subagents per sprint-orchestrator skill "Hermes-Subagent Fallback" pattern, because OinkV `main` agent LLM-timed-out on 2026-04-19T19:23:36Z dispatch (`FailoverError: LLM request timed out` + `session file locked`).

> ⚠️ **Provenance note for Mike:** this consolidated audit is OinkV's voice only by proxy. Three Hermes subagents did the verification work in parallel (~13 min wall-clock), matching the Wave 1 Phase A `OINKV-AUDIT.md` format. If Mike prefers OinkV's own voice, re-dispatching after the `main` agent is free of the current GitHub-issue workload (flag audits #137/#138/#139 active since ~21:15 CEST) remains an option — but all three plans have concrete ship-readiness verdicts below that can drive FORGE revisions immediately.

---

## Headline Verdict per Plan

| Plan | Tier | Ship-Ready? | Top Blockers | Estimated revision effort |
|------|------|-------------|--------------|---------------------------|
| **B1** — DB abstraction layer | 🔴 CRITICAL | ❌ NOT SHIP-READY — REVISE | (1) File inventory misses ~10 sqlite3 consumers, notably `oinkdb-api.py` (38 refs). (2) `event_store.py` dual-location (canonical + vendored) not addressed. (3) Design Q-B1-2 reproduces A1's cross-repo import problem. | 30-60 min FORGE (additive, core design stands) |
| **B2** — PostgreSQL schema + migration | 🔴 CRITICAL | ❌ REJECT — REWRITE REQUIRED | (1) DDL fabricated for 5 of 7 tables. (2) "50 columns" label wrong in 5 places (actual 52). (3) 5 CHECK constraints + 5 triggers silently dropped. (4) 6 of 11 indexes missing. (5) Row counts wrong (1407 not 494; plan says "~1144 post-A10"). (6) A10 P1 alert (104 NULL `filled_at` MARKET-FILLED rows) silently preserved. | 2-4 hrs FORGE — must regenerate §3 DDL from live `.schema` |
| **B3** — Parallel-write verification | 🔴 CRITICAL | ❌ NOT SHIP-READY — REWRITE §1 + §3 | (1) 2 phantom functions in write-site inventory (`_close_signal`, `_scan_once` don't exist). (2) Signal-gateway repo entirely missing (A6 ghost-closure writes skipped). (3) Reconciler column list omits all A1-A11 new columns. (4) 132-line drift on `_check_sl_tp`. | 60-90 min FORGE |

**Wave 1 overall:** 🔴 **NONE of the 3 plans are ship-ready as-drafted.** Core architecture is sound for all three, but inventories and DDL are materially inaccurate. Plans were drafted 2026-04-19 18:03–18:08 CEST, which predated A10's merge by ~25 min and did not re-verify against the then-current code. All three need a drift-correction pass before ANVIL can execute Phase 0 proposals.

---

## Cross-Plan Findings

These issues recur across B1+B2+B3 and should be addressed together in FORGE's revision pass:

### 1. Commit-hash staleness (all 3 plans)

All three plans list `oinkfarm @ 46154543` as the canonical micro-gate commit. Actual HEAD is **`50b23834`** (4 commits ahead: A11, A10 initial, A10 R1 fixes). **Fix:** update each plan's §0 Canonical-files header, re-scan for any new sqlite3/write-site consumers introduced between 46154543 and 50b23834 (notably A10's `merge_databases.py`).

### 2. Schema drift (B2 + B3)

`signals` table has **52** columns, not 50 (A8 `sl_type`, A11 `leverage_source`). Impacts:
- B2: DDL column count wrong
- B3: reconciler spot-check omits the 2 new columns
- B1: orthogonal (no schema touch)

**Fix:** FORGE regenerates column lists from `sqlite3 /home/m/data/oinkfarm.db ".schema signals"` — don't rewrite from memory.

### 3. Cross-repo / dual-location files (B1 + B3)

`event_store.py` now exists in **two locations**:
- `/home/oinkv/.openclaw/workspace/scripts/event_store.py` (canonical, used by micro-gate)
- `/home/oinkv/oink-sync/oink_sync/event_store.py` (vendored by A1, used by lifecycle)

Both write to `signal_events`. B1 lists only one; B3 implies only one. Both must be listed with vendoring-sync policy documented. The Wave-1 Phase A audit already flagged this pattern; the Phase B plans re-introduced the gap.

### 4. Signal-gateway write sites (B3)

A6 added `INSERT INTO signal_events ... 'GHOST_CLOSURE'` and an `UPDATE signals SET notes=...` in `signal-gateway/scripts/signal_gateway/signal_router.py`. This is a **third repo** that writes to the production DB. B3 does not address it. If dual-write flows only through `oink_db.connect()` in oinkfarm + oink-sync, signal-gateway's writes silently skip PostgreSQL.

### 5. Missing write-surface columns in reconciler (B3)

B3 §3 reconciler omits the 13 columns added or heavily touched by Phase A (notably `filled_at`, `sl_type`, `leverage_source`, `tp{1,2,3}_hit_at`, `close_source`, `notes`, `payload` on signal_events, and all 4 A1 event columns). A "7 consecutive clean days" verdict could pass while Phase A correctness silently drifts — defeating the Phase B purpose.

---

## What Wave 1 Got Right (cross-plan credit)

- No regression to the Wave-1 Phase A kraken-sync mistake (dead code) — all 3 plans correctly target `oink-sync/lifecycle.py`, not `scripts/kraken-sync.py`.
- Architecture choices are sound: thin DB abstraction (B1), dual-write with SQLite authoritative (B3), B2's 3-step cutover sequencing.
- Rollback semantics are clean for all 3 plans (revert + env-var disable).
- Acceptance criteria tied to specific SQL / row-count checks.
- Phase 4 V3 spec alignment confirmed (no scope creep, no spec deviation).

---

## Coverage

Wave 1 is defined in `HEAVY-HYBRID-ROADMAP.md` as B1+B2+B3+B4+B5. This audit covers **B1, B2, B3** (the 3 🔴 CRITICAL, highest-risk plans). **B4 and B5 are deferred to the next orchestrator cycle** because:

- **B4 (PostgreSQL cutover, 🔴 CRITICAL)** — very small plan (8,361 bytes), primarily a Mike-gated config switch. Content depends on B1+B2+B3 shipping first. Auditing ahead of B1/B2/B3 revisions would produce a moving target.
- **B5 (emitter extraction from signal_router, 🟡 STANDARD)** — independent decomposition track that ships in parallel with the PostgreSQL work. Lower tier and self-contained. Can be audited in a dedicated cycle once B1-B3 revisions land.

A follow-up dispatch for B4 + B5 can be queued after FORGE revises B1-B3.

---

## Recommended Next Steps (for Mike + FORGE)

1. **FORGE revises B1, B2, B3** per the individual audit findings:
   - B1: re-grep all 3 repos for sqlite3 consumers; update §1 + §2 inventories; resolve Q-B1-2 as "vendor per A1 precedent" unless Mike prefers repo consolidation.
   - B2: **do not patch** — regenerate §3 DDL from live `.schema`. Restore 6 CHECKs and 11 indexes. Resolve OQ-B2-2 (A10 P1 rollback sequence) before migration plan is finalized.
   - B3: re-verify §1 write-site inventory against current code (no phantom functions). Add signal-gateway to §2. Expand §3 reconciler column list.

2. **Estimated total FORGE revision effort:** 3-5 hours (B2 is the heaviest). B1 and B3 are additive; only B2 may need partial rewrite.

3. **Do NOT start Phase 0 proposals on unrevised plans.** ANVIL would either abandon the plan mid-Phase-1 (when the phantom functions surface) or ship a half-abstraction (B1's missing oinkdb-api.py).

4. **A10 P1 alert is a B2 precondition.** B2 silently preserves the 104 KPI-R5 violations. If Mike rolls A10 back, B2's pre-migration row counts change. If Mike accepts A10's historical data, document the acceptance in B2's §3 so the P1 propagates into PostgreSQL by design, not by accident.

5. **B4 + B5 audit** can be dispatched after B1-B3 revisions land.

---

## Provenance Files

- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B1.md` (16,282 bytes) — detailed B1 audit
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B2.md` (25,557 bytes) — detailed B2 audit (subagent write direct)
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-B3.md` (18,267 bytes) — detailed B3 audit
- `/home/oinkv/forge-workspace/plans/OINKV-AUDIT-PHASE-B-HERMES-FALLBACK-DISPATCHED.marker` — dispatch rationale
- `/tmp/dispatch_oinkv_phaseb_audit.log` — OinkV's original LLM-timeout evidence
- Previous (stale) dispatch marker renamed: `OINKV-AUDIT-PHASE-B-DISPATCHED.marker.FAILED-llm-timeout-20260419T1923Z`

---

*Consolidated audit complete. Hermes fallback, 2026-04-19T19:55Z.*
