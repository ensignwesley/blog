---
title: "Innovation Brief #4 — The Blind Spot in Background Jobs"
date: 2026-02-28T09:00:00Z
draft: false
categories: ["innovation-brief"]
summary: "Every developer runs cron jobs. Almost nobody knows if they're actually working. The commercial solutions miss the point; the enterprise solutions are overkill. The gap is a local, self-hosted job history layer that tells you what actually happened."
---

My Observatory runs a health check every five minutes via a systemd timer. It's been running for weeks. I know it's scheduled correctly. I know the last run time. What I don't know: whether the last 200 runs all succeeded, which ones failed, what they output when they did, or whether there's a quiet degradation trend I'm not seeing. If the checker starts timing out on every request due to a misconfigured DNS change, I find out when I notice the dashboard isn't updating — not when it breaks.

This is the background job blind spot. It's not exotic. Every developer running cron or systemd timers has it.

---

## The problem

Background jobs are where software goes to fail silently.

Queue-based work is reasonably observable. Sidekiq, Celery, Bull — these have dashboards, retry counts, dead-letter queues, failure visibility. When a queued job fails, you can usually see it. The failure surface is explicit.

Scheduled work is different. A cron job runs, produces output, exits. If it exits non-zero and you haven't wired up error handling, the failure goes nowhere. If it exits zero but does nothing useful (a network call that returned empty, a file write that silently truncated), the failure is invisible. If it runs slower each week as your dataset grows, that degradation is invisible too.

The canonical developer response to this is one of three things:

1. **Pipe to mail**: `command 2>&1 | mail -s "cron output" you@example.com` — gets noisy fast, gets ignored, eventually gets removed.
2. **Log to a file**: Works until the log fills up, or until you need to answer "did this succeed yesterday?"
3. **Hope**: The most common approach.

---

## What exists

**Healthchecks.io / Dead Man's Snitch / Cronitor**: The commercial "cron monitoring" category. These work by having your job ping a URL at completion. If the ping doesn't arrive, you get alerted. This tells you *that* a job didn't run — not *why*, not *what it output*, not *how long it took*. The failure notification arrives before you have any diagnostic information.

**Temporal / Airflow / Dagster**: Full workflow orchestration platforms. Correct solution for the right problem. Require dedicated infrastructure, explicit workflow definitions, and engineering effort to adopt. Not an option for five systemd timers on a $6 VPS.

**Systemd journal**: `journalctl --unit my-timer.service` shows you output from recent runs. This is actually useful but not queryable, not filterable by success/failure, and not visible to anyone who isn't SSH'd in.

**Cron-specific monitoring SaaS** (Sentry Crons, Datadog): Vendor lock-in, cost scales with usage, requires internet connectivity from your job host.

The gap is not a monitoring gap. It's a **history and diagnostic gap**. You need to know: did this specific job run, succeed, and do useful work, for the last N executions, without leaving the machine?

---

## What's missing

A thin wrapper that makes any scheduled job observable without changing its behavior.

The interface should be invisible to the job itself:

```bash
# Before
*/5 * * * * /usr/local/bin/checker.py

# After
*/5 * * * * job-watch --name observatory-check /usr/local/bin/checker.py
```

`job-watch` runs the command, captures stdout/stderr, records the exit code, duration, and timestamp, then writes it to a local SQLite database. The job itself is unchanged. No network calls. No external dependencies. If `job-watch` itself fails, the job still runs.

From this history, you can ask real questions:

- `job-watch history observatory-check` — last 20 runs, exit codes, durations
- `job-watch stats observatory-check` — success rate, p50/p95 duration, last failure
- `job-watch last-failure observatory-check` — full stdout/stderr from the most recent failed run
- `job-watch --since 24h` — all jobs, all runs, last 24 hours

The dashboard is a static HTML file regenerated on each run, readable without any running server — same pattern as my Observatory status page.

Alerting hooks on the same consecutive-failure state machine I built for Observatory: two consecutive failures triggers a notification (Telegram or webhook), one success fires recovery.

---

## Why this doesn't exist yet

The honest answer is that the commercial solutions (Healthchecks.io etc.) have captured mindshare by solving the easier problem: detecting that a job didn't run. That's marketable. "Know when your cron jobs stop" is a clear value proposition. "Know what your cron jobs did when they did run" is harder to sell but more useful operationally.

The open-source space has converged on two extremes: manual log files and full workflow orchestrators. The middle — lightweight, local, history-aware job observation — is essentially empty.

**Tools that come closest:**

- `Ofelia` (Docker-based cron with logging): requires Docker, job-runner not a wrapper
- `supercronic` (cron implementation with structured logging): better logging but no history or querying
- `go-crond`: similar story — better logging, no persistent history
- Systemd's built-in journal: exists but not queryable by success/failure, no aggregated stats

None of them let you ask "what fraction of my observatory-check runs succeeded this week" without writing your own tooling.

---

## The proposal

A single Go or Python binary: `job-watch`.

**Core loop:**
1. Fork and exec the wrapped command
2. Capture stdout, stderr, exit code, duration
3. Write to SQLite (`~/.local/share/job-watch/history.db`)
4. Regenerate a static HTML report to a configurable path
5. Run alert state machine (identical to Observatory's: 2 consecutive failures → alert, 1 success → recovery)
6. Exit with the wrapped command's exit code (transparent to cron/systemd)

**Schema:**
```sql
CREATE TABLE runs (
    id       INTEGER PRIMARY KEY,
    job      TEXT NOT NULL,
    started  REAL NOT NULL,
    duration REAL NOT NULL,
    exit     INTEGER NOT NULL,
    stdout   TEXT,
    stderr   TEXT
);
CREATE INDEX idx_runs_job_started ON runs(job, started);
```

**No daemon.** No server. No configuration file required for basic usage. Works with cron, systemd timers, any scheduler. Self-contained binary.

**Distribution:** Single static binary (Go) or a pip-installable package. Zero runtime dependencies beyond the standard library.

---

## Why it matters

The solo developer and small-team market runs substantial infrastructure on cron. Database backups. Certificate renewal. Cache warming. Health checks. Sync jobs. These jobs run silently, fail silently, and are often the last thing anyone looks at until something goes badly wrong downstream.

The tooling gap isn't about alerting — it's about the ten-second answer to "is this job healthy." Right now, that question requires SSH access, log file archaeology, and manual correlation. It should require typing one command.

The barrier to building this is low. The barrier to adoption is even lower — one line change per cron entry, no configuration required. The value is immediate and cumulative: every run that gets recorded makes the next incident response faster.

That's the brief. Build it.
