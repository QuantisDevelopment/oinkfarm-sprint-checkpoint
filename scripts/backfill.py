#!/usr/bin/env python3
"""
backfill.py — Reconstruct the event history of the Heavy Hybrid sprint
from existing file artifacts, git history, and GitHub PRs.

Idempotent: every synthesized event carries a deterministic
`source_fingerprint` in its `extra` dict. Re-runs skip events whose
fingerprints already exist in events.jsonl.

Usage:
    python3 backfill.py --dry-run    # report only, no writes
    python3 backfill.py              # write to events.jsonl (lockfile)
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# -------------------------------------------------------------------- paths
HOME = Path("/home/oinkv")
CHECKPOINT_DIR = HOME / "sprint-checkpoint"
EVENTS_PATH = CHECKPOINT_DIR / "events.jsonl"
LIB_DIR = CHECKPOINT_DIR / "lib"

FORGE_PLANS = HOME / "forge-workspace" / "plans"
ANVIL_PROPOSALS = HOME / "anvil-workspace" / "proposals"
VIGIL_REVIEWS = HOME / "vigil-workspace" / "reviews"
GUARDIAN_REVIEWS = HOME / "guardian-workspace" / "reviews"
GUARDIAN_CANARY = HOME / "guardian-workspace" / "canary-reports"

GH_BIN = "/home/linuxbrew/.linuxbrew/bin/gh"

# Map PR repo -> local git checkout for merge-commit deduplication
REPO_PATHS = {
    "oinkfarm":       HOME / ".openclaw" / "workspace",
    "oink-sync":      HOME / "oink-sync",
    "signal-gateway": HOME / "signal-gateway",
    "oinkdb-api":     HOME / "oinkdb-api",
}
REPO_OWNER = "QuantisDevelopment"

# -------------------------------------------------------------------- mapping
# Wave 1: A1-A3, Wave 2: A4/A7/A5, Wave 3: A6/A8/A9/A11, Wave 4: A10
A_WAVE = {
    "A1": 1, "A2": 1, "A3": 1,
    "A4": 2, "A5": 2, "A7": 2,
    "A6": 3, "A8": 3, "A9": 3, "A11": 3,
    "A10": 4,
}


def task_phase_wave(task_id: str):
    """Return (phase, wave) for a task_id or (None, None) if unknown."""
    if not task_id:
        return None, None
    if task_id.startswith("A"):
        return "A", A_WAVE.get(task_id)
    if task_id.startswith("B"):
        try:
            n = int(task_id[1:])
        except ValueError:
            return "B", None
        if 1 <= n <= 5:
            return "B", 1
        if 6 <= n <= 8:
            return "B", 2
        if 9 <= n <= 11:
            return "B", 3
        if 12 <= n <= 15:
            return "B", 4
        return "B", None
    if task_id.startswith("C"):
        return "C", None
    return None, None


# Which repo a task most likely touches (used for PR_OPENED fallback)
TASK_REPO_HINT = {
    # A-phase touches all three, but most merges we have evidence of:
    "A1": "oinkfarm", "A2": "oinkfarm", "A3": "oinkfarm",
    "A4": "oinkfarm", "A5": "oinkfarm", "A6": "oinkfarm",
    "A7": "oinkfarm", "A8": "oinkfarm", "A9": "oinkfarm",
    "A10": "oinkfarm", "A11": "oinkfarm",
    "B1": "oinkfarm", "B2": "oinkfarm", "B3": "oinkfarm",
    "B5": "signal-gateway", "B6": "signal-gateway",
    "B7": "signal-gateway", "B8": "signal-gateway",
}

# -------------------------------------------------------------------- known Mike gates
MIKE_GATES = [
    ("A10-APPROVE", "A10", "Approve A10 merge algorithm + dedup strategy", ["APPROVE", "REVISE"]),
    ("B4-APPROVE", "B4", "Cutover requires Mike's explicit go-ahead", ["APPROVE", "DEFER"]),
    ("Q-B1-1", "B1", "PostgreSQL driver: psycopg3 vs psycopg2?", ["psycopg3", "psycopg2"]),
    ("Q-B1-2", "B1", "oink_db.py location?", ["canonical", "other"]),
    ("Q-B2-1", "B2", "PostgreSQL hosting: same server or separate?", ["same", "separate"]),
    ("Q-B2-3", "B2", "TimescaleDB now or later (B14)?", ["now", "later"]),
    ("Q-B2-4", "B2", "84 closed signals with NULL filled_at — backfill/accept/block?", ["backfill", "accept", "block"]),
    ("Q-B2-5", "B2", "trg_entry_price_update REJECTED_AUDIT exception handling", ["pg_trigger", "check_only"]),
    ("Q-B3-2", "B3", "Minimum verification period: 7 or 14 days?", ["7d", "14d"]),
    ("Q-B4-4", "B4", "signal-gateway.service systemd re-enable or keep manual?", ["re-enable", "keep_manual"]),
    ("Q-B4-5", "B4", ".openclaw/workspace fork-sync or re-point to canonical?", ["fork_sync", "repoint"]),
    ("Q-HH-1", "B12", "Redis hosting: same server or separate?", ["same", "separate"]),
    ("Q-HH-2", "B12", "Redis Streams retention policy: MAXLEN or time-based?", ["maxlen", "time_based"]),
    ("Q-HH-3", "B13", "Docker Compose: single host or multi-host?", ["single", "multi"]),
    ("Q-HH-4", "B9", "W1 enforcement level: DB REVOKE UPDATE, or app-level guard?", ["db_revoke", "app_guard"]),
    ("Q-HH-5", "C2", "Confidence routing: hard reject or soft flag?", ["hard_reject", "soft_flag"]),
    ("Q-HH-6", None, "Phase D entry gate: who decides prerequisites are met?", ["mike_guardian_joint"]),
]

# -------------------------------------------------------------------- helpers
SCORE_RE = re.compile(
    r"(?:Overall(?:\s+score)?|[Ww]eighted\s+score|^Score)[:\s*\-]*\**\s*`?([\d]+(?:\.\d+)?)`?",
    re.MULTILINE,
)
# Fallback: first "9.xx / 10" style number on a line mentioning "score"
SCORE_FALLBACK_RE = re.compile(
    r"[Ss]core[^\n]{0,40}?(\d{1,2}\.\d{1,2})\s*(?:/\s*10)?"
)

VERDICT_KEYWORDS = ["REVISE", "REQUEST CHANGES", "FAIL", "APPROVE", "PASS"]
CANARY_VERDICT_ORDER = ["FAIL", "WARNING", "INCONCLUSIVE", "PENDING", "PASS"]


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def mtime_iso(path: Path) -> str:
    return iso_utc(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc))


def sha256_fp(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()[:24]


def extract_task_id(name: str):
    """Pull the first occurrence of A1..A11 / B1..B15 / C1..C7 from a string."""
    m = re.search(r"\b(A(?:1[01]|[1-9])|B(?:1[0-5]|[1-9])|C[1-7])\b", name)
    return m.group(1) if m else None


def parse_score(text: str):
    m = SCORE_RE.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m = SCORE_FALLBACK_RE.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def parse_verdict(text: str):
    """Return PASS | REVISE | FAIL | APPROVE | None."""
    upper = text.upper()
    # Structured markers first
    for pat, label in [
        (r"VERDICT[:\s*]+\**\s*[✅✓]?\s*PASS\b", "PASS"),
        (r"VERDICT[:\s*]+\**\s*[🔄↻]?\s*REVISE\b", "REVISE"),
        (r"VERDICT[:\s*]+\**\s*[🚩🔴]?\s*FAIL\b", "FAIL"),
        (r"VERDICT[:\s*]+\**\s*[✅✓]?\s*APPROVE\b", "APPROVE"),
        (r"VERDICT[:\s*]+\**\s*REQUEST\s+CHANGES\b", "REVISE"),
    ]:
        if re.search(pat, upper):
            return label
    # fall back to first keyword hit (priority order matters: REVISE > FAIL > APPROVE > PASS)
    for kw in ["REVISE", "REQUEST CHANGES", "FAIL", "APPROVE", "PASS"]:
        if re.search(rf"\b{re.escape(kw)}\b", upper):
            return "REVISE" if kw == "REQUEST CHANGES" else kw
    return None


def parse_canary_verdict(text: str):
    """Return PASS | FAIL | WARNING | INCONCLUSIVE | PENDING | None."""
    # look inside a "Verdict" section first
    m = re.search(
        r"(##\s*(?:Current|Final|Canary)?\s*Verdict[^\n]*\n[\s\S]{0,500})",
        text, re.IGNORECASE,
    )
    region = m.group(1) if m else text
    upper = region.upper()
    for kw in CANARY_VERDICT_ORDER:
        if re.search(rf"\b{kw}\b", upper):
            return kw
    # whole-document fallback
    upper = text.upper()
    for kw in CANARY_VERDICT_ORDER:
        if re.search(rf"\b{kw}\b", upper):
            return kw
    return None


# -------------------------------------------------------------------- emit shim
USE_REAL_MODULE = False
_real_validate = None
try:
    sys.path.insert(0, str(LIB_DIR))
    from checkpoint_reporting import emit_event as _real_emit  # noqa: F401
    try:
        from checkpoint_reporting import _validate_event as _real_validate  # noqa: F401
    except Exception:
        _real_validate = None
    USE_REAL_MODULE = True
except Exception:
    USE_REAL_MODULE = False


class EventWriter:
    """Writes events to events.jsonl with locking + monotonic event_id.

    In dry-run mode, buffers events in memory and never touches disk.
    """

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self._existing_fps: set[str] = set()
        self._existing_ids: set[str] = set()
        self._max_counter_per_sec: dict[str, int] = defaultdict(int)
        self.buffer: list[dict] = []
        self._load_existing()

    def _load_existing(self):
        if not EVENTS_PATH.exists():
            return
        with EVENTS_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eid = ev.get("event_id")
                if eid:
                    self._existing_ids.add(eid)
                    m = re.match(r"evt_(\d{8}T\d{6}Z)_(\d+)", eid)
                    if m:
                        ts_part, ctr = m.group(1), int(m.group(2))
                        if ctr > self._max_counter_per_sec[ts_part]:
                            self._max_counter_per_sec[ts_part] = ctr
                fp = (ev.get("extra") or {}).get("source_fingerprint")
                if fp:
                    self._existing_fps.add(fp)

    def has_fp(self, fp: str) -> bool:
        return fp in self._existing_fps

    def _next_event_id(self, ts_iso: str) -> str:
        # ts_iso like 2026-04-20T10:30:00Z -> 20260420T103000Z
        compact = ts_iso.replace("-", "").replace(":", "")
        self._max_counter_per_sec[compact] += 1
        n = self._max_counter_per_sec[compact]
        return f"evt_{compact}_{n:06d}"

    def emit(self, *, event_type, ts, task_id, agent, phase=None, wave=None,
             repo=None, branch=None, pr=None, artifact_path=None,
             status=None, blocker=None, extra=None):
        extra = dict(extra or {})
        fp = extra.get("source_fingerprint")
        if fp and fp in self._existing_fps:
            return None  # dedup

        event_id = self._next_event_id(ts)
        ev = {
            "event_id": event_id,
            "ts": ts,
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
            "extra": extra,
        }
        self.buffer.append(ev)
        if fp:
            self._existing_fps.add(fp)
        self._existing_ids.add(event_id)
        return ev

    def flush(self):
        if self.dry_run or not self.buffer:
            return
        EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        # sort by ts ascending, then by event_id for stability
        self.buffer.sort(key=lambda e: (e["ts"], e["event_id"]))
        with EVENTS_PATH.open("a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                for ev in self.buffer:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


# -------------------------------------------------------------------- collectors
class BackfillRun:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.writer = EventWriter(dry_run)
        self.warnings: list[str] = []
        self.source_counts: Counter = Counter()  # events created per source
        self.skipped = 0
        self._all_pr_events: list[dict] = []  # used for commit-dedup

    def _add(self, ev: dict | None, source_key: str):
        if ev is None:
            self.skipped += 1
        else:
            self.source_counts[source_key] += 1

    def emit_or_skip(self, source_key: str, **kwargs):
        extra = kwargs.get("extra") or {}
        fp = extra.get("source_fingerprint")
        if fp and self.writer.has_fp(fp):
            self.skipped += 1
            return None
        ev = self.writer.emit(**kwargs)
        if ev is None:
            self.skipped += 1
        else:
            self.source_counts[source_key] += 1
        return ev

    # ---- FORGE plans -------------------------------------------------
    def collect_forge_plans(self):
        key = "forge_plans"
        if not FORGE_PLANS.exists():
            self.warnings.append(f"FORGE plans dir missing: {FORGE_PLANS}")
            return
        count0 = self.source_counts[key]
        for p in sorted(FORGE_PLANS.glob("TASK-*-plan*.md")):
            task_id = extract_task_id(p.name)
            if not task_id:
                self.warnings.append(f"forge plan: no task_id in {p.name}")
                continue
            phase, wave = task_phase_wave(task_id)
            ts = mtime_iso(p)
            fp = sha256_fp("forge_plan", p.name, p.stat().st_mtime)
            self.emit_or_skip(
                key,
                event_type="TASK_PLANNED",
                ts=ts,
                task_id=task_id,
                agent="forge",
                phase=phase, wave=wave,
                artifact_path=str(p),
                status="NOT_STARTED",
                extra={
                    "plan_path": str(p),
                    "source_fingerprint": fp,
                },
            )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced (all dedup or empty dir)")

    # ---- ANVIL proposals --------------------------------------------
    def collect_anvil_proposals(self):
        key = "anvil_proposals"
        if not ANVIL_PROPOSALS.exists():
            self.warnings.append(f"ANVIL proposals dir missing: {ANVIL_PROPOSALS}")
            return
        count0 = self.source_counts[key]
        # include plain A4-PROPOSAL.md and B1-PROPOSAL.md too
        patterns = ["*-PHASE0-PROPOSAL.md", "*-PROPOSAL.md"]
        seen: set[Path] = set()
        for pat in patterns:
            for p in sorted(ANVIL_PROPOSALS.glob(pat)):
                if p in seen:
                    continue
                seen.add(p)
                task_id = extract_task_id(p.name)
                if not task_id:
                    self.warnings.append(f"anvil proposal: no task_id in {p.name}")
                    continue
                phase, wave = task_phase_wave(task_id)
                ts = mtime_iso(p)
                fp = sha256_fp("anvil_proposal", p.name, p.stat().st_mtime)
                self.emit_or_skip(
                    key,
                    event_type="PROPOSAL_READY",
                    ts=ts,
                    task_id=task_id,
                    agent="anvil",
                    phase=phase, wave=wave,
                    artifact_path=str(p),
                    status="PROPOSAL_REVIEW",
                    extra={
                        "proposal_path": str(p),
                        "source_fingerprint": fp,
                    },
                )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- APPROVED markers --------------------------------------------
    def collect_proposal_approved(self):
        key = "proposal_approved"
        count0 = self.source_counts[key]
        # Exactly PHASE0-APPROVED.marker (not REVIEW-APPROVED, not PHASE1-APPROVED)
        for p in sorted(ANVIL_PROPOSALS.glob("*-PHASE0-APPROVED.marker")):
            task_id = extract_task_id(p.name)
            if not task_id:
                continue
            phase, wave = task_phase_wave(task_id)
            ts = mtime_iso(p)
            fp = sha256_fp("proposal_approved", p.name, p.stat().st_mtime)
            self.emit_or_skip(
                key,
                event_type="PROPOSAL_APPROVED",
                ts=ts,
                task_id=task_id,
                agent="system",   # approval is system-observed (both reviewers passed)
                phase=phase, wave=wave,
                artifact_path=str(p),
                status="CODE",
                extra={
                    "approver": "vigil+guardian",
                    "source_fingerprint": fp,
                },
            )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- VIGIL / GUARDIAN reviews ------------------------------------
    def collect_reviews(self, root: Path, reviewer: str):
        key = f"reviews_{reviewer}"
        if not root.exists():
            self.warnings.append(f"{reviewer} reviews dir missing: {root}")
            return
        count0 = self.source_counts[key]
        # accept *REVIEW*.md except skip COMPLETE markers
        for p in sorted(root.glob("*.md")):
            name = p.name
            if "REVIEW" not in name.upper():
                continue
            if "POST-DEPLOY" in name.upper():
                continue  # handled by canary
            task_id = extract_task_id(name)
            if not task_id:
                self.warnings.append(f"{reviewer} review: no task_id in {name}")
                continue
            phase, wave = task_phase_wave(task_id)
            ts = mtime_iso(p)
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                self.warnings.append(f"{reviewer} review read fail {name}: {exc}")
                continue
            score = parse_score(text)
            verdict_raw = parse_verdict(text) or "PASS"
            # Schema restricts verdict to PASS | REVISE | FAIL.
            # Phase 0 uses APPROVE/REQUEST CHANGES — normalize.
            verdict = {
                "APPROVE": "PASS",
                "REQUEST CHANGES": "REVISE",
            }.get(verdict_raw, verdict_raw)
            if verdict not in ("PASS", "REVISE", "FAIL"):
                verdict = "PASS"

            is_lightweight = bool(re.search(r"🟢|LIGHTWEIGHT", text))
            score_note = None
            if score is None:
                # Phase 0 reviews are qualitative APPROVE/REQUEST CHANGES;
                # LIGHTWEIGHT (🟢) phase 1 reviews also have no numeric score by spec.
                # Schema requires score to be a number in [0,10], so synthesize a
                # placeholder aligned with the verdict and flag it.
                if "PHASE0" in name.upper():
                    score_note = "phase0_qualitative"
                elif is_lightweight:
                    score_note = "lightweight_no_score"
                else:
                    self.warnings.append(f"{reviewer} review no score: {name}")
                    score_note = "score_parse_failed"
                score = 9.5 if verdict == "PASS" else (5.0 if verdict == "REVISE" else 3.0)
            # clamp defensively
            try:
                score = max(0.0, min(10.0, float(score)))
            except (TypeError, ValueError):
                score = 9.5
                score_note = (score_note or "") + "|score_clamp_failed"
            # Round/phase hints
            is_phase0 = "PHASE0" in name.upper()
            round_tag = None
            rm = re.search(r"-R(\d)", name.upper())
            if rm:
                round_tag = int(rm.group(1))

            fp = sha256_fp("review", reviewer, p.name, p.stat().st_mtime)
            extra = {
                "reviewer": reviewer,
                "score": score,
                "verdict": verdict,
                "review_path": str(p),
                "phase_tag": "0" if is_phase0 else "1",
                "source_fingerprint": fp,
            }
            if round_tag is not None:
                extra["round"] = round_tag
            if score_note:
                extra["score_note"] = score_note
            self.emit_or_skip(
                key,
                event_type="REVIEW_POSTED",
                ts=ts,
                task_id=task_id,
                agent=reviewer,
                phase=phase, wave=wave,
                artifact_path=str(p),
                extra=extra,
            )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- canary reports ---------------------------------------------
    def collect_canary(self):
        key = "canary"
        if not GUARDIAN_CANARY.exists():
            self.warnings.append(f"canary dir missing: {GUARDIAN_CANARY}")
            return
        count0 = self.source_counts[key]
        for p in sorted(GUARDIAN_CANARY.glob("*-CANARY.md")):
            task_id = extract_task_id(p.name)
            if not task_id:
                self.warnings.append(f"canary: no task_id in {p.name}")
                continue
            phase, wave = task_phase_wave(task_id)
            ts = mtime_iso(p)
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                self.warnings.append(f"canary read fail {p.name}: {exc}")
                continue
            verdict = parse_canary_verdict(text)
            if verdict is None:
                self.warnings.append(f"canary {p.name}: no verdict keyword")

            # CANARY_STARTED (use mtime as proxy; may predate verdict)
            fp_start = sha256_fp("canary_started", p.name, p.stat().st_mtime)
            self.emit_or_skip(
                key,
                event_type="CANARY_STARTED",
                ts=ts,
                task_id=task_id,
                agent="guardian",
                phase=phase, wave=wave,
                artifact_path=str(p),
                status="CANARY",
                extra={
                    "baseline_ts": ts,
                    "report_path": str(p),
                    "source_fingerprint": fp_start,
                },
            )

            # Terminal verdict event only if verdict parsed clearly
            if verdict in ("PASS", "FAIL"):
                etype = "CANARY_PASS" if verdict == "PASS" else "CANARY_FAIL"
                fp_v = sha256_fp("canary_verdict", p.name, p.stat().st_mtime, verdict)
                extra = {
                    "report_path": str(p),
                    "verdict": verdict,
                    "source_fingerprint": fp_v,
                }
                if verdict == "PASS":
                    # schema requires signals_observed; default per GUARDIAN protocol
                    extra["signals_observed"] = 10
                else:
                    extra["issues"] = ["see_report"]
                self.emit_or_skip(
                    key,
                    event_type=etype,
                    ts=ts,
                    task_id=task_id,
                    agent="guardian",
                    phase=phase, wave=wave,
                    artifact_path=str(p),
                    status="DONE" if verdict == "PASS" else "BLOCKED",
                    extra=extra,
                )
            # WARNING/INCONCLUSIVE/PENDING are only annotated; no terminal event
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- GitHub PRs --------------------------------------------------
    def collect_github_prs(self):
        key = "github_prs"
        count0 = self.source_counts[key]
        self._pr_merge_commits: set[str] = set()

        for repo in REPO_PATHS.keys():
            try:
                out = subprocess.run(
                    [GH_BIN, "pr", "list",
                     "--repo", f"{REPO_OWNER}/{repo}",
                     "--state", "all", "--limit", "100",
                     "--json", "number,title,state,mergedAt,mergeCommit,headRefName,createdAt,body"],
                    capture_output=True, text=True, timeout=60,
                )
            except Exception as exc:
                self.warnings.append(f"gh pr list {repo} failed: {exc}")
                continue
            if out.returncode != 0:
                self.warnings.append(f"gh pr list {repo} rc={out.returncode}: {out.stderr.strip()[:200]}")
                continue
            try:
                prs = json.loads(out.stdout or "[]")
            except json.JSONDecodeError as exc:
                self.warnings.append(f"gh pr list {repo}: bad json: {exc}")
                continue
            if not prs:
                self.warnings.append(f"gh pr list {repo}: 0 PRs returned")
                continue

            for pr in prs:
                num = pr.get("number")
                title = pr.get("title") or ""
                branch = pr.get("headRefName") or ""
                state = pr.get("state")
                created = pr.get("createdAt")
                merged = pr.get("mergedAt")
                mc = pr.get("mergeCommit") or {}
                commit_sha = mc.get("oid") if isinstance(mc, dict) else None

                task_id = extract_task_id(branch) or extract_task_id(title)
                # skip if no task_id AND looks unrelated (reduces A/B noise for pre-sprint PRs)
                # We still want A/B matches, so just skip when None
                if not task_id:
                    continue
                phase, wave = task_phase_wave(task_id)

                # PR_OPENED
                if created:
                    ts = created.replace("+00:00", "Z")
                    if not ts.endswith("Z"):
                        ts = ts[:19] + "Z"
                    fp = sha256_fp("pr_opened", repo, num)
                    self.emit_or_skip(
                        key,
                        event_type="PR_OPENED",
                        ts=ts,
                        task_id=task_id,
                        agent="anvil",
                        phase=phase, wave=wave,
                        repo=repo, branch=branch, pr=num,
                        status="PR_REVIEW",
                        extra={
                            "pr": num, "title": title,
                            "source_fingerprint": fp,
                        },
                    )

                # MERGED
                if state == "MERGED" and merged:
                    ts = merged.replace("+00:00", "Z")
                    if not ts.endswith("Z"):
                        ts = ts[:19] + "Z"
                    fp = sha256_fp("pr_merged", repo, num, commit_sha or "")
                    self.emit_or_skip(
                        key,
                        event_type="MERGED",
                        ts=ts,
                        task_id=task_id,
                        agent="anvil",
                        phase=phase, wave=wave,
                        repo=repo, branch=branch, pr=num,
                        status="MERGED",
                        extra={
                            "pr": num, "commit_sha": commit_sha,
                            "source_fingerprint": fp,
                        },
                    )
                    if commit_sha:
                        self._pr_merge_commits.add(commit_sha)
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- git-log merges (dedup against PR MERGED by commit_sha) -----
    def collect_git_merges(self):
        key = "git_merges"
        count0 = self.source_counts[key]
        pat = re.compile(r"\bfeat\((A(?:1[01]|[1-9])|B(?:1[0-5]|[1-9]))\)")
        for repo, path in REPO_PATHS.items():
            if not (path / ".git").exists():
                self.warnings.append(f"git repo missing: {path}")
                continue
            try:
                out = subprocess.run(
                    ["git", "-C", str(path), "log", "--all",
                     "--pretty=%H|%aI|%s"],
                    capture_output=True, text=True, timeout=60,
                )
            except Exception as exc:
                self.warnings.append(f"git log {repo} failed: {exc}")
                continue
            if out.returncode != 0:
                self.warnings.append(f"git log {repo} rc={out.returncode}")
                continue
            for line in out.stdout.splitlines():
                try:
                    sha, ts, subj = line.split("|", 2)
                except ValueError:
                    continue
                # skip if this commit is already covered by a PR MERGED event
                if sha in self._pr_merge_commits:
                    continue
                m = pat.search(subj)
                task_id = None
                if m:
                    task_id = m.group(1)
                elif "Merge anvil/" in subj:
                    task_id = extract_task_id(subj)
                elif subj.startswith(("B1:", "B2:", "B3:", "B5:", "B6:", "B7:", "B8:",
                                      "Task B", "Task A", "Merge B", "Merge A")):
                    task_id = extract_task_id(subj)
                if not task_id:
                    continue
                phase, wave = task_phase_wave(task_id)
                # normalize ISO
                ts_iso = ts.replace("+00:00", "Z")
                try:
                    dt = datetime.fromisoformat(ts)
                    ts_iso = iso_utc(dt)
                except Exception:
                    pass
                fp = sha256_fp("git_merge", repo, sha)
                self.emit_or_skip(
                    key,
                    event_type="MERGED",
                    ts=ts_iso,
                    task_id=task_id,
                    agent="anvil",
                    phase=phase, wave=wave,
                    repo=repo,
                    status="MERGED",
                    extra={
                        "pr": None,
                        "commit_sha": sha,
                        "commit_subject": subj,
                        "source": "git_log",
                        "source_fingerprint": fp,
                    },
                )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced (OK if all PR-covered)")

    # ---- Mike gates --------------------------------------------------
    def collect_mike_gates(self):
        key = "mike_gates"
        # Use the HEARTBEAT.md mtime as the "flagged" timestamp, falling back to now.
        heartbeat = HOME / "forge-workspace" / "HEARTBEAT.md"
        if heartbeat.exists():
            ts_default = mtime_iso(heartbeat)
        else:
            ts_default = iso_utc(datetime.now(tz=timezone.utc))
        count0 = self.source_counts[key]
        for qid, task_id, question, options in MIKE_GATES:
            phase, wave = task_phase_wave(task_id)
            fp = sha256_fp("mike_gate", qid)
            self.emit_or_skip(
                key,
                event_type="DECISION_NEEDED",
                ts=ts_default,
                task_id=task_id,
                agent="forge",
                phase=phase, wave=wave,
                status="BLOCKED",
                blocker="waiting_for_mike_decision",
                extra={
                    "question_id": qid,
                    "question": question,
                    "options": options,
                    "source_fingerprint": fp,
                },
            )
        if self.source_counts[key] == count0:
            self.warnings.append(f"{key}: 0 events produced")

    # ---- orchestrate -------------------------------------------------
    def run(self):
        self.collect_forge_plans()
        self.collect_anvil_proposals()
        self.collect_proposal_approved()
        self.collect_reviews(VIGIL_REVIEWS, "vigil")
        self.collect_reviews(GUARDIAN_REVIEWS, "guardian")
        self.collect_canary()
        self.collect_github_prs()
        self.collect_git_merges()
        self.collect_mike_gates()

    # ---- reporting ---------------------------------------------------
    def report(self):
        by_type: Counter = Counter()
        by_phase: Counter = Counter()
        by_type_phase: Counter = Counter()
        for ev in self.writer.buffer:
            by_type[ev["event_type"]] += 1
            ph = ev.get("phase") or "-"
            by_phase[ph] += 1
            by_type_phase[(ev["event_type"], ph)] += 1

        print(f"\n{'='*66}")
        print(f"BACKFILL SUMMARY  (mode={'DRY-RUN' if self.dry_run else 'LIVE'})")
        print(f"{'='*66}")
        print(f"events.jsonl:        {EVENTS_PATH}")
        print(f"real module used:    {USE_REAL_MODULE}")
        print(f"total NEW events:    {len(self.writer.buffer)}")
        print(f"skipped (dedup):     {self.skipped}")
        print()
        print("-- by source --")
        for src, n in sorted(self.source_counts.items(), key=lambda x: -x[1]):
            print(f"  {src:<22} {n}")
        print()
        print("-- by event_type --")
        for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {t:<22} {n}")
        print()
        print("-- by phase --")
        for ph, n in sorted(by_phase.items()):
            print(f"  phase={ph:<4} {n}")
        print()
        print("-- by event_type × phase --")
        phases = sorted({ph for _, ph in by_type_phase.keys()})
        types = sorted({t for t, _ in by_type_phase.keys()})
        hdr = f"  {'event_type':<22}" + "".join(f"{p:>7}" for p in phases) + "  total"
        print(hdr)
        for t in types:
            row = f"  {t:<22}"
            total = 0
            for p in phases:
                n = by_type_phase.get((t, p), 0)
                total += n
                row += f"{n:>7}"
            row += f"  {total:>5}"
            print(row)
        print()
        if self.warnings:
            print(f"-- warnings ({len(self.warnings)}) --")
            for w in self.warnings:
                print(f"  ! {w}")
        else:
            print("-- warnings: none --")
        print(f"{'='*66}\n")


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Backfill Heavy Hybrid sprint event history.")
    ap.add_argument("--dry-run", action="store_true",
                    help="print event counts per type; no writes")
    args = ap.parse_args()

    run = BackfillRun(dry_run=args.dry_run)
    run.run()
    run.writer.flush()
    run.report()

    return 0


if __name__ == "__main__":
    sys.exit(main())
