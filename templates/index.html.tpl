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
