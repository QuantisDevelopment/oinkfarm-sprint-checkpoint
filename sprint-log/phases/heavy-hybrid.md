# Heavy Hybrid Roadmap — Long-horizon Decisions

## What is Heavy Hybrid?

> Heavy Hybrid is the long-horizon roadmap captured as Q-HH decisions — Redis placement, retention policy, container strategy, W1 enforcement, confidence routing, and Phase-D gating. Six decisions resolved, zero open.

**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)

## Open Q-HH gates

_No open Q-HH gates._

## Resolved Q-HH decisions

| When | ID | Answer |
|---|---|---|
| Apr 21, 17:39 CEST | `Q-HH-5` | SOFT-FLAG. Below-threshold confidence signals pass through the pipeline with a visual marker ('low-confidence' label) on the dashboard, NOT dropped. Rationale: (1) 'We see all the data, clearly labeled' philosophy — consistent with data-purity endgame; (2) reversibility — hard-reject loses historical context, we can't retroactively analyze signals we dropped; (3) user-side filterability — any operator (Mike, Dominik) can filter on the dashboard based on the label; (4) C5 anomaly detection depends on having full signal history including low-confidence ones to detect drift patterns. Implementation note for FORGE: the C2 plan should specify the label taxonomy (e.g., 'low-conf', 'medium-conf', 'high-conf' with explicit percentile thresholds) and ensure the DB schema carries the confidence score through to every downstream query, not just a boolean flag. |
| Apr 20, 22:54 CEST | `Q-HH-2` | Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at runtime. |
| Apr 20, 22:54 CEST | `Q-HH-3` | Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `Q-HH-4` | signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFORCE toggle in oink_db.py. |
| Apr 20, 22:54 CEST | `Q-HH-5` | Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |
| Apr 20, 13:32 CEST | `Q-HH-6` | GUARDIAN publishes monthly Phase D Readiness Report scoring each of Arbiter's 7 prerequisites with traffic-light + evidence citations. Mike signs off entry when all 7 are GREEN for 2 consecutive reports. CEO (Dominik) consult is optional, not required. FORGE does NOT plan Phase D tasks until gate passes. |
| Apr 20, 13:15 CEST | `Q-HH-1` | Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-topology Docker Compose model ('8 services + PostgreSQL + Redis'). 256MB RAM allocation for Redis is trivial on barn. Redis MAXLEN retention (Q-HH-2) caps memory footprint. Trigger for re-evaluation: if Redis CPU >30% sustained or stream lag shows contention with PG writes. Risk: low — Redis is even easier to relocate than PG (stateless streams with AOF persistence; redis-cli --rdb dump). |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
