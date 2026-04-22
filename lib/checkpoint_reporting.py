"""
checkpoint_reporting — core event-stream writer/reader for the Heavy Hybrid sprint.

Public API (see schema/events.schema.json and /tmp/checkpoint-reporting-SCHEMA.md for spec):

    emit_event(event_type, *, task_id=None, agent, phase=None, wave=None,
               repo=None, branch=None, pr=None, artifact_path=None,
               status=None, blocker=None, extra=None) -> dict

    publish_artifact(src_path, *, task_id, category, agent) -> dict
    set_task_status(task_id, new_status, agent) -> dict
    declare_blocker(task_id, reason, agent, details="") -> dict
    close_blocker(task_id, agent, reason=None) -> dict
    lint_checkpoint() -> list[dict]
    read_events(*, since=None, event_types=None, task_id=None, agent=None) -> list[dict]

All writes are multi-agent safe via fcntl.flock(LOCK_EX). Event IDs are monotonic:
`evt_YYYYMMDDTHHMMSSZ_NNNNNN` — counter seeded from max existing ID in file.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterator

import jsonschema

# -----------------------------------------------------------------------------
# Paths (overridable via env var for tests)
# -----------------------------------------------------------------------------

_DEFAULT_ROOT = Path(os.environ.get(
    "CHECKPOINT_ROOT",
    "/home/oinkv/sprint-checkpoint",
)).resolve()


def _root() -> Path:
    """Return current checkpoint root (env-overridable for tests)."""
    return Path(os.environ.get("CHECKPOINT_ROOT", str(_DEFAULT_ROOT))).resolve()


def _events_path() -> Path:
    return _root() / "events.jsonl"


def _schema_path() -> Path:
    return _root() / "schema" / "events.schema.json"


def _artifacts_root() -> Path:
    return _root() / "raw-artifacts"


# -----------------------------------------------------------------------------
# Enums (mirror schema — kept here for fast Python-side validation)
# -----------------------------------------------------------------------------

EVENT_TYPES = {
    "TASK_PLANNED", "PROPOSAL_READY", "PROPOSAL_APPROVED", "PROPOSAL_REJECTED",
    "CODE_STARTED", "PR_OPENED", "REVIEW_POSTED", "MERGED",
    "CANARY_STARTED", "CANARY_PASS", "CANARY_FAIL",
    "BLOCKED", "BLOCKER_RESOLVED",
    "DECISION_NEEDED", "DECISION_RESOLVED",
    "STATUS_CHANGED", "ARTIFACT_PUBLISHED", "AGENT_HEARTBEAT", "SPRINT_NOTE",
}

AGENTS = {"anvil", "vigil", "guardian", "forge", "hermes", "oinkv", "oinkdb", "mike", "system"}

BLOCKER_KEYS = {
    "waiting_for_mike_decision",
    "waiting_for_vigil_review",
    "waiting_for_guardian_review",
    "waiting_for_proposal_approval",
    "waiting_for_canary",
    "waiting_for_upstream_task",
    "design_clarification_needed",
    "test_failure",
    "external_dependency",
}

STATUSES = {
    "PROPOSAL", "PROPOSAL_REVIEW", "CODE", "PR_REVIEW", "MERGED",
    "CANARY", "DONE", "BLOCKED", "DEFERRED", "NOT_STARTED",
}

PHASES = {"A", "B", "C", "D", "meta"}

REPOS = {"oinkfarm", "oink-sync", "signal-gateway", "oinkdb-api"}

# event_type -> required keys in `extra`
REQUIRED_EXTRA: dict[str, tuple[str, ...]] = {
    "TASK_PLANNED": ("plan_path",),
    "PROPOSAL_READY": ("proposal_path",),
    "PROPOSAL_APPROVED": ("approver",),
    "PROPOSAL_REJECTED": ("reviewer", "reason"),
    "CODE_STARTED": ("branch",),
    "PR_OPENED": ("pr", "title"),
    "REVIEW_POSTED": ("reviewer", "score", "verdict"),
    "MERGED": ("pr", "commit_sha"),
    "CANARY_STARTED": ("baseline_ts",),
    "CANARY_PASS": ("report_path", "signals_observed"),
    "CANARY_FAIL": ("report_path", "issues"),
    "BLOCKED": ("reason",),
    "BLOCKER_RESOLVED": ("reason",),
    "DECISION_NEEDED": ("question_id", "question", "options"),
    "DECISION_RESOLVED": ("question_id", "answer"),
    "STATUS_CHANGED": ("from_status", "to_status"),
    "ARTIFACT_PUBLISHED": ("category", "src_path"),
    "AGENT_HEARTBEAT": ("current_task", "phase"),
    "SPRINT_NOTE": ("text",),
}

VERDICTS = {"PASS", "REVISE", "FAIL"}

_TASK_ID_RE = re.compile(r"^[A-Z][0-9]+$")
_EVENT_ID_RE = re.compile(r"^evt_(\d{8}T\d{6}Z)_(\d{6})$")
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# -----------------------------------------------------------------------------
# Validation errors
# -----------------------------------------------------------------------------

class CheckpointValidationError(ValueError):
    """Raised when an event fails validation before write."""


# -----------------------------------------------------------------------------
# Schema cache
# -----------------------------------------------------------------------------

_SCHEMA_CACHE: dict[str, Any] = {}


def _load_schema() -> dict:
    key = str(_schema_path())
    cached = _SCHEMA_CACHE.get(key)
    if cached is not None:
        return cached
    with open(_schema_path(), "r", encoding="utf-8") as f:
        schema = json.load(f)
    # Pre-check that the schema itself is valid (cheap on first call only).
    jsonschema.Draft202012Validator.check_schema(schema)
    _SCHEMA_CACHE[key] = schema
    return schema


# -----------------------------------------------------------------------------
# Time + ID helpers
# -----------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str) -> datetime:
    """Parse a checkpoint ISO ts (YYYY-MM-DDTHH:MM:SSZ) to aware UTC datetime."""
    if not _TS_RE.match(ts):
        # Lenient fallback — allow any fromisoformat-parsable string with Z
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _pr_key(pr) -> object | None:
    """Normalize a PR identifier into a stable dict key.

    Accepts bare integers (42), numeric strings ("42"), or repo-qualified
    references like "QuantisDevelopment/oink-sync#10". Returns None for empty
    / unparseable values so callers can skip them safely. Historically this
    was `int(pr)`, which blew up on the repo-qualified form — that crash is
    what prompted this helper.
    """
    if pr is None:
        return None
    if isinstance(pr, int):
        return pr
    s = str(pr).strip()
    if not s:
        return None
    try:
        return int(s)
    except (TypeError, ValueError):
        return s  # repo-qualified string like "owner/repo#123"


def _scan_max_counter_for_ts(ts_token: str) -> int:
    """Return the highest counter N observed for the given ts_token in events.jsonl.

    Returns 0 if no matching event found.
    """
    path = _events_path()
    if not path.exists():
        return 0
    max_n = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = obj.get("event_id", "")
            m = _EVENT_ID_RE.match(eid)
            if m and m.group(1) == ts_token:
                n = int(m.group(2))
                if n > max_n:
                    max_n = n
    return max_n


def _next_event_id(ts: datetime) -> str:
    """Generate a monotonic event_id for the given ts. Must be called while
    holding the file lock, so the counter scan is race-free."""
    ts_token = ts.strftime("%Y%m%dT%H%M%SZ")
    max_n = _scan_max_counter_for_ts(ts_token)
    return f"evt_{ts_token}_{(max_n + 1):06d}"


# -----------------------------------------------------------------------------
# Low-level append (with exclusive lock)
# -----------------------------------------------------------------------------

def _append_jsonl(event: dict) -> None:
    """Append a single JSON event to events.jsonl atomically.

    NOTE: the caller passes an event that ALREADY has event_id + ts filled.
    This helper only appends; event-id generation happens inside emit_event
    while the same lock is held.
    """
    path = _events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, sort_keys=False, separators=(",", ": "))
    # The newline must be in the single write() call so flock guarantees
    # atomicity — partial lines would corrupt the stream.
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _emit_with_lock(event_stub: dict) -> dict:
    """Acquire lock, assign event_id + ts, validate, append, return.

    All atomicity-critical logic is inside this one lock span so two
    concurrent writers cannot collide on counter or on partial lines.
    """
    path = _events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Open the file for append under an exclusive lock; we do the counter
    # scan + the write inside the same lock.
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            now = _utc_now()
            event_stub["ts"] = _iso_z(now)
            event_stub["event_id"] = _next_event_id(now)
            # Validate AFTER id + ts are stamped (they are required).
            _validate_event(event_stub)
            line = json.dumps(event_stub, ensure_ascii=False, separators=(",", ": "))
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return event_stub


# -----------------------------------------------------------------------------
# Python-side validation (fast reject + clear errors before jsonschema)
# -----------------------------------------------------------------------------

def _validate_event(event: dict) -> None:
    et = event.get("event_type")
    if et not in EVENT_TYPES:
        raise CheckpointValidationError(
            f"Unknown event_type: {et!r} (allowed: {sorted(EVENT_TYPES)})"
        )

    agent = event.get("agent")
    if agent not in AGENTS:
        raise CheckpointValidationError(
            f"Unknown agent: {agent!r} (allowed: {sorted(AGENTS)})"
        )

    task_id = event.get("task_id")
    if task_id is not None and not _TASK_ID_RE.match(task_id):
        raise CheckpointValidationError(
            f"Invalid task_id: {task_id!r} — must match [A-Z]\\d+ or be null"
        )

    phase = event.get("phase")
    if phase is not None and phase not in PHASES:
        raise CheckpointValidationError(
            f"Invalid phase: {phase!r} (allowed: {sorted(PHASES)})"
        )

    repo = event.get("repo")
    if repo is not None and repo not in REPOS:
        raise CheckpointValidationError(
            f"Invalid repo: {repo!r} (allowed: {sorted(REPOS)})"
        )

    status = event.get("status")
    if status is not None and status not in STATUSES:
        raise CheckpointValidationError(
            f"Invalid status: {status!r} (allowed: {sorted(STATUSES)})"
        )

    blocker = event.get("blocker")
    if blocker is not None and blocker not in BLOCKER_KEYS:
        raise CheckpointValidationError(
            f"Invalid blocker_key: {blocker!r} (allowed: {sorted(BLOCKER_KEYS)})"
        )

    extra = event.get("extra") or {}
    if not isinstance(extra, dict):
        raise CheckpointValidationError("extra must be an object (dict)")

    required = REQUIRED_EXTRA.get(et, ())
    missing = [k for k in required if k not in extra]
    if missing:
        raise CheckpointValidationError(
            f"{et} requires extra keys {list(required)}; missing: {missing}"
        )

    if et == "REVIEW_POSTED":
        v = extra.get("verdict")
        if v not in VERDICTS:
            raise CheckpointValidationError(
                f"REVIEW_POSTED.extra.verdict must be one of {sorted(VERDICTS)}, got {v!r}"
            )
        s = extra.get("score")
        if not isinstance(s, (int, float)) or not (0 <= s <= 10):
            raise CheckpointValidationError(
                f"REVIEW_POSTED.extra.score must be number in [0,10], got {s!r}"
            )

    if et == "BLOCKED":
        if extra.get("reason") not in BLOCKER_KEYS:
            raise CheckpointValidationError(
                f"BLOCKED.extra.reason must be a BLOCKER_KEY; got {extra.get('reason')!r}"
            )

    ts = event.get("ts", "")
    if not _TS_RE.match(ts):
        raise CheckpointValidationError(
            f"ts must be YYYY-MM-DDTHH:MM:SSZ UTC; got {ts!r}"
        )

    eid = event.get("event_id", "")
    if not _EVENT_ID_RE.match(eid):
        raise CheckpointValidationError(
            f"event_id must match evt_YYYYMMDDTHHMMSSZ_NNNNNN; got {eid!r}"
        )

    # Finally hand to jsonschema for the belt-and-braces strict check.
    schema = _load_schema()
    try:
        jsonschema.validate(event, schema, cls=jsonschema.Draft202012Validator)
    except jsonschema.ValidationError as e:
        raise CheckpointValidationError(f"Schema validation failed: {e.message}") from e


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def emit_event(
    event_type: str,
    *,
    task_id: str | None = None,
    agent: str,
    phase: str | None = None,
    wave: int | None = None,
    repo: str | None = None,
    branch: str | None = None,
    pr: int | None = None,
    artifact_path: str | None = None,
    status: str | None = None,
    blocker: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Emit an event to events.jsonl. Returns the fully-populated event dict."""
    event: dict[str, Any] = {
        "event_id": "",         # filled inside lock
        "ts": "",               # filled inside lock
        "event_type": event_type,
        "task_id": task_id,
        "phase": phase,
        "wave": wave,
        "agent": agent,
        "repo": repo,
        "branch": branch,
        "pr": pr,
        "artifact_path": artifact_path,
        "status": status,
        "blocker": blocker,
        "extra": extra or {},
    }
    return _emit_with_lock(event)


def publish_artifact(
    src_path: str,
    *,
    task_id: str,
    category: str,
    agent: str,
) -> dict:
    """Copy src_path to raw-artifacts/{agent}/{category}/{basename} and emit
    an ARTIFACT_PUBLISHED event. Returns the emitted event (with artifact_path
    set to the destination, relative to checkpoint root)."""
    if agent not in AGENTS:
        raise CheckpointValidationError(f"Unknown agent: {agent!r}")
    if not category or "/" in category or category.startswith("."):
        raise CheckpointValidationError(
            f"Invalid category: {category!r} (must be a single path segment)"
        )
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"publish_artifact: src not found: {src_path}")
    if not src.is_file():
        raise CheckpointValidationError(
            f"publish_artifact: src must be a regular file: {src_path}"
        )

    dest_dir = _artifacts_root() / agent / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)

    try:
        rel_dest = dest.relative_to(_root())
        artifact_rel = str(rel_dest)
    except ValueError:
        artifact_rel = str(dest)

    return emit_event(
        "ARTIFACT_PUBLISHED",
        task_id=task_id,
        agent=agent,
        artifact_path=artifact_rel,
        extra={
            "category": category,
            "src_path": str(src_path),
        },
    )


def set_task_status(task_id: str, new_status: str, agent: str) -> dict:
    """Emit STATUS_CHANGED. from_status is derived from the last
    STATUS_CHANGED event for task_id (defaults to NOT_STARTED)."""
    if new_status not in STATUSES:
        raise CheckpointValidationError(
            f"Invalid new_status: {new_status!r} (allowed: {sorted(STATUSES)})"
        )

    prior = None
    for ev in _iter_events():
        if ev.get("task_id") == task_id and ev.get("event_type") == "STATUS_CHANGED":
            prior = ev
    from_status = (prior or {}).get("extra", {}).get("to_status", "NOT_STARTED")

    return emit_event(
        "STATUS_CHANGED",
        task_id=task_id,
        agent=agent,
        status=new_status,
        extra={"from_status": from_status, "to_status": new_status},
    )


def declare_blocker(
    task_id: str,
    reason: str,
    agent: str,
    details: str = "",
) -> dict:
    """Emit a BLOCKED event. `reason` MUST be a BLOCKER_KEY."""
    if reason not in BLOCKER_KEYS:
        raise CheckpointValidationError(
            f"declare_blocker.reason must be a BLOCKER_KEY; got {reason!r} "
            f"(allowed: {sorted(BLOCKER_KEYS)})"
        )
    extra = {"reason": reason}
    if details:
        extra["details"] = details
    return emit_event(
        "BLOCKED",
        task_id=task_id,
        agent=agent,
        blocker=reason,
        status="BLOCKED",
        extra=extra,
    )


def close_blocker(
    task_id: str,
    agent: str,
    reason: str | None = None,
) -> dict:
    """Emit BLOCKER_RESOLVED. If reason is omitted, resolves the most recent
    BLOCKED event for task_id."""
    if reason is None:
        most_recent = None
        for ev in _iter_events():
            if ev.get("task_id") == task_id and ev.get("event_type") == "BLOCKED":
                most_recent = ev
        if most_recent is None:
            raise CheckpointValidationError(
                f"close_blocker: no prior BLOCKED event for task_id={task_id}"
            )
        reason = (most_recent.get("extra") or {}).get("reason") or most_recent.get("blocker")
        if reason not in BLOCKER_KEYS:
            raise CheckpointValidationError(
                f"close_blocker: latest BLOCKED has invalid reason {reason!r}"
            )
    elif reason not in BLOCKER_KEYS:
        raise CheckpointValidationError(
            f"close_blocker.reason must be a BLOCKER_KEY or None; got {reason!r}"
        )

    return emit_event(
        "BLOCKER_RESOLVED",
        task_id=task_id,
        agent=agent,
        blocker=reason,
        extra={"reason": reason},
    )


# -----------------------------------------------------------------------------
# Reader (iterator-friendly)
# -----------------------------------------------------------------------------

def _iter_events() -> Iterator[dict]:
    """Yield every event in events.jsonl in file order. Silently skips blank
    lines and JSON parse errors (the dashboard reducer is defensive)."""
    path = _events_path()
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def read_events(
    *,
    since: str | None = None,
    event_types: list[str] | None = None,
    task_id: str | None = None,
    agent: str | None = None,
) -> list[dict]:
    """Return events matching filters (all filters AND together).

    since       — ISO timestamp (any fromisoformat-parseable form accepted;
                  Z suffix handled). Inclusive comparison ts >= since.
    event_types — list of event_type strings to keep.
    task_id     — exact match.
    agent       — exact match.
    """
    since_dt: datetime | None = None
    if since:
        since_dt = _parse_ts(since)
    types_set = set(event_types) if event_types else None

    out: list[dict] = []
    for ev in _iter_events():
        if types_set is not None and ev.get("event_type") not in types_set:
            continue
        if task_id is not None and ev.get("task_id") != task_id:
            continue
        if agent is not None and ev.get("agent") != agent:
            continue
        if since_dt is not None:
            try:
                ev_ts = _parse_ts(ev.get("ts", ""))
            except Exception:
                continue
            if ev_ts < since_dt:
                continue
        out.append(ev)
    return out


# -----------------------------------------------------------------------------
# Lint — detect gaps per schema §lint_checkpoint
# -----------------------------------------------------------------------------

def _synth_event_id(ev: dict) -> str:
    """Return ev['event_id'] if present, else a sortable synthetic id derived
    from ts. Legacy rows (pre-schema-freeze) may lack event_id; we must never
    KeyError in gap emitters downstream. See skill: checkpoint-reporting §5."""
    eid = ev.get("event_id")
    if eid:
        return eid
    ts = ev.get("ts") or ev.get("timestamp") or ""
    # Normalize "2026-04-21T22:16:53.148551+00:00" or "2026-04-21T22:16:53Z" → "20260421T221653"
    compact = ts.replace("-", "").replace(":", "").replace("+00:00", "").rstrip("Z").split(".")[0]
    return f"evt_{compact}_synthetic"


def lint_checkpoint(now: datetime | None = None) -> list[dict]:
    """Return a list of {task_id, agent, issue, severity, event_id, detected_at}
    for each gap pattern defined in the frozen schema.

    Rules:
      - MERGED with no subsequent CANARY_STARTED within 2h       → severity=warn
      - CANARY_STARTED with no CANARY_PASS/FAIL within 48h       → severity=warn
      - PR_OPENED with no REVIEW_POSTED within 24h               → severity=warn
      - BLOCKED >4h with no BLOCKER_RESOLVED                     → severity=warn
      - AGENT_HEARTBEAT stale >3h for an active agent            → severity=warn
      - DECISION_NEEDED >24h with no DECISION_RESOLVED           → severity=error
    """
    now = now or _utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    events = list(_iter_events())
    gaps: list[dict] = []

    def _age_hours(ev: dict) -> float:
        ts = ev.get("ts") or ev.get("timestamp")
        if not ts:
            return 0.0
        try:
            return (now - _parse_ts(ts)).total_seconds() / 3600.0
        except Exception:
            return 0.0

    # --- MERGED without CANARY_STARTED within 2h (per task_id) ---
    merged_by_task: dict[str, dict] = {}
    canary_started_by_task: dict[str, dict] = {}
    canary_verdict_by_task: dict[str, dict] = {}
    pr_opened_by_pr: dict[int, dict] = {}
    review_by_pr: dict[int, dict] = {}
    blocked_by_task: dict[str, dict] = {}
    resolved_by_task: dict[str, dict] = {}
    heartbeat_by_agent: dict[str, dict] = {}
    decisions_needed: dict[str, dict] = {}
    decisions_resolved: dict[str, dict] = {}

    for ev in events:
        et = ev.get("event_type")
        tid = ev.get("task_id")
        extra = ev.get("extra") or {}
        if et == "MERGED" and tid:
            merged_by_task[tid] = ev
        elif et == "CANARY_STARTED" and tid:
            canary_started_by_task[tid] = ev
        elif et in ("CANARY_PASS", "CANARY_FAIL") and tid:
            canary_verdict_by_task[tid] = ev
        elif et == "PR_OPENED":
            pr = extra.get("pr") or ev.get("pr")
            pr_key = _pr_key(pr)
            if pr_key is not None:
                pr_opened_by_pr[pr_key] = ev
        elif et == "REVIEW_POSTED":
            pr = ev.get("pr") or extra.get("pr")
            pr_key = _pr_key(pr)
            if pr_key is not None:
                # Keep the EARLIEST review so PR_OPENED→first-review latency is captured.
                existing = review_by_pr.get(pr_key)
                if existing is None or _parse_ts(ev["ts"]) < _parse_ts(existing["ts"]):
                    review_by_pr[pr_key] = ev
        elif et == "BLOCKED" and tid:
            blocked_by_task[tid] = ev
        elif et == "BLOCKER_RESOLVED" and tid:
            resolved_by_task[tid] = ev
        elif et == "AGENT_HEARTBEAT":
            a = ev.get("agent")
            if a:
                prev = heartbeat_by_agent.get(a)
                ev_ts = ev.get("ts") or ev.get("timestamp")
                if not ev_ts:
                    continue
                try:
                    ev_parsed = _parse_ts(ev_ts)
                except Exception:
                    continue
                if prev is None:
                    heartbeat_by_agent[a] = ev
                else:
                    prev_ts = prev.get("ts") or prev.get("timestamp")
                    try:
                        if ev_parsed > _parse_ts(prev_ts):
                            heartbeat_by_agent[a] = ev
                    except Exception:
                        heartbeat_by_agent[a] = ev
        elif et == "DECISION_NEEDED":
            qid = extra.get("question_id")
            if qid:
                decisions_needed[qid] = ev
        elif et == "DECISION_RESOLVED":
            qid = extra.get("question_id")
            if qid:
                decisions_resolved[qid] = ev

    # MERGED → no CANARY within 2h
    for tid, merged in merged_by_task.items():
        canary = canary_started_by_task.get(tid)
        if canary is None or _parse_ts(canary["ts"]) < _parse_ts(merged["ts"]):
            if _age_hours(merged) > 2:
                gaps.append({
                    "task_id": tid,
                    "agent": merged.get("agent"),
                    "issue": "MERGED with no CANARY_STARTED within 2h",
                    "severity": "warn",
                    "event_id": merged["event_id"],
                    "detected_at": _iso_z(now),
                })

    # CANARY_STARTED → no verdict within 48h
    for tid, started in canary_started_by_task.items():
        verdict = canary_verdict_by_task.get(tid)
        if verdict is None or _parse_ts(verdict["ts"]) < _parse_ts(started["ts"]):
            if _age_hours(started) > 48:
                gaps.append({
                    "task_id": tid,
                    "agent": started.get("agent"),
                    "issue": "CANARY_STARTED with no verdict within 48h",
                    "severity": "warn",
                    "event_id": _synth_event_id(started),
                    "detected_at": _iso_z(now),
                })

    # PR_OPENED → no REVIEW_POSTED within 24h
    for pr, opened in pr_opened_by_pr.items():
        review = review_by_pr.get(pr)
        if review is None or _parse_ts(review["ts"]) < _parse_ts(opened["ts"]):
            if _age_hours(opened) > 24:
                gaps.append({
                    "task_id": opened.get("task_id"),
                    "agent": opened.get("agent"),
                    "issue": f"PR_OPENED (pr={pr}) with no REVIEW_POSTED within 24h",
                    "severity": "warn",
                    "event_id": _synth_event_id(opened),
                    "detected_at": _iso_z(now),
                })

    # BLOCKED >4h without BLOCKER_RESOLVED (match by task_id, only if most
    # recent resolution is older than the block)
    for tid, blocked in blocked_by_task.items():
        resolved = resolved_by_task.get(tid)
        if resolved is None or _parse_ts(resolved["ts"]) < _parse_ts(blocked["ts"]):
            if _age_hours(blocked) > 4:
                gaps.append({
                    "task_id": tid,
                    "agent": blocked.get("agent"),
                    "issue": (
                        f"BLOCKED > 4h with no BLOCKER_RESOLVED "
                        f"(reason={(blocked.get('extra') or {}).get('reason')})"
                    ),
                    "severity": "warn",
                    "event_id": _synth_event_id(blocked),
                    "detected_at": _iso_z(now),
                })

    # AGENT_HEARTBEAT stale >3h (for agents that have ever heartbeat — only
    # non-meta agents; 'system' and 'mike' do not heartbeat)
    for a, hb in heartbeat_by_agent.items():
        if a in ("system", "mike"):
            continue
        if _age_hours(hb) > 3:
            gaps.append({
                "task_id": hb.get("task_id"),
                "agent": a,
                "issue": f"AGENT_HEARTBEAT stale > 3h for {a}",
                "severity": "warn",
                "event_id": _synth_event_id(hb),
                "detected_at": _iso_z(now),
            })

    # DECISION_NEEDED >24h without DECISION_RESOLVED
    for qid, need in decisions_needed.items():
        resolved = decisions_resolved.get(qid)
        if resolved is None or _parse_ts(resolved["ts"]) < _parse_ts(need["ts"]):
            if _age_hours(need) > 24:
                gaps.append({
                    "task_id": need.get("task_id"),
                    "agent": need.get("agent"),
                    "issue": f"DECISION_NEEDED (qid={qid}) unresolved > 24h",
                    "severity": "error",
                    "event_id": _synth_event_id(need),
                    "detected_at": _iso_z(now),
                })

    # Deterministic order: by severity (error first), then detected_at, then event_id
    severity_rank = {"error": 0, "warn": 1, "info": 2}
    gaps.sort(key=lambda g: (severity_rank.get(g["severity"], 9), g["event_id"]))
    return gaps


# -----------------------------------------------------------------------------
# __all__
# -----------------------------------------------------------------------------

__all__ = [
    "emit_event",
    "publish_artifact",
    "set_task_status",
    "declare_blocker",
    "close_blocker",
    "lint_checkpoint",
    "read_events",
    "CheckpointValidationError",
    "EVENT_TYPES",
    "AGENTS",
    "BLOCKER_KEYS",
    "STATUSES",
    "PHASES",
    "REPOS",
]
