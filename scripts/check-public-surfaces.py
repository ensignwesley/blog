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


SURFACES: tuple[Surface, ...] = (
    Surface("Blog", "/", ("Reports from the Frontline", "Wesley&#39;s Log")),
    Surface("Projects", "/projects/", ("Projects", "Live Tools", "All Projects")),
    Surface("Status", "/status/", ("System Status", "Service status checks")),
    Surface("Observatory", "/observatory/", ("Observatory", "ALL SYSTEMS OPERATIONAL")),
    Surface("Dead Drop", "/drop", ("DEAD DROP", "Encrypt &amp; Drop")),
    Surface("DEAD//CHAT", "/chat", ("DEAD//CHAT", "Establish Connection")),
    Surface("Forth REPL", "/forth/", ("FORTH", "Wesley's Forth", "connected")),
    Surface("Lisp REPL", "/lisp/", ("λ LISP", "Welcome to Wesley\\'s Lisp")),
    Surface("Markov", "/markov/", ("CAPTAIN'S LOG GENERATOR", "Generate Log")),
    Surface("Pathfinder", "/pathfinder/", ("PATHFINDER", "Algorithm", "A*")),
    Surface("Comments API", "/comments/", ("Comments API", "Self-hosted blog comment service")),
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
        if missing:
            errors.append(f"{surface.name}: missing marker(s): {', '.join(missing)}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"site base URL (default: {DEFAULT_BASE})")
    args = parser.parse_args()

    errors = check_surfaces(args.base, SURFACES)
    errors.extend(check_status_data(args.base))

    if errors:
        print("\nFAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("\nall public surface checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
