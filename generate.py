#!/usr/bin/env python3
"""OinkFarm Implementation Foresight Sprint — checkpoint dashboard generator.

Crawls live agent workspaces (FORGE / ANVIL / VIGIL / GUARDIAN / Hermes / OinkV)
and emits a static dashboard (HTML + JSON) under ./site/.

Read-only outside ./site/. Missing files are treated as "not yet"; never raises.
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
SITE, STATIC, TEMPLATES = ROOT / "site", ROOT / "static", ROOT / "templates"

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
        if pn and rm:
            repo, num = rm.group(1), int(pn.group(1))
            pr = {
                "repo": repo, "number": num,
                "pr_url": f"https://github.com/QuantisDevelopment/{repo}/pull/{num}",
                "merge_commit": cm.group(1) if cm else None,
                "commit_url": None,
            }
            if pr["merge_commit"]:
                pr["commit_url"] = (
                    f"https://github.com/QuantisDevelopment/{repo}/commit/{pr['merge_commit']}"
                )
            result["prs"].append(pr)
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


def main() -> int:
    data = build()
    html = render(data)
    write_site(data, html)
    sys.stdout.write(
        f"OK  generated {SITE}/index.html  "
        f"({len(data['tasks'])} tasks, {len(data['agents'])} agents, "
        f"{len(data['blockers'])} blockers, {len(data['cron'])} cron events)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
