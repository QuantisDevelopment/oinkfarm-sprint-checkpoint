# State of the Sprint — Plain English

*Last updated: 2026-04-22 08:11 UTC · Read time: ~8 min*

## The Mission (one paragraph)

OinkFarm is the pipeline that watches Discord and Telegram for trading signals, parses them with a mix of deterministic parsers and a local LLM (Gemma), checks them against live prices from four exchanges, and tracks every signal from post to close. It runs about 1,000 signals/day across crypto and a handful of non-crypto assets, on a single server ("the barn"). The thing that's broken is **trust in the data**: ~5 historical signals were closed by mistake, about 84% of FILLED signals are missing the exact fill timestamp, the profit/loss on partially-closed trades is off by up to 2x, and there's no end-to-end accuracy measurement. An outside reviewer — **Arbiter V3** — spent seven phases analysing this and returned a verdict called **HEAVY HYBRID**: keep what already works (ingestion, parsers, multi-exchange pricing, supervisor, 92.5% lifecycle automation), adopt a stronger data substrate from the architecture documents (event log, trace layer, PostgreSQL, Redis Streams), decompose the 4,366-line `signal_router` God Object into real services, and **defer** the algorithmic/execution layer until the data underneath is provably correct. Heavy Hybrid is not a rewrite — it's a four-phase upgrade (A Data Truth → B Infrastructure → C Observability → D Algo, deferred) that refuses to throw away working code.

## Today in one paragraph

The merge train finally left the station. ANVIL shipped M189 Step-0 at 08:01 UTC as a coordinated three-PR landing across the three repos that matter — oinkfarm#190, signal-gateway#31, and oink-sync#12 — all going in on the same commit wave (83f198a, 8787b94, 8311ea6). That's the event-model Phase-1 work that's been sitting in merge-train prep since last night, and it cleared cleanly with all three PRs shipping together rather than drifting apart. Canary from GUARDIAN is the next thing to watch.

B9 (W1 immutable signal records, the INSERT-only origin table on the critical path) picked up a fresh VIGIL approval at 07:51, stacking on top of this morning's GUARDIAN clearance — so B9 is now through both review gates and lined up for merge. On the frustrating side, B4 (the PostgreSQL cutover itself) did the same blocker-resolved-then-re-blocked dance as last tick, twice within a minute at 07:47 and 07:48: a phantom external-dependency flag that's really just the B3 seven-day reconciliation soak gating things as expected. Not a new problem, but it's noisy on the dashboard.

No new question kicked up for Mike this tick. The watchlist hasn't changed: five PRs (A11 #133, B1 #21 and #149, B2 #24, B5 #25) still sit without a logged review inside 24 hours, and PILOT plus VIGIL heartbeats are reading stale past three hours. Most of that is metadata lag on already-merged work rather than real silence, but if it persists through another run it's worth a nudge.

## Where We Are Today (one paragraph)

**Phase A is complete AND proven** — all 11 tasks (A1-A11) shipped in the last 48 hours, and as of 13:08 UTC today the four canary failures (A4, A6, A9, A10) that were red overnight have been re-run and all PASS, with A10 validating 17 live signals against the recovered historical dataset at zero drift. **Phase B is in flight** with 8 of 15 tasks merged (B1 database abstraction layer, B2 PostgreSQL schema + one-time migration, B3 parallel-write verification scaffold, B5 emitter extraction, B6 Cornix/Chroma parsers, B7 WG Bot parsers, B8 router decomposition). **FORGE has published all 15 Phase B plans plus a Phase C summary and a Heavy Hybrid roadmap.** Phase C is fully scoped (7 tasks), Phase D remains deferred. **Live risks are down to housekeeping:** GUARDIAN confirmed the B3 dual-write gap is intentional (`OINK_DB_DUAL_WRITE=false` is correct until B3 reconciliation tooling is live), and the remaining warnings are stale PR-metadata gaps on already-merged tasks, not real blockers. **Nine Mike-gates are open**, including the big one: B4 PostgreSQL cutover approval, earliest on **2026-04-26** (7 consecutive clean reconciliation days after B3 merged 2026-04-19; clock still clean). Phase C starts **late May 2026** after Phase B quality gates pass.

## Last 48 Hours — The Story

**Friday night into Saturday (2026-04-18).** The sprint was still in Phase 2 of the older `/signals/*` API work. FORGE published the first three Phase A plans (A1, A2, A3) around 23:27 CEST. ANVIL immediately drafted A3 (auto-fill `filled_at` for MARKET orders — the 84%-NULL root cause), VIGIL passed it at 9.85, GUARDIAN passed it at 10.0. A3 merged shortly after midnight as PR #125. That was the starting gun for the real Phase A push.

**Sunday (2026-04-19) — Phase A shipped in a single day.** Between 01:11 and 17:27 CEST, every remaining Phase A task shipped: A1 (signal_events schema + 12 event types), A2 (remaining_pct partial-close model — fixed the 2x PnL error), A4 (PARTIALLY_CLOSED status), A5 (parser-type confidence scoring), A6 (ghost closure confirmation flag), A7 (UPDATE→NEW detection guard — phantom trade prevention), A8 (conditional SL type), A9 (denomination multiplier for 1000x-prefixed symbols), A11 (leverage source tracking). All were gated through the same loop: FORGE plan → ANVIL proposal → VIGIL + GUARDIAN phase-0 verdicts (target ≥9.5) → ANVIL codes → VIGIL + GUARDIAN phase-1 review → ANVIL merges → GUARDIAN canary. A10 (database merge — test DB into prod DB, recovering ~1,165 historical signals) needed two passes: first proposal got a VIGIL REVISE at 7.9, v2 came back 9.7/9.8 and merged 20:30. B1's plan published at 18:03, and FORGE kept running — B9 and B12 plans landed by 19:31. Late evening, GUARDIAN ran the Phase A canary battery: A1 PASS, A2 PASS, A3 PASS, A5 PASS, A11 PASS — and A4, A6, A9, A10 **FAIL**. Those are the four dashboard-red rows Mike can see in "Missing evidence" right now.

**The throttle went on overnight.** Mike's directive "throttle on" translated into Hermes running FORGE, ANVIL and GUARDIAN as parallel tracks instead of sequenced — the result is visible on the 20 Apr timeline: by 00:22 CEST B1 was already merged; by 03:47 B3 was merged; B5 at 06:55; B6 at 08:46; B7 at 12:17; B8 at 11:57. **Eight Phase B merges in under 12 hours.** In parallel, FORGE published the full Wave 2/3/4 plan set — B4, B5, B6, B7, B8, B10, B11, B13, B15 plus a Phase C summary and the HEAVY-HYBRID-ROADMAP master document. That roadmap laid out all 15 Phase B tasks, the 7 Phase D prerequisites, the critical path (B1→B2→B3→B4→B9→B10), and the parallelism strategy that saves ~3-4 weeks.

**Two product-level changes Mike pushed today.** First, "**dashboard is stale**" — that produced commit `aa34cf7` ("rewrite as event-stream reducer + 4-section layout (Mike spec)") plus `9d64833` ("event-stream reporting core + shared skill") and `c35b3bf` backfilling 262 historical events into the canonical `events.jsonl`. The dashboard is now computed by reducing the event log rather than polling agent workspaces, which is why "Live now" refreshes cleanly and "Freshness by agent" can show who went quiet. Second, "**stop parking everything on me**" — Hermes built a decision-triage pass (published today as `Q-RESOLUTION-PROPOSALS.md`) that took 15 outstanding Q-* architectural questions and routed 13 of them away from Mike: 5 to Hermes-ops, 4 to agent council, 4 to single-agent technical calls, leaving only **2 genuine Mike-gates** (Q-B3-2 verification window, Q-HH-6 Phase D entry authority). Mike answered both today: **7 days with reset-on-discrepancy** for B3, and **monthly GUARDIAN Phase D Readiness Report + 2-consecutive-GREEN + Mike sign-off, CEO consult optional** for Phase D entry. Hermes then resolved the 6 non-Mike gates in its own lane — psycopg3, canonical oink_db.py location, same-server hosting for PG and Redis, re-enable systemd unit before B4, fork-sync for B4.

**What went wrong and how it got fixed.** The B1 merge on 04-20 00:22 triggered a 2.5x lock-wait regression caught by VIGIL on phase-1 review — ANVIL fixed it by deriving `busy_timeout` from the `timeout` parameter (commits `75a32f7f`, `963fa3e`, `c18b1a4`, `f58216f8`, `0fbcbf1b`). B2 came in with a GUARDIAN REVISE at 5.0 (data-integrity concern on migration script) and was re-scored to 9.5/9.6 after ANVIL's R2. B3 got a VIGIL REVISE at 7.55; R2 re-scored 9.6. The Phase A canary failures (A4/A6/A9/A10) have **not** been fixed yet — they are flagged in the dashboard's Missing Evidence panel and are the first items GUARDIAN needs to address before Phase B Wave 3 can depend on Phase A data quality.

**What's been autonomous vs Mike-direct.** Autonomous: all 11 Phase A plans (FORGE), all 15 Phase B plans (FORGE), all ANVIL proposals/code, all VIGIL/GUARDIAN reviews and canaries, 6 Hermes-ops decisions today, and the dashboard+event-stream rebuild. Mike-direct: the "throttle on" parallelization order, the "dashboard is stale" feedback that triggered the event-sourcing rewrite, the "stop parking everything on me" directive that produced the triage skill, Q-B3-2 (7-day + reset rule), Q-HH-6 (Phase D entry governance). Everything else resolved inside the agent loop.

## What's Next — The Plan

- **Next merges expected (this week):** B2 canary result (currently CANARY_PENDING), B3 verification window opens, B6/B7/B8 canary results land. Phase B Wave 2 decomposition is essentially done — next real code merge is B4 (cutover) itself, which is a one-day task gated on B3's 7-clean-day soak.
- **The April 26 cutover gate (B4):** B3 merged 2026-04-19. Under the **7-day + reset rule**, earliest B4 cutover is **2026-04-26** if every daily reconciliation report shows zero row-count and zero event-count discrepancies. Any single discrepancy resets the clock. Mike's explicit go-ahead is still required on the day.
- **Phase C start (late May 2026):** Begins after Phase B quality gate (all Wave 3 + Wave 4 tasks green, W1 immutable records live on PostgreSQL, W4 trace layer shipped). Roadmap estimates week 8+ from now; detailed plans for C1-C7 get written when Phase B is near-complete.
- **Phase D (deferred; governed by Q-HH-6 rule):** No Phase D planning work until GUARDIAN's **monthly Phase D Readiness Report** shows all 7 Arbiter prerequisites GREEN for **2 consecutive months**. Template was published today (`PHASE-D-READINESS-REPORT-TEMPLATE.md`). Mike signs off when ready; Dominik (CEO) consult is optional, not required.

## The Players

| Role | Who | What they do in one line |
|---|---|---|
| ANVIL ⚒️ | OpenClaw agent | Writes the actual code and opens PRs |
| VIGIL 🔍 | OpenClaw agent | Reviews code quality + spec compliance (5-dim score, target ≥9.5) |
| GUARDIAN 🛡️ | OpenClaw agent | Reviews data integrity + runs canary after deploys |
| FORGE 🔥 | OpenClaw agent | Writes the technical execution plans ANVIL works from |
| Hermes 🪽 | This agent | Orchestrates, triages decisions, reports to Mike |
| OinkV 🐷 | Main OpenClaw agent | Owns the signal pipeline; reviews plans from pipeline-truth angle |
| Mike | Human | CEO of OinkFarm, final authority on all gates |
| Dominik | Human | Co-founder; CEO of Quantis Capital; optional consult on Phase D |

## How to Read the Dashboard

The dashboard at [quantisdevelopment.github.io/oinkfarm-sprint-checkpoint](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) is computed by reducing the event log at `events.jsonl` — it is not a hand-edited status page. **🔴 Live now** shows the last 1h / 4h / 24h of events: merges, canary results, decisions, plan publications. **🧭 Needs Mike** is the queue of gates that can only be closed by you, with age and options — 9 open right now; clicking a question ID shows the full FORGE plan reference. **🔍 Missing evidence** is the dashboard's gap detector: PRs without reviews within 24h, merges without canaries within 2h, decisions sitting open too long — 19 gaps visible, mostly historical PR metadata. **🫀 Freshness by agent** is your single-glance health check: each agent's last emitted event, how long ago, and fresh/stale colouring — if FORGE goes 🔴 stale overnight, something's wrong with the planning loop. Click any task ID in the Tasks table to jump to its per-task page with canary status and full timeline.

## Glossary

**ANVIL ⚒️** — OpenClaw agent that consumes FORGE's plans and writes the actual implementation code, opens PRs, deploys merges.

**Arbiter V3** — Independent technical evaluation of OinkFarm vs the 26-document architecture plan. Seven phases, approved 9.5/10 on all dimensions. Produced the HEAVY HYBRID verdict that this sprint is executing against.

**B1–B15** — The 15 Phase B tasks. Examples: B1 = database abstraction layer, B2 = PostgreSQL schema, B3 = parallel-write verification, B4 = PostgreSQL cutover, B9 = W1 immutable signal records, B12 = Redis Streams, B13 = Docker Compose deployment.

**Barn** — Nickname for the production server where OinkFarm runs. Hosts signal-gateway, oink-sync, OinkDB API, SQLite, and will host PostgreSQL + Redis post-B4.

**Canary** — A post-merge safety check run by GUARDIAN: does the new code preserve data integrity in production? PASS unblocks the next task; FAIL blocks the task and surfaces to the dashboard.

**Council review** — When a Q-* architectural decision needs multiple agent perspectives (e.g. FORGE + GUARDIAN on data-integrity questions), Hermes opens a GitHub Issue with a 48h comment window. Alternative to kicking it to Mike.

**FORGE 🔥** — OpenClaw agent that reads the Arbiter V3 report plus the codebase and produces the Technical Execution Plans that ANVIL implements from. Does not write code, does not review code.

**GUARDIAN 🛡️** — OpenClaw agent that owns data-integrity review (schema correctness, formula accuracy, migration safety, query performance, regression risk) and runs every post-deploy canary. Will publish the monthly Phase D Readiness Report.

**Heavy Hybrid** — The four-phase upgrade verdict from Arbiter V3. Retain what works, adopt the stronger architecture substrate, adapt orchestration into real services, defer algo/execution until data is trusted. Phases A, B, C, D.

**Hermes 🪽** — This agent. Orchestrates the sprint, triages decisions away from Mike where safe, reports status, owns the event stream and dashboard.

**Mike-gate** — A decision only Mike can make. After triage, 2 of today's 15 Q-* questions are genuine Mike-gates (Q-B3-2, Q-HH-6); the rest route elsewhere.

**oink-sync** — The FastAPI service on port 8889 that handles real-time price updates, SL/TP detection, limit fill detection, and price history snapshots across four exchanges (Binance, Bybit, Kraken, yfinance).

**OinkDB** — The read-only API on port 8888 that serves dashboard, portfolio webhook, and OinkTrader. Also the name of the SQLite database file behind it (`/home/m/data/oinkfarm.db`).

**OinkV 🐷** — The main OpenClaw agent that owns the signal pipeline, used as a pre-audit reviewer for FORGE's plans (staleness check on file paths, function signatures, DB schema).

**Phase A** — "Data Truth." Tasks A1-A11 — fix signal-data correctness on the existing SQLite foundation. **Complete.**

**Phase B** — "Infrastructure." Tasks B1-B15 — migrate to PostgreSQL, decompose the signal_router God Object into real services, add Redis Streams, containerize with Docker Compose. **In flight (8/15 merged).**

**Phase C** — "Observability." Tasks C1-C7 — expand KPIs to 55-65, add anomaly detection, confidence-based routing, differentiated SLA monitoring, per-trader Bayesian metrics. **Scoped, starts late May.**

**Phase D** — "Algo / Execution." Automated trading on top of the trusted data substrate. **Deferred.** Entry gated by GUARDIAN's Phase D Readiness Report showing all 7 Arbiter prerequisites GREEN for 2 consecutive months, then Mike signs off.

**PostgreSQL** — Target database replacing SQLite. B1 adds the abstraction layer, B2 ships the schema, B3 runs parallel-write verification for 7+ days, B4 cuts over.

**Redis Streams** — Target message substrate between the 8 decomposed services. 8 topics (ingestion.raw, notification.outbound, lifecycle.event, …). MAXLEN retention (approximate). B12 ships it.

**signal-gateway** — The single asyncio process (systemd-supervised) that captures Discord Gateway WebSocket + Telegram MTProto messages and routes them into the parse → gate → store pipeline.

**SQLite** — The current database (`oinkfarm.db`, WAL mode). Works fine today; being replaced because scale-up to 1,000 signals/day and the trace/event requirements exceed what SQLite comfortably supports.

**VIGIL 🔍** — OpenClaw agent that reviews every PR for code quality, spec compliance, test coverage, rollback safety, and data-integrity impact. Target score ≥9.5 on every dimension.

**W1 immutable** — "Wave 1" signal origin records — the raw ingested signal, INSERT-only, never updated. B9 adds the enforcement. Arbiter's phrasing: "Signal origin records are INSERT-only." Combined with W2 (lifecycle events), W3 (materialized views), W4 (full 18-timestamp trace) this becomes the trusted data substrate Phase C and Phase D depend on.

---

*[Event index](events/README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [Heavy Hybrid roadmap](../../forge-workspace/plans/HEAVY-HYBRID-ROADMAP.md)*
