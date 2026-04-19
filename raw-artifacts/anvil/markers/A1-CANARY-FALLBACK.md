# A1 Canary Fallback — Manual Verification Path

**Task:** A1 — signal_events Table Extension + Lifecycle Instrumentation
**Date:** 2026-04-19
**Purpose:** Backup verification when weekend / low-volume traffic delays natural event generation

## Primary Canary Goal

Within the first monitoring window after deploy, verify:

```sql
SELECT COUNT(*) FROM signal_events;
```

returns `> 0`, and at least two distinct `event_type` values appear during normal operation.

## Fallback Trigger

Use this fallback if low activity means natural signals are insufficient to satisfy the first-hour check.

## Manual Verification Paths

### Path A — micro-gate path (preferred)
Inject or replay a safe test payload through the normal micro-gate path in a controlled environment so that a known `SIGNAL_CREATED` event is emitted.

**Expected outcome:**
- one new signal row (in test/safe scope only)
- one corresponding `SIGNAL_CREATED` row in `signal_events`

### Path B — oink-sync path
Select a safe staging/test signal or controlled paper-style row and drive one deterministic lifecycle transition:
- TP hit → expect `TP_HIT` + `SL_MODIFIED`
- limit fill → expect `ORDER_FILLED`
- stale limit expiry → expect `LIMIT_EXPIRED`

**Expected outcome:**
- matching lifecycle mutation in `signals`
- corresponding append-only row(s) in `signal_events`

## Verification Queries

### Event count
```sql
SELECT COUNT(*) FROM signal_events;
```

### Distinct event types
```sql
SELECT event_type, COUNT(*)
FROM signal_events
GROUP BY event_type
ORDER BY COUNT(*) DESC, event_type;
```

### Latest events
```sql
SELECT id, signal_id, event_type, field, old_value, new_value, source, created_at
FROM signal_events
ORDER BY id DESC
LIMIT 20;
```

### Schema completeness
```sql
PRAGMA table_info(signal_events);
```

Expected columns:
- id
- signal_id
- event_type
- payload
- source
- created_at
- field
- old_value
- new_value
- source_msg_id

## Safety Notes

- Prefer controlled non-production or clearly reversible verification where possible
- Do not inject noisy or ambiguous live data solely to satisfy the counter
- If using a live-system fallback, choose the smallest reversible path and log exactly what was triggered

## Success Condition

Canary fallback succeeds when:
1. append-only events are written and queryable
2. source column is populated
3. field-change events include structured metadata where applicable
4. no signal mutation failure occurs if event logging is unavailable
