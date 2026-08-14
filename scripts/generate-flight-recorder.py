#!/usr/bin/env python3
"""Generate the static Flight Recorder page from Preflight evidence.

The Flight Recorder is deliberately boring: read local JSON records, inspect recent
repo commits, and write a static HTML timeline. No database. No client framework.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD_DIR = Path.home() / ".local/share/preflight/records"
DEFAULT_OUTPUT = ROOT / "static/flight-recorder/index.html"
MAX_RECORDS = 12
COMMIT_LOOKBACK_HOURS = 30

REPOS = {
    "preflight": Path.home() / "preflight",
    "blog": Path.home() / "blog",
    "profile": Path.home() / "ensignwesley-profile",
    "dead-drop": Path.home() / "dead_drop",
    "dead-chat": Path.home() / "chat",
    "forth": Path.home() / "forth",
    "comments": ROOT / "repos/comments",
    "lisp": ROOT / "repos/lisp",
    "observatory": ROOT / "repos/observatory",
    "svc": ROOT / "repos/svc",
    "versioncheck": ROOT / "repos/versioncheck",
}

SMOKE_LABELS = {
    "dead-drop": "Dead Drop health + storage-backed readiness",
    "dead-chat": "DEAD//CHAT health + security headers",
    "forth": "Forth health endpoint",
    "comments": "Comments health + storage-backed readiness",
    "status-data": "Status JSON freshness + service roster",
    "observatory-api": "Observatory API freshness + service-key roster",
}


@dataclass(frozen=True)
class Commit:
    repo: str
    short_hash: str
    timestamp: datetime
    subject: str


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def format_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def run_git(repo: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def load_records(record_dir: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(record_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "checked_at" not in data:
            continue
        data["_path"] = path
        records.append(data)
        if len(records) >= limit:
            break
    records.sort(key=lambda item: item["checked_at"], reverse=True)
    return records


def load_commits(since: datetime, until: datetime) -> list[Commit]:
    commits: list[Commit] = []
    since_arg = since.isoformat()
    until_arg = until.isoformat()
    fmt = "%h%x00%cI%x00%s"
    for name, repo in REPOS.items():
        if not (repo / ".git").exists():
            continue
        output = run_git(repo, ["log", f"--since={since_arg}", f"--until={until_arg}", f"--pretty=format:{fmt}"])
        for line in output.splitlines():
            parts = line.split("\x00")
            if len(parts) != 3:
                continue
            short_hash, ts, subject = parts
            try:
                timestamp = parse_time(ts)
            except ValueError:
                continue
            commits.append(Commit(name, short_hash, timestamp, subject))
    return sorted(commits, key=lambda item: item.timestamp, reverse=True)


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    probes = record.get("probes", []) or []
    passed = [probe for probe in probes if probe.get("status") == "pass"]
    failed = [probe for probe in probes if probe.get("status") != "pass"]
    names = [str(probe.get("name", "unknown")) for probe in probes]
    smoke = [SMOKE_LABELS[name] for name in names if name in SMOKE_LABELS]
    elapsed = [probe.get("elapsed_ms") for probe in passed if isinstance(probe.get("elapsed_ms"), (int, float))]
    return {
        "total": len(probes),
        "passed": len(passed),
        "failed": len(failed),
        "failed_probes": failed,
        "names": names,
        "smoke": smoke,
        "fastest_ms": min(elapsed) if elapsed else None,
        "slowest_ms": max(elapsed) if elapsed else None,
    }


def group_commits(records: list[dict[str, Any]], commits: list[Commit]) -> dict[str, list[Commit]]:
    # Attach each commit once. Prefer the first Preflight record after the commit
    # happened; if the commit landed just after the newest record, attach it to
    # that newest record as part of the same maintenance run.
    result: dict[str, list[Commit]] = {str(record["_path"]): [] for record in records}
    ordered = sorted(records, key=lambda item: parse_time(item["checked_at"]))
    if not ordered:
        return result

    record_times = [(record, parse_time(record["checked_at"])) for record in ordered]
    newest_record, newest_time = record_times[-1]
    for commit in commits:
        target = None
        for record, checked_at in record_times:
            if checked_at >= commit.timestamp:
                target = record
                break
        if target is None and newest_time < commit.timestamp <= newest_time + timedelta(minutes=15):
            target = newest_record
        if target is not None:
            result[str(target["_path"])].append(commit)

    for bucket in result.values():
        bucket.sort(key=lambda item: item.timestamp, reverse=True)
    return result


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_badge(status: str) -> str:
    cls = "pass" if status == "pass" else "fail"
    label = "PASS" if status == "pass" else "ATTENTION"
    return f'<span class="badge {cls}">{label}</span>'


def render(records: list[dict[str, Any]], commits_by_record: dict[str, list[Commit]]) -> str:
    generated_at = datetime.now(timezone.utc)
    latest = parse_time(records[0]["checked_at"]) if records else None
    entries: list[str] = []

    for record in records:
        checked_at = parse_time(record["checked_at"])
        summary = summarize_record(record)
        status = str(record.get("status", "unknown"))
        commits = commits_by_record.get(str(record["_path"]), [])
        smoke_items = "".join(f"<li>{h(item)}</li>" for item in summary["smoke"])
        if not smoke_items:
            smoke_items = "<li>No named smoke checks captured in this record.</li>"
        commit_items = "".join(
            f'<li><span class="repo">{h(commit.repo)}</span> '
            f'<code>{h(commit.short_hash)}</code> — {h(commit.subject)} '
            f'<span class="muted">({h(format_time(commit.timestamp))})</span></li>'
            for commit in commits[:8]
        )
        if not commit_items:
            commit_items = '<li class="muted">No tracked repo commits in this window.</li>'
        failed_items = "".join(
            f'<li><span class="fail-text">{h(probe.get("name", "unknown"))}</span>: {h(probe.get("detail") or probe.get("status"))}</li>'
            for probe in summary["failed_probes"]
        )
        if not failed_items:
            failed_items = '<li class="muted">No failed probes recorded.</li>'
        probe_names = ", ".join(summary["names"])
        latency = ""
        if summary["fastest_ms"] is not None and summary["slowest_ms"] is not None:
            latency = f'<span>{h(summary["fastest_ms"])}–{h(summary["slowest_ms"])} ms probe range</span>'
        entries.append(
            f"""
      <article class="entry">
        <div class="entry-top">
          <div>
            <time datetime="{h(checked_at.isoformat())}">{h(format_time(checked_at))}</time>
            <h2>{h(summary['passed'])}/{h(summary['total'])} checks passed</h2>
          </div>
          {render_badge(status)}
        </div>
        <p class="summary">Preflight verified {h(summary['total'])} public surfaces and service endpoints. {h(summary['failed'])} probe(s) need attention.</p>
        <div class="metrics">
          <span>{h(record.get('tool', 'preflight'))} {h(record.get('version', ''))}</span>
          <span>{h(record.get('host', {}).get('hostname', 'unknown-host'))}</span>
          {latency}
        </div>
        <details open>
          <summary>What changed</summary>
          <ul>{commit_items}</ul>
        </details>
        <details>
          <summary>What was verified</summary>
          <p class="probe-list">{h(probe_names)}</p>
          <ul>{smoke_items}</ul>
        </details>
        <details>
          <summary>Failures</summary>
          <ul>{failed_items}</ul>
        </details>
      </article>"""
        )

    latest_text = format_time(latest) if latest else "No records found"
    entries_text = "\n".join(entries) if entries else '<p class="empty">No Preflight records found.</p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flight Recorder — Reports from the Frontline</title>
  <style>
    :root {{
      --bg: #0a0e12;
      --surface: #111820;
      --surface-2: #0e151c;
      --border: #1e2a36;
      --teal: #2dd4bf;
      --text: #c8d6e5;
      --muted: #6b8796;
      --green: #22c55e;
      --red: #ef4444;
      --amber: #f59e0b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: 'Courier New', Courier, monospace;
      line-height: 1.55;
      padding: 2rem 1rem;
    }}
    .container {{ max-width: 860px; margin: 0 auto; }}
    header {{ border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
    .site-name {{ color: var(--teal); font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; text-decoration: none; }}
    h1 {{ color: var(--teal); font-size: clamp(1.8rem, 5vw, 3rem); margin: 0.7rem 0 0.3rem; }}
    .subtitle, .muted, .probe-list {{ color: var(--muted); }}
    .subtitle {{ max-width: 680px; margin: 0; }}
    .meta-bar {{ display: flex; flex-wrap: wrap; gap: 0.7rem; margin-top: 1rem; font-size: 0.78rem; color: var(--muted); }}
    .meta-bar span {{ border: 1px solid var(--border); background: var(--surface-2); padding: 0.25rem 0.55rem; border-radius: 3px; }}
    .timeline {{ display: grid; gap: 1rem; }}
    .entry {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--teal); border-radius: 4px; padding: 1.1rem 1.25rem; }}
    .entry-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }}
    time {{ color: var(--muted); font-size: 0.78rem; }}
    h2 {{ color: var(--text); margin: 0.15rem 0 0; font-size: 1.1rem; }}
    .summary {{ margin: 0.8rem 0; }}
    .metrics {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.8rem 0 1rem; }}
    .metrics span, .repo {{ color: var(--teal); background: rgba(45, 212, 191, 0.07); border: 1px solid rgba(45, 212, 191, 0.22); border-radius: 3px; padding: 0.12rem 0.4rem; font-size: 0.76rem; }}
    .badge {{ display: inline-flex; align-items: center; border-radius: 3px; padding: 0.22rem 0.55rem; font-size: 0.74rem; font-weight: bold; letter-spacing: 0.1em; }}
    .badge.pass {{ color: var(--green); border: 1px solid var(--green); background: rgba(34,197,94,0.08); }}
    .badge.fail {{ color: var(--red); border: 1px solid var(--red); background: rgba(239,68,68,0.08); }}
    details {{ border-top: 1px solid var(--border); padding-top: 0.7rem; margin-top: 0.7rem; }}
    summary {{ color: var(--teal); cursor: pointer; font-weight: bold; }}
    ul {{ margin: 0.55rem 0 0; padding-left: 1.2rem; }}
    li {{ margin: 0.25rem 0; }}
    code {{ color: var(--amber); }}
    .fail-text {{ color: var(--red); }}
    footer {{ margin-top: 3rem; border-top: 1px solid var(--border); padding-top: 1.5rem; text-align: center; font-size: 0.78rem; color: var(--muted); }}
    a {{ color: var(--teal); }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <a href="/" class="site-name">☠ Reports from the Frontline</a>
      <h1>Flight Recorder</h1>
      <p class="subtitle">Reverse-chronological evidence trail from Preflight runs, smoke-style endpoint checks, and tracked repo commits. Static HTML. No database. No green lights without receipts.</p>
      <div class="meta-bar">
        <span>Generated {h(format_time(generated_at))}</span>
        <span>Latest record {h(latest_text)}</span>
        <span>{h(len(records))} records shown</span>
      </div>
    </header>

    <main class="timeline" aria-label="Flight recorder timeline">
{entries_text}
    </main>

    <footer>
      <a href="/">← Blog</a> &nbsp;·&nbsp;
      <a href="/projects/">Projects</a> &nbsp;·&nbsp;
      <a href="/status/">Status</a> &nbsp;·&nbsp;
      <a href="/observatory/">Observatory</a>
    </footer>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate static Flight Recorder HTML")
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORD_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=MAX_RECORDS)
    args = parser.parse_args()

    records = load_records(args.records, args.limit)
    if records:
        newest = parse_time(records[0]["checked_at"])
        oldest = parse_time(records[-1]["checked_at"]) - timedelta(hours=COMMIT_LOOKBACK_HOURS)
        commits = load_commits(oldest, newest + timedelta(minutes=15))
    else:
        commits = []
    commits_by_record = group_commits(records, commits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(records, commits_by_record))
    print(f"wrote {args.output} from {len(records)} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
