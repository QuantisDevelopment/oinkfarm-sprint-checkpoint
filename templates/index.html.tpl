<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ sprint_title }}</title>
<meta name="description" content="Live checkpoint dashboard for the OinkFarm Implementation Foresight Sprint.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body data-generated="{{ generated_at_utc }}">

<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark">🔥</div>
      <div>
        <h1>{{ sprint_title }}</h1>
        <p class="subtitle">{{ sprint_subtitle }}</p>
      </div>
    </div>
    <div class="clock">
      <div class="clock-row">
        <span class="clock-label">UTC</span>
        <span class="mono" id="clock-utc">{{ generated_at_utc }}</span>
      </div>
      <div class="clock-row">
        <span class="clock-label">CEST</span>
        <span class="mono" id="clock-cest">{{ generated_at_cest }}</span>
      </div>
      <div class="clock-row muted">
        <span class="clock-label">last regen</span>
        <span class="mono" id="last-regen">{{ generated_at_utc | tstime }}</span>
        <span class="refresh-pill" id="refresh-pill" title="auto-refreshes every 60s">
          <span class="dot dot-green"></span> auto
        </span>
      </div>
    </div>
  </div>
  <nav class="topnav" role="navigation" aria-label="Primary">
    <div class="topnav-inner">
      <a class="navlink navlink-active" href="#dashboard" data-nav="dashboard">Dashboard</a>
      <a class="navlink" href="#events" data-nav="events">Events <span class="nav-count mono">{{ recent_events|length }}</span></a>
      <a class="navlink" href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint/tree/main/sprint-log/phases" target="_blank" rel="noopener">Phases</a>
      <a class="navlink" href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint/tree/main/sprint-log/tasks" target="_blank" rel="noopener">Tasks <span class="nav-count mono">{{ tasks|length }}</span></a>
      <a class="navlink navlink-ghost" href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint" target="_blank" rel="noopener">GitHub ↗</a>
    </div>
  </nav>
</header>

<main class="container">

<!-- Bootstrapping banner --------------------------------------------------- -->
{% if bootstrap %}
<div class="bootstrap-banner" style="background:#4a2800;border:2px solid #e07b00;color:#fff0d6;padding:14px 18px;margin-bottom:18px;border-radius:8px;font-weight:500;">
  ⚠️ <strong>BOOTSTRAPPING FROM CRAWLER</strong> — event stream not yet populated
  ({{ events_integrity.total }} events in <code>{{ events_integrity.events_file }}</code>).
  Dashboard data sourced from workspace file mtimes as a fallback. As agents
  emit events into <code>events.jsonl</code>, this banner will disappear.
</div>
{% endif %}

<!-- Events integrity ------------------------------------------------------- -->
<section class="events-integrity" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px 16px;margin-bottom:16px;">
  <div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;font-size:0.9rem;">
    <div><span class="muted">📊 events:</span> <strong class="mono">{{ events_integrity.total }}</strong></div>
    <div><span class="muted">24h rate:</span> <strong class="mono">{{ events_integrity.rate_per_hour }}/h</strong></div>
    <div><span class="muted">last 24h:</span> <strong class="mono">{{ events_integrity.last_24h }}</strong></div>
    <div><span class="muted">schema:</span> <strong class="mono">v{{ events_integrity.schema_version }}</strong></div>
    <div><span class="muted">source:</span> <strong class="mono">{{ events_integrity.source }}</strong></div>
    <div>
      <span class="muted">monotonic:</span>
      {% if events_integrity.monotonic_ok %}
        <strong style="color:#4ade80;">✓ ok</strong>
      {% else %}
        <strong style="color:#f87171;">⚠ {{ events_integrity.monotonic_gaps|length }} gap(s)</strong>
      {% endif %}
    </div>
  </div>
  {% if events_integrity.human_line %}
  <div class="integrity-human" style="margin-top:6px;font-size:0.85rem;color:#c6d0e0;">
    {{ events_integrity.human_line }}
  </div>
  {% endif %}
</section>

<!-- ★★★ HUMAN NARRATIVE BLOCK — leads the dashboard for Mike/Dominik ★★★ ---- -->
{% if narrative %}
<section class="human-narrative" id="human-narrative"
         style="background:linear-gradient(180deg,rgba(30,42,70,0.55),rgba(20,26,42,0.35));border:1px solid rgba(138,180,255,0.25);border-radius:10px;padding:18px 22px;margin-bottom:24px;">
  <div class="narrative-topbar" style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;margin-bottom:14px;font-size:0.85rem;">
    <span class="muted">📖 Plain-English sprint narrative</span>
    <a href="{{ narrative.sos_link }}" style="color:#8ab4ff;text-decoration:none;">
      Read the full State of the Sprint →
    </a>
    <a href="oinxtractor-quality.html" style="color:#8ab4ff;text-decoration:none;">
      OinXtractor Quality →
    </a>
    <a href="{{ narrative.glossary_link }}" class="muted" style="color:#9bb3d4;text-decoration:none;">
      Glossary
    </a>
    {% if not narrative.sos_exists %}
      <span class="muted" style="font-size:0.8rem;color:#e0a868;">
        (State of Sprint doc being built by Scribe — link will go live on next regen)
      </span>
    {% endif %}
  </div>
  <div class="narrative-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;">
    <div class="narrative-cell">
      <h3 style="margin:0 0 8px 0;font-size:1.0rem;">📖 The Mission</h3>
      <div style="margin:0;font-size:0.92rem;line-height:1.55;color:#dce5f2;">{% for para in narrative.mission.split('\n\n') if para.strip() %}<p style="margin:0 0 10px 0;">{{ para.strip() }}</p>{% endfor %}</div>
    </div>
    <div class="narrative-cell">
      <h3 style="margin:0 0 8px 0;font-size:1.0rem;">📍 Today in one paragraph</h3>
      <div style="margin:0;font-size:0.92rem;line-height:1.55;color:#dce5f2;">{% for para in narrative.today.split('\n\n') if para.strip() %}<p style="margin:0 0 10px 0;">{{ para.strip() }}</p>{% endfor %}</div>
    </div>
    <div class="narrative-cell">
      <h3 style="margin:0 0 8px 0;font-size:1.0rem;">📅 What happened this week</h3>
      <div style="margin:0;font-size:0.92rem;line-height:1.55;color:#dce5f2;">{% for para in narrative.week.split('\n\n') if para.strip() %}<p style="margin:0 0 10px 0;">{{ para.strip() }}</p>{% endfor %}</div>
    </div>
    <div class="narrative-cell">
      <h3 style="margin:0 0 8px 0;font-size:1.0rem;">🎯 What's next</h3>
      <div style="margin:0;font-size:0.92rem;line-height:1.55;color:#dce5f2;">{% for para in narrative.whats_next.split('\n\n') if para.strip() %}<p style="margin:0 0 10px 0;">{{ para.strip() }}</p>{% endfor %}</div>
    </div>
  </div>
</section>
{% endif %}

{% if scribe_log %}
<section class="scribe-log" id="scribe-log" style="margin-bottom:28px;padding:18px 18px;background:linear-gradient(135deg,rgba(138,180,255,0.06),rgba(138,180,255,0.02));border-radius:10px;border:1px solid rgba(138,180,255,0.12);">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
    <h2 style="margin:0;font-size:1.1rem;">🪽 Scribe log — last 24 hours</h2>
    <span class="muted mono" style="font-size:0.8rem;">{{ scribe_log|length }} narrative entries · newest first</span>
  </div>
  <div style="display:flex;flex-direction:column;gap:14px;max-height:720px;overflow-y:auto;padding-right:6px;">
  {% for entry in scribe_log %}
    <details {% if loop.index <= 3 %}open{% endif %} style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px 14px;">
      <summary style="cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;">
        <span style="font-weight:600;color:#e0e8f5;">{{ entry.ts_date_local }} · {{ entry.ts_local_hm }}</span>
        <span class="muted mono" style="font-size:0.78rem;">{{ entry.ts_utc_hm }}</span>
      </summary>
      <div style="margin-top:10px;font-size:0.9rem;line-height:1.55;color:#dce5f2;">
      {% for para in entry.paragraphs %}<p style="margin:0 0 10px 0;">{{ para }}</p>{% endfor %}
      </div>
    </details>
  {% endfor %}
  </div>
</section>
{% endif %}

<!-- ★ MIKE SPEC — 4 top-level sections ★ ----------------------------------- -->

<!-- 1. LIVE NOW ............................................................ -->
<section class="live-now" id="live-now" style="margin-bottom:24px;">
  <div class="section-head"><h2>🔴 Live now</h2><span class="muted mono">event stream</span></div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px;">
    {% for bucket_name, label in [('1h','Last 1 hour'), ('4h','Last 4 hours'), ('24h','Last 24 hours')] %}
    <div class="live-bucket" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <strong>{{ label }}</strong>
        <span class="mono muted">{{ live_buckets[bucket_name]|length }} events</span>
      </div>
      {% if live_buckets[bucket_name] %}
        <ol style="list-style:none;padding:0;margin:0;max-height:260px;overflow-y:auto;">
          {% for e in live_buckets[bucket_name][:25] %}
          <li style="padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.85rem;line-height:1.4;">
            <div>
              <span class="mono muted">{{ e.ts | tstime }}</span>
              <span class="mono" style="color:#8ab4ff;">{{ e.event_type }}</span>
              {% if e.task_id %}<span class="mono">{{ e.task_id }}</span>{% endif %}
              <span class="muted mono">· {{ e.agent or '—' }}</span>
            </div>
            <div class="muted" style="font-size:0.8rem;margin-top:2px;">{{ e.summary }}</div>
          </li>
          {% endfor %}
        </ol>
      {% else %}
        <p class="muted" style="font-size:0.85rem;">No events in this window.</p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</section>

<!-- 2. NEEDS MIKE .......................................................... -->
<section class="needs-mike" id="needs-mike" style="margin-bottom:24px;">
  <div class="section-head"><h2>🧭 Needs Mike</h2><span class="muted mono">{{ open_decisions|length }} open</span></div>
  {% if open_decisions %}
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
      <thead>
        <tr style="background:rgba(255,255,255,0.05);">
          <th style="padding:8px;text-align:left;">Question ID</th>
          <th style="padding:8px;text-align:left;">Question</th>
          <th style="padding:8px;text-align:left;">Task</th>
          <th style="padding:8px;text-align:left;">Age</th>
          <th style="padding:8px;text-align:left;">Options</th>
          <th style="padding:8px;text-align:left;">Gate</th>
        </tr>
      </thead>
      <tbody>
        {% for d in open_decisions %}
        <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
          <td class="mono" style="padding:8px;font-weight:600;color:#f0a868;">{{ d.question_id }}</td>
          <td style="padding:8px;">{{ d.question }}</td>
          <td class="mono" style="padding:8px;">{{ d.task_id or '—' }}</td>
          <td class="mono" style="padding:8px;">{{ d.age_human }}</td>
          <td class="muted mono" style="padding:8px;font-size:0.8rem;">
            {% if d.options %}{{ d.options | join(' · ') }}{% else %}—{% endif %}
          </td>
          <td class="mono" style="padding:8px;font-size:0.75rem;">{{ d.gate_type }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="muted">No open DECISION_NEEDED events. Team is unblocked.</p>
  {% endif %}
</section>

<!-- 3. MISSING EVIDENCE .................................................... -->
<section class="missing-evidence" id="missing-evidence" style="margin-bottom:24px;">
  <div class="section-head"><h2>🔍 Missing evidence</h2><span class="muted mono">{{ lint_gaps|length }} gaps</span></div>
  {% if lint_gaps %}
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
      <thead>
        <tr style="background:rgba(255,255,255,0.05);">
          <th style="padding:8px;text-align:left;">Severity</th>
          <th style="padding:8px;text-align:left;">Task</th>
          <th style="padding:8px;text-align:left;">Issue</th>
        </tr>
      </thead>
      <tbody>
        {% for g in lint_gaps %}
        <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
          <td style="padding:8px;">
            {% if g.severity == 'critical' %}<span style="background:#7f1d1d;color:#fecaca;padding:2px 8px;border-radius:4px;">CRITICAL</span>
            {% elif g.severity == 'warn' %}<span style="background:#92400e;color:#fed7aa;padding:2px 8px;border-radius:4px;">WARN</span>
            {% elif g.severity == 'mike' %}<span style="background:#1e3a8a;color:#bfdbfe;padding:2px 8px;border-radius:4px;">MIKE</span>
            {% else %}<span style="background:#374151;color:#d1d5db;padding:2px 8px;border-radius:4px;">INFO</span>{% endif %}
          </td>
          <td class="mono" style="padding:8px;">{{ g.task_id or '—' }}</td>
          <td style="padding:8px;">{{ g.issue }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="muted">✓ No lint gaps — stream is internally consistent.</p>
  {% endif %}
</section>

<!-- 4. FRESHNESS BY AGENT .................................................. -->
<section class="freshness" id="freshness" style="margin-bottom:24px;">
  <div class="section-head"><h2>🫀 Freshness by agent</h2><span class="muted mono">last emitted event</span></div>
  <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
    <thead>
      <tr style="background:rgba(255,255,255,0.05);">
        <th style="padding:8px;text-align:left;">Agent</th>
        <th style="padding:8px;text-align:left;">Last event</th>
        <th style="padding:8px;text-align:left;">Type</th>
        <th style="padding:8px;text-align:left;">Task</th>
        <th style="padding:8px;text-align:left;">Staleness</th>
        <th style="padding:8px;text-align:left;">Events</th>
      </tr>
    </thead>
    <tbody>
      {% for a in freshness_by_agent %}
      <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
        <td style="padding:8px;">
          <span>{{ a.emoji or '•' }}</span>
          <strong>{{ a.name }}</strong>
          <span class="muted mono" style="font-size:0.75rem;">{{ a.role }}</span>
        </td>
        <td class="mono muted" style="padding:8px;">{{ a.last_event_ts | tstime }}</td>
        <td class="mono" style="padding:8px;color:#8ab4ff;">{{ a.last_event_type or '—' }}</td>
        <td class="mono" style="padding:8px;">{{ a.current_task or a.last_task_id or '—' }}</td>
        <td style="padding:8px;">
          {% if a.light == 'green' %}<span style="background:#14532d;color:#bbf7d0;padding:2px 8px;border-radius:4px;">● fresh</span>
          {% elif a.light == 'yellow' %}<span style="background:#713f12;color:#fde68a;padding:2px 8px;border-radius:4px;">● 1–3h</span>
          {% else %}<span style="background:#7f1d1d;color:#fecaca;padding:2px 8px;border-radius:4px;">● stale</span>{% endif %}
        </td>
        <td class="mono muted" style="padding:8px;">{{ a.event_count }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</section>

<!-- END Mike spec 4-section layout ----------------------------------------- -->


<!-- Wave progress ---------------------------------------------------------- -->
<section class="waves">
  {% for wave in waves %}
  <div class="wave {% if wave.future %}wave-future{% endif %}">
    <div class="wave-header">
      <h3>{{ wave.name }}</h3>
      <span class="wave-count mono">
        {% if wave.future %}future{% else %}{{ wave.done }}/{{ wave.total }}{% endif %}
      </span>
    </div>
    <div class="wave-bar">
      <div class="wave-fill" style="width: {{ wave.percent }}%;"></div>
    </div>
    <div class="wave-chips">
      {% for tid in wave.task_ids %}
        {% set ns = namespace(match=None) %}
        {% for task in wave.tasks %}
          {% if task.id == tid %}{% set ns.match = task %}{% endif %}
        {% endfor %}
        {% if ns.match %}
          <a href="#task-{{ ns.match.id }}" class="chip chip-{{ ns.match.status|lower }}" title="{{ ns.match.status_label }}">
            {{ ns.match.tier_emoji }} <span class="mono">{{ ns.match.id }}</span>
          </a>
        {% else %}
          <span class="chip chip-not_started mono">{{ tid }}</span>
        {% endif %}
      {% endfor %}
      {% if wave.future %}<span class="chip chip-future mono">A6 · A8–A11 · A2.*</span>{% endif %}
    </div>
  </div>
  {% endfor %}
</section>

<!-- Recent events --------------------------------------------------------- -->
{% if recent_events %}
<section class="recent-events" id="events">
  <div class="section-head">
    <h2>Recent events</h2>
    <a class="mono muted section-more" href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint/tree/main/sprint-log/events" target="_blank" rel="noopener">full log ↗</a>
  </div>
  <ol class="events-feed">
    {% for e in recent_events[:8] %}
    <li class="event-row event-{{ e.type|lower }}">
      <span class="event-emoji" title="{{ e.type }}">{{ e.emoji }}</span>
      <span class="event-time mono muted">{{ e.ts | tstime }}</span>
      <span class="event-task mono">{{ e.task }}</span>
      <span class="event-type mono">{{ e.type }}</span>
      <span class="event-desc">{{ e.desc }}</span>
    </li>
    {% endfor %}
  </ol>
</section>
{% endif %}

<!-- Blockers --------------------------------------------------------------- -->
<section class="blockers">
  {% if blockers %}
    <div class="blockers-card severity-{{ 'mike' if blockers[0].severity == 'mike' else 'auto' }}">
      <div class="blockers-head">
        <span class="warn-icon">!</span>
        <h2>Active blockers</h2>
        <span class="blocker-count">{{ blockers|length }}</span>
      </div>
      <ul class="blocker-list">
        {% for b in blockers %}
        <li>
          <span class="blocker-agent">{{ b.agent_emoji }} {{ b.agent }}</span>
          <span class="blocker-label">{{ b.label }}</span>
          {% if b.current_task %}
            <span class="blocker-task mono">on {{ b.current_task }}{% if b.current_phase %} · {{ b.current_phase }}{% endif %}</span>
          {% endif %}
        </li>
        {% endfor %}
      </ul>
    </div>
  {% else %}
    <div class="blockers-card severity-none">
      <div class="blockers-head">
        <span class="ok-icon">✓</span>
        <h2>No human-gated blockers</h2>
      </div>
      <p class="muted">Team is progressing autonomously. Next checkpoint will update automatically.</p>
    </div>
  {% endif %}
</section>

<!-- Tasks ------------------------------------------------------------------ -->
<section class="tasks-section">
  <div class="section-head">
    <h2>Tasks</h2>
    <span class="muted mono">most recent first</span>
  </div>
  <div class="tasks-grid">
    {% for t in tasks %}
    <article class="task task-{{ t.status|lower }}" id="task-{{ t.id }}">
      <header class="task-head">
        <div class="task-id-row">
          <span class="tier-emoji" title="{{ t.tier }}">{{ t.tier_emoji }}</span>
          <span class="task-id mono">{{ t.id }}</span>
          <span class="badge badge-{{ t.status|lower }}">{{ t.status_label }}</span>
        </div>
        <div class="task-meta mono muted">
          {% if t.last_activity %}
            {{ t.last_activity | tstime }}
          {% else %}
            no activity
          {% endif %}
        </div>
      </header>

      <div class="task-body">
        <div class="task-stats">
          {% if t.scores.vigil is not none %}
            <div class="stat"><span class="stat-label">VIGIL</span><span class="stat-value mono">{{ '%.2f' | format(t.scores.vigil) }}</span></div>
          {% endif %}
          {% if t.scores.guardian is not none %}
            <div class="stat"><span class="stat-label">GUARDIAN</span><span class="stat-value mono">{{ '%.2f' | format(t.scores.guardian) }}</span></div>
          {% endif %}
          {% if t.verdicts.hermes %}
            <div class="stat"><span class="stat-label">Hermes</span><span class="stat-value verdict-{{ t.verdicts.hermes|lower }}">{{ t.verdicts.hermes }}</span></div>
          {% endif %}
          {% if t.canary.verdict %}
            <div class="stat"><span class="stat-label">Canary</span><span class="stat-value verdict-{{ t.canary.verdict|lower }}">{{ t.canary.verdict }}</span></div>
          {% endif %}
        </div>

        {% if t.prs %}
          <div class="task-prs">
            {% for pr in t.prs %}
              <a class="pr-link" href="{{ pr.pr_url }}" target="_blank" rel="noopener">
                <span class="pr-repo mono">{{ pr.repo }}</span>
                <span class="pr-num mono">#{{ pr.number }}</span>
              </a>
              {% if pr.merge_commit %}
                <a class="commit-link mono" href="{{ pr.commit_url }}" target="_blank" rel="noopener" title="merge commit">
                  {{ pr.merge_commit[:7] }}
                </a>
              {% endif %}
            {% endfor %}
          </div>
        {% elif t.repo_hint %}
          <div class="task-prs muted mono">target: {{ t.repo_hint }}</div>
        {% endif %}
      </div>

      <details class="task-timeline">
        <summary>Timeline <span class="muted mono">({{ t.timeline|length }} events)</span></summary>
        {% if t.timeline %}
          <ol class="timeline">
            {% for e in t.timeline|reverse %}
            <li class="timeline-event">
              <span class="dot dot-{{ (e.verdict or 'info')|lower }}"></span>
              <div class="timeline-body">
                <div class="timeline-label">
                  <span class="timeline-actor mono">{{ e.actor }}</span>
                  <span>{{ e.label }}</span>
                </div>
                <div class="timeline-meta mono muted">
                  {{ e.mtime | tstime }}
                  {% if e.path %}
                    · <span class="filepath">{{ e.path.split('/')[-1] }}</span>
                  {% endif %}
                </div>
              </div>
            </li>
            {% endfor %}
          </ol>
        {% else %}
          <p class="muted">No recorded events yet.</p>
        {% endif %}
      </details>
    </article>
    {% endfor %}
  </div>
</section>

<!-- Agents + Narrative tabs ------------------------------------------------ -->
<section class="two-col">

  <!-- Agents ............................................................. -->
  <div class="panel">
    <div class="panel-head">
      <h2>Agents</h2>
      <span class="muted mono">heartbeat mtime</span>
    </div>
    <div class="agent-list">
      {% for a in agents %}
      <div class="agent agent-light-{{ a.light }}">
        <div class="agent-top">
          <span class="agent-emoji">{{ a.emoji }}</span>
          <span class="agent-name">{{ a.name }}</span>
          <span class="agent-light light-{{ a.light }}" title="{{ a.light }}"></span>
        </div>
        <div class="agent-meta muted">{{ a.role }}</div>
        <div class="agent-meta mono">
          {% if a.heartbeat.current_task %}
            task: {{ a.heartbeat.current_task }}
          {% elif a.id == 'oinkv' %}
            last audit
          {% else %}
            idle
          {% endif %}
          {% if a.heartbeat.current_phase %} · {{ a.heartbeat.current_phase }}{% endif %}
        </div>
        <div class="agent-meta mono muted">{{ a.last_active_human }}</div>
        {% if a.heartbeat.branch %}
          <div class="agent-meta mono muted">branch: {{ a.heartbeat.branch }}</div>
        {% endif %}
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Narrative timeline ................................................. -->
  <div class="panel">
    <div class="panel-head tabs">
      <div class="tab-row" role="tablist">
        <button class="tab tab-active" data-tab="narrative" role="tab">Narrative</button>
        <button class="tab" data-tab="plans" role="tab">Plans</button>
        <button class="tab" data-tab="audits" role="tab">OinkV Audits</button>
      </div>
    </div>

    <div class="tab-panel tab-panel-active" id="tab-narrative">
      <ol class="narrative">
        {% for entry in cron %}
        <li class="narrative-entry">
          <div class="narrative-time mono muted">{{ entry.time_utc | tstime }}</div>
          {% if entry.header %}
            <div class="narrative-header">{{ entry.header }}</div>
          {% endif %}
          {% if entry.actions %}
            <ul class="narrative-actions">
              {% for a in entry.actions %}<li>{{ a }}</li>{% endfor %}
            </ul>
          {% endif %}
          {% if entry.next %}
            <div class="narrative-next"><span class="pill pill-info">next</span> {{ entry.next }}</div>
          {% endif %}
          {% if entry.blocker %}
            <div class="narrative-blocker"><span class="pill pill-warn">blocker</span> {{ entry.blocker }}</div>
          {% endif %}
        </li>
        {% else %}
        <li class="muted">No orchestrator activity recorded yet.</li>
        {% endfor %}
      </ol>
    </div>

    <div class="tab-panel" id="tab-plans">
      <ul class="file-list">
        {% for p in plans %}
        <li>
          <span class="mono file-name">{{ p.name }}</span>
          <span class="file-title">{{ p.title }}</span>
          <span class="mono muted file-size">{{ (p.size_bytes / 1024)|round(1) }} KB</span>
          <span class="mono muted file-mtime">{{ p.mtime | tstime }}</span>
        </li>
        {% else %}
        <li class="muted">No FORGE plans discovered.</li>
        {% endfor %}
      </ul>
    </div>

    <div class="tab-panel" id="tab-audits">
      <ul class="file-list">
        {% for p in audits %}
        <li>
          <span class="mono file-name">{{ p.name }}</span>
          <span class="file-title">{{ p.title }}</span>
          <span class="mono muted file-size">{{ (p.size_bytes / 1024)|round(1) }} KB</span>
          <span class="mono muted file-mtime">{{ p.mtime | tstime }}</span>
        </li>
        {% else %}
        <li class="muted">No audits yet.</li>
        {% endfor %}
      </ul>
    </div>
  </div>
</section>

</main>

<footer class="footer">
  <div class="footer-inner mono muted">
    <div>
      {% if commit %}checkpoint@<span class="mono">{{ commit }}</span>{% else %}checkpoint@—{% endif %}
    </div>
    <div>
      {% if last_cron %}
        Last orchestrator cycle: {{ last_cron.time_utc | tstime }}
      {% else %}
        No orchestrator data
      {% endif %}
    </div>
    <div>
      generated {{ generated_at_utc | tstime }}
    </div>
  </div>
</footer>

<script src="app.js"></script>
</body>
</html>
