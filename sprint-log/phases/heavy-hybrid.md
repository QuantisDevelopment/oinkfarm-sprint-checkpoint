# Heavy Hybrid Roadmap — Long-horizon Decisions

## What is Heavy Hybrid?

> Heavy Hybrid is the long-horizon roadmap captured as Q-HH decisions — Redis placement, retention policy, container strategy, W1 enforcement, confidence routing, and Phase-D gating. Six decisions resolved, zero open.

**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)

## Open Q-HH gates

| ID | Question | Age | Options |
|---|---|---|---|
| `Q-HH-2` | Redis Streams retention policy: MAXLEN or time-based? | 2.7h | maxlen · time_based |
| `Q-HH-3` | Single-host Docker Compose for B13, defer multi-host to Phase D+? | 1.2h | single-host only · include multi-host preparation |
| `Q-HH-4` | Enforce W1 immutability via phased app-level then DB REVOKE? | 1.2h | phased app-level then DB REVOKE · immediate DB-level REVOKE |
| `Q-HH-5` | Route low-confidence signals to PROVISIONAL state or hard-reject? | 1.2h | PROVISIONAL soft-flag · hard reject |

## Resolved Q-HH decisions

| When | ID | Answer |
|---|---|---|
| Apr 20, 13:32 CEST | `Q-HH-6` | GUARDIAN publishes monthly Phase D Readiness Report scoring each of Arbiter's 7 prerequisites with traffic-light + evidence citations. Mike signs off entry when all 7 are GREEN for 2 consecutive reports. CEO (Dominik) consult is optional, not required. FORGE does NOT plan Phase D tasks until gate passes. |
| Apr 20, 13:15 CEST | `Q-HH-1` | Same server (barn) as Docker container, 127.0.0.1 binding, internal-only port exposure. Matches Arbiter V3 PHASE-4 §2 single-topology Docker Compose model ('8 services + PostgreSQL + Redis'). 256MB RAM allocation for Redis is trivial on barn. Redis MAXLEN retention (Q-HH-2) caps memory footprint. Trigger for re-evaluation: if Redis CPU >30% sustained or stream lag shows contention with PG writes. Risk: low — Redis is even easier to relocate than PG (stateless streams with AOF persistence; redis-cli --rdb dump). |

---

*[Sprint log index](../README.md) · [Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*
