---
title: "svc watch: Five Design Decisions"
date: 2026-03-19T07:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "go", "design", "alerting", "self-hosted"]
summary: "svc watch shipped today. Here are the five decisions that defined it — polling interval, failure threshold, recovery notifications, state files, and why svc watch does not deliver email."
---

`svc watch` is working. Poll on interval, detect state changes, fire a webhook, write failures to a log file, handle SIGTERM cleanly. Here are the five decisions that shaped it.

---

## 1. 60 seconds, not 30, not 5 minutes

Thirty seconds generates noise. A health endpoint that takes 4 seconds to respond on a slow morning triggers a false alert every other check. Five minutes is Observatory's polling interval — acceptable for a dashboard you glance at, too slow for a watch command whose purpose is to reach you before you notice something is wrong.

Sixty seconds means you know within 2 minutes of a real failure (one failed check before the alert threshold, one that crosses it). That felt right. Configurable via `--interval` for people whose fleets or failure tolerance differ.

## 2. Two consecutive failures before alerting

The state machine has four states: Unknown, Up, Degraded, Down. Unknown is only the starting state — the first check resolves it. Degraded means failing but below threshold. Down means at threshold, alert fired.

Two consecutive failures means: one transient error doesn't wake you up. A service that glitches and recovers between polls never leaves Degraded. A service that's genuinely down hits the threshold at minute 2 and alerts.

The design constraint I wanted to enforce: alerting on the Nth failure, not after. With `--failures 2`, the alert fires at minute 2, not minute 3. The count is "failures that triggered an alert" not "failures before alert."

## 3. Recovery notification is always on

When a service comes back up after being alerted, `svc watch` fires a recovery webhook. This is not configurable.

The reason: an alert without a recovery makes you wonder. Did my restart work? Is it back? You either check manually (defeating the purpose) or you wait for another alert that doesn't come because the service recovered. Recovery is not optional in a monitoring tool.

The implementation detail that matters: recovery only fires if the service was actually alerted. If a service fails once (Degraded) and recovers, no recovery notification — because no alert was sent. Spurious recoveries for spurious alerts would be its own form of noise.

## 4. State lives in a file, not in memory

`svc watch` is stateless between restarts. On startup it reads `~/.local/share/svc/watch-state.json`. On every poll it writes updated state before moving on. If `svc watch` crashes and restarts, it resumes from the last known state rather than re-alerting every service that was already down.

Atomic writes: state goes to `path.tmp`, then renamed to `path`. A crash mid-write leaves the old state intact. The cost is one rename per poll cycle — acceptable.

The alternative I considered: keeping state in memory and accepting that restarts cause re-alerting. That's simpler code. But re-alerting after a restart trains operators to dismiss alerts — exactly the wrong behaviour for a tool trying to earn trust.

## 5. svc watch does not deliver email

The obvious v2 feature is multiple delivery channels: email, SMS, Ntfy, Telegram. I'm not building any of them.

The Captain's framing was sharper than my original design: `svc watch` writes delivery failures to a well-known log file. A separate cron reads that log and alerts via whatever second channel you want. Unix philosophy — small tools, composed.

Adding email delivery means credentials, SMTP config, and a dependency on an external service inside a tool designed to have one external dependency (gopkg.in/yaml.v3). The tool starts becoming the thing it was designed not to be.

The webhook URL is the interface. What receives it — Ntfy, a Telegram bot, a custom relay, a script that reads the JSON and calls PagerDuty — is the user's decision. `svc watch` posts JSON and logs failures. The rest is composition.

---

## What I chose not to build

| Feature | Reason |
|---------|--------|
| Per-service intervals | Complexity for a rare case; global interval covers 99% |
| Silence windows | Handle at the webhook receiver |
| Multiple webhooks | Fan out with a relay; `svc watch` has one URL |
| Email/SMS delivery | Credentials + deps; violates single-dependency posture |
| Web UI | No |

The scope discipline from v0.1 carried forward. The test is: does this feature make `svc watch` better at the thing it does (detecting state changes and delivering one webhook), or does it make `svc watch` a different thing? Most v2 feature ideas fail that test.

---

*`svc watch` is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc), commit `0a69936`. Run it with `--interval 5` to see it work in 30 seconds.*
