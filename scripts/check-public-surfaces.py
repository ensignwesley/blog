#!/usr/bin/env python3
"""Check Wesley's public web surfaces without third-party dependencies.

This is a lightweight maintenance gate for daily reviews. It does not replace
browser screenshots or deeper service smoke tests; it catches obvious drift:
wrong page, missing marker text, stale status data, or a degraded fleet badge.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE = "https://wesley.thesisko.com"
MAX_STATUS_AGE_SECONDS = 15 * 60
TIMEOUT_SECONDS = 15
CURRENT_MODEL = "gpt-5.5"

EXPECTED_STATUS_SERVICES = (
    "Blog",
    "Dead Drop",
    "DEAD//CHAT",
    "Status",
    "Observatory",
    "Pathfinder",
    "Comments",
    "Forth REPL",
    "Lisp REPL",
    "Markov REPL",
)

EXPECTED_OBSERVATORY_TARGETS = (
    "blog",
    "dead-drop",
    "dead-chat",
    "status",
    "observatory",
    "pathfinder",
    "comments",
    "forth",
    "lisp",
    "markov",
)


@dataclass(frozen=True)
class Surface:
    name: str
    path: str
    markers: tuple[str, ...]
    any_markers: tuple[str, ...] = ()
    forbidden_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class HealthEndpoint:
    name: str
    path: str
    service: str
    storage_backed: bool = False


SURFACES: tuple[Surface, ...] = (
    Surface("Blog", "/", ("Reports from the Frontline", "Wesley&#39;s Log")),
    Surface("Projects", "/projects/", ("Projects", "Live Tools", "All Projects")),
    Surface("About", "/about/", ("About", "Junior Operations Officer", CURRENT_MODEL)),
    Surface("Uses", "/uses/", ("The Model", f"OpenAI {CURRENT_MODEL}", "OpenClaw")),
    Surface("Status", "/status/", ("System Status", "Service status checks")),
    Surface(
        "Observatory",
        "/observatory/",
        ("Observatory",),
        any_markers=("ALL SYSTEMS OPERATIONAL", "OPERATIONAL — LATENCY ANOMALIES DETECTED"),
        forbidden_markers=("OUTAGE DETECTED", "DOWN —"),
    ),
    Surface("Dead Drop", "/drop", ("DEAD DROP", "Encrypt &amp; Drop")),
    Surface("DEAD//CHAT", "/chat", ("DEAD//CHAT", "Establish Connection")),
    Surface("Forth REPL", "/forth/", ("FORTH", "Wesley's Forth", "connected")),
    Surface("Lisp REPL", "/lisp/", ("λ LISP", "Welcome to Wesley\\'s Lisp")),
    Surface(
        "Markov",
        "/markov/",
        ("CAPTAIN'S LOG GENERATOR", "Generate Log", "aria-live=\"polite\"", "role=\"status\""),
    ),
    Surface(
        "Pathfinder",
        "/pathfinder/",
        ("PATHFINDER", "Algorithm", "A*", "Interactive pathfinding grid", "role=\"alert\""),
    ),
    Surface("Comments API", "/comments/", ("Comments API", "Self-hosted blog comment service")),
    Surface(
        "Comments Widget",
        "/posts/day-1-reports-from-the-frontline/#comments",
        (
            'section class="comments" id="comments"',
            'data-post="day-1-reports-from-the-frontline"',
            'id="cmt-form"',
            'id="cmt-list"',
        ),
    ),
)


HEALTH_ENDPOINTS: tuple[HealthEndpoint, ...] = (
    HealthEndpoint("Dead Drop health", "/drop/health", "dead-drop", storage_backed=True),
    HealthEndpoint("DEAD//CHAT health", "/chat/health", "dead-chat"),
    HealthEndpoint("Forth health", "/forth/health", "forth"),
    HealthEndpoint("Comments health", "/comments/health", "comments", storage_backed=True),
)


PROJECT_CATALOG_MARKERS: dict[str, tuple[str, ...]] = {
    "Blog": ("Reports from the Frontline", "https://github.com/ensignwesley/blog"),
    "Dead Drop": ("Dead Drop", "/drop", "https://github.com/ensignwesley/dead-drop"),
    "DEAD//CHAT": ("DEAD//CHAT", "/chat", "https://github.com/ensignwesley/dead-chat"),
    "Comments": ("Comments", "https://github.com/ensignwesley/comments"),
    "Forth": ("Wesley&#39;s Forth", "/forth/", "https://github.com/ensignwesley/forth"),
    "Lisp": ("Wesley&#39;s Lisp", "/lisp/", "https://github.com/ensignwesley/lisp"),
    "Observatory": ("Observatory", "/observatory/", "https://github.com/ensignwesley/observatory"),
    "Markov": ("Markov Chain Captain&#39;s Log Generator", "/markov/", "https://github.com/ensignwesley/markov-captains-log"),
    "Pathfinder": ("Pathfinder", "/pathfinder/"),
    "Status": ("Status", "/status/"),
    "svc": ("svc", "https://github.com/ensignwesley/svc"),
    "restorecheck": ("restorecheck", "https://github.com/ensignwesley/restorecheck"),
    "versioncheck": ("versioncheck", "https://github.com/ensignwesley/versioncheck"),
    "Dead Link Hunter": ("Dead Link Hunter", "https://github.com/ensignwesley/deadlinks"),
    "raw-drop": ("raw-drop", "https://github.com/ensignwesley/raw-drop"),
}


def fetch(url: str, accept: str = "text/html") -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": "wesley-public-surface-check/1.0", "Accept": accept})
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body
    except URLError as exc:  # pragma: no cover - depends on network state
        raise RuntimeError(str(exc)) from exc


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def check_surfaces(base: str, surfaces: Iterable[Surface]) -> list[str]:
    errors: list[str] = []
    for surface in surfaces:
        url = base.rstrip("/") + surface.path
        try:
            status, body = fetch(url)
        except RuntimeError as exc:
            errors.append(f"{surface.name}: fetch failed: {exc}")
            continue

        if status != 200:
            errors.append(f"{surface.name}: expected HTTP 200, got {status}")
            continue

        missing = [marker for marker in surface.markers if marker not in body]
        if surface.any_markers and not any(marker in body for marker in surface.any_markers):
            missing.append("one of: " + ", ".join(surface.any_markers))
        if missing:
            errors.append(f"{surface.name}: missing marker(s): {', '.join(missing)}")
            continue

        forbidden = [marker for marker in surface.forbidden_markers if marker in body]
        if forbidden:
            errors.append(f"{surface.name}: found forbidden marker(s): {', '.join(forbidden)}")
            continue

        print(f"ok {surface.name}")

    return errors


def check_status_data(base: str) -> list[str]:
    url = base.rstrip("/") + "/status/data.json"
    errors: list[str] = []
    try:
        status, body = fetch(url, accept="application/json")
    except RuntimeError as exc:
        return [f"Status data: fetch failed: {exc}"]

    if status != 200:
        return [f"Status data: expected HTTP 200, got {status}"]

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return [f"Status data: invalid JSON: {exc}"]

    if not data.get("all_up"):
        down = [svc.get("name", "<unnamed>") for svc in data.get("services", []) if not svc.get("up")]
        errors.append("Status data: fleet not all up" + (f" ({', '.join(down)})" if down else ""))

    generated_at = data.get("generated_at")
    if not generated_at:
        errors.append("Status data: missing generated_at")
    else:
        try:
            age = (datetime.now(timezone.utc) - parse_time(generated_at)).total_seconds()
        except ValueError as exc:
            errors.append(f"Status data: bad generated_at {generated_at!r}: {exc}")
        else:
            if age < 0:
                errors.append(f"Status data: generated_at is in the future ({generated_at})")
            elif age > MAX_STATUS_AGE_SECONDS:
                errors.append(f"Status data: stale ({int(age)}s old, generated_at={generated_at})")
            else:
                print(f"ok Status data fresh ({int(age)}s old)")

    services = data.get("services")
    if not isinstance(services, list):
        errors.append(f"Status data: expected service list, got {type(services).__name__}")
    else:
        service_names = [str(service.get("name", "")) for service in services if isinstance(service, dict)]
        if tuple(service_names) != EXPECTED_STATUS_SERVICES:
            errors.append(
                "Status data: service roster drifted "
                f"(expected {', '.join(EXPECTED_STATUS_SERVICES)}; got {', '.join(service_names)})"
            )

        for service in services:
            if not isinstance(service, dict):
                errors.append(f"Status data: malformed service entry {service!r}")
                continue

            name = str(service.get("name", "<unnamed>"))
            checked_at = service.get("checked_at")
            if not checked_at:
                errors.append(f"Status data: {name} missing checked_at")
                continue

            try:
                checked_age = (datetime.now(timezone.utc) - parse_time(str(checked_at))).total_seconds()
            except ValueError as exc:
                errors.append(f"Status data: {name} bad checked_at {checked_at!r}: {exc}")
            else:
                if checked_age < 0:
                    errors.append(f"Status data: {name} checked_at is in the future ({checked_at})")
                elif checked_age > MAX_STATUS_AGE_SECONDS:
                    errors.append(
                        f"Status data: {name} stale check ({int(checked_age)}s old, checked_at={checked_at})"
                    )

    return errors


def check_observatory_api(base: str) -> list[str]:
    """Validate the live Observatory data feed, not just the rendered page."""
    url = base.rstrip("/") + "/observatory/api"
    errors: list[str] = []
    try:
        status, body = fetch(url, accept="application/json")
    except RuntimeError as exc:
        return [f"Observatory API: fetch failed: {exc}"]

    if status != 200:
        return [f"Observatory API: expected HTTP 200, got {status}"]

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return [f"Observatory API: invalid JSON: {exc}"]

    generated_at = data.get("generated_at")
    if not generated_at:
        errors.append("Observatory API: missing generated_at")
    else:
        try:
            age = (datetime.now(timezone.utc) - parse_time(generated_at)).total_seconds()
        except ValueError as exc:
            errors.append(f"Observatory API: bad generated_at {generated_at!r}: {exc}")
        else:
            if age < 0:
                errors.append(f"Observatory API: generated_at is in the future ({generated_at})")
            elif age > MAX_STATUS_AGE_SECONDS:
                errors.append(f"Observatory API: stale ({int(age)}s old, generated_at={generated_at})")

    if data.get("all_up") is not True:
        errors.append("Observatory API: all_up is not true")

    services = data.get("services")
    if not isinstance(services, dict):
        errors.append(f"Observatory API: expected service object, got {type(services).__name__}")
    elif tuple(services.keys()) != EXPECTED_OBSERVATORY_TARGETS:
        errors.append(
            "Observatory API: target roster drifted "
            f"(expected {', '.join(EXPECTED_OBSERVATORY_TARGETS)}; got {', '.join(services.keys())})"
        )
    else:
        for slug, service in services.items():
            current = service.get("current") if isinstance(service, dict) else None
            if not isinstance(current, dict):
                errors.append(f"Observatory API: {slug} missing current check")
                continue
            if current.get("ok") is not True:
                errors.append(f"Observatory API: {slug} current.ok is not true")
            if current.get("status_code") != 200:
                errors.append(f"Observatory API: {slug} current.status_code is {current.get('status_code')!r}")
            if not isinstance(current.get("response_ms"), (int, float)) or current.get("response_ms", -1) < 0:
                errors.append(f"Observatory API: {slug} missing non-negative response_ms")

    if not errors:
        print("ok Observatory API")
    return errors


def check_observatory_csv(base: str) -> list[str]:
    """Validate the CSV export remains fresh and machine-readable."""
    url = base.rstrip("/") + "/observatory/export.csv"
    try:
        status, body = fetch(url, accept="text/csv")
    except RuntimeError as exc:
        return [f"Observatory CSV: fetch failed: {exc}"]

    if status != 200:
        return [f"Observatory CSV: expected HTTP 200, got {status}"]

    reader = csv.DictReader(StringIO(body))
    required_fields = {"timestamp_utc", "target", "url", "ok", "status_code", "response_ms", "zscore", "anomaly"}
    if set(reader.fieldnames or ()) != required_fields:
        return [f"Observatory CSV: unexpected header {reader.fieldnames!r}"]

    rows = list(reader)
    if not rows:
        return ["Observatory CSV: no rows"]

    errors: list[str] = []
    try:
        latest = max(parse_time(row["timestamp_utc"]) for row in rows if row.get("timestamp_utc"))
    except ValueError as exc:
        errors.append(f"Observatory CSV: bad timestamp: {exc}")
    else:
        age = (datetime.now(timezone.utc) - latest).total_seconds()
        if age < 0:
            errors.append(f"Observatory CSV: latest timestamp is in the future ({latest.isoformat()})")
        elif age > MAX_STATUS_AGE_SECONDS:
            errors.append(f"Observatory CSV: stale ({int(age)}s old, latest={latest.isoformat()})")

    targets = {row.get("target") for row in rows}
    if targets != set(EXPECTED_OBSERVATORY_TARGETS):
        errors.append(
            "Observatory CSV: target roster drifted "
            f"(expected {', '.join(EXPECTED_OBSERVATORY_TARGETS)}; got {', '.join(sorted(targets))})"
        )

    if not errors:
        print("ok Observatory CSV")
    return errors


def check_health_endpoints(base: str, endpoints: Iterable[HealthEndpoint]) -> list[str]:
    errors: list[str] = []
    for endpoint in endpoints:
        url = base.rstrip("/") + endpoint.path
        try:
            status, body = fetch(url, accept="application/json")
        except RuntimeError as exc:
            errors.append(f"{endpoint.name}: fetch failed: {exc}")
            continue

        if status != 200:
            errors.append(f"{endpoint.name}: expected HTTP 200, got {status}")
            continue

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            errors.append(f"{endpoint.name}: invalid JSON: {exc}")
            continue

        endpoint_errors: list[str] = []
        if data.get("ok") is not True:
            endpoint_errors.append("ok is not true")
        if data.get("service") != endpoint.service:
            endpoint_errors.append(f"expected service {endpoint.service!r}, got {data.get('service')!r}")
        if not isinstance(data.get("version"), str) or not data.get("version"):
            endpoint_errors.append("missing version")
        if not isinstance(data.get("uptime_seconds"), int) or data.get("uptime_seconds", -1) < 0:
            endpoint_errors.append("missing non-negative uptime_seconds")

        if endpoint.storage_backed:
            storage = data.get("storage")
            if not isinstance(storage, dict):
                endpoint_errors.append("missing storage object")
            else:
                if storage.get("readable") is not True:
                    endpoint_errors.append("storage.readable is not true")
                if storage.get("writable") is not True:
                    endpoint_errors.append("storage.writable is not true")

        if endpoint_errors:
            errors.extend(f"{endpoint.name}: {error}" for error in endpoint_errors)
        else:
            print(f"ok {endpoint.name}")

    return errors


def check_projects_catalog(base: str) -> list[str]:
    """Catch project-page drift: missing launch paths or GitHub repo links."""
    url = base.rstrip("/") + "/projects/"
    try:
        status, body = fetch(url)
    except RuntimeError as exc:
        return [f"Projects catalog: fetch failed: {exc}"]

    if status != 200:
        return [f"Projects catalog: expected HTTP 200, got {status}"]

    errors: list[str] = []
    for project, markers in PROJECT_CATALOG_MARKERS.items():
        missing = [marker for marker in markers if marker not in body]
        if missing:
            errors.append(f"Projects catalog: {project} missing marker(s): {', '.join(missing)}")

    if not errors:
        print(f"ok Projects catalog ({len(PROJECT_CATALOG_MARKERS)} projects)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"site base URL (default: {DEFAULT_BASE})")
    args = parser.parse_args()

    errors = check_surfaces(args.base, SURFACES)
    errors.extend(check_projects_catalog(args.base))
    errors.extend(check_status_data(args.base))
    errors.extend(check_observatory_api(args.base))
    errors.extend(check_observatory_csv(args.base))
    errors.extend(check_health_endpoints(args.base, HEALTH_ENDPOINTS))

    if errors:
        print("\nFAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("\nall public surface checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
