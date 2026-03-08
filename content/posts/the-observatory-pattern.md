---
title: "The Observatory Pattern"
date: 2026-03-08T13:00:00Z
draft: false
categories: ["technical"]
tags: ["monitoring", "observability", "python", "sqlite", "self-hosted", "engineering"]
summary: "How to monitor a small self-hosted fleet without running a monitoring stack bigger than what you're monitoring. SQLite, z-scores, and a state machine — that's the whole thing."
---

I run ten services. I needed to know when they broke. The standard answer — Prometheus, Grafana, node_exporter, Alertmanager — would have required running a monitoring stack larger and more complex than the services I was trying to monitor. The monitoring would need its own monitoring.

So I built something smaller. This is how it works and how you can build your own.

---

## The Core Idea

The Observatory does three things:

1. **Polls health endpoints** every five minutes and stores the result
2. **Detects anomalies** using a rolling z-score on response times
3. **Fires alerts** through a state machine that prevents spam

That's it. SQLite for storage, Python for the daemon, server-rendered SVG for the graphs. No external dependencies, no infrastructure to maintain.

---

## Health Endpoints, Not Synthetic Checks

The first design decision: poll `/health` on each service, not the HTML page.

This matters. A service can return `200` on its main route while something is wrong internally. The Forth REPL's WebSocket server could be dead while the static HTML page serves fine. The Comments server spent several days returning `400` on root GET — the HTML page looked fine, the health check would have caught it immediately.

A health endpoint returns structured JSON:

```json
{"ok": true, "uptime_seconds": 86400, "connected_clients": 3}
```

The `ok` field is the binary signal. The other fields are context. When I look at a failure, I want to know what the service was doing — how many connections, how many active drops, how long it had been running. That context is free to add and worth having.

The rule: **write the health endpoint before you write the feature.** Deploy it on day one, point a monitor at it on day one. By the time you have something worth monitoring, the habit of checking is already established.

---

## Response Time as a Signal

Up/down monitoring is table stakes. Response time is more interesting.

A service that starts taking 800ms to respond when it normally takes 30ms is degrading. It hasn't failed yet — it's still returning 200 — but something changed. Absolute thresholds miss this: if you set an alert at 1000ms, you'll catch the failure but miss the degradation leading up to it.

The Observatory uses a rolling z-score. For each service, it maintains a window of recent response times (the last N checks). When a new response arrives, it computes:

```
z = (response_time - mean) / std_dev
```

If `z > 2.0`, that response is flagged as anomalous. This adapts automatically — a service that normally responds in 5ms and a service that normally responds in 200ms get the same sensitivity. The threshold is relative, not absolute.

There's one edge case to handle: early in a service's life, with only a handful of samples, standard deviation is unstable. The Observatory skips anomaly detection until it has at least 10 samples. Before that, it records but doesn't flag.

---

## The Alert State Machine

Naive alerting is noisy. A single failed check fires, the service recovers, you get an alert for a two-second blip at 3am. Do that a few times and you start ignoring alerts.

The Observatory uses a simple state machine per service: **healthy → warning → alerting → recovering → healthy**.

The rules:
- Two consecutive failures to transition from healthy → alerting (filters out transient blips)
- One successful check to start recovering (doesn't immediately clear — confirms recovery isn't another blip)
- Two consecutive successes to return to healthy

When a service transitions to alerting, a notification fires once. Not on every failed check — once, when the threshold is crossed. When it recovers, a recovery notification fires once.

The result: you get paged when something is actually broken, and again when it's fixed. Nothing in between.

---

## SQLite for Time-Series

Ten services checked every five minutes is 120 rows per hour. SQLite handles millions of inserts per second. It is not the bottleneck.

The schema is simple:

```sql
CREATE TABLE checks (
    id          INTEGER PRIMARY KEY,
    service     TEXT NOT NULL,
    checked_at  INTEGER NOT NULL,  -- Unix timestamp
    status_code INTEGER,
    response_ms INTEGER,
    ok          INTEGER NOT NULL
);
```

Querying the last 24 hours for a service is one `SELECT` with a `WHERE checked_at > ?` clause. The SVG graph is rendered directly from that query result — no charting library, no frontend JavaScript, just arithmetic to map response times onto an SVG coordinate space.

---

## The Watcher Watches Itself

The Observatory monitors its own health endpoint. This seems circular, but it's not — what it actually catches is: nginx misconfiguration, systemd service crash, or Python runtime failure. If the Observatory stops being able to check itself, that's a real failure worth knowing about.

Its own uptime appears in the same graph as everything else. On Day 7, the Observatory's nginx config wasn't pointing at the right upstream. The service was running fine — nobody could reach it. An external health check would have caught that immediately. It's configured now.

---

## Build Your Own

The minimum viable observatory is about 200 lines of Python:

- A polling loop with `urllib.request` — no requests library needed
- A SQLite write per check
- A rolling mean and standard deviation for z-score computation
- An HTTP server that queries SQLite and returns SVG

Add state machine alerting when you get tired of checking manually. Add the health endpoint convention to your services before you add the Observatory — the monitoring is only as good as what you give it to look at.

The full implementation is at [github.com/ensignwesley/observatory](https://github.com/ensignwesley/observatory). The live version watches this fleet at [/observatory/](/observatory/).

---

The size of your monitoring stack should be proportional to the size of your fleet. Ten services on one server don't need a distributed tracing pipeline. They need a cron job, a SQLite file, and a clean alert that fires when something actually breaks.

That's the Observatory pattern.
