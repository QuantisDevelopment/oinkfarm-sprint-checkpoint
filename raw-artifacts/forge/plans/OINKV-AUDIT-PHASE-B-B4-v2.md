# OinkV Engineering Audit — FORGE Plan B4 v2

**Auditor:** OinkV  
**Date:** 2026-04-20 05:xx CEST  
**Scope:** `/home/oinkv/forge-workspace/plans/TASK-B4-plan.md`  
**Tier:** 🔴 CRITICAL — PostgreSQL cutover / authoritative-store switch

---

## 0. Audit Header

| Item | Value |
|------|-------|
| Plan under review | `/home/oinkv/forge-workspace/plans/TASK-B4-plan.md` |
| Size | 24,486 bytes |
| mtime | 2026-04-20 05:16 CEST |
| Revision | v2 |
| Canonical heads verified | oinkfarm `6af042f7`, oink-sync `73d074f1`, signal-gateway `cc70e5ba`, `.openclaw/workspace` `0fbcbf1b` |
| Runtime facts re-checked | `signal-gateway.service.DISABLED`, no `micro-gate` unit, `psql` absent, `psycopg` absent, `reconcile_stores.py` has no `--full` flag |

### Re-audit summary

v2 clears the original command-level blockers and materially improves operator safety. The prior 3 SHOWSTOPPER and 2 CRITICAL findings are addressed. However, two residual plan-consistency issues remain in a CRITICAL-tier document.

---

## 1. Findings Map

| Prior finding | Prior severity | v2 verdict | Evidence |
|---|---:|---|---|
| `systemctl --user restart micro-gate` targeted nonexistent unit | 🔴 SHOWSTOPPER | ✅ FIXED | v2 removes the unit restart and correctly states micro-gate is inline under signal-gateway (`USE_INLINE_GATE=1`) |
| `signal-gateway.service` is DISABLED / live process is manual nohup | 🔴 SHOWSTOPPER | ✅ FIXED | v2 uses a manual `pkill ... && nohup ...` restart pattern and explicitly documents `.DISABLED` |
| `reconcile_stores.py --full` flag does not exist | 🔴 SHOWSTOPPER | ✅ FIXED | v2 removes `--full`; live `--help` confirms only `--output-dir`, `--day`, `--db` |
| `OINK_PG_URL` missing from env-flip recipe | 🔴 CRITICAL | ✅ FIXED | v2 adds a dedicated env-var matrix and includes `OINK_PG_URL` in cutover instructions |
| PostgreSQL / psycopg / B2 migration / dual-write prerequisites absent | 🔴 CRITICAL | ✅ FIXED | v2 adds the P1-P8 blocker table and explicitly marks P4-P8 unmet |
| `.openclaw/workspace` fork is B1-only | 🟡 MAJOR | ✅ FIXED | v2 adds explicit fork-sync / re-point handling and Mike flag Q-B4-5 |
| "7+ days" vs "7 reports" ambiguity | 🟠 MINOR | ✅ FIXED | v2 disambiguates to 72h bootstrap plus 7+ daily CLEAN reports |
| Local-time backup filename ambiguity | 🟠 MINOR | ✅ FIXED | v2 switches backups to UTC timestamp form |
| Stale pre-Phase-B commit references | 🔴 | ✅ FIXED | v2 cites post-B3 heads matching live repos |

---

## 2. New findings in v2

### N1 — Internal readiness language still overstates B3 completion
**Severity:** 🟡 MAJOR

v2 correctly adds the §1 prerequisite gate showing:
- P7 `OINK_DB_DUAL_WRITE=true` is still ❌
- P8 reconciliation reports are still ❌
- PostgreSQL tooling is still not provisioned

But two later sections still read as if B3 verification has already completed:
- §3: `Schema is already in place from B2. Data is synchronized from B3.`
- §8 risk row: `Missing data after cutover | Very Low (B3 verified 7+ days)`

Those lines contradict the new gate table and soften the operator's sense of actual readiness.

**Required fix:** make these lines future-conditional or gate-conditional, for example:
- `Schema will be in place after B2 migration completes; data will be synchronized only after B3 dual-write + reconciliation prerequisites are satisfied.`
- Update the risk row to reference the prerequisite gate rather than treating B3 verification as already complete.

---

### N2 — Fork-sync is still treated as an in-window cutover step despite being a prerequisite-class change
**Severity:** 🟡 MAJOR

v2 correctly identifies the `.openclaw/workspace` fork gap, but the operational placement is still risky for a CRITICAL cutover:
- §2 says `No Code Changes Required`
- §4a.-1 and T-10min explicitly perform a code sync: `cp /home/oinkv/oinkfarm/scripts/oink_db.py /home/oinkv/.openclaw/workspace/scripts/oink_db.py`

That is not a pure config flip. It is a tracked-code synchronization step on a live dependency path for dashboard / oinkdb-api / portfolio-webhook. Doing it inside the cutover window mixes repo drift remediation with authoritative-store cutover.

**Required fix:** move fork-sync / re-pointing out of the T-10 cutover window and into a completed precondition. The plan should treat this as:
- a pre-B4 micro-task completed and verified before scheduling the cutover, or
- a new prerequisite row in the gate table.

Also update the §2 `No Code Changes Required` language so it no longer contradicts the plan's own actions.

---

## 3. Final Verdict

## 🟡 MINOR-REVISION

### Why not REJECT
The original audit blockers are fixed:
- no phantom unit restarts remain,
- no invalid reconciler flag remains,
- the env-var gap is closed,
- the prerequisite chain is now explicit and honest.

The core B4 structure is now sound.

### Why not SHIP-READY yet
Because this is a CRITICAL cutover plan, the remaining contradictions matter:
1. parts of the doc still speak as if B3 verification is already complete,
2. fork-sync is still embedded as a cutover-window operation while the same document labels B4 a config-only transition.

These are revision-level issues, not redesign-level issues. A focused v2.1 pass should clear them.

### Required changes for SHIP-READY
1. Fix the two over-optimistic readiness statements (§3 and §8).
2. Promote fork-sync / re-pointing to a completed prerequisite, not a T-10 step.
3. Update the `No Code Changes Required` wording to match the real operational sequence.

---

## 4. SLA

**SLA for revised B4 plan:** 4 hours  
Reason: CRITICAL-tier plan, but residual issues are documentation / sequencing corrections, not architectural rewrites.

---

## 5. Audit close note

B4 v2 is substantially better than v1 and is close. Once the two residual consistency issues are corrected, I would expect a clean SHIP-READY verdict.
