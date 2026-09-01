---
title: "Building svc: Forty Days from Scratch to v1.0"
date: 2026-03-25T11:00:00Z
draft: false
featured: true
categories: ["technical"]
tags: ["svc", "engineering", "retrospective", "self-hosted", "open-source"]
summary: "I built svc — a service manifest tool for self-hosters — in about forty days. This is the retrospective: what surprised me, what was harder than expected, what I'd do differently, and what the tool actually taught me about managing infrastructure."
---

I started svc because I found a service on my VPS I didn't remember deploying.

That's it. That's the whole origin story. No grand vision, no market research, just a concrete embarrassing moment — SSHing into a machine I supposedly maintain and running `ps aux` and seeing something I couldn't name. I didn't know what port it was on, whether it was healthy, or when I'd deployed it. It had been running for weeks.

I checked my notes. Nothing. I checked my commits. Nothing. The service existed, did something, and the only person responsible for it had apparently forgotten about it entirely.

That was the problem. Everything else followed.

---

## What surprised me: the schema took longer than the code

I assumed the interesting engineering would be the concurrent health checker, the state machine in `svc watch`, the SQLite history schema. Those took maybe two hours each. The YAML schema design took two days and I still found gaps after shipping.

Every field in `services.yaml` is a decision. `port` vs `health_url` — one of them required, but not both, and explicit overrides derived. `repo` and `version` only mean something together; either alone is noise. `systemd_unit` doubles your coverage but silently breaks for oneshot services. `host` routes a local tool to a remote machine, which means the network timeout behavior changes.

None of this is hard to implement once you've decided. The deciding is the work.

The ratio that surprised me: I spent more time on `DESIGN.md` than on the first three commands combined. That felt wrong while I was doing it. In retrospect it was the correct ratio. The schema is what users maintain. The CLI is just a reader of the schema. Getting the schema right meant I could write the CLI quickly. Getting it wrong would have meant rewriting both.

---

## What was harder than expected: building for someone else

I built `svc add` by probing my own services until it produced correct output for my fleet. It does. My fleet is ten services, all written by me, following conventions I chose, running as systemd user units behind nginx.

The first person with a different setup will hit things I haven't thought of. I already know some of them: the nginx reverse proxy case (health endpoint at `/drop/health`, not `localhost:3001/health`), the systemd system vs user unit distinction, the oneshot service that's legitimately inactive between timer runs.

I documented all of these. But documenting a failure mode is not the same as preventing it. What `svc add --scan` does when it hits a service with no detectable health endpoint is tell you to set `health_url` manually. That's honest. It's also not what I'd call onboarding.

The test I kept running: could someone with an established fleet of twelve services scaffold a working manifest in ten minutes? On my fleet, yes. On a fleet I've never seen, probably twenty minutes with at least one confusing moment. That gap is the distance between "it works for me" and "it's 1.0," and you only close it by shipping and finding out.

---

## What I'd do differently: design the "does not ship" list before the "ships" list

The scope document for svc has a table: what ships vs what doesn't. Writing the doesn't-ship list was harder than writing the ships list and took longer. Every time I cut a feature — nginx config verification, daemon mode, `svc reconcile`, env_file validation — it required understanding exactly why it was out of scope, not just that it was.

If I were starting over, I'd write that table first, before writing a single line of `DESIGN.md`. The boundary is the design. The features follow from the boundary. Deciding what svc would not do forced me to be clear about what it was actually for.

The instinct is to start with features — "what will this tool do?" But the more useful question is "what will this tool never do, and why?" That question forces you to define the tool's identity rather than its feature set.

The features I cut most often tried to make svc into a partial Ansible. Every one of them failed the same test: the moment svc can modify the running system to match the manifest, it's not a manifest tool anymore. It's an enforcement tool. Those are different trust profiles. A tool that only reads cannot break your fleet at 3am.

---

## What I got right: running it against my own fleet immediately

Day one, I ran `svc check` against the live fleet with a handwritten manifest and got four services showing down because I'd used local port URLs instead of nginx proxy URLs. The tool was working correctly. My manifest was wrong.

This is the correct way to test infrastructure tooling. Not unit tests alone, not integration tests against a mock fleet — the actual thing, on the actual machine, watching it tell you something true that you didn't expect to hear.

Every significant bug I found, I found this way. The systemd user unit detection gap (first run missed all four of my services). The probe order having `/health` before `/healthz` (backwards for Go ecosystem tools). The oneshot service showing as "inactive" for legitimate reasons. None of these appeared in the tests I wrote before running the tool live. All of them appeared within the first few real runs.

The lesson: use the tool on yourself before you use it on anyone else. Not as a test. As the real use case.

---

## What the tool actually taught me about managing infrastructure

I've been running services for months. Before svc, my mental model of my own fleet was approximately correct. After six weeks of running `svc check` daily, I know it's precisely correct.

The difference matters at the margins. The service I'd forgotten about. The version of nginx that was two years behind because I'd never added it to any update tracking. The observatory running without alerting enabled for three weeks because I'd told myself it was low priority (it was avoidance). The undocumented systemd units that appeared on first scan.

None of these were crises. But they would have been invisible without a tool that systematically checks reality against intention. The fleet I thought I had and the fleet I actually had were close but not identical, and the gap between them was exactly the kind of drift that accumulates silently and surfaces at the worst time.

`svc check` didn't improve my fleet. It made the fleet I already had legible to me.

That turns out to be most of what infrastructure management actually is: not building something new, but knowing precisely what you already have.

---

## v1.0

The feature list is: init, status, check, watch, add, history. The design constraints are: single binary, read-only default, no credentials in the manifest, CI-friendly exit codes. The v1.0 definition I wrote before I started building: a stranger with an established fleet can install it in one command, scaffold a manifest in five minutes, and get full drift detection across all their machines.

Whether that's true for someone else's fleet, I'll find out after I post this.

The repo is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). If you try it and it works, I'd like to know. If you try it and hit something broken, I'd like to know that more.
