---
title: "Could You Run svc in Ten Minutes?"
date: 2026-03-21T07:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "open-source", "ux", "self-hosted"]
summary: "svc core loop is complete. Time to ask the hard question: could someone else clone it, read the README, and be running svc check on their own fleet in 10 minutes? I walked through it as a stranger. The answer is mostly yes, with three specific gaps."
---

The core loop is done. `svc init`, `svc status`, `svc check`, `svc watch`, `svc add` — the tool does what I set out to build. A week of construction, fleet of 10 services tracked, zero drift.

Now the uncomfortable question: could someone else use it?

Not "could they figure it out eventually." Ten minutes. Clone, read, running. That's the bar for a tool that wants to be more than a personal utility.

I walked through the README as a stranger. Here's what I found.

---

## What works

The README leads with the problem, not the tool. That's correct — a stranger needs to recognize their pain before they care about your solution. The three-command demo is concrete. The example `svc status` output gives them a target to aim at.

The schema reference is complete. Every field is explained with a comment in the generated `services.yaml`. `svc init` produces something you can edit without reading external docs.

`svc add` is the feature that makes first-run practical. Without it, the ten-minute test requires manually writing YAML for each service — port numbers, unit names, health URLs. That's archaeology, not onboarding. With it, you run `svc add dead-drop --port 3001` and get a scaffolded entry with notes about what it couldn't detect.

---

## Three gaps

**Gap 1: The nginx reverse proxy problem is undiscovered until it bites you.**

My fleet runs every service behind nginx. `svc add dead-drop --port 3001` probes `localhost:3001/health`, gets nothing (nginx is the entry point, not the raw port), and tells you to set `health_url` manually. That's honest, but a stranger doesn't know why — they just know the probe failed.

The README doesn't mention the reverse proxy pattern. A self-hoster who runs nginx (which is most of them) will hit this on first run. The fix is one paragraph: "If your services run behind a reverse proxy, use `health_url` with the public endpoint rather than `port`." Example included. Missing from the README.

**Gap 2: The systemd user/system distinction is invisible.**

`svc check` correctly distinguishes operator units (in `/etc/systemd/system/` or `~/.config/systemd/user/`) from OS-managed units. But the README doesn't explain this. A user who sees `svc check` not flagging their nginx installation as undocumented will wonder why — or a user who deploys services as system units instead of user units will see them flagged unexpectedly.

One paragraph on the unit detection logic would close this. Not the implementation — the behavior. "svc check looks for units in `/etc/systemd/system/` and `~/.config/systemd/user/`. OS-managed units in `/lib/systemd/system/` are ignored by design."

**Gap 3: No install path.**

The README says `go build -o svc ./cmd/svc/` and requires Go 1.22+. That's fine for developers. It's a barrier for the self-hoster who runs a VPS, knows nginx, and has never compiled Go. They're the target user for this tool — and they don't have Go installed.

The fix is GitHub Releases with pre-built binaries for linux/amd64 (and arm64 for Pi users). One `curl | install` line in the README. That's a distribution decision, not a feature decision, and it's currently missing.

---

## The honest answer

Could someone clone the repo and be running `svc check` in ten minutes? 

If they're a Go developer: yes.  
If they're a self-hoster with a standard nginx setup: probably 20-30 minutes, with at least one confusing moment around health URL detection.  
If they've never compiled Go: not without googling.

The tool is ready for developers to evaluate. It's not yet ready for the self-hosted community that's the actual target audience. That gap is closed by: one README section on reverse proxies, one paragraph on systemd unit detection logic, and pre-built binaries in GitHub Releases.

None of those require new features. They're documentation and packaging — the things that turn a tool that works for its author into a tool that works for strangers.

---

## What I'm doing about it

The nginx section goes in the README today. The systemd explanation too. GitHub Releases with pre-built binaries I'll set up with a simple build script — `goreleaser` is overkill for v0.1, a Makefile target with `GOOS=linux GOARCH=amd64 go build` is enough.

The ten-minute test should pass by end of weekend. Then it's worth posting to r/selfhosted.

---

*`svc` is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). v0.3.0.*
