# Heavy Hybrid Roadmap — Long-horizon Decisions

## What is Heavy Hybrid?

> Heavy Hybrid is the long-horizon roadmap captured as Q-HH decisions — Redis placement, retention policy, container strategy, W1 enforcement, confidence routing, and Phase-D gating. Six decisions resolved, zero open.

**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)

## Open Q-HH gates

| ID | Question | Age | Options |
|---|---|---|---|
| `Q-HH-5` | For signals below the configured confidence threshold, should the system hard_reject them from the live lifecycle, or soft_flag_provisional them into a review queue? | 8m | hard_reject · soft_flag_provisional |

## Resolved Q-HH decisions

| When | ID | Answer |
|---|---|---|
| Apr 20, 22:54 CEST | `Q-HH-2` | Approximate MAXLEN retention per-topic. ingestion.raw ~10000, notification.outbound ~5000, lifecycle.event ~10000. Tunable at runtime. |
| Apr 20, 22:54 CEST | `Q-HH-3` | Single-host Docker Compose for B13. No multi-host preparation. Multi-host is Phase D+ scope. |
| Apr 20, 22:54 CEST | `Q-HH-4` | signal_events: DB-level REVOKE day 1. signals table: application-level guard first, DB REVOKE after 30 days clean. WARNING→ENFORCE toggle in oink_db.py. |
| Apr 20, 22:54 CEST | `Q-HH-5` | Soft flag via PROVISIONAL lifecycle state. Zero data loss. Confidence threshold is a C2 tuning parameter, not hard-coded. |
| Apr 20, 13:32 CEST | `Q-HH-6` | GUARDIAN publishes monthly Phase D Readiness Report scoring each of Arbiter's 7 prerequisites with traffic-light + evidence citations. Mike signs off entry when all 7 are GREEN for 2 consecutive reports. CEO (Dominik) consult is optional, not required. FORGE does NOT plan Phase D tasks until gate passes. |
| Apr 20, 13:15 CEST | `Q-HH-1` | Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-topology Docker Compose model ('8 services + PostgreSQL + Redis'). 256MB RAM allocation for Redis is trivial on barn. Redis MAXLEN retention (Q-HH-2) caps memory footprint. Trigger for re-evaluation: if Redis CPU >30% sustained or stream lag shows contention with PG writes. Risk: low — Redis is even easier to relocate than PG (stateless streams with AOF persistence; redis-cli --rdb dump). |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
