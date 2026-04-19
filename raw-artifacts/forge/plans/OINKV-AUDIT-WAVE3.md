# Wave 3 OinkV Plan Audit — Consolidated Summary

**Audit date:** 2026-04-19T15:30Z
**Audit method:** Hermes-subagent fallback (3 parallel subagents; canonical OinkV LLM-timeout avoidance)
**Plans audited:** A8, A9, A11 (A6 excluded — already shipped; A10 excluded — 🔴 CRITICAL awaiting Mike)
**Base commits:** oink-sync `ab5d941`, oinkfarm `69d6840a`, signal-gateway `1adeaa1` (A6 just merged)

---

## Headline Verdicts

| Plan | Tier | Verdict | 🔴 CRITICAL | 🟡 MINOR | 🟢 CONFIRMED |
|------|------|---------|-------------|----------|---------------|
| A8 — Conditional SL Type | 🟡 STANDARD | READY-WITH-MINOR-EDITS | 0 | 5 | ~10 |
| A9 — Denomination Multiplier | 🟢 LIGHTWEIGHT | READY (implementation already underway on anvil/A9-denomination-multiplier branches; INSERT-time as plan §0 specifies) | 1 (doc-only) | 6 | 7 |
| A11 — Leverage Source Tracking | 🟢 LIGHTWEIGHT | READY-WITH-MINOR-EDITS | 0 | 6 | 6 |

**Overall:** All three plans are safe to implement without FORGE revision. The one 🔴 CRITICAL is a documentation inconsistency in A6-A11-SUMMARY.md (not in the plan itself) that Mike should know about but does not block ANVIL — ANVIL follows plans, not summaries.

## Key Findings

### A8 (Conditional SL Type)
- Every line-number citation verified accurate at HEAD (micro-gate-v3.py canonical: `.openclaw/workspace/scripts/`)
- SQL migration ran clean on DB copy: produces 465 FIXED + 28 NONE (matches plan §3c prediction exactly)
- SQLite 3.46.1 supports `DROP COLUMN` rollback (plan's rollback strategy viable)
- No kraken-sync dead-code targeting (Wave 1 showstopper absent)
- Test file path should point to `.openclaw/workspace/tests/` (A5/A7 convention), not `signal-gateway/tests/`

### A9 (Denomination Multiplier)
- 🔴 **Doc inconsistency:** A6-A11-SUMMARY.md §"FORGE Design Decisions" claims "Normalize at Comparison Time, Not INSERT Time" — WRONG. The authoritative TASK-A9-plan.md §0/§4e explicitly chooses INSERT-time normalization. ANVIL has correctly followed the plan (implementation at `890afce1` on .openclaw/workspace confirms INSERT-time). FORGE should fix the summary.
- `lifecycle.py` NOT touched → Financial Hotpath tier stays 🟢 LIGHTWEIGHT (stable)
- Live oink-sync tests: 23/23 pass on denomination suite
- "1 known bad signal" claim is misidentified in the plan (id=1497 stored correctly; real anomaly is PEPE→PF_PEPEUSD rows which A9 does NOT fix — minor scope clarification needed but not blocking)
- ANVIL has already implemented on both repos — moving straight to review

### A11 (Leverage Source Tracking)
- Leverage extraction block at line 831-839 of micro-gate matches plan excerpt verbatim
- `leverage_source` column does NOT exist in signals schema → clean add
- Live NULL-rate verified at **80.12%** (493 total / 395 NULL) — plan's 80.1% claim exact
- No enum collision with existing `close_source` values
- INSERT line cited as "855" in plan; actual line is 922 (binding at 929/938) — minor drift, not blocking
- Plan §0 lists 4 enum values (EXPLICIT/EXTRACTED/DEFAULT/NULL) but §4a only implements 2 — scope clarification needed

## Individual Audit Files

- /home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A8.md (13.7 KB)
- /home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A9.md (22.1 KB)
- /home/oinkv/forge-workspace/plans/OINKV-AUDIT-WAVE3-A11.md (15 KB)

## Provenance Note

These audits were produced by 3 parallel Hermes `delegate_task` subagents (Claude Opus 4-7), NOT by the OinkV agent. OinkV was bypassed this cycle because Wave 2's OinkV dispatch hit `FailoverError: LLM request timed out` and we chose to avoid re-burning 60+ min of wall-clock. The Hermes-fallback method is documented in `oinkfarm-sprint-orchestrator` skill "Hermes-Subagent Fallback" section.

Tokens: ~3.2M input / ~86K output across 3 tasks. Wall clock: ~9 min 4 sec for all three audits.

## Recommended Next Actions

1. **FORGE:** Patch A6-A11-SUMMARY.md §"FORGE Design Decisions" to match TASK-A9-plan.md §0 (INSERT-time normalization, not comparison-time).
2. **ANVIL:** A9 already at PR stage (oink-sync #8, oinkfarm #132 — both CLEAN). Await VIGIL review, then optionally start A11 (🟢 LIGHTWEIGHT) or A8 Phase 0 (🟡 STANDARD — needs full proposal + GUARDIAN review).
3. **Orchestrator:** Dispatch VIGIL A9 Phase 1 review + Hermes parallel review. 🟢 LIGHTWEIGHT = no GUARDIAN.
4. **Mike:** No approval needed for A8/A9/A11 audit findings. A10 (DB merge) still requires your approval per FORGE's Wave 3 summary flags.
