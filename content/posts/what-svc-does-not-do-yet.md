---
title: "What svc Does Not Do Yet"
date: 2026-03-17T08:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "roadmap", "self-hosted"]
summary: "svc v0.1.0 gives you a pretty table and an exit code. Honest assessment of the three gaps that matter: alerting, history, and write operations."
---

`svc check` exits 1 when something is wrong. If you're running it manually, that's useful. If your blog 502s at 3am, you won't know until morning — because nobody ran `svc check` at 3am.

That's the honest gap. Here are the three that matter most.

---

## Gap 1: No alerting

`svc` is a pull tool. You run it; it tells you what's true at that moment. It has no watch mode, no push notifications, no way to reach you when a service goes down.

Observatory fills part of this — it polls every 5 minutes and has anomaly detection. But it has no push either. Right now "alerting" means checking the Observatory dashboard and hoping you checked recently.

**v0.2 plan:** A `svc watch` mode — run continuously, poll on a configurable interval, send a webhook POST on status change. One URL in `services.yaml` under `manifest.alert_webhook`. Pipe it to a Telegram bot, a Ntfy topic, whatever. The tool doesn't need to know; it just needs to POST JSON when state changes.

The design constraint: `svc watch` should be stateless between restarts. State lives in the manifest and in whatever receives the webhook, not in `svc` itself.

---

## Gap 2: No history

`svc status` tells you what's true right now. It doesn't tell you: was this service down an hour ago? How often does it go unhealthy? What's the uptime over the last 30 days?

Observatory tracks this for my fleet, but it's a separate tool with its own SQLite database. `svc` has no memory between runs.

**v0.2 plan:** Optional SQLite log — `svc check --record` appends each run's results to a local `svc.db`. Then `svc history <service>` shows you the last N checks, uptime percentage, and last failure. Opt-in, not default — the common case (CI check, manual run) doesn't need a database.

---

## Gap 3: No writes

`svc` reports drift. It can't close it. If `svc check` finds an undocumented unit, you have to manually add it to the manifest. If a service is down, you have to `systemctl restart` it yourself.

This is intentional for v0.1 — a tool that only reads can't break your fleet at 3am. But there's one write operation that's safe and high-value:

**v0.2 plan:** `svc add <id>` — scaffold a manifest entry from a running service. Probe the port, check if `/health` responds, detect the systemd unit, print the YAML to stdout. You review it and append. The tool drafts; you decide.

System-write operations (`svc restart`, `svc reconcile`) are not v0.2. Maybe not ever. That's a different product with a different trust profile.

---

## What v0.1.0 actually is

A documentation tool with a health checker. If you maintain the manifest, `svc check` tells you when reality drifts from what you wrote down. That's genuinely useful — the first run against my fleet found two undocumented units I'd forgotten about.

But "useful when you run it" and "notices problems before you do" are different products. v0.2 closes that gap.

---

*`svc` is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). v0.1.0 is working. v0.2 is next.*
