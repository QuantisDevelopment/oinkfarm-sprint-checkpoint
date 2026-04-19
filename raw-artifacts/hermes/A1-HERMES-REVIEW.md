# 🧠 HERMES Independent Review — PR #126 + PR #4 / Task A1 (signal_events extension + lifecycle instrumentation)

**Branches:** oinkfarm `anvil/A1-signal-events-extension` (commits `09e0f94b`, `498d8b28`) + oink-sync `anvil/A1-signal-events-extension` (commits `ef948f3`, `620bd46`, plus `dbe33d4` yfinance-aliases carryover)
**Tier:** 🔴 CRITICAL (Financial Hotpath #6: micro-gate INSERT + lifecycle SL/TP writes)
**Review mode:** Third-party sanity check (VIGIL PASS 9.60, GUARDIAN PASS 9.80)
**Date:** 2026-04-19

---

## Parity audit — oinkfarm canonical vs oink-sync vendored copy

Ran Python import on both copies:
- `scripts/event_store.py::LIFECYCLE_EVENTS` → 19 elements
- `oink_sync/event_store.py::LIFECYCLE_EVENTS` → 19 elements
- **Byte-exact equality** of the set contents, including `PRICE_ALERT` under "# Stage 7: Monitoring" in both.
- `diff -u` between the two files shows only a 4-line delta: the vendored file prepends a 3-line "Vendored from oinkfarm commit 3b5453b7" header and drops the canonical-copy cross-reference docstring. All `EventStore` methods, SQL, migration logic, and quarantine codes are byte-identical.

✅ Parity confirmed.

## Fix-architecture audit — `commit=True`

Task context referenced "all 13 call sites" needing `commit=True`. The implemented fix is tighter than that: `commit=True` is hoisted into the wrapper layer.

| Codebase | Wrapper | Call sites |
|---|---|---|
| oinkfarm `scripts/micro-gate-v3.py` | `_log_event()` lines 61–78 (one `es.log(..., commit=True)`) | 5 emit sites (lines 882, 1026, 1031, 1104, 1183) |
| oink-sync `oink_sync/lifecycle.py` | `Lifecycle._log_event()` lines 228–248 (one `es.log(..., commit=True)`) | 6 emit sites (lines 402, 474, 481, 545, 635, 702) |

One-line wrapper fix → covers every current and future `_log_event()` call. This is architecturally superior to 13 inline `commit=True` flags because new callsites cannot regress.

## Try/except scope audit (VIGIL's Phase 0 concern)

Both `_log_event` wrappers have a single narrow try/except covering only `_get_event_store()` + `es.log()`. Verified by reading:
- `scripts/micro-gate-v3.py:73–78` — except covers ONLY event-store init + log
- `oink_sync/lifecycle.py:238–248` — same pattern
- Every callsite in `lifecycle.py` places the emit AFTER the signal UPDATE, checks `cur.rowcount`, then calls `self._log_event()`. If the UPDATE raises, it's not caught by the event except. Examined lines 380–408 (`_check_sl_tp`), 464–478 (`_process_tp_hits`), 540–548 (`_check_limit_fills`), 630–642 (`_expire_stale_limits`), 697–708 (`_check_sl_proximity`).

✅ No silent swallowing of signal-mutation exceptions.

## Schema ALTER idempotency audit

Both copies at `ensure_schema()`:

```python
for col in ("field TEXT", "old_value TEXT", "new_value TEXT", "source_msg_id TEXT"):
    try:
        self.conn.execute(f"ALTER TABLE signal_events ADD COLUMN {col}")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise
```

Traps ONLY duplicate-column; any other OperationalError propagates. `_schema_ready` flag makes repeated `ensure_schema()` calls cheap. `test_schema_migration_idempotent` forces `_schema_ready = False` and runs twice — passes. ✅

## Dry-run parity audit

`_process_update` returns at the `if dry_run:` gate BEFORE any `_log_event()` call (line 1002–1004, _before_ the try block at 1006). Same for `_process_closure` (line 1149–1152). Dry-run correctly emits zero events — matches A3's behavior. ✅

## Downstream consumer audit (added nullable columns)

Repo-wide grep for `signal_events` reads:
- oinkfarm: only `event_store.py` and tests. `get_events()` was updated to `SELECT id, event_type, payload, source, created_at, field, old_value, new_value, source_msg_id`. No API/analytics/reporter path queries the table.
- oink-sync: only `event_store.py` and tests.

Nullable-column addition is backward-compatible for any external consumer that later queries the table with `SELECT *` — they just get extra NULL columns. ✅

## Test-Run Result

Ran the new tests in-place (read-only; did not modify workspace files):

| Suite | Location | Result |
|---|---|---|
| `tests/test_event_store_a1.py` | oinkfarm | **11 passed** in 0.02s |
| `tests/test_lifecycle_events.py` | oink-sync | **8 passed** in 0.02s |
| `tests/test_micro_gate_filled_at.py` (A3 regression) | oinkfarm | **8 passed** in 0.02s |
| `tests/test_yfinance_afterhours.py` (PYTHONPATH=.) | oink-sync | **8 passed** in 0.22s |

**Total: 35/35 pass.** No regressions. No collection errors after PYTHONPATH set.

Note: task brief referenced `tests/test_lifecycle_a1.py` — the actual filename shipped is `tests/test_lifecycle_events.py`. Content matches the diff.

## Findings beyond VIGIL/GUARDIAN

1. **(nit, non-blocking) Scope bleed in PR #4:** commit `dbe33d4` ("fix: resolve commodity futures via yfinance aliases") is NOT on master — `git branch --contains dbe33d4` returns only the A1 and `fix/issue-114-gc-futures-yfinance` branches. VIGIL's review stated this pre-existed from prior master merge; that's not what the git history shows. The commit is carried through PR #4 along with the A1 changes. Both are additive and individually tested, and the futures aliases are clearly scoped (backends/yfinance_be.py, resolver.py, test_yfinance_afterhours.py). Worth noting in the merge commit message.
2. **(observation, positive) `commit=True` is applied at the wrapper layer** — one-line fix per codebase covers all emit sites. Architecturally superior to patching 13 inline calls; cannot regress as new callsites are added.
3. **(observation) `TRADE_CLOSED_SL` fallback** at `oink_sync/lifecycle.py:400–401` for non-`sl_hit` close_source is defensively sound but unreachable in practice — `_check_sl_tp` only reaches the event-emit block when `close_source == "sl_hit"`. VIGIL flagged this; agree it's defensive and acceptable.
4. **(observation) PRICE_ALERT dedup** relies on `self._sl_cooldowns[sig_id] = now` set just before the event emit, and the `_last_expiry_check` guard. No explicit test that a second alert within `sl_cooldown_s` is suppressed; VIGIL tracked as follow-up. Not blocking.

## Verdict: ✅ LGTM

Clean surgical fix to a well-diagnosed bug. Root-cause documentation is textbook quality. Both copies in parity, test suites green (35/35), schema migration is the safest possible case (0-row table, additive, idempotent), non-fatal wrapper scope is genuinely tight, downstream consumers untouched, dry-run produces zero events. The wrapper-level `commit=True` hoist is a better fix than the "patch 13 callsites" framing suggested. The only substantive finding beyond VIGIL/GUARDIAN is a minor scope note about the yfinance futures commit riding along in PR #4 — worth mentioning in the merge commit message but not a blocker. Concur with VIGIL 9.60 PASS and GUARDIAN 9.80 PASS. Ship both PRs as a coordinated merge, run the canary per GUARDIAN's 6-point criteria.

*— 🧠 HERMES, independent third-party review, 2026-04-19*
