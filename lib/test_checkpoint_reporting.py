"""
Tests for checkpoint_reporting — pytest-compatible.

Usage:
    cd /home/oinkv/sprint-checkpoint
    python -m pytest lib/test_checkpoint_reporting.py -v

All tests operate in a per-test tmpdir (CHECKPOINT_ROOT override) so the
real events.jsonl is never touched.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Make the module importable when pytest is launched from the repo root.
LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import checkpoint_reporting as cr  # noqa: E402


# Path to the real schema file the module expects to find under CHECKPOINT_ROOT.
REAL_SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "events.schema.json"


@pytest.fixture
def ckpt_root(tmp_path, monkeypatch):
    """Isolated checkpoint root with fresh events.jsonl + schema copy."""
    (tmp_path / "schema").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REAL_SCHEMA, tmp_path / "schema" / "events.schema.json")
    (tmp_path / "events.jsonl").touch()
    monkeypatch.setenv("CHECKPOINT_ROOT", str(tmp_path))
    # Nuke schema cache so the fresh copy is re-read.
    cr._SCHEMA_CACHE.clear()
    yield tmp_path
    cr._SCHEMA_CACHE.clear()


# -----------------------------------------------------------------------------
# Happy path: one emit per event_type
# -----------------------------------------------------------------------------

HAPPY_CASES = [
    ("TASK_PLANNED", {"extra": {"plan_path": "plans/A1-plan.md"}}),
    ("PROPOSAL_READY", {"extra": {"proposal_path": "A1-PHASE0-PROPOSAL.md"}}),
    ("PROPOSAL_APPROVED", {"extra": {"approver": "vigil"}}),
    ("PROPOSAL_REJECTED", {"extra": {"reviewer": "guardian", "reason": "scope"}}),
    ("CODE_STARTED", {"branch": "anvil/A1-foo", "extra": {"branch": "anvil/A1-foo"}}),
    ("PR_OPENED", {"pr": 42, "extra": {"pr": 42, "title": "A1 impl"}}),
    ("REVIEW_POSTED", {"pr": 42, "extra": {"reviewer": "vigil", "score": 9.5, "verdict": "PASS"}}),
    ("MERGED", {"pr": 42, "extra": {"pr": 42, "commit_sha": "deadbeef"}}),
    ("CANARY_STARTED", {"extra": {"baseline_ts": "2026-04-20T10:00:00Z"}}),
    ("CANARY_PASS", {"extra": {"report_path": "canary/A1.md", "signals_observed": 120}}),
    ("CANARY_FAIL", {"extra": {"report_path": "canary/A1.md", "issues": ["drift>5%"]}}),
    ("BLOCKED", {"blocker": "waiting_for_vigil_review",
                 "extra": {"reason": "waiting_for_vigil_review"}}),
    ("BLOCKER_RESOLVED", {"blocker": "waiting_for_vigil_review",
                           "extra": {"reason": "waiting_for_vigil_review"}}),
    ("DECISION_NEEDED", {"extra": {"question_id": "q1", "question": "ship?", "options": ["yes", "no"]}}),
    ("DECISION_RESOLVED", {"extra": {"question_id": "q1", "answer": "yes"}}),
    ("STATUS_CHANGED", {"status": "CODE",
                         "extra": {"from_status": "PROPOSAL", "to_status": "CODE"}}),
    ("ARTIFACT_PUBLISHED", {"artifact_path": "raw-artifacts/anvil/proposals/x.md",
                             "extra": {"category": "proposals", "src_path": "/tmp/x.md"}}),
    ("AGENT_HEARTBEAT", {"extra": {"current_task": "A1", "phase": "code"}}),
    ("SPRINT_NOTE", {"extra": {"text": "Day 2: wave 1 green."}}),
]


@pytest.mark.parametrize("event_type,kwargs", HAPPY_CASES)
def test_emit_event_happy_path(ckpt_root, event_type, kwargs):
    ev = cr.emit_event(
        event_type,
        task_id="A1",
        agent="anvil",
        phase="A",
        wave=1,
        **kwargs,
    )
    assert ev["event_type"] == event_type
    assert ev["event_id"].startswith("evt_")
    assert ev["ts"].endswith("Z")
    # Confirm it landed on disk.
    lines = (ckpt_root / "events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event_id"] == ev["event_id"]


def test_event_id_monotonic(ckpt_root):
    ids = []
    for _ in range(5):
        ev = cr.emit_event(
            "SPRINT_NOTE", task_id=None, agent="hermes", phase="meta",
            extra={"text": "hi"},
        )
        ids.append(ev["event_id"])
    # IDs must be strictly increasing as strings (ts_token + counter).
    assert ids == sorted(ids)
    assert len(set(ids)) == 5


# -----------------------------------------------------------------------------
# Concurrent-write safety
# -----------------------------------------------------------------------------

def test_concurrent_writes_no_interleave(ckpt_root):
    N_PER_THREAD = 50

    def worker(agent):
        for i in range(N_PER_THREAD):
            cr.emit_event(
                "SPRINT_NOTE",
                task_id=None,
                agent=agent,
                phase="meta",
                extra={"text": f"{agent}-{i}"},
            )

    t1 = threading.Thread(target=worker, args=("hermes",))
    t2 = threading.Thread(target=worker, args=("system",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    raw = (ckpt_root / "events.jsonl").read_text()
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    assert len(lines) == N_PER_THREAD * 2, "Expected exactly 100 lines from 2 threads"
    ids = set()
    for ln in lines:
        obj = json.loads(ln)  # must be parseable — no interleaving
        assert obj["event_id"] not in ids, "Duplicate event_id across threads"
        ids.add(obj["event_id"])
    assert len(ids) == N_PER_THREAD * 2


# -----------------------------------------------------------------------------
# Validation rejection cases
# -----------------------------------------------------------------------------

def test_reject_unknown_event_type(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event("NOT_A_REAL_TYPE", task_id="A1", agent="anvil",
                      extra={"text": "x"})


def test_reject_unknown_agent(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event("SPRINT_NOTE", agent="not_an_agent", extra={"text": "x"})


def test_reject_missing_required_extra(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event("MERGED", task_id="A1", agent="anvil", extra={"pr": 1})
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event("TASK_PLANNED", task_id="A1", agent="forge", extra={})


def test_reject_bad_task_id(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event("SPRINT_NOTE", task_id="lowercase1", agent="hermes",
                      extra={"text": "x"})


def test_reject_bad_blocker_key(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.declare_blocker("A1", reason="not_a_real_blocker", agent="anvil")


def test_reject_bad_review_verdict(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.emit_event(
            "REVIEW_POSTED", task_id="A1", agent="vigil", pr=1,
            extra={"reviewer": "vigil", "score": 9.0, "verdict": "GOOD"},
        )


# -----------------------------------------------------------------------------
# publish_artifact
# -----------------------------------------------------------------------------

def test_publish_artifact_copies_and_emits(ckpt_root, tmp_path):
    src = tmp_path / "A1-proposal.md"
    src.write_text("# A1\nhello\n")

    ev = cr.publish_artifact(str(src), task_id="A1", category="proposals", agent="anvil")

    dest = ckpt_root / "raw-artifacts" / "anvil" / "proposals" / "A1-proposal.md"
    assert dest.exists()
    assert dest.read_text() == "# A1\nhello\n"
    assert ev["event_type"] == "ARTIFACT_PUBLISHED"
    assert ev["artifact_path"] == "raw-artifacts/anvil/proposals/A1-proposal.md"
    assert ev["extra"]["category"] == "proposals"
    assert ev["extra"]["src_path"] == str(src)


def test_publish_artifact_missing_src_raises(ckpt_root):
    with pytest.raises(FileNotFoundError):
        cr.publish_artifact("/nope/does-not-exist.md",
                             task_id="A1", category="proposals", agent="anvil")


# -----------------------------------------------------------------------------
# set_task_status / declare_blocker / close_blocker
# -----------------------------------------------------------------------------

def test_set_task_status_tracks_from(ckpt_root):
    ev1 = cr.set_task_status("A1", "PROPOSAL", agent="anvil")
    assert ev1["extra"] == {"from_status": "NOT_STARTED", "to_status": "PROPOSAL"}

    ev2 = cr.set_task_status("A1", "CODE", agent="anvil")
    assert ev2["extra"]["from_status"] == "PROPOSAL"
    assert ev2["extra"]["to_status"] == "CODE"


def test_declare_then_close_blocker(ckpt_root):
    cr.declare_blocker("A1", "waiting_for_vigil_review", agent="anvil")
    ev = cr.close_blocker("A1", agent="anvil")
    assert ev["event_type"] == "BLOCKER_RESOLVED"
    assert ev["extra"]["reason"] == "waiting_for_vigil_review"


def test_close_blocker_without_prior_raises(ckpt_root):
    with pytest.raises(cr.CheckpointValidationError):
        cr.close_blocker("A99", agent="anvil")


# -----------------------------------------------------------------------------
# read_events filters
# -----------------------------------------------------------------------------

def _seed_sample_stream(ckpt_root):
    """Write a hand-crafted stream with known timestamps (bypasses emit_event
    so we can control ts exactly for filter tests)."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    events = [
        ("A1", "anvil", "TASK_PLANNED", now - timedelta(hours=5),
         {"plan_path": "p.md"}),
        ("A1", "anvil", "PROPOSAL_READY", now - timedelta(hours=4),
         {"proposal_path": "x.md"}),
        ("A2", "vigil",  "SPRINT_NOTE", now - timedelta(hours=3),
         {"text": "note"}),
        ("A1", "anvil", "CODE_STARTED", now - timedelta(hours=2),
         {"branch": "anvil/A1"}),
        ("A2", "hermes", "SPRINT_NOTE", now - timedelta(hours=1),
         {"text": "note2"}),
    ]
    path = ckpt_root / "events.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i, (tid, agent, et, ts, extra) in enumerate(events):
            ts_tok = ts.strftime("%Y%m%dT%H%M%SZ")
            obj = {
                "event_id": f"evt_{ts_tok}_{(i+1):06d}",
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": et,
                "task_id": tid,
                "phase": "A",
                "wave": 1,
                "agent": agent,
                "repo": None,
                "branch": None,
                "pr": None,
                "artifact_path": None,
                "status": None,
                "blocker": None,
                "extra": extra,
            }
            f.write(json.dumps(obj) + "\n")
    return now


def test_read_events_no_filter_returns_all(ckpt_root):
    _seed_sample_stream(ckpt_root)
    all_evs = cr.read_events()
    assert len(all_evs) == 5


def test_read_events_filter_event_types(ckpt_root):
    _seed_sample_stream(ckpt_root)
    notes = cr.read_events(event_types=["SPRINT_NOTE"])
    assert len(notes) == 2
    assert all(e["event_type"] == "SPRINT_NOTE" for e in notes)


def test_read_events_filter_task_id(ckpt_root):
    _seed_sample_stream(ckpt_root)
    a1 = cr.read_events(task_id="A1")
    assert len(a1) == 3
    assert all(e["task_id"] == "A1" for e in a1)


def test_read_events_filter_agent(ckpt_root):
    _seed_sample_stream(ckpt_root)
    anvils = cr.read_events(agent="anvil")
    assert len(anvils) == 3


def test_read_events_filter_since(ckpt_root):
    now = _seed_sample_stream(ckpt_root)
    cutoff = (now - timedelta(hours=2, minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = cr.read_events(since=cutoff)
    # Should include CODE_STARTED (-2h) and SPRINT_NOTE (-1h) only.
    assert len(recent) == 2
    assert {e["event_type"] for e in recent} == {"CODE_STARTED", "SPRINT_NOTE"}


def test_read_events_combined_filters(ckpt_root):
    _seed_sample_stream(ckpt_root)
    hits = cr.read_events(task_id="A1", event_types=["CODE_STARTED"])
    assert len(hits) == 1
    assert hits[0]["event_type"] == "CODE_STARTED"


# -----------------------------------------------------------------------------
# lint_checkpoint — one test per gap pattern
# -----------------------------------------------------------------------------

def _write_event(ckpt_root, *, ts, event_type, task_id=None, agent="anvil",
                  pr=None, extra=None, blocker=None, n=1):
    """Append a single event with explicit ts/event_id (bypasses emit_event's
    atomic append so tests can seed past-dated events)."""
    ts_tok = ts.strftime("%Y%m%dT%H%M%SZ")
    obj = {
        "event_id": f"evt_{ts_tok}_{n:06d}",
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": event_type,
        "task_id": task_id,
        "phase": "A",
        "wave": 1,
        "agent": agent,
        "repo": None,
        "branch": None,
        "pr": pr,
        "artifact_path": None,
        "status": None,
        "blocker": blocker,
        "extra": extra or {},
    }
    with open(ckpt_root / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


def test_lint_detects_merged_no_canary(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=3), event_type="MERGED",
                 task_id="A1", extra={"pr": 1, "commit_sha": "abc"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert any("CANARY_STARTED within 2h" in g["issue"] and g["task_id"] == "A1"
               for g in gaps)


def test_lint_ignores_merged_with_canary(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=3), event_type="MERGED",
                 task_id="A1", extra={"pr": 1, "commit_sha": "abc"}, n=1)
    _write_event(ckpt_root, ts=now - timedelta(hours=2, minutes=30),
                 event_type="CANARY_STARTED", task_id="A1",
                 agent="guardian", extra={"baseline_ts": "x"}, n=2)
    gaps = cr.lint_checkpoint(now=now)
    assert not any("CANARY_STARTED within 2h" in g["issue"] for g in gaps)


def test_lint_detects_canary_no_verdict_48h(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=50),
                 event_type="CANARY_STARTED", task_id="A2", agent="guardian",
                 extra={"baseline_ts": "x"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert any("no verdict within 48h" in g["issue"] and g["task_id"] == "A2"
               for g in gaps)


def test_lint_detects_pr_no_review_24h(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=30), event_type="PR_OPENED",
                 task_id="A3", agent="anvil", pr=99,
                 extra={"pr": 99, "title": "A3"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert any("PR_OPENED" in g["issue"] and "pr=99" in g["issue"] for g in gaps)


def test_lint_detects_blocked_over_4h(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=6), event_type="BLOCKED",
                 task_id="A4", agent="anvil",
                 blocker="waiting_for_vigil_review",
                 extra={"reason": "waiting_for_vigil_review"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert any("BLOCKED > 4h" in g["issue"] and g["task_id"] == "A4" for g in gaps)


def test_lint_ignores_resolved_blocker(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=6), event_type="BLOCKED",
                 task_id="A4", agent="anvil",
                 blocker="waiting_for_vigil_review",
                 extra={"reason": "waiting_for_vigil_review"}, n=1)
    _write_event(ckpt_root, ts=now - timedelta(hours=1),
                 event_type="BLOCKER_RESOLVED", task_id="A4", agent="anvil",
                 blocker="waiting_for_vigil_review",
                 extra={"reason": "waiting_for_vigil_review"}, n=2)
    gaps = cr.lint_checkpoint(now=now)
    assert not any("BLOCKED > 4h" in g["issue"] for g in gaps)


def test_lint_detects_stale_heartbeat(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=4),
                 event_type="AGENT_HEARTBEAT", task_id=None, agent="anvil",
                 extra={"current_task": "A1", "phase": "code"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert any("AGENT_HEARTBEAT stale" in g["issue"] and g["agent"] == "anvil"
               for g in gaps)


def test_lint_detects_unresolved_decision_24h(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(hours=30),
                 event_type="DECISION_NEEDED", task_id="A5", agent="hermes",
                 extra={"question_id": "q42", "question": "go?",
                        "options": ["y", "n"]}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    found = [g for g in gaps if "q42" in g["issue"]]
    assert found and found[0]["severity"] == "error"


def test_lint_clean_stream_returns_empty(ckpt_root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _write_event(ckpt_root, ts=now - timedelta(minutes=30), event_type="MERGED",
                 task_id="A6", extra={"pr": 1, "commit_sha": "abc"}, n=1)
    gaps = cr.lint_checkpoint(now=now)
    assert gaps == []
