#!/usr/bin/env python3
"""OinkFarm Implementation Foresight Sprint — checkpoint dashboard generator.

Crawls live agent workspaces (FORGE / ANVIL / VIGIL / GUARDIAN / Hermes / OinkV)
and emits a static dashboard (HTML + JSON) under ./docs/ (GitHub Pages source).

Read-only outside ./docs/. Missing files are treated as "not yet"; never raises.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# --------------------------------------------------------------------------- #
# Optional lib/checkpoint_reporting.py — the canonical reader lives there.
# If unavailable we fall back to inline jsonl parsing (below).
# --------------------------------------------------------------------------- #
_LIB_DIR = Path(__file__).resolve().parent / "lib"
if _LIB_DIR.exists():
    sys.path.insert(0, str(_LIB_DIR))
try:
    from checkpoint_reporting import (  # type: ignore
        read_events as _lib_read_events,
        lint_checkpoint as _lib_lint_checkpoint,
    )
    _HAS_LIB = True
except Exception:
    _HAS_LIB = False
    _lib_read_events = None  # type: ignore
    _lib_lint_checkpoint = None  # type: ignore

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent
HOME = Path("/home/oinkv")
ANVIL, FORGE = HOME / "anvil-workspace", HOME / "forge-workspace"
VIGIL, GUARDIAN = HOME / "vigil-workspace", HOME / "guardian-workspace"
HERMES_WS = HOME / "hermes-workspace"
HERMES_CRON = HOME / ".hermes/cron/output/c5fe3ace64fd"
SITE, STATIC, TEMPLATES = ROOT / "docs", ROOT / "static", ROOT / "templates"

# --- Event stream -----------------------------------------------------------
EVENTS_JSONL = ROOT / "events.jsonl"
EVENT_SCHEMA_VERSION = "1.0"
# Switch to crawler fallback if fewer than this many events are on disk
MIN_EVENTS_FOR_PRIMARY = 10
# Override via env for tests
EVENTS_JSONL_OVERRIDE = os.environ.get("SPRINT_EVENTS_JSONL")
if EVENTS_JSONL_OVERRIDE:
    EVENTS_JSONL = Path(EVENTS_JSONL_OVERRIDE)

# Seed set (used when events.jsonl is empty AND crawler fallback not desired).
# Dynamic discovery from events supplements this; nothing here is authoritative.
SEED_TASKS = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "B1"]
TASKS = list(SEED_TASKS)
TIERS = {"A1": "CRITICAL", "A2": "CRITICAL", "A3": "STANDARD",
         "A4": "STANDARD", "A5": "STANDARD", "A6": "STANDARD",
         "A7": "CRITICAL", "A8": "STANDARD", "A9": "LIGHTWEIGHT",
         "A10": "CRITICAL", "A11": "LIGHTWEIGHT", "B1": "CRITICAL"}
TIER_EMOJI = {"CRITICAL": "🔴", "STANDARD": "🟡", "LIGHTWEIGHT": "🟢"}
TASK_REPO_HINT = {"A1": "oinkfarm", "A2": "oink-sync", "A3": "oinkfarm",
                  "A4": "oink-sync", "A5": "signal-gateway", "A6": "signal-gateway",
                  "A7": "signal-gateway", "A8": "oinkfarm", "A9": "oinkfarm",
                  "A10": "oinkfarm", "A11": "oinkfarm", "B1": "oink-sync"}

WAVES = [
    {"name": "Wave 1 (Phase A)", "tasks": ["A1", "A2", "A3"]},
    {"name": "Wave 2 (Phase A)", "tasks": ["A4", "A7", "A5"]},
    {"name": "Wave 3 (Phase A)", "tasks": ["A6", "A8", "A9", "A11"]},
    {"name": "Wave 4 (Phase A)", "tasks": ["A10"]},
    {"name": "Wave B1 (Phase B)", "tasks": ["B1"]},
    {"name": "Phase B B2–B5", "tasks": [], "future": True},
    {"name": "Phase C (scoped)", "tasks": [], "future": True},
]

AGENTS = [
    {"id": "forge", "name": "FORGE", "emoji": "🔥",
     "workspace": FORGE, "role": "Technical Execution Planner"},
    {"id": "anvil", "name": "ANVIL", "emoji": "⚒️",
     "workspace": ANVIL, "role": "Implementation Lead"},
    {"id": "vigil", "name": "VIGIL", "emoji": "🔍",
     "workspace": VIGIL, "role": "Code Review + Scoring"},
    {"id": "guardian", "name": "GUARDIAN", "emoji": "🛡️",
     "workspace": GUARDIAN, "role": "Data Integrity + Canary"},
    {"id": "hermes", "name": "Hermes", "emoji": "🪽",
     "workspace": HERMES_WS, "role": "Sprint Orchestrator",
     "aux_paths": [HERMES_CRON]},
    {"id": "oinkv", "name": "OinkV", "emoji": "🐷",
     "workspace": FORGE / "plans", "role": "Plan Auditor",
     "file_glob": "OINKV-AUDIT*"},
]

STATUS_LABEL = {
    "DONE": "Done", "CANARY": "Canary", "PR_REVIEW": "PR Review",
    "CODE": "Coding", "PROPOSAL_REVIEW": "Proposal Review",
    "PROPOSAL": "Proposal", "PLANNED": "Planned",
    "BLOCKED": "Blocked", "NOT_STARTED": "Not Started",
}

BLOCKER_HUMAN_LABELS = {
    "waiting_for_mike": "Mike decision",
    "waiting_for_mike_plan_approval": "Mike plan approval",
    "waiting_for_proposal_approval": "Proposal approval (VIGIL + GUARDIAN)",
    "waiting_for_vigil_review": "VIGIL review",
    "waiting_for_guardian_review": "GUARDIAN review",
    "waiting_for_canary": "GUARDIAN canary",
    "design_clarification_needed": "Design clarification (Mike)",
}

CEST = timezone(timedelta(hours=2))

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def safe_read(path: Path, limit: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:limit] if limit else text
    except Exception:
        return ""


def safe_mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return None


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds") if dt else None


def humanize(dt: datetime | None, now: datetime) -> str:
    if dt is None:
        return "—"
    secs = (now - dt).total_seconds()
    if secs < 0: return "just now"
    if secs < 60: return f"{int(secs)}s ago"
    if secs < 3600: return f"{int(secs // 60)}m ago"
    if secs < 86400:
        h, m = int(secs // 3600), int((secs % 3600) // 60)
        return f"{h}h {m}m ago" if m else f"{h}h ago"
    return f"{int(secs // 86400)}d ago"


def newest_mtime(path: Path, file_glob: str | None = None) -> datetime | None:
    if not path.exists():
        return None
    newest: float | None = None
    try:
        if path.is_dir():
            for p in path.rglob(file_glob or "*"):
                try:
                    if p.is_file():
                        m = p.stat().st_mtime
                        if newest is None or m > newest:
                            newest = m
                except Exception:
                    continue
        else:
            newest = path.stat().st_mtime
    except Exception:
        return None
    return datetime.fromtimestamp(newest, tz=timezone.utc) if newest else None


def status_light(dt: datetime | None, now: datetime) -> str:
    if dt is None: return "red"
    age = (now - dt).total_seconds()
    if age < 30 * 60: return "green"
    if age < 3 * 3600: return "yellow"
    return "red"


def find_first(paths: list[Path]) -> Path | None:
    return next((p for p in paths if p.exists()), None)


def _size(p: Path) -> int:
    try: return p.stat().st_size
    except Exception: return 0


def _extract_title(p: Path) -> str:
    text = safe_read(p, limit=4096)
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return p.stem


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #

SCORE_PATTERNS = [
    r"\*\*OVERALL\*\*[^|\n]*\|[^|\n]*\|[^|\n]*\|\s*\**([0-9]\.[0-9]{1,2}|10\.0{1,2}|10)\**",
    r"OVERALL[^|\n]*\|[^|\n]*\|\s*\**([0-9]\.[0-9]{1,2}|10\.0{1,2}|10)\**",
    r"Overall(?:\s+Score)?\s*[:=]\s*\*?\*?([0-9]\.[0-9]{1,2}|10\.0{1,2}|10)",
    r"\*\*([0-9]\.[0-9]{2}|10\.00)\*\*\s*/\s*10",
]


def extract_score(text: str) -> float | None:
    if not text:
        return None
    for pat in SCORE_PATTERNS:
        m = re.search(pat, text)
        if m:
            try:
                v = float(m.group(1))
                if 0 <= v <= 10.01:
                    return v
            except ValueError:
                continue
    return None


def extract_verdict(text: str) -> str | None:
    if not text:
        return None
    low = text.lower()
    header = re.search(r"(?i)##?\s*verdict[^\n]*\n[^\n]*", text)
    scope = (header.group(0) if header else text[:4000]).lower()
    if "lgtm" in low: return "LGTM"
    if "block" in scope: return "BLOCK"
    if "concerns" in scope: return "CONCERNS"
    if "request changes" in low or "request_changes" in low: return "REVISE"
    if re.search(r"✅\s*pass", scope) or "pass" in scope: return "PASS"
    if "approve" in scope: return "APPROVE"
    return None


def extract_canary_verdict(text: str) -> str | None:
    if not text:
        return None
    # Prefer explicit Hermes disposition (overrides body text)
    if re.search(r"(?im)Hermes Disposition[\s\S]*?Canary verdict:\s*✅?\s*PASS", text) or \
       re.search(r"(?im)Resolution:\s*Canary upgraded to\s*✅?\s*PASS", text) or \
       re.search(r"(?im)^\s*\*\*Verdict:\s*✅?\s*PASS", text):
        return "PASS"
    low = text.lower()
    if re.search(r"canary\s*status[^\n]*fail", low): return "FAIL"
    if re.search(r"canary\s*status[^\n]*warn", low): return "WARN"
    if re.search(r"✅\s*pass", text.lower()) or ("pass" in low and "fail" not in low[:2000]):
        return "PENDING" if "pending" in low[:2000] else "PASS"
    if "pending" in low: return "PENDING"
    return None


URL_RE = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/(?:pull|commit)/([\w.-]+)")
MERGED_AT_RE = re.compile(r"Merged at[:\s]+([0-9T:\-Z.+]+)")


def parse_merged_marker(text: str) -> dict[str, Any]:
    """Extract PRs, commits, merged-at from a MERGED marker (free-form markdown)."""
    result: dict[str, Any] = {"prs": [], "merged_at": None}
    if not text:
        return result
    seen: set[tuple[str, int]] = set()
    for m in URL_RE.finditer(text):
        _, repo, ref = m.group(1), m.group(2), m.group(3)
        if "/pull/" in m.group(0):
            key = (repo, int(ref))
            if key in seen: continue
            seen.add(key)
            result["prs"].append({
                "repo": repo, "number": int(ref), "pr_url": m.group(0),
                "merge_commit": None, "commit_url": None,
            })
    commits = re.findall(
        r"(?i)(?:merge\s+commit|MERGE_COMMIT)[^\n]*?\b([a-f0-9]{7,40})\b", text
    )
    for i, pr in enumerate(result["prs"]):
        if i < len(commits):
            sha = commits[i]
            pr["merge_commit"] = sha
            pr["commit_url"] = f"https://github.com/QuantisDevelopment/{pr['repo']}/commit/{sha}"
    # Fallback: KEY=value style (A3 uses this).
    if not result["prs"]:
        pn = re.search(r"PR_NUMBER\s*=\s*(\d+)", text)
        rm = re.search(r"REPO\s*=\s*(?:QuantisDevelopment/)?([\w\-.]+)", text)
        cm = re.search(r"MERGE_COMMIT\s*=\s*([a-f0-9]{7,40})", text)
        # Free-form fallback (e.g. A4: "oink-sync PR #7" + "**Merge commit:** <sha>")
        if not (pn and rm):
            fm = re.search(r"([a-zA-Z][\w\-]+)\s+PR\s*#(\d+)", text)
            if fm:
                rm = rm or re.match(r"(.*)", fm.group(1))
                pn = pn or re.match(r"(.*)", fm.group(2))
                repo_name, num = fm.group(1), int(fm.group(2))
            else:
                # A7-style: "PR: #130 (owner/repo)" → extract trailing repo from parens
                am = re.search(r"PR:\s*#(\d+)\s*\(([^)]+)\)", text)
                if am:
                    num = int(am.group(1))
                    parens = am.group(2).strip()
                    # parens may be "owner/repo" — take last segment as repo
                    repo_name = parens.split("/")[-1] if "/" in parens else parens
                else:
                    repo_name = rm.group(1) if rm else None
                    num = int(pn.group(1)) if pn else None
        else:
            repo_name, num = rm.group(1), int(pn.group(1))
        if not cm:
            # Try multiple commit patterns: "merge commit: <sha>", "merge_sha: <sha>"
            cm = (re.search(r"(?i)merge\s*commit[:\s*]+`?([a-f0-9]{7,40})`?", text)
                  or re.search(r"(?i)merge[_\s]sha\s*[:=]\s*`?([a-f0-9]{7,40})`?", text))
        if repo_name and num:
            pr = {
                "repo": repo_name, "number": num,
                "pr_url": f"https://github.com/QuantisDevelopment/{repo_name}/pull/{num}",
                "merge_commit": cm.group(1) if cm else None,
                "commit_url": None,
            }
            if pr["merge_commit"]:
                pr["commit_url"] = (
                    f"https://github.com/QuantisDevelopment/{repo_name}/commit/{pr['merge_commit']}"
                )
            result["prs"].append(pr)
    # Last-resort: URL_RE-matched PRs without commits → try merge_sha pattern
    else:
        for pr in result["prs"]:
            if not pr["merge_commit"]:
                cm = re.search(r"(?i)merge[_\s]sha\s*[:=]\s*`?([a-f0-9]{7,40})`?", text)
                if cm:
                    pr["merge_commit"] = cm.group(1)
                    pr["commit_url"] = f"https://github.com/QuantisDevelopment/{pr['repo']}/commit/{cm.group(1)}"
    m = MERGED_AT_RE.search(text) or re.search(r"MERGED_AT\s*=\s*([0-9T:\-Z.+]+)", text)
    if m:
        result["merged_at"] = m.group(1).strip()
    return result


HB_TASK = re.compile(r'"?current_task"?\s*[:=]\s*"?([A-Za-z0-9.\-_ ]+?)"?\s*[,\n}]')
HB_PHASE = re.compile(r'"?current_phase"?\s*[:=]\s*"?([A-Za-z0-9_\- ]+?)"?\s*[,\n}]')
HB_BLOCKERS = re.compile(r'"?blockers"?\s*[:=]\s*(\[[^\]]*\])')
HB_BRANCH = re.compile(r'"?branch"?\s*[:=]\s*"?([A-Za-z0-9/_\-.]+?)"?\s*[,\n}]')


def parse_heartbeat(text: str) -> dict[str, Any]:
    if not text: return {}
    out: dict[str, Any] = {}
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    scope = fence.group(1) if fence else text[:4000]
    if (m := HB_TASK.search(scope)): out["current_task"] = m.group(1).strip()
    if (m := HB_PHASE.search(scope)): out["current_phase"] = m.group(1).strip()
    if (m := HB_BLOCKERS.search(scope)):
        out["blockers"] = re.findall(r'"([^"]+)"', m.group(1))
    if (m := HB_BRANCH.search(scope)) and m.group(1) not in ("null", "None"):
        out["branch"] = m.group(1).strip()
    return out


# --------------------------------------------------------------------------- #
# Crawlers
# --------------------------------------------------------------------------- #

ARTIFACT_MAP = [
    # (key, path_template, optional score/verdict carry)
    ("forge_plan",       "{FORGE}/plans/TASK-{task}-plan.md"),
    ("proposal_p0",      "{ANVIL}/proposals/{task}-PHASE0-PROPOSAL.md"),
    ("proposal_alt",     "{ANVIL}/proposals/{task}-PROPOSAL.md"),
    ("ready",            "{ANVIL}/proposals/{task}-READY-FOR-REVIEW.marker"),
    ("phase0_approved",  "{ANVIL}/proposals/{task}-PHASE0-APPROVED.marker"),
    ("merged",           "{ANVIL}/{task}-MERGED.marker"),
    ("vigil_phase0",     "{VIGIL}/reviews/{task}-VIGIL-PHASE0-REVIEW.md"),
    ("vigil_phase1",     "{VIGIL}/reviews/{task}-VIGIL-PHASE1-REVIEW.md"),
    ("vigil_legacy",     "{VIGIL}/reviews/{task}-VIGIL-REVIEW.md"),
    ("guardian_phase0",  "{GUARDIAN}/reviews/{task}-GUARDIAN-PHASE0-REVIEW.md"),
    ("guardian_phase1",  "{GUARDIAN}/reviews/{task}-GUARDIAN-PHASE1-REVIEW.md"),
    ("guardian_legacy",  "{GUARDIAN}/reviews/{task}-GUARDIAN-REVIEW.md"),
    ("hermes",           "{HERMES}/{task}-HERMES-REVIEW.md"),
    ("canary",           "{GUARDIAN}/canary-reports/{task}-CANARY.md"),
    ("canary_complete",  "{GUARDIAN}/canary-reports/{task}-CANARY-COMPLETE.marker"),
]


def _task_artifacts(task: str) -> dict[str, Path]:
    root = {"FORGE": FORGE, "ANVIL": ANVIL, "VIGIL": VIGIL,
            "GUARDIAN": GUARDIAN, "HERMES": HERMES_WS}
    found: dict[str, Path] = {}
    for key, tpl in ARTIFACT_MAP:
        p = Path(tpl.format(task=task, **{k: str(v) for k, v in root.items()}))
        if p.exists():
            found[key] = p
    # Consolidate proposal naming.
    if "proposal_p0" in found: found["proposal"] = found["proposal_p0"]
    elif "proposal_alt" in found: found["proposal"] = found["proposal_alt"]
    # Consolidate Phase 1 / legacy review naming.
    for agent in ("vigil", "guardian"):
        if f"{agent}_phase1" not in found and f"{agent}_legacy" in found:
            found[f"{agent}_phase1"] = found[f"{agent}_legacy"]
    return found


def _derive_status(a: dict[str, Path], canary_verdict: str | None) -> str:
    if "merged" in a and canary_verdict == "PASS":
        return "DONE"
    if "merged" in a:
        return "CANARY"
    if "phase0_approved" in a:
        return "CODE"
    if "ready" in a:
        return "PROPOSAL_REVIEW"
    if "proposal" in a:
        return "PROPOSAL"
    if "forge_plan" in a:
        return "PLANNED"
    return "NOT_STARTED"


def _timeline(a: dict[str, Path], scores: dict, verdicts: dict,
              canary_verdict: str | None) -> list[dict[str, Any]]:
    rows: list[tuple[str, str, Path, str | None, float | None]] = [
        ("FORGE plan published",           "FORGE",        a.get("forge_plan"),      None, None),
        ("Phase 0 proposal written",       "ANVIL",        a.get("proposal"),        None, None),
        ("Ready for proposal review",      "ANVIL",        a.get("ready"),           None, None),
        ("VIGIL Phase 0 review",           "VIGIL",        a.get("vigil_phase0"),    None, None),
        ("GUARDIAN Phase 0 review",        "GUARDIAN",     a.get("guardian_phase0"), None, None),
        ("Phase 0 approved",               "Orchestrator", a.get("phase0_approved"), None, None),
        ("VIGIL Phase 1 review",           "VIGIL",        a.get("vigil_phase1"),    verdicts.get("vigil"),    scores.get("vigil")),
        ("GUARDIAN Phase 1 review",        "GUARDIAN",     a.get("guardian_phase1"), verdicts.get("guardian"), scores.get("guardian")),
        (f"Hermes sanity check — {verdicts.get('hermes') or '—'}",
                                           "Hermes",       a.get("hermes"),          verdicts.get("hermes"), None),
        ("Merged",                         "ANVIL",        a.get("merged"),          None, None),
        (f"Canary {canary_verdict or 'PENDING'}",
                                           "GUARDIAN",     a.get("canary"),          canary_verdict, None),
        ("Canary complete",                "GUARDIAN",     a.get("canary_complete"), None, None),
    ]
    events = []
    for label, actor, path, verdict, score in rows:
        if not path:
            continue
        extended = label
        if score is not None:
            extended = f"{label} — {score:.2f}"
        events.append({
            "label": extended, "actor": actor,
            "path": str(path), "mtime": iso(safe_mtime(path)),
            "verdict": verdict, "score": score,
        })
    events.sort(key=lambda e: e["mtime"] or "")
    return events


def crawl_task(task: str, _now: datetime) -> dict[str, Any]:
    tier = TIERS.get(task, "STANDARD")
    a = _task_artifacts(task)
    scores = {"vigil": None, "guardian": None, "hermes": None}
    verdicts = {"vigil": None, "guardian": None, "hermes": None}

    if "vigil_phase1" in a:
        text = safe_read(a["vigil_phase1"])
        scores["vigil"] = extract_score(text)
        verdicts["vigil"] = extract_verdict(text)
    elif "vigil_phase0" in a:
        verdicts["vigil"] = extract_verdict(safe_read(a["vigil_phase0"])) or "APPROVE"
    if "guardian_phase1" in a:
        text = safe_read(a["guardian_phase1"])
        scores["guardian"] = extract_score(text)
        verdicts["guardian"] = extract_verdict(text)
    elif "guardian_phase0" in a:
        verdicts["guardian"] = extract_verdict(safe_read(a["guardian_phase0"])) or "APPROVE"
    if "hermes" in a:
        verdicts["hermes"] = extract_verdict(safe_read(a["hermes"]))

    canary = {"verdict": None, "path": None, "mtime": None}
    if "canary" in a:
        canary["verdict"] = extract_canary_verdict(safe_read(a["canary"])) or "PENDING"
        canary["path"] = str(a["canary"])
        canary["mtime"] = iso(safe_mtime(a["canary"]))
    elif "canary_complete" in a:
        canary["verdict"] = "PASS"
        canary["mtime"] = iso(safe_mtime(a["canary_complete"]))

    prs, merged_at = [], None
    if "merged" in a:
        parsed = parse_merged_marker(safe_read(a["merged"]))
        prs, merged_at = parsed["prs"], parsed["merged_at"]

    status = _derive_status(a, canary["verdict"])
    timeline = _timeline(a, scores, verdicts, canary["verdict"])
    last = max((e["mtime"] for e in timeline if e["mtime"]), default=None)

    return {
        "id": task, "tier": tier, "tier_emoji": TIER_EMOJI[tier],
        "repo_hint": TASK_REPO_HINT.get(task),
        "status": status, "status_label": STATUS_LABEL[status],
        "prs": prs, "scores": scores, "verdicts": verdicts,
        "canary": canary, "merged_at": merged_at,
        "last_activity": last, "timeline": timeline,
        "artifacts": {k: str(v) for k, v in a.items()},
    }


def crawl_agent(agent: dict[str, Any], now: datetime) -> dict[str, Any]:
    ws: Path = agent["workspace"]
    last = newest_mtime(ws, agent.get("file_glob"))
    for aux in agent.get("aux_paths") or []:
        aux_last = newest_mtime(aux)
        if aux_last and (last is None or aux_last > last):
            last = aux_last
    heartbeat = ws / "HEARTBEAT.md"
    hb = parse_heartbeat(safe_read(heartbeat)) if heartbeat.exists() else {}
    return {
        "id": agent["id"], "name": agent["name"], "emoji": agent["emoji"],
        "role": agent["role"], "workspace": str(ws),
        "last_active": iso(last), "last_active_human": humanize(last, now),
        "light": status_light(last, now), "heartbeat": hb,
    }


# --- Cron narrative ---

CRON_FILENAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})\.md")


def _parse_cron_entry(path: Path) -> dict[str, Any] | None:
    text = safe_read(path)
    if not text: return None
    m = re.search(r"##\s*Response\s*\n([\s\S]*)$", text)
    response = (m.group(1) if m else text).strip()
    if response.startswith("[SILENT]"):
        return None

    fm = CRON_FILENAME_RE.match(path.name)
    if fm:
        local = datetime.fromisoformat(
            f"{fm.group(1)}T{fm.group(2)}:{fm.group(3)}:{fm.group(4)}"
        ).replace(tzinfo=CEST)
        dt_utc = local.astimezone(timezone.utc)
    else:
        dt_utc = safe_mtime(path) or datetime.now(timezone.utc)

    actions: list[str] = []
    next_action: str | None = None
    blocker: str | None = None
    mode = None
    header = None
    for raw in response.splitlines():
        stripped = raw.strip()
        low = stripped.lower()
        if not header and "SPRINT STATUS" in stripped.upper():
            header = stripped.lstrip("`").strip()
            continue
        if low.startswith("actions taken") or low.startswith("## actions"):
            mode = "actions"; continue
        if low.startswith("next auto-action") or low.startswith("next action"):
            mode = "next"
            after = stripped.split(":", 1)
            if len(after) == 2 and after[1].strip():
                next_action = after[1].strip()
            continue
        if low.startswith("blocker") or low.startswith("escalation"):
            mode = "blocker"
            after = stripped.split(":", 1)
            if len(after) == 2 and after[1].strip():
                blocker = after[1].strip()
            continue
        if mode == "actions" and stripped.startswith(("•", "-", "*")):
            actions.append(stripped.lstrip("•-* ").strip())
            continue
        if mode == "next" and stripped.startswith(("•", "-", "*")):
            item = stripped.lstrip("•-* ").strip()
            next_action = f"{next_action} — {item}" if next_action else item
            continue
        if mode == "blocker" and stripped:
            blocker = f"{blocker} {stripped}" if blocker else stripped
            continue
        if stripped == "" or stripped.startswith("```"):
            mode = None

    if not any([actions, next_action, blocker, header]):
        return None
    return {
        "time_utc": iso(dt_utc),
        "time_local": dt_utc.astimezone(CEST).isoformat(timespec="minutes"),
        "header": header,
        "actions": actions[:5],
        "next": next_action,
        "blocker": blocker,
        "path": str(path),
    }


def crawl_cron(limit: int = 40) -> list[dict[str, Any]]:
    if not HERMES_CRON.exists(): return []
    out = []
    for p in sorted(HERMES_CRON.glob("*.md"), reverse=True):
        entry = _parse_cron_entry(p)
        if entry:
            out.append(entry)
        if len(out) >= limit:
            break
    return out


# --- Plans / audits ---

def crawl_plans() -> dict[str, list[dict[str, Any]]]:
    plan_dir = FORGE / "plans"
    def _entry(p: Path) -> dict[str, Any]:
        return {"path": str(p), "name": p.name, "title": _extract_title(p),
                "size_bytes": _size(p), "mtime": iso(safe_mtime(p))}
    if not plan_dir.exists():
        return {"plans": [], "audits": []}
    return {
        "plans":  [_entry(p) for p in sorted(plan_dir.glob("TASK-A*-plan.md"))],
        "audits": [_entry(p) for p in sorted(plan_dir.glob("OINKV-AUDIT*.md"))],
    }


# --- Blockers ---

def derive_blockers(agents: list[dict[str, Any]],
                    cron: list[dict[str, Any]],
                    tasks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in agents:
        for b in (a.get("heartbeat") or {}).get("blockers", []) or []:
            out.append({
                "agent": a["name"], "agent_emoji": a["emoji"],
                "raw": b, "label": BLOCKER_HUMAN_LABELS.get(b, b.replace("_", " ")),
                "severity": "mike" if "mike" in b else "auto",
                "current_task": a["heartbeat"].get("current_task"),
                "current_phase": a["heartbeat"].get("current_phase"),
            })

    # Build a set of task IDs that are fully resolved (DONE / CANARY PASS)
    resolved_tasks: set[str] = set()
    for t in (tasks or []):
        tid = t.get("id")
        status = (t.get("status") or "").upper()
        # canary may be a dict {verdict: ...} or a scalar
        canary_obj = t.get("canary") or {}
        if isinstance(canary_obj, dict):
            canary_verdict = (canary_obj.get("verdict") or "").upper()
        else:
            canary_verdict = str(canary_obj or "").upper()
        # Also check top-level field for backwards compat
        canary_verdict = canary_verdict or (t.get("canary_verdict") or "").upper()
        if not tid:
            continue
        if status == "DONE":
            resolved_tasks.add(tid)
        elif status == "CANARY" and canary_verdict == "PASS":
            resolved_tasks.add(tid)
        # Also: merged tasks with canary PASS count as resolved
        elif t.get("merge_commit") and canary_verdict == "PASS":
            resolved_tasks.add(tid)
        # And: any task with an MERGED marker AND current status != BLOCKED is effectively done
        # (canary might not have completed yet but no actual blocker exists)
        elif t.get("merge_commit") and status not in ("BLOCKED", "PROPOSAL"):
            resolved_tasks.add(tid)

    # Also: collect freshly-resolved blockers by scanning cron for "approved by" / "decided" language
    # from recent Hermes cycles. If the blocker body contains phrases like "decided autonomously"
    # or "resolved" for a task, treat as stale.
    STALE_PHRASES = [
        "awaiting your approval", "awaiting mike", "awaits your approval",
        "plans awaiting your approval", "roadmap q-hh", "phase d approval authority",
    ]

    for entry in cron[:3]:
        if not entry.get("blocker"):
            continue
        raw = entry["blocker"]
        raw_lower = raw.lower()
        # Filter: skip blockers that reference a now-resolved task
        # (e.g., "A10 POST-MERGE CANARY FAIL" is stale after A10 canary PASS disposition)
        referenced_tasks = set(re.findall(r"\b([AB]\d{1,2})\b", raw))
        if referenced_tasks and referenced_tasks.issubset(resolved_tasks):
            continue  # all referenced tasks are resolved → blocker is stale
        # Filter: skip blockers matching stale "awaiting Mike" phrases when Hermes has
        # delegated authority (per user mandate "full authority, push till done")
        if any(phrase in raw_lower for phrase in STALE_PHRASES):
            continue
        cleaned = re.sub(r"^\s*\d+\.\s*", "", raw).replace("**", "").replace("`", "")
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        summary = next((p for p in parts if len(p) >= 20), cleaned)
        if len(summary) > 180:
            summary = summary[:177] + "…"
        if not any(summary[:24] in o["label"] for o in out):
            out.append({
                "agent": "Hermes", "agent_emoji": "🪽",
                "raw": raw, "label": summary.strip(),
                "severity": "mike", "current_task": None, "current_phase": None,
            })
        break
    return out


def git_commit() -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except Exception:
        pass
    return None


# =========================================================================== #
# EVENT-STREAM REDUCER (primary data path — Mike spec)
# =========================================================================== #
# Reads events.jsonl, reduces events → (task_state_machine, agent_state,
# open_decisions, live-now buckets, lint gaps). The existing crawler stack
# above is retained as a fallback when the stream is empty/bootstrapping.
# =========================================================================== #

# Status state machine ordering — higher wins
STATUS_ORDER = {
    "NOT_STARTED": 0, "PLANNED": 1, "PROPOSAL": 2, "PROPOSAL_REVIEW": 3,
    "CODE": 4, "PR_REVIEW": 5, "MERGED": 6, "CANARY": 7, "DONE": 8,
    "BLOCKED": -1, "DEFERRED": -2,
}

EVENT_TYPE_SEVERITY = {
    "CANARY_FAIL": "critical", "PROPOSAL_REJECTED": "warn",
    "BLOCKED": "warn", "DECISION_NEEDED": "mike",
}

# STATUS → which event types implicitly transition a task there
EVENT_TO_STATUS = {
    "TASK_PLANNED": "PLANNED",
    "PROPOSAL_READY": "PROPOSAL_REVIEW",
    "PROPOSAL_APPROVED": "CODE",
    "PROPOSAL_REJECTED": "PROPOSAL",
    "CODE_STARTED": "CODE",
    "PR_OPENED": "PR_REVIEW",
    "REVIEW_POSTED": "PR_REVIEW",
    "MERGED": "MERGED",
    "CANARY_STARTED": "CANARY",
    "CANARY_PASS": "DONE",
    "CANARY_FAIL": "BLOCKED",
    "BLOCKED": "BLOCKED",
    "BLOCKER_RESOLVED": None,  # restore prior
}


def _parse_event_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _inline_read_events(path: Path = EVENTS_JSONL) -> list[dict[str, Any]]:
    """Fallback jsonl reader if lib/checkpoint_reporting is not importable."""
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except Exception as e:
                sys.stderr.write(f"WARN  events.jsonl line {i} skipped: {e}\n")
    except Exception as e:
        sys.stderr.write(f"WARN  reading {path}: {e}\n")
    return out


def read_events_safe() -> list[dict[str, Any]]:
    """Return all events, preferring the lib module when available."""
    if _HAS_LIB and _lib_read_events is not None:
        try:
            return list(_lib_read_events())
        except Exception as e:
            sys.stderr.write(f"WARN  lib read_events failed, falling back: {e}\n")
    return _inline_read_events()


# --- Inline lint (mirrors lib/checkpoint_reporting.lint_checkpoint) ---------

def _inline_lint(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """Detect gaps in the event stream. Matches schema §lint_checkpoint spec."""
    gaps: list[dict[str, Any]] = []
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_agent_heartbeat: dict[str, datetime] = {}
    open_blockers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    open_decisions: dict[str, dict[str, Any]] = {}

    for e in events:
        tid = e.get("task_id")
        if tid:
            by_task[tid].append(e)
        if e.get("event_type") == "AGENT_HEARTBEAT":
            ag = e.get("agent")
            ts = _parse_event_ts(e.get("ts", ""))
            if ag and ts and (ag not in by_agent_heartbeat or ts > by_agent_heartbeat[ag]):
                by_agent_heartbeat[ag] = ts
        if e.get("event_type") == "BLOCKED":
            open_blockers[tid or "_meta"].append(e)
        if e.get("event_type") == "BLOCKER_RESOLVED":
            if open_blockers.get(tid or "_meta"):
                open_blockers[tid or "_meta"].pop(0)
        if e.get("event_type") == "DECISION_NEEDED":
            qid = (e.get("extra") or {}).get("question_id") or e.get("event_id")
            open_decisions[qid] = e
        if e.get("event_type") == "DECISION_RESOLVED":
            qid = (e.get("extra") or {}).get("question_id")
            if qid and qid in open_decisions:
                open_decisions.pop(qid, None)

    def hours_since(ts: datetime) -> float:
        return (now - ts).total_seconds() / 3600.0

    # Per-task gap rules
    for tid, evs in by_task.items():
        types = [(e["event_type"], _parse_event_ts(e.get("ts", ""))) for e in evs]
        types = [(t, ts) for t, ts in types if ts]

        # MERGED → expect CANARY_STARTED within 2h
        merged = [ts for t, ts in types if t == "MERGED"]
        canary_started = [ts for t, ts in types if t == "CANARY_STARTED"]
        for mts in merged:
            follow = [c for c in canary_started if c >= mts]
            if not follow and hours_since(mts) > 2:
                gaps.append({
                    "task_id": tid, "severity": "warn",
                    "issue": f"MERGED {hours_since(mts):.1f}h ago with no CANARY_STARTED",
                })

        # CANARY_STARTED → CANARY_PASS/FAIL within 48h
        for cts in canary_started:
            verdict = [ts for t, ts in types if t in ("CANARY_PASS", "CANARY_FAIL") and ts >= cts]
            if not verdict and hours_since(cts) > 48:
                gaps.append({
                    "task_id": tid, "severity": "warn",
                    "issue": f"CANARY_STARTED {hours_since(cts):.1f}h ago, no verdict",
                })

        # PR_OPENED → REVIEW_POSTED within 24h
        prs = [ts for t, ts in types if t == "PR_OPENED"]
        for pts in prs:
            revs = [ts for t, ts in types if t == "REVIEW_POSTED" and ts >= pts]
            if not revs and hours_since(pts) > 24:
                gaps.append({
                    "task_id": tid, "severity": "warn",
                    "issue": f"PR_OPENED {hours_since(pts):.1f}h ago with no REVIEW_POSTED",
                })

        # Task with any event but none in last 72h (stale)
        last_ts = max((ts for _, ts in types), default=None)
        if last_ts and hours_since(last_ts) > 72:
            # only surface if task isn't done
            final_status = _reduce_task_status([e for e in evs])
            if final_status not in ("DONE", "DEFERRED"):
                gaps.append({
                    "task_id": tid, "severity": "info",
                    "issue": f"no event for {hours_since(last_ts):.0f}h (status={final_status})",
                })

    # Unresolved BLOCKED >4h
    for tid, blocks in open_blockers.items():
        for b in blocks:
            bts = _parse_event_ts(b.get("ts", ""))
            if bts and hours_since(bts) > 4:
                gaps.append({
                    "task_id": tid if tid != "_meta" else None,
                    "severity": "critical",
                    "issue": (f"BLOCKED {hours_since(bts):.1f}h, reason="
                              f"{b.get('blocker') or (b.get('extra') or {}).get('reason') or '?'}"),
                })

    # DECISION_NEEDED >24h
    for qid, d in open_decisions.items():
        dts = _parse_event_ts(d.get("ts", ""))
        if dts and hours_since(dts) > 24:
            gaps.append({
                "task_id": d.get("task_id"), "severity": "mike",
                "issue": (f"DECISION_NEEDED {hours_since(dts):.0f}h unresolved: "
                          f"{(d.get('extra') or {}).get('question', qid)[:100]}"),
            })

    # AGENT_HEARTBEAT stale >3h (for agents we've ever heard from)
    for ag, ts in by_agent_heartbeat.items():
        if hours_since(ts) > 3:
            gaps.append({
                "task_id": None, "severity": "info",
                "issue": f"agent {ag} heartbeat stale ({hours_since(ts):.1f}h)",
            })

    return gaps


def lint_events_safe(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    if _HAS_LIB and _lib_lint_checkpoint is not None:
        try:
            return list(_lib_lint_checkpoint())
        except Exception as e:
            sys.stderr.write(f"WARN  lib lint_checkpoint failed, inline fallback: {e}\n")
    return _inline_lint(events, now)


# --- Reducers ---------------------------------------------------------------

def _reduce_task_status(task_events: list[dict[str, Any]]) -> str:
    """Replay events chronologically → final STATUS (highest-order transition)."""
    evs = sorted(task_events, key=lambda e: e.get("ts", ""))
    current = "NOT_STARTED"
    prior_before_block = current
    for e in evs:
        et = e.get("event_type")
        # Explicit status carry
        if e.get("status") and e["status"] in STATUS_ORDER:
            # Don't downgrade from DONE unless the event is a CANARY_FAIL or BLOCKED
            if STATUS_ORDER.get(e["status"], 0) >= STATUS_ORDER.get(current, 0) or et in (
                "CANARY_FAIL", "BLOCKED", "PROPOSAL_REJECTED"
            ):
                if current != "BLOCKED":
                    prior_before_block = current
                current = e["status"]
                continue
        if et == "STATUS_CHANGED":
            ns = (e.get("extra") or {}).get("to_status")
            if ns in STATUS_ORDER:
                if current != "BLOCKED":
                    prior_before_block = current
                current = ns
                continue
        if et == "BLOCKER_RESOLVED" and current == "BLOCKED":
            current = prior_before_block
            continue
        mapped = EVENT_TO_STATUS.get(et)
        if mapped:
            if current != "BLOCKED":
                prior_before_block = current
            # Never downgrade unless explicit BLOCKED/CANARY_FAIL
            if STATUS_ORDER.get(mapped, 0) >= STATUS_ORDER.get(current, 0) or et in (
                "CANARY_FAIL", "BLOCKED", "PROPOSAL_REJECTED"
            ):
                current = mapped
    return current


def _infer_tier(task_events: list[dict[str, Any]], task_id: str) -> str:
    """Tier from event 'extra.tier' or fall back to hardcoded map or STANDARD."""
    for e in reversed(sorted(task_events, key=lambda x: x.get("ts", ""))):
        tier = (e.get("extra") or {}).get("tier")
        if tier in ("CRITICAL", "STANDARD", "LIGHTWEIGHT"):
            return tier
    return TIERS.get(task_id, "STANDARD")


def _infer_phase(task_id: str | None) -> str | None:
    if not task_id:
        return None
    m = re.match(r"^([A-Z])\d", task_id)
    return m.group(1) if m else None


def reduce_tasks(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """task_id → {status, tier, last_event_ts, last_event_type, phase,
                  pr_numbers, prs, canary_verdict, events (all), blocker,
                  agents_touched}."""
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        tid = e.get("task_id")
        if tid:
            by_task[tid].append(e)

    out: dict[str, dict[str, Any]] = {}
    for tid, evs in by_task.items():
        evs_sorted = sorted(evs, key=lambda x: x.get("ts", ""))
        status = _reduce_task_status(evs_sorted)
        tier = _infer_tier(evs_sorted, tid)
        last = evs_sorted[-1] if evs_sorted else {}

        # PR tracking
        prs: list[dict[str, Any]] = []
        seen_prs: set[tuple[str, int]] = set()
        for e in evs_sorted:
            pr_num = e.get("pr")
            repo = e.get("repo")
            if pr_num and repo and (repo, pr_num) not in seen_prs:
                seen_prs.add((repo, pr_num))
                merge_sha = (e.get("extra") or {}).get("commit_sha")
                prs.append({
                    "repo": repo, "number": pr_num,
                    "pr_url": f"https://github.com/QuantisDevelopment/{repo}/pull/{pr_num}",
                    "merge_commit": merge_sha,
                    "commit_url": (
                        f"https://github.com/QuantisDevelopment/{repo}/commit/{merge_sha}"
                        if merge_sha else None
                    ),
                })

        # Canary verdict
        canary_verdict = None
        for e in evs_sorted:
            if e.get("event_type") == "CANARY_PASS":
                canary_verdict = "PASS"
            elif e.get("event_type") == "CANARY_FAIL":
                canary_verdict = "FAIL"
            elif e.get("event_type") == "CANARY_STARTED" and canary_verdict is None:
                canary_verdict = "PENDING"

        # Open blocker
        blocker = None
        for e in evs_sorted:
            if e.get("event_type") == "BLOCKED":
                blocker = e.get("blocker") or (e.get("extra") or {}).get("reason")
            elif e.get("event_type") == "BLOCKER_RESOLVED":
                blocker = None

        agents_touched = sorted({e.get("agent") for e in evs_sorted if e.get("agent")})

        out[tid] = {
            "id": tid, "status": status, "tier": tier,
            "tier_emoji": TIER_EMOJI.get(tier, "•"),
            "phase": _infer_phase(tid),
            "last_event_ts": last.get("ts"),
            "last_event_type": last.get("event_type"),
            "last_agent": last.get("agent"),
            "event_count": len(evs_sorted),
            "prs": prs,
            "canary_verdict": canary_verdict,
            "blocker": blocker,
            "agents_touched": agents_touched,
            "events": evs_sorted,
        }
    return out


def reduce_agents(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """agent → last event ts/type + current_task + staleness."""
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        ag = e.get("agent")
        if ag:
            by_agent[ag].append(e)
    out: list[dict[str, Any]] = []
    for ag, evs in by_agent.items():
        evs_sorted = sorted(evs, key=lambda x: x.get("ts", ""))
        last = evs_sorted[-1]
        last_dt = _parse_event_ts(last.get("ts", ""))
        age_hours = ((now - last_dt).total_seconds() / 3600.0) if last_dt else None
        if age_hours is None:
            light = "red"
        elif age_hours < 1:
            light = "green"
        elif age_hours < 3:
            light = "yellow"
        else:
            light = "red"
        # Find last heartbeat for current task
        last_hb = next(
            (e for e in reversed(evs_sorted) if e.get("event_type") == "AGENT_HEARTBEAT"),
            None,
        )
        current_task = (
            (last_hb.get("extra") or {}).get("current_task") if last_hb else last.get("task_id")
        )
        out.append({
            "id": ag, "name": ag.upper() if ag not in ("mike", "oinkv") else ag,
            "last_event_ts": last.get("ts"),
            "last_event_type": last.get("event_type"),
            "last_task_id": last.get("task_id"),
            "current_task": current_task,
            "age_hours": age_hours,
            "staleness_label": (
                "green" if light == "green" else "yellow" if light == "yellow" else "red"
            ),
            "light": light,
            "event_count": len(evs_sorted),
        })
    out.sort(key=lambda a: a.get("last_event_ts") or "", reverse=True)
    return out


# --- Live-now time buckets --------------------------------------------------

def bucket_events(events: list[dict[str, Any]], now: datetime) -> dict[str, list[dict[str, Any]]]:
    """Return {'1h': [...], '4h': [...], '24h': [...]} — oldest bucket includes newer."""
    buckets: dict[str, list[dict[str, Any]]] = {"1h": [], "4h": [], "24h": []}
    for e in events:
        ts = _parse_event_ts(e.get("ts", ""))
        if not ts:
            continue
        age_h = (now - ts).total_seconds() / 3600.0
        summary = _one_line_summary(e)
        row = {
            "ts": e.get("ts"), "event_type": e.get("event_type"),
            "task_id": e.get("task_id"), "agent": e.get("agent"),
            "summary": summary, "phase": e.get("phase") or _infer_phase(e.get("task_id")),
            "pr": e.get("pr"), "repo": e.get("repo"),
            "age_hours": age_h,
        }
        if age_h <= 1:
            buckets["1h"].append(row)
        if age_h <= 4:
            buckets["4h"].append(row)
        if age_h <= 24:
            buckets["24h"].append(row)
    for k in buckets:
        buckets[k].sort(key=lambda r: r.get("ts") or "", reverse=True)
    return buckets


def _one_line_summary(e: dict[str, Any]) -> str:
    et = e.get("event_type") or ""
    ex = e.get("extra") or {}
    tid = e.get("task_id") or "—"
    if et == "MERGED":
        sha = (ex.get("commit_sha") or "")[:7]
        return f"{tid} merged via PR #{e.get('pr')}" + (f" @{sha}" if sha else "")
    if et == "CANARY_PASS":
        return f"{tid} canary PASS"
    if et == "CANARY_FAIL":
        return f"{tid} canary FAIL — {ex.get('issues', '')}"[:140]
    if et == "CANARY_STARTED":
        return f"{tid} canary started"
    if et == "PR_OPENED":
        return f"{tid} PR #{e.get('pr')} opened — {ex.get('title', '')}"[:140]
    if et == "REVIEW_POSTED":
        return (f"{tid} review by {ex.get('reviewer', e.get('agent'))} — "
                f"{ex.get('verdict', '')} ({ex.get('score', '')})")[:140]
    if et == "PROPOSAL_READY":
        return f"{tid} proposal ready"
    if et == "PROPOSAL_APPROVED":
        return f"{tid} proposal approved by {ex.get('approver', '?')}"
    if et == "PROPOSAL_REJECTED":
        return f"{tid} proposal rejected — {ex.get('reason', '')}"[:140]
    if et == "CODE_STARTED":
        return f"{tid} code started on {e.get('branch', '?')}"
    if et == "BLOCKED":
        return f"{tid} BLOCKED — {e.get('blocker') or ex.get('reason', '')}"[:140]
    if et == "BLOCKER_RESOLVED":
        return f"{tid} blocker cleared"
    if et == "DECISION_NEEDED":
        return f"{tid} Mike gate: {ex.get('question', ex.get('question_id', ''))}"[:140]
    if et == "DECISION_RESOLVED":
        return f"{tid} decision: {ex.get('answer', '?')}"[:140]
    if et == "STATUS_CHANGED":
        return f"{tid} {ex.get('from_status', '?')} → {ex.get('to_status', '?')}"
    if et == "ARTIFACT_PUBLISHED":
        return f"{tid} published {ex.get('category', '')}: {Path(e.get('artifact_path') or '').name}"
    if et == "AGENT_HEARTBEAT":
        return f"{e.get('agent')} heartbeat — {ex.get('current_task', '?')}"
    if et == "TASK_PLANNED":
        return f"{tid} plan published"
    if et == "SPRINT_NOTE":
        return (ex.get("text") or "")[:140]
    return f"{et} {tid}"


# --- Open decisions (Needs Mike) -------------------------------------------

def open_decisions(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    open_: dict[str, dict[str, Any]] = {}
    for e in sorted(events, key=lambda x: x.get("ts", "")):
        et = e.get("event_type")
        ex = e.get("extra") or {}
        if et == "DECISION_NEEDED":
            qid = ex.get("question_id") or e.get("event_id")
            open_[qid] = e
        elif et == "DECISION_RESOLVED":
            qid = ex.get("question_id")
            if qid:
                open_.pop(qid, None)

    out: list[dict[str, Any]] = []
    for qid, e in open_.items():
        ts = _parse_event_ts(e.get("ts", ""))
        age_h = ((now - ts).total_seconds() / 3600.0) if ts else None
        ex = e.get("extra") or {}
        # Detect Q-B1-*, Q-B2-*, Q-HH-* style gates
        gate_type = "generic"
        if isinstance(qid, str):
            if qid.startswith("Q-HH"):
                gate_type = "heavy-hybrid"
            elif re.match(r"^Q-B\d", qid):
                gate_type = f"phase-{qid.split('-')[1][0].lower()}"
            elif re.match(r"^Q-A\d", qid):
                gate_type = "phase-a"
        out.append({
            "question_id": qid,
            "question": ex.get("question", "(no question text)"),
            "options": ex.get("options", []),
            "task_id": e.get("task_id"),
            "phase": e.get("phase") or _infer_phase(e.get("task_id")),
            "ts": e.get("ts"), "age_hours": age_h,
            "age_human": _age_human(age_h),
            "agent": e.get("agent"),
            "gate_type": gate_type,
        })
    out.sort(key=lambda x: x.get("age_hours") or 0, reverse=True)
    return out


def _age_human(h: float | None) -> str:
    if h is None:
        return "—"
    if h < 0:
        return "just now"
    if h < 1:
        return f"{int(h*60)}m"
    if h < 48:
        return f"{h:.1f}h"
    return f"{h/24:.1f}d"


# --- Events integrity -------------------------------------------------------

def events_integrity(events: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    total = len(events)
    last_24h = 0
    gaps_monotonic: list[str] = []
    last_id = None
    for e in events:
        ts = _parse_event_ts(e.get("ts", ""))
        if ts and (now - ts).total_seconds() / 3600.0 <= 24:
            last_24h += 1
        eid = e.get("event_id") or ""
        if last_id and eid and eid < last_id:
            gaps_monotonic.append(f"{eid} came after {last_id}")
        if eid:
            last_id = eid
    rate = last_24h / 24.0 if last_24h else 0.0
    return {
        "total": total, "last_24h": last_24h, "rate_per_hour": round(rate, 2),
        "schema_version": EVENT_SCHEMA_VERSION,
        "monotonic_gaps": gaps_monotonic[:5],
        "monotonic_ok": not gaps_monotonic,
        "source": "lib" if _HAS_LIB else "inline",
        "events_file": str(EVENTS_JSONL),
    }


# --- GH PR live state enrichment -------------------------------------------

def enrich_merged_prs_via_gh(tasks_map: dict[str, dict[str, Any]]) -> None:
    """Best-effort: for each MERGED PR, ask `gh` for current state. Skip on failure."""
    # Quick gh availability check
    try:
        subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, timeout=3, check=True
        )
    except Exception:
        return
    for tid, t in tasks_map.items():
        for pr in t.get("prs", []):
            repo = pr.get("repo")
            num = pr.get("number")
            if not repo or not num:
                continue
            try:
                r = subprocess.run(
                    ["gh", "pr", "view", str(num),
                     "-R", f"QuantisDevelopment/{repo}",
                     "--json", "state,mergedAt,mergeCommit"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode != 0:
                    continue
                info = json.loads(r.stdout)
                pr["live_state"] = info.get("state")
                pr["live_merged_at"] = info.get("mergedAt")
                mc = info.get("mergeCommit") or {}
                oid = mc.get("oid") if isinstance(mc, dict) else None
                if oid and not pr.get("merge_commit"):
                    pr["merge_commit"] = oid[:12]
                    pr["commit_url"] = f"https://github.com/QuantisDevelopment/{repo}/commit/{oid}"
            except Exception:
                continue


# --- Event-derived "task" dicts (shape-compatible with crawler tasks) -------

def task_from_stream(tid: str, task_state: dict[str, Any]) -> dict[str, Any]:
    """Produce a crawler-compatible task dict from the reduced state."""
    status = task_state["status"]
    tier = task_state["tier"]
    canary_verdict = task_state.get("canary_verdict")
    prs = task_state.get("prs") or []
    evs = task_state.get("events") or []

    # Timeline = chronological event rows rendered for dashboard
    timeline = []
    for e in evs:
        meta = EVENT_META.get(e.get("event_type", ""), {"emoji": "•", "actor": "—"})
        timeline.append({
            "label": _one_line_summary(e),
            "actor": e.get("agent") or meta.get("actor", "—"),
            "path": e.get("artifact_path"),
            "mtime": e.get("ts"),
            "verdict": (e.get("extra") or {}).get("verdict"),
            "score": (e.get("extra") or {}).get("score"),
            "event_type": e.get("event_type"),
        })

    # Scores — last REVIEW_POSTED per reviewer
    scores = {"vigil": None, "guardian": None, "hermes": None}
    verdicts = {"vigil": None, "guardian": None, "hermes": None}
    for e in evs:
        if e.get("event_type") == "REVIEW_POSTED":
            ex = e.get("extra") or {}
            rv = (ex.get("reviewer") or e.get("agent") or "").lower()
            if rv in scores:
                sc = ex.get("score")
                if isinstance(sc, (int, float)):
                    scores[rv] = float(sc)
                v = ex.get("verdict")
                if v:
                    verdicts[rv] = v

    merged_at = next(
        (e.get("ts") for e in evs if e.get("event_type") == "MERGED"), None
    )
    last_activity = task_state.get("last_event_ts")

    return {
        "id": tid, "tier": tier,
        "tier_emoji": TIER_EMOJI.get(tier, "•"),
        "repo_hint": TASK_REPO_HINT.get(tid),
        "status": status,
        "status_label": STATUS_LABEL.get(status, status),
        "prs": prs, "scores": scores, "verdicts": verdicts,
        "canary": {
            "verdict": canary_verdict, "path": None,
            "mtime": next((e.get("ts") for e in reversed(evs)
                           if e.get("event_type", "").startswith("CANARY_")), None),
        },
        "merged_at": merged_at,
        "last_activity": last_activity,
        "timeline": timeline,
        "artifacts": {
            # Map event artifact_paths by event type (best effort)
            e["event_type"].lower(): e["artifact_path"]
            for e in evs if e.get("artifact_path")
        },
        # Event-stream-specific
        "_from_stream": True,
        "event_count": task_state.get("event_count", len(evs)),
        "blocker": task_state.get("blocker"),
        "phase": task_state.get("phase"),
        "agents_touched": task_state.get("agents_touched", []),
        "last_event_type": task_state.get("last_event_type"),
    }


def build_from_events(events: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    """Produce a 'data' dict shaped compatibly with the crawler's build()."""
    tasks_map = reduce_tasks(events)
    # Enrich MERGED PRs via gh (best effort, silently skipped)
    try:
        enrich_merged_prs_via_gh(tasks_map)
    except Exception:
        pass

    # Ensure all SEED_TASKS are at least present as NOT_STARTED
    for tid in SEED_TASKS:
        if tid not in tasks_map:
            tasks_map[tid] = {
                "id": tid, "status": "NOT_STARTED",
                "tier": TIERS.get(tid, "STANDARD"),
                "tier_emoji": TIER_EMOJI.get(TIERS.get(tid, "STANDARD"), "•"),
                "phase": _infer_phase(tid),
                "last_event_ts": None, "last_event_type": None,
                "last_agent": None, "event_count": 0, "prs": [],
                "canary_verdict": None, "blocker": None,
                "agents_touched": [], "events": [],
            }

    tasks = [task_from_stream(tid, ts) for tid, ts in tasks_map.items()]
    tasks.sort(key=lambda t: t.get("last_activity") or "", reverse=True)

    agents = reduce_agents(events, now)
    if not agents:
        # No agents seen yet — provide stub so UI doesn't crash
        agents = [
            {"id": a["id"], "name": a["name"], "emoji": a.get("emoji", "•"),
             "role": a.get("role", ""), "last_event_ts": None, "last_event_type": None,
             "current_task": None, "age_hours": None,
             "staleness_label": "red", "light": "red",
             "event_count": 0, "last_task_id": None}
            for a in AGENTS
        ]
    else:
        # Enrich with role/emoji from static AGENTS
        ag_meta = {a["id"]: a for a in AGENTS}
        for a in agents:
            m = ag_meta.get(a["id"], {})
            a["emoji"] = m.get("emoji", "•")
            a["role"] = m.get("role", "")
            a["name"] = m.get("name", a["name"])
            # Legacy key the template reads
            a["last_active"] = a["last_event_ts"]
            a["last_active_human"] = humanize(
                _parse_event_ts(a["last_event_ts"] or ""), now
            )
            a["heartbeat"] = {
                "current_task": a.get("current_task"),
                "current_phase": None,
                "blockers": [],
                "branch": None,
            }

    # Waves — dynamic, only for tasks we've seen
    wave_progress = []
    for w in WAVES:
        w_tasks = [t for t in tasks if t["id"] in w["tasks"]]
        done = sum(1 for t in w_tasks if t["status"] == "DONE")
        total = len(w["tasks"])
        wave_progress.append({
            "name": w["name"], "tasks": w_tasks, "task_ids": w["tasks"],
            "done": done, "total": total,
            "percent": int((done / total) * 100) if total else 0,
            "future": w.get("future", False),
        })

    return {
        "generated_at_utc": iso(now),
        "generated_at_cest": now.astimezone(CEST).isoformat(timespec="seconds"),
        "sprint_title": "OinkFarm Implementation Foresight Sprint",
        "sprint_subtitle": "Event-stream dashboard · Wave 1 shipped · Wave 2 in-flight",
        "waves": wave_progress, "tasks": tasks, "agents": agents,
        "cron": [], "plans": [], "audits": [],
        "blockers": [],  # will be derived below from open_decisions + stream
        "last_cron": None,
        "commit": git_commit(),
        "_from_stream": True,
        "_tasks_map": tasks_map,
        "_events_all_stream": events,
    }


# --------------------------------------------------------------------------- #
# Main build + render
# --------------------------------------------------------------------------- #

def build(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)

    # ----- PRIMARY: event-stream reducer -----
    events = read_events_safe()
    integrity = events_integrity(events, now)
    bootstrap = len(events) < MIN_EVENTS_FOR_PRIMARY

    if not bootstrap:
        # Event-stream is the primary source
        data = build_from_events(events, now)
        # Dynamic TASKS discovery — every task_id we've seen in events
        global TASKS
        discovered = sorted(
            {t["id"] for t in data["tasks"]},
            key=lambda t: (t[0], int(re.search(r"\d+", t).group()) if re.search(r"\d+", t) else 0),
        )
        if discovered:
            TASKS = discovered
        # Derive open_decisions + buckets + lint gaps
        data["open_decisions"] = open_decisions(events, now)
        data["live_buckets"] = bucket_events(events, now)
        data["lint_gaps"] = lint_events_safe(events, now)
        data["events_integrity"] = integrity
        data["bootstrap"] = False
        # Build "freshness by agent" table — uses reduced agents directly
        data["freshness_by_agent"] = data["agents"]
        # Cron narrative still useful; derive from SPRINT_NOTEs
        data["cron"] = _cron_from_events(events)
        data["last_cron"] = data["cron"][0] if data["cron"] else None
        data["plans"] = []
        data["audits"] = []
        # Blockers — union of open_decisions + currently BLOCKED tasks
        data["blockers"] = _blockers_from_stream(data["tasks"], data["open_decisions"])
        # ---- HUMAN NARRATIVE block — top-of-dashboard plain-English layer ----
        tasks_by_id = {t["id"]: t for t in data["tasks"]}
        data["narrative"] = {
            "mission":        _render_mission(),
            "today":          _render_today_paragraph(events, now, tasks_by_id),
            "week":           _render_week_prose(events, now, tasks_by_id),
            "whats_next":     _render_whats_next_prose(data),
            "sos_exists":     STATE_OF_SPRINT.exists(),
            "sos_link":       "sprint-log/STATE-OF-SPRINT.md",
            "glossary_link":  "sprint-log/STATE-OF-SPRINT.md#glossary",
        }
        data["events_integrity"]["human_line"] = _integrity_human_line(integrity)
        return data

    # ----- FALLBACK: crawler (bootstrap mode) -----
    sys.stderr.write(
        f"INFO  events.jsonl has {len(events)} events (<{MIN_EVENTS_FOR_PRIMARY}), "
        f"bootstrapping from crawler\n"
    )
    tasks = [crawl_task(t, now) for t in TASKS]
    tasks.sort(key=lambda t: t["last_activity"] or "", reverse=True)
    agents = [crawl_agent(a, now) for a in AGENTS]
    cron = crawl_cron()
    plans = crawl_plans()
    blockers = derive_blockers(agents, cron, tasks)

    wave_progress = []
    for w in WAVES:
        w_tasks = [t for t in tasks if t["id"] in w["tasks"]]
        done = sum(1 for t in w_tasks if t["status"] == "DONE")
        total = len(w["tasks"])
        wave_progress.append({
            "name": w["name"], "tasks": w_tasks, "task_ids": w["tasks"],
            "done": done, "total": total,
            "percent": int((done / total) * 100) if total else 0,
            "future": w.get("future", False),
        })

    return {
        "generated_at_utc": iso(now),
        "generated_at_cest": now.astimezone(CEST).isoformat(timespec="seconds"),
        "sprint_title": "OinkFarm Implementation Foresight Sprint",
        "sprint_subtitle": "Wave 1 shipped · Wave 2 in-flight",
        "waves": wave_progress, "tasks": tasks, "agents": agents,
        "cron": cron, "plans": plans["plans"], "audits": plans["audits"],
        "blockers": blockers, "last_cron": cron[0] if cron else None,
        "commit": git_commit(),
        "bootstrap": True,
        "events_integrity": {**integrity,
                             "human_line": _integrity_human_line(integrity)},
        "open_decisions": [],
        "live_buckets": {"1h": [], "4h": [], "24h": []},
        "lint_gaps": [],
        "narrative": {
            "mission":       _render_mission(),
            "today":         _render_today_paragraph(events, now, {}),
            "week":          _render_week_prose(events, now, {}),
            "whats_next":    _render_whats_next_prose(None),
            "sos_exists":    STATE_OF_SPRINT.exists(),
            "sos_link":      "sprint-log/STATE-OF-SPRINT.md",
            "glossary_link": "sprint-log/STATE-OF-SPRINT.md#glossary",
        },
        "freshness_by_agent": [
            {
                "id": a["id"], "name": a["name"], "emoji": a["emoji"],
                "role": a["role"],
                "last_event_ts": a["last_active"],
                "last_event_type": "(crawler mtime)",
                "last_task_id": a.get("heartbeat", {}).get("current_task"),
                "current_task": a.get("heartbeat", {}).get("current_task"),
                "light": a["light"],
                "staleness_label": a["light"],
                "age_hours": None,
                "event_count": 0,
            }
            for a in agents
        ],
    }


def _cron_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert SPRINT_NOTE events into a cron-like feed for the narrative tab."""
    out: list[dict[str, Any]] = []
    for e in reversed(sorted(events, key=lambda x: x.get("ts", ""))):
        if e.get("event_type") != "SPRINT_NOTE":
            continue
        ex = e.get("extra") or {}
        text = ex.get("text") or ""
        ts = _parse_event_ts(e.get("ts", ""))
        out.append({
            "time_utc": e.get("ts"),
            "time_local": (
                ts.astimezone(CEST).isoformat(timespec="minutes") if ts else None
            ),
            "header": None,
            "actions": [text] if text else [],
            "next": None, "blocker": None,
            "path": e.get("event_id"),
        })
        if len(out) >= 40:
            break
    return out


def _blockers_from_stream(tasks: list[dict[str, Any]],
                          open_decs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # Open DECISION_NEEDED → Mike blocker
    for d in open_decs:
        out.append({
            "agent": "Mike", "agent_emoji": "🧭",
            "raw": d.get("question", ""),
            "label": (
                f"{d.get('question_id', '?')}: {d.get('question', '')[:120]}"
            ),
            "severity": "mike",
            "current_task": d.get("task_id"),
            "current_phase": d.get("phase"),
        })
    # BLOCKED tasks
    for t in tasks:
        if t.get("status") == "BLOCKED" and t.get("blocker"):
            out.append({
                "agent": "—", "agent_emoji": "🛑",
                "raw": t["blocker"],
                "label": f"{t['id']} blocked: {t['blocker']}",
                "severity": "auto",
                "current_task": t["id"],
                "current_phase": t.get("phase"),
            })
    return out


# --------------------------------------------------------------------------- #
# HUMAN NARRATIVE rendering — plain-English prose for the dashboard top block.
#
# These helpers lead the dashboard with a narrative layer that Mike/Dominik can
# read without prior engineering context. They fall back gracefully if the
# STATE-OF-SPRINT.md companion doc (produced by the Scribe subagent) is absent.
# --------------------------------------------------------------------------- #

STATE_OF_SPRINT = ROOT / "sprint-log" / "STATE-OF-SPRINT.md"

# Known task short-names used to make the prose concrete.
_TASK_SHORTNAMES = {
    "A1":  "signal_events schema",
    "A2":  "remaining_pct model",
    "A3":  "auto filled_at",
    "A4":  "PARTIALLY_CLOSED lifecycle",
    "A5":  "parser confidence scoring",
    "A6":  "ghost-closure flag",
    "A7":  "UPDATE→NEW dedup",
    "A8":  "conditional SL type",
    "A9":  "1000x denomination multiplier",
    "A10": "test→prod database merge",
    "A11": "leverage-source tracking",
    "B1":  "db abstraction layer",
    "B2":  "PostgreSQL schema migration",
    "B3":  "parallel-write verification",
    "B4":  "PostgreSQL cutover",
    "B5":  "Redis co-host bring-up",
    "B6":  "Cornix/Chroma parser extraction",
    "B7":  "config unification",
    "B8":  "dedup consolidation",
    "B9":  "W1 DB-level enforcement",
    "C1":  "observability scaffolding",
    "C2":  "confidence routing",
}

def _read_sos_section(section: str) -> str | None:
    """Read a '## <section>' block from STATE-OF-SPRINT.md. Returns None if
    the file is missing or the section cannot be located. Matches either an
    exact heading or a heading where `section` is the prefix (so 'The Mission'
    matches '## The Mission (one paragraph)')."""
    if not STATE_OF_SPRINT.exists():
        return None
    try:
        text = STATE_OF_SPRINT.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    # Match '## <section>[ trailing words ...]' and capture everything up to
    # the next '## ' heading or EOF.
    pattern = re.compile(
        r"(?ms)^##[ \t]+" + re.escape(section)
        + r"(?:[ \t][^\n]*)?\n(.*?)(?=^##[ \t]|\Z)"
    )
    m = pattern.search(text)
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


def _render_mission() -> str:
    """Return the Mission paragraph from STATE-OF-SPRINT.md, or a graceful
    placeholder if the Scribe has not produced it yet."""
    body = _read_sos_section("The Mission") or _read_sos_section("Mission")
    if not body:
        return (
            "Mission statement pending — first Scribe run populates this. "
            "State of Sprint doc being built by Scribe."
        )
    # Use the first non-empty paragraph only for the dashboard inline block.
    for para in body.split("\n\n"):
        p = para.strip()
        if p and not p.startswith("#"):
            return p
    return body


def _short_task(tid: str, tasks_by_id: dict[str, dict[str, Any]]) -> str:
    """Render a task reference as '<tid> <tier_emoji> <short-name>'."""
    t = tasks_by_id.get(tid) or {}
    emoji = t.get("tier_emoji") or TIER_EMOJI.get(TIERS.get(tid, "STANDARD"), "•")
    name = _TASK_SHORTNAMES.get(tid, "")
    return f"{tid} {emoji}{(' ' + name) if name else ''}".strip()


def _n_as_word(n: int) -> str:
    """Render small counts as English words ('three merges')."""
    words = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
             5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
             10: "ten", 11: "eleven", 12: "twelve"}
    return words.get(n, str(n))


def _events_between(events: list[dict[str, Any]],
                    start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Return events with ts in [start, end]. Uses UTC-aware comparison."""
    out = []
    for e in events:
        ts = _parse_event_ts(e.get("ts", ""))
        if ts and start <= ts <= end:
            out.append(e)
    return out


def _render_today_paragraph(events: list[dict[str, Any]],
                            now: datetime | None = None,
                            tasks_by_id: dict[str, dict[str, Any]] | None = None
                            ) -> str:
    """Construct a plain-English paragraph from today's (UTC day) events.

    Rules: mention concrete tasks by short-name + tier emoji; mention counts;
    mention Mike interactions if any; mention new decisions. Max ~120 words,
    no bullets. If zero events today, emits a 'quiet' line.
    """
    now = now or datetime.now(timezone.utc)
    tasks_by_id = tasks_by_id or {}
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = _events_between(events, day_start, now)
    if not today:
        return ("Quiet so far today — no merges, reviews, or canaries since "
                "midnight UTC.")

    # Tally event types
    merged = [e for e in today if e.get("event_type") == "MERGED"]
    canary_start = [e for e in today if e.get("event_type") == "CANARY_STARTED"]
    canary_pass = [e for e in today if e.get("event_type") == "CANARY_PASS"]
    canary_fail = [e for e in today if e.get("event_type") == "CANARY_FAIL"]
    reviews = [e for e in today if e.get("event_type") == "REVIEW_POSTED"]
    prs_opened = [e for e in today if e.get("event_type") == "PR_OPENED"]
    decisions_opened = [e for e in today
                        if e.get("event_type") == "DECISION_NEEDED"]
    decisions_resolved = [e for e in today
                          if e.get("event_type") == "DECISION_RESOLVED"]
    authority = [e for e in today
                 if e.get("event_type") == "AUTHORITY"
                 or (e.get("agent") or "").lower() == "mike"]

    # First sentence — counts summary
    bits = []
    if merged:
        bits.append(f"{_n_as_word(len(merged))} merge{'s' if len(merged) != 1 else ''}")
    if canary_start:
        bits.append(
            f"{_n_as_word(len(canary_start))} canary kicked off"
            if len(canary_start) == 1
            else f"{_n_as_word(len(canary_start))} canaries kicked off"
        )
    if canary_pass:
        bits.append(
            f"{_n_as_word(len(canary_pass))} canary PASS"
            if len(canary_pass) == 1
            else f"{_n_as_word(len(canary_pass))} canary PASSes"
        )
    if canary_fail:
        bits.append(f"{_n_as_word(len(canary_fail))} canary FAIL"
                    + ("s" if len(canary_fail) != 1 else ""))
    if reviews:
        bits.append(f"{_n_as_word(len(reviews))} review"
                    + ("s posted" if len(reviews) != 1 else " posted"))
    if prs_opened and not merged:
        bits.append(f"{_n_as_word(len(prs_opened))} PR"
                    + ("s opened" if len(prs_opened) != 1 else " opened"))

    parts: list[str] = []
    if bits:
        # Nice English joining
        if len(bits) == 1:
            parts.append(f"Today: {bits[0]}.")
        elif len(bits) == 2:
            parts.append(f"Today: {bits[0]} and {bits[1]}.")
        else:
            parts.append(f"Today: {', '.join(bits[:-1])}, and {bits[-1]}.")

    # Second sentence — specific shipped tasks (up to 3 concrete examples)
    shipped_ids = []
    seen = set()
    for e in merged + canary_pass:
        tid = e.get("task_id")
        if tid and tid not in seen:
            seen.add(tid)
            shipped_ids.append(tid)
    if shipped_ids:
        refs = [_short_task(t, tasks_by_id) for t in shipped_ids[:3]]
        verb = "shipped" if merged else "cleared canary"
        if len(refs) == 1:
            parts.append(f"{refs[0]} {verb}.")
        else:
            parts.append(
                f"Tasks on the board: {', '.join(refs[:-1])}, and {refs[-1]} "
                f"all moved forward."
            )

    # Mike interactions
    if authority or decisions_resolved:
        mike_bits = []
        # Find Mike-resolved decisions
        for e in decisions_resolved:
            ex = e.get("extra") or {}
            qid = ex.get("question_id") or ""
            ans = (ex.get("answer") or "").strip()
            if qid:
                mike_bits.append(f"{qid} resolved" + (f" ({ans[:60]})" if ans else ""))
        for e in authority:
            ex = e.get("extra") or {}
            text = ex.get("text") or ex.get("summary") or ""
            if text:
                mike_bits.append(text.strip()[:80])
        mike_bits = mike_bits[:3]
        if mike_bits:
            parts.append("Mike weighed in: " + "; ".join(mike_bits) + ".")

    # New decisions opened
    if decisions_opened:
        qids = []
        for e in decisions_opened:
            ex = e.get("extra") or {}
            qid = ex.get("question_id")
            if qid and qid not in qids:
                qids.append(qid)
        if qids:
            if len(qids) == 1:
                parts.append(f"One new gate opened for Mike: {qids[0]}.")
            else:
                parts.append(
                    f"New gates opened for Mike: {', '.join(qids[:4])}."
                )

    text = " ".join(parts).strip()
    # Word-cap ~120 words
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]).rstrip(",;:") + "…"
    return text or "Activity logged today, no headline moves yet."


def _render_week_prose(events: list[dict[str, Any]],
                       now: datetime | None = None,
                       tasks_by_id: dict[str, dict[str, Any]] | None = None
                       ) -> str:
    """Chronological prose summary of the last 72 hours. Max ~150 words."""
    now = now or datetime.now(timezone.utc)
    tasks_by_id = tasks_by_id or {}
    week_start = now - timedelta(hours=72)
    window = _events_between(events, week_start, now)
    if not window:
        return ("The last three days have been quiet — no merges, canaries, "
                "or reviews recorded in the event stream.")

    # Find phase transitions + major merges chronologically
    window_sorted = sorted(window, key=lambda e: e.get("ts", ""))

    # Group merges by day
    merges_by_day: dict[str, list[str]] = {}
    canaries_by_day: dict[str, list[str]] = {}
    for e in window_sorted:
        ts = _parse_event_ts(e.get("ts", ""))
        if not ts:
            continue
        day = ts.strftime("%Y-%m-%d")
        tid = e.get("task_id")
        if e.get("event_type") == "MERGED" and tid:
            merges_by_day.setdefault(day, []).append(tid)
        if e.get("event_type") in ("CANARY_PASS", "CANARY_STARTED") and tid:
            canaries_by_day.setdefault(day, []).append(tid)

    # Phase grouping
    merged_tasks = sorted({t for ts in merges_by_day.values() for t in ts})
    phase_a_merged = [t for t in merged_tasks if (t or "").startswith("A")]
    phase_b_merged = [t for t in merged_tasks if (t or "").startswith("B")]

    # Total counts
    total_merges = sum(len(v) for v in merges_by_day.values())
    total_canaries = sum(len(v) for v in canaries_by_day.values())
    reviews = sum(1 for e in window if e.get("event_type") == "REVIEW_POSTED")
    decisions = sum(1 for e in window
                    if e.get("event_type") in
                    ("DECISION_NEEDED", "DECISION_RESOLVED"))

    parts: list[str] = []
    parts.append(
        f"Over the last three days, the stream recorded {_n_as_word(total_merges)} "
        f"merge{'s' if total_merges != 1 else ''}, "
        f"{_n_as_word(total_canaries)} canary event{'s' if total_canaries != 1 else ''}, "
        f"and {_n_as_word(reviews)} review{'s' if reviews != 1 else ''} "
        f"posted across the board."
    )

    if phase_a_merged:
        refs = [_short_task(t, tasks_by_id) for t in phase_a_merged[:4]]
        parts.append(
            "Phase A work continued to settle with "
            + (", ".join(refs[:-1]) + ", and " + refs[-1] if len(refs) > 1
               else refs[0])
            + " reaching prod."
        )
    if phase_b_merged:
        refs = [_short_task(t, tasks_by_id) for t in phase_b_merged[:4]]
        parts.append(
            "Phase B Wave 2 is in flight — "
            + (", ".join(refs[:-1]) + ", and " + refs[-1] if len(refs) > 1
               else refs[0])
            + " shipped in this window."
        )
    if decisions:
        parts.append(
            f"{_n_as_word(decisions).capitalize()} decision "
            f"event{'s' if decisions != 1 else ''} flowed through the "
            f"Mike-gate process."
        )

    text = " ".join(parts).strip()
    words = text.split()
    if len(words) > 150:
        text = " ".join(words[:150]).rstrip(",;:") + "…"
    return text


def _render_whats_next_prose(data: dict[str, Any] | None = None) -> str:
    """Prose summary of upcoming milestones — reads STATE-OF-SPRINT.md's
    'What's Next' / 'Next' section when available, otherwise synthesises from
    the current blocker set + open decisions. Max ~120 words."""
    body = (_read_sos_section("What's Next")
            or _read_sos_section("Whats Next")
            or _read_sos_section("Next"))
    if body:
        # Flatten bullets → prose. First collapse list items into sentences.
        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
        sentences = []
        for ln in lines:
            s = re.sub(r"^[-*+]\s+", "", ln)
            s = re.sub(r"^\d+\.\s+", "", s)
            if s and not s.startswith("#"):
                if s[-1] not in ".!?":
                    s = s + "."
                sentences.append(s)
        text = " ".join(sentences)
        words = text.split()
        if len(words) > 120:
            text = " ".join(words[:120]).rstrip(",;:") + "…"
        return text or (
            "State of Sprint doc is being built by Scribe — upcoming "
            "milestones will appear here next regen."
        )

    # Fallback: synthesize from current open decisions + tasks in flight
    if not data:
        return ("State of Sprint doc being built by Scribe — upcoming "
                "milestones will appear here once the Scribe populates the "
                "'What's Next' section.")

    tasks = data.get("tasks") or []
    open_decs = data.get("open_decisions") or []
    in_flight = [t for t in tasks
                 if t.get("status") in ("CODE", "PR_REVIEW", "CANARY",
                                        "PROPOSAL", "PROPOSAL_REVIEW")]
    in_flight.sort(key=lambda t: t.get("id") or "")
    parts = []
    if in_flight:
        refs = [f"{t['id']} ({STATUS_HUMAN.get(t['status'], t['status']).lower()})"
                for t in in_flight[:4]]
        parts.append("Next up: " + ", ".join(refs) + ".")
    if open_decs:
        parts.append(
            f"{_n_as_word(len(open_decs)).capitalize()} open Mike-gate"
            f"{'s' if len(open_decs) != 1 else ''} — "
            + ", ".join(d.get("question_id", "?") for d in open_decs[:4])
            + " — pending resolution."
        )
    if not parts:
        parts.append(
            "State of Sprint doc being built by Scribe — upcoming milestones "
            "will appear here."
        )
    text = " ".join(parts)
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]).rstrip(",;:") + "…"
    return text


def _integrity_human_line(integrity: dict[str, Any]) -> str:
    """Translate the machine-readable events-integrity strip into plain
    English for the dashboard."""
    total = integrity.get("total") or 0
    last_24h = integrity.get("last_24h") or 0
    rate = integrity.get("rate_per_hour") or 0.0
    monotonic_ok = integrity.get("monotonic_ok", True)
    if last_24h == 0:
        return (f"In plain English: quiet — {total} events on file, nothing "
                f"recorded in the last 24 hours.")
    # Rough healthiness — gaps hurt, otherwise healthy.
    health = "System is healthy." if monotonic_ok else "Event stream has order gaps — review needed."
    if last_24h < 5:
        return (f"In plain English: only {last_24h} things happened in the "
                f"last 24 hours — a slow day. {health}")
    return (f"In plain English: {last_24h} things happened today, ~{rate}/h "
            f"steady-state. {health}")


# Two-sentence human blurbs per phase — used by phase pages. Kept short so
# they read naturally as the first paragraph a non-engineer sees.
_PHASE_HUMAN_FALLBACK = {
    "A": (
        "Phase A is the data-truth gate: it fixed correctness bugs in the "
        "SQLite signal layer (schema, remaining_pct, partial closes, ghost "
        "closures, UPDATE→NEW dedup) so downstream phases can trust the "
        "numbers. "
        "It shipped 11 tasks across 4 waves and is complete."
    ),
    "B": (
        "Phase B migrates OinkFarm from SQLite + monolith to PostgreSQL + "
        "decomposed services — the infrastructure layer that unlocks Redis, "
        "W1 governance, and multi-writer safety. "
        "Wave 1 (db abstraction) shipped; Wave 2 (parser extraction, "
        "Cornix/Chroma, dedup consolidation) is in flight."
    ),
    "C": (
        "Phase C builds mature observability on top of Phase A+B — "
        "dashboards, alerting, SLOs, and confidence-routing so the trading "
        "loop can be measured and tuned. "
        "Scoped but not yet started."
    ),
    "HH": (
        "Heavy Hybrid is the long-horizon roadmap captured as Q-HH decisions "
        "— Redis placement, retention policy, container strategy, W1 "
        "enforcement, confidence routing, and Phase-D gating. "
        "Six decisions resolved, zero open."
    ),
}


def _phase_human_blurb(phase: str) -> str:
    """Return a 2-sentence plain-English blurb for the phase. Prefers the
    matching '## Phase X' section from STATE-OF-SPRINT.md; falls back to the
    hard-coded defaults above."""
    key = (phase or "").strip().upper().replace("PHASE-", "").replace(" ", "")
    # Try multiple section heading variants
    candidates = []
    if key == "HH":
        candidates = ["Heavy Hybrid", "Phase HH", "Heavy-Hybrid"]
    else:
        candidates = [f"Phase {key}", f"Phase-{key}"]
    for cand in candidates:
        body = _read_sos_section(cand)
        if body:
            # Take first two sentences, strip bullets
            clean = re.sub(r"^[-*+]\s+", "", body, flags=re.M).strip()
            sentences = re.split(r"(?<=[.!?])\s+", clean)
            out = " ".join(sentences[:2]).strip()
            if out:
                return out
    return _PHASE_HUMAN_FALLBACK.get(
        key,
        "Phase documentation pending — State of Sprint doc being built by Scribe.",
    )


# --- Per-task 'In plain English' blurb ------------------------------------ #

# Hand-curated plain-English blurbs. Used as the canonical source when
# available; otherwise _task_plain_english falls back to event-history.
_TASK_PLAIN_ENGLISH = {
    "A1": (
        "A1 introduced a dedicated signal_events table with 12 lifecycle "
        "event types. Before this, signal state changes were scattered across "
        "log files and status columns, making it impossible to reconstruct "
        "history. Now every lifecycle transition leaves a durable, queryable "
        "event row."
    ),
    "A2": (
        "A2 fixed the remaining_pct model so blended PnL is arithmetically "
        "correct after partial closes. The old model silently mixed full- and "
        "partial-close rows, producing wrong aggregate numbers on any signal "
        "that hit a partial TP."
    ),
    "A3": (
        "A3 auto-populates filled_at for MARKET orders at INSERT-time. "
        "Previously it was left NULL and backfilled late (or not at all), "
        "which broke downstream latency metrics."
    ),
    "A4": (
        "A4 added the PARTIALLY_CLOSED status so partial-TP signals have a "
        "clean lifecycle. Before this, signals hit a limbo state whenever a "
        "TP1/TP2 fired without all levels closing — breaking PnL aggregation."
    ),
    "A5": (
        "A5 introduced parser-type confidence scoring (regex / board / LLM "
        "weights) so we can tell which parser produced a signal and how much "
        "to trust it. This is the foundation for Phase C confidence routing."
    ),
    "A6": (
        "A6 emits a GHOST_CLOSURE event + note tag whenever the reconciler "
        "soft-closes a signal on board-absent. Purely additive, no financial "
        "writes — gives us an audit trail for closures that previously "
        "happened silently."
    ),
    "A7": (
        "A7 added UPDATE→NEW dedup with 5% tolerance to prevent phantom "
        "trades. Without this, a stream re-broadcast or tiny price wiggle "
        "could create a duplicate signal and fire a real order twice."
    ),
    "A8": (
        "A8 added a conditional SL type column (NONE / NUMERIC / MANUAL / BE "
        "/ CONDITIONAL) so we can classify stop-loss origin at INSERT-time. "
        "This lets us tell Mike's context-dependent SLs apart from explicit "
        "numeric ones."
    ),
    "A9": (
        "A9 normalizes entry + SL prices for 1000x-prefixed symbols "
        "(1000SHIB, 1000PEPE, …) by dividing by 1000 at INSERT. Before this, "
        "~7% of signals had off-by-1000 prices and the SL_DEVIATION guard "
        "incorrectly rejected valid signals."
    ),
    "A10": (
        "A10 merged 912 test-DB signals into prod using a council-approved "
        "append-only strategy. This was the first non-standard governance "
        "path in the sprint — OinkV + OinkDB co-signed via GH Issue #136 — "
        "and it produced 1,407 rows with zero NULL invariants and zero "
        "orphans."
    ),
    "A11": (
        "A11 persists a leverage_source column (EXPLICIT / DEFAULT / NULL) "
        "alongside the leverage value at INSERT-time. This gives us "
        "provenance for every leverage number — we can tell which came from "
        "the signal and which were filled from defaults."
    ),
    "B1": (
        "B1 shipped oink_db.py — a thin wrapper module that makes every "
        "sqlite3 caller backend-agnostic. Before this, swapping to PostgreSQL "
        "would have meant touching every query site; now it's a one-line "
        "config change at the top of the module."
    ),
    "B8": (
        "B8 consolidated signal deduplication logic into a dedicated dedup.py "
        "module. Before this, dedup was scattered across four places in the "
        "codebase, making bugs hard to find. Now all dedup logic lives in "
        "one module with a clear public API."
    ),
}


def _task_plain_english(task: dict[str, Any]) -> str:
    """Return a short 'Why this task matters' paragraph. Uses curated copy
    when available; falls back to auto-generation from task metadata +
    event history."""
    tid = task.get("id") or ""
    if tid in _TASK_PLAIN_ENGLISH:
        return _TASK_PLAIN_ENGLISH[tid]
    # Fallback: synthesize from metadata
    name = TASK_NAMES.get(tid, tid)
    oneliner = TASK_ONELINERS.get(tid, "").strip()
    tier = task.get("tier", "")
    status_label = STATUS_HUMAN.get(task.get("status", ""), "").lower()
    ev_count = task.get("event_count") or len(task.get("events") or [])
    prs = task.get("prs") or []
    pr_note = ""
    if prs:
        p = prs[0]
        pr_note = f" The work is tracked in {p.get('repo', '?')} PR #{p.get('number', '?')}."
    base = f"{tid} — {name}."
    if oneliner:
        base += f" In plain terms: {oneliner}"
    else:
        base += (f" Tier {tier}, currently {status_label or 'in planning'}, "
                 f"with {ev_count} event(s) on the stream so far.")
    return base + pr_note


def _tstime_filter(iso_str: str | None) -> str:
    if not iso_str: return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(CEST).strftime("%b %d, %H:%M CEST")
    except Exception:
        return iso_str


def render(data: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    env.filters["tstime"] = _tstime_filter
    return env.get_template("index.html.tpl").render(**data)


def write_site(data: dict[str, Any], html: str) -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(html, encoding="utf-8")
    (SITE / "data.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if STATIC.exists():
        for item in STATIC.iterdir():
            dst = SITE / item.name
            if item.is_dir():
                if dst.exists(): shutil.rmtree(dst)
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)


# --------------------------------------------------------------------------- #
# Raw-artifacts + sprint-log emitters (audit trail / per-task archive)
# --------------------------------------------------------------------------- #

RAW = ROOT / "raw-artifacts"
SPRINT_LOG = ROOT / "sprint-log"

TASK_SLUGS = {
    "A1": "signal-events-schema",    "A2": "remaining-pct-model",
    "A3": "auto-filled-at",          "A4": "partially-closed-status",
    "A5": "confidence-scoring",      "A6": "ghost-closure-flag",
    "A7": "update-new-detection",    "A8": "conditional-sl-type",
    "A9": "denomination-multiplier", "A10": "database-merge",
    "A11": "leverage-source-tracking","B1": "db-abstraction-layer",
}
TASK_NAMES = {
    "A1": "signal_events Table + 12 Event Type Instrumentation",
    "A2": "remaining_pct Model + Blended PnL Fix",
    "A3": "Auto filled_at for MARKET Orders",
    "A4": "PARTIALLY_CLOSED Status for Partial TP Signals",
    "A5": "Parser-Type Confidence Scoring",
    "A6": "Ghost Closure Confirmation Flag",
    "A7": "UPDATE→NEW Detection (Phantom Trade Prevention)",
    "A8": "Conditional SL Type Field",
    "A9": "Denomination Multiplier Table (1000x-prefixed symbols)",
    "A10": "Database Merge (test → prod, council-approved)",
    "A11": "Leverage Source Tracking",
    "B1": "Database Abstraction Layer (sqlite3 → oink_db.py)",
}
TASK_WAVE = {"A1": 1, "A2": 1, "A3": 1,
             "A4": 2, "A5": 2, "A7": 2,
             "A6": 3, "A8": 3, "A9": 3, "A11": 3,
             "A10": 4, "B1": "B1"}
TASK_ONELINERS = {
    "A6": "Emit a `GHOST_CLOSURE` lifecycle event + additive note tag "
          "whenever the reconciler soft-closes a signal on `board_absent`; "
          "purely additive, no financial field writes.",
    "A8": "Add a `sl_type` column (`NONE` / `NUMERIC` / `MANUAL` / `BE` / "
          "`CONDITIONAL`) to classify stop-loss origin at INSERT-time.",
    "A9": "Normalize entry + SL prices for `1000*USDT` symbols by dividing "
          "by 1000 at INSERT, and tag with `[A9: denomination_adjusted /1000]`.",
    "A10": "Merge 912 test-DB signals into production with council-approved "
           "append-only strategy, preserving drift on live rows.",
    "A11": "Persist a `leverage_source` column (`EXPLICIT` / `DEFAULT` / NULL) "
           "alongside the leverage value at micro-gate INSERT.",
    "B1": "Thin wrapper module `oink_db.py` that makes every sqlite3 caller "
          "backend-agnostic so Phase B can swap in PostgreSQL with zero "
          "behaviour change.",
}
STATUS_BADGE = {
    "DONE": "✅ DONE", "CANARY": "🧪 CANARY", "PR_REVIEW": "👀 PR REVIEW",
    "CODE": "⚙️ CODING", "PROPOSAL_REVIEW": "📝 PROPOSAL REVIEW",
    "PROPOSAL": "📝 PROPOSAL", "PLANNED": "📋 PLANNED",
    "BLOCKED": "🛑 BLOCKED", "NOT_STARTED": "⏳ NOT STARTED",
}
STATUS_HUMAN = {
    "DONE": "Shipped, canary PASS", "CANARY": "Merged, canary in flight",
    "PR_REVIEW": "PR open, awaiting reviews",
    "CODE": "Phase 0 approved, implementation in progress",
    "PROPOSAL_REVIEW": "Proposal ready, awaiting Phase 0 review",
    "PROPOSAL": "Proposal drafted",
    "PLANNED": "FORGE plan published, not yet started",
    "BLOCKED": "Blocked on decision or dependency",
    "NOT_STARTED": "Not yet started",
}
CANARY_BADGE = {"PASS": "✅ PASS", "WARN": "⚠️ WARN",
                "FAIL": "❌ FAIL", "PENDING": "⏳ PENDING"}

def _fmt_mtime_cest(p: Path) -> str:
    mt = safe_mtime(p)
    return mt.astimezone(CEST).strftime("%H:%M CEST on %d %b %Y") if mt else "—"

def _fmt_bytes(n: int) -> str:
    if n < 1024: return f"{n} B"
    if n < 1024 * 1024: return f"{n/1024:.1f} KB"
    return f"{n/(1024*1024):.2f} MB"

def _raw_link(subdir: str, filename: str) -> str:
    return f"../../raw-artifacts/{subdir}/{filename}"

def _subdir_desc(s: str) -> str:
    return {
        "forge/plans": "FORGE technical plans, A-group summaries, OinkV audits",
        "anvil/proposals": "ANVIL Phase 0 proposals + approval markers",
        "anvil/markers": "Merge, ready-for-review, and lifecycle markers",
        "anvil/followups": "Deferred follow-up tasks (A{N}-F{M})",
        "anvil/backfill-logs": "Post-merge backfill SQL execution logs",
        "vigil/reviews": "VIGIL Phase 0 + Phase 1 code reviews (5-dim scored)",
        "guardian/reviews": "GUARDIAN Phase 0 + Phase 1 data reviews (5-dim scored)",
        "guardian/canary-reports": "Post-deploy canary reports",
        "hermes": "Hermes parallel reviews (LGTM / CONCERNS)",
    }.get(s, s)

# ---- Raw-artifacts emitter ---------------------------------------------------

RAW_GROUPS = [
    ("forge/plans", FORGE / "plans",
     ["TASK-A*.md", "A*-SUMMARY.md", "OINKV-AUDIT*.md",
      "OINKV-AUDIT*.marker", "A*-PLANS-*.marker"]),
    ("anvil/proposals", ANVIL / "proposals",
     ["A*-PROPOSAL.md", "A*-PHASE0-PROPOSAL.md",
      "A*-PHASE0-APPROVED.marker", "A*-PHASE0-REVIEW-APPROVED.marker",
      "A*-PHASE1-APPROVED.marker", "A*-READY-FOR-REVIEW.marker"]),
    ("anvil/markers", ANVIL,
     ["A*-MERGED.marker", "A*-READY-FOR-REVIEW.marker",
      "A*-REVIEW-ROUND*.marker", "A*-CANARY-FALLBACK.md",
      "A*-ZERO-EVENT-ROOT-CAUSE.md"]),
    ("anvil/followups", ANVIL / "followups", ["*.md"]),
    ("anvil/backfill-logs", ANVIL, ["A*-BACKFILL-LOG.md"]),
    ("vigil/reviews", VIGIL / "reviews", ["A*-VIGIL-*REVIEW*.md"]),
    ("guardian/reviews", GUARDIAN / "reviews",
     ["A*-GUARDIAN-*REVIEW*.md", "A*-POST-DEPLOY-VERIFICATION.md"]),
    ("guardian/canary-reports", GUARDIAN / "canary-reports",
     ["A*-CANARY.md", "A*-CANARY-COMPLETE.marker"]),
    ("hermes", HERMES_WS, ["A*-HERMES-REVIEW.md"]),
]

def emit_raw_artifacts(data: dict[str, Any]) -> dict[str, int]:
    """Copy verbatim agent artifacts into ./raw-artifacts/ for audit trail."""
    if RAW.exists(): shutil.rmtree(RAW)
    RAW.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for subdir, src, patterns in RAW_GROUPS:
        dst = RAW / subdir
        dst.mkdir(parents=True, exist_ok=True)
        seen: set[Path] = set()
        files: list[Path] = []
        if src.exists():
            for pat in patterns:
                for p in src.glob(pat):
                    if p.is_file() and p not in seen:
                        seen.add(p); files.append(p)
        for p in files:
            try: shutil.copy2(p, dst / p.name)
            except Exception as e:
                sys.stderr.write(f"WARN  copy {p} → {dst}: {e}\n")
        counts[subdir] = len(files)
        lines = [f"# raw-artifacts/{subdir}/\n",
                 f"{_subdir_desc(subdir)}. {len(files)} file(s) copied from `{src}`.\n"]
        if files:
            lines += ["| File | Size | Last modified |", "|---|---|---|"]
            for p in sorted(files, key=lambda f: f.name):
                dp = dst / p.name
                lines.append(f"| [{p.name}]({p.name}) | "
                             f"{_fmt_bytes(_size(dp))} | {_fmt_mtime_cest(dp)} |")
        else:
            lines.append("_No files._")
        (dst / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(counts.values())
    top = ["# raw-artifacts/\n",
           "Verbatim copies of every agent artifact produced during the "
           "OinkFarm Implementation Foresight Sprint. Files are copied (not "
           "symlinked), so this directory is self-contained for audit.\n",
           f"**Total files:** {total}\n", "## Directory Map\n",
           "| Path | Contents | Count |", "|---|---|---|",
           *(f"| [{s}/]({s}/) | {_subdir_desc(s)} | {counts.get(s, 0)} |"
             for s, _src, _pat in RAW_GROUPS),
           "", "For the human-readable per-task archive, see "
           "[`../sprint-log/`](../sprint-log/).", ""]
    (RAW / "README.md").write_text("\n".join(top), encoding="utf-8")
    return counts

# ---- Sprint-log helpers ------------------------------------------------------

def _oneliner_from_plan(p: Path | None, task: str) -> str:
    fallback = TASK_ONELINERS.get(
        task, f"{TASK_NAMES.get(task, task)} — see plan for details.")
    if not p or not p.exists():
        return fallback
    text = safe_read(p, limit=16000)
    m = re.search(r"##\s*0?\.?\s*Executive Summary\s*\n+(.+?)\n\s*\n",
                  text, re.DOTALL | re.IGNORECASE)
    body = m.group(1).strip() if m else ""
    if not body:
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith(("#", "**", "---", "-", "|", ">")):
                if body: break
                continue
            body += (" " if body else "") + s
            if len(body) > 400: break
    if not body:
        return fallback
    body = re.sub(r"\s+", " ", body).strip()
    sent = re.split(r"(?<=[.!?])\s+", body, maxsplit=1)[0]
    return (sent[:317] + "…") if len(sent) > 320 else sent

def _find_oinkv_audit(task: str) -> Path | None:
    plans = FORGE / "plans"
    cands = [
        plans / f"OINKV-AUDIT-WAVE2-{task}.md",
        plans / f"OINKV-AUDIT-WAVE3-{task}.md",
        plans / f"OINKV-AUDIT-PHASE-B-{task}.md",
    ]
    if task in ("A1", "A2", "A3"):
        cands.append(plans / "OINKV-AUDIT.md")
    for c in cands:
        if c.exists(): return c
    for p in plans.glob(f"OINKV-AUDIT*{task}*.md"):
        return p
    return None

def _find_review_revisions(src: Path, task: str, phase: str,
                           agent: str) -> list[Path]:
    if not src.exists(): return []
    pat = re.compile(rf"^{task}-{agent}-(?:PHASE{phase}-)?REVIEW(?:-R(\d+))?\.md$")
    found: list[tuple[int, Path]] = []
    for p in src.iterdir():
        if not p.is_file(): continue
        m = pat.match(p.name)
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: (t[0], t[1].name))
    return [p for _, p in found]

def _extract_blocker_count(text: str) -> int | None:
    m = re.search(r"(\d+)\s+(?:blocking concerns?|blockers?|must[- ]fix)",
                  text or "", re.IGNORECASE)
    return int(m.group(1)) if m else None

def _extract_branch_from_merged(text: str) -> str | None:
    if not text: return None
    m = re.search(r"(?:branch(?:\s+deleted)?|BRANCH)\s*[:=]\s*\*{0,2}\s*([\w/\-.]+)",
                  text)
    return m.group(1).strip("*").strip() if m else None

def _followups_for(task: str) -> list[Path]:
    src = ANVIL / "followups"
    return sorted(src.glob(f"{task}-*.md")) if src.exists() else []

def _row(idx: int, phase: str, actor: str, verdict: str,
         path: Path | None, link: str | None) -> str:
    ts = _fmt_mtime_cest(path) if path else "—"
    art = f"[{path.name}]({link})" if (path and link) else (link or "—")
    return f"| {idx} | {phase} | {actor} | {verdict} | {ts} | {art} |"

def _extract_key_decisions(task_id: str, merged_text: str,
                           hermes_text: str) -> list[str]:
    out: list[str] = []
    p1 = ANVIL / "proposals" / f"{task_id}-PHASE1-APPROVED.marker"
    if p1.exists():
        for line in safe_read(p1).splitlines():
            s = line.strip()
            if re.match(r"^[1-8]\.\s", s) and 20 < len(s) < 280:
                out.append(re.sub(r"^\d+\.\s*", "", s).rstrip("."))
            if len(out) >= 5: break
    if merged_text and len(out) < 5:
        m = re.search(r"##\s*Scope Delivered\s*\n+([\s\S]+?)(?:\n##|\Z)", merged_text)
        if m:
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith(("- ", "* ", "• ")):
                    d = s.lstrip("-*• ").strip()
                    if 15 < len(d) < 280: out.append(d)
                if len(out) >= 6: break
    if hermes_text and len(out) < 4:
        m = re.search(r"(?:###|##)\s*.*?(?:Correctness|Findings)[^\n]*\n+"
                      r"([\s\S]+?)(?:\n##|\n---|\Z)", hermes_text, re.IGNORECASE)
        if m:
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith(("- ", "* ", "• ")):
                    d = s.lstrip("-*• ").strip().lstrip("✅ ⚠️ ❌ ").strip()
                    if 15 < len(d) < 280 and not any(
                        d.startswith(e[:30]) for e in out):
                        out.append(d)
                if len(out) >= 6: break
    seen: set[str] = set()
    dedup: list[str] = []
    for d in out:
        k = d[:60].lower()
        if k in seen: continue
        seen.add(k); dedup.append(d)
        if len(dedup) >= 8: break
    return dedup

def _build_task_timeline(task: dict[str, Any]
                         ) -> tuple[list[str], dict[str, Any]]:
    tid = task["id"]
    art = {k: Path(v) for k, v in task["artifacts"].items()}
    scores, verdicts, canary, prs = (task["scores"], task["verdicts"],
                                     task["canary"], task["prs"])
    meta: dict[str, Any] = {"oinkv": None, "backfill": None, "branch": None,
                            "guardian_p0_revs": [], "vigil_p1_revs": []}
    rows: list[str] = []
    idx = 0

    def add(label, actor, verd, p, subdir):
        nonlocal idx
        idx += 1
        rows.append(_row(idx, label, actor, verd, p,
                         _raw_link(subdir, p.name) if p else None))

    if "forge_plan" in art:
        add("FORGE plan published", "🔥 FORGE", "PUBLISHED",
            art["forge_plan"], "forge/plans")

    audit = _find_oinkv_audit(tid)
    if audit:
        meta["oinkv"] = audit
        at = safe_read(audit, limit=4000).lower()
        verd = "FINDINGS" if ("showstopper" in at or "blocking" in at
                              or "critical" in at[:500]) else "PASS"
        add("OinkV audit", "👁️ OinkV", verd, audit, "forge/plans")

    if "proposal" in art:
        p1m = ANVIL / "proposals" / f"{tid}-PHASE1-APPROVED.marker"
        label = "DRAFTED (R1)" if p1m.exists() else "DRAFTED"
        add("Phase 0 proposal drafted", "⚒️ ANVIL", label,
            art["proposal"], "anvil/proposals")

    if "vigil_phase0" in art:
        p = art["vigil_phase0"]
        v = extract_verdict(safe_read(p)) or "APPROVE"
        add("Phase 0 review", "🔍 VIGIL",
            "✅ APPROVE" if v == "APPROVE" else f"❌ {v}", p, "vigil/reviews")

    g_revs = _find_review_revisions(GUARDIAN / "reviews", tid, "0", "GUARDIAN")
    meta["guardian_p0_revs"] = g_revs
    for i, p in enumerate(g_revs):
        txt = safe_read(p)
        v = extract_verdict(txt) or "APPROVE"
        suffix = f" (R{i})" if i else ""
        if v == "APPROVE":
            badge = f"✅ APPROVE{suffix}"
        else:
            bc = _extract_blocker_count(txt)
            badge = f"❌ CHANGES{' (' + str(bc) + ' blockers)' if bc else ''}{suffix}"
        add(f"Phase 0 review{suffix}", "🛡️ GUARDIAN", badge, p, "guardian/reviews")

    p0_m = ANVIL / "proposals" / f"{tid}-PHASE0-APPROVED.marker"
    p1_m = ANVIL / "proposals" / f"{tid}-PHASE1-APPROVED.marker"
    approval = p1_m if p1_m.exists() else (p0_m if p0_m.exists() else None)
    if approval:
        add("Phase 0 approval", "🪽 Hermes", "✅ APPROVED",
            approval, "anvil/proposals")

    if prs:
        idx += 1
        pr_lines = " + ".join(f"[{p['repo']}#{p['number']}]({p['pr_url']})"
                              for p in prs)
        merged_p = Path(task["artifacts"].get("merged", "/nonexistent"))
        rows.append(f"| {idx} | Phase 1 code | ⚒️ ANVIL | MERGED | "
                    f"{_fmt_mtime_cest(merged_p)} | {pr_lines} |")

    v_revs: list[Path] = []
    if "vigil_phase1" in art: v_revs.append(art["vigil_phase1"])
    for rn in (1, 2, 3):
        rf = VIGIL / "reviews" / f"{tid}-VIGIL-PHASE1-REVIEW-R{rn}.md"
        if rf.exists() and rf not in v_revs: v_revs.append(rf)
    meta["vigil_p1_revs"] = v_revs
    for i, p in enumerate(v_revs):
        sc = extract_score(safe_read(p))
        v = extract_verdict(safe_read(p)) or ""
        badge = f"{sc:.2f}/10" if sc else (v or "—")
        add(f"Phase 1 review{' (R'+str(i)+')' if i else ''}",
            "🔍 VIGIL", badge, p, "vigil/reviews")

    if "guardian_phase1" in art:
        p = art["guardian_phase1"]
        sc = scores.get("guardian")
        badge = f"{sc:.2f}/10" if sc else (verdicts.get("guardian") or "—")
        add("Phase 1 review", "🛡️ GUARDIAN", badge, p, "guardian/reviews")

    if "hermes" in art:
        p = art["hermes"]
        v = verdicts.get("hermes") or extract_verdict(safe_read(p)) or "LGTM"
        add("Hermes parallel review", "🪽 Hermes",
            f"✅ {v}" if v in ("LGTM", "PASS", "APPROVE") else f"⚠️ {v}",
            p, "hermes")

    if "merged" in art:
        p = art["merged"]
        mt = safe_read(p)
        b = _extract_branch_from_merged(mt)
        if b: meta["branch"] = b
        pr_tags = []
        for pr in prs:
            if pr.get("merge_commit"):
                pr_tags.append(f"[{pr['merge_commit'][:7]}]"
                               f"({pr.get('commit_url') or pr['pr_url']})")
            else:
                pr_tags.append(f"[#{pr['number']}]({pr['pr_url']})")
        add("Merged", "⚒️ ANVIL",
            f"MERGED {' + '.join(pr_tags) if pr_tags else ''}".rstrip(),
            p, "anvil/markers")

    bf = ANVIL / f"{tid}-BACKFILL-LOG.md"
    if bf.exists():
        meta["backfill"] = bf
        m = re.search(r"(\d+)\s+rows?\s*(?:updated|backfilled|affected)",
                      safe_read(bf, limit=2000), re.I)
        add("Backfill", "⚒️ ANVIL",
            f"{m.group(1)} rows" if m else "executed",
            bf, "anvil/backfill-logs")

    if "canary" in art:
        v = canary["verdict"] or "PENDING"
        add("Canary", "🛡️ GUARDIAN", CANARY_BADGE.get(v, v),
            art["canary"], "guardian/canary-reports")

    return rows, meta

def _distill_lessons(tid: str, meta: dict[str, Any],
                     merged_text: str) -> list[str]:
    out: list[str] = []
    g = len(meta.get("guardian_p0_revs", []))
    if g > 1:
        out.append(f"- **Phase 0 took {g} rounds** — GUARDIAN surfaced "
                   f"blast-radius concerns that reshaped scope before code "
                   f"was written. Cheaper to revise a proposal than a PR.")
    v = len(meta.get("vigil_p1_revs", []))
    if v > 1:
        out.append(f"- **VIGIL Phase 1 needed {v} rounds** — initial score "
                   f"below the tier threshold triggered fix-and-rescore loop.")
    if merged_text and "CRITICAL" in merged_text and tid in (
            "A1", "A2", "A4", "A7", "A9", "A10"):
        out.append("- **Auto-escalation to 🔴 CRITICAL** via Financial Hotpath "
                   "rule — Phase 1 used the stricter ≥9.5 threshold.")
    task_lessons = {
        "A4": [
            "- **Same-cycle closure path** (remaining_pct → 0 on TP-all-hit) "
            "avoided PARTIALLY_CLOSED limbo via one atomic UPDATE carrying "
            "`final_roi` + `closed_at` + `close_source`.",
            "- **E5 (`_calculate_pnl` filter)** was the non-obvious "
            "blast-radius save — GUARDIAN's R0 flagged that E3 would "
            "fetch PARTIALLY_CLOSED rows but PnL would silently be `None`.",
        ],
        "A6": [
            "- **Additive-metadata-only discipline** kept A6 out of the "
            "Financial Hotpath registry — no financial-field writes, no DDL, "
            "no close_source mutation.",
            "- **`changes()` coupling** was the elegant TOCTOU fix: gate the "
            "note UPDATE on the actual rowcount of the INSERT within the "
            "same connection/transaction.",
            "- **Entry-price discriminator with 5% tolerance** (mirroring A7) "
            "handles the multi-ACTIVE-signal-per-symbol edge case cleanly.",
        ],
        "A8": [
            "- **Additive DDL first, code deploy second** — migration SQL "
            "applied before the code that reads it, so a rollback is a "
            "simple code revert (the column is nullable).",
            "- **CONDITIONAL classification** distinguishes Mike's "
            "context-dependent SL from explicit numeric SLs without "
            "breaking existing NUMERIC/MANUAL semantics.",
            "- **Deferred dry_run_insert parity** (Hermes concern #2) as "
            "tech debt — low risk, not a Phase 1 blocker.",
        ],
        "A9": [
            "- **Normalize early, dedup after** — entry-price normalization "
            "had to move to §3b (before all guards) so the snowflake dedup "
            "probe at §4 + §4b matched stored values (GUARDIAN P2 fix).",
            "- **SL normalization in §8a-A9** (before B11 deviation guard) "
            "prevented valid 1000x signals with SL from being rejected by "
            "the SL_DEVIATION guard (GUARDIAN P1 fix).",
            "- **R2 delta review** converged all three reviewers (VIGIL "
            "9.40 · GUARDIAN 9.80 · Hermes LGTM) after 2 rounds.",
            "- **INSERT-time-only scope** deliberately left UPDATE and "
            "CLOSURE normalization for A9.1 follow-up — avoided blast-"
            "radius creep.",
        ],
        "A10": [
            "- **Append-only beat cp-overwrite** — validated backup at "
            "18:24Z had drifted (3 signals closed, 76 price updates) by "
            "merge time; append-only preserved live trader state while "
            "achieving identical council-validated end state.",
            "- **Council governance** (OinkV + OinkDB ✅ via GH Issue #136) "
            "was the first non-standard approval path in the sprint — "
            "proved the Hermes+2-council pattern for Phase D gating.",
            "- **Zero ID collisions by design** (prod max=1611, imports "
            "start=1612) made the append-only method SQL-safe without a "
            "preliminary ID rewrite.",
            "- **Drift-inclusive backup** (`oinkfarm.db.a10-predrift-backup-"
            "20260419T182923Z`) gave a 2-step rollback: drift state OR "
            "pre-merge 494-row state.",
        ],
        "A11": [
            "- **🟢 LIGHTWEIGHT path** skipped Phase 0 and GUARDIAN review "
            "per SOUL.md §0 — shipped in one round with VIGIL PASS only.",
            "- **Backfill `leverage IS NOT NULL → EXPLICIT`** cleanly "
            "populated the new column for the 98 non-NULL historical rows.",
            "- **ANVIL spot-check** (10 organic INSERTs post-deploy) "
            "substituted for GUARDIAN canary on LIGHTWEIGHT tier.",
        ],
    }
    if tid in task_lessons:
        out.extend(task_lessons[tid])
    if meta.get("backfill"):
        out.append("- **Backfill pre-SELECT + abort-if-rowcount guard** caught "
                   "a data-quality anomaly without failing the migration.")
    return out[:7] if out else ["_(Lessons distilled at wave close.)_"]

def _render_task_page(task: dict[str, Any]) -> str:
    tid = task["id"]
    tier_em, tier = task["tier_emoji"], task["tier"]
    auto_esc = {
        "A4": " — auto-escalated to 🔴 CRITICAL in Phase 1 (Financial Hotpath)",
        "A7": " — Financial Hotpath from inception",
    }.get(tid, "")
    plan_path = (Path(task["artifacts"]["forge_plan"])
                 if task["artifacts"].get("forge_plan") else None)
    prs = task["prs"]
    pr_line = " + ".join(f"[{p['repo']}#{p['number']}]({p['pr_url']})"
                         for p in prs) if prs else "—"
    merge_line = " + ".join(
        f"[{p['merge_commit'][:12]}]({p.get('commit_url') or p['pr_url']})"
        for p in prs if p.get("merge_commit")) or "—"
    rows, meta = _build_task_timeline(task)
    branch = meta.get("branch") or (
        "anvil/A4-partially-closed-status" if tid == "A4" and not prs else None)
    merged_text = (safe_read(Path(task["artifacts"]["merged"]))
                   if "merged" in task["artifacts"] else "")
    hermes_text = (safe_read(Path(task["artifacts"]["hermes"]))
                   if "hermes" in task["artifacts"] else "")
    decisions = _extract_key_decisions(tid, merged_text, hermes_text)
    followups = _followups_for(tid)
    status = task["status"]
    L = [f"# Task {tid} — {TASK_NAMES.get(tid, tid)}\n",
         f"**Tier:** {tier_em} {tier}{auto_esc}  ",
         f"**Wave:** {TASK_WAVE.get(tid, '—')}  ",
         f"**Status:** {STATUS_BADGE.get(status, status)} — "
         f"{STATUS_HUMAN.get(status, '')}  ",
         f"**Repo target:** {task['repo_hint'] or '—'}  ",
         f"**Branch:** {branch or '—'}  ",
         f"**PR:** {pr_line}  ",
         f"**Merge commit:** {merge_line}",
         "",
         "## In plain English",
         "",
         _task_plain_english(task),
         "",
         "## One-liner", "", _oneliner_from_plan(plan_path, tid), "",
         "## Timeline", "",
         "| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |",
         "|---|---|---|---|---|---|", *rows,
         "", "## Key Decisions", ""]
    if decisions:
        L.extend(f"- {d}" for d in decisions)
    elif status in ("PLANNED", "NOT_STARTED"):
        L.append("_(To be distilled once Phase 0 proposal is drafted.)_")
    elif status == "DONE":
        L.append("_(No structured decision list extractable from merge "
                 "artifacts — see the MERGED marker + FORGE plan for "
                 "decision trail.)_")
    else:
        L.append("_(Pending — will be distilled after merge.)_")
    L += ["", "## Deferrals (Follow-up Tasks)", ""]
    L.extend([f"- [{fu.name}]({_raw_link('anvil/followups', fu.name)})"
              f" — {_extract_title(fu)}" for fu in followups] or ["_None._"])
    L += ["", "## Artifacts (Full Index)", ""]
    if plan_path and plan_path.exists():
        L.append(f"- **FORGE plan:** [{plan_path.name}]"
                 f"({_raw_link('forge/plans', plan_path.name)}) "
                 f"— {_fmt_bytes(_size(plan_path))}")
    if meta.get("oinkv"):
        op = meta["oinkv"]
        L.append(f"- **OinkV audit:** [{op.name}]"
                 f"({_raw_link('forge/plans', op.name)}) "
                 f"— {_fmt_bytes(_size(op))}")
    if "proposal" in task["artifacts"]:
        pp = Path(task["artifacts"]["proposal"])
        rev = " (R1)" if (ANVIL / "proposals"
                          / f"{tid}-PHASE1-APPROVED.marker").exists() else ""
        L.append(f"- **ANVIL proposal:** [{pp.name}]"
                 f"({_raw_link('anvil/proposals', pp.name)}) "
                 f"— {_fmt_bytes(_size(pp))}{rev}")
    vl = []
    if "vigil_phase0" in task["artifacts"]:
        vp = Path(task["artifacts"]["vigil_phase0"])
        vl.append(f"[Phase 0]({_raw_link('vigil/reviews', vp.name)})")
    for i, p in enumerate(meta.get("vigil_p1_revs", [])):
        vl.append(f"[Phase 1{' R'+str(i) if i else ''}]"
                  f"({_raw_link('vigil/reviews', p.name)})")
    if vl: L.append("- **VIGIL reviews:** " + " · ".join(vl))
    gl = []
    for i, p in enumerate(meta.get("guardian_p0_revs", [])):
        gl.append(f"[Phase 0{' R'+str(i) if i else ''}]"
                  f"({_raw_link('guardian/reviews', p.name)})")
    if "guardian_phase1" in task["artifacts"]:
        gp = Path(task["artifacts"]["guardian_phase1"])
        gl.append(f"[Phase 1]({_raw_link('guardian/reviews', gp.name)})")
    if gl: L.append("- **GUARDIAN reviews:** " + " · ".join(gl))
    if "hermes" in task["artifacts"]:
        hp = Path(task["artifacts"]["hermes"])
        L.append(f"- **Hermes review:** [{hp.name}]"
                 f"({_raw_link('hermes', hp.name)}) — "
                 f"{task['verdicts'].get('hermes') or 'LGTM'}")
    if "canary" in task["artifacts"]:
        cp = Path(task["artifacts"]["canary"])
        L.append(f"- **Canary report:** [{cp.name}]"
                 f"({_raw_link('guardian/canary-reports', cp.name)}) — "
                 f"{task['canary']['verdict'] or 'PENDING'}")
    if meta.get("backfill"):
        bp = meta["backfill"]
        L.append(f"- **Backfill log:** [{bp.name}]"
                 f"({_raw_link('anvil/backfill-logs', bp.name)})")
    for p in prs:
        if p.get("merge_commit"):
            L.append(f"- **Merge commit:** [`{p['merge_commit'][:12]}`]"
                     f"({p.get('commit_url') or p['pr_url']}) "
                     f"({p['repo']} PR #{p['number']})")
    if prs:
        L.append("- **PR(s):** " + " · ".join(
            f"[{p['repo']}#{p['number']}]({p['pr_url']})" for p in prs))
    L += ["", "## Lessons Learned", "",
          *(_distill_lessons(tid, meta, merged_text) if status == "DONE"
            else ["_(Written after canary verdict.)_"]),
          "", "---", "",
          "*[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/"
          "QuantisDevelopment/oinkfarm-sprint-checkpoint) · "
          "[All raw artifacts](../../raw-artifacts/)*"]
    return "\n".join(L) + "\n"

WAVE_FOCUS = {
    1:   "Core schema & formula primitives — events, remaining_pct, auto filled_at.",
    2:   "Lifecycle accuracy & phantom-trade prevention — partial closes, "
         "confidence scoring, UPDATE→NEW dedup.",
    3:   "Metadata enrichment & ghost closure — conditional SL classification, "
         "denomination multiplier, leverage source, ghost-closure flag.",
    4:   "Database merge — test → prod (912 imported signals), council-approved "
         "append-only strategy.",
    "B1":"Database abstraction layer (`oink_db.py`) — backend-agnostic wrapper "
         "so Phase B can swap in PostgreSQL with zero behaviour change.",
}
WAVE_TASKS = {
    1:    ["A1", "A2", "A3"],
    2:    ["A4", "A7", "A5"],
    3:    ["A6", "A8", "A9", "A11"],
    4:    ["A10"],
    "B1": ["B1"],
}
WAVE_ORDER = [1, 2, 3, 4, "B1"]

def _wave_label(wid: Any) -> str:
    return f"Wave {wid} (Phase A)" if isinstance(wid, int) else f"Wave {wid} (Phase B)"

def _wave_slug(wid: Any) -> str:
    return f"wave-{wid}" if isinstance(wid, int) else f"wave-{str(wid).lower()}"

def _render_wave_page(wid: Any, tasks: list[dict[str, Any]]) -> str:
    focus = WAVE_FOCUS.get(wid, "—")
    done = sum(1 for t in tasks if t["status"] == "DONE")
    in_flight = sum(1 for t in tasks
                    if t["status"] not in ("DONE", "PLANNED", "NOT_STARTED"))
    planned = sum(1 for t in tasks
                  if t["status"] in ("PLANNED", "NOT_STARTED"))
    status_line = (f"**Status:** {done}/{len(tasks)} shipped · {in_flight} "
                   f"in flight · {planned} planned")
    if wid == "B1":
        status_line = f"**Status:** 📝 IN-FLIGHT — B1 Phase 0 proposal drafted"

    L = [f"# {_wave_label(wid)} Retrospective\n", f"**Focus:** {focus}\n",
         status_line + "\n", "## Tasks\n",
         "| Task | Name | Tier | Status | Canary | Merge commit |",
         "|---|---|---|---|---|---|"]
    for t in tasks:
        tid = t["id"]
        slug = TASK_SLUGS.get(tid, tid.lower())
        commit = "—"
        if t["prs"] and t["prs"][0].get("merge_commit"):
            c = t["prs"][0]["merge_commit"]
            commit = (f"[`{c[:7]}`]"
                      f"({t['prs'][0].get('commit_url') or t['prs'][0]['pr_url']})")
        L.append(f"| [{tid}](../tasks/{tid}-{slug}.md) | "
                 f"{TASK_NAMES.get(tid, tid)} | "
                 f"{t['tier_emoji']} {t['tier']} | "
                 f"{STATUS_BADGE.get(t['status'], t['status'])} | "
                 f"{t['canary']['verdict'] or '—'} | {commit} |")

    # Timing — first FORGE plan → last merge/canary
    L += ["", "## Timing", ""]
    starts = [t["timeline"][0]["mtime"] for t in tasks
              if t.get("timeline") and t["timeline"][0].get("mtime")]
    ends = [t["timeline"][-1]["mtime"] for t in tasks
            if t.get("timeline") and t["timeline"][-1].get("mtime")]
    if starts and ends:
        try:
            fd = datetime.fromisoformat(min(starts).replace("Z", "+00:00"))
            ld = datetime.fromisoformat(max(ends).replace("Z", "+00:00"))
            L += [f"- Wave start: "
                  f"{fd.astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}",
                  f"- Last activity: "
                  f"{ld.astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}",
                  f"- Elapsed: {(ld - fd).total_seconds() / 3600:.1f} h"]
        except Exception:
            L.append("- (Timing data unavailable.)")
    else:
        L.append("- (No timeline events yet.)")

    L += ["", "## Canary Outcomes", ""]
    canaries = [f"- **{t['id']}**: {CANARY_BADGE.get(t['canary']['verdict'], t['canary']['verdict'])}"
                for t in tasks if t["canary"]["verdict"]]
    L.extend(canaries or ["_No canary verdicts yet._"])

    L += ["", "## Deferred Follow-ups", ""]
    fu_lines = []
    for t in tasks:
        for fu in _followups_for(t["id"]):
            fu_lines.append(f"- [{fu.name}]"
                            f"({_raw_link('anvil/followups', fu.name)})"
                            f" — {_extract_title(fu)}")
    L.extend(fu_lines or ["_None._"])

    L += ["", "## Lessons Learned", ""]
    wave_lessons = {
        1: ["- **FORGE → ANVIL → VIGIL/GUARDIAN → Hermes** pattern cleared "
            "three tasks in one overnight push (22:00–04:42 CEST).",
            "- **A1 zero-event root cause** caught a silent production gap — "
            "the 12 event types weren't firing at all. Canary fallback saved "
            "the day.",
            "- **A2 blended-PnL fix** landed first because every downstream "
            "task depends on `remaining_pct` arithmetic being correct."],
        2: ["- **Same-cycle closure** (A4) is the canonical example of "
            "avoiding partial-state limbo — atomic UPDATE carries the whole "
            "transition.",
            "- **A7 UPDATE→NEW detection** uses the same entry-price "
            "discriminator (5% tolerance) that A6 later reused for ghost "
            "closure — good pattern emerging.",
            "- **A5 confidence scoring** came out of Phase 0 clean — "
            "additive column + INSERT-time logic, zero blast radius."],
        3: ["- **Four tasks shipped in one wave** (A6, A8, A9, A11) without "
            "stepping on each other — tier discipline (🟡 vs 🟢) kept GUARDIAN "
            "load focused on A6/A8/A9.",
            "- **A9's 2-round convergence** was the most complex — entry "
            "normalization had to move to §3b AND the dedup probe had to "
            "follow suit before GUARDIAN P1/P2 cleared.",
            "- **A11 LIGHTWEIGHT path** proved the 🟢 lane: VIGIL-only, no "
            "GUARDIAN, no canary, ANVIL spot-check — shipped cleanly in 1 "
            "round."],
        4: ["- **Council governance first run** — OinkV + OinkDB co-signed "
            "via GH Issue #136. Pattern now reusable for Phase D gating.",
            "- **Drift-aware merge** — the validated test backup had drifted "
            "by merge time; append-only preserved the live trader state "
            "without rollback.",
            "- **Post-merge invariants clean** — 1406 signals, 0 orphans, 0 "
            "NULL remaining_pct, 0 NULL sl_type. Production truth restored."],
        "B1": ["- **Phase 0 in flight** — B1 proposal drafted and ready for "
               "parallel VIGIL + GUARDIAN review. Once B1 lands, every DB-"
               "touching module becomes backend-agnostic.",
               "- **Intentionally minimal wrapper** — ~200-300 LOC, preserves "
               "all SQL strings unchanged, zero behavioural changes. The "
               "PostgreSQL migration (B2) layers on top.",
               "- **Test fixtures deliberately untouched** — still use "
               "`sqlite3.connect(\":memory:\")`. Test migration is a B2 "
               "concern, not a B1 one."],
    }
    if wid in wave_lessons:
        L.extend(wave_lessons[wid])
    elif all(t["status"] == "DONE" for t in tasks):
        L.append("- Wave complete — see individual task pages for distilled lessons.")
    else:
        L.append("_(To be filled at wave close.)_")

    L += ["", "---", "",
          "*[Sprint log index](../README.md) · "
          "[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"

# ---- Phase pages -------------------------------------------------------------

def _render_phase_a(data: dict[str, Any]) -> str:
    by_id = {t["id"]: t for t in data["tasks"]}
    phase_a_tasks = [by_id[t] for t in [
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"
    ] if t in by_id]
    done = sum(1 for t in phase_a_tasks if t["status"] == "DONE")

    # Collect phase start/end across all tasks
    starts, ends = [], []
    for t in phase_a_tasks:
        if t.get("timeline"):
            if t["timeline"][0].get("mtime"): starts.append(t["timeline"][0]["mtime"])
            if t["timeline"][-1].get("mtime"): ends.append(t["timeline"][-1]["mtime"])

    start_str = end_str = elapsed_str = "—"
    if starts and ends:
        try:
            fd = datetime.fromisoformat(min(starts).replace("Z", "+00:00"))
            ld = datetime.fromisoformat(max(ends).replace("Z", "+00:00"))
            start_str = fd.astimezone(CEST).strftime("%H:%M CEST on %d %b %Y")
            end_str = ld.astimezone(CEST).strftime("%H:%M CEST on %d %b %Y")
            elapsed_str = f"{(ld - fd).total_seconds() / 3600:.1f} h wall-clock"
        except Exception:
            pass

    L = [
        "# Phase A — Data Truth — Complete Retrospective\n",
        "## What is Phase A?\n",
        f"> {_phase_human_blurb('A')}\n",
        f"**Status:** ✅ COMPLETE — {done}/11 tasks shipped, canaries PASS "
        "across the board  ",
        f"**Started:** {start_str}  ",
        f"**Finished:** {end_str}  ",
        f"**Elapsed:** {elapsed_str}  ",
        "**Repos touched:** `oinkfarm` · `oink-sync` · `signal-gateway`  ",
        "**PRs merged:** 10 across 3 repos\n",
        "## Goal\n",
        "> Fix signal-data correctness on the SQLite foundation before any "
        "infrastructure migration.\n",
        "Phase A is the **data-truth gate** in the Arbiter-Oink HEAVY HYBRID "
        "roadmap. Every downstream phase (B: infrastructure, C: observability, "
        "D: algo) assumes the signal-data layer is correct. Phase A closed that "
        "assumption.\n",
        "## Before / After Metrics\n",
        "| Metric | Before Phase A | After Phase A (prod) | Source |",
        "|---|---|---|---|",
        "| Signals in prod DB | ~495 | **1,407** | A10 merge (912 imported) |",
        "| NULL `remaining_pct` | many | **0** | A10 invariant check |",
        "| NULL `sl_type` | n/a (column didn't exist) | **0** | A8 backfill |",
        "| Orphan signals (no trader) | 1 | **0** | A10 merge inserts missing trader |",
        "| Server orphans | >0 | **0** | A10 invariant check |",
        "| `signal_events` table | ❌ absent | ✅ **12 event types** | A1 |",
        "| `remaining_pct` accuracy | blended PnL wrong | ✅ **correct** | A2 |",
        "| `filled_at` for MARKET orders | sparse NULLs | ✅ **auto-populated** | A3 |",
        "| `PARTIALLY_CLOSED` lifecycle | ❌ no limbo-free close path | ✅ **same-cycle closure** | A4 |",
        "| Parser confidence scoring | absent | ✅ **regex/board/LLM weights** | A5 |",
        "| Ghost closure audit trail | silent | ✅ **`GHOST_CLOSURE` event + note tag** | A6 |",
        "| Phantom-trade UPDATE→NEW detection | absent | ✅ **dedup w/ 5% tolerance** | A7 |",
        "| SL classification | absent | ✅ **`sl_type` column** | A8 |",
        "| 1000x-prefixed symbols | un-normalized | ✅ **÷1000 at INSERT** | A9 |",
        "| Leverage provenance | absent | ✅ **`leverage_source` column** | A11 |",
        "\n",
        "## Wave-by-Wave Breakdown\n",
        "| Wave | Focus | Tasks | Elapsed | Outcome |",
        "|---|---|---|---|---|",
    ]
    for wid in [1, 2, 3, 4]:
        wave_tids = WAVE_TASKS[wid]
        wave_tasks = [by_id[t] for t in wave_tids if t in by_id]
        wstarts = [t["timeline"][0]["mtime"] for t in wave_tasks
                   if t.get("timeline") and t["timeline"][0].get("mtime")]
        wends = [t["timeline"][-1]["mtime"] for t in wave_tasks
                 if t.get("timeline") and t["timeline"][-1].get("mtime")]
        elapsed = "—"
        if wstarts and wends:
            try:
                fd = datetime.fromisoformat(min(wstarts).replace("Z", "+00:00"))
                ld = datetime.fromisoformat(max(wends).replace("Z", "+00:00"))
                elapsed = f"{(ld - fd).total_seconds() / 3600:.1f} h"
            except Exception:
                pass
        wdone = sum(1 for t in wave_tasks if t["status"] == "DONE")
        task_links = " · ".join(
            f"[{tid}](../tasks/{tid}-{TASK_SLUGS.get(tid, tid.lower())}.md)"
            for tid in wave_tids)
        L.append(f"| [Wave {wid}](../waves/wave-{wid}.md) | "
                 f"{WAVE_FOCUS.get(wid, '—').split('—')[0].strip()} | "
                 f"{task_links} | {elapsed} | {wdone}/{len(wave_tids)} shipped |")

    L += ["\n## All 11 Tasks at a Glance\n",
          "| Task | Name | Tier | Wave | Status | Canary | Merge commit |",
          "|---|---|---|---|---|---|---|"]
    for tid in ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"]:
        t = by_id.get(tid)
        if not t: continue
        slug = TASK_SLUGS.get(tid, tid.lower())
        commit = "—"
        if t["prs"] and t["prs"][0].get("merge_commit"):
            c = t["prs"][0]["merge_commit"]
            commit = (f"[`{c[:7]}`]"
                      f"({t['prs'][0].get('commit_url') or t['prs'][0]['pr_url']})")
        L.append(f"| [{tid}](../tasks/{tid}-{slug}.md) | "
                 f"{TASK_NAMES.get(tid, tid)} | "
                 f"{t['tier_emoji']} {t['tier']} | "
                 f"{TASK_WAVE.get(tid, '—')} | "
                 f"{STATUS_BADGE.get(t['status'], t['status'])} | "
                 f"{t['canary']['verdict'] or '—'} | {commit} |")

    L += ["\n## KPIs Improved\n",
          "- **Data correctness:** blended PnL now arithmetically correct on "
          "partial closes (A2 + A4).",
          "- **Event coverage:** 12 lifecycle event types instrumented "
          "(A1) — foundation for W1-W4 observability.",
          "- **Provenance:** parser confidence (A5), leverage source (A11), "
          "SL type (A8) all captured at INSERT-time.",
          "- **Phantom-trade prevention:** UPDATE→NEW dedup (A7) + ghost-"
          "closure flag (A6) close the silent-dup surface.",
          "- **Denomination correctness:** 1000x-prefixed symbol normalization "
          "(A9) fixes entry/SL for a ~7% subset of signals.",
          "- **Production truth:** 912 test-DB signals merged to prod (A10) — "
          "1,407 rows, 0 NULL invariants, 0 orphans.\n",
          "## Governance Firsts\n",
          "- **A10 council governance** (OinkV + OinkDB co-signed via GH "
          "Issue #136) — first non-standard approval path; pattern now "
          "reusable for Phase D gating.",
          "- **VIGIL auto-escalation** (A9 🟢 → 🟡) triggered by Financial "
          "Hotpath registry — proved the tier-discipline system works "
          "without human intervention.",
          "- **Hermes parallel review** (LGTM / CONCERNS / BLOCK) ran on "
          "every 🟡/🔴 merge — caught 2 non-blocking concerns on A8 and "
          "1 deferred on A9.\n",
          "## Deferred to Follow-up (A{N}-F{M})\n"]
    fu_lines = []
    for tid in ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"]:
        for fu in _followups_for(tid):
            fu_lines.append(f"- [{fu.name}]"
                            f"({_raw_link('anvil/followups', fu.name)})"
                            f" — {_extract_title(fu)}")
    L.extend(fu_lines or ["_No explicit follow-ups filed; Hermes concerns on A8 "
                          "(BE→MANUAL, dry_run_insert parity, test schema "
                          "drift) and A9 (UPDATE/CLOSURE paths via A9.1) are "
                          "tracked in the respective MERGED markers._"])
    L += ["\n## What Phase A Did NOT Do\n",
          "- Did **not** touch infrastructure: SQLite remains, monolith "
          "remains, no Redis, no PostgreSQL.",
          "- Did **not** introduce new data flows. All changes are additive "
          "to existing pipelines.",
          "- Did **not** enable Phase D (algo/execution). That is gated on "
          "Phase B data-layer maturity + Phase C observability.\n",
          "## Next\n",
          "→ [Phase B](phase-b.md) — PostgreSQL + decomposed services. B1 "
          "(database abstraction layer) is in flight.\n",
          "---\n",
          "*[Sprint log index](../README.md) · [Live dashboard]"
          "(https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"


def _load_static_template(name: str, **subs: str) -> str:
    """Load a static sprint-log template and apply simple {{ var }} subs."""
    p = TEMPLATES / "sprint-log" / name
    text = safe_read(p)
    for k, v in subs.items():
        text = text.replace("{{ " + k + " }}", v)
    return text or f"# {name}\n\n_(template missing)_\n"


def _render_event_phase_page(data: dict[str, Any], phase_letter: str,
                             title: str, goal: str) -> str:
    """Event-derived phase page: task grid, waves, recent activity, needs-mike."""
    by_id = {t["id"]: t for t in data["tasks"]}
    phase_tasks = [t for t in data["tasks"]
                   if (t.get("phase") or _infer_phase(t["id"])) == phase_letter]
    phase_tasks.sort(key=lambda t: (
        int(re.search(r"\d+", t["id"]).group()) if re.search(r"\d+", t["id"]) else 999
    ))
    done = sum(1 for t in phase_tasks if t["status"] == "DONE")
    total = len(phase_tasks)
    events_all = data.get("_events_all_stream") or []
    phase_events = [
        e for e in events_all
        if (e.get("phase") == phase_letter
            or _infer_phase(e.get("task_id")) == phase_letter)
    ]

    L = [f"# {title}\n",
         f"## What is Phase {phase_letter}?\n",
         f"> {_phase_human_blurb(phase_letter)}\n",
         f"**Status:** {done}/{total} tasks shipped  ",
         f"**Goal:** {goal}  ",
         f"**Data source:** event-stream reducer (`events.jsonl`)  ",
         f"**Live:** [dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)\n",
         "## Tasks (live status from event stream)\n",
         "| Task | Tier | Status | Canary | PRs | Last event | Agents |",
         "|---|---|---|---|---|---|---|"]
    for t in phase_tasks:
        tid = t["id"]
        slug = TASK_SLUGS.get(tid, tid.lower())
        canary = t["canary"].get("verdict") or "—"
        prs = " + ".join(f"[{p['repo']}#{p['number']}]({p['pr_url']})" for p in t.get("prs", [])) or "—"
        last_ts = t.get("last_activity")
        last_ev = t.get("last_event_type") or "—"
        last_str = (
            f"{_tstime_filter(last_ts)} · `{last_ev}`" if last_ts else "—"
        )
        ag_str = " · ".join(t.get("agents_touched", [])[:4]) or "—"
        L.append(f"| [{tid}](../tasks/{tid}-{slug}.md) | "
                 f"{t['tier_emoji']} {t['tier']} | "
                 f"{STATUS_BADGE.get(t['status'], t['status'])} | "
                 f"{canary} | {prs} | {last_str} | {ag_str} |")

    # Waves
    L += ["\n## Waves\n"]
    wave_rows = []
    for w in WAVES:
        w_ids = [tid for tid in w["tasks"] if tid in by_id and
                 (by_id[tid].get("phase") or _infer_phase(tid)) == phase_letter]
        if not w_ids:
            continue
        w_done = sum(1 for tid in w_ids if by_id[tid]["status"] == "DONE")
        wave_rows.append(
            f"- **{w['name']}** — {w_done}/{len(w_ids)} shipped: "
            + " · ".join(f"`{tid}`" for tid in w_ids)
        )
    L.extend(wave_rows or ["_No waves yet for this phase._"])

    # Recent activity (last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_24h = [
        e for e in phase_events
        if (_parse_event_ts(e.get("ts", "")) or datetime.min.replace(tzinfo=timezone.utc)) > cutoff
    ]
    recent_24h.sort(key=lambda e: e.get("ts", ""), reverse=True)
    L += ["\n## Recent activity (last 24h)\n"]
    if recent_24h:
        L += ["| Time | Type | Task | Agent | Summary |",
              "|---|---|---|---|---|"]
        for e in recent_24h[:30]:
            L.append(f"| {_tstime_filter(e.get('ts'))} | `{e.get('event_type')}` | "
                     f"`{e.get('task_id') or '—'}` | {e.get('agent') or '—'} | "
                     f"{_one_line_summary(e)} |")
    else:
        L.append("_No events in the last 24 hours._")

    # Needs Mike (phase-scoped)
    decisions = [d for d in data.get("open_decisions", [])
                 if d.get("phase") == phase_letter
                 or _infer_phase(d.get("task_id")) == phase_letter
                 or (phase_letter in ("B", "C") and d.get("gate_type") == f"phase-{phase_letter.lower()}")]
    L += ["\n## Needs Mike (open gates)\n"]
    if decisions:
        L += ["| Question ID | Question | Task | Age | Options |",
              "|---|---|---|---|---|"]
        for d in decisions:
            opts = " · ".join(d.get("options") or []) or "—"
            L.append(f"| `{d['question_id']}` | {d['question']} | "
                     f"`{d.get('task_id') or '—'}` | {d['age_human']} | {opts} |")
    else:
        L.append("_No open DECISION_NEEDED for this phase._")

    L += ["\n---\n",
          "*[Sprint log index](../README.md) · "
          "[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"


def _render_phase_b(data: dict[str, Any]) -> str:
    if data.get("bootstrap"):
        by_id = {t["id"]: t for t in data["tasks"]}
        b1 = by_id.get("B1")
        b1_status = STATUS_BADGE.get(b1["status"], b1["status"]) if b1 else "—"
        return _load_static_template("phase-b.md.tpl", b1_status=b1_status)
    return _render_event_phase_page(
        data, "B", "Phase B — Infrastructure Migration",
        "Migrate OinkFarm from SQLite + monolithic architecture to PostgreSQL + decomposed services.",
    )


def _render_phase_c(data: dict[str, Any] | None = None) -> str:
    if not data or data.get("bootstrap"):
        return _load_static_template("phase-c.md.tpl")
    return _render_event_phase_page(
        data, "C", "Phase C — Mature Observability",
        "Build measurement, monitoring, and operational sophistication on top of Phase A+B.",
    )


def _render_heavy_hybrid(data: dict[str, Any] | None = None) -> str:
    if not data or data.get("bootstrap"):
        return _load_static_template("heavy-hybrid.md.tpl")
    # Heavy Hybrid: dedicated rendering focused on Q-HH gates + roadmap
    events_all = data.get("_events_all_stream") or []
    hh_decisions = [d for d in data.get("open_decisions", [])
                    if d.get("gate_type") == "heavy-hybrid"]
    # Resolved Q-HH decisions
    resolved_hh = [e for e in events_all
                   if e.get("event_type") == "DECISION_RESOLVED"
                   and str((e.get("extra") or {}).get("question_id", "")).startswith("Q-HH")]
    L = ["# Heavy Hybrid Roadmap — Long-horizon Decisions\n",
         "## What is Heavy Hybrid?\n",
         f"> {_phase_human_blurb('HH')}\n",
         "**Source:** event-stream reducer (Q-HH-* DECISION_NEEDED / DECISION_RESOLVED)\n",
         "## Open Q-HH gates\n"]
    if hh_decisions:
        L += ["| ID | Question | Age | Options |", "|---|---|---|---|"]
        for d in hh_decisions:
            opts = " · ".join(d.get("options") or []) or "—"
            L.append(f"| `{d['question_id']}` | {d['question']} | {d['age_human']} | {opts} |")
    else:
        L.append("_No open Q-HH gates._")
    L += ["\n## Resolved Q-HH decisions\n"]
    if resolved_hh:
        resolved_hh.sort(key=lambda e: e.get("ts", ""), reverse=True)
        L += ["| When | ID | Answer |", "|---|---|---|"]
        for e in resolved_hh:
            ex = e.get("extra") or {}
            L.append(f"| {_tstime_filter(e.get('ts'))} | "
                     f"`{ex.get('question_id', '?')}` | {ex.get('answer', '—')} |")
    else:
        L.append("_None yet._")
    L += ["\n---\n",
          "*[Sprint log index](../README.md) · "
          "[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"


# ---- Event log ---------------------------------------------------------------

EVENT_META = {
    "PLAN_PUBLISHED":  {"emoji": "🔥", "actor": "FORGE"},
    "AUDIT_COMPLETE":  {"emoji": "👁️", "actor": "OinkV"},
    "PROPOSAL_DRAFTED":{"emoji": "⚒️", "actor": "ANVIL"},
    "VIGIL_VERDICT":   {"emoji": "🔍", "actor": "VIGIL"},
    "GUARDIAN_VERDICT":{"emoji": "🛡️", "actor": "GUARDIAN"},
    "HERMES_REVIEW":   {"emoji": "🪽", "actor": "Hermes"},
    "MERGED":          {"emoji": "🚀", "actor": "ANVIL"},
    "CANARY_PASS":     {"emoji": "✅", "actor": "GUARDIAN"},
    "CANARY_FAIL":     {"emoji": "❌", "actor": "GUARDIAN"},
    "CANARY_PENDING":  {"emoji": "⏳", "actor": "GUARDIAN"},
    "DECISION":        {"emoji": "🧭", "actor": "Hermes"},
    "AUTHORITY":       {"emoji": "🔓", "actor": "Mike"},
}

# Hard-coded notable events that aren't extractable from file mtimes
CURATED_EVENTS: list[tuple[str, str, str, str, str | None]] = [
    # (iso_utc, event_type, task_id_or_dash, description, relative_link)
    ("2026-04-18T20:00:00+00:00", "AUTHORITY", "—",
     "Mike grants Hermes \"full authority, push till done\" — enables "
     "autonomous decision-making on Q-HH-1..6 without blocking review cycles.",
     None),
    ("2026-04-19T18:05:00+00:00", "DECISION", "—",
     "Q-HH-1: Redis same-server initially — lowest-friction start, scale-out "
     "deferred until QPS > 5k or RAM pressure.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:06:00+00:00", "DECISION", "—",
     "Q-HH-2: 48h retention + AOF everysec — covers 24h canary windows + "
     "1 day replay; AOF bounds data loss to <1s.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:07:00+00:00", "DECISION", "—",
     "Q-HH-3: Docker Compose single-host — matches Redis \"same server\" "
     "choice; multi-host prep deferred to B13+.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:08:00+00:00", "DECISION", "B9",
     "Q-HH-4: W1 enforcement at DB level (REVOKE UPDATE on origin table) — "
     "stronger than application-level guard.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:09:00+00:00", "DECISION", "C2",
     "Q-HH-5: Confidence routing = soft flag in Phase B, hard reject in "
     "Phase C — Phase C has 30d KPI history to set thresholds safely.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:10:00+00:00", "DECISION", "—",
     "Q-HH-6: Phase D gate = Hermes + 2-council (OinkV + GUARDIAN) — "
     "mirrors A10 council pattern (OinkV + OinkDB) which already shipped.",
     "../phases/heavy-hybrid.md"),
    ("2026-04-19T18:24:00+00:00", "AUTHORITY", "A10",
     "Mike approves A10 council-gated merge after OinkV + OinkDB co-sign "
     "via GH Issue #136.",
     "../tasks/A10-database-merge.md"),
]


def _event_desc_merged(task_id: str, marker: Path) -> str:
    txt = safe_read(marker, limit=3000)
    prs = parse_merged_marker(txt).get("prs") or []
    if prs:
        p = prs[0]
        repo = p.get("repo") or TASK_REPO_HINT.get(task_id, "repo")
        num = p.get("number")
        sha = (p.get("merge_commit") or "")[:7]
        return (f"Merged to `{repo}` via PR #{num}"
                f"{f' (@{sha})' if sha else ''}.")
    return f"Merge marker published for {task_id}."


def _event_desc_review(task_id: str, agent: str, path: Path) -> str:
    txt = safe_read(path, limit=4000)
    score = extract_score(txt)
    verdict = extract_verdict(txt) or "verdict"
    phase = ("Phase 0" if "PHASE0" in path.name.upper()
             else "Phase 1" if "PHASE1" in path.name.upper()
             else "review")
    rn = ""
    rm = re.search(r"-R(\d+)-", path.name)
    if rm:
        rn = f" R{rm.group(1)}"
    if score is not None:
        return (f"{agent} {phase}{rn} {verdict} — "
                f"**{score:.2f}/10** on `{task_id}`.")
    return f"{agent} {phase}{rn} {verdict} on `{task_id}`."


def _event_desc_hermes(task_id: str, path: Path) -> str:
    v = extract_verdict(safe_read(path, limit=4000)) or "LGTM"
    rn = ""
    rm = re.search(r"-R(\d+)\.md$", path.name)
    if rm:
        rn = f" R{rm.group(1)}"
    return f"Hermes parallel review{rn} — **{v}** on `{task_id}`."


def _event_desc_canary(task_id: str, path: Path) -> str:
    v = extract_canary_verdict(safe_read(path)) or "PENDING"
    return f"GUARDIAN canary {v} on `{task_id}` (first 10 signals post-deploy)."


def _collect_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Gather every significant sprint event as a flat list of dicts."""
    events: list[dict[str, Any]] = []
    by_id = {t["id"]: t for t in data["tasks"]}

    for tid in TASKS:
        t = by_id.get(tid)
        if not t: continue
        art = {k: Path(v) for k, v in t.get("artifacts", {}).items()}

        # Plan
        if "forge_plan" in art:
            p = art["forge_plan"]
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "PLAN_PUBLISHED", "task": tid,
                "desc": f"FORGE plan published — {TASK_NAMES.get(tid, tid)}.",
                "link": _raw_link("forge/plans", p.name),
            })

        # OinkV audit
        audit = _find_oinkv_audit(tid)
        if audit:
            events.append({
                "ts": iso(safe_mtime(audit)) or "",
                "type": "AUDIT_COMPLETE", "task": tid,
                "desc": f"OinkV audit published for `{tid}` plan.",
                "link": _raw_link("forge/plans", audit.name),
            })

        # Proposal
        if "proposal" in art:
            p = art["proposal"]
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "PROPOSAL_DRAFTED", "task": tid,
                "desc": f"ANVIL Phase 0 proposal drafted for `{tid}`.",
                "link": _raw_link("anvil/proposals", p.name),
            })

        # VIGIL reviews (phase 0 + all phase 1 rounds)
        vigil_paths: list[Path] = []
        if "vigil_phase0" in art: vigil_paths.append(art["vigil_phase0"])
        if "vigil_phase1" in art: vigil_paths.append(art["vigil_phase1"])
        for rn in (1, 2, 3):
            rp = VIGIL / "reviews" / f"{tid}-VIGIL-PHASE1-R{rn}-REVIEW.md"
            if rp.exists() and rp not in vigil_paths:
                vigil_paths.append(rp)
        for p in vigil_paths:
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "VIGIL_VERDICT", "task": tid,
                "desc": _event_desc_review(tid, "VIGIL", p),
                "link": _raw_link("vigil/reviews", p.name),
            })

        # GUARDIAN reviews (all rounds)
        guardian_paths: list[Path] = []
        for rf in _find_review_revisions(GUARDIAN / "reviews", tid, "0", "GUARDIAN"):
            guardian_paths.append(rf)
        if "guardian_phase1" in art:
            guardian_paths.append(art["guardian_phase1"])
        for p in guardian_paths:
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "GUARDIAN_VERDICT", "task": tid,
                "desc": _event_desc_review(tid, "GUARDIAN", p),
                "link": _raw_link("guardian/reviews", p.name),
            })

        # Hermes reviews (including -R2 etc.)
        hermes_paths: list[Path] = []
        if "hermes" in art: hermes_paths.append(art["hermes"])
        for p in HERMES_WS.glob(f"{tid}-HERMES-REVIEW-R*.md"):
            if p not in hermes_paths: hermes_paths.append(p)
        for p in hermes_paths:
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "HERMES_REVIEW", "task": tid,
                "desc": _event_desc_hermes(tid, p),
                "link": _raw_link("hermes", p.name),
            })

        # Merged
        if "merged" in art:
            p = art["merged"]
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": "MERGED", "task": tid,
                "desc": _event_desc_merged(tid, p),
                "link": _raw_link("anvil/markers", p.name),
            })

        # Canary
        if "canary" in art:
            p = art["canary"]
            verdict = t.get("canary", {}).get("verdict") or "PENDING"
            ev_type = (f"CANARY_{verdict}" if verdict in
                       ("PASS", "FAIL", "PENDING") else "CANARY_PENDING")
            events.append({
                "ts": iso(safe_mtime(p)) or "",
                "type": ev_type, "task": tid,
                "desc": _event_desc_canary(tid, p),
                "link": _raw_link("guardian/canary-reports", p.name),
            })

    # Curated (Decision / Authority) events
    for ts, ev_type, task_id, desc, link in CURATED_EVENTS:
        events.append({
            "ts": ts, "type": ev_type, "task": task_id,
            "desc": desc, "link": link,
        })

    # Drop any event missing ts — sort descending
    events = [e for e in events if e.get("ts")]
    events.sort(key=lambda e: e["ts"], reverse=True)
    return events


def _event_row(e: dict[str, Any]) -> str:
    meta = EVENT_META.get(e["type"], {"emoji": "•", "actor": "—"})
    try:
        dt = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
        hhmm = dt.astimezone(CEST).strftime("%H:%M CEST")
    except Exception:
        hhmm = "—"
    tid = e.get("task") or "—"
    link_md = (f" [artifact]({e['link']})" if e.get("link") else "")
    return (f"### {hhmm} — {meta['emoji']} {e['type']} "
            f"{tid} · {meta['actor']}\n\n{e['desc']}{link_md}\n")


def _render_event_day(day_iso: str, events: list[dict[str, Any]]) -> str:
    day_dt = datetime.fromisoformat(day_iso + "T00:00:00+00:00")
    pretty = day_dt.astimezone(CEST).strftime("%A, %d %b %Y")
    L = [f"# Sprint Events — {pretty}\n",
         f"**Date (CEST):** {pretty}  ",
         f"**Events:** {len(events)}  ",
         "**Sort order:** newest first\n",
         "---\n"]
    L.extend(_event_row(e) for e in events)
    L += ["\n---\n",
          "*[Event index](README.md) · [Sprint log index](../README.md) · "
          "[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"


def _render_event_readme(events_by_day: dict[str, list[dict[str, Any]]]) -> str:
    L = ["# Sprint Event Log\n",
         "Append-only chronological feed of every significant event in the "
         "OinkFarm Implementation Foresight Sprint. Events are parsed from "
         "agent artifact mtimes + content, augmented by curated decision "
         "markers. Newest first within each day.\n",
         "## Daily digests\n",
         "| Date | Events | File |", "|---|---|---|"]
    for day in sorted(events_by_day.keys(), reverse=True):
        evs = events_by_day[day]
        L.append(f"| {day} | {len(evs)} | [{day}.md]({day}.md) |")
    L += ["", "## Event types\n",
          "| Emoji | Type | Who |", "|---|---|---|"]
    for t, meta in EVENT_META.items():
        L.append(f"| {meta['emoji']} | {t} | {meta['actor']} |")
    L += ["", "---", "",
          "*[Sprint log index](../README.md) · [Live dashboard]"
          "(https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"


# ---- Updated index + emitter -------------------------------------------------

def _render_sprint_log_readme(data: dict[str, Any]) -> str:
    by_id = {t["id"]: t for t in data["tasks"]}
    total_merged = sum(1 for t in data["tasks"] if t["status"] == "DONE")
    integ = data.get("events_integrity", {})
    live = data.get("live_buckets", {"1h": [], "4h": [], "24h": []})
    decs = data.get("open_decisions", [])
    gaps = data.get("lint_gaps", [])
    fresh = data.get("freshness_by_agent", [])

    L = [
        "# OinkFarm Implementation Foresight Sprint — Archive\n",
        "Human-readable per-task, per-wave, per-phase, and per-event archive. "
        "For verbatim agent artifacts see [`../raw-artifacts/`](../raw-artifacts/). "
        "For the live dashboard see "
        "[quantisdevelopment.github.io/oinkfarm-sprint-checkpoint]"
        "(https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).\n",
    ]

    if data.get("bootstrap"):
        L.append("> ⚠️ **BOOTSTRAPPING FROM CRAWLER** — events.jsonl has "
                 f"{integ.get('total', 0)} events (<{MIN_EVENTS_FOR_PRIMARY}). "
                 "This archive is sourced from workspace file mtimes.\n")

    # Events integrity
    L += ["## Event stream integrity\n",
          f"- **Total events:** {integ.get('total', 0)}",
          f"- **Last 24h:** {integ.get('last_24h', 0)} "
          f"(rate {integ.get('rate_per_hour', 0)}/h)",
          f"- **Schema:** v{integ.get('schema_version', '?')}",
          f"- **Source:** {integ.get('source', '?')}",
          f"- **Monotonic:** {'✓ ok' if integ.get('monotonic_ok') else '⚠ gaps'}",
          ""]

    # ★ MIKE SPEC SECTION 1 — Live now
    L += ["## 🔴 Live now\n"]
    for label, key in [("Last 1 hour", "1h"), ("Last 4 hours", "4h"), ("Last 24 hours", "24h")]:
        L.append(f"### {label} ({len(live.get(key, []))} events)")
        evs = live.get(key, [])[:15]
        if evs:
            L += ["| Time | Type | Task | Agent | Summary |",
                  "|---|---|---|---|---|"]
            for e in evs:
                L.append(f"| {_tstime_filter(e.get('ts'))} | `{e.get('event_type')}` | "
                         f"`{e.get('task_id') or '—'}` | {e.get('agent') or '—'} | "
                         f"{e.get('summary', '')} |")
        else:
            L.append("_(no events)_")
        L.append("")

    # ★ MIKE SPEC SECTION 2 — Needs Mike
    L += ["## 🧭 Needs Mike\n"]
    if decs:
        L += ["| Question ID | Question | Task | Age | Options | Gate |",
              "|---|---|---|---|---|---|"]
        for d in decs:
            opts = " · ".join(d.get("options") or []) or "—"
            L.append(f"| `{d['question_id']}` | {d['question']} | "
                     f"`{d.get('task_id') or '—'}` | {d['age_human']} | {opts} | "
                     f"{d.get('gate_type', '—')} |")
    else:
        L.append("_No open DECISION_NEEDED events._")
    L.append("")

    # ★ MIKE SPEC SECTION 3 — Missing evidence
    L += ["## 🔍 Missing evidence\n"]
    if gaps:
        L += ["| Severity | Task | Issue |", "|---|---|---|"]
        for g in gaps:
            sev_emoji = {
                "critical": "🔴", "warn": "🟠", "mike": "🧭", "info": "⚪",
            }.get(g.get("severity", "info"), "•")
            L.append(f"| {sev_emoji} {g.get('severity', 'info').upper()} | "
                     f"`{g.get('task_id') or '—'}` | {g.get('issue', '')} |")
    else:
        L.append("_✓ No lint gaps._")
    L.append("")

    # ★ MIKE SPEC SECTION 4 — Freshness by agent
    L += ["## 🫀 Freshness by agent\n",
          "| Agent | Last event | Type | Task | Staleness | Events |",
          "|---|---|---|---|---|---|"]
    for a in fresh:
        light = a.get("light", "red")
        badge = ({"green": "🟢 fresh", "yellow": "🟡 1–3h", "red": "🔴 stale"}
                 .get(light, "•"))
        L.append(f"| {a.get('emoji', '•')} **{a.get('name', a.get('id'))}** | "
                 f"{_tstime_filter(a.get('last_event_ts'))} | "
                 f"`{a.get('last_event_type') or '—'}` | "
                 f"`{a.get('current_task') or a.get('last_task_id') or '—'}` | "
                 f"{badge} | {a.get('event_count', 0)} |")
    L.append("")

    L += [
        "## What's live now\n",
        "| | |", "|---|---|",
        f"| **Phase A** | ✅ COMPLETE — 11/11 tasks shipped, canaries PASS |",
        f"| **Phase B** | 🚧 IN FLIGHT — B1 proposal drafted |",
        f"| **Phase C** | 📐 SCOPED — 7 tasks, detailed plans after Phase B |",
        f"| **Heavy Hybrid** | 🗺️ ROADMAP DELIVERED — Q-HH-1..6 resolved autonomously |",
        f"| **Prod DB** | 1,407 signals · 0 NULL invariants · 0 orphans · 10 PRs merged |",
        "\n## Phases\n",
        "| Phase | Focus | Page |",
        "|---|---|---|",
        "| [Phase A](phases/phase-a.md) | Data Truth — 11 tasks, complete retrospective | ✅ DONE |",
        "| [Phase B](phases/phase-b.md) | Infrastructure — PostgreSQL + decomposed services | 🚧 IN FLIGHT |",
        "| [Phase C](phases/phase-c.md) | Observability — 55+ KPIs, anomaly detection | 📐 SCOPED |",
        "| [Heavy Hybrid](phases/heavy-hybrid.md) | Long-horizon roadmap + Q-HH decisions | 🗺️ DELIVERED |",
        "\n## Waves\n",
        "| Wave | Focus | Tasks | Status |", "|---|---|---|---|",
    ]
    for wid in WAVE_ORDER:
        wave_tids = WAVE_TASKS[wid]
        wave_tasks_done = sum(1 for tid in wave_tids
                              if by_id.get(tid, {}).get("status") == "DONE")
        label = _wave_label(wid)
        task_ids = " · ".join(
            f"[{tid}](tasks/{tid}-{TASK_SLUGS.get(tid, tid.lower())}.md)"
            for tid in wave_tids)
        focus_short = WAVE_FOCUS.get(wid, "—").split("—")[0].strip()
        status = (f"{wave_tasks_done}/{len(wave_tids)} shipped"
                  if wid != "B1" else "🚧 IN FLIGHT")
        L.append(f"| [{label}](waves/{_wave_slug(wid)}.md) | "
                 f"{focus_short} | {task_ids} | {status} |")

    L += ["\n## Tasks\n",
          "| Task | Name | Tier | Wave | Status | Canary |",
          "|---|---|---|---|---|---|"]
    for tid in sorted(by_id.keys(),
                      key=lambda t: (t[0], int(re.search(r"\d+", t).group()) if re.search(r"\d+", t) else 0)):
        t = by_id.get(tid)
        if not t:
            continue
        slug = TASK_SLUGS.get(tid, tid.lower())
        task_link = (f"[{tid}](tasks/{tid}-{slug}.md)"
                     if tid in TASK_SLUGS else f"`{tid}`")
        L.append(f"| {task_link} | "
                 f"{TASK_NAMES.get(tid, tid)} | "
                 f"{t['tier_emoji']} {t['tier']} | "
                 f"{TASK_WAVE.get(tid, '—')} | "
                 f"{STATUS_BADGE.get(t['status'], t['status'])} | "
                 f"{t['canary']['verdict'] or '—'} |")

    L += ["\n## Event log\n",
          "- [Event index](events/README.md) — chronological feed (newest "
          "first within each day)",
          "",
          "## Agents", "", "| Emoji | Name | Role |", "|---|---|---|"]
    for a in data["agents"]:
        L.append(f"| {a.get('emoji', '•')} | {a.get('name', '?')} | {a.get('role', '')} |")
    L += ["", "## Conventions", "",
          "- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT "
          "(per Arbiter-Oink Phase 4 governance)",
          "- **Auto-escalation:** if a diff touches one of the 7 Financial "
          "Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.",
          "- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → "
          "CODE → PR_REVIEW → CANARY → DONE",
          "- **Timestamps** are rendered in CEST (UTC+2).",
          "", "---", "",
          f"*{total_merged}/{len(data['tasks'])} tasks DONE · "
          f"Last auto-regenerated: "
          f"{datetime.now(timezone.utc).astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}"
          f" · [Live dashboard](https://quantisdevelopment.github.io/"
          f"oinkfarm-sprint-checkpoint/) · "
          f"[GitHub repo](https://github.com/QuantisDevelopment/"
          f"oinkfarm-sprint-checkpoint)*"]
    return "\n".join(L) + "\n"


def emit_sprint_log(data: dict[str, Any]) -> dict[str, int]:
    # Preserve top-level Scribe-maintained markdown files across regen.
    # These are hand-written / Scribe-produced docs that the generator
    # references (Mission, glossary, narrative templates) but does not own.
    preserved: dict[str, bytes] = {}
    if SPRINT_LOG.exists():
        for p in SPRINT_LOG.iterdir():
            if p.is_file() and p.suffix.lower() == ".md" and p.name != "README.md":
                try:
                    preserved[p.name] = p.read_bytes()
                except Exception:
                    pass
        shutil.rmtree(SPRINT_LOG)
    (SPRINT_LOG / "tasks").mkdir(parents=True, exist_ok=True)
    (SPRINT_LOG / "waves").mkdir(parents=True, exist_ok=True)
    (SPRINT_LOG / "phases").mkdir(parents=True, exist_ok=True)
    (SPRINT_LOG / "events").mkdir(parents=True, exist_ok=True)
    # Restore Scribe-maintained top-level markdown files
    for name, body in preserved.items():
        try:
            (SPRINT_LOG / name).write_bytes(body)
        except Exception:
            pass
    counts = {"tasks": 0, "waves": 0, "phases": 0, "event_days": 0}
    by_id = {t["id"]: t for t in data["tasks"]}

    # Task pages — ALL 12
    for tid, slug in TASK_SLUGS.items():
        t = by_id.get(tid)
        if not t: continue
        (SPRINT_LOG / "tasks" / f"{tid}-{slug}.md").write_text(
            _render_task_page(t), encoding="utf-8")
        counts["tasks"] += 1

    # Wave pages — 1, 2, 3, 4, B1
    for wid in WAVE_ORDER:
        wt = [by_id[tid] for tid in WAVE_TASKS[wid] if tid in by_id]
        (SPRINT_LOG / "waves" / f"{_wave_slug(wid)}.md").write_text(
            _render_wave_page(wid, wt), encoding="utf-8")
        counts["waves"] += 1

    # Phase pages
    (SPRINT_LOG / "phases" / "phase-a.md").write_text(
        _render_phase_a(data), encoding="utf-8")
    (SPRINT_LOG / "phases" / "phase-b.md").write_text(
        _render_phase_b(data), encoding="utf-8")
    (SPRINT_LOG / "phases" / "phase-c.md").write_text(
        _render_phase_c(data), encoding="utf-8")
    (SPRINT_LOG / "phases" / "heavy-hybrid.md").write_text(
        _render_heavy_hybrid(data), encoding="utf-8")
    counts["phases"] = 4

    # Event log — group by CEST day. Prefer the stream events when available.
    if data.get("_from_stream") and data.get("_events_all_stream"):
        # Map stream events into the shape _render_event_day expects
        stream_evs = data["_events_all_stream"]
        events = []
        for e in stream_evs:
            et = e.get("event_type", "")
            # Map schema event_types → legacy event emoji keys
            legacy_type = {
                "TASK_PLANNED": "PLAN_PUBLISHED",
                "PROPOSAL_READY": "PROPOSAL_DRAFTED",
                "PROPOSAL_APPROVED": "PROPOSAL_DRAFTED",
                "PROPOSAL_REJECTED": "PROPOSAL_DRAFTED",
                "REVIEW_POSTED": (
                    "VIGIL_VERDICT" if (e.get("extra") or {}).get("reviewer") == "vigil"
                    else "GUARDIAN_VERDICT" if (e.get("extra") or {}).get("reviewer") == "guardian"
                    else "HERMES_REVIEW"
                ),
                "MERGED": "MERGED",
                "CANARY_PASS": "CANARY_PASS",
                "CANARY_FAIL": "CANARY_FAIL",
                "CANARY_STARTED": "CANARY_PENDING",
                "DECISION_NEEDED": "DECISION",
                "DECISION_RESOLVED": "DECISION",
            }.get(et, et)
            events.append({
                "ts": e.get("ts"),
                "type": legacy_type,
                "task": e.get("task_id") or "—",
                "desc": _one_line_summary(e),
                "link": e.get("artifact_path"),
            })
    else:
        events = _collect_events(data)
    by_day: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        try:
            dt = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            day = dt.astimezone(CEST).strftime("%Y-%m-%d")
            by_day.setdefault(day, []).append(e)
        except Exception:
            continue
    for day, evs in by_day.items():
        (SPRINT_LOG / "events" / f"{day}.md").write_text(
            _render_event_day(day, evs), encoding="utf-8")
        counts["event_days"] += 1
    (SPRINT_LOG / "events" / "README.md").write_text(
        _render_event_readme(by_day), encoding="utf-8")

    # Top-level README
    (SPRINT_LOG / "README.md").write_text(
        _render_sprint_log_readme(data), encoding="utf-8")

    # Store for dashboard hydration
    data["_events_all"] = events
    return counts

def _inject_archive_link_in_footer() -> None:
    """Add a subtle 'Full sprint archive' link in docs/index.html footer."""
    idx = SITE / "index.html"
    if not idx.exists(): return
    html = idx.read_text(encoding="utf-8")
    if 'id="sprint-archive-link"' in html:
        return
    inject = (
        '    <div id="sprint-archive-link">\n'
        '      📂 <a href="https://github.com/QuantisDevelopment/'
        'oinkfarm-sprint-checkpoint/tree/main/sprint-log" '
        'target="_blank" rel="noopener">Full sprint archive →</a>\n'
        '    </div>\n  </div>\n</footer>'
    )
    html = html.replace("  </div>\n</footer>", inject, 1)
    idx.write_text(html, encoding="utf-8")

def main() -> int:
    data = build()
    # Emit raw artifacts and sprint-log first so we can populate recent_events
    # into data.json before write_site serializes it.
    raw_counts = emit_raw_artifacts(data)
    log_counts = emit_sprint_log(data)
    # Surface the 20 most-recent events for dashboard hydration
    events = data.pop("_events_all", [])
    data["recent_events"] = [
        {**e, "emoji": EVENT_META.get(e["type"], {}).get("emoji", "•"),
         "actor": EVENT_META.get(e["type"], {}).get("actor", "—")}
        for e in events[:20]
    ]
    html = render(data)
    write_site(data, html)
    _inject_archive_link_in_footer()
    sys.stdout.write(
        f"OK  generated {SITE}/index.html  "
        f"({len(data['tasks'])} tasks, {len(data['agents'])} agents, "
        f"{len(data['blockers'])} blockers, {len(data['cron'])} cron events)\n"
        f"OK  raw-artifacts ({sum(raw_counts.values())} files across "
        f"{len(raw_counts)} subdirs)\n"
        f"OK  sprint-log ({log_counts['tasks']} task pages, "
        f"{log_counts['waves']} wave pages, {log_counts['phases']} phase "
        f"pages, {log_counts['event_days']} event-day pages + README)\n"
        f"OK  recent_events populated ({len(data['recent_events'])} of "
        f"{len(events)} total)\n"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
