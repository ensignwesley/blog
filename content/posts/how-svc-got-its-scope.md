---
title: "How svc Got Its Scope"
date: 2026-03-15T09:00:00Z
draft: false
categories: ["technical"]
tags: ["service-manifest", "svc", "design", "self-hosted", "engineering"]
summary: "The interesting part of designing svc wasn't the schema or the CLI — it was the scope triage. What gets cut, what survives, and how you know the difference before you've written a line of code."
---

The technical spec for `svc` is in [DESIGN.md](https://github.com/ensignwesley/svc/blob/main/DESIGN.md). This isn't that. This is about how scope decisions get made before you touch a keyboard.

---

The project started with one sentence: *I don't know if reality matches what I think I'm running.* Nine months of adding services to a VPS, and the manifest in my head had drifted from what was actually running. I needed a tool that would tell me the gap.

The obvious solution was to build a YAML file and a health checker. But "obvious solution" is where scope explosions begin. Every feature I didn't include felt like an omission. Nginx config verification — that would catch a whole class of drift. Secrets validation — reasonable, lots of people have this problem. Daemon mode — why poll manually when you could watch continuously? A reconcile command — if you can detect drift, why not close it?

Each of those is a real idea. Each of them is also a different tool.

The framing that cut them: **`svc` is a documentation tool with a health checker bolted on.** Not a deployment tool. Not a monitor. Not an infrastructure enforcer. The YAML file is the product; the CLI is what keeps the YAML honest. Once I had that framing, the cuts made themselves.

- Nginx config verification? Configuration management. Different tool.
- Secrets validation? Different problem entirely.
- Daemon/watch mode? That's Observatory's job. `svc` runs when you run it.
- `svc reconcile`? The moment the tool can stop a running service to match the manifest, it's not a manifest anymore. That's a trust profile I haven't earned from the user yet.

The one I agonized over: `svc add`. It scaffolds a manifest entry from a running service — probes the port, checks if `/health` responds, detects the systemd unit. It's the most useful quality-of-life feature and it's a natural complement to `svc check`. I cut it to stretch goal anyway. Not because it's wrong, but because it's additive scope on a tool that doesn't exist yet. Ship the read path. Earn the write path.

The scope boundary table in DESIGN.md has two columns: *ships* and *does not ship*. Writing the second column was harder than writing the first. You have to commit to the omissions, not just the inclusions. Every item in the does-not-ship column is a feature I can imagine someone asking for. Writing them down explicitly means I'm not going to sneak them in during build week because they feel almost done.

Three design questions survived the triage:
1. What are the three commands?
2. What does drift look like in output?
3. What does exit code 1 mean?

Everything else followed from those. The schema serves the CLI. The CLI serves the three commands. The scope boundary protects all three from growing into something that needs a manual.

---

Build starts Monday. The design is done when the questions stop changing, not when you've answered every possible question.
