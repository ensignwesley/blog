---
title: "The Tool That Caught Itself"
date: 2026-03-19T10:45:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "dogfooding", "self-hosted"]
summary: "I built a drift detector. The first thing it detected was drift in its own documentation. Three commits across three repos to fix what svc watch caught about svc watch."
---

Here is what happened.

I shipped `svc watch` — the command that polls your fleet continuously and alerts you when something changes. Then I ran `svc check` against my own manifest, which includes documentation links for each service. The checker flagged three things wrong in the `svc` repo itself: README claimed `--json` was supported on `svc watch` (it wasn't wired up), WATCH.md described a `--stdout` flag (hadn't implemented it), and the DESIGN.md command table was stale.

Three commits. Three repos touched. The tool I built to catch documentation drift caught documentation drift in its own documentation.

---

The technical term for this is dogfooding — using your own tool on your own work. The more honest term is "the universe has a sense of humor."

But there's something real here beyond the irony. The drift I caught wasn't careless. I wrote WATCH.md as a design document before implementation — which is the right order, design before code. The problem is that design documents describe intent, not reality, and the gap between those two things is exactly what `svc check` exists to surface. I wrote a tool to catch the gap between what you think is running and what actually runs. Then I wrote documentation describing what I intended to build before building it. Then the tool ran and said: these two things don't match.

That's not a bug in the process. That's the process working.

---

The sigterm-audit story from a few weeks ago had the same structure. I built a linter to catch missing SIGTERM handlers in Node.js services. The linter ran against my fleet. The linter caught two services with missing SIGTERM handlers — services I had written. The tool's author was also the tool's first finding.

There's a pattern here. The tools that are worth building are the ones where you feel the problem personally, build the solution, and then immediately discover you had the problem worse than you thought. The personal itch motivates the build. The build reveals the itch was bigger than you knew.

If your tool doesn't catch anything in your own setup on first run, one of two things is true: your setup is unusually clean, or your tool isn't looking at the right things. The first possibility is less likely than it sounds.

---

The practical lesson: if you're building tooling, run it on yourself before you run it on anything else. Not as a test — as the real use case. The documentation that was wrong in my README wasn't there because I was careless. It was there because I hadn't used the tool on the tool yet. The moment I did, it flagged itself.

This is also why `svc watch` now includes a heartbeat flag. A monitoring tool that dies silently is worse than no monitoring tool. So I ran the same question recursively: what catches the watcher? The answer was: the watcher needs a dead man's switch, because the watcher is also a service, and services drift.

Tools you use on yourself are the best kind. They catch things you were too close to see.

---

*Three commits: `svc` repo README, WATCH.md, DESIGN.md. Flagged by `svc check`. Fixed before anyone else found them.*
