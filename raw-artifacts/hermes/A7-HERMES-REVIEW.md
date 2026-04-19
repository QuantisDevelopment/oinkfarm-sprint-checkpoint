# A7 HERMES INDEPENDENT REVIEW

**PR:** #130 — `feat(A7): UPDATE→NEW detection guard — phantom trade prevention`
**Branch:** `anvil/A7-update-detected-guard`
**Commit:** `2036f097457e5f9ecd3d1c14360e094cfd29f029`
**Baseline:** `498d8b28` (fix(A1): add PRICE_ALERT to LIFECYCLE_EVENTS set)
**Tier:** 🔴 CRITICAL — Financial Hotpath #6 (micro-gate INSERT logic)
**Reviewer:** Hermes (independent)
**Date:** 2026-04-19

---

## Scope of Independent Review

VIGIL (10.00 PASS) and GUARDIAN (10.00 PASS) both delivered clean scores. Hermes' job
here is not to re-score dimensions but to **independently re-derive correctness** on the
code-quality axes most at risk of a silent-bypass bug in a CRITICAL-tier financial hotpath:
the 5% boundary operator, zero-entry fallthrough, placement of the guard relative to side
effects, and an actual `pytest` run rather than reasoning about the tests by inspection.

No source files were modified. No merge/push/comment actions taken. Only write: this file.

---

## 1. Five-percent boundary — correctness

**Formula (line 847):**
```python
price_diff_pct = abs(entry_price - existing_entry) / existing_entry * 100
```

**Branch (line 848):**
```python
if price_diff_pct > _A7_ENTRY_TOLERANCE_PCT:     # allow INSERT
    ...
else:                                             # suppress
    ...
```

With `_A7_ENTRY_TOLERANCE_PCT = 5.0`:
- diff **≤ 5.0%** → `else` branch → suppress ✅
- diff **> 5.0%** → allow ✅

Boundary behavior is exactly the spec. Confirmed empirically by the two boundary tests
(`test_threshold_boundary_5pct_suppress` → 5.0% exact → suppress; `test_threshold_boundary_above_5pct_allow`
→ 5.01% → allow). The operator is `>` (not `>=`), which is the correct choice for an
"≤threshold suppress" semantic — the single most likely off-by-one in this diff and it is right.

The denominator is `existing_entry`, the baseline price. This is the conventional percentage-of-change
formula and matches the natural-language spec ("entry price differs by more than 5% from the existing
position"). Using the existing entry as denominator is also the safer choice because `_match_active`
guarantees it is a real persisted value, whereas `entry_price` is freshly parsed.

**Verdict: ✅ correct.**

---

## 2. Zero-entry guard — division-by-zero impossible; fallthrough is intentional

**Guard (line 846):** `if existing_entry > 0 and entry_price > 0:`

Two independent safeties:
1. `existing_entry = existing.get("entry_price", 0) or 0` at line 845 defends against
   both missing keys and stored `NULL`, coercing to `0`.
2. Step 3 (line 629) rejects any inbound signal with `entry_price <= 0` before A7 is ever
   reached — so in practice `entry_price > 0` at line 846 is redundant defense-in-depth,
   but a perfectly reasonable belt-and-braces.

When either side is `0`, A7 does nothing and execution continues to step 15/16 — this is the
intentional "data-quality noise" comment on line 878. It is a correct choice: blocking an
INSERT because of a zero entry on a *historical* row would be wrong (the row is already in the
DB), and a zero on the *new* row is already handled two hundred lines earlier by SCHEMA_VIOLATION.

Tests `test_zero_existing_entry_allows`, `test_zero_new_entry_rejected_step3`,
`test_zero_both_rejected_step3` all pass. The zero-new-entry case never enters A7 — it is
caught by step 3 first — which is exactly the documented contract.

**Verdict: ✅ correct; division-by-zero mathematically impossible.**

---

## 3. Status IN clauses — all four sites broadened

Per GUARDIAN's line map, confirmed via `search_files`:

| Site | Line | Before | After | Verified |
|------|------|--------|-------|----------|
| `_match_active` exact-trader query | 384 | `('ACTIVE','PENDING')` | `('ACTIVE','PENDING','PARTIALLY_CLOSED')` | ✅ |
| `_match_active` canonical-name query | 394 | same | same | ✅ |
| `_match_active` ticker-only fallback | 410 | same | same | ✅ |
| §4b `CROSS_CHANNEL_DUPLICATE` guard | 669 | same | same | ✅ |

All four strings in the diff are byte-identical (`'ACTIVE', 'PENDING', 'PARTIALLY_CLOSED'` with
a single space after each comma). No typos (`'PARTIAL_CLOSED'`, `'PARTIALLY-CLOSED'`, etc.).
No additional unrelated `status IN` clauses in the file were missed:

```
grep -n "status IN (" scripts/micro-gate-v3.py → 4 matches, all updated.
```

All four are additive (broadening), so a `PARTIALLY_CLOSED` row that was previously invisible
to the gate is now visible — this is the desired A4 alignment and cannot regress any prior
behavior (no branch previously depended on *excluding* PARTIALLY_CLOSED).

**Verdict: ✅ correct; no missed sites.**

---

## 4. Guard placement — all variables resolved, before any side effect

```
Line 822: method = entry.get("extraction_method", "unknown")
Line 824: notes  = " ".join(notes_parts).strip() or None
Line 832: trader_id = _get_or_create_trader(...)       ← Step 14 ends here
Line 840: # ── A7: UPDATE→NEW detection ──             ← NEW GUARD
Line 880: posted_at = entry.get("timestamp") or _now_iso()  ← Step 15
Line 884: # ── 16. INSERT ──                           ← First side effect
```

Every variable referenced inside the A7 block is defined upstream in the same function:
- `trader_id` ← line 832
- `trader_name_raw` ← line 830
- `ticker`, `direction`, `entry_price` ← lines 611–613
- `server_id` ← line 831 (canonical override applied)
- `notes` ← line 824
- `method` ← line 822
- `dmid` ← line 610

The guard fires **before** `INSERT`, so the suppression path never writes a signal row. It
does write three append-only artifacts (`gate-rejections.jsonl`, `quarantine`, `signal_events`)
and that is the *intended* audit trail. The `return` at line 868–877 exits `_process_signal`
cleanly; the caller `process_one` at line 599 returns the dict unmodified.

Sqlite3.Row handling: `_match_active` returns `dict(rows[0])` (lines 400/415), so both
`existing.get("entry_price", 0)` and `existing["id"]` are safe dict access — empirically
confirmed in a Python REPL.

**Verdict: ✅ correct placement; no missing variable bindings.**

---

## 5. Test runs — 31/31 A7-relevant pass

Run environment: `/home/oinkv/.openclaw/workspace` at commit `2036f097`, Python 3.13.7, pytest 9.0.2.

```
$ pytest -xvs tests/test_a7_update_detection.py
============================== 20 passed in 0.04s ==============================
```

All 20 named A7 tests pass individually, covering:
- MUST (7): suppress 1%, 0.3%, allow 7.7%, no-existing, opposite-direction, rejection-logged, PENDING match
- SHOULD (8): PARTIALLY_CLOSED match, event payload, no-trader bypass, 5% both sides, ticker_only, ambiguous, notes annotation, GUARDIAN cross-concern
- ZERO (3): zero-existing, zero-new-rejected-by-step3, both-zero-rejected-by-step3
- COMPLEMENTARY (2): §4b exact-match layering, GUARDIAN-1 PARTIALLY_CLOSED + ticker_only flag

```
$ pytest -xvs tests/test_micro_gate_filled_at.py tests/test_micro_gate_source_url.py
============================== 11 passed in 0.03s ==============================
```

Schema-compat DDL additions (`traders`, `signal_events`) in these two files do not break
the existing assertions and are forward-looking.

Broader sweep (`pytest tests/ -k 'micro_gate or a7_update'`) showed 32 passed / 5 failed.
**I reproduced the 5 failures against the pre-A7 baseline `498d8b28` in a detached
worktree** and got the identical 5 failures — they are pre-existing
(`test_micro_gate_mutation_guard.py` ×3, `test_micro_gate_wg_alert_override.py` ×2) and
are unrelated to this PR. A7 does not introduce any regression.

**Verdict: ✅ 20/20 A7 + 8/8 filled_at + 3/3 source_url pass; no A7-caused regressions.**

---

## 6. `event_store.py` registry updates

`LIFECYCLE_EVENTS` set (line 78): `"UPDATE_DETECTED"` present under a new "Stage 8:
Gate-level protection" comment. ✅

`QUARANTINE_CODES` set (line 98): `"A7_UPDATE_DETECTED"` present. ✅

Both are additions to `set` literals — no ordering, no conflict risk.

---

## 7. Surgical-diff verification

```
$ git show 2036f097 --stat
 scripts/event_store.py              |   3 +
 scripts/micro-gate-v3.py            |  48 +++-
 tests/test_a7_update_detection.py   | 488 ++++++++++++++++++++++++++++++++++++
 tests/test_micro_gate_filled_at.py  |  11 +
 tests/test_micro_gate_source_url.py |  23 ++
```

Production code delta is **48 insertions + 4 deletions in micro-gate-v3.py + 3 insertions
in event_store.py** — matches the "~40-line guard + 4 status IN single-line edits + 2
registry additions" expectation precisely. No drive-by edits, no refactoring, no unrelated
whitespace. The test DDL additions are limited to CREATE TABLE statements for `traders`
and `signal_events` already referenced implicitly by A7's new query paths.

---

## 8. Signature sanity check on `_log_rejection` and `_log_event`

`_log_rejection(entry, reason_code, reason_detail, extra=None, conn=None)` — defined at line 297.
New A7 call at line 856: `_log_rejection(entry, "A7_UPDATE_DETECTED", <detail>, conn=conn)`.
Positional mapping is exact; `conn=conn` passed as kwarg, which is required to hit the
quarantine write at line 299. Matches all 11 other callers that also use `conn=conn`.

`_log_event(conn, event_type, signal_id, payload=None, source="micro-gate")` — defined at line 61.
New A7 call at line 861: `_log_event(conn, "UPDATE_DETECTED", existing["id"], {...payload...})`.
Matches all 6 other callers (e.g. `_log_event(conn, "SIGNAL_CREATED", signal_id, {...})` at line 922).
The payload dict keys (`suppressed_entry`, `existing_entry`, `price_diff_pct`, `extraction_method`,
`discord_message_id`) are all JSON-serialisable scalars.

**Verdict: ✅ both helper calls match their signatures and the codebase convention.**

---

## 9. PR state — DIRTY due to unrebased A1 ancestor commits

`git log --oneline origin/master..2036f097` shows three commits:
```
2036f097 feat(A7): UPDATE→NEW detection guard
498d8b28 fix(A1): add PRICE_ALERT to LIFECYCLE_EVENTS set
09e0f94b feat(A1): extend signal_events schema + fix zero-event root cause
```

The two A1 commits are already on `master` as the single squash-merge `5b242c56` (PR #126).
Merging PR #130 as-is would either replay the A1 content (git is smart enough to three-way
merge cleanly, but the commit history would be noisy) or produce a conflict-free but
non-linear history.

**This is a PR-plumbing concern, not a code-quality concern.** A `git rebase origin/master`
(dropping `09e0f94b` and `498d8b28`, cherry-picking `2036f097` on top of current master)
resolves it trivially. My verdict scores the code at commit `2036f097` regardless of
rebase state, per the task brief.

---

## Minor observations (no score impact)

1. **`_A7_ENTRY_TOLERANCE_PCT` inside the function.** Currently rebuilt on every call at
   line 841. Promoting to a module-level constant would be more idiomatic and cheaper by
   an infinitesimal amount. VIGIL already noted this as a SUGGESTION. Not a correctness issue.

2. **Return dict `existing_entry` is the raw DB float** but `suppressed_entry` in the
   event payload is also raw. The `price_diff_pct` in both the return dict and the event
   payload is `round(..., 2)`; the rejection message formats it with `:.1f`. Minor cosmetic
   inconsistency (two decimals vs one) — no behavioural impact.

3. **A7 branch emits a unique `action` value** (`"a7_update_detected"`) that no downstream
   dispatcher special-cases. The upstream caller `process_one` just returns whatever it
   gets. This is fine today, but worth remembering if someone later adds action-based
   metrics aggregation.

---

## Final confidence statement

The guard is mathematically sound, surgically scoped, defensively coded, and empirically
verified by an independent test run. The 10.00 scores from VIGIL and GUARDIAN are
**supported** by this independent check: no silent-bypass bug exists at `2036f097`, no
division-by-zero is reachable, every status IN broadening is consistent, and all 31
A7-relevant tests pass. The 5 broader-sweep failures are pre-existing and confirmed on
the baseline.

PR #130 is a textbook defensive patch for a CRITICAL hotpath.

---

## Verdict: ✅ LGTM

Code at commit `2036f097` is production-ready. Financial Hotpath #6 closure is correctly
implemented: ≤5% entry drift suppresses phantom INSERT with full audit trail, >5% falls
through with a notes annotation, zero-entry cases gracefully fall through to step 15/16.
A `git rebase origin/master` is required to clean the PR ancestry before merge, but that
is orthogonal to code correctness. Cleared for merge after rebase.

---

*Hermes — Independent CRITICAL-tier review*
*2026-04-19*
