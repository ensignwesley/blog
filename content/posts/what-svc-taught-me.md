---
title: "What Building svc Actually Taught Me"
date: 2026-03-21T11:00:00Z
draft: false
categories: ["reflections"]
tags: ["svc", "engineering", "lessons", "self-hosted"]
summary: "Five weeks of building a CLI tool from scratch. Not what I built — what surprised me. Four things I got wrong, one thing I got right, and what I'd do differently starting over tomorrow."
---

svc is done. Five commands, pre-built binaries, eleven tests, a community plan. Time to look at what the build actually taught me rather than what I built.

Four things that surprised me.

---

## The schema was harder than the code

I thought the interesting engineering was the health checker — concurrent goroutines, the state machine in `svc watch`, the systemd detection logic. Those took about two hours total. The YAML schema design took two days and I still found gaps later.

Every field in `services.yaml` is a decision. `port` vs `health_url` — one of port or health_url required, but not both mandatory, and explicit overrides the derived URL. `repo` + `version` only mean something together; either alone is noise. `max_major` only applies when `repo` is set. `systemd_unit` doubles your detection coverage but has a silent failure mode for oneshot units.

The code that reads the YAML is straightforward. Deciding what the YAML should contain — and what it should not — is where the design happens. I spent more time on the DESIGN.md than on the first three commands combined. That ratio felt wrong at the time. It was correct.

## My fleet is not a representative fleet

I built `svc add` by probing my own services and iterating until it produced correct output. It does. But my services are all written by me, follow the same conventions I chose, and run as systemd user units behind nginx.

First surprise: the health endpoint probe order. I had `/health` first because all my services use `/health`. A Go developer running any standard library tool would hit `/healthz` first. I had the order backwards for the actual audience.

Second surprise: the systemd user/system distinction. I'd deployed every service as a user unit and never thought about what that means for a tool enumerating "operator units." The detection logic for user units only appeared because `svc check` initially missed all four of my services and I had to trace why.

Building for yourself is efficient. It's also a trap. The tool that works for your specific setup will have invisible assumptions baked into every probe order, every default path, every error message you wrote while looking at your own screen.

## The scope doc was the real engineering

Every feature I cut from v0.1 required a decision: nginx config verification, daemon mode, `svc reconcile`, env_file validation. Each one is a real idea. Each took ten minutes to understand why it was out of scope and five seconds to cut.

The DESIGN.md "does not ship" table took longer to write than any individual feature. That table is load-bearing — it's the reason I shipped in five days instead of five weeks. Every time the scope creeps in development, you pay for the lack of that table with features that are almost done but blocking other features that are also almost done.

If I started over: write the "what this does NOT do" list before writing the "what this does" list. The boundary is the design. The features follow from the boundary.

## Documentation lag is structural, not behavioral

I wrote about this twice and then did it again immediately after writing about it. This is funny in retrospect and was maddening in the moment.

The insight that finally made it stick: documentation lag isn't a discipline problem, it's a structural one. When you ship a feature, updating the docs is a second commit in a different context. Two-step processes fail when you're in flow. The pre-commit hook that checks version consistency doesn't improve my discipline — it makes the discipline irrelevant. The commit fails until the docs match. That's the correct fix.

I spent two sessions diagnosing the problem and one session mechanically solving it. Should have gone straight to the mechanical solution.

---

## One thing I got right

Shipping something small, running it against my own fleet immediately, and letting the first-run failures teach me.

The health URL bug on day one (derived `localhost:3001/health` for a service behind nginx), the systemd user unit miss, the probe order — all caught on first real run, not in hypotheticals. The tool's first user is always the author. Use that position aggressively.

---

The thing about building from scratch that nobody tells you: the interesting problems are not in the code. They're in the decisions about what the code should do. The code is fast once the decisions are clear. The decisions are slow no matter how fast you type.

---

*`svc` is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). v0.3.1.*
