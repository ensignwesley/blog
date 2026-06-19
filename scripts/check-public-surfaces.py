#!/usr/bin/env python3
"""Check Wesley's public web surfaces without third-party dependencies.

This is a lightweight maintenance gate for daily reviews. It does not replace
browser screenshots or deeper service smoke tests; it catches obvious drift:
wrong page, missing marker text, stale status data, or a degraded fleet badge.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE = "https://wesley.thesisko.com"
MAX_STATUS_AGE_SECONDS = 15 * 60
TIMEOUT_SECONDS = 15


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
    Surface("Markov", "/markov/", ("CAPTAIN'S LOG GENERATOR", "Generate Log")),
    Surface("Pathfinder", "/pathfinder/", ("PATHFINDER", "Algorithm", "A*")),
    Surface("Comments API", "/comments/", ("Comments API", "Self-hosted blog comment service")),
)


HEALTH_ENDPOINTS: tuple[HealthEndpoint, ...] = (
    HealthEndpoint("Dead Drop health", "/drop/health", "dead-drop", storage_backed=True),
    HealthEndpoint("DEAD//CHAT health", "/chat/health", "dead-chat"),
    HealthEndpoint("Forth health", "/forth/health", "forth"),
    HealthEndpoint("Comments health", "/comments/health", "comments", storage_backed=True),
)


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
    if not isinstance(services, list) or len(services) != 10:
        errors.append(f"Status data: expected 10 services, got {len(services) if isinstance(services, list) else type(services).__name__}")

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"site base URL (default: {DEFAULT_BASE})")
    args = parser.parse_args()

    errors = check_surfaces(args.base, SURFACES)
    errors.extend(check_status_data(args.base))
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
