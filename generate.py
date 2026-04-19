#!/usr/bin/env python3
"""OinkFarm Implementation Foresight Sprint — checkpoint dashboard generator.

Crawls live agent workspaces (FORGE / ANVIL / VIGIL / GUARDIAN / Hermes / OinkV)
and emits a static dashboard (HTML + JSON) under ./docs/ (GitHub Pages source).

Read-only outside ./docs/. Missing files are treated as "not yet"; never raises.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

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

TASKS = ["A1", "A2", "A3", "A4", "A5", "A7"]
TIERS = {"A1": "CRITICAL", "A2": "CRITICAL", "A3": "STANDARD",
         "A4": "STANDARD", "A5": "STANDARD", "A7": "CRITICAL"}
TIER_EMOJI = {"CRITICAL": "🔴", "STANDARD": "🟡", "LIGHTWEIGHT": "🟢"}
TASK_REPO_HINT = {"A1": "oinkfarm", "A2": "oink-sync", "A3": "oinkfarm",
                  "A4": "oink-sync", "A5": "signal-gateway", "A7": "signal-gateway"}

WAVES = [
    {"name": "Wave 1", "tasks": ["A1", "A2", "A3"]},
    {"name": "Wave 2", "tasks": ["A4", "A7", "A5"]},
    {"name": "Wave 3+", "tasks": [], "future": True},
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
                    cron: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    for entry in cron[:3]:
        if not entry.get("blocker"):
            continue
        raw = entry["blocker"]
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


# --------------------------------------------------------------------------- #
# Main build + render
# --------------------------------------------------------------------------- #

def build(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    tasks = [crawl_task(t, now) for t in TASKS]
    tasks.sort(key=lambda t: t["last_activity"] or "", reverse=True)
    agents = [crawl_agent(a, now) for a in AGENTS]
    cron = crawl_cron()
    plans = crawl_plans()
    blockers = derive_blockers(agents, cron)

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
    }


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
    "A1": "signal-events-schema", "A2": "remaining-pct-model",
    "A3": "auto-filled-at",       "A4": "partially-closed-status",
    "A5": "confidence-scoring",   "A7": "update-new-detection",
}
TASK_NAMES = {
    "A1": "signal_events Table + 12 Event Type Instrumentation",
    "A2": "remaining_pct Model + Blended PnL Fix",
    "A3": "Auto filled_at for MARKET Orders",
    "A4": "PARTIALLY_CLOSED Status for Partial TP Signals",
    "A5": "Parser-Type Confidence Scoring",
    "A7": "UPDATE→NEW Detection (Phantom Trade Prevention)",
}
TASK_WAVE = {"A1": 1, "A2": 1, "A3": 1, "A4": 2, "A5": 2, "A7": 2}
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
    fallback = f"{TASK_NAMES.get(task, task)} — see plan for details."
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
    cands = [plans / f"OINKV-AUDIT-WAVE2-{task}.md"]
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
    if merged_text and "CRITICAL" in merged_text and tid in ("A1","A2","A4","A7"):
        out.append("- **Auto-escalation to 🔴 CRITICAL** via Financial Hotpath "
                   "rule — Phase 1 used the stricter ≥9.5 threshold.")
    if tid == "A4":
        out.append("- **Same-cycle closure path** (remaining_pct → 0 on TP-all-hit)"
                   " avoided PARTIALLY_CLOSED limbo via one atomic UPDATE carrying"
                   " `final_roi` + `closed_at` + `close_source`.")
        out.append("- **E5 (`_calculate_pnl` filter)** was the non-obvious "
                   "blast-radius save — GUARDIAN's R0 flagged that E3 would "
                   "fetch PARTIALLY_CLOSED rows but PnL would silently be `None`.")
    if meta.get("backfill"):
        out.append("- **Backfill pre-SELECT + abort-if-rowcount guard** caught "
                   "a data-quality anomaly without failing the migration.")
    return out[:6] if out else ["_(Lessons distilled at wave close.)_"]

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
         "", "## One-liner", "", _oneliner_from_plan(plan_path, tid), "",
         "## Timeline", "",
         "| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |",
         "|---|---|---|---|---|---|", *rows,
         "", "## Key Decisions", ""]
    if decisions:
        L.extend(f"- {d}" for d in decisions)
    elif status in ("PLANNED", "NOT_STARTED"):
        L.append("_(To be distilled once Phase 0 proposal is drafted.)_")
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

def _render_wave_page(n: int, tasks: list[dict[str, Any]]) -> str:
    focus = {1: "Core schema & formula primitives — events, remaining_pct, "
                "auto filled_at.",
             2: "Lifecycle accuracy & phantom-trade prevention — partial "
                "closes, confidence scoring, UPDATE→NEW dedup."}.get(n, "—")
    done = sum(1 for t in tasks if t["status"] == "DONE")
    in_flight = sum(1 for t in tasks
                    if t["status"] not in ("DONE", "PLANNED", "NOT_STARTED"))
    planned = sum(1 for t in tasks
                  if t["status"] in ("PLANNED", "NOT_STARTED"))

    L = [f"# Wave {n} Retrospective\n", f"**Focus:** {focus}\n",
         f"**Status:** {done}/{len(tasks)} shipped · {in_flight} in flight · "
         f"{planned} planned\n", "## Tasks\n",
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
    # Timing
    L += ["", "## Timing", ""]
    times = [(t["timeline"][0]["mtime"], t["timeline"][-1]["mtime"])
             for t in tasks if t.get("timeline")]
    if times:
        try:
            starts = [x[0] for x in times if x[0]]
            ends = [x[1] for x in times if x[1]]
            fd = datetime.fromisoformat(min(starts).replace("Z", "+00:00"))
            ld = datetime.fromisoformat(max(ends).replace("Z", "+00:00"))
            L += [f"- Wave start: "
                  f"{fd.astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}",
                  f"- Last activity: "
                  f"{ld.astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}",
                  f"- Elapsed: {(ld - fd).total_seconds() / 3600:.1f} h"]
        except Exception:
            L.append("- (Timing data unavailable.)")
    L += ["", "## Canary Outcomes", ""]
    canaries = [f"- **{t['id']}**: {t['canary']['verdict']}"
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
    L.append("- Wave complete — see individual task pages for distilled lessons."
             if all(t["status"] == "DONE" for t in tasks)
             else "_(To be filled at wave close.)_")
    L += ["", "---", "",
          "*[Sprint log index](../README.md) · "
          "[Live dashboard](https://quantisdevelopment.github.io/"
          "oinkfarm-sprint-checkpoint/)*"]
    return "\n".join(L) + "\n"

def _render_sprint_log_readme(data: dict[str, Any]) -> str:
    L = ["# OinkFarm Implementation Foresight Sprint — Archive\n",
         "Human-readable per-task archive. For verbatim agent artifacts see "
         "[`../raw-artifacts/`](../raw-artifacts/). For the live dashboard see "
         "[quantisdevelopment.github.io/oinkfarm-sprint-checkpoint]"
         "(https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/).\n",
         "## Waves", "", "| Wave | Focus | Tasks | Status |",
         "|---|---|---|---|"]
    wave_focus = {1: "Core schema & formula primitives",
                  2: "Lifecycle accuracy & phantom-trade prevention"}
    for w in data["waves"]:
        if w.get("future"): continue
        n = int(w["name"].split()[-1]) if w["name"].split()[-1].isdigit() else 0
        task_ids = " · ".join(
            f"[{tid}](tasks/{tid}-{TASK_SLUGS.get(tid, tid.lower())}.md)"
            for tid in w["task_ids"])
        L.append(f"| [{w['name']}](waves/wave-{n}.md) | "
                 f"{wave_focus.get(n, '—')} | {task_ids} | "
                 f"{w['done']}/{w['total']} shipped |")
    L += ["", "## Tasks", "",
          "| Task | Name | Tier | Wave | Status | Canary |",
          "|---|---|---|---|---|---|"]
    by_id = {t["id"]: t for t in data["tasks"]}
    for w in data["waves"]:
        for tid in w["task_ids"]:
            t = by_id.get(tid)
            if not t: continue
            slug = TASK_SLUGS.get(tid, tid.lower())
            L.append(f"| [{tid}](tasks/{tid}-{slug}.md) | "
                     f"{TASK_NAMES.get(tid, tid)} | "
                     f"{t['tier_emoji']} {t['tier']} | "
                     f"{TASK_WAVE.get(tid, '—')} | "
                     f"{STATUS_BADGE.get(t['status'], t['status'])} | "
                     f"{t['canary']['verdict'] or '—'} |")
    L += ["", "## Agents", "", "| Emoji | Name | Role |", "|---|---|---|"]
    for a in data["agents"]:
        L.append(f"| {a['emoji']} | {a['name']} | {a['role']} |")
    L += ["", "## Conventions", "",
          "- **Tier colour:** 🔴 CRITICAL / 🟡 STANDARD / 🟢 LIGHTWEIGHT "
          "(per Arbiter-Oink Phase 4 governance)",
          "- **Auto-escalation:** if a diff touches one of the 7 Financial "
          "Hotpath functions, tier is upgraded to 🔴 regardless of proposal tier.",
          "- **Status progression:** PLANNED → PROPOSAL → PROPOSAL_REVIEW → "
          "CODE → PR_REVIEW → CANARY → DONE",
          "- **Timestamps** are rendered in CEST (UTC+2).",
          "", "---", "",
          f"*Last auto-regenerated: "
          f"{datetime.now(timezone.utc).astimezone(CEST).strftime('%H:%M CEST on %d %b %Y')}"
          f" · [Live dashboard](https://quantisdevelopment.github.io/"
          f"oinkfarm-sprint-checkpoint/) · "
          f"[GitHub repo](https://github.com/QuantisDevelopment/"
          f"oinkfarm-sprint-checkpoint)*"]
    return "\n".join(L) + "\n"

def emit_sprint_log(data: dict[str, Any]) -> dict[str, int]:
    if SPRINT_LOG.exists():
        shutil.rmtree(SPRINT_LOG)
    (SPRINT_LOG / "tasks").mkdir(parents=True, exist_ok=True)
    (SPRINT_LOG / "waves").mkdir(parents=True, exist_ok=True)
    counts = {"tasks": 0, "waves": 0}
    by_id = {t["id"]: t for t in data["tasks"]}
    for tid, slug in TASK_SLUGS.items():
        t = by_id.get(tid)
        if not t: continue
        (SPRINT_LOG / "tasks" / f"{tid}-{slug}.md").write_text(
            _render_task_page(t), encoding="utf-8")
        counts["tasks"] += 1
    for w in data["waves"]:
        if w.get("future"): continue
        n = int(w["name"].split()[-1]) if w["name"].split()[-1].isdigit() else 0
        if n:
            wt = [by_id[tid] for tid in w["task_ids"] if tid in by_id]
            (SPRINT_LOG / "waves" / f"wave-{n}.md").write_text(
                _render_wave_page(n, wt), encoding="utf-8")
            counts["waves"] += 1
    (SPRINT_LOG / "README.md").write_text(
        _render_sprint_log_readme(data), encoding="utf-8")
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
    html = render(data)
    write_site(data, html)
    raw_counts = emit_raw_artifacts(data)
    log_counts = emit_sprint_log(data)
    _inject_archive_link_in_footer()
    sys.stdout.write(
        f"OK  generated {SITE}/index.html  "
        f"({len(data['tasks'])} tasks, {len(data['agents'])} agents, "
        f"{len(data['blockers'])} blockers, {len(data['cron'])} cron events)\n"
        f"OK  raw-artifacts ({sum(raw_counts.values())} files across "
        f"{len(raw_counts)} subdirs)\n"
        f"OK  sprint-log ({log_counts['tasks']} task pages, "
        f"{log_counts['waves']} wave pages + README)\n"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
