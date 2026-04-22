# OinkFarm Heavy Hybrid — Sprint Report

*Document owner: Hermes (manager agent)
Last updated: **2026-04-22 10:50 CEST**
Canonical event stream: `events.jsonl` (795 events captured)
Public dashboard: https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/*

---

## 1. What is Heavy Hybrid?

OinkFarm is a real-time crypto-signal pipeline: it watches Discord + Telegram for trading
calls, parses them with a mix of deterministic parsers and a local LLM (Gemma), checks
them against live prices from four exchanges, and tracks every signal from post to close.
The system runs ~1,000 signals per day on a single server ("the barn"), covering crypto
and a handful of non-crypto assets.

By early April 2026 the system was functionally complete but **the trust in its data**
had degraded: ~5 historical signals had been closed by mistake, ~84% of `FILLED` signals
were missing the exact `filled_at` timestamp, PnL on partially-closed trades was off by
up to 2×, and there was no end-to-end accuracy measurement.

An independent reviewer — **Arbiter V3** — spent seven phases analysing the codebase and
produced a verdict branded **HEAVY HYBRID**:

> *Keep what already works (ingestion, parsers, multi-exchange pricing, supervisor,
> 92.5% lifecycle automation), adopt a stronger data substrate from the architecture
> documents (event log, trace layer, PostgreSQL, Redis Streams), decompose the
> 4,366-line `signal_router` God Object into real services, and defer the
> algorithmic / execution layer until the data underneath is provably correct.*

Heavy Hybrid is **not a rewrite**. It is a four-phase upgrade that refuses to throw away
working code:

| Phase | Purpose | Timeline |
|---|---|---|
| **A · Data Truth** | Close the data-integrity gaps inside the existing SQLite-backed pipeline | **✅ Shipped 2026-04-18 → 2026-04-19** |
| **B · Infrastructure** | Decompose the God Object + move to PostgreSQL + add Redis Streams + shadow-mode observability | **🟡 In flight — 8 of 15 tasks merged** |
| **C · Observability + Confidence + Anomaly** | 7 tasks: unified metrics, confidence-routing UI, anomaly detection, alerting, runbooks | **🔵 Planned — starts late May 2026** |
| **D · Algorithmic / Execution** | Automated position sizing, execution routing, hedging | **⚫ Deferred** — gated on a 2-month clean Phase-D Readiness Report (Q-HH-6) |

The HH endgame is **data purity**. The dashboard is the window onto the data, not a
competing product. The trading-execution layer (Phase D) only begins when the data layer
is provably correct for two consecutive months.

---

## 2. The Agents

Heavy Hybrid is executed by a multi-agent council. Every merge goes through multiple
reviewer gates before touching production. Roles:

| Role | Handle | Model | Responsibility |
|---|---|---|---|
| **Hermes** 🪽 | *this* | `anthropic/claude-opus-4-7` | Manager. Orchestrates work, routes decisions, files GitHub issues, kicks stalled agents, triages Mike-gates. Writes reports for Mike + Dominik. |
| **OinkV** 🐷 | `main` | `anthropic/claude-opus-4-6` | Owns the OinkFarm signal pipeline source-of-truth. Reviews Phase plans from pipeline-truth angle. Repo: `signal-gateway`. |
| **OinkDB** 🗄️ | `oinkdb` | `anthropic/claude-opus-4-6` | Owns the canonical signal database + `:8888` API. Handles integrity audits, lifecycle events, trader scorecards. Repo: `oinkdb-api`. |
| **FORGE** 🔥 | `forge` | `openai/gpt-5.4` | Writes the technical execution plans that ANVIL implements. Cross-vendor second-opinion critic on architectural questions. |
| **ANVIL** ⚒️ | `anvil` | `anthropic/claude-opus-4-6` | The builder. Drafts proposals, writes the code, opens PRs, runs merge trains. |
| **VIGIL** 🔍 | `vigil` | `anthropic/claude-opus-4-7` | Code-quality + spec-compliance reviewer. Scores proposals on a 5-dimension rubric, target ≥ 9.5 for CRITICAL tier. |
| **GUARDIAN** 🛡️ | `guardian` | `anthropic/claude-opus-4-7` | Data-integrity reviewer + post-merge canary runner. Same 9.5 bar as VIGIL. |
| **OinXtractor** 📥 | `extractor` | `anthropic/claude-opus-4-6` | Extracts structured data from raw inputs (used as a support tool; not on the critical HH path). |
| **Pilot** 🛩️ | `pilot` | `anthropic/claude-opus-4-6` | (Post-sunset 2026-04-22) Owns the `:8484` social-listener dashboard and sprint-duty tickets. No longer a trading-system owner. |
| **Mike** 👤 | human | — | CEO of QuantisDevelopment. Final authority on scope + P0 gates + irreversible production-data mutations. |
| **Dominik** 👤 | human | — | Co-founder; CEO of Quantis Capital. Optional consult on Phase D entry. |

### 2.1 The review-and-merge loop

Every task walks this loop before code hits `master`:

```
FORGE publishes plan  →  ANVIL drafts proposal  →  VIGIL + GUARDIAN score proposal
                                                   (≥ 9.5 for CRITICAL tier)
                                                        ↓
                                                ANVIL writes code
                                                        ↓
                                            VIGIL + GUARDIAN Phase-1 review
                                                        ↓
                                           ANVIL merges (squash + delete branch)
                                                        ↓
                                         GUARDIAN runs post-deploy canary
                                                        ↓
                                     CANARY_PASS → task closed; CANARY_FAIL → fix + re-canary
```

Hermes monitors progress via the **event stream** — a 795-event append-only log at
`sprint-checkpoint/events.jsonl` that every agent writes to when they start/finish/block.
The public dashboard is a pure reducer over this log; no hand-edited state.

### 2.2 Governance rules ("Kitten Mittens")

Established protocol for live-production work:

1. **One finding per issue** — repro + observed/expected + blast radius + fix sketch.
2. **One PR per fix** — small, isolated, reversible. No bundling.
3. **Fail-closed defaults** on every behavior change.
4. **Runtime QA before declaring done** — no "diff-only" sign-off on live paths.
5. **Agent council on any production-data mutation** — mandatory multi-agent review.
6. **CEO (Mike) signs off on P0 / irreversible mutations** — only the non-reversible
   class (A10 DB merge, destructive migrations, B4 Postgres cutover). Scope, ordering
   and backlog decisions never park on Mike.

---

## 3. What Has Happened (chronological)

### Phase A · Data Truth — shipped in a single weekend

**2026-04-18 (Fri night → Sat).** FORGE published the first three Phase A plans.
ANVIL drafted A3 (auto-fill `filled_at` for MARKET orders — the 84%-NULL root cause),
VIGIL scored 9.85, GUARDIAN 10.0. A3 shipped as `oinkfarm#125` shortly after midnight.
That was the starting gun.

**2026-04-19 (Sun).** Between 01:11 and 17:27 CEST, all 10 remaining Phase A tasks
shipped:

| Task | What it fixed |
|---|---|
| **A1** | `signal_events` schema + 12 event types (append-only audit backbone) |
| **A2** | `remaining_pct` partial-close model — fixed the 2× PnL error |
| **A3** | Auto-fill `filled_at` for MARKET orders (shipped 2026-04-18) |
| **A4** | `PARTIALLY_CLOSED` status |
| **A5** | Parser-type confidence scoring |
| **A6** | Ghost-closure confirmation flag |
| **A7** | `UPDATE → NEW` detection guard (phantom-trade prevention) |
| **A8** | Conditional SL type |
| **A9** | Denomination multiplier for 1000×-prefixed symbols |
| **A10** | Database merge — test DB into prod DB, recovered ~1,165 historical signals |
| **A11** | Leverage source tracking |

**A10 needed two proposal passes** — first got VIGIL REVISE at 7.9, v2 re-scored
9.7 / 9.8 and merged at 20:30 CEST.

**Phase A canary results** (evening 2026-04-19):
- ✅ PASS: A1, A2, A3, A5, A11
- 🔴 FAIL (later re-run and PASS): A4, A6, A9, A10

All four canary failures were re-validated at 13:08 UTC on 2026-04-20 with **A10
validating 17 live signals against the recovered historical dataset at zero drift**.

### Phase B · Infrastructure — 8 of 15 merged

**2026-04-19 → 2026-04-20 "throttle on".** Mike's directive translated into Hermes
running FORGE / ANVIL / GUARDIAN as **parallel tracks** instead of sequenced. Result:
**8 Phase B merges in under 12 hours**:

| Task | PR | Merged | What shipped |
|---|---|---|---|
| **B1** | `oinkfarm#149`, `oinkdb-api#9`, `signal-gateway#21` | 2026-04-20 00:22 | Database abstraction layer (the seam that lets SQLite → Postgres happen) |
| **B2** | `oinkfarm#153`, `oinkdb-api#11`, `signal-gateway#24` | 2026-04-20 01:21 | PostgreSQL schema translation + one-time data migration |
| **B3** | multi-repo | 2026-04-20 03:47 | Parallel-write verification scaffold |
| **B5** | `signal-gateway#25` | 2026-04-20 06:55 | Emitter extraction |
| **B6** | `signal-gateway#29` (final) | 2026-04-21 22:45 | Extract Cornix + Chroma parsers from 4,366-line `signal_router` |
| **B7** | `signal-gateway#27` | 2026-04-20 10:17 | Extract WG Bot parsers |
| **B8** | `signal-gateway#26` | 2026-04-20 09:57 | Cross-channel dedup consolidation — extract `dedup.py` |

**Phase B canary results** (as of 2026-04-22 02:29 UTC): B1, B2, B3, B5, B6, B7, B8
all PASS — the eight shipped tasks have cleared post-deploy validation.

**2026-04-22 08:01 UTC — M189 merge train.** This morning ANVIL landed a coordinated
three-PR merge for the event-model Phase-1 work (the `be_tolerance` shared helper that
M189 depends on):
- `oinkfarm#190` (83f198a9)
- `signal-gateway#31` (8787b94)
- `oink-sync#12` (8311ea6)

All three landed on the same commit wave. GUARDIAN canary started immediately.

### Infrastructure events (non-task)

- **Dashboard rewrite (2026-04-20)** — Mike flagged "dashboard is stale". Hermes
  rewrote it as an event-stream reducer with 4-section layout
  (`aa34cf7`, `9d64833`, `c35b3bf` backfilled 262 historical events). The dashboard
  is now computed from the event log rather than polling agent workspaces.
- **Decision-triage pass (2026-04-20)** — Mike said "stop parking everything on me".
  Hermes took 15 outstanding `Q-*` architectural questions and routed 13 of them
  away from Mike: 5 to Hermes-ops, 4 to agent council, 4 to single-agent technical
  calls. Only 2 genuine Mike-gates remained (Q-B3-2 verification window, Q-HH-6
  Phase D entry authority) — both answered same day.
- **Heavy Hybrid Q-HH decisions (all 6 resolved)** —
  `Q-HH-1` same-server Docker Compose, `Q-HH-2` per-topic MAXLEN, `Q-HH-3` single-host,
  `Q-HH-4` signal_events DB-level REVOKE day 1, `Q-HH-5` soft-flag provisional
  low-confidence, `Q-HH-6` monthly Phase-D Readiness Report with 2-consecutive-GREEN
  + Mike sign-off, Dominik optional.
- **Sprint cadence crons (Hermes-owned)** — manager-review (60m), health-monitor
  (60m), flag-auditor (60m), GitHub-issue-tracker (30m), sprint-checkpoint-publisher
  (10m), sprint-escalation-watcher (30m), sprint-scribe (30m), sprint-poke-watcher
  (15m — aggressive stall-recovery with model rotation).
- **Bybit Suite / Thunderbolt / CFT sunset (2026-04-22)** — Pilot's prior trading-
  system ownership was retired. Live Bybit trading migrated to a new-server Hermes.
  Local services stopped + disabled. Pilot's brain files rewritten; historical lore
  archived at `pilot-workspace/vault/sunset-2026-04-22/`. Preservation tags:
  `sunset-2026-04-22-pre-cleanup` on oinkfarm master, `sunset-2026-04-22` on
  `QuantisDevelopment/oinktrader-cft` (archived). Pilot's new role: `:8484` dashboard
  + sprint-duty.

### Headline stats (at 2026-04-22 10:50 CEST)

- **56 merge events** across three repos (oinkfarm, signal-gateway, oinkdb-api)
- **28 CANARY_PASS** / **4 CANARY_FAIL** (all 4 re-run to PASS)
- **795 events** in the canonical event stream (first event 2026-04-18 18:23 UTC)
- **11 Phase A tasks shipped + validated**
- **8 Phase B tasks shipped + canary-clean**
- **0 open Mike-gates** at report time
- **~1,487 total signals** tracked in live OinkDB (95 active, 19 pending, 1,157 closed)

---

## 4. What Remains (the forward plan)

### Phase B remaining work (7 tasks)

Merged: B1, B2, B3, B5, B6, B7, B8 + M189 prerequisite. Remaining:

| Task | Status | What it does |
|---|---|---|
| **B4** | Waiting on 7-day B3 soak | **PostgreSQL cutover itself.** Flip `OINK_DB_DUAL_WRITE=true`, run 7 consecutive clean reconciliation days, then cut over. Mike-gate before production flip. |
| **B9** | In review (Guardian ✅, Vigil pending) | W1 immutable `signal_events` records — INSERT-only origin table on the critical path |
| **B10** | Plan published | Redis Streams topic provisioning |
| **B11** | Plan published | Event-walk authoritative source flip (dual-compute → authoritative) |
| **B12** | In review | Shadow-mode `publish_to_stream` — 8 topics |
| **B13** | Plan published | Docker Compose single-host topology |
| **B14** / **B15** | Plan published | Remaining refactor + observability scaffolding |

### Phase C · Observability + Confidence + Anomaly (starts late May 2026)

Seven tasks, all scoped, plans drafted by FORGE:

1. **C1** — Unified metrics surface (Prometheus/OpenTelemetry)
2. **C2** — Confidence-routing UI (soft-flag provisional per Q-HH-5)
3. **C3** — Parser accuracy regression harness
4. **C4** — Alerting (PagerDuty / Discord critical alerts)
5. **C5** — Anomaly detection over full signal history
6. **C6** — Runbook library
7. **C7** — Executive reporting + weekly data-quality digest

### Phase D · Algorithmic / Execution — DEFERRED

Not planned by FORGE until the Phase-D gate passes. Governance per `Q-HH-6`:

1. GUARDIAN publishes a **monthly Phase-D Readiness Report** scoring Arbiter's 7
   prerequisites (traffic-light per prerequisite + evidence citations).
2. Mike signs off when **all 7 are GREEN for 2 consecutive reports**.
3. CEO (Dominik) consult is *optional*, not required.
4. **FORGE does not draft Phase D plans** until the gate passes.

Template already published at `PHASE-D-READINESS-REPORT-TEMPLATE.md`.

### Milestones on the calendar

| Date | Milestone | Notes |
|---|---|---|
| **2026-04-22** (today) | M189 merge train canary | In progress |
| **2026-04-23 → 2026-04-26** | B3 reconciliation soak (7 clean days) | Any single discrepancy resets the clock |
| **2026-04-26 (earliest)** | **B4 PostgreSQL cutover** | Mike-gate. Requires zero discrepancies across 7 daily reports. |
| **2026-04-27 → 2026-05-15** | B9 / B10 / B11 / B12 / B13 merges + canaries | Phase B Wave 3/4 completion |
| **May 16-17, 2026** | **Heavy Hybrid core readiness target** | Phase B complete + Phase C kickoff |
| **Late May 2026** | Phase C start | 7 tasks, sequenced |
| **+2 months from C complete** | First Phase-D Readiness Report | GUARDIAN-generated |
| **+4 months earliest** | Phase D entry if gate passes | Mike sign-off on 2 consecutive GREEN reports |

---

## 5. How to Read the Dashboard

Public URL: **https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/**

- **🔴 Live now** — events from the last 1 h / 4 h / 24 h (merges, canaries, decisions,
  plan publications). This is the ops pulse.
- **🧭 Needs Mike** — open Mike-gates with age and options. Clicking a question ID
  shows the full FORGE plan reference. Zero open right now.
- **🔍 Missing evidence** — gap detector: PRs without reviews within 24 h, merges
  without canaries within 2 h, decisions open too long. Most current entries are
  historical PR-metadata gaps on already-merged tasks.
- **🫀 Freshness by agent** — each agent's last emitted event with stale/fresh
  colouring. If FORGE goes 🔴 stale overnight, the planning loop has broken.
- **Tasks table** — click any task ID for its per-task page with canary status +
  full timeline.

The dashboard publishes every 10 minutes via the `sprint-checkpoint-publisher` cron
(`deliver=local`, pushes to `gh-pages` branch). Event-stream integrity is verified
by the **Scribe** cron (every 30 min) and the **Escalation-watcher** cron (every
30 min, Mike-ping only on FAIL / BLOCK / multi-hour stall).

---

## 6. Principles — the non-negotiables

1. **Data purity first** — Phase D does not start until the data under it is proven
   for 2 months.
2. **Every change is reviewed by two reviewers + a canary** — VIGIL + GUARDIAN +
   post-merge canary, no exceptions on CRITICAL tier.
3. **Cross-vendor review** — FORGE runs on `openai/gpt-5.4` specifically so a
   different training distribution catches Opus blind spots.
4. **No bundling, no rewrites, no vanity refactors** — one PR per issue, small and
   reversible.
5. **Fail-closed on every behavior change** — error paths must be safe paths.
6. **Evidence over vibes** — every "it's fixed" claim is backed by a canary, a
   screenshot, or a `curl` response in the event stream.
7. **Agents handle prep + dry-runs + validations autonomously** — Mike is only
   pulled in for irreversible production-data mutations. Scope / ordering / backlog
   never park on Mike.
8. **The dashboard is the window to the data, not a competing priority** —
   correctness > polish. If a number can't be trusted, the dashboard shows the
   problem explicitly.

---

## 7. Risk watch

| Risk | Mitigation |
|---|---|
| B3 reconciliation soak reset by a late-detected discrepancy | 7-clean-day + reset rule; GUARDIAN runs daily reconciliation; any discrepancy logs a BLOCKED event |
| B4 PostgreSQL cutover corrupts live data | One-shot migration is tested via B2's migration script + dual-write verification (B3). Rollback tag + systemd disable-before-enable pattern documented. |
| Phase B merge velocity drops during canary wait | Parallel FORGE plan-ahead (all 15 plans + Phase C + HH roadmap already published) keeps ANVIL never waiting |
| Agent drift / stale context leaking back in | Sprint-poke-watcher cron (15 min) + model rotation every 3rd run + memory invariants in Hermes skills |
| Mike unavailable for a gate | Gate list is pre-triaged; Hermes escalates only on genuine irreversible mutations; every other open item has a pre-approved fallback path |

---

## 8. Appendix — Source-of-truth artefacts

- **Event stream**: `sprint-checkpoint/events.jsonl` (795 events)
- **State of the sprint (auto-generated)**: `sprint-checkpoint/sprint-log/STATE-OF-SPRINT.md`
- **Heavy Hybrid roadmap**: `sprint-checkpoint/sprint-log/phases/heavy-hybrid.md`
- **Per-phase plans**: `sprint-checkpoint/sprint-log/phases/phase-{a,b,c}.md`
- **Per-wave plans**: `sprint-checkpoint/sprint-log/waves/wave-{1,2,3,4}.md`
- **Per-task detail**: `sprint-checkpoint/sprint-log/tasks/{A*,B*}.md`
- **Phase-D Readiness Report template**: `PHASE-D-READINESS-REPORT-TEMPLATE.md`
- **FORGE plans (raw)**: `sprint-checkpoint/raw-artifacts/forge/plans/`
- **Dashboard generator**: `sprint-checkpoint/generate.py` + `templates/`
- **Cron orchestration scripts**: `~/.hermes/scripts/{manager-review,flag-auditor,
  github-issue-tracker,sprint-checkpoint-publisher,sprint-escalation-watcher,
  sprint-scribe,sprint-poke-watcher,hermes-monitor}.py`

---

*This report is maintained by Hermes. It is regenerated on demand but not
automatically — the event stream + dashboard are the live surfaces. If you need a
fresh snapshot, ask and a new version will be checked in.*
