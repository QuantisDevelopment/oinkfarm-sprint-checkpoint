# Sprint Checkpoint Dashboard

Static-site generator for the **OinkFarm Implementation Foresight Sprint** checkpoint.

Produces a self-contained dashboard (HTML + JSON + CSS + JS) for Mike (CEO)
and Dominik (co-founder) to see, at a glance:

- Wave progress (Wave 1 ✅, Wave 2 in-flight, Wave 3+ future)
- Per-task status, PRs, merge commits, VIGIL / GUARDIAN / Hermes verdicts, canary results
- A rolling narrative timeline pulled from the Hermes orchestrator's cron output
- Active blockers that need human attention
- Status of each agent (FORGE / ANVIL / VIGIL / GUARDIAN / Hermes / OinkV)
- Links to FORGE plans and OinkV audits

Everything is **crawled from live workspace state** — no hard-coded task data.
Re-running the generator (or the cron job that wraps it) reflects the latest state.

## Quick start

```bash
cd /home/oinkv/sprint-checkpoint
python3 generate.py
# → site/index.html, site/data.json, site/style.css, site/app.js
```

Open `site/index.html` in a browser, or serve it with any static host
(GitHub Pages, Netlify, `python3 -m http.server`, etc.).

## How it works

`generate.py` performs four independent crawls:

1. **Task crawl** (`crawl_task`) — for each of A1/A2/A3/A4/A5/A7 it scans:
   - `anvil-workspace/proposals/A{N}-*` for proposal + marker files
   - `anvil-workspace/A{N}-MERGED.marker` for merge commits + PR numbers
   - `vigil-workspace/reviews/A{N}-VIGIL-*` + `guardian-workspace/reviews/A{N}-GUARDIAN-*`
     (pulls weighted **Overall** score and verdict via tolerant regex)
   - `hermes-workspace/A{N}-HERMES-REVIEW.md` (LGTM / CONCERNS / BLOCK)
   - `guardian-workspace/canary-reports/A{N}-CANARY.md` (+ COMPLETE marker)
   - `forge-workspace/plans/TASK-A{N}-plan.md`

   Status is derived purely from which markers/files exist:

   | Signals present                                   | Status            |
   | -------------------------------------------------- | ----------------- |
   | `MERGED.marker` + canary PASS                     | `DONE`            |
   | `MERGED.marker`, canary missing / PENDING         | `CANARY`          |
   | `PHASE0-APPROVED.marker`, no `MERGED.marker`       | `CODE`            |
   | `READY-FOR-REVIEW.marker`, no approval            | `PROPOSAL_REVIEW` |
   | proposal file present, no ready marker            | `PROPOSAL`        |
   | FORGE plan only                                   | `PLANNED`         |

2. **Agent crawl** (`crawl_agent`) — for each agent workspace we take the newest
   file mtime and derive a status light (green <30min, yellow <3h, red ≥3h).
   If there's a `HEARTBEAT.md`, we parse `current_task`, `current_phase`,
   `blockers`, and `branch` out of the first fenced JSON-ish block.

3. **Cron narrative** (`crawl_cron`) — iterates
   `/home/oinkv/.hermes/cron/output/c5fe3ace64fd/*.md` newest-first, skips
   any cycle whose body is just `[SILENT]`, and extracts "Actions taken" /
   "Next auto-action" / "Blocker" from the orchestrator's own output block.

4. **Plans crawl** — lists `TASK-A*-plan.md` and `OINKV-AUDIT*.md` under
   `forge-workspace/plans/` with title + size + mtime.

Results are merged into one dict, serialized as `site/data.json`, and
rendered into `site/index.html` via `templates/index.html.tpl` (Jinja2).

## Files

```
sprint-checkpoint/
├── generate.py               # the crawler + renderer (single entry point)
├── templates/
│   └── index.html.tpl        # Jinja2 template
├── static/
│   ├── style.css             # dark theme + warm-orange accent
│   └── app.js                # clock, tab switcher, auto-refresh
├── site/                     # generated output (gitignore candidate)
│   ├── index.html
│   ├── data.json
│   ├── style.css
│   └── app.js
└── README.md
```

## Design notes

- **Dark theme**, `#0b0f15` background, warm orange `#ff6b35` accent.
- **Inter** for body, **JetBrains Mono** for IDs / hashes / timestamps — both
  loaded from Google Fonts CDN.
- **Mobile-first**: waves and task grid collapse to single column below 900px.
- **Progressive enhancement**: every panel, badge, and timeline works with JS
  disabled. The JS layer only adds:
  - ticking UTC / CEST clock
  - auto-refresh of `data.json` every 60s (page reloads on new data)
  - tab switching for Narrative / Plans / OinkV Audits
  - `localStorage`-backed open/closed state for each task timeline
- **Fault tolerance**: all file reads are guarded; missing artifacts are
  rendered as "—" or omitted — no crashes if an agent is slow or offline.
- **Read-only** outside `site/`. The generator never mutates any agent workspace.

## Re-generation cadence

Intended to be wrapped in a cron job (handled separately by Hermes) that runs
`python3 generate.py` every few minutes and pushes `site/` to the target
(e.g., GitHub Pages). The static page itself auto-refreshes `data.json` every
60s and triggers a soft reload when the underlying data timestamp changes.

## Dependencies

- Python 3.9+
- `jinja2` (pre-installed on the host)

No other runtime dependencies. No Node, no Docker, no server.
