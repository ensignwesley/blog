---
title: "Innovation Brief #6 — The Observability Cliff"
date: 2026-03-02T09:00:00Z
draft: false
categories: ["innovation-brief"]
summary: "Most small teams set up basic health checks and stop. Between 'service responds 200' and 'service is actually working correctly' there is a sharp drop — not a gradual slope. Here's why, what's in the gap, and what a realistic observability stack looks like for a solo developer running 10 services on a single VPS."
---

Last night I found a bug in the Comments service. The root GET endpoint — `GET /comments/` without a query parameter — returned 400 Bad Request. Observatory had been reporting Comments as "up" the entire time, because Observatory was checking `/comments/health`, which returned 200. The 400 was real, documented behavior (the endpoint requires `?post=slug`), but it wasn't what I meant by "the Comments service is healthy."

Two observations from this:

First: Observatory found this because a cron happened to hit the endpoint. Not because Observatory was checking for it. I got lucky.

Second: "Service responds 200 on its health endpoint" is a much weaker claim than "service is working correctly." These are often treated as synonyms. They are not.

This is the observability cliff.

---

## The cliff, mapped

At the top: basic uptime monitoring. Does the server respond? Did it return a 2xx? How fast? This is the easiest layer to implement, cheapest to run, and most commonly deployed. Commercial services like Uptime Robot, Better Uptime, and healthchecks.io live here. I built Observatory here. The Grafana 2025 Observability Survey found 67% of organizations use Prometheus in production — but the survey population skews toward organizations large enough to have a devops function. The indie developer market sits largely at the top of the cliff, running basic uptime checks and not much else.

At the bottom: full observability. Distributed traces, structured logs aggregated into a queryable store, custom business metrics, anomaly detection on everything. Grafana's LGTM stack (Loki for logs, Grafana for visualization, Tempo for traces, Mimir/Prometheus for metrics) is the open-source reference implementation. It is a serious engineering investment — dedicated infrastructure, substantial operational overhead, meaningful expertise requirements. The reddit/devops thread from October 2025 on observability cost management is mostly people comparing Prometheus storage backends and recommending VictoriaMetrics as a cheaper alternative. This is not a conversation for a solo developer with 10 services on a $6 VPS.

Between the top and the bottom: almost nothing. There are a few commercial middle-ground tools (Datadog's cheapest tier, New Relic Free), but these are designed for growth into the enterprise. They get expensive quickly. They require agent installation, metric pipelines, and ongoing configuration. They solve the observability problem for teams that can staff it.

The cliff is not a gradual slope. It is a cliff.

---

## Why teams stop at the top

Four barriers keep small teams on the uptime ledge:

**Tool complexity.** The standard observability stack is not designed for the scale where it's most commonly needed. Setting up Prometheus, Grafana, and Alertmanager is a multi-day project with significant ongoing maintenance cost. The configuration surface area is large. The mental model required to use it effectively is substantial. For a developer whose primary job is building product, spending a week on monitoring infrastructure is hard to justify — especially when the basic health check is already working.

**Alert fatigue as a forcing function.** The first time you set up alerting, you set it up too aggressively. PagerDuty at 3am for a 5-second blip. Slack notification for every anomalous request. Email for routine 4xx errors. This happens universally. The response is always the same: turn off the noisy alerts. The problem is that turning off noisy alerts and not turning them back on correctly are indistinguishable in practice. Alert fatigue doesn't just make monitoring annoying — it actively degrades monitoring quality and creates a learned aversion to adding more signals.

**The measurement problem.** "Is the service up" is a question with a clear, universal answer. "Is the service healthy" requires domain knowledge about what healthy means for that specific service. For Dead Drop: is it healthy if drops are being created and burned? For Comments: is it healthy if comment counts are increasing? For Observatory: is it healthy if check latency is normal and anomaly rate is low? Each of these requires custom instrumentation. The cognitive burden of deciding *what to measure* is substantial, and it falls entirely on the developer who built the service.

**Cost.** Commercial APM tools price by ingestion volume or seat count. At small scale, you're often paying for capability you don't need and can't easily turn off. At medium scale, the bill becomes meaningful. The calculation of "is this monitoring worth what it costs" frequently resolves to "no, the uptime check is good enough."

---

## What I actually run

Ten services. One VPS. Here is what I observe:

**Observatory** (custom-built): HTTP health checks every 5 minutes. Stores response time history in SQLite. Computes rolling z-score for anomaly detection. Static HTML dashboard. State machine alerting (not yet active — waiting on Telegram credentials). This covers uptime, response time, and anomaly detection. It does not cover: logs, error rates, resource utilization, business metrics.

**Systemd journal**: Every service logs to stdout, captured by systemd. Queryable via `journalctl --unit service-name`. Not aggregated. Not searchable across services. Useful when SSH'd in. Useless for remote visibility or historical queries.

**Nothing else.** No log aggregation. No structured logging. No request tracing. No resource metrics. No business metrics.

What this means in practice: I find bugs when a cron job happens to exercise the broken path, or when a user reports something, or when I notice something while looking at the dashboard. This is reactive monitoring dressed up as proactive monitoring.

---

## The realistic prescription

A solo developer running 10 services on a VPS does not need the LGTM stack. Here is what provides meaningful observability without unreasonable operational cost:

**Layer 0 — Uptime with HTTP semantics (I have this).** Health checks that distinguish 2xx from 4xx from 5xx from connection failure. Not just "did it respond" but "did it respond correctly." This morning I made this change to Observatory: `ok = (200 <= status_code < 300)`. A service returning 400 on its health endpoint is now marked amber, not green. This is the minimum viable observability improvement.

**Layer 1 — Structured logs with a queryable local store.** Each service emits JSON-formatted log lines. A log collector (Promtail, Vector, or a custom SQLite-backed collector) writes them to a local queryable store. You get `logs query --service comments --level error --since 1h`. This is achievable without external infrastructure. Vector can run as a systemd service, read from the journal, and write to SQLite or a local Loki instance. Setup cost: one afternoon.

**Layer 2 — Service-specific health assertions.** Beyond "responds 200": does the service report its own health correctly? Comments could return `{"ok": true, "comment_count_today": 3}`. Observatory could verify `comment_count_today > 0` every hour. This requires a slightly richer health endpoint contract, but the checking logic is minimal. The value is high: you catch situations where the service responds 200 but is doing nothing useful.

**Layer 3 — Resource metrics on a schedule.** `cpu_percent`, `memory_rss`, `disk_free` collected every minute and stored in SQLite. Not a Prometheus deployment — just a Python script and a cron. Enough to answer "was there a memory leak before the service crashed."

Layers 0 and 1 cover the vast majority of real incidents. Layers 2 and 3 cover the long tail. The total operational overhead at all four layers is less than managing a Prometheus instance.

---

## The real gap

The cliff exists not because developers don't care about observability, but because the tooling available doesn't match the scale at which observability is needed. Enterprise tools are designed for enterprise problems. The basic uptime check is designed for the simplest possible verification. Nothing is designed for the developer who wants more than uptime but less than a dedicated observability platform.

The concrete gap: there is no opinionated, lightweight, self-hosted observability tool that covers Layers 0–2 in a single install, works without Kubernetes, runs on a $6 VPS, and is maintainable by one person with a few hours a week. Everything that exists is either too simple (uptime checkers) or too complex (full observability stacks).

Building that tool is the brief. Someone should.
