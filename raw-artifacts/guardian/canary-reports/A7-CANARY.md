# A7 Canary Report — UPDATE→NEW Detection Guard

**Task:** A7 — phantom trade prevention (`UPDATE_DETECTED` suppression)  
**Tier:** 🔴 CRITICAL  
**Merge commit:** `61573158`  
**Merged at:** 2026-04-19T13:27:00Z  
**Canary started:** 2026-04-19T11:29Z  
**Status:** IN PROGRESS

---

## Canary Target

This canary is event-shaped, not signal-shaped.

- Primary target: first **10 `UPDATE_DETECTED` suppressions**
- Timeout: **48h**
- If fewer than 3 suppressions in 48h: **INCONCLUSIVE**

For each suppression, verify:
1. existing signal unchanged
2. no new signal row inserted
3. `signal_events` contains `UPDATE_DETECTED`
4. `quarantine` contains `A7_UPDATE_DETECTED`
5. rejection log contains matching line
6. payload `signal_id` matches the existing ACTIVE/PENDING/PARTIALLY_CLOSED row

Secondary target:
- spot-check **3 allowed INSERTs** with entry diff >5% and verify A7 note annotation in `signals.notes`

---

## Pre-Deploy Baseline

- SC-4 signal count: **492**
- `UPDATE_DETECTED` events: **0**
- `A7_UPDATE_DETECTED` quarantine entries: **0**
- gate-rejections log entries: **5394** baseline expectation from review context
- Status distribution baseline:
  - ACTIVE = **77**
  - PARTIALLY_CLOSED = **2**
  - PENDING = **11**

---

## Artifact Paths Verified

### Merge marker
- `/home/oinkv/anvil-workspace/A7-MERGED.marker`

### Live rejection log
The active log path is:
- `/home/oinkv/.openclaw/workspace/status/gate-rejections.jsonl`

The older path under `/home/oinkv/signal-gateway/status/` is **not** the live file for this deployment.

---

## Initial Production Snapshot

### Database
- Total signals: **492**
- `UPDATE_DETECTED` events in `signal_events`: **0**
- `A7_UPDATE_DETECTED` entries in `quarantine`: **0**
- ACTIVE: **77**
- PARTIALLY_CLOSED: **2**
- PENDING: **11**

### Standard monitoring snapshot
- SC-1 total signal_events: **279**
- SC-2 false closures: **11.8841%**
- SC-4 total signals: **492**
- KPI-R1 breakeven 7d: **20.4167%**
- KPI-R4 NULL leverage: **80.0813%**
- KPI-R5 MARKET/FILLED with NULL filled_at: **0**
- KPI-R6 ingestion: **24 last 24h** vs **39.2857/day avg 7d**

**Immediate daily-monitoring verdict:** no >5% regression detected from baseline guardrails.

---

## Early Canary Finding

The rejection log already contains `A7_UPDATE_DETECTED` lines, but the production DB does **not** yet show matching audit artifacts.

### Observed in live rejection log
- total log lines now: **5494**
- `A7_UPDATE_DETECTED`-like lines found: **100**

Representative entries reference:
- trader: `Tester`
- channel: `active-futures`
- existing signal: `#100`
- examples with diffs `0.3%`, `1.0%`, `5.0%`

### Observed in production DB at same check
- `signal_events.event_type='UPDATE_DETECTED'`: **0**
- `quarantine.error_code='A7_UPDATE_DETECTED'`: **0**
- post-A7 inserted signals (`posted_at >= 2026-04-19T13:27:00Z`): **0**
- `signals.id = 100`: **absent**
- trader `Tester`: **absent**

### Interpretation
These are still **synthetic or test-generated suppressions**, not validated production suppressions. The evidence is now stronger than at canary start: the rejection-log count continues to rise, but there are still zero matching DB-side audit artifacts, zero post-A7 inserted rows, and the referenced target entities (`Tester`, `signal #100`) do not exist in production.

This remains **not countable** toward the 10-suppression canary target. It is now a **persistent synthetic-log anomaly** in the live rejection stream, but not yet a production suppression failure.

---

## Allowed-Insert Spot Check State

- post-A7 inserted signals observed so far: **0**
- signals with obvious A7 note annotations found so far: **0 confirmed live A7 inserts**
- one historical note match exists on signal `#876`, but it is legacy/human commentary and not treated as an A7 canary sample

Allowed-insert canary count:
- **0 / 3** spot-checks completed

---

## Suppression Canary Log

| # | Suppression source | Rejection log | signal_events | quarantine | existing row unchanged | no new row | Verdict |
|---|--------------------|---------------|---------------|------------|------------------------|------------|---------|
| 1 | Organic production suppression, Eric / VVV / LONG, msg `1495402373475209276` | ✅ matching A7 line | ✅ event `signal_events.id=296` on signal `#1610` | ✅ quarantine `id=17` | ✅ existing `ACTIVE` row `#1610` preserved | ✅ no duplicate insert | PASS |
| 2 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 3 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 4 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 5 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 6 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 7 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 8 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 9 | Awaiting validated production suppression | — | — | — | — | — | Pending |
| 10 | Awaiting validated production suppression | — | — | — | — | — | Pending |

---

## First Validated Production Suppression

A real production suppression has now been observed and validated.

### Evidence bundle
- Rejection log line at `2026-04-19T12:36:09.629640+00:00`
- Trader / ticker / direction: **Eric / VVV / LONG**
- Existing protected row: **signal #1610** (`ACTIVE`, entry `9.4141`)
- Suppressed incoming entry: **9.3849**
- Price diff: **0.31%**
- `signal_events`: **UPDATE_DETECTED id=296** linked to signal `#1610`
- `quarantine`: **A7_UPDATE_DETECTED id=17**
- Post-A7 inserted rows: **0**

### Validation result
This is a clean canary pass for suppression sample #1:
1. existing signal unchanged, ✅
2. no new signal row inserted, ✅
3. `signal_events` contains `UPDATE_DETECTED`, ✅
4. `quarantine` contains `A7_UPDATE_DETECTED`, ✅
5. rejection log contains matching line, ✅
6. payload points to the existing active row, ✅

Synthetic `Tester / signal #100` noise is still present in the rejection log, but it is now clearly separable from at least one real production suppression.

## Current Canary Verdict

**PENDING, ADVANCING**

Reason:
1. Merge is confirmed.
2. Standard SC/KPI monitoring is stable.
3. **1 / 10** validated production suppressions now passes the full artifact check.
4. Synthetic `Tester` noise still exists in the live rejection log, but it is no longer the only A7 pattern in production.
5. No allowed-insert spot-check sample has appeared yet, so the secondary path remains unverified.

---

## Next Checks

1. Monitor for the first validated production `UPDATE_DETECTED` suppression with all three artifacts present.
2. Compare any future rejection-log A7 lines against:
   - `signal_events.UPDATE_DETECTED`
   - `quarantine.A7_UPDATE_DETECTED`
   - unchanged target signal row
   - no inserted duplicate signal row
3. Spot-check first 3 >5% allowed INSERTs for A7 note annotation.
4. Treat additional `Tester` / `signal #100` lines as synthetic noise unless they begin correlating with DB artifacts.
5. If the artifact mismatch appears on real production suppressions, escalate as canary anomaly.
6. If <3 validated suppressions by 48h after merge, mark **INCONCLUSIVE**.
