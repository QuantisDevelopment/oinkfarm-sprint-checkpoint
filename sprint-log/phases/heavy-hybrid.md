# Heavy Hybrid Roadmap — Long-horizon Decisions

**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)

## Open Q-HH gates

| ID | Question | Age | Options |
|---|---|---|---|
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | 1.4h | maxlen · time_based |
| `Q-HH-3` | Docker Compose: single host or multi-host? | 1.4h | single · multi |
| `Q-HH-4` | W1 enforcement level: DB REVOKE UPDATE, or app-level guard? | 1.4h | db_revoke · app_guard |
| `Q-HH-5` | Confidence routing: hard reject or soft flag? | 1.4h | hard_reject · soft_flag |
| `Q-HH-6` | Phase D entry gate: who decides prerequisites are met? | 1.4h | mike_guardian_joint |

## Resolved Q-HH decisions

| When | ID | Answer |
|---|---|---|
| Apr 20, 13:15 CEST | `Q-HH-1` | Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-topology Docker Compose model ('8 services + PostgreSQL + Redis'). 256MB RAM allocation for Redis is trivial on barn. Redis MAXLEN retention (Q-HH-2) caps memory footprint. Trigger for re-evaluation: if Redis CPU >30% sustained or stream lag shows contention with PG writes. Risk: low — Redis is even easier to relocate than PG (stateless streams with AOF persistence; redis-cli --rdb dump). |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
