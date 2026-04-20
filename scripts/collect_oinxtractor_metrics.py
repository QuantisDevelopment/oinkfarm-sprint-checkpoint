#!/usr/bin/env python3
"""
collect_oinxtractor_metrics.py — OinXtractor Quality metrics collector.

Standalone script that:
  1. Pulls 4 metric bundles (latency, unknown rate, accuracy, corrections memory)
  2. Writes docs/oinxtractor-metrics.json (consumed by the HTML page via fetch)
  3. Renders docs/oinxtractor-quality.html (self-contained static page)
  4. Emits an ARTIFACT_PUBLISHED event via lib/checkpoint_reporting

Designed to NEVER crash:
  - Any data source unreachable -> that bundle's status becomes "pending" or
    "error" with a human-readable message; page still renders cleanly.
  - All sources going PENDING is an expected pre-#171 state.

Deps: stdlib only (urllib). No external packages required.
"""

from __future__ import annotations

import json
import os
import re
import sys
import ssl
import urllib.request
import urllib.error
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Paths + lib wiring
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent       # sprint-checkpoint/
DOCS = ROOT / "docs"
JSON_OUT = DOCS / "oinxtractor-metrics.json"
HTML_OUT = DOCS / "oinxtractor-quality.html"

# Optional checkpoint-reporting lib for ARTIFACT_PUBLISHED event
_LIB = ROOT / "lib"
if _LIB.exists():
    sys.path.insert(0, str(_LIB))
try:
    from checkpoint_reporting import emit_event as _emit_event  # type: ignore
except Exception:
    _emit_event = None  # graceful

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

OINKDB_API = os.environ.get("OINKDB_API", "http://localhost:8888")
SUPERMEMORY_API_KEY = os.environ.get("SUPERMEMORY_API_KEY", "")
SUPERMEMORY_BASE = "https://api.supermemory.ai/v3"

BASELINE_MD = Path("/home/oinkv/guardian-workspace/kpi/extraction-accuracy-baseline.md")

UNKNOWN_SENTINEL_RE = re.compile(r"\[extracted:\s*([^\]]+)\]", re.I)

HTTP_TIMEOUT = 5.0

# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)

def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _parse_iso(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    try:
        txt = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def _percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    k = max(0, min(len(sorted_vals) - 1, int(round((p / 100.0) * (len(sorted_vals) - 1)))))
    return float(sorted_vals[k])

# --------------------------------------------------------------------------- #
# HTTP (stdlib only)
# --------------------------------------------------------------------------- #

def _http_json(url: str, *, method: str = "GET", headers: dict | None = None,
               data: dict | None = None, timeout: float = HTTP_TIMEOUT) -> dict | list | None:
    body = None
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except Exception:
        return None

# --------------------------------------------------------------------------- #
# Bundle 1 — Extraction latency
# --------------------------------------------------------------------------- #

def collect_latency() -> dict:
    """
    Strategy (best available today):
      - Pull recent signals from OinkDB API /signals/recent?hours=168.
      - Estimate "extraction landing latency" as (updated_at - posted_at) for
        each signal, where posted_at = Discord message ts and updated_at = last
        row touch (close-enough proxy for first-update / extraction landing).
      - Label source="estimated" so consumers know this is pre-#171 proxy data.

    If API unreachable or the signals table has no usable timestamps, fall back
    to status="pending" with a clear message.
    """
    url = f"{OINKDB_API}/signals/recent?hours=168"
    payload = _http_json(url)
    if not payload or not isinstance(payload, dict) or "items" not in payload:
        return {
            "status": "pending",
            "message": f"OinkDB API unreachable or unexpected schema at {url}",
            "p50_24h_sec": None, "p95_24h_sec": None,
            "p50_7d_sec": None, "p95_7d_sec": None,
            "series_24h": [], "series_7d": [],
            "source": "oinkdb_api",
        }

    items = payload.get("items") or []
    now = _utc_now()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    # hourly buckets (last 24h) and daily buckets (last 7d)
    hour_buckets: dict[str, list[float]] = defaultdict(list)
    day_buckets: dict[str, list[float]] = defaultdict(list)
    lat_24h: list[float] = []
    lat_7d: list[float] = []

    for s in items:
        posted = _parse_iso(s.get("posted_at"))
        updated = _parse_iso(s.get("updated_at"))
        if not posted or not updated:
            continue
        dt = (updated - posted).total_seconds()
        # Drop zeros and >24h (likely stale/reopened rows)
        if dt <= 0 or dt > 86400:
            continue

        if posted >= cutoff_7d:
            lat_7d.append(dt)
            day_key = posted.strftime("%Y-%m-%d")
            day_buckets[day_key].append(dt)
        if posted >= cutoff_24h:
            lat_24h.append(dt)
            hour_key = posted.strftime("%Y-%m-%dT%H:00Z")
            hour_buckets[hour_key].append(dt)

    def _summarise(vals: list[float]) -> tuple[float | None, float | None]:
        if not vals:
            return None, None
        v = sorted(vals)
        return _percentile(v, 50), _percentile(v, 95)

    p50_24h, p95_24h = _summarise(lat_24h)
    p50_7d, p95_7d = _summarise(lat_7d)

    series_24h = []
    for hr in sorted(hour_buckets.keys()):
        v = sorted(hour_buckets[hr])
        series_24h.append({"t": hr,
                           "p50": _percentile(v, 50),
                           "p95": _percentile(v, 95),
                           "n": len(v)})

    series_7d = []
    for day in sorted(day_buckets.keys()):
        v = sorted(day_buckets[day])
        series_7d.append({"t": day,
                          "p50": _percentile(v, 50),
                          "p95": _percentile(v, 95),
                          "n": len(v)})

    if not lat_7d:
        return {
            "status": "pending",
            "message": ("Signals endpoint reachable but no (posted_at, updated_at) "
                        "pairs in last 7d — will populate as #171 wiring lands."),
            "p50_24h_sec": None, "p95_24h_sec": None,
            "p50_7d_sec": None, "p95_7d_sec": None,
            "series_24h": [], "series_7d": [],
            "source": "oinkdb_api",
        }

    return {
        "status": "ok",
        "message": ("Proxy: (updated_at - posted_at) delta per signal — "
                    "best-available pre-#171 landing-latency estimator."),
        "p50_24h_sec": round(p50_24h, 1) if p50_24h is not None else None,
        "p95_24h_sec": round(p95_24h, 1) if p95_24h is not None else None,
        "p50_7d_sec":  round(p50_7d, 1)  if p50_7d  is not None else None,
        "p95_7d_sec":  round(p95_7d, 1)  if p95_7d  is not None else None,
        "series_24h": series_24h,
        "series_7d": series_7d,
        "source": "estimated",
        "sample_size_24h": len(lat_24h),
        "sample_size_7d": len(lat_7d),
    }

# --------------------------------------------------------------------------- #
# Bundle 2 — [extracted: unknown] rate
# --------------------------------------------------------------------------- #

def collect_unknown_rate() -> dict:
    url = f"{OINKDB_API}/signals/recent?hours=168"
    payload = _http_json(url)
    if not payload or not isinstance(payload, dict) or "items" not in payload:
        return {
            "status": "pending",
            "message": f"OinkDB API unreachable at {url}",
            "rate_24h_pct": None, "rate_7d_pct": None,
            "series_7d": [],
            "total_extractions_24h": 0,
            "unknown_count_24h": 0,
            "method_breakdown_24h": {},
            "note": "Target: <5% per Issue #116 acceptance",
        }

    items = payload.get("items") or []
    now = _utc_now()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    def _method(s: dict) -> str:
        notes = s.get("notes") or ""
        m = UNKNOWN_SENTINEL_RE.search(notes)
        if m:
            return m.group(1).strip().lower()
        return "(no_sentinel)"

    day_totals: dict[str, int] = defaultdict(int)
    day_unknowns: dict[str, int] = defaultdict(int)

    total_24h = 0
    unknown_24h = 0
    total_7d = 0
    unknown_7d = 0
    method_counts_24h: Counter = Counter()

    for s in items:
        posted = _parse_iso(s.get("posted_at"))
        if not posted:
            continue
        mth = _method(s)
        is_unknown = (mth == "unknown")

        if posted >= cutoff_7d:
            total_7d += 1
            day_key = posted.strftime("%Y-%m-%d")
            day_totals[day_key] += 1
            if is_unknown:
                unknown_7d += 1
                day_unknowns[day_key] += 1

        if posted >= cutoff_24h:
            total_24h += 1
            method_counts_24h[mth] += 1
            if is_unknown:
                unknown_24h += 1

    series_7d = []
    for day in sorted(day_totals.keys()):
        tot = day_totals[day]
        unk = day_unknowns[day]
        series_7d.append({
            "t": day,
            "pct": round(100.0 * unk / tot, 1) if tot else 0.0,
            "count": unk,
            "total": tot,
        })

    def _safe_pct(u: int, t: int) -> float | None:
        return round(100.0 * u / t, 1) if t else None

    status = "ok"
    message = "Live from OinkDB /signals/recent notes field sentinel."
    if total_7d == 0:
        status = "pending"
        message = "No signals landed in trailing 7d; rate cannot be computed."

    return {
        "status": status,
        "message": message,
        "rate_24h_pct": _safe_pct(unknown_24h, total_24h),
        "rate_7d_pct": _safe_pct(unknown_7d, total_7d),
        "series_7d": series_7d,
        "total_extractions_24h": total_24h,
        "unknown_count_24h": unknown_24h,
        "total_extractions_7d": total_7d,
        "unknown_count_7d": unknown_7d,
        "method_breakdown_24h": dict(method_counts_24h.most_common()),
        "note": "Target: <5% per Issue #116 acceptance",
    }

# --------------------------------------------------------------------------- #
# Bundle 3 — Accuracy by trader (proxy from baseline markdown)
# --------------------------------------------------------------------------- #

def collect_accuracy_by_trader() -> dict:
    """Parse GUARDIAN's proxy baseline markdown table — current best-available."""
    if not BASELINE_MD.exists():
        return {
            "status": "pending",
            "message": f"Baseline doc missing: {BASELINE_MD}",
            "baseline_reference": str(BASELINE_MD),
            "rows": [],
        }
    try:
        text = BASELINE_MD.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Failed to read baseline: {exc}",
            "baseline_reference": str(BASELINE_MD),
            "rows": [],
        }

    # Find the per-trader table
    lines = text.splitlines()
    rows: list[dict] = []
    in_table = False
    header_seen = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Per-trader proxy breakdown"):
            in_table = True
            continue
        if in_table and stripped.startswith("##"):
            break
        if not in_table:
            continue
        if not stripped.startswith("|"):
            continue
        # Skip the header + separator
        if "| Trader" in line and "candidate" in line:
            header_seen = True
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        if not header_seen:
            continue
        # Split the row (escape \| for names like "Monk \| pingu")
        # Replace "\|" -> sentinel, split, restore
        safe = line.replace(r"\|", "\u0001")
        parts = [p.replace("\u0001", "|").strip() for p in safe.strip("|").split("|")]
        if len(parts) < 4:
            continue
        trader = parts[0]
        try:
            samples = int(parts[1])
        except Exception:
            continue
        try:
            misreads = int(parts[2])
        except Exception:
            misreads = 0
        try:
            safe_noise = int(parts[3])
        except Exception:
            safe_noise = 0
        note = parts[4] if len(parts) >= 5 else ""

        # Proxy "accuracy" — (samples - misreads) / samples. Pre-#171 this is a
        # VERY rough indicator; per the baseline, true per-trader accuracy is
        # not yet instrumented.
        accuracy = 1.0 - (misreads / samples) if samples else None

        # Tier by sample size
        if samples >= 50:
            tier = "high_volume"
        elif samples >= 10:
            tier = "mid_volume"
        else:
            tier = "low_volume"

        rows.append({
            "trader": trader,
            "accuracy": round(accuracy, 4) if accuracy is not None else None,
            "samples": samples,
            "misreads": misreads,
            "safe_noise": safe_noise,
            "delta_vs_baseline": None,   # no historical anchor yet
            "tier": tier,
            "note": note,
        })

    if not rows:
        return {
            "status": "pending",
            "message": "Could not parse Per-trader table from baseline doc.",
            "baseline_reference": str(BASELINE_MD),
            "rows": [],
        }

    # Overall aggregate proxy — weighted by samples
    total_samples = sum(r["samples"] for r in rows)
    total_misreads = sum(r["misreads"] for r in rows)
    overall_accuracy = round(1.0 - (total_misreads / total_samples), 4) if total_samples else None

    return {
        "status": "proxy_only",
        "message": ("Proxy baseline from GUARDIAN sampled audits + candidate-volume "
                    "denominator. True per-trader weekly extraction accuracy is not "
                    "yet instrumented (pre-#171)."),
        "baseline_reference": str(BASELINE_MD),
        "rows": rows,
        "overall_accuracy_proxy": overall_accuracy,
        "overall_samples": total_samples,
        "overall_misreads": total_misreads,
    }

# --------------------------------------------------------------------------- #
# Bundle 4 — Correction memory (Supermemory)
# --------------------------------------------------------------------------- #

def _supermemory_total(container_tag: str) -> int | None:
    """
    Return total memories in the given container, or None on failure.

    Supermemory /v3/search requires a non-empty q; we use a broad token and
    take the reported `total`. This gives a conservative lower bound for the
    bucket size; acceptable as a dashboard widget.
    """
    if not SUPERMEMORY_API_KEY:
        return None
    url = f"{SUPERMEMORY_BASE}/search"
    headers = {"Authorization": f"Bearer {SUPERMEMORY_API_KEY}"}
    # Try a handful of broad queries; highest total wins (search is semantic,
    # so a single word may undercount). All containers we care about are small.
    best = 0
    hit = False
    for q in ("memory", "signal", "trade", "extraction", "correction"):
        payload = _http_json(url, method="POST", headers=headers,
                             data={"q": q, "limit": 1, "containerTags": [container_tag]})
        if not payload or "total" not in payload:
            continue
        hit = True
        try:
            t = int(payload.get("total") or 0)
            if t > best:
                best = t
        except Exception:
            pass
    return best if hit else None


def collect_correction_memory() -> dict:
    oinx_total = _supermemory_total("oinxtractor_corrections")
    barn_total = _supermemory_total("openclaw_barn")

    # Growth series placeholder — Supermemory API doesn't expose creation
    # histograms without extra bookkeeping. Leave empty series + note.
    growth: list[dict] = []

    if oinx_total is None and barn_total is None:
        return {
            "status": "pending",
            "message": ("Supermemory unreachable or SUPERMEMORY_API_KEY unset. "
                        "Widget will populate once correction-memory writes begin."),
            "oinxtractor_corrections_count": 0,
            "openclaw_barn_total": 0,
            "growth_series_7d": growth,
        }

    status = "ok"
    msg = "Live from Supermemory /v3/search (total field, best-effort upper bound)."
    if (oinx_total or 0) == 0:
        status = "pending"
        msg = ("Supermemory reachable but `oinxtractor_corrections` container is "
               "empty. Widget will populate as the correction-memory write path "
               "goes live.")

    return {
        "status": status,
        "message": msg,
        "oinxtractor_corrections_count": int(oinx_total or 0),
        "openclaw_barn_total": int(barn_total or 0),
        "growth_series_7d": growth,
    }

# --------------------------------------------------------------------------- #
# Bundle assembly + write
# --------------------------------------------------------------------------- #

def build_bundle() -> dict:
    out: dict[str, Any] = {
        "ts": _iso_z(_utc_now()),
        "generator": "sprint-checkpoint/scripts/collect_oinxtractor_metrics.py",
    }
    # Each collector is wrapped so one failure never breaks the bundle
    for name, fn in (
        ("latency", collect_latency),
        ("unknown_rate", collect_unknown_rate),
        ("accuracy_by_trader", collect_accuracy_by_trader),
        ("correction_memory", collect_correction_memory),
    ):
        try:
            out[name] = fn()
        except Exception as exc:
            out[name] = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}
    return out

# --------------------------------------------------------------------------- #
# HTML rendering (self-contained)
# --------------------------------------------------------------------------- #

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OinXtractor Quality — OinkFarm Sprint</title>
<meta name="description" content="Live quality metrics for the OinXtractor signal extraction pipeline.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  .oinx-wrap { max-width: 960px; margin: 0 auto; padding: 28px 24px 64px; }
  .oinx-head h1 { font-size: 1.6rem; letter-spacing: -0.01em; margin-bottom: 6px; }
  .oinx-head p.lede { color: var(--fg-muted); margin: 0 0 18px; font-size: 0.95rem; }
  .oinx-backlink { display:inline-block; color: var(--fg-muted); font-size: 0.82rem; margin-bottom: 14px; }
  .oinx-backlink:hover { color: var(--accent); }

  .oinx-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
  @media (max-width: 720px) { .oinx-grid { grid-template-columns: 1fr; } }

  .oinx-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px 14px;
    display: flex; flex-direction: column; gap: 10px;
    position: relative;
    transition: border-color 0.2s ease;
  }
  .oinx-card:hover { border-color: var(--border-hi); }
  .oinx-card.status-ok     { border-left: 3px solid var(--green); }
  .oinx-card.status-warn   { border-left: 3px solid var(--yellow); }
  .oinx-card.status-crit   { border-left: 3px solid var(--red); }
  .oinx-card.status-pending{ border-left: 3px solid var(--fg-dim); opacity: 0.78; }

  .oinx-card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
  .oinx-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.09em;
    color: var(--fg-muted); font-weight: 600;
  }
  .oinx-pill {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em;
    padding: 2px 8px; border-radius: 999px; font-weight: 600;
  }
  .pill-ok     { color: var(--green);  background: var(--green-soft);  border: 1px solid rgba(63,185,80,0.35); }
  .pill-warn   { color: var(--yellow); background: var(--yellow-soft); border: 1px solid rgba(210,153,34,0.35); }
  .pill-crit   { color: var(--red);    background: var(--red-soft);    border: 1px solid rgba(248,81,73,0.35); }
  .pill-pending{ color: var(--fg-muted); background: var(--bg-2); border: 1px solid var(--border); }

  .oinx-number {
    font-family: var(--font-mono); font-weight: 600; font-size: 2.4rem;
    line-height: 1.1; color: var(--fg); letter-spacing: -0.02em;
  }
  .oinx-number .unit { font-size: 1.1rem; color: var(--fg-muted); margin-left: 4px; }
  .oinx-number.muted { color: var(--fg-dim); }
  .oinx-subnum { font-family: var(--font-mono); font-size: 0.82rem; color: var(--fg-muted); }
  .oinx-explain { font-size: 0.86rem; color: var(--fg-muted); line-height: 1.5; margin: 0; }
  .oinx-threshold { font-size: 0.74rem; color: var(--fg-dim); font-family: var(--font-mono); }
  .oinx-spark { height: 64px; width: 100%; margin-top: 4px; }
  .oinx-awaiting { font-size: 0.82rem; color: var(--fg-dim); font-style: italic; }

  .oinx-details { margin-top: 28px; display: flex; flex-direction: column; gap: 14px; }
  .oinx-details details {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px 18px;
  }
  .oinx-details details[open] { border-color: var(--border-hi); }
  .oinx-details summary {
    cursor: pointer; font-weight: 600; font-size: 0.95rem;
    display: flex; justify-content: space-between; align-items: center; gap: 12px;
    list-style: none;
  }
  .oinx-details summary::-webkit-details-marker { display: none; }
  .oinx-details summary::after { content: "▸"; color: var(--fg-muted); transition: transform 0.2s; }
  .oinx-details details[open] summary::after { transform: rotate(90deg); }
  .oinx-details .detail-body { margin-top: 12px; font-size: 0.9rem; color: var(--fg); }
  .oinx-details .detail-body p { margin: 6px 0; color: var(--fg-muted); line-height: 1.55; }

  table.oinx-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
  table.oinx-table th, table.oinx-table td {
    text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border);
  }
  table.oinx-table th {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--fg-muted); font-weight: 600; cursor: pointer; user-select: none;
  }
  table.oinx-table th:hover { color: var(--fg); }
  table.oinx-table td.num { font-family: var(--font-mono); text-align: right; }
  table.oinx-table tr:hover td { background: var(--bg-hover); }
  .tier-high_volume { color: var(--green); font-size: 0.72rem; }
  .tier-mid_volume  { color: var(--yellow); font-size: 0.72rem; }
  .tier-low_volume  { color: var(--fg-dim); font-size: 0.72rem; }

  .oinx-footer {
    margin-top: 32px; padding-top: 18px; border-top: 1px solid var(--border);
    font-family: var(--font-mono); font-size: 0.78rem; color: var(--fg-muted);
    display: flex; gap: 16px; flex-wrap: wrap;
  }
  .oinx-footer a { color: var(--fg-muted); }
  .oinx-footer a:hover { color: var(--accent); }

  .kv { display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; font-size: 0.85rem; }
  .kv dt { color: var(--fg-muted); font-family: var(--font-mono); font-size: 0.78rem; }
  .kv dd { margin: 0; font-family: var(--font-mono); }

  .breakdown-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .breakdown-chips .chip { padding: 3px 8px; font-size: 0.78rem;
    background: var(--bg-2); border: 1px solid var(--border); border-radius: 999px; }
</style>
</head>
<body>

<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark">🔬</div>
      <div>
        <h1>OinXtractor Quality</h1>
        <p class="subtitle">Live quality metrics for the signal extraction pipeline — updated every 10 minutes.</p>
      </div>
    </div>
    <div class="clock">
      <div class="clock-row">
        <span class="clock-label">last refreshed</span>
        <span class="mono" id="last-refreshed">__TS_PRETTY__</span>
      </div>
      <div class="clock-row muted">
        <span class="clock-label">next refresh</span>
        <span class="mono">__NEXT_PRETTY__</span>
      </div>
    </div>
  </div>
  <nav class="topnav" role="navigation" aria-label="Primary">
    <div class="topnav-inner">
      <a class="navlink" href="index.html">← Dashboard</a>
      <a class="navlink navlink-active" href="oinxtractor-quality.html">OinXtractor Quality</a>
      <a class="navlink navlink-ghost" href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint" target="_blank" rel="noopener">GitHub ↗</a>
    </div>
  </nav>
</header>

<main class="oinx-wrap">

<section class="oinx-head">
  <h1>Extraction pipeline health</h1>
  <p class="lede">Four KPIs tracking how fast, how often, and how accurately the OinXtractor
    turns Discord trader posts into structured OinkDB rows. Click any card for detail.</p>
</section>

<section class="oinx-grid" id="oinx-cards">
  <!-- populated by render_js -->
</section>

<section class="oinx-details" id="oinx-details">
  <!-- populated by render_js -->
</section>

<footer class="oinx-footer">
  <div>Last refreshed: <span class="mono">__TS_PRETTY__</span></div>
  <div>·</div>
  <div>Next refresh: <span class="mono">__NEXT_PRETTY__</span></div>
  <div>·</div>
  <div>Source: <a href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint/blob/main/scripts/collect_oinxtractor_metrics.py" target="_blank" rel="noopener"><span class="mono">scripts/collect_oinxtractor_metrics.py</span></a></div>
</footer>

</main>

<script id="oinx-data" type="application/json">__JSON_PAYLOAD__</script>
<script>
(function(){
  const DATA = JSON.parse(document.getElementById('oinx-data').textContent);

  // Chart.js dark defaults
  if (window.Chart) {
    Chart.defaults.color = '#8892a6';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  }

  function fmtNum(n, unit, digits) {
    if (n === null || n === undefined || Number.isNaN(n)) return '—';
    const s = Number(n).toFixed(digits ?? 1);
    return unit ? `${s}<span class="unit">${unit}</span>` : s;
  }

  function statusPill(kind) {
    const map = {
      ok:      ['pill-ok',     'healthy'],
      warn:    ['pill-warn',   'warning'],
      crit:    ['pill-crit',   'critical'],
      pending: ['pill-pending','pending'],
      proxy:   ['pill-warn',   'proxy only'],
      error:   ['pill-crit',   'error'],
    };
    const [cls, label] = map[kind] || map.pending;
    return `<span class="oinx-pill ${cls}">${label}</span>`;
  }

  function classify(section, metric) {
    // Return one of: ok, warn, crit, pending
    if (!section) return 'pending';
    if (section.status === 'pending') return 'pending';
    if (section.status === 'error') return 'crit';
    if (metric.kind === 'latency_p50') {
      const v = section.p50_24h_sec;
      if (v === null || v === undefined) return 'pending';
      if (v < 60) return 'ok';
      if (v < 180) return 'warn';
      return 'crit';
    }
    if (metric.kind === 'unknown_rate') {
      const v = section.rate_24h_pct;
      if (v === null || v === undefined) return 'pending';
      if (v < 5) return 'ok';       // Issue #116 acceptance target
      if (v < 25) return 'warn';
      return 'crit';
    }
    if (metric.kind === 'accuracy') {
      if (section.status === 'proxy_only') return 'warn';
      const v = section.overall_accuracy_proxy;
      if (v === null || v === undefined) return 'pending';
      if (v >= 0.95) return 'ok';
      if (v >= 0.85) return 'warn';
      return 'crit';
    }
    if (metric.kind === 'corrections') {
      // Counts never fail — ok whenever the container has data
      if (section.oinxtractor_corrections_count > 0) return 'ok';
      return 'pending';
    }
    return 'pending';
  }

  function makeSpark(ctx, points, label, colour) {
    if (!points || points.length === 0) return null;
    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: points.map(p => p.t),
        datasets: [{
          label: label,
          data: points.map(p => p.v),
          borderColor: colour,
          backgroundColor: colour + '22',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 4,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false },
                   tooltip: { mode: 'index', intersect: false } },
        scales: {
          x: { display: false },
          y: { display: false, beginAtZero: true }
        },
        elements: { line: { borderJoinStyle: 'round' } }
      }
    });
  }

  // -------- Card: Latency --------
  const lat = DATA.latency || {};
  const latKind = classify(lat, {kind:'latency_p50'});
  const latPoints = (lat.series_24h || []).map(p => ({t: p.t, v: p.p50}));
  const latPrimary = lat.p50_24h_sec;
  const latIsPending = latKind === 'pending';

  // -------- Card: Unknown rate --------
  const unk = DATA.unknown_rate || {};
  const unkKind = classify(unk, {kind:'unknown_rate'});
  const unkPoints = (unk.series_7d || []).map(p => ({t: p.t, v: p.pct}));
  const unkPrimary = unk.rate_24h_pct;
  const unkIsPending = unkKind === 'pending';

  // -------- Card: Accuracy --------
  const acc = DATA.accuracy_by_trader || {};
  const accKind = classify(acc, {kind:'accuracy'});
  const accPrimary = acc.overall_accuracy_proxy ? (100 * acc.overall_accuracy_proxy) : null;
  const accIsPending = accKind === 'pending';

  // -------- Card: Corrections --------
  const corr = DATA.correction_memory || {};
  const corrKind = classify(corr, {kind:'corrections'});
  const corrPoints = (corr.growth_series_7d || []).map(p => ({t: p.t, v: p.count}));
  const corrPrimary = corr.oinxtractor_corrections_count;
  const corrIsPending = corrKind === 'pending';

  const cards = [
    {
      id: 'lat',
      label: '⏱ Extraction latency (p50, 24h)',
      number: latIsPending ? '—' : fmtNum(latPrimary, 's', 1),
      sub: latIsPending ? '' : `p95 ${fmtNum(lat.p95_24h_sec, 's', 1)} · n=${lat.sample_size_24h ?? 0}`,
      explain: 'Median seconds from Discord post to OinkDB row landing. Lower is better — fast extraction means traders can react before the market moves.',
      threshold: 'healthy < 60s · warn 60–180s · critical ≥ 180s',
      kind: latKind,
      points: latPoints,
      colour: '#ff6b35',
      pending: latIsPending,
      pendingMsg: lat.message,
    },
    {
      id: 'unk',
      label: '❓ [extracted: unknown] rate (24h)',
      number: unkIsPending ? '—' : fmtNum(unkPrimary, '%', 1),
      sub: unkIsPending ? '' : `${unk.unknown_count_24h}/${unk.total_extractions_24h} signals · 7d ${fmtNum(unk.rate_7d_pct, '%', 1)}`,
      explain: 'Share of signals whose extraction method is the "unknown" fallback sentinel. Target <5% per Issue #116 — today reflects pre-#171 baseline.',
      threshold: 'healthy < 5% · warn 5–25% · critical ≥ 25%',
      kind: unkKind,
      points: unkPoints,
      colour: '#d29922',
      pending: unkIsPending,
      pendingMsg: unk.message,
    },
    {
      id: 'acc',
      label: '🎯 Extraction accuracy (weekly proxy)',
      number: accIsPending ? '—' : fmtNum(accPrimary, '%', 1),
      sub: accIsPending ? '' : `${acc.overall_samples ?? 0} sampled signals · ${acc.overall_misreads ?? 0} misread${acc.overall_misreads === 1 ? '' : 's'}`,
      explain: 'Proxy accuracy from GUARDIAN sampled audits (1 − misreads/samples). Weekly per-trader true accuracy lands once #171 instrumentation is wired.',
      threshold: 'healthy ≥ 95% · warn 85–95% · critical < 85%',
      kind: accKind,
      points: [],
      colour: '#4f9bff',
      pending: accIsPending,
      pendingMsg: acc.message,
    },
    {
      id: 'corr',
      label: '📚 Correction memory',
      number: corrIsPending ? '0' : String(corrPrimary),
      sub: corrIsPending ? 'awaiting first corrections' : `barn library: ${corr.openclaw_barn_total ?? 0}`,
      explain: 'Count of correction memories the OinXtractor has absorbed (Supermemory container `oinxtractor_corrections`). Grows as Mike fixes misreads and the system learns.',
      threshold: 'grows with pipeline maturity',
      kind: corrKind,
      points: corrPoints,
      colour: '#b392f0',
      pending: corrIsPending,
      pendingMsg: corr.message,
    },
  ];

  // Render cards
  const grid = document.getElementById('oinx-cards');
  grid.innerHTML = cards.map(c => `
    <div class="oinx-card status-${c.kind}" id="card-${c.id}">
      <div class="oinx-card-head">
        <span class="oinx-label">${c.label}</span>
        ${statusPill(c.kind)}
      </div>
      <div class="oinx-number ${c.pending ? 'muted' : ''}">${c.number}</div>
      <div class="oinx-subnum">${c.sub || '&nbsp;'}</div>
      <p class="oinx-explain">${c.explain}</p>
      <div class="oinx-threshold">${c.threshold}</div>
      ${c.points && c.points.length
        ? `<canvas class="oinx-spark" id="spark-${c.id}"></canvas>`
        : (c.pending
            ? `<div class="oinx-awaiting">Awaiting data — ${escapeHtml(c.pendingMsg || 'collector will populate on next cycle.')}</div>`
            : `<div class="oinx-awaiting">(trend chart will appear once enough data points accumulate)</div>`)
      }
    </div>
  `).join('');

  // Draw sparklines
  cards.forEach(c => {
    if (!c.points || !c.points.length) return;
    const canvas = document.getElementById('spark-' + c.id);
    if (!canvas) return;
    makeSpark(canvas.getContext('2d'), c.points, c.label, c.colour);
  });

  // -------- Details sections --------
  const details = document.getElementById('oinx-details');

  // 1. Latency detail
  const latHtml = `
    <details>
      <summary>Extraction latency — p50 / p95 breakdown</summary>
      <div class="detail-body">
        <p>${escapeHtml(lat.message || '')}</p>
        <dl class="kv">
          <dt>p50 (24h)</dt><dd>${lat.p50_24h_sec ?? '—'} s</dd>
          <dt>p95 (24h)</dt><dd>${lat.p95_24h_sec ?? '—'} s</dd>
          <dt>p50 (7d)</dt><dd>${lat.p50_7d_sec ?? '—'} s</dd>
          <dt>p95 (7d)</dt><dd>${lat.p95_7d_sec ?? '—'} s</dd>
          <dt>source</dt><dd>${lat.source || 'n/a'}</dd>
          <dt>samples (24h)</dt><dd>${lat.sample_size_24h ?? 0}</dd>
          <dt>samples (7d)</dt><dd>${lat.sample_size_7d ?? 0}</dd>
        </dl>
        ${lat.series_24h && lat.series_24h.length
          ? `<canvas id="lat-hourly" style="height:180px;margin-top:14px;"></canvas>`
          : `<p><em>Hourly chart will render once the 24h series has at least one bucket.</em></p>`}
      </div>
    </details>`;

  // 2. Unknown rate detail
  const methods = unk.method_breakdown_24h || {};
  const methodChips = Object.entries(methods)
    .map(([k, v]) => `<span class="chip">${escapeHtml(k)}: <strong>${v}</strong></span>`)
    .join('');
  const unkHtml = `
    <details>
      <summary>[extracted: unknown] rate — Issue #116 reference</summary>
      <div class="detail-body">
        <p>${escapeHtml(unk.message || '')}</p>
        <p><strong>${unk.note || ''}</strong> ·
           <a href="https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint/issues/116" target="_blank" rel="noopener">see Issue #116</a>.
           Today's rate reflects the pre-#171 baseline; values &gt; 5% indicate the extractor
           is returning the fallback sentinel instead of a structured method tag.</p>
        <dl class="kv">
          <dt>rate (24h)</dt><dd>${unk.rate_24h_pct ?? '—'}%</dd>
          <dt>rate (7d)</dt><dd>${unk.rate_7d_pct ?? '—'}%</dd>
          <dt>total (24h)</dt><dd>${unk.total_extractions_24h ?? 0}</dd>
          <dt>unknown (24h)</dt><dd>${unk.unknown_count_24h ?? 0}</dd>
          <dt>total (7d)</dt><dd>${unk.total_extractions_7d ?? 0}</dd>
          <dt>unknown (7d)</dt><dd>${unk.unknown_count_7d ?? 0}</dd>
        </dl>
        <div style="margin-top:10px;">
          <div class="oinx-label" style="margin-bottom:4px;">Breakdown by extraction_method (24h)</div>
          <div class="breakdown-chips">${methodChips || '<em class="muted">(no methods seen in window)</em>'}</div>
        </div>
        ${unk.series_7d && unk.series_7d.length
          ? `<canvas id="unk-daily" style="height:180px;margin-top:14px;"></canvas>`
          : `<p><em>Daily trend will render once the 7-day series has at least one day.</em></p>`}
      </div>
    </details>`;

  // 3. Accuracy detail — sortable table
  const rows = acc.rows || [];
  const accRowsHtml = rows.map((r, i) => `
    <tr data-idx="${i}">
      <td>${escapeHtml(r.trader)}</td>
      <td class="num">${r.accuracy !== null && r.accuracy !== undefined
        ? (100 * r.accuracy).toFixed(1) + '%' : '—'}</td>
      <td class="num">${r.samples ?? 0}</td>
      <td class="num">${r.misreads ?? 0}</td>
      <td class="num">${r.delta_vs_baseline !== null && r.delta_vs_baseline !== undefined
        ? r.delta_vs_baseline.toFixed(2) : '—'}</td>
      <td><span class="tier-${r.tier}">${r.tier}</span></td>
    </tr>
  `).join('');
  const accHtml = `
    <details>
      <summary>Extraction accuracy by trader (proxy baseline)</summary>
      <div class="detail-body">
        <p>${escapeHtml(acc.message || '')}</p>
        <p>Baseline: <code>${escapeHtml(acc.baseline_reference || '')}</code></p>
        <table class="oinx-table" id="acc-table">
          <thead>
            <tr>
              <th data-col="trader">Trader</th>
              <th data-col="accuracy" class="num">Accuracy</th>
              <th data-col="samples" class="num">Samples</th>
              <th data-col="misreads" class="num">Misreads</th>
              <th data-col="delta" class="num">Δ vs baseline</th>
              <th data-col="tier">Tier</th>
            </tr>
          </thead>
          <tbody>${accRowsHtml || '<tr><td colspan="6" class="muted">No rows parsed.</td></tr>'}</tbody>
        </table>
      </div>
    </details>`;

  // 4. Correction memory detail
  const corrHtml = `
    <details>
      <summary>Correction memory growth</summary>
      <div class="detail-body">
        <p>${escapeHtml(corr.message || '')}</p>
        <dl class="kv">
          <dt>oinxtractor_corrections</dt><dd>${corr.oinxtractor_corrections_count ?? 0}</dd>
          <dt>openclaw_barn (total library)</dt><dd>${corr.openclaw_barn_total ?? 0}</dd>
        </dl>
        <p><a href="https://app.supermemory.ai" target="_blank" rel="noopener">Supermemory dashboard ↗</a></p>
        ${corr.growth_series_7d && corr.growth_series_7d.length
          ? `<canvas id="corr-growth" style="height:180px;margin-top:14px;"></canvas>`
          : `<p><em>Growth chart will render once correction writes begin landing.</em></p>`}
      </div>
    </details>`;

  details.innerHTML = latHtml + unkHtml + accHtml + corrHtml;

  // Hourly latency chart
  if (lat.series_24h && lat.series_24h.length) {
    const ctx = document.getElementById('lat-hourly').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: lat.series_24h.map(p => p.t.slice(11,16)),
        datasets: [
          { label: 'p50 (s)', data: lat.series_24h.map(p => p.p50), borderColor: '#ff6b35', backgroundColor: '#ff6b3522', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 2 },
          { label: 'p95 (s)', data: lat.series_24h.map(p => p.p95), borderColor: '#f85149', backgroundColor: '#f8514922', borderWidth: 2, fill: false, tension: 0.3, pointRadius: 2 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: { y: { beginAtZero: true, ticks: { callback: v => v + 's' } } }
      }
    });
  }

  // Daily unknown rate chart
  if (unk.series_7d && unk.series_7d.length) {
    const ctx = document.getElementById('unk-daily').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: unk.series_7d.map(p => p.t.slice(5)),
        datasets: [{
          label: 'unknown rate (%)',
          data: unk.series_7d.map(p => p.pct),
          backgroundColor: unk.series_7d.map(p => p.pct < 5 ? '#3fb95088' : p.pct < 25 ? '#d2992288' : '#f8514988'),
          borderColor: unk.series_7d.map(p => p.pct < 5 ? '#3fb950' : p.pct < 25 ? '#d29922' : '#f85149'),
          borderWidth: 1,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } } }
      }
    });
  }

  // Correction growth chart (placeholder — renders when data exists)
  if (corr.growth_series_7d && corr.growth_series_7d.length) {
    const ctx = document.getElementById('corr-growth').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: corr.growth_series_7d.map(p => p.t),
        datasets: [{
          label: 'corrections',
          data: corr.growth_series_7d.map(p => p.count),
          borderColor: '#b392f0',
          backgroundColor: '#b392f022',
          borderWidth: 2, fill: true, tension: 0.3,
        }]
      },
      options: { responsive: true, maintainAspectRatio: false,
                 plugins: { legend: { display: false } },
                 scales: { y: { beginAtZero: true } } }
    });
  }

  // Sortable accuracy table
  const accTable = document.getElementById('acc-table');
  if (accTable) {
    const tbody = accTable.querySelector('tbody');
    const ths = accTable.querySelectorAll('th');
    const dataRows = (acc.rows || []).map((r, i) => ({...r, _i: i}));
    let sortKey = 'samples';
    let sortDesc = true;
    function render() {
      dataRows.sort((a, b) => {
        const get = (r) => {
          if (sortKey === 'trader') return r.trader.toLowerCase();
          if (sortKey === 'tier') return r.tier;
          if (sortKey === 'accuracy') return r.accuracy ?? -1;
          if (sortKey === 'delta') return r.delta_vs_baseline ?? 0;
          return r[sortKey] ?? 0;
        };
        const A = get(a), B = get(b);
        if (A < B) return sortDesc ? 1 : -1;
        if (A > B) return sortDesc ? -1 : 1;
        return 0;
      });
      tbody.innerHTML = dataRows.map(r => `
        <tr>
          <td>${escapeHtml(r.trader)}</td>
          <td class="num">${r.accuracy !== null && r.accuracy !== undefined ? (100*r.accuracy).toFixed(1)+'%' : '—'}</td>
          <td class="num">${r.samples ?? 0}</td>
          <td class="num">${r.misreads ?? 0}</td>
          <td class="num">${r.delta_vs_baseline !== null && r.delta_vs_baseline !== undefined ? r.delta_vs_baseline.toFixed(2) : '—'}</td>
          <td><span class="tier-${r.tier}">${r.tier}</span></td>
        </tr>`).join('');
    }
    ths.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.dataset.col;
        if (sortKey === col) sortDesc = !sortDesc; else { sortKey = col; sortDesc = true; }
        render();
      });
    });
    render();
  }

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
})();
</script>
</body>
</html>
"""


def _ts_pretty(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def render_html(bundle: dict) -> str:
    ts = _parse_iso(bundle["ts"]) or _utc_now()
    next_refresh = ts + timedelta(minutes=10)
    html = HTML_TEMPLATE
    # JSON payload: embed entire bundle (safe to inline; no user-provided strings)
    payload = json.dumps(bundle, ensure_ascii=True)
    # Avoid breaking </script> parsers
    payload = payload.replace("</", "<\\/")
    html = html.replace("__TS_PRETTY__", _ts_pretty(ts))
    html = html.replace("__NEXT_PRETTY__", _ts_pretty(next_refresh))
    html = html.replace("__JSON_PAYLOAD__", payload)
    return html


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)

    bundle = build_bundle()

    # Write JSON
    JSON_OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # Write HTML
    HTML_OUT.write_text(render_html(bundle), encoding="utf-8")

    # Emit checkpoint event (best-effort)
    if _emit_event is not None:
        try:
            _emit_event(
                "ARTIFACT_PUBLISHED",
                agent="hermes",
                artifact_path=str(HTML_OUT.relative_to(ROOT)),
                extra={
                    "category": "oinxtractor_quality",
                    "src_path": str(JSON_OUT.relative_to(ROOT)),
                    "latency_status": bundle["latency"].get("status"),
                    "unknown_rate_status": bundle["unknown_rate"].get("status"),
                    "accuracy_status": bundle["accuracy_by_trader"].get("status"),
                    "corrections_status": bundle["correction_memory"].get("status"),
                },
            )
        except Exception as exc:
            # Don't crash the collector if the event-stream is unavailable
            print(f"[warn] ARTIFACT_PUBLISHED emit failed: {exc}", file=sys.stderr)

    # Human-readable summary on stdout
    statuses = {k: (bundle[k].get("status") if isinstance(bundle.get(k), dict) else "?")
                for k in ("latency", "unknown_rate", "accuracy_by_trader", "correction_memory")}
    print(f"[ok] wrote {JSON_OUT}")
    print(f"[ok] wrote {HTML_OUT}")
    print(f"[ok] statuses: {statuses}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
