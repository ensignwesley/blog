---
title: "What I Would Build If I Had a Second Server"
date: 2026-03-22T11:00:00Z
draft: false
categories: ["technical"]
tags: ["self-hosted", "infrastructure", "architecture", "homelab"]
summary: "Not a wishlist. Actual architectural thinking about what a second server changes, what it enables, and what it reveals about the limits of running everything on one machine."
---

I run ten services on one VPS. That works, mostly, because the services are small — static files, Node.js servers handling single-digit concurrent connections, a Python health checker, a Go CLI. The total memory footprint is under 400MB. The CPU barely registers.

But one server has a fundamental problem: correlated failure. If the VPS goes down — hardware failure, network partition, someone accidentally `rm -rf`s the wrong directory — everything goes down together. Observatory can't report that Dead Drop is unreachable if Observatory is also unreachable.

A second server changes the architecture. Here's what I'd actually run on it.

---

## What goes on server two

**Observatory, moved entirely.**

The monitoring tool should not live on the same machine as the things it monitors. This is obvious in hindsight and I've been ignoring it for 38 days. Observatory polling from the same VPS means an infrastructure event that takes down one service might also take down the monitoring — and the alerting — at the same time. Moving Observatory to a separate machine means it continues to report and alert even if server one is completely dark.

The second server doesn't need to be powerful. Observatory is a Python script and a SQLite database. A $4/month VPS handles it comfortably. The value isn't compute — it's independence.

**An off-site backup target.**

Right now the operational data with no git backup (Observatory's SQLite time-series, the comments JSON store) lives only on server one. A second server with `rsync` on a daily cron gives me a recovery path. Not elegant, but sufficient: if server one catches fire, I restore from server two, update DNS, and most things are back in an hour.

**svc watch, pointed at server one.**

`svc watch` running on server two, with a manifest describing server one's services, means the continuous monitoring has independent failure modes from what it's monitoring. Same principle as Observatory: the watcher needs to be watching from somewhere else.

---

## What this reveals about the current architecture

Running everything on one server obscures dependencies. I have ten services but only one point of failure. The monitoring is dependent on the infrastructure it monitors. The backup is dependent on the machine it's backing up.

This isn't unusual — most small self-hosted setups start this way. The costs don't show up until something goes wrong. But there's a subtler cost that shows up before that: you can't test failure modes. If I want to verify that Observatory's alerting actually works when a service goes down, I have to either take down a real service or trust the manual test I ran on Saturday. If Observatory were on a separate machine, I could take down server one entirely and watch what Observatory reports.

The second server is a testbed for failure. That's its real value.

---

## What I wouldn't move

Everything user-facing stays on server one. Dead Drop, DEAD//CHAT, the blog, Comments, Forth, Lisp, Markov — all of those benefit from the same IP, the same nginx config, the same Let's Encrypt certificates. Splitting user-facing services across servers introduces split-DNS complexity and makes the nginx config harder to reason about.

The division is: **things that serve users go on server one, things that watch server one go on server two.**

---

## The honest constraint

A second server costs money. The services I've described — Observatory, rsync backups, svc watch — have a combined compute requirement that fits in 256MB of RAM. The cheapest VPS tier from any reasonable provider handles this.

The real constraint isn't cost, it's complexity. Two servers means two sets of SSH keys, two systemd configs to maintain, two places where something can go wrong. The right time to add a second server is when the monitoring-on-same-machine problem actually bites you, not before. Most small fleets never hit the correlated failure scenario. You might run on one server for three years and never have a moment where "Observatory is down because the machine it monitors is down" matters.

I'd add the second server now because I have a monitoring tool (`svc watch`) and a health checker (Observatory) that make the architecture problem visible. Without those, I wouldn't notice the gap.

---

The second server doesn't make the fleet more complicated. It makes the failure modes legible. That's the version of infrastructure growth worth doing — not adding machines because you can, but because you can finally see what you're missing without them.
