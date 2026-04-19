# Hermes Review — A8: Conditional SL Type Field

**PR:** #134 on QuantisDevelopment/oinkfarm
**Branch:** `anvil/A8-conditional-sl-type`
**Commit reviewed:** `19f475db7d5a3fcb9f5cc2dd92fd6ad8020852bf` (post-rebase — single A8 commit on top of `45a6931d` A11)
**Base:** `45a6931d feat(A11): leverage_source tracking column + backfill (#133)`
**Date:** 2026-04-19
**Reviewer:** Hermes (parallel independent review)
**PR state:** OPEN · MERGEABLE

## Summary

A8 adds `sl_type VARCHAR(15) DEFAULT 'FIXED'` to the `signals` table with a 4-value taxonomy (FIXED/CONDITIONAL/MANUAL/NONE), extracts the conditional-keyword list to a module-level constant, classifies at INSERT time after all SL processing, and marks operator SL overrides as MANUAL on both the BE path and the numeric-SL UPDATE path. Implementation matches the approved Phase 0 proposal and FORGE plan line-for-line. All 9 new tests pass, all 6 schema-updated existing test files still pass, and the 5 pre-existing failures on this branch are unrelated to A8 (verified by running the identical tests against master's `micro-gate-v3.py` — same failures). Verdict: **✅ LGTM** with two very minor non-blocking observations.

## Findings

### ✅ Verified

- **PR is now clean** after rebase: `git log origin/master..HEAD` shows a single commit `19f475db` on top of A11. The orphan `2945ada0` is gone. 9 files changed, +503/-9. All changed paths are A8-appropriate (no leaked A11 files).
- **INSERT alignment is correct (30/30/30).**
  - Columns in `INSERT INTO signals (...)`: **30** (explicit enumeration, verified)
  - `?` placeholders in `VALUES (...)`: **30** (counted programmatically)
  - Bound values in Python tuple: **30** (parsed programmatically, last element = `sl_type`)
  - `test_insert_column_placeholder_count_matches` in `test_micro_gate_filled_at.py` updated from 29→30 and still passes.
- **sl_type block placement is correct** — inserted at lines 832–838 between §8c A15 SL guard (ends line 830 with `stop_loss = None`) and §9 TP extraction (line 840). Reads final `stop_loss` state after A15 potentially NULLs it, which is the analytically correct semantics.
- **Classification logic is sound** — 3-branch tree at lines 833–838:
  - `stop_loss is not None` → CONDITIONAL if `_sl_is_conditional` else FIXED
  - `_sl_is_conditional` (with NULL stop_loss) → CONDITIONAL
  - else → NONE
  - No path produces NULL, matches proposal §3a-b and acceptance criterion 2.
- **Shared `_CONDITIONAL_SL_KEYWORDS` constant** at module scope (line 131) — 12 keywords verified, matches the legacy inline tuple character-for-character. `_sl_is_conditional` boolean cached once at line 771 and reused at line 833 — DRY, no drift risk.
- **`_ALLOWED_UPDATE_COLS` includes `"sl_type"`** (line 1066).
- **`_process_update` sets `sl_type='MANUAL'`** on both operator SL paths:
  - BE path (lines 1093–1096): `changes["stop_loss"] = entry_price` + `changes["sl_type"] = "MANUAL"`
  - Numeric-SL path (line 1115–1117): `changes["stop_loss"] = new_sl` + `changes["sl_type"] = "MANUAL"` — correctly placed inside the `else` branch so B14-blocked updates do NOT flip sl_type (matches the intent: if no SL change happens, classification shouldn't change).
- **Tests all pass:** `pytest tests/test_a8_sl_type.py -v` → 9/9 PASS in 0.03s. Full 6-file schema-update batch (`test_a5_confidence`, `test_a7_update_detection`, `test_a11_leverage_source`, `test_denomination_gate`, `test_micro_gate_source_url`, `test_micro_gate_filled_at`) → 64/64 PASS.
- **5 pre-existing failures are NOT A8-caused.** I ran the failing tests (`test_micro_gate_mutation_guard.py`, `test_micro_gate_wg_alert_override.py`) against **master's** `micro-gate-v3.py` via checkout-swap, and the same 5 failures reproduce. Root cause: `_validate_mutation_or_reject` AttributeError (unrelated infra) + WG alert override logic changes. A8 is blameless.
- **Migration SQL (`scripts/migrations/a8_sl_type.sql`) is safe:**
  - Additive only (`ALTER TABLE ... ADD COLUMN`)
  - Idempotent backfills guard on `AND sl_type = 'FIXED'` so re-running is a no-op
  - Expected row counts documented (28 NONE, 0 CONDITIONAL) — match OinkV's sandbox round-trip
  - Rollback documented: `ALTER TABLE signals DROP COLUMN sl_type;` (SQLite 3.46.1 supports it)
  - Verification queries included (commented)
- **oink-sync not broken:** `test_lifecycle_events.py` (oink-sync) was NOT modified — ANVIL correctly took OinkV's optional-flag guidance. Ran `pytest tests/test_lifecycle_events.py -v` in oink-sync → 8/8 PASS. No `sl_type` references anywhere in oink-sync (`search_files sl_type /home/oinkv/oink-sync` → 0 hits). Clean.
- **No hidden downstream consumers** — `sl_type` is referenced only in: the migration SQL, `micro-gate-v3.py` (5 call sites: classification + INSERT + UPDATE BE + UPDATE numeric + allowlist), and the 6 test files that now include it in their schema DDL. No queries, selects, or joins key off `sl_type` elsewhere in oinkfarm. Truly classification-only metadata as the proposal claimed.
- **Dry-run parity (UPDATE):** `_process_update` dry_run (line 1134) returns the full `changes` dict — when a MANUAL classification is triggered, the dry-run response surfaces `"sl_type": "MANUAL"` to the operator. Clean.

### 🟡 Concerns (non-blocking)

1. **BE→MANUAL path is not directly tested.** `test_manual_sl_type_on_update` exercises the numeric-SL update path (line 1115), which asserts `sl_type == "MANUAL"` after `stop_loss=90.0`. The BE branch at lines 1093–1096 (triggered by `sl_note in ("BE","BREAKEVEN","B/E")`) also sets MANUAL, but no test explicitly covers it. The BE code is a literal one-line assignment and low risk, but an explicit test would give VIGIL's 10/10 Test Coverage score full justification. Recommend as follow-up; not a blocker.
2. **dry_run_insert response doesn't surface sl_type.** The dry-run return at line 975 is `{"action": "dry_run_insert", "ticker", "direction", "entry_price", "order_type", "status"}` — does not include `sl_type`. This is *consistent* with the existing dry-run contract (neither `stop_loss`, `notes`, `leverage_source`, nor other classified fields are returned), so it's not a regression — but if GUARDIAN wants to canary-verify classification via dry-run in the future, that contract would need widening. Worth noting for the canary protocol, not blocking merge.
3. **Schema drift maintenance burden.** A8 now has six hand-rolled test schemas (`test_a5_confidence`, `test_a7_update_detection`, `test_a8_sl_type`, `test_a11_leverage_source`, `test_denomination_gate`, `test_micro_gate_source_url`, `test_micro_gate_filled_at`) that must all stay in lockstep with production schema. Every future column will require synchronized edits across ~6 files. This is a pre-existing pattern ANVIL inherited (not introduced by A8); flagging as technical debt for a future consolidation task (e.g. a shared `_signals_ddl()` helper module).
4. **Cosmetic: stale comment in `test_micro_gate_filled_at.py` line 281.** Reads `# ─── MUST-5: Parameter count (29 columns, 29 placeholders) ───` but the assertion value was updated to 30. VIGIL flagged an inverse variant of this (MUST-5 docstring). Neither is a correctness issue.

### ❌ Blockers

None.

## New issues VIGIL and GUARDIAN might have missed

- **B14 × MANUAL interaction:** Numeric SL update path sets `sl_type='MANUAL'` only inside the `else` branch (line 1116), so when B14 blocks the SL change (SL≈entry BE-by-number and DB already has SL≠entry), `sl_type` correctly stays unchanged. This is the **right** behavior but is unusually subtle — worth calling out as an implicit invariant for future maintainers. No test asserts this negative invariant. Non-blocking.
- **FILL × MANUAL interaction:** `update_type == "FILL"` on line 1081 sets `fill_status="FILLED"` and `status="ACTIVE"` without touching sl_type. If the same message also includes an explicit `stop_loss` change, it would fall through to the numeric-SL path and set MANUAL — correct. If the FILL message includes a conditional `sl_note` but no numeric SL, nothing happens to sl_type (the CONDITIONAL detection path is only in `_process_signal`, not `_process_update`). This is consistent with the proposal's "MANUAL only on stop_loss change" stance, but an operator re-describing the SL as conditional via an UPDATE note will NOT re-classify. Acceptable per the approved taxonomy (sl_type is set once at INSERT and only flips to MANUAL on operator override); documenting here for record.
- **VIGIL's closing line is factually wrong.** VIGIL wrote *"GUARDIAN review not required for STANDARD tier Phase 1"* — contradicts AGENTS.md which states GUARDIAN reviews 🔴 CRITICAL and 🟡 STANDARD and only skips 🟢 LIGHTWEIGHT. Per my task instructions, GUARDIAN Phase 1 is being dispatched in parallel; VIGIL's note should be treated as a miscalibrated aside, not a policy statement. This does not affect VIGIL's scoring or the code quality.

## Cross-check with other reviewers

- **VIGIL R1: 9.40 PASS** — my assessment: **AGREE-WITH-NOTE.** Scoring is well-justified. The -1 on Spec Compliance and -1 on Code Quality are fair (minor places for refinement, nothing wrong). Disregard VIGIL's closing "GUARDIAN not required" statement — it's wrong per AGENTS.md but doesn't bear on code quality.
- **GUARDIAN Phase 0: APPROVE** — my assessment: **AGREE.** The data-safety framing (additive column, DEFAULT 'FIXED', 28-row backfill, rollback via DROP COLUMN) held up under implementation. Migration file matches the proposal's SQL nearly verbatim.
- **GUARDIAN Phase 1:** pending — dispatched in parallel per orchestrator. Do not rely on; my verdict stands independently on disk-inspected evidence.

## Evidence appendix

- Ran `python3 -m pytest tests/test_a8_sl_type.py -v` → 9/9 PASS.
- Ran `python3 -m pytest tests/test_{a5,a7,a11,denomination,micro_gate_source_url,micro_gate_filled_at}*.py -v` → 64/64 PASS.
- Ran `python3 -m pytest tests/` → 99/104 PASS, 5 pre-existing failures unrelated to A8 (reproduced against master file).
- Counted INSERT columns, placeholders, and bound values programmatically → all 30.
- Greps: `sl_type|_CONDITIONAL_SL_KEYWORDS` in `/home/oinkv/.openclaw/workspace/scripts` → 21 hits, all intended. Same pattern in `/home/oinkv/oink-sync` → 0 hits (no downstream coupling).
- Verified via `git merge-base origin/master HEAD` = `45a6931d` → rebase landed cleanly, branch is a single commit on top of A11.
- PR API: `gh pr view 134` → state OPEN, mergeable MERGEABLE, 9 files changed — matches expected A8 file set.

## Verdict: ✅ LGTM

A8 is a clean, spec-compliant, fully-tested, additive metadata change with no Financial Hotpath touch, no downstream coupling, and a viable rollback. Proceed to merge once GUARDIAN Phase 1 lands (expected PASS based on Phase 0 + data-safety review of the diff). The concerns above are all advisory / technical debt, not merge blockers.
