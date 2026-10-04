#!/usr/bin/env python3
"""Check the surviving public operations and exact active project roster."""
from __future__ import annotations
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://wesley.thesisko.com"
SURFACES = {
    "/": ("Reports from the Frontline", "Promotion Review"),
    "/projects/": ("Projects", "Preflight", "Project Museum"),
    "/about/": ("About", "Promotion Review Portal"),
    "/promotion-review/": ("Promotion Review Portal", "Secure Coms"),
    "/comments/": ("Comments API", "Self-hosted blog comment service"),
    "/posts/forth-and-lisp-two-machines/": ('id="comments"', 'data-post="forth-and-lisp-two-machines"', "const API = '/comments/';"),
}
RETIRED_LINKS = ("/drop", "/chat", "/forth/", "/observatory/", "/status/", "/lisp/", "/markov/", "/pathfinder/", "/flight-recorder/", "/project-discovery/")

def fetch(url: str, *, accept: str | None = None):
    headers = {"User-Agent": "wesley-public-surface-check/2.0"}
    if accept:
        headers["Accept"] = accept
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=12) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    errors = []
    for path, markers in SURFACES.items():
        try:
            status, body = fetch(args.base.rstrip("/") + path, accept="text/html" if path == "/comments/" else None)
            if status != 200: errors.append(f"{path}: HTTP {status}")
            else:
                for marker in markers:
                    if marker not in body: errors.append(f"{path}: missing {marker!r}")
                if path in ("/", "/projects/"):
                    for retired in RETIRED_LINKS:
                        if f'href="{retired}' in body: errors.append(f"{path}: retired link {retired}")
            print(f"{path}: HTTP {status}")
        except (OSError, URLError) as exc:
            errors.append(f"{path}: {exc}")
    try:
        status, body = fetch(args.base.rstrip("/") + "/promotion-review/api/status")
        data = json.loads(body) if status == 200 else {}
        if status != 200 or data.get("service") != "promotion-review" or data.get("status") != "phase1":
            errors.append("promotion status contract failed")
        print(f"/promotion-review/api/status: HTTP {status}")
    except (OSError, URLError, ValueError) as exc:
        errors.append(f"promotion status: {exc}")
    try:
        status, body = fetch(args.base.rstrip("/") + "/comments/health")
        data = json.loads(body) if status == 200 else {}
        storage = data.get("storage", {})
        if status != 200 or data.get("service") != "comments" or not data.get("ok") or not storage.get("readable") or not storage.get("writable"):
            errors.append("comments health contract failed")
        print(f"/comments/health: HTTP {status}")
    except (OSError, URLError, ValueError) as exc:
        errors.append(f"comments health: {exc}")
    for error in errors: print("FAIL", error, file=sys.stderr)
    if errors: return 1
    print("all surviving public surface checks passed")
    return 0

if __name__ == "__main__": raise SystemExit(main())
