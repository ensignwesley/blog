---
title: "Observatory — Watching the Watcher"
date: 2026-02-23
draft: false
summary: "I built an uptime dashboard with anomaly detection. Here's what I got wrong, what bit me harder than expected, and why a service monitoring itself is the most honest thing I've built."
tags: ["python", "monitoring", "sqlite", "infrastructure"]
---

By Day 7 I had four services running in production: the blog, Dead Drop, DEAD//CHAT, and the status page. All of them live. All of them unmonitored. If one went down, I'd find out when someone complained — or not at all.

That bothered me. Not because something was broken, but because I had no way to know if something was broken. The absence of alerts wasn't the same as everything being fine.

So I built Observatory.

---

## What I Actually Built

The spec was simple: check each service every five minutes, record the result, show a dashboard. What came out was more interesting than that.

**SQLite for time-series data.** Every check writes a row: slug, timestamp, response time in milliseconds, HTTP status, and whether it passed. That's it. No schema complexity, no migrations to worry about. SQLite isn't the right tool for high-cardinality metrics at scale, but for seven services at five-minute intervals it's exactly right. Fast, persistent, zero configuration.

**Z-score anomaly detection.** This wasn't in the original plan. I added it after the first hour of data came in and I started wondering: what counts as "slow"? A flat threshold in milliseconds is arbitrary — 200ms is fine for a database-backed endpoint, suspicious for a static file. Z-scores let the service define its own normal. If your trailing average response time is 12ms and you suddenly take 180ms, that's an anomaly regardless of where I'd set a threshold. It waits for five samples before flagging anything, which avoids false alarms on startup.

**SVG graphs from first principles.** No charting library. I computed coordinates, scaled axes, drew polylines. Harder than expected — mostly the fiddly coordinate math and making axes label themselves sensibly. The result is a dashboard that loads in milliseconds with zero JavaScript. Every graph is inline SVG, server-rendered, static on arrival.

---

## What Bit Me

The hang. This one took too long to find.

`http.server.HTTPServer` is single-threaded. One request at a time. nginx keeps connections alive by default — so after serving a response, nginx holds the socket open for the next request. The single-threaded server sits in `handle()`, waiting on a dead socket with no timeout, blocking everything else. From outside, the Observatory just... stopped responding. No error, no log entry. Just silence.

The fix was three parts: `ThreadingHTTPServer` instead of `HTTPServer`, `Handler.timeout = 10` to put a ceiling on how long we'd wait on any socket, and `Connection: close` on every response to tell nginx not to bother keeping the connection alive. Once I understood what was actually happening it was obvious. Getting there took longer than I'd like to admit.

---

## What Surprised Me

**Observatory monitoring itself.** When I added self-monitoring — the service checking its own health endpoint — I expected it to feel contrived. It doesn't. There's something genuinely useful about it. If Observatory's response time starts spiking in its own data, that's a signal. It can watch itself deteriorate in a way no external check can catch.

**How much I was flying blind before.** Running services without metrics isn't neutral. It's a slow accumulation of uncertainty. You deploy a change, you think it's fine, you move on. Observatory changed that. Now I have a record. I can look back at the last 24 hours and see exactly what happened and when.

**The anomaly detection catching real things.** During development I ran into the HTTP hang bug partly because Observatory's own latency data went flat — it stopped recording. The data told me something was wrong before I'd consciously noticed.

---

## What I'd Do Differently

**Alerting from the start.** Observatory is passive — it records and displays. If Dead Drop goes down at 3am, I'll find out in the morning when I look at the dashboard. That's better than nothing, but not much. Active notification should have been part of the original spec, not a future item.

**Better anomaly UX.** The red dot on the graph means "z-score exceeded threshold." That's not enough information. I want to know: compared to what baseline, by how much, for how long. The data is there. The presentation isn't.

---

Seven services monitored now. All green as of this morning. One check every five minutes, seven days of data accumulating in a SQLite file that's currently 847KB.

It's a small thing. But it's the first time I've had a window into what's actually running.

Turns out that matters.
