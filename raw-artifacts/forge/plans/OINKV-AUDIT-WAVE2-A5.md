# OINKV Staleness Audit — TASK-A5-plan.md

**Task:** A5 — Map `extraction_method` (notes) to `confidence` score in micro-gate
**Tier:** 🟡 STANDARD
**Base commit:** signal-gateway `38eb8e8` (verified `38eb8e8799f237bdc907e87e5044135a1f117023`)
**Auditor:** Hermes Agent (fallback — OinkV dispatch hit FailoverError LLM timeout)
**Audit date:** 2026-04-19
**Plan version audited:** 1.0

---

## Summary Verdict

**OVERALL: ⚠️ APPROVE WITH REVISIONS REQUIRED**

The plan's core design (map `extraction_method` → `confidence` via a `PARSER_CONFIDENCE_MAP`) is sound, and the SQL schema claim is fully verified. However, the plan has two significant drifts from current code:

1. **Line-number references and the "canonical" source file disagree.** Plan cites `signal-gateway/scripts/micro-gate-v3.py` line numbers (573–576, 250, 597). The task context explicitly names `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (61460 bytes, 1407 lines) as canonical; the signal-gateway copy is 47073 bytes / 1063 lines and is *older / differently shaped*. ANVIL must be told which file is the target.
2. **The `PARSER_CONFIDENCE_MAP` keys do not match the `extraction_method` values actually written by production code.** Three of the six keys (`board_reconciler`, `oinkdb_opus`, `manual`) are **not produced anywhere in the signal-gateway source tree**, while four extraction_method values that **are** actively produced (`telegram_direct`, `oinxtractor_agent`, `inline_fallback`, `qwen_v3`) are **missing from the map**.

These are the CRITICAL issues. Everything else is CONFIRMED or MINOR.

---

## Findings

### CRITICAL — C1: Canonical-file ambiguity (two micro-gate copies on disk, with different line numbers)

- Task context specifies canonical: `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` — **61460 bytes, 1407 lines**.
- Plan §2 and §4b quote line numbers from `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` — **47073 bytes, 1063 lines** at commit `38eb8e8`.
- Verified line numbers:

| Plan citation | signal-gateway (plan's implicit target) | .openclaw/workspace (task's stated canonical) |
|---|---|---|
| Confidence normalization "lines 573–576" | ✅ lines 573–576 match | ❌ actual lines **797–801** |
| `_log_rejection` extraction_method "line 250" | ✅ line 250 matches | ❌ actual line **314** |
| notes `[extracted: method]` "line 597" | ✅ line 597 matches | ❌ actual lines **822–823** |

The `.openclaw/workspace` copy has an additional ~344 lines including an `EventStore` import block (lines 36–63), quarantine helper (`_quarantine`, lines ~326+), `_log_event` wrapper, and `_payload_source_url` / `_payload_close_source_url` helpers. This is the file ANVIL touches for A5 per the task contract, but the plan's patch location instructions will be **off by ~220–230 lines** against it.

**Action for ANVIL:** Treat all "line NNN" references in TASK-A5-plan.md §1, §2, §4 as nominal; use the *markers* ("after `_safe_float(ext.get(\"confidence\"), 0.8)` block", "after `method = entry.get(\"extraction_method\", \"unknown\")`") rather than absolute line numbers. The structural logic (confidence normalization block exists; method tag is written to notes) is confirmed in both copies.

**Also note:** Plan §2 says "signal-gateway repo … commit `38eb8e879` is the verified HEAD" — HEAD of signal-gateway is `38eb8e8799f237bdc907e87e5044135a1f117023`, so `38eb8e8` / `38eb8e879` matches. But the canonical file for the change lives in `.openclaw/workspace/scripts/`, which is not tracked by that repo. If A5 must ship in both copies, the plan should say so explicitly (it does not).

---

### CRITICAL — C2: `PARSER_CONFIDENCE_MAP` keys are not the extraction_method values the code actually produces

All `extraction_method = "…"` assignments grepped across the signal-gateway repo and `.openclaw/workspace/scripts/`:

| extraction_method value | Where it's set | In plan's map? |
|---|---|---|
| `cornix_regex` | `signal_router.py:3043` | ✅ (0.95) |
| `chroma_regex` | `signal_router.py:3191` | ✅ (0.90) |
| `llm_nl` | `signal_router.py:3407` | ✅ (0.70) |
| `telegram_direct` | `signal_router.py:2000` | ❌ **missing** |
| `oinxtractor_agent` | `signal_router.py:3297`, `oinxtractor_client.py:190` | ❌ **missing** |
| `inline_fallback` | `signal_router.py:3272` (default before override) | ❌ **missing** |
| `qwen_v3` | `.openclaw/workspace/scripts/signal-extract-v3.py:492` | ❌ **missing** |
| `board_reconciler` | _not found in any current .py file_ | ✅ (0.90) — **phantom** |
| `oinkdb_opus` | _not found in any current .py file_ | ✅ (0.85) — **phantom** |
| `manual` | _not found in any current .py file_ | ✅ (0.95) — **phantom** |

Historical/legacy values observable in DB notes and JSONL payloads but **not emitted by current code**: `text_qwen_nl_v5` (renamed to `llm_nl` in commit `9fa2d19`, retained as back-compat *display key* only — not a current producer), `text_oinxtractor_agent` (same — display-only back-compat in `discord_notify.py`), `wg_reconciler`, `board_embed_new_signal`, `board_embed`, `board_vision`, `dom_text`, `dom_image_download`, `mtproto_text`.

Several of the "Known Parser Types in Production" rows in plan §1 are not grounded in current source:

- **`board_reconciler`** — The docstring `board_parser.py` exists with `parse_board_embed()`, but it does NOT set `extraction_method` to `board_reconciler` anywhere in `signal-gateway/scripts/`. Grep returns zero hits for the literal string `board_reconciler` in any Python file under `/home/oinkv`. It appears only in tmp-queue JSON fixtures (`.openclaw/workspace/status/tmp-insert-*.json`) as `"wg_reconciler"` (different spelling) and in git commit messages.
- **`oinkdb_opus`** — No producer in any Python file under `/home/oinkv`.
- **`manual`** — No producer as an `extraction_method` value in any Python file under `/home/oinkv`. Manual-entry paths exist in other contexts, but they don't set `extraction_method = "manual"`.

Conversely, the **top active producer** of extraction_method values — `oinxtractor_agent` (Qwen 35B image-first chart extraction) — is the most common LLM path in current production but is **absent from the plan's map**. FORGE recommended 0.70 for `llm_nl` based on LLM hallucination risk; applying the same logic to `oinxtractor_agent` is non-obvious (image-based extraction has different failure modes than text-NL extraction), and the plan gives no guidance for this value. Likewise `telegram_direct` (MTProto-direct, structurally reliable) would plausibly warrant 0.90+ but is unmapped; it will fall through to the default `0.8` after A5 ships, which is effectively a no-op for that code path.

**Action for ANVIL / Mike:**
- Drop `board_reconciler`, `oinkdb_opus`, `manual` from the map (or escalate to Mike — these may be *aspirational* values for not-yet-implemented parsers referenced in Arbiter-Oink Phase 4 §3; in that case the plan should say "future parser, wired to the map pre-emptively" explicitly).
- Add `oinxtractor_agent` (FORGE-recommend 0.80–0.85 given image-LLM risk profile vs. text-only `llm_nl=0.70`), `telegram_direct` (≥0.90), `inline_fallback` (likely 0.70 — the name suggests a less-reliable path), and if the `.openclaw` canonical is the target, `qwen_v3` (0.70 — same tier as `llm_nl`).
- At minimum, ANVIL should defer the key-selection question to Mike; the map rows in plan §4a are not code-verified for three of six entries.

---

### CONFIRMED — CF1: `signals.confidence` column shape

Plan quotes:
```
17|confidence|FLOAT|1|0.8|0
```

Verified against `/home/oinkv/oinkfarm/data/oinkfarm.db` (production-shape db — other location `/home/oinkv/oink-sync/oink.db` is 0-byte on this host):
```
17|confidence|FLOAT|1|0.8|0
```
Exact match: column index 17, type FLOAT, NOT NULL, default 0.8. ✅

### CONFIRMED — CF2: Current confidence distribution in DB

Actual query result (plan §1 predicts "most signals at 0.8 — legacy default in effect"):
```
0.8   → 489 signals
0.85  → 2 signals
0.9   → 1 signal
```
Plan's prediction is accurate (99.4% of rows are exactly 0.8). ✅

### CONFIRMED — CF3: `_safe_float(ext.get("confidence"), 0.8)` logic and `> 1.0 / 10.0` normalization

Both `.openclaw/workspace` (line 798–801) and `signal-gateway` (line 573–576) copies have identical logic:
```python
confidence = _safe_float(ext.get("confidence"), 0.8)
if confidence > 1.0:
    confidence = round(confidence / 10.0, 2)
confidence = max(0.0, min(1.0, confidence))
```
✅ Plan's characterization and recommended "capture whether extractor supplied explicit None" pattern (§4b, Option 1) is correct and safe.

### CONFIRMED — CF4: `extraction_method` is on `entry`, not on `ext`

Plan §1 note "`extraction_method` is already read from the `entry` dict (top-level, not nested in `ext`)" — verified:
- `_log_rejection`: `entry.get("extraction_method")` (signal-gateway:250 / .openclaw:314) ✅
- notes tag: `entry.get("extraction_method", "unknown")` (signal-gateway:597 / .openclaw:822) ✅

### CONFIRMED — CF5: No downstream `confidence` consumers that would break

Grep across `/home/oinkv/signal-gateway` and `/home/oinkv/.openclaw/workspace/scripts`:
- `oink-sync/oink_sync/lifecycle.py`: **0** hits for `confidence` or `extraction_method`. ✅ (Plan's §9 Evidence claim verified.)
- `oink-sync/oink_sync/` overall: **0** hits for either symbol.
- `.openclaw/workspace/scripts/trader_commentary.py` + `trader_score.py`: the `confidence` references are a different concept (Bayesian sample-size confidence in `trader_score` / `TraderScore.confidence`), **unrelated** to `signals.confidence`. No consumer reads `signals.confidence` for scoring or PnL.
- `signal-gateway/scripts/signal_gateway/reconciler.py` + `discord_notify.py`: use a string-typed `confidence="HIGH" | "MEDIUM" | "LOW"` for reconciler action confidence — again a **different column/concept**, not `signals.confidence`. Safe.
- Dashboard (`.openclaw/workspace/scripts/dashboard/`): **0** hits for `confidence`. Safe.
- `portfolio_stats.py`, `portfolio-webhook.py`: **0** hits. Safe.

Plan §8 risk row "Confidence column used in downstream ML/scoring logic — Unknown/Unknown" can be **downgraded to Low/Low** based on this evidence. No downstream breakage risk for the metadata change. ✅

### CONFIRMED — CF6: Notes field `[extracted: METHOD]` tag already in place and left unchanged

Code path at `.openclaw:822–823` (and `signal-gateway:597–598`) writes `notes_parts.append(f"[extracted: {method}]")`. Plan §4e correctly states A5 does not need to touch this. ✅

### CONFIRMED — CF7: No `event_store.py` in signal-gateway/scripts

`ls /home/oinkv/signal-gateway/scripts/` does NOT contain `event_store.py`. ✅ Plan §9 fact verified.

**However:** `/home/oinkv/.openclaw/workspace/scripts/event_store.py` **does** exist, and the canonical micro-gate (`.openclaw/workspace/scripts/micro-gate-v3.py`) already imports it (lines 36–42) and uses `_log_event()` through a `_get_event_store()` cache. Plan §4d says "No Event Logging Required" for A5 and defers event logging — which is a reasonable call, but the statement "micro-gate-v3.py currently contains no `EventStore` import" in plan §9 is TRUE for the signal-gateway copy and FALSE for the `.openclaw/workspace` canonical copy. See MINOR M3.

### CONFIRMED — CF8: Dedup logic does not use confidence

`_match_active` / `_match_closed_for_override` return tuple `(signal_row, confidence)` where `confidence` is a *string-typed* match-quality enum (`"ambiguous"`, `"ticker_only"`, `"closed_override"`, etc.), not the float column. No cross-referencing of `signals.confidence` in dedup. Plan §8 risk "Signal dedup (cross-channel) uses confidence — No/None" is confirmed. ✅

---

### MINOR — M1: Plan §4a map omits existing production extraction_method values

See C2 above. Downgrading from CRITICAL to a MINOR variant would be appropriate only if Mike confirms the missing-from-plan values (`oinxtractor_agent`, `telegram_direct`, `inline_fallback`, `qwen_v3`) are acceptable to leave on the 0.8 fallback. Keeping this as CRITICAL here because `oinxtractor_agent` is a **major active path** and letting it silently default to 0.8 would undercut the task's stated goal of "replacing the catch-all 0.8 default with a parser-type confidence map".

### MINOR — M2: Plan §9 Evidence "(Database queries run:)" block cites an empty DB

Plan shows `PRAGMA table_info(signals)` output and a confidence-distribution query. The `/home/oinkv/oink-sync/oink.db` path is a 0-byte file on this host at audit time. The evidence is still essentially correct (verified against `/home/oinkv/oinkfarm/data/oinkfarm.db`, which has identical shape), but the plan names the wrong DB file. Non-blocking. For ANVIL: validate against `/home/oinkv/oinkfarm/data/oinkfarm.db` when running acceptance-criteria queries.

### MINOR — M3: Plan asserts "no EventStore import in micro-gate" — stale for the canonical copy

See CF7. Statement is correct for the `signal-gateway` copy only. If ANVIL confuses the two copies (see C1), they could redundantly add an event-store import that already exists in the canonical. Cross-reference with the resolution of C1.

### MINOR — M4: Test file path target

Plan §2 says `tests/test_micro_gate_confidence.py`. Two test directories exist:
- `/home/oinkv/signal-gateway/tests/` (28 tests, no `test_micro_gate_confidence.py`)
- `/home/oinkv/.openclaw/workspace/tests/` (8 tests, no `test_micro_gate_confidence.py`)

Plan doesn't say which. If canonical is `.openclaw/workspace/scripts/micro-gate-v3.py`, test should land in `.openclaw/workspace/tests/`. Non-blocking but ANVIL needs the same C1 resolution to know where tests go.

### MINOR — M5: `PARSER_CONFIDENCE_MAP.get(method, 0.8)` semantics OK — but note method can be None

In `.openclaw` line 822 / `signal-gateway` line 597: `method = entry.get("extraction_method", "unknown")`. The `"unknown"` default means `method` is never `None` when looked up in the map. Plan §4b pseudocode uses `PARSER_CONFIDENCE_MAP.get(method, 0.8)` which will return 0.8 for both `"unknown"` and any value not in the map. ✅ Safe.

However, in `_log_rejection` (line 314 .openclaw / 250 signal-gateway), `entry.get("extraction_method")` has NO default — so it can be `None`. This is not in the A5 scope (reject path doesn't write signals), so non-blocking, but ANVIL should mirror the `"unknown"` default convention.

---

## Drift Summary Between .openclaw/workspace vs signal-gateway copies

Both copies have **identical** logic for the three target blocks A5 modifies:
- Confidence normalization block (lines 797–801 / 573–576)
- `_log_rejection` extraction_method field (lines 314 / 250)
- Notes tag append (lines 822–823 / 597–598)

The drift is **purely line-number/offset** — NOT semantic. The `.openclaw/workspace` copy has extra pre-/post-processing code above these targets (EventStore wrapper, quarantine helper, source_url helpers), adding ~220–230 lines of vertical offset. A5's change will apply cleanly to either copy if ANVIL follows the *anchor-based* markers rather than the absolute line numbers.

**Recommendation:** ANVIL should implement A5 against the canonical `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` as the task contract specifies. Whether it also needs to be mirrored into the `signal-gateway` repo (and tied to commit `38eb8e8`) should be clarified by Mike.

---

## Recommended Plan Revisions (for FORGE, before ANVIL pickup)

1. **Clarify canonical file path** in §2. State plainly: "Target file is `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (61460 bytes, 1407 lines). The signal-gateway copy is older and not the target." If both copies must be patched, say so.
2. **Reconcile `PARSER_CONFIDENCE_MAP` keys with production** — at minimum add `oinxtractor_agent`, `telegram_direct`, `inline_fallback`; decide with Mike whether to keep the `board_reconciler` / `oinkdb_opus` / `manual` placeholder keys.
3. **Replace absolute line numbers** with anchor-based references ("After the `# ── 10. Confidence normalization ──` comment block").
4. **Update §9 Evidence** to name `/home/oinkv/oinkfarm/data/oinkfarm.db` as the verification DB, and remove the "no EventStore import" assertion (or scope it to the signal-gateway copy).
5. **Update §8 risk table** — downgrade the "Confidence used in downstream ML/scoring" risk from "Unknown/Unknown" to Low/Low; CF5 evidence supports this.

---

## Acceptance Criteria Audit (Plan §6)

| AC# | Plan statement | Testable against current code? | Notes |
|---|---|---|---|
| 1 | cornix_regex signals → confidence=0.95 | ✅ yes | cornix_regex is a live producer |
| 2 | Explicit ext.confidence=0.73 preserved | ✅ yes | Requires Option-1 `is None` check per §4b |
| 3 | Unknown/missing → 0.80 | ✅ yes | Map-get default |
| 4 | >1.0 / 10.0 normalization unaffected | ✅ yes | Verified existing logic untouched above proposed change |
| 5 | All 6 signal-gateway tests pass | ⚠️ there are 28 tests in `signal-gateway/tests/`, 8 in `.openclaw/workspace/tests/` | Plan's "6 tests" count is stale |
| 6 | Notes tag `[extracted: …]` continues to appear | ✅ yes | Code path unchanged |

AC#5 count is stale but non-blocking (ANVIL runs `pytest`, not a hard-coded count).

---

## Files examined (audit evidence)

- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` (canonical, 1407 lines)
- `/home/oinkv/signal-gateway/scripts/micro-gate-v3.py` (repo copy, 1063 lines, HEAD `38eb8e8`)
- `/home/oinkv/signal-gateway/scripts/signal_gateway/signal_router.py` (extraction_method producers)
- `/home/oinkv/signal-gateway/scripts/signal_gateway/oinxtractor_client.py` (oinxtractor_agent producer)
- `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` (string-typed `confidence` — unrelated concept)
- `/home/oinkv/signal-gateway/scripts/signal_gateway/discord_notify.py` (back-compat extraction_method display names)
- `/home/oinkv/.openclaw/workspace/scripts/signal-extract-v3.py` (qwen_v3 producer)
- `/home/oinkv/.openclaw/workspace/scripts/trader_score.py`, `trader_commentary.py` (unrelated `confidence` field, not `signals.confidence`)
- `/home/oinkv/.openclaw/workspace/scripts/portfolio_stats.py`, `portfolio-webhook.py` (no `confidence` consumption)
- `/home/oinkv/oink-sync/oink_sync/lifecycle.py` (verified: no `confidence` / no `extraction_method`)
- `/home/oinkv/oinkfarm/data/oinkfarm.db` (PRAGMA + distribution query)
- Git log: `signal-gateway` HEAD confirmed as `38eb8e8799f237bdc907e87e5044135a1f117023`

**Queries run:**
```sql
PRAGMA table_info(signals);        -- confirms col 17 FLOAT NOT NULL DEFAULT 0.8
SELECT ROUND(confidence,2), COUNT(*) FROM signals GROUP BY 1;   -- {0.8:489, 0.85:2, 0.9:1}
SELECT notes FROM signals WHERE notes LIKE '%[extracted:%' LIMIT 6;  -- shows text_qwen_nl_v5 / wg_reconciler / text_oinxtractor_agent / unknown
```

---

## Final Call

A5 can go to ANVIL **after** C1 and C2 are resolved by FORGE (or explicitly deferred-to-Mike). The core idea is sound and low-risk; the execution detail (which file, which parser names) is where the plan has drifted from code. Recommend a plan v1.1 revision rather than proceeding as-is.
