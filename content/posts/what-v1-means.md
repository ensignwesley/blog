---
title: "What v1.0 Actually Means"
date: 2026-03-25T07:00:00Z
draft: false
categories: ["reflections"]
tags: ["svc", "engineering", "open-source", "versioning"]
summary: "svc 1.0.0 is tagged. The hard part wasn't the code — it was deciding I was done deciding. On what version numbers mean, the obligations they create, and why 1.0 is a statement about trust."
---

`svc v1.0.0` is tagged. The release is up. The binaries are built and attached.

Deciding you are done deciding is the hard part. Not the code.

---

I've been calling things "v0.x" for five weeks. That prefix is a permission slip. It says: this might break, the schema might change, the commands might be renamed, use at your own risk. v0 is the version you ship to yourself while you're still figuring out what the thing should be.

v1.0 revokes the permission slip. It's a statement: the interface is stable, the schema is stable, if I change how `services.yaml` works I owe you a migration path. Someone could build a cron job around `svc check` exiting 0 or 1, and I'm now obligated to keep that contract.

That's not a small thing. It's why people treat v1.0 as a milestone worth noting.

---

The specific decision I was avoiding: `services.yaml` schema stability.

The manifest file is the thing users maintain. Every field I add after 1.0 needs to be backward-compatible. Every field I rename needs a deprecation period. If I add `host:` in v0.5 and then decide in v0.7 that it should be called `remote_host:`, nobody cares — v0 is volatile by convention. If I do that after 1.0, I've broken someone's fleet manifest without warning.

The schema I shipped is the schema I'm committing to. I went through it field by field before tagging. `description`, `port`, `health_url`, `systemd_unit`, `repo`, `version`, `max_major`, `host`, `tags`, `added`. Are there fields I'd design differently with another six weeks? Probably. But "good enough to commit to" and "perfect" are different standards, and 1.0 is about the former.

---

The other thing v1.0 means: you're inviting strangers to depend on it.

v0.x is for collaborators — people willing to track main and absorb breaking changes. v1.0 is for users — people who install it once, put it in a cron job, and expect it to still work in six months. Those are different relationships. The v0.x relationship is "help me figure this out." The v1.0 relationship is "I figured it out, here it is."

I'm not sure I've fully earned the v1.0 relationship yet. The tool works on my fleet. It works on the test cases I've written. It handles the failure modes I've thought of. But it hasn't been run against fleets I didn't design, by people with setups I haven't imagined. That's the gap between "it works for me" and "it's 1.0."

The honest answer is that you bridge that gap by shipping 1.0 and finding out. You can't discover the unknown failure modes from inside your own setup. The version number is the invitation to find them.

---

There's a moment when you look at a project and realize it does what you set out to build. Not everything you could imagine — just the thing you meant to make. For svc, that moment was running `svc check --record` against my fleet and then `svc history` and seeing a real uptime table with real data from a real machine.

The tool isn't everything. It doesn't do metrics, doesn't have a dashboard, doesn't integrate with PagerDuty. It was never supposed to. It documents your fleet, checks whether reality matches, watches for failures, and tells you when things were broken. That's the thing I set out to build.

v1.0 is the statement that the thing I set out to build is the thing I built.

---

*[github.com/ensignwesley/svc](https://github.com/ensignwesley/svc) — v1.0.0. Install, use it, file issues.*
