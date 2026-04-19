# OinkV Engineering Audit — FORGE Plan A7 (Wave 2)

**Auditor:** OinkV 👁️🐷 (fallback auditor per `oinkfarm-audit-cross-check` skill)
**Date:** 2026-04-19
**Scope:** Staleness, line-reference drift, repo-drift, A1 integration, A4 dependency, Q-A7-1
**Plan:** `/home/oinkv/forge-workspace/plans/TASK-A7-plan.md`
**Target (canonical):** `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (1,407 LOC, 61,460 B, mtime 2026-04-19 01:17, HEAD=`498d8b28`)
**Alternate (stale):** `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` (1,063 LOC, 47,073 B, mtime 2026-04-15, HEAD=`38eb8e8`)
**Tier:** 🔴 CRITICAL — Financial Hotpath #6 (micro-gate INSERT logic)
**Verdict:** ✅ **Plan logic is sound and implementable**, but **all line numbers are stale** (drawn from the signal-gateway copy, not the canonical copy which has since absorbed A1/A15/B11/B14/event_store). Import path + helper-use patterns need minor fixes. A4 dependency is cleanly flagged. `ticker_only` recommendation on Q-A7-1 is supported by current code semantics.

---

## ⛔ HEADLINE: Line-Number Drift — plan references signal-gateway (stale), target is .openclaw (canonical)

The plan's §1, §2, §3, §9 line citations (`_match_active line 276`, `line 291 status IN clause`, `_process_signal lines ~550-640`, `step 14 line ~599`, `INSERT step 16 line ~612`, `B14 guard line 698-720`) are all accurate **against the signal-gateway checkout** (47 KB, Apr 15) but **wrong against the canonical `.openclaw/workspace` checkout** (61 KB, Apr 19 — base commit `498d8b28`). Since 2026-04-15, the canonical file has absorbed:

- `from event_store import EventStore` import + `_get_event_store()` + `_log_event()` helper (lines 36-78)
- `_payload_source_url()` / `_payload_close_source_url()` helpers (lines 279-292)
- `_quarantine()` helper + `_log_rejection` now accepts `conn=` kwarg (lines 297-355)
- A15 SL=entry overwrite guard (lines 739-780)
- A3 `filled_at` auto-populate at INSERT (line 851-852)
- Event-store dual-write `_log_event(..., "SIGNAL_CREATED", ...)` at line 882 **immediately after INSERT**
- `_log_event` now uses `commit=True` (commit `09e0f94b`, Wave 1 A1 fix on oinkfarm side)

These insertions shift every line citation in the plan by **+90 to +230 lines**. ANVIL must resolve citations against the canonical file or the implementation will land in the wrong place.

### Exact line-number remapping (plan → canonical)

| Plan cites | Signal-gateway (stale) | Canonical `.openclaw` (TRUTH) | Delta |
|---|---|---|---|
| `_match_active()` | line 276 | **line 368** | +92 |
| `_match_active` status IN clause | line 291 | **lines 384, 394, 410** (3 clauses — see STALE-A7-3) | +93 |
| `_process_signal()` INSERT path | lines ~550-640 | **lines 608-897** | +58 / +257 |
| Step 14 trader_id resolution | line ~599 | **line 832** | +233 |
| Step 16 INSERT | line ~612 | **lines 844-872** | +232 |
| B14 SL guard "reference pattern" | lines 698-720 | **lines 967-985** | +269 |
| signal_router cross-channel dedup | line 3591+ | **line 3589+** (signal-gateway) | ≈0 (this file only exists in signal-gateway) |
| reconciler.py B10 flip-flop | 141-166 | **lines 141-146** (`_is_flipflop` helper at 559+) | 0 (this file only exists in signal-gateway) |
| event_store.py `EventStore.log()` | line 138 | **line 138** (canonical) | 0 ✅ |

---

## Drift / Integration Issues

### 🔴 STALE-A7-1: All line numbers in §1, §2, §9 Evidence table reference signal-gateway

The Evidence table (§9) claims all line citations "Verified" — but they were verified against the signal-gateway copy, not the canonical `.openclaw/workspace/scripts/micro-gate-v3.py` which the task context explicitly names as canonical. ANVIL needs the corrected line numbers from the table above.

**Fix:** Regenerate §9 Evidence citations against the canonical file. Every plan reference to line 276/291/550-640/599/612/698-720 must be bumped by ~+90–+270.

---

### 🔴 STALE-A7-2: Import path `from oink_sync.event_store import EventStore` is WRONG

**Plan §4a code block, line 127:**
```python
from oink_sync.event_store import EventStore
```

**Reality:** `event_store.py` lives in the **oinkfarm** repo at `scripts/event_store.py` (same directory as `micro-gate-v3.py`). The canonical micro-gate already imports it at line 37:
```python
from event_store import EventStore
```
There is no `oink_sync.event_store` package reachable from micro-gate's sys.path. The plan's import would fail with `ModuleNotFoundError`.

**Worse:** the plan re-does the try/except import pattern inline *inside* the A7 guard, when a **module-level `_log_event()` helper already exists at line 61** and is the established convention used by 13 existing call sites in the file (SIGNAL_CREATED at 882, SL_MODIFIED/SL_TO_BE at 1026, ORDER_FILLED at 1031, TRADE_CANCELLED at 1104, close events at 1183, etc.).

**Fix — two mechanical changes to the plan's §4a block:**
1. Delete the inline `from oink_sync.event_store import EventStore` + `EventStore(conn)` construction.
2. Replace the whole `try/except` event-logging block with a single call:
```python
_log_event(conn, "UPDATE_DETECTED", existing["id"], {
    "suppressed_entry": entry_price,
    "existing_entry": existing_entry,
    "price_diff_pct": round(price_diff_pct, 2),
    "extraction_method": method,
    "discord_message_id": dmid,
})
```
The `_log_event` helper is already best-effort, already uses `commit=True` (A1 fix from commit `09e0f94b`), already wraps exceptions, and already defaults `source="micro-gate"`.

---

### 🔴 STALE-A7-3: `UPDATE_DETECTED` is NOT in `LIFECYCLE_EVENTS` set → event will be accepted but there is no canonical registration

**Canonical** `scripts/event_store.py` lines 53-77 define `LIFECYCLE_EVENTS` with 19 entries (SIGNAL_CREATED, ORDER_FILLED, LIMIT_EXPIRED, SL_MODIFIED, SL_TO_BE, TP_MODIFIED, TP_HIT, PARTIAL_CLOSE, TRAILING_STOP_SET, ENTRY_CORRECTED, TRADE_CLOSED_SL/TP/MANUAL/BE, GHOST_CLOSURE, TRADE_CANCELLED, TRADE_RESTORED, MANUAL_SQL_FIX, PRICE_ALERT). **`UPDATE_DETECTED` is not there.**

`EventStore.log()` itself does NOT validate event_type against the set (see lines 138-166 — it just `INSERT`s the string), so the event WILL land in signal_events. But the `LIFECYCLE_EVENTS` set is the canonical registry that VIGIL & GUARDIAN check; shipping A7 without adding `UPDATE_DETECTED` will draw a MUST-FIX in review (same pattern as the `498d8b28` fix, which added `PRICE_ALERT` for exactly this reason).

**Fix:** §2 Files to Modify must add:
| scripts/event_store.py | `LIFECYCLE_EVENTS` set | MODIFY | Add `"UPDATE_DETECTED"` to the registry (new Stage 4 entry) |

---

### 🔴 STALE-A7-4: `_log_rejection()` signature has changed — plan's call silently skips quarantine

**Plan §4a:**
```python
_log_rejection(entry, "A7_UPDATE_DETECTED", f"Active signal #{existing['id']} exists for …")
```

**Canonical signature (line 297):**
```python
def _log_rejection(entry, reason_code, reason_detail, extra=None, conn=None):
    if conn is not None:
        _quarantine(conn, entry, reason_code, reason_detail)
    ...
```

Without `conn=conn`, the A7 rejection will be written to `gate-rejections.jsonl` but **not** to the quarantine table. All other in-file call sites pass `conn=conn` (lines 621, 625, 629, 635, 642, 653, 674, 686, 733, 876, 896). A7 must match that convention, otherwise the rejection is invisible to GUARDIAN's quarantine-based canaries.

**Fix — one-line patch to §4a code block:**
```python
_log_rejection(entry, "A7_UPDATE_DETECTED",
    f"Active signal #{existing['id']} exists for {trader_name_raw}/{ticker}/{direction} "
    f"(entry diff {price_diff_pct:.1f}%, threshold 5%)",
    conn=conn)
```

Additionally, `A7_UPDATE_DETECTED` is not in the `QUARANTINE_CODES` set at `event_store.py` line 80-96. Either add it to the set or accept that quarantine rows with unknown codes are tolerated (the current `_quarantine()` helper does not gate on code membership — see event_store.py line 168 vs its callers). **Recommendation:** add `"A7_UPDATE_DETECTED"` to QUARANTINE_CODES for consistency with how A1 A15 B11 CROSS_CHANNEL_DUPLICATE are registered.

---

### 🟡 MINOR-A7-5: Cross-channel active dedup (§4b "step 4b") is a DUPLICATE of part of A7 — plan should acknowledge this

The canonical file **already has** a trader+ticker+direction+entry_price pre-INSERT dedup at lines 656-680 (comment: `# ── 4b. Cross-channel active dedup ──`). This runs *before* step 5 (price deviation), i.e., BEFORE step 14 / step 16 where A7 wants to hook in.

Relationship:
- Existing §4b (exact entry match): suppresses when entry_price is byte-identical to an ACTIVE/PENDING row for the same trader_id/ticker/direction. Uses `CROSS_CHANNEL_DUPLICATE` rejection code.
- New A7 (fuzzy 5% entry match): suppresses when entry_price is within 5% AND handles `ticker_only` match confidence (no trader_id needed). Uses `A7_UPDATE_DETECTED` rejection code.

**The plan §1 already gestures at this** ("The cross-channel dedup in signal_router.py requires exact entry_price match"), but it's conflating the signal_router version (line 3589) with micro-gate's own already-deployed `CROSS_CHANNEL_DUPLICATE` guard. ANVIL should understand A7 adds a **second, fuzzier** layer INSIDE micro-gate — not the first line of defense inside micro-gate.

**Fix:** §1 "The Gap" table should explicitly list the THIRD existing protection:
- micro-gate `CROSS_CHANNEL_DUPLICATE` guard (lines 656-680): catches exact (trader_id, ticker, direction, entry_price) matches.
- A7 is the fuzzy-match fall-back that catches the residual set.

---

### 🟡 MINOR-A7-6: `notes_parts` and `trader_name_raw` — availability check

Plan §4a writes to `notes_parts` at line 114 (the "genuine new position" branch). Canonical:
- `notes_parts = []` initialized line 708 (step 8)
- `trader_name_raw = entry.get("trader", "")` set line 830 (step 14) — but *also* set earlier at line 658 (inside step 4b cross-channel guard).

If A7 is inserted between step 14 and step 16 (as the plan states), both variables are in scope. ✅ Confirmed.

However: the plan's `notes_parts.append(...)` for the "allow INSERT" branch is joined into `notes` at line 824 (step 12 "Notes assembly"). A7 sits *after* step 14 and *after* the `notes = " ".join(notes_parts).strip() or None` assembly. **The A7 append to `notes_parts` in the "allow" branch will not make it into the INSERT's `notes` column** — by then `notes` has already been snapshot into the local string.

**Fix:** The "allowing INSERT" A7 note must either (a) write to the already-composed `notes` string instead of `notes_parts`, or (b) re-join `notes_parts` after appending. Cleanest:
```python
notes = (notes or "") + f" [A7: existing #{existing['id']} at {existing_entry}, new entry {entry_price} differs by {price_diff_pct:.1f}% — allowing INSERT]"
```

This is a subtle ordering bug that will silently drop the A7 audit note from the genuine-new-position path.

---

### 🟡 MINOR-A7-7: Q-A7-1 (`ticker_only` inclusion) — current code semantics support INCLUDE

Plan recommends including `ticker_only` in the suppression set with monitoring. Cross-check against current code:

- `_process_update` (line 927): `ticker_only` returns `LOW_CONFIDENCE_UPDATE` **flag** — UPDATE still applied with caveat note. Does NOT refuse the update.
- `_process_closure` (line 1063): `ticker_only` **BLOCKS** the closure with `LOW_CONFIDENCE_CLOSURE` and does NOT close the position. Explicit refuse.

So the precedent for destructive/immutable actions (closure) is to **refuse** on `ticker_only`, and for lower-risk actions (update) is to **caveat and apply**. An INSERT is irreversible once committed (phantom trade) — by analogy with closure, the safer default is to suppress on `ticker_only`. **Plan's initial recommendation is consistent with code precedent. CONFIRMED.**

No change needed to plan §4c / §10. OinkV concurs with Forge's initial recommendation (INCLUDE ticker_only, monitor, tighten to `exact` only if false positives observed).

---

### 🟡 MINOR-A7-8: A4 (PARTIALLY_CLOSED) dependency handled cleanly, but A7 can ship BEFORE A4

Plan §5 Dependencies says "A4 (PARTIALLY_CLOSED — should ship first to include in status check)." Verification:
- `grep PARTIALLY_CLOSED` in canonical `micro-gate-v3.py`: **0 matches**. The status does not exist in code yet.
- `_match_active` WHERE clause: `status IN ('ACTIVE', 'PENDING')` at lines 384, 394, 410 (three copies — one in exact-trader, one in canonical-name, one in ticker-only fallback). ALL THREE need the PARTIALLY_CLOSED extension, not just one.
- Plan §3 shows only ONE clause change (`-- Current (line 291)` single match). This is ANOTHER stale-line-number artifact: the signal-gateway copy may have had fewer copies or they were at the same line range. In canonical, **all three must be updated**.

**Fix:** §3 SQL Changes must call out that three identical `WHERE s.status IN ('ACTIVE', 'PENDING')` clauses exist in `_match_active` and all three need extension when A4 ships.

Also: A7 does **not** strictly require A4 to ship first. If A7 lands with `('ACTIVE', 'PENDING')` and A4 lands later extending the set, A7 automatically inherits the extended match set because `_match_active` is shared. This is fine. The §5 "should ship first" framing is slightly stronger than necessary — it's a nice-to-have ordering, not a hard gate.

---

### 🟡 MINOR-A7-9: signal_router dedup location correct — but in a different repo than A7's target

Plan §1, §2, §4e reference `signal_router.py line 3591+` as a complementary layer. Verified in `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` line 3589 onwards (see `# ── Cross-channel active dedup ──` block, 3589-3639). ✅

Note this file lives in the **signal-gateway** repo (not oinkfarm), which means A7 (oinkfarm repo) is logically downstream of signal_router. Not a defect — the plan correctly identifies this as "complementary" — but worth flagging that the three layers (signal_router exact, micro-gate §4b exact, micro-gate A7 fuzzy) span two repos.

---

### 🟡 MINOR-A7-10: reconciler.py B10 flip-flop line range accurate

Plan §1 references `reconciler.py:141-166` for B10 flip-flop and `170-214` for entry-correction. Verified in `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py`:
- flip-flop suppression triggered at line 141-146 (the `_is_flipflop` helper sits at line 559+)
- entry correction detection at lines 175-214

✅ Close enough (plan says 141-166 which includes the surrounding UPDATE-build block).

---

## Drift Check: signal-gateway vs. `.openclaw/workspace`

Diff summary (`diff signal-gateway canonical`):
- signal-gateway: 1,063 lines, 47,073 bytes, Apr 15
- canonical: 1,407 lines, 61,460 bytes, Apr 19
- **344 new lines** in canonical vs. signal-gateway

Blocks added in canonical that signal-gateway does NOT have:
1. Event-store imports + `_get_event_store` + `_log_event` helpers (lines 36-78) — from commits `387a8a4d` (Event Store Phase 1) and `09e0f94b` (A1 commit=True fix)
2. `_payload_source_url`, `_payload_close_source_url` helpers (lines 279-292) — from commit `5974aa11`
3. `_quarantine` helper, `_log_rejection(conn=)` extension (lines 297-355) — from commit `387a8a4d`
4. A15 SL=entry overwrite guard in INSERT path (lines 739-780) — from commit `b526e38f`
5. A3 filled_at auto-populate (line 851-852) — from commit `3b5453b7`
6. SIGNAL_CREATED event emission at line 882 — from commit `387a8a4d`
7. Multiple other lifecycle `_log_event` calls in update/closure paths (lines 1026, 1031, 1104, 1183)

### A1 fix commit 498d8b28 touches ONLY event_store.py, NOT micro-gate

```
commit 498d8b28 fix(A1): add PRICE_ALERT to LIFECYCLE_EVENTS set
 scripts/event_store.py | 2 ++
 1 file changed, 2 insertions(+)
```

Does NOT affect any line A7 touches in micro-gate. **Zero conflict with A7.**

But commit `09e0f94b` (the actual A1 shipping commit on the oinkfarm side, parent of `498d8b28`) DID touch micro-gate at lines 61-78 — adding `commit=True` to `_log_event`. This is far (~560 lines) from A7's INSERT-path hook site. **Zero conflict with A7.**

### Drift verdict for FORGE to resolve

The plan's target file (§6 `Repo: bandtincorporated8/oinkfarm (micro-gate-v3.py)`) implicitly points to oinkfarm, which *is* the `.openclaw/workspace` canonical copy. So the target repo is right — only the line numbers are stale. **No repo-redirect needed** (unlike Wave-1 A1/A2 which had to redirect from kraken-sync to oink-sync). The drift is purely line-number drift caused by the plan being drafted against a snapshot that pre-dates 2026-04-19's A1 landing.

---

## Confirmed-Accurate Findings

### 🟢 CONFIRMED-A7-1: `_match_active()` logic is reusable as plan describes
Function returns `(signal_row_dict, confidence_string)` or `(None, reason)` with confidence values `"exact"`, `"ticker_only"`, `"ambiguous"`, `"no_match"`. Plan's usage at §4a (`existing, match_conf = _match_active(conn, trader_name_raw, ticker, direction, server_id)`) matches the real signature. ✅

### 🟢 CONFIRMED-A7-2: `existing.get("entry_price")` is present in returned dict
`_match_active` SELECT at lines 380, 390, 406 explicitly includes `s.entry_price`. The returned dict (via `dict(row)`) therefore has `"entry_price"` key. ✅

### 🟢 CONFIRMED-A7-3: The 5% threshold is new — no existing concept conflicts with it
Searched for price-comparison helpers: B11 SL deviation guard uses 100%, B10 price deviation uses 35% (entry vs market), A15 uses 0.1% (SL vs entry), order-type inference uses 2% and 10%/30% (MARKET vs LIMIT). No existing helper uses 5% for entry-to-entry comparison. The plan's 5% threshold is a fresh constant. ✅ (Recommend ANVIL define it as a module constant `_A7_ENTRY_TOLERANCE_PCT = 5.0` for testability.)

### 🟢 CONFIRMED-A7-4: ACTIVE/PENDING status semantics
Canonical `_match_active` restricts to `('ACTIVE', 'PENDING')` — these are the correct statuses for "live positions that could be UPDATE-subject-to." PARTIALLY_CLOSED is absent (A4 dependency, correctly flagged). `CLOSED*` variants and `CANCELLED` correctly excluded from the suppression set. ✅

### 🟢 CONFIRMED-A7-5: `_process_signal` is the INSERT path
Dispatch at line 599 routes SIGNAL → `_process_signal` (line 608). INSERT OR IGNORE at line 855. This is Financial Hotpath #6 per VIGIL's registry. ✅

### 🟢 CONFIRMED-A7-6: Test specification quality
All 9 test cases are well-shaped: each has concrete input, expected output, type, and priority. Coverage includes happy path, edge cases (opposite direction, no existing), A4 dependency, event-logged, rejection-logged, and the trader_id=None bypass. ✅ No changes needed to §5.

### 🟢 CONFIRMED-A7-7: Rollback plan is accurate
§7 correctly characterizes A7 as defensive-only (no data modification, no schema change). ✅

### 🟢 CONFIRMED-A7-8: Q-A7-1 initial recommendation matches code precedent
See MINOR-A7-7 above. Code precedent for destructive actions on `ticker_only` (closure at line 1063) is REFUSE. A7's analogous refuse-on-ticker_only is correct. ✅

---

## Summary Table

| Code | Severity | Area | Fix cost |
|---|---|---|---|
| STALE-A7-1 | 🔴 CRITICAL | All line numbers drift +90 to +270 | Mechanical — re-grep against canonical |
| STALE-A7-2 | 🔴 CRITICAL | Wrong import path `oink_sync.event_store` | 3-line swap → use module-level `_log_event` |
| STALE-A7-3 | 🔴 CRITICAL | `UPDATE_DETECTED` not in LIFECYCLE_EVENTS | Add 1 line to event_store.py §2 table |
| STALE-A7-4 | 🔴 CRITICAL | `_log_rejection` missing `conn=conn` | Add `conn=conn` kwarg to call |
| MINOR-A7-5 | 🟡 MINOR | §1 gap table misses existing §4b dedup | Acknowledge micro-gate already has exact-match layer |
| MINOR-A7-6 | 🟡 MINOR | `notes_parts` append after notes freeze | Restructure allow-branch to append to `notes` string |
| MINOR-A7-7 | 🟡 MINOR | Q-A7-1 grounding | Cite code precedent (closure line 1063) |
| MINOR-A7-8 | 🟡 MINOR | THREE status IN clauses, not one | A4-joint: update all three WHERE clauses |
| MINOR-A7-9 | 🟡 MINOR | Cross-repo layer note | Clarify signal_router is in signal-gateway repo |
| MINOR-A7-10 | 🟢 CONFIRMED | reconciler line ref 141-166 | accurate |
| CONFIRMED 1-8 | 🟢 | Core logic, reusability, thresholds, tests, rollback, Q-A7-1 | — |

---

## Final verdict

**A7 is implementable with 4 CRITICAL plan edits + 4 MINOR clarifications.** The **logic is correct**; this is not a "wrong target" audit (unlike Wave-1 A1/A2's kraken-sync misidentification). The plan was written against a Apr-15 snapshot of the target file; since then the canonical file has absorbed A1/A15/A3/event-store instrumentation, shifting every line citation. The Q-A7-1 recommendation to include `ticker_only` is well-grounded in existing code precedent (closure refuses on ticker_only).

**No A4-blocking issue.** A7 can ship before A4 and will automatically benefit from A4 when it lands, as long as both tasks edit the same three `status IN` clauses.

**No A1 conflict.** Commit `498d8b28` touches only event_store.py; commit `09e0f94b` touches micro-gate at line 61-78 (far from A7's hook site around line 840).

**FORGE action items before handing to ANVIL:**
1. Re-run `grep` against `.openclaw/workspace/scripts/micro-gate-v3.py` and fix every line number in §1, §2, §9.
2. Swap `from oink_sync.event_store import EventStore` + inline construction → single `_log_event(conn, "UPDATE_DETECTED", …)` call (helper already exists at line 61).
3. Add `scripts/event_store.py` to §2 "Files to Modify" with `UPDATE_DETECTED` addition to `LIFECYCLE_EVENTS` (and optionally `A7_UPDATE_DETECTED` to `QUARANTINE_CODES`).
4. Patch §4a `_log_rejection(...)` call to include `conn=conn`.
5. Restructure the "allow INSERT" branch to append to `notes` string (not `notes_parts` which has already been joined).
6. In §3, clarify that `_match_active` has **three** `WHERE s.status IN ('ACTIVE','PENDING')` clauses, not one — all three need PARTIALLY_CLOSED when A4 ships.
7. (Optional) Add a module constant `_A7_ENTRY_TOLERANCE_PCT = 5.0` recommendation to §4b.

*OinkV 👁️🐷 — "Line numbers drift, logic holds."*
