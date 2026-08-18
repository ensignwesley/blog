#!/usr/bin/env python3
"""Refresh the static fallback content on the public status page."""

from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS_PAGE = ROOT / "static/status/index.html"
STATUS_DATA = ROOT / "static/status/data.json"
START = "      <!-- status-fallback:start -->"
END = "    <!-- status-fallback:end -->"
STALE_AFTER = timedelta(minutes=10)


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def format_time(value: str) -> str:
    parsed = parse_time(value)
    if parsed is None:
        return "check time unavailable"
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def rt_class(ms: Any) -> str:
    try:
        value = float(ms)
    except (TypeError, ValueError):
        return ""
    if value < 100:
        return "fast"
    if value < 500:
        return "ok"
    return "slow"


def safe_link(value: Any) -> str:
    href = str(value or "")
    if href.startswith(("https://", "http://", "/")):
        return h(href)
    return ""


def render_card(service: dict[str, Any]) -> str:
    up = bool(service.get("up"))
    anomalous = bool(up and service.get("anomaly"))
    label = "SLOW SPIKE" if anomalous else "OPERATIONAL" if up else "DOWN"
    badge = "warn" if anomalous else "up" if up else "down"
    checked = format_time(str(service.get("checked_at", "")))
    name = h(service.get("name", "Unknown service"))
    desc = h(service.get("description", ""))
    href = safe_link(service.get("link"))
    response_ms = service.get("response_ms")
    ms_text = "—" if response_ms is None else f"{h(response_ms)}ms"
    ms_class = rt_class(response_ms)
    ms = f'<span class="{ms_class}">{ms_text}</span>' if ms_class else f"<span>{ms_text}</span>"
    linked_name = f'<a href="{href}" target="_blank" rel="noopener">{name}</a>' if href else name
    card_class = "card anomaly" if anomalous else "card"
    return f"""      <article class="{card_class}" role="listitem" aria-label="{name}: {h(label.lower())}, {h(ms_text)}; checked {h(checked)}">
        <div class="card-info">
          <h2 class="card-name">{linked_name}</h2>
          <div class="card-desc">{desc}</div>
        </div>
        <div class="card-status">
          <div class="badge {badge}" aria-label="Status: {h(label)}"><span class="dot" aria-hidden="true"></span>{h(label)}</div>
          <div class="rtime" aria-label="Response time">{ms}</div>
          <div class="checked-at">Checked {h(checked)}</div>
        </div>
      </article>"""


def render_fallback(data: dict[str, Any]) -> str:
    services = data.get("services") if isinstance(data.get("services"), list) else []
    anomalies = [service for service in services if service.get("up") and service.get("anomaly")]
    generated_at = parse_time(str(data.get("generated_at", "")))
    stale = generated_at is None or datetime.now(timezone.utc) - generated_at > STALE_AFTER
    if not services:
        overall_class = "overall has-down"
        overall_label = "STATUS DATA UNAVAILABLE"
        cards = '      <div class="loading" role="status">Status data unavailable — try refreshing.</div>'
    elif stale:
        overall_class = "overall stale"
        overall_label = "STATUS DATA STALE"
        cards = "\n".join(render_card(service) for service in services)
    elif not data.get("all_up"):
        overall_class = "overall has-down"
        overall_label = "DEGRADED"
        cards = "\n".join(render_card(service) for service in services)
    elif anomalies:
        overall_class = "overall has-warn"
        noun = "ANOMALY" if len(anomalies) == 1 else "ANOMALIES"
        overall_label = f"{len(anomalies)} PERFORMANCE {noun}"
        cards = "\n".join(render_card(service) for service in services)
    else:
        overall_class = "overall all-up"
        overall_label = "ALL SYSTEMS OPERATIONAL"
        cards = "\n".join(render_card(service) for service in services)

    generated = format_time(str(data.get("generated_at", "")))
    stale_note = f" Telemetry is older than {int(STALE_AFTER.total_seconds() // 60)} minutes." if stale else ""
    return f"""{START}
      <div id="overall" class="{overall_class}"><span class="dot"></span> {h(overall_label)}</div>
    </header>

    <div id="services" class="services" role="list" aria-label="Service status checks" aria-live="polite">
{cards}
    </div>

    <div id="meta" class="meta" aria-live="polite">Static snapshot from {h(generated)}. JavaScript refreshes this data once per minute.{h(stale_note)}</div>
{END}"""


def main() -> int:
    page = STATUS_PAGE.read_text()
    try:
        data = json.loads(STATUS_DATA.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    start = page.index(START)
    end = page.index(END, start) + len(END)
    STATUS_PAGE.write_text(page[:start] + render_fallback(data) + page[end:] + ("\n" if not page.endswith("\n") else ""))
    print(f"wrote {STATUS_PAGE} from {STATUS_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
