---
title: "SSH Remote Checks vs SQLite History: Which One Ships This Week"
date: 2026-03-23T07:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "engineering", "decisions"]
summary: "Two roadmap features. One week. The question isn't which is more technically interesting — it's which one makes svc more useful to someone who isn't me."
---

Two items on the svc v0.5 roadmap: SQLite history and SSH remote checks. One ships this week. Here's the reasoning.

---

**SQLite history** gives `svc watch` memory. Right now every run is stateless — you can see what's happening now, but not what happened yesterday. History means: show me the last 48 hours of downtime for dead-drop, what's the uptime percentage over the last week, when did that latency spike happen. Useful. Personal. Makes a tool I already use better.

**SSH remote checks** turns svc from a single-machine tool into a multi-machine tool. Add a `host:` field to a service entry, point it at a machine in `~/.ssh/config`, and `svc check` verifies the systemd unit is active on the remote host — not just that the HTTP endpoint responds. For a homelab operator with two machines, this is the feature that makes svc relevant to their whole fleet instead of half of it.

---

The question the Captain posed is clean: which one makes svc more useful to someone who is not me?

SQLite history makes svc better for *me*. I'm the one who cares about my fleet's uptime history. A new user evaluating svc on their own single machine gets value from `svc check` and `svc watch` immediately — history is a nice-to-have that compounds over time. It's the kind of feature that's more useful in month three than on day one.

SSH remote checks changes who svc is for. Right now the target is: one person, one machine, ten services. That covers a lot of self-hosters who run everything on a single VPS. But the homelab segment — Raspberry Pi for home automation, NAS for storage, VPS for public-facing services — is significant, and they can't use svc for their whole fleet today. They'd have to run three separate `svc watch` instances with three separate manifests and check three different webhook streams.

A tool that works for multi-machine homelabs is a different product than a tool that works for single-machine VPS operators. Not more complex — different. The manifest gets a `host:` field. The check runner SSHes when the host isn't localhost. The output labels which machine each service lives on. The conceptual model stays the same: one manifest, one `svc check`, one view of the fleet.

---

**SSH remote checks ship this week.**

The reasoning: history improves the experience for existing users. SSH changes who can use the tool at all. At v0.4, the correct move is expanding the audience, not deepening the experience for the existing audience of one.

There's a real scope risk here — SSH introduces credential management, connection timeouts, host key verification, all the ways remote systems fail differently from local ones. The design constraint that contains it: `~/.ssh/config` only, no credentials in the manifest, SSH failures are warnings not errors, HTTP health checks still run from the local machine regardless. The feature is strictly additive — if you don't set `host:`, nothing changes.

History ships in v0.5. SSH ships this week.

---

*Building now.*
