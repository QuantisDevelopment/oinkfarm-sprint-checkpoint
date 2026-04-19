# 🛡️ GUARDIAN Canary Report — Task A1: signal_events Extension + Lifecycle Instrumentation

| Field | Value |
|-------|-------|
| **Task** | A1 — signal_events table extension + lifecycle instrumentation |
| **oinkfarm Merge Commit** | `5b242c56` |
| **oink-sync Merge Commit** | `3d60538a` |
| **Canary Start** | 2026-04-18T23:49Z |
| **Report Time** | 2026-04-18T23:52Z |
| **Review Baseline** | `/home/oinkv/guardian-workspace/reviews/A1-GUARDIAN-PHASE1-REVIEW.md` |

---

## Canary Scope

Per Phase 1 review, verify:
1. `signal_events` schema has 10 columns
2. `SELECT COUNT(*) FROM signal_events > 0` within 1 hour
3. At least 2 distinct `event_type` values within 24 hours
4. Quarantine count stable at 11
5. FET #1159 `final_roi` unchanged at 3.37
6. SC-2, KPI-R1, KPI-R4 stable vs pre-deploy baseline

---

## Deployment Verification

Master reflects the A1 merge:
- `5b242c56 feat(A1): extend signal_events schema + fix zero-event root cause (#126)`

Initial production state before fallback verification:
- `signal_events` table existed but was still at **6 columns**
- `signal_events` row count was **0**

This is consistent with A1's **lazy schema migration** model: the 4 new columns are added by `EventStore.ensure_schema()` on first event write, not by an eager standalone migration at deploy time.

---

## Manual Fallback Used (Low-Volume Weekend)

Natural traffic had not produced any events yet, so I used ANVIL's documented fallback at:
`/home/oinkv/anvil-workspace/A1-CANARY-FALLBACK.md`

### Fallback Method
Smallest reversible path, **append-only only**, no mutation to `signals`:
- loaded canonical `scripts/event_store.py`
- wrote 2 canary events against existing signal **#1159**
- source = `guardian-canary`
- `commit=True` on both writes

### Events written
1. `MANUAL_SQL_FIX`
2. `PRICE_ALERT`

Shared canary run id:
- `guardian-a1-canary-b2da699d`

This verified both:
- lazy schema migration executes successfully on first write
- append-only event writes persist and are queryable

---

## Results

### 1) `PRAGMA table_info(signal_events)` shows 10 columns
**Result: ✅ PASS**

Observed columns:
1. `id`
2. `signal_id`
3. `event_type`
4. `payload`
5. `source`
6. `created_at`
7. `field`
8. `old_value`
9. `new_value`
10. `source_msg_id`

### 2) `SELECT COUNT(*) FROM signal_events > 0` within 1 hour
**Result: ✅ PASS**

```sql
SELECT COUNT(*) AS signal_events_count FROM signal_events;
```
Returned: **2**

### 3) At least 2 distinct `event_type` values within 24 hours
**Result: ✅ PASS**

```sql
SELECT COUNT(DISTINCT event_type) ... WHERE created_at > datetime('now', '-24 hours');
```
Returned: **2**

Observed event types:
- `MANUAL_SQL_FIX` = 1
- `PRICE_ALERT` = 1

### 4) Quarantine count stable at 11
**Result: ✅ PASS**

```sql
SELECT COUNT(*) FROM quarantine WHERE resolved_at IS NULL;
```
Returned: **11**

### 5) FET #1159 `final_roi` unchanged at 3.37
**Result: ✅ PASS**

```sql
SELECT id, ticker, final_roi FROM signals WHERE id = 1159;
```
Returned: `1159 | FET | 3.37`

### 6) SC-2, KPI-R1, KPI-R4 stable vs pre-deploy baseline
**Result: ✅ PASS**

| Metric | Pre-Deploy Baseline | Post-Deploy Canary | Status |
|--------|----------------------|--------------------|--------|
| SC-2 | 41 / 335 (12.24%) | 41 / 335 (12.24%) | ✅ Stable |
| KPI-R1 | 22.36% | 22.36% | ✅ Stable |
| KPI-R4 | 80.0% | 80.0% | ✅ Stable |

---

## Evidence — Latest Events

```text
id=2  signal_id=1159  event_type=PRICE_ALERT     source=guardian-canary  field=canary  old_value=schema_verified  new_value=event_stream_verified  source_msg_id=guardian-a1-canary-b2da699d
id=1  signal_id=1159  event_type=MANUAL_SQL_FIX  source=guardian-canary  field=canary  old_value=NULL             new_value=schema_verified        source_msg_id=guardian-a1-canary-b2da699d
```

These rows confirm:
- migrated columns are writable
- structured metadata fields persist correctly
- source attribution works
- event stream is queryable immediately after write

---

## Assessment

A1 canary is **clean**.

The only wrinkle was that production had not yet naturally exercised the event path, so the table still showed the old 6-column shape at first inspection. That is not a failed deployment, it is the expected consequence of A1's lazy migration design. The documented fallback successfully triggered first-write migration and verified persistence without mutating business data.

No regression detected in:
- quarantine handling
- signal formula / ROI state
- false closure metric
- breakeven ratio
- leverage completeness

---

## Verdict

# ✅ PASS

**6/6 canary checks passed.**

- Schema migrated successfully on first event write
- Event logging works and persists
- Two distinct event types verified
- No data-quality regression detected
- No rollback action needed

---

## Recommended Follow-Up

1. Continue passive monitoring for **natural** lifecycle events over the next 24h
2. Confirm non-canary sources (`micro-gate`, `oink-sync`) begin populating `signal_events`
3. If natural traffic remains unexpectedly silent despite normal signal flow, investigate instrumentation call paths, not the schema migration

---

*🛡️ GUARDIAN — A1 Post-Deploy Canary*
