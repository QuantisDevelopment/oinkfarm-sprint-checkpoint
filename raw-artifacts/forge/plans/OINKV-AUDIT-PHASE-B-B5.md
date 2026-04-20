# OinkV Engineering Audit — FORGE Plan B5 (Hermes fallback)

**Auditor:** Hermes Agent (Hermes-subagent fallback; OinkV main lane LLM-timed-out at 2026-04-20T04:38 CEST, FailoverError after 306s)
**Date:** 2026-04-20 04:58 CEST
**Scope:** `TASK-B5-plan.md` — signal_router.py God Object decomposition, Phase 1 (emitter extraction)
**Tier:** 🟡 STANDARD — code refactor, no schema/data changes, single-repo blast radius (signal-gateway)

---

## 0. Audit Header

| Item | Value |
|------|-------|
| Plan under review | `/home/oinkv/forge-workspace/plans/TASK-B5-plan.md` |
| Size | 11,258 bytes |
| mtime (plan) | 2026-04-19 18:08 CEST |
| Line count | 247 |
| Canonical target | `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` |
| Live signal_router.py LOC | **4,451** (plan claims 4,460 — drifted by -9 via B3 ghost-closure merge) |
| Live signal-gateway HEAD | **`cc70e5b`** *Merge B3: Re-vendor oink_db.py + ghost closure fix* |
| Plan-cited HEAD | `c6cb99e` — **STALE** (pre-B3) |
| Prior audit template | `OINKV-AUDIT-PHASE-B-B3-v2.md` (format mirror) |

⚠️ **Provenance note:** Plan drafted 2026-04-19 18:08 CEST; signal-gateway B3 merged 2026-04-20 04:24. Every line number in the plan is from a pre-B3 snapshot. B3's diff is very small (9 LOC net deletion, all in the A6 GHOST_CLOSURE block around line 3972) so drift on the emitter-relevant regions is ≤3 lines.

---

## 1. Summary

| Severity | Count |
|----------|------:|
| 🔴 SHOWSTOPPER | 0 |
| 🔴 CRITICAL | 2 |
| 🟡 MAJOR | 3 |
| 🟠 MINOR | 5 |
| ✅ CONFIRMED | 7 |

### Verdict

**🟡 MINOR-REVISION** — The plan is architecturally sound and cites the correct canonical path, but the §1 current-state inventory contains **one phantom method name** (`_forward_raw_to_signals`, which does not exist — the real function is `_route_passthrough` at line 2035), a **3× LOC undercount** for `oinxtractor_client.py` (plan says ~150, actual 479), and a **structurally narrow emitter API** that doesn't cover the ~37 live `self._fire_and_forget(self._notifier.*)` dispatch sites which span 5 notifier methods (`notify_signal`, `notify_telegram`, `post_raw_feed`, `notify_alert_signal`, `notify_reconciler_action`, `log_pipeline_event`) — the plan's `emit_signal/emit_lifecycle/emit_raw` trinity maps cleanly to only 3 of those 6. These are correctable in a v2 pass without rearchitecting.

### Headline

> Plan correctly identifies emitter as the cleanest extraction target and correctly states the dependency direction (`router → emitter → discord_notify`, one-way). But it misreads the current delivery architecture: **all HTTP webhook POSTs already live in discord_notify.py**, not in signal_router.py. The ~37 emitter-ish call sites in signal_router.py are thin wrappers (`self._fire_and_forget(self._notifier.X(...))`), so the claimed "400-600 LOC savings" is almost certainly an overestimate (realistic: 150-250 LOC). The pre-emit filter ownership split in §4d also has an ordering bug: `_should_suppress_lifecycle` calls `_check_signal_state`, so moving the former to emitter while keeping the latter in router inverts the declared one-way dependency.

---

## 2. Critical Findings

### C1 — Phantom function name `_forward_raw_to_signals()`

**Plan §1 row 3:**
> `_forward_raw_to_signals()` | ~2036+ | Raw message forwarding to #signals webhook

**Live code (signal_router.py):**
- `grep -n "_forward_raw_to_signals" signal_router.py` → **0 hits**
- `grep -n "def.*forward" signal_router.py` → **0 hits**
- The method at line **2035** is `async def _route_passthrough(self, event: dict[str, Any])`. Its docstring says *"Forward raw message straight to #signals webhook. No extraction, no gate."*

The plan author clearly paraphrased the docstring as the function name. Line number ~2036 is correct (docstring is on line 2036 of the pre-B3 snapshot, line 2036 live too — the function def is on 2035), but the **method name does not exist**.

**Impact:** ANVIL following the plan literally will grep for `_forward_raw_to_signals`, get zero hits, and have to redo the discovery work. This is the same class of failure as B3-v1's phantom `_close_signal()` and `_scan_once()`.

**Fix:** Rename the row to `_route_passthrough()` at line **2035** (docstring mentions raw-forward behaviour; actual delivery calls are at lines 2380 `notify_signal`, 2395 `post_raw_feed`, 2402 `log_pipeline_event`).

---

### C2 — Emitter API trinity undercounts real notifier surface

**Plan §4a** proposes:
```python
class SignalEmitter:
    async def emit_signal(...)     # webhook + telegram + discord
    async def emit_lifecycle(...)  # SL/TP/closure
    async def emit_raw(...)        # raw #signals forward
```

**Live delivery inventory (grep `self._fire_and_forget(self._notifier` in signal_router.py):**
- **37 total call sites** to `self._notifier.*`, covering **6 distinct notifier methods**:

| Notifier method | Call-site count | Purpose | Plan's emit_* mapping |
|-----------------|----------------:|---------|-----------------------|
| `notify_signal` | 5 | Signal extraction → #signals webhook | ✅ `emit_signal` |
| `notify_telegram` | 1 | Telegram channel signal post | ✅ `emit_signal` (sub-step) |
| `post_raw_feed` | 5 | Raw message → #raw-feed audit | ✅ `emit_raw` |
| `notify_alert_signal` | 1 | WG active-alerts channel delivery | ❌ **UNMAPPED** |
| `notify_reconciler_action` | 1 | Board reconciler lifecycle delivery | ❌ **UNMAPPED** |
| `log_pipeline_event` | **24** | Pipeline audit/metrics breadcrumb | ❌ **UNMAPPED** |

`log_pipeline_event` alone accounts for **65% of all notifier calls** (24/37) and is not mentioned anywhere in the plan's emitter API sketch. `notify_alert_signal` (line 2576) and `notify_reconciler_action` (line 2676) are also live and are not covered by the `emit_signal / emit_lifecycle / emit_raw` trinity.

**Impact:** Either (a) the emitter's public API grows a 4th method (`emit_pipeline_event`) plus two more (`emit_alert_signal`, `emit_reconciler_action`), or (b) the emitter exposes `notifier` as a passthrough, in which case the "encapsulation" claim in §4c is hollow. Plan must pick one and document it.

**Fix options:**
- **Option 1 (clean):** Expand the API to `emit_signal / emit_lifecycle / emit_raw / emit_alert / emit_reconciler / emit_pipeline_event`. Then the 37 sites map cleanly.
- **Option 2 (pragmatic):** State explicitly that `emit_pipeline_event` and `emit_alert / emit_reconciler` are part of the first-cut API. The plan §4a already has placeholder signatures; adding 3 more entries costs 10 lines of plan doc.

This is blocking because VIGIL will flag "API surface does not cover call-site inventory" in code review.

---

## 3. Major Findings

### M1 — `oinxtractor_client.py` LOC undercounted 3×

**Plan §1 module table:**
> `oinxtractor_client.py` | ~150 | Oinxtractor API client | Already separate

**Live:**
```
$ wc -l /home/oinkv/signal-gateway/scripts/signal_gateway/oinxtractor_client.py
479
```

Plan states ~150; live file is **479 LOC** — ~3.2× the claim. This doesn't affect the emitter extraction itself, but it's a factual error in the "current state analysis" table and it weakens the §10 Evidence block which footnotes "Files read" with this module.

**Disposition:** Non-blocking for the extraction, but correct the §1 table. The total "already-extracted" LOC figure in §10 ("~1,955 LOC already extracted") should be recomputed: 512 + 352 + 1,091 + 479 = **2,434 LOC** already out of the God Object, not 1,955.

---

### M2 — Pre-emit filter ownership split inverts declared dependency direction

**Plan §4d:**
> - `_check_signal_state()` — queries DB for existing active position → **stays in router**
> - `_should_suppress_lifecycle()` — decides if lifecycle event is noise → **move to emitter**

**Live code (signal_router.py line 1571):**
```python
def _should_suppress_lifecycle(self, trader, ticker, action_type, *, message_id=""):
    ...
    state = self._check_signal_state(trader, ticker)   # ← CALLS THE ROUTER METHOD
```

If `_should_suppress_lifecycle` moves to `emitter.py` and `_check_signal_state` stays in `signal_router.py`, then:
- `emitter.py` calls back into `signal_router.py` to run the state check
- This violates the plan's own §8 risk mitigation: *"Clean dependency direction: router → emitter, never reverse"*

**Impact:** Either the emitter imports `SignalRouter` (circular import risk → the exact risk §8 row 3 tries to mitigate), or the emitter takes a `state_provider: Callable` injection, or `_check_signal_state` ALSO moves to the emitter. The plan does not discuss any of these options.

**Fix (recommended):** Move `_check_signal_state` to the emitter too. It's purely a DB read against `signals`/`traders`, has its own 60s TTL cache (`_signal_state_cache`), and is used only by `_should_suppress_lifecycle`. No router logic depends on it.

Alternative: Pass state as a callback via `EmitterConfig`. More complex, but preserves the "routing decision stays in router" boundary the plan articulates.

Either way, §4d needs a concrete answer.

---

### M3 — LOC savings estimate (400-600) inconsistent with live distribution

**Plan §0 / §6 acceptance criterion 1:**
> signal_router.py reduced by 400-600 LOC (from 4,460 to ~3,900-4,060)

**Observation:** The existing delivery code in `signal_router.py` is not a large self-contained block — it's **37 thin wrapper calls** to `self._notifier.*` interleaved with routing logic. Each wrapper is ~8-15 lines including kwargs. Extracting them to an emitter wrapper doesn't *delete* lines; it *replaces N-line blocks with M-line calls to `self._emitter.X()`*, where M ≈ N (same kwargs must still be assembled).

Realistic line savings:
- Move `_fire_and_forget` (~18 lines) → emitter
- Move `_mark_forwarded` / `_is_recently_forwarded` (~26 lines) → emitter
- Move `_should_suppress_lifecycle` / `_check_signal_state` / `_classify_lifecycle_action` (~115 lines) → emitter
- Move `_forwarded_signals` + `_signal_state_cache` + `_lifecycle_sent` fields (~20 lines of dataclass fields) → emitter
- Replace 37 call sites with pass-through calls: **net-zero** (same kwargs)

Expected net reduction: **~180-220 LOC**, not 400-600. Plan's acceptance criterion is likely unachievable without also moving parser-adjacent code (scope creep into B6/B7 territory).

**Fix:** Relax §6 criterion 1 to "reduced by 150-250 LOC" OR rescope to include moving additional ownership. Do NOT paper this over in the plan — VIGIL will measure the delta against the stated target and fail the PR if it's 200 LOC when the plan promises 500.

---

## 4. Minor Findings

### Min1 — `_fire_and_forget()` line drift 1422→1424 (+2)

Plan: 1422-1438. Live: **1424-1441**. Drift +2. Cosmetic. Within ±10 tolerance.

### Min2 — `_mark_forwarded()` / `_is_recently_forwarded()` line drift 1464→1466 (+2)

Plan: 1464-1490. Live: **1466-1491**. Drift +2. Cosmetic.

### Min3 — Pre-emit filter range drift 1297-1615 → 1299-1614

Plan: 1297-1615. Live: _forwarded_signals field at **1295-1297**, `_mark_forwarded` at **1466**, `_is_recently_forwarded` at **1482**, `_check_signal_state` at **1495**, `_should_suppress_lifecycle` at **1544**, `_classify_lifecycle_action` at **1617** (static). Plan's range is essentially right — the block is **1295-1656**, ~320 LOC. Plan understates by ~50 lines on the upper end.

### Min4 — "Webhook POST blocks | scattered (~6 sites)" misdescribes architecture

Plan §1 row 4:
> Webhook POST blocks | scattered (~6 sites) | HTTP webhook delivery to OinkDB/micro-gate

Live `grep "aiohttp\|httpx\|\.post(" signal_router.py`:
- **All `self._notifier.*` calls** are the webhook delivery (discord_notify.py owns the POSTs)
- **Only direct aiohttp.post in signal_router.py**: `_social_session.post()` at line 2751 for **social-listener ingest** (NOT the OinkDB/micro-gate webhook)
- `_oinkdb_session` at line 2850 is a **GET session** for oinkdb read queries — not a POST

So there are **0 direct HTTP webhook POSTs to OinkDB/micro-gate in signal_router.py**. They all go through `DiscordNotifier`. Plan's "~6 sites" is incorrect but the emitter extraction still works — it just means the emitter *wraps* the notifier rather than *contains* the webhook code. This is already implied by §6 criterion 5 ("discord_notify.py unchanged — emitter wraps it").

**Fix:** Replace the row with "Notifier dispatch call sites (37 in total via `self._fire_and_forget(self._notifier.X)`)".

### Min5 — Plan-cited `c6cb99e` is stale HEAD

Plan §Header: `HEAD c6cb99e`. Live HEAD: **`cc70e5b`** (B3 merged). Expected drift given plan pre-dates B3 by ~10 hours. Recommend plan §Header update to `cc70e5b` and a 1-line mention in §0 that B3's ghost-closure fix (line 3972, `connect()` replaces `connect_readonly()`) has landed and is **disjoint** from the emitter extraction region (lines 1424-1656 + 37 call sites).

---

## 5. Confirmed (spot-checks that passed)

| Item | Plan claim | Live verification | Result |
|------|------------|-------------------|--------|
| Canonical path | `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` | Exists; 4,451 LOC; 211,148 B; mtime 2026-04-20 04:24 | ✅ |
| `_fire_and_forget` exists | Line 1422-1438 | `def _fire_and_forget(self, coro) -> None` at line **1424**, body 1424-1441 | ✅ EXACT (±2 lines) |
| `_mark_forwarded` exists | Line 1464-1490 | `def _mark_forwarded(self, trader, ticker, direction, entry)` at line **1466**, body 1466-1480 | ✅ EXACT (±2) |
| `_is_recently_forwarded` exists | Line 1464-1490 | `def _is_recently_forwarded(...)` at line **1482**, body 1482-1491 | ✅ EXACT (±2) |
| `extractor.py` LOC | 512 | `wc -l` → **512** | ✅ EXACT |
| `board_parser.py` LOC | 352 | `wc -l` → **352** | ✅ EXACT |
| `discord_notify.py` LOC | 1,091 | `wc -l` → **1,091** | ✅ EXACT |
| Dependency direction stated | `router → emitter → discord_notify`, no cycles | §8 risk row 3 + §6 criterion 6 | ✅ STATED (but see M2 for violation in §4d) |
| `DiscordNotifier` import site | `from .discord_notify import DiscordNotifier` | Line **235** | ✅ |
| Forwarded-cache dedup semantics | TTL 300s, `(trader, ticker, direction, entry)` key | Line 1297: `_FORWARDED_TTL: float = 300.0`; key at line 1468: `(trader.lower(), ticker.upper(), direction.upper(), f"{entry:.10g}")` | ✅ EXACT |
| B3 ghost-closure fix disjoint region | Implied disjoint (plan silent on B3) | B3 fix at line **3972** in `_route_board_update` body; emitter region is 1297-1656 + call sites | ✅ Disjoint (but plan should acknowledge B3 has landed) |

---

## 6. Phantom / Missing Reference Scan

### Phantoms (plan cites, code doesn't have)

| Plan reference | Live status | Severity |
|---------------|-------------|----------|
| `_forward_raw_to_signals()` | **Does not exist** — real name is `_route_passthrough` @ 2035 | 🔴 C1 |
| "~6 webhook POST blocks in signal_router.py" | 0 direct POSTs to OinkDB/micro-gate in router; all via DiscordNotifier | 🟠 Min4 |

### Missed (code has, plan would need to address but ignores)

| Live reference | Coverage status in plan | Severity |
|---------------|-------------------------|----------|
| `self._notifier.log_pipeline_event()` ×24 sites | Not in `emit_signal/emit_lifecycle/emit_raw` API | 🔴 C2 |
| `self._notifier.notify_alert_signal()` (line 2576) | Not in plan's API | 🔴 C2 |
| `self._notifier.notify_reconciler_action()` (line 2676) | Not in plan's API | 🔴 C2 |
| `_check_signal_state` → `_should_suppress_lifecycle` call dependency | §4d splits them across modules without bridging | 🟡 M2 |
| `_trader_hints` / `_trader_hints_mtime` state (lines 1311-1314) | Not covered — stays in router (correct but plan is silent) | 🟢 |
| Social-listener ingest (line 2744, `_social_session.post`) | Not mentioned — should stay in router (this IS a webhook POST but it's ingest-out, not signal-out) | 🟢 (by design) |

---

## 7. Test Coverage Adequacy

Plan §5 lists 8 tests. Checked against the 4 failure modes from the task prompt:

| Failure mode | Covered? | Notes |
|--------------|---------|-------|
| Webhook failure (HTTP 500, connection reset) | ❌ | `test_emit_signal_webhook` tests the happy path only |
| Telegram timeout | ❌ | `test_emit_signal_telegram` doesn't specify timeout behaviour |
| Discord 429 rate limit | ❌ | Not in the test list |
| Dedup bridge (`_mark_forwarded` → `_is_recently_forwarded`) | ✅ | `test_recently_forwarded` + `test_forwarded_cache_expiry` |

**Gap:** None of the listed tests exercise the failure/timeout/rate-limit paths. `discord_notify.py` already has retry/rate-limit handling internally (check `tests/test_discord_notify_lifecycle_jsonl.py`), so a thin emitter wrapper may only need to test "emitter passes errors through without swallowing" and "fire-and-forget logs rather than raises" (which `test_emitter_fire_and_forget` *does* cover ✅).

**Disposition:** Add at minimum `test_emit_signal_webhook_failure` and `test_emit_signal_telegram_timeout` to §5. Discord 429 is arguably discord_notify.py's responsibility (emitter just sees an exception). Non-blocking but recommended.

---

## 8. B3 Interaction Analysis

Plan pre-dates B3's merge (plan: 2026-04-19 18:08 CEST; B3 merged: 2026-04-20 04:24 CEST). The B3 fix replaces `connect_readonly()` with `connect()` at signal_router.py line **3972** inside the `_route_board_update` A6 GHOST_CLOSURE block.

**Region disjoint-ness verified:**
- Emitter extraction scope: lines 1295-1656 (filter + dedup + forward helpers) + 37 scattered call sites (mostly 2013-3776)
- B3 fix scope: line 3972 (`with connect(timeout=2) as _a6conn:`) inside `_route_board_update` at line 3795

Regions do not overlap. **B5 can proceed without touching B3's fix.**

However, the plan §0 executive summary should be updated to acknowledge B3 has landed (one-line footnote) so ANVIL doesn't rebase confusion. This is Min5.

**Note:** `connect_readonly` is still used at lines 1518, 2235, 2310, 3058, 3600, 3899 (6 more sites). These are DB reads — correct usage. The fix at 3972 was specifically for a block that writes to `signal_events` / `signals`, which required write capability. Not an emitter concern.

---

## 9. Dependency Graph Verification

**Plan claim (§6 criterion 6):**
> Import graph is clean: `signal_router → emitter → discord_notify` (no circular dependencies)

**After extraction, expected imports:**
- `emitter.py` will need to import: `DiscordNotifier` (from `discord_notify`), `OinkConnection`/`connect_readonly` (from `scripts.oink_db`), possibly `RouterConfig` or a subset-config
- `signal_router.py` will need to import: `SignalEmitter` (new)
- `discord_notify.py` must NOT import `emitter.py` — ✅ straightforward, it's already stable

**Risk: emitter.py → scripts.oink_db (for `_check_signal_state`)**

If M2's recommendation is followed and `_check_signal_state` moves to emitter, then `emitter.py` will import `from scripts.oink_db import connect_readonly`. This is identical to signal_router.py's current import at line 30 — no cycle risk, just an additional consumer. The re-vendored `oink_db.py` at `/home/oinkv/signal-gateway/scripts/oink_db.py` (B3 re-vendoring) is stable and this will not trigger any re-vendor work.

**Verdict:** Import graph is implementable cleanly IF M2 is addressed. If M2 is ignored (emitter imports SignalRouter), it becomes a circular-import risk. Current plan implicitly depends on resolving M2.

---

## 10. Residual Risks (informational)

These do not block ship-readiness but ANVIL should keep them in implementation view:

1. **State lifecycle** — emitter owns `_forwarded_signals`, `_lifecycle_sent`, `_signal_state_cache`, `_forwarded_signals_order`. Persistence across restarts must be preserved. Currently the router's `persist_state()` (line 2007 et al.) writes out router state; emitter state needs either its own persistence or a router→emitter handoff in `persist_state()`. Plan is silent on this.

2. **`_fire_and_forget` semaphore ownership** — the bounded-concurrency semaphore `_bg_semaphore: asyncio.Semaphore(5)` (initialized in `__post_init__` line 1317) is shared by *all* router background tasks, including non-emitter ones. Moving `_fire_and_forget` wholesale to emitter either (a) splits into two semaphores (different concurrency budgets — behavioural change) or (b) shares the semaphore (emitter constructor takes it as an arg). Plan §4a constructor signature does not mention this.

3. **`post_raw_feed` audit trail** — `#raw-feed` forwards (5 sites) are an audit requirement, not a user notification. If emitter routes them through `emit_raw`, ensure the "fire-and-forget with error logging" semantics are preserved so an audit-feed outage doesn't break signal delivery.

4. **Relation to Redis Streams (§9 Q-B5-2)** — Plan correctly defers Redis service-boundary work. No action now; flagged for Mike.

---

## 11. Audit Finding Disposition

| ID | Severity | Issue | Suggested Fix |
|----|----------|-------|---------------|
| **C1** | 🔴 CRITICAL | Phantom `_forward_raw_to_signals()` | Rename to `_route_passthrough()` at line 2035 in §1 |
| **C2** | 🔴 CRITICAL | Emitter API misses 24 log_pipeline_event + 2 other notifier methods | Expand API to 6 emit_* methods OR document passthrough |
| **M1** | 🟡 MAJOR | oinxtractor_client.py LOC 150 vs live 479 | Update §1 table and §10 "already extracted" math |
| **M2** | 🟡 MAJOR | §4d splits `_check_signal_state` / `_should_suppress_lifecycle` across modules | Move both to emitter, or add state-provider callback |
| **M3** | 🟡 MAJOR | "400-600 LOC savings" likely overestimated (realistic 150-250) | Relax §6 criterion 1 to "150-250 LOC" |
| **Min1** | 🟠 MINOR | Line drift `_fire_and_forget` +2 | Update 1422→1424 in §1 |
| **Min2** | 🟠 MINOR | Line drift `_mark_forwarded`/`_is_recently_forwarded` +2 | Update 1464→1466 |
| **Min3** | 🟠 MINOR | Pre-emit filter range 1297-1615 vs live 1295-1656 | Non-blocking; cosmetic |
| **Min4** | 🟠 MINOR | "~6 webhook POST blocks" mischaracterizes architecture | Reword as "37 notifier dispatch sites" |
| **Min5** | 🟠 MINOR | Stale HEAD `c6cb99e` | Update to `cc70e5b`; add 1-line B3-disjoint note in §0 |

No SHOWSTOPPERs — the plan's canonical path is correct, the dependency direction is correctly declared, B3 is disjoint, and the extraction target is the right first choice for decomposition.

---

## 12. Verdict

### 🟡 MINOR-REVISION

**Rationale:**
- **Canonical path is correct** (B3-audit taught us to verify this first; plan §Header passes).
- **Dependency direction is correct** (§6 criterion 6 + §8 risk row 3), modulo M2's internal inconsistency.
- **B3 is disjoint** from emitter extraction region — B5 can land without touching B3's fix.
- **C1 (phantom function name)** is a v2-fix: 1-line correction. Without this, ANVIL will waste 30min on a grep that returns zero.
- **C2 (emitter API trinity)** is a v2-fix: expand §4a to 6 emit_* methods OR document passthrough. Without this, VIGIL will flag API/call-site mismatch.
- **M1/M2/M3** are plan-hygiene corrections — not architectural rewrites. All three are 1-2 paragraph edits.
- Line drifts (Min1/Min2/Min3) are all ≤3 lines — within the ±10 tolerance I used on B3-v2. Cosmetic.

**Recommendation for Mike:**
Route back to FORGE for a v2 revision addressing C1 + C2 + M1 + M2 + M3. Expect ~2-3 paragraphs of net plan additions and 5-6 line-number corrections. Do **not** escalate to REWRITE — the core decomposition strategy is sound, the canonical path is correct, and the risk assessment is reasonable.

After v2: expect a clean ✅ SHIP-READY audit in the same format as B3-v2.

**Alternative fast-track:** If the team wants to ship B5 without a full FORGE revision loop, ANVIL can self-correct C1 (grep reveals the real name in 30 seconds) and C2 (by reading the notifier API and expanding `emit_*` accordingly). VIGIL review then catches any residual gaps. This is the cost/risk trade-off for Mike to decide.

---

*Audit complete. Hermes Agent fallback, 2026-04-20 04:58 CEST.*
*Provenance: OinkV main lane LLM-timed-out 04:38 CEST today (FailoverError after 306s). Dispatched per `/home/oinkv/.hermes/skills/devops/oinkfarm-sprint-orchestrator/SKILL.md` "Hermes-Subagent Fallback" pattern.*
*Evidence: signal-gateway HEAD `cc70e5b` (post-B3 merge); signal_router.py 4,451 LOC verified via `wc -l`; 37 notifier dispatch sites verified via `grep -c "self\._fire_and_forget(self\._notifier"`; phantom `_forward_raw_to_signals` confirmed absent via `grep -n "_forward_raw_to_signals"` → 0 hits.*
