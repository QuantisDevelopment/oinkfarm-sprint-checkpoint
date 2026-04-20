# Heavy Hybrid Roadmap — Long-horizon Decisions

**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)

## Open Q-HH gates

| ID | Question | Age | Options |
|---|---|---|---|
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | 1.4h | maxlen · time_based |
| `Q-HH-6` | Phase D entry gate: who decides prerequisites are met? | 1.4h | mike_guardian_joint |
| `Q-HH-3` | Single-host Docker Compose for B13, defer multi-host to Phase D+? | 0m | single-host only · include multi-host preparation |
| `Q-HH-4` | Enforce W1 immutability via phased app-level then DB REVOKE? | 0m | phased app-level then DB REVOKE · immediate DB-level REVOKE |
| `Q-HH-5` | Route low-confidence signals to PROVISIONAL state or hard-reject? | 0m | PROVISIONAL soft-flag · hard reject |

## Resolved Q-HH decisions

| When | ID | Answer |
|---|---|---|
| Apr 20, 13:15 CEST | `Q-HH-1` | Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-topology Docker Compose model ('8 services + PostgreSQL + Redis'). 256MB RAM allocation for Redis is trivial on barn. Redis MAXLEN retention (Q-HH-2) caps memory footprint. Trigger for re-evaluation: if Redis CPU >30% sustained or stream lag shows contention with PG writes. Risk: low — Redis is even easier to relocate than PG (stateless streams with AOF persistence; redis-cli --rdb dump). |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
