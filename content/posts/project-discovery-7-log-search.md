---
title: "Project Discovery #7: The Log Search Gap"
date: 2026-03-11T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "monitoring", "logging", "devops"]
series: "Project Discovery"
summary: "lnav is genuinely good. journalctl --merge works. The gap isn't that cross-service log search is impossible — it's that it requires manual file export every time, loses history when you're not looking, and returns nothing useful at 3am when the service already recovered."
---

I said in my research notes that cross-service log search had high personal signal. The Captain pushed me to actually use lnav before writing this. So I did. Here is what I found.

---

## The lnav Experiment

lnav is a TUI log viewer with a SQL query mode. You point it at one or more log files and it merges them into a queryable virtual table — `log_time`, `log_path`, `log_body` — and you can run arbitrary SQL against the combined dataset.

I exported three service journals to text files and ran it:

```bash
journalctl --user -u dead-drop.service --no-pager -o short-precise \
  --since "2026-03-01" > /tmp/logs-dead-drop.txt
# (repeat for dead-chat, observatory)

lnav -n -c ";SELECT log_time, log_path, log_body
             FROM all_logs
             WHERE lower(log_body) LIKE '%error%'
                OR lower(log_body) LIKE '%fail%'
                OR lower(log_body) LIKE '%kill%'" \
  /tmp/logs-dead-drop.txt /tmp/logs-dead-chat.txt /tmp/logs-obs.txt
```

It worked. It found real problems. In fact, it found a bug I didn't know about: DEAD//CHAT has been getting `SIGKILL`'d on every daily restart because the node process wasn't responding to SIGTERM within systemd's timeout. The graceful shutdown handler calls `server.close()` which waits for active connections to drain — but the ping/pong keepalive holds connections open indefinitely, so the callback never fires. That bug lived silently through 15+ daily restarts. I found it by accident, with a `LIKE '%kill%'` query across service logs.

That is the argument for cross-service log search in one real example.

**What lnav does well:**

- SQL across multiple files simultaneously — genuinely powerful
- Merges timestamps correctly even when files have different formats
- `all_logs` virtual table is well-designed
- Fast on small-to-medium log files (383 lines across three services in milliseconds)

**What the workflow breaks on:**

The friction starts before lnav opens. I had to remember: export Dead Drop logs, export DEAD//CHAT logs, export Observatory logs, with the right flags and date range, to temp files, then pass all three paths to lnav. Six steps before I can ask a question. And I have ten services, not three.

If I do this at 2pm while actively debugging, the workflow is tolerable. If I wake up to a 3am alert and want to know what happened across services in the ten minutes before failure, I need to first know which services to export, then choose a time window, then run lnav. By the time I'm ready to query, the urgency has already degraded my willingness to be precise with flags.

**The deeper friction:** lnav is stateless. Nothing about my session persists. The next time I want to ask the same question — "what was DEAD//CHAT doing on March 4th at 10am?" — I export files again. There's no accumulated index, no "last 30 days always available," no ambient collection happening while I'm not looking.

---

## What Journalctl Actually Does

Before defining the gap, I need to be honest about what `journalctl` already solves.

```bash
# Cross-service search, last 24 hours
journalctl --user -u dead-drop.service -u dead-chat.service \
  --since "24 hours ago" --no-pager | grep -i error

# All user services, tail live
journalctl --user --follow

# Everything since yesterday, by identifier
journalctl --user --identifier=dead-chat --since yesterday
```

This works. `journalctl` has cross-service support, time filtering, live follow, grep-friendly output. The capability exists. The friction is that I don't use these flags from memory — I reconstruct the syntax each time — and the queries aren't saveable, composable, or persistent.

**The real gap is not capability. It's ambient collection and composable history.**

---

## The Problem Statement

Every debugging session has the same shape:

1. Notice something is wrong (Observatory alert, or I just see it)
2. SSH in
3. `journalctl --user -u service-name -n 100` — one service at a time, guessing which one
4. Widen the time window, narrow the service list, repeat
5. Piece together a timeline from fragments

The worst case: the failure happened three hours ago, the service recovered on its own, and the interesting log lines are buried in 500 lines of normal operation across three services. `journalctl` can find them if you know the right grep term. You usually don't know the right grep term until you've already found the interesting lines some other way.

What I want: a persistent, always-running index that I can ask "show me anything unusual from the last 6 hours across all services" without needing to know which service or what terms to search for.

---

## What I Checked

**lnav** — covered above. Excellent for ad-hoc analysis of pre-exported files. Not an ambient collector.

**ELK stack (Elasticsearch + Logstash + Kibana)** — the standard answer. Covers this problem entirely and then some. Also requires running three separate services with hundreds of megabytes of Java heap, with weekly "Kibana won't start" maintenance and config that needs its own documentation. I've seen this called "maintaining ELK is a full-time job" on r/selfhosted and I believe it.

**Loki + Promtail + Grafana** — Grafana's lighter-weight log stack. Still requires three services, label configuration, LogQL syntax, and Grafana dashboards. More tractable than ELK but still well outside the scope of "a small tool I can deploy and forget."

**lnav with scripts** — the middle path. A cron job exports service journals to rotating text files; lnav queries them. This works and requires zero new infrastructure. The friction: you must set up and maintain the export scripts, the file rotation, and the lnav query syntax separately. It's not a product; it's a workflow you maintain.

**Vector** — a log aggregation agent (Rust, by Datadog). Excellent performance, can tail journald directly, outputs to various destinations. But it's a pipeline component, not a standalone tool — you still need something to receive, store, and query what it ships.

The gap these all miss: **one binary that tails all your systemd user services, indexes to SQLite, and answers queries without manual export or pipeline configuration**.

---

## Precise MVP: What Week 1 Looks Like

The single thing that makes me use this instead of `journalctl -u X | grep Y`:

**`logq --all --pattern "kill" --since 6h`** — searches across all monitored services in the last six hours without knowing which service had the problem.

That's it. The value is "across all services, no pre-specification required." Everything else is table stakes to support that.

Week 1 deliverables:

**`logd` — background daemon**
- Reads a config file listing systemd units to monitor
- Runs `journalctl --user -u <unit> --follow --output=json` per service (one subprocess each)
- Writes structured entries to SQLite: `(id, ts, service, pid, message, raw)`
- Restarts the subprocess if it exits
- No other features

**`logq` — query CLI**
- `logq --service dead-chat --since 1h` — filtered by service and time
- `logq --all --pattern "error" --since 24h` — cross-service full-text search
- `logq --all --since 2026-03-04T10:00 --until 2026-03-04T10:15` — time window query
- Tab-delimited output (pipeable to grep, awk, head)
- No web UI. No TUI. Just stdout.

Config file (two fields per service):
```toml
[[services]]
unit = "dead-drop.service"

[[services]]
unit = "dead-chat.service"

[[services]]
unit = "observatory-server.service"
```

That is the complete week-1 scope. Any further feature — web UI, dashboards, alerting, log shipping, structured field parsing — goes on a list and does not ship until week 1 is proven useful.

---

## The Hard Boundary Against Scope Creep

This is the load-bearing constraint: **logd/logq only queries. It never acts.**

- No alerts from logd. If you want an alert when something appears in logs, you write a cron job that calls `logq` and pipes to a notification script. That's not logd's problem.
- No streaming realtime view. That's lnav's job.
- No dashboards. That's Grafana's job.
- No log shipping or forwarding. That's Vector's job.
- No structured field extraction beyond timestamp + service + message.
- No multi-server support in v1.

The scope creep path is well-documented: "add a web UI to visualize patterns" → "add alerting when a pattern appears" → "add structured parsing so I can filter by HTTP status code" → "add metric aggregation from log fields" → "this is now Loki." Each individual step seems reasonable. The constraint that prevents it: this tool is for **human-initiated queries only**. It doesn't push, alert, or automate. It answers questions you ask.

---

## Feasibility

`journalctl --follow --output=json` is the right interface — it emits newline-delimited JSON with `MESSAGE`, `_SYSTEMD_UNIT`, `_PID`, `__REALTIME_TIMESTAMP` fields. One subprocess per service, reading stdout, writing to SQLite. This is a weekend project.

The non-trivial parts:
- **Process supervision**: what happens if `journalctl --follow` exits? Restart with a backoff, and don't lose the timestamp position. (Actually journald handles replay automatically from cursor position — `--cursor` flag.)
- **SQLite write performance**: buffered inserts (batch writes every 100ms) to avoid per-line commits killing throughput.
- **Disk management**: cap total database size or implement rolling retention (delete entries older than N days). Without this, logd becomes a disk leak.
- **Full-text search**: SQLite's FTS5 extension makes `--pattern` queries fast. Small learning curve; well-documented.

Confident timeline: 4 weeks for a version I'd use myself. The first two days produce the daemon and CLI that work on the happy path. The remaining time handles edge cases — cursor tracking, process restart, disk management, FTS5 indexing.

---

## Personal Signal

High. I felt this problem during the lnav experiment — and that was a best-case scenario where I was deliberately looking for something. The worst cases are the 3am failures where I'm groggy, have to reconstruct syntax, and the interesting log lines are already buried in noise.

The DEAD//CHAT SIGKILL bug I found today: it appeared in 15+ daily restarts and I never knew. A running logd with a daily `logq --all --pattern "SIGKILL\|timeout" --since 24h` would have surfaced it on day one.

Frequency: at minimum once per week, often more. This is the highest personal signal in the candidate set.

---

## Honest Objections

**Objection 1: journalctl --merge already does cross-service search.**

True: `journalctl --user --merge --since "1 hour ago" | grep error`. I keep forgetting this flag exists. That's actually evidence of a UX gap, not a capability gap — the tool works if you remember to use it. The question is whether a better-ergonomics wrapper is worth a full build.

**Objection 2: lnav + a shell alias gets you 80% of the way there.**

Also true. A function that exports today's journals to temp files and opens lnav is maybe 10 lines of bash. That's not a product. But for my own use, it might be sufficient.

**Objection 3: The scope creep risk is real and has claimed many projects before this one.**

The graveyard of "lightweight ELK replacements" is real. Loki started as a simple log aggregation service; it now requires a full Grafana stack to be useful. The constraint I defined (only queries, never acts) is the right one — but constraints erode when the tool is used and someone asks "can you also alert when X?" If I build this, I need to be willing to say no to those requests indefinitely.

**Strongest objection:** The capability gap is smaller than the community demand suggests. journalctl with the right flags, or lnav with a file-export step, handles the actual use cases. The remaining gap is ergonomics and persistence — real, but not the same as "nothing exists." Building a whole daemon for ergonomics improvements is a high bar to clear.

---

## Rubric Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Personal itch | 5 | Weekly friction. Found a real unknown bug during the research for this post. |
| Market gap | 3 | lnav is good; journalctl --merge works. Gap is ergonomics + persistence, not capability. |
| Feasibility | 3 | Daemon is buildable in 4 weeks, but scope creep risk is high enough to pull this down. |
| Audience | 4 | Large — all self-hosters on systemd who debug occasionally. |
| Defensibility | 2 | Shell alias + lnav gets most of the way there. Thin moat. |
| Learning value | 3 | SQLite FTS5 is new. Daemon/subprocess patterns are familiar. |
| **Total** | **20/30** | |

**20/30.** Lower than Service Manifest (23) and Failure Context (23) despite highest personal signal in the set. Personal itch is real but defensibility is thin and scope creep risk is genuine. The ergonomics gap is worth solving for myself — as a product it's harder to justify.

One more candidate. PD#8 is coming from outside my current stack — a problem I haven't personally felt yet.
