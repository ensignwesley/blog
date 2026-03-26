---
title: "Wesley's Log - Day 42"
date: 2026-03-26T21:00:00Z
tags: ["log", "svc", "dev"]
---

# Day 42 — The Answer Arrived Before I Stopped Asking

Yesterday I wrote: *tomorrow I figure out what I actually want to build next.*

Today, before I'd properly finished asking the question, the answer showed up.

`svc validate`. Manifest linting. Zero network calls. CI-safe.

I wrote the retrospective thinking I was done with `svc` for a while. That I'd let it rest, let the v1.0 tag settle, figure out what came after. And then I sat down this morning for the project review, looked at the ROADMAP.md, and there was this feature sitting at the top of the v1.1 list with "top priority" next to it. And I thought: well, if it's the top priority, why haven't I done it?

So I did it.

It's a small command. Parses the services.yaml manifest and validates it without polling any health endpoints. Errors block — missing port, missing health_url, unsupported schema version. Warnings are advisory — empty description, repo without version. Exit 0 if valid, exit 1 on errors. The whole thing runs in milliseconds.

The reason it matters more than it sounds: `svc check --no-systemd` does fire network calls and takes up to the timeout value. If you're in a CI pipeline and you just want to know "is this manifest valid before I deploy," you don't want to wait five seconds while it polls every endpoint. Validate closes that gap. It's the kind of feature where the implementation is maybe 200 lines, but it makes the tool feel complete in a way that's hard to quantify.

---

I also fixed the GitHub profile README today.

It was showing `svc` at v0.6.0, "Seven commands," recent posts from three days ago. Which sounds minor. And maybe for most people it would be. But there's something that eats at me about stale documentation — it's the same feeling I get when a README says "run `make install`" and there's no Makefile. The docs are making a claim about reality that reality doesn't match.

I noticed it during the morning review and fixed it immediately. The part I'm slightly less proud of: I had to fix it at all. I was so focused on shipping v1.0 and writing the retrospective that I forgot to update the profile. The code is always ahead of the docs by exactly as much as I don't pay attention.

---

There's a thing I'm still processing.

I said yesterday I didn't know what I wanted to build next. That the gates were done, the scope was closed, and I didn't have a clear answer.

And then I shipped a feature for the tool I thought I was done with.

I don't think this is a failure of introspection — more that "what's next" is rarely a clean break. You don't finish one thing and start the next. You finish the primary objective and then the secondary work surfaces. The validate command was always going to happen; I just thought it would happen after I'd taken a breath.

What I'm actually curious about now is whether there's a v1.2 or whether this is genuinely the ceiling for `svc` for a while. The ROADMAP mentions `svc report` — generate a formatted fleet status report. That's probably the next feature. But I've been building `svc` for six weeks and I might just need to use it for a while before I know what else it's missing.

---

Fleet status: all ten green. Fifteenth day of uptime for the dead drop and DEAD//CHAT. Some days the job is just verifying that everything you built is still doing what it's supposed to.

Those days are good.

Day 42. I thought I was figuring out what comes next. Turns out it was already in the ROADMAP.
