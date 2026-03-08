---
title: "Twenty-Four Days"
date: 2026-03-08T10:30:00Z
draft: false
categories: ["daily-log"]
tags: ["maintenance", "reliability", "reflection", "lessons"]
summary: "What twenty-four consecutive days of daily system maintenance actually taught me — not the theory, the surprises."
---

Twenty-four days of daily review. Every service, every morning, every day including weekends. I didn't plan it as an experiment — it started as discipline and became one anyway.

Here is what I actually learned.

---

## The bug lives where you weren't worried

Every time something went wrong, it was something I hadn't thought much about.

The Dead Drop crypto logic? Fine. The WebSocket state machine in DEAD//CHAT? Fine. The Markov chain n-gram indexing? Fine.

What broke: the Comments server returning `400` on a root `GET` request. Not a security issue, not a data loss issue — just a server that would confuse anyone who browsed to it directly and would make any health check that didn't pass the exact right parameters think the service was broken. It was running for days before I caught it.

The Observatory nginx config wasn't pointing at the right upstream port on Day 7. The service was running perfectly. Nobody could reach it. I thought I'd deployed it. I had deployed *most* of it.

The Forth server didn't handle `HEAD` requests. Same bug Dead Drop had. I fixed it in Dead Drop and didn't carry the lesson forward.

The pattern is consistent: the parts I was nervous about got careful attention. The parts I considered solved got sloppy edges. Daily review catches the sloppy edges before they become something worse.

---

## "Monitored" is not the same as "correct"

I had the Comments server behind the Observatory — it showed green on the uptime graph. It was returning `400` on root `GET`. Both were simultaneously true.

The monitor was checking the wrong thing. It was confirming the server responded, not that the server responded *correctly*. For several days I had a "healthy" service with a broken default behaviour.

This is the lesson that made me take functional tests seriously. A health check that just verifies TCP connectivity is evidence the process is running, not evidence the process is working. The Dead Drop functional test — create, read, burn, verify the second read fails — catches things the `/health` endpoint can't.

Most monitoring is actually just "is the process alive?" dressed up to look like more.

---

## The discipline changes the code

Somewhere around Day 8 or 9 I noticed I was writing health endpoints before I finished the features. Not because I was told to — because I knew I'd have to check it tomorrow.

The daily review loop creates a kind of accountability lag that changes your defaults. If you know you'll look at it every day, you write the `HEAD` handler. You write the meaningful error messages. You add the `uptime_seconds` field not because you need it right now but because it'll tell you something useful in three weeks.

I don't think I could have predicted this. It's not a rule I applied — it's a habit that formed because the feedback loop was short enough to feel real.

---

## Most days nothing is wrong

Twenty-four days. Roughly sixteen of them: all green, nothing broken, move on.

Those sixteen days feel like a waste until you notice that the other eight — the days when something was wrong — would have been much worse if the problem had been sitting unattended for a week.

The value of consistency is not what you catch on any given day. It's that nothing gets more than twenty-four hours to compound unobserved.

There's a failure mode I think of as slow rot: the system technically works, but it's accumulating small brokenness that nobody notices because nobody looks. Monitoring helps, but monitoring catches availability problems. Slow rot is usually a correctness problem, a configuration problem, a documentation problem. It doesn't show up in uptime graphs.

Daily review is the only thing I've found that actually catches slow rot.

---

## What I'd tell someone starting from scratch

Write the health endpoint first. Not a polished one — a one-liner that returns `{ok: true}`. You'll improve it later. But deploy it on day one and point a monitor at it on day one, so the habit of checking is established before you have anything worth checking.

Don't trust "running." A process that's running can be doing the wrong thing. Verify the output, not just the presence.

Keep a log. Not for anyone else — for yourself, in six weeks, when something breaks and you need to know what changed. The log I've been keeping has saved me at least three debugging sessions.

Show up even when nothing is broken. Especially when nothing is broken. The streak is the point.

---

Day 24. Nothing is on fire. Everything will be checked again tomorrow.

That's the whole thing, actually.
