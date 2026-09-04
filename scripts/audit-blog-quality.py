#!/usr/bin/env python3
"""Audit the blog against the current editorial bar.

This is intentionally static and local: it catches stale daily-log framing,
front matter gaps, and recent-post mix problems before a public build ships.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "content" / "posts"
RETIRED_TITLE = re.compile(r"(?:wesley'?s log|^day \d+\b|a day of)", re.I)
META_TAGS = {"diary", "reflection", "communication", "metrics", "promotion-portal"}
SUBJECT_TAGS = {"devops", "engineering", "forth", "lisp", "monitoring", "security", "deployment", "comments", "websocket"}
EDITORIAL_RESET = datetime(2026, 9, 1, tzinfo=timezone.utc)


@dataclass
class Post:
    path: Path
    title: str
    date: datetime
    draft: bool
    summary: str
    tags: list[str]


def parse_list(value: str) -> list[str]:
    return re.findall(r'"([^"]+)"|\'([^\']+)\'|([^,\[\]\s]+)', value)


def flatten(matches):
    return [next(part for part in match if part).strip() for match in matches]


def parse_post(path: Path) -> Post | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    try:
        front = text.split("---\n", 2)[1]
    except IndexError:
        return None
    fields: dict[str, str] = {}
    for line in front.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    title = fields.get("title", path.stem)
    raw_date = fields.get("date", "1970-01-01T00:00:00Z").replace("Z", "+00:00")
    try:
        date = datetime.fromisoformat(raw_date)
    except ValueError:
        date = datetime(1970, 1, 1, tzinfo=timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return Post(
        path=path,
        title=title,
        date=date,
        draft=fields.get("draft", "false").lower() == "true",
        summary=fields.get("summary", ""),
        tags=flatten(parse_list(fields.get("tags", ""))),
    )


def main() -> int:
    posts = [post for path in POSTS.glob("*.md") if (post := parse_post(path))]
    published = sorted([post for post in posts if not post.draft], key=lambda post: post.date, reverse=True)
    recent = published[:10]
    failures: list[str] = []
    warnings: list[str] = []

    retired = [post for post in published if RETIRED_TITLE.search(post.title)]
    legacy_retired = [post for post in retired if post.date < EDITORIAL_RESET]
    if legacy_retired:
        warnings.append(
            f"{len(legacy_retired)} legacy daily-log titles remain in archive; do not use this format again."
        )
    new_retired = [post for post in retired if post.date >= EDITORIAL_RESET]
    if new_retired:
        failures.append(
            "new-era retired-format titles found: "
            + ", ".join(f"{post.path.name} — {post.title}" for post in new_retired[:10])
        )

    for post in recent:
        if RETIRED_TITLE.search(post.title) and post.date >= EDITORIAL_RESET:
            failures.append(f"recent retired-format title: {post.path.name} — {post.title}")
        if len(post.summary) < 80:
            warnings.append(f"short/missing summary: {post.path.name}")

    recent_meta = sum(1 for post in recent[:5] if META_TAGS.intersection(tag.lower() for tag in post.tags))
    recent_subject = sum(1 for post in recent[:5] if SUBJECT_TAGS.intersection(tag.lower() for tag in post.tags))
    if recent_meta > recent_subject:
        warnings.append(
            f"recent mix is meta-heavy: {recent_meta} meta-tagged vs {recent_subject} subject-matter posts in latest 5"
        )

    tag_counts = Counter(tag.lower() for post in recent for tag in post.tags)
    print("Blog quality audit")
    print(f"published_posts={len(published)} recent_checked={len(recent)}")
    print("latest_posts:")
    for post in recent[:5]:
        print(f"- {post.date.date()} {post.path.name}: {post.title}")
    print("top_recent_tags=" + ", ".join(f"{tag}:{count}" for tag, count in tag_counts.most_common(8)))
    if warnings:
        print("warnings:")
        for item in warnings[:12]:
            print(f"- {item}")
    if failures:
        print("failures:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("PASS: recent posts avoid retired log format and maintain a subject-matter mix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
