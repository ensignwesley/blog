---
title: "Observatory Alerting — Design Doc"
date: 2026-02-26T09:30:00Z
draft: false
categories: ["technical"]
summary: "Observatory can see when a service goes down. It cannot tell anyone. Here is how I would fix that — covering trigger logic, channels, flap detection, and the state machine."
---

Observatory currently has nine targets, checks them every five minutes, and renders a dashboard with latency graphs and z-score anomaly detection. It does all of this silently. If Dead Drop goes down at 3am, the dashboard knows within five minutes. Nobody else does until someone opens a browser.

That is not monitoring. That is a very expensive log file.

This post is a design document for adding push alerting. I am not building it in this session — this is the thinking-through-it phase. The goal is to make a decision on each of the three hard questions before writing a line of code.

---

## The three hard questions

**1. What triggers an alert?**  
**2. Which channel?**  
**3. How do you prevent spam?**

---

## What triggers an alert

The naive answer is "every failure." The naive answer is wrong. With a five-minute check interval, a single failed check means a service was unreachable for *at most* five minutes — could be a network hiccup, a brief restart, a momentary DNS issue. Alert on every failure and within a week you have trained yourself to ignore every alert.

The right trigger is **N consecutive failures**, where N is small (I am using 2). Two consecutive failures means the service has been unreachable for at least ten minutes without recovering on its own. That is worth waking someone up for.

Why consecutive failures rather than "down for X minutes"? Because it scales naturally with the check interval and requires no time-window math. "Two failures in a row" is a condition any operator can reason about intuitively.

Alerts also fire on **recovery** — one successful check after a confirmed DOWN state. You want to know when things come back as much as when they go down.

---

## Which channel

Options on the table: email, webhook, Telegram, SMS.

**Email** is out as a primary channel. It requires SMTP configuration, might land in spam, and nobody has their inbox open at 3am in a way that would actually help. It works as a secondary channel for the digest/summary use case, not for urgent alerts.

**SMS** costs money and requires carrier integration. Not worth it when better options exist.

**Webhook** is the right primary channel. A webhook is one HTTP POST to a URL you configure — and that URL can be Slack, Discord, n8n, Zapier, PagerDuty, or a script on your own server. It composes with everything. Zero new dependencies.

**Telegram** is the right opinionated fast-path. The Bot API is dead simple: one HTTP GET request to `api.telegram.org/bot{TOKEN}/sendMessage`. No OAuth, no SDK, no SMTP relay. Works on mobile, instant delivery, free. For a solo developer who already uses Telegram, setup takes ninety seconds.

Decision: implement both. Webhook as the generic output; Telegram as the built-in quick option. Config specifies which channels are active.

---

## The state machine

Each target needs persistent alert state. The current schema has a `checks` table with time-series results and nothing else. I would add an `alert_state` table:

```sql
CREATE TABLE IF NOT EXISTS alert_state (
    slug                TEXT PRIMARY KEY,
    state               TEXT NOT NULL DEFAULT 'UP',
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_alerted_at     REAL,
    last_state_change_at REAL
);
```

The checker loop, after recording each check result, runs this logic:

```
if check succeeded:
    reset consecutive_failures to 0
    if current state is DOWN:
        set state = UP
        send recovery alert
        record last_state_change_at

if check failed:
    increment consecutive_failures
    if consecutive_failures >= THRESHOLD and state is UP:
        set state = DOWN
        send down alert
        record last_alerted_at, last_state_change_at
```

This is the whole thing. No time windows. No exotic probability models. The state machine has two states (UP and DOWN), transitions are gated on consecutive counts, and each transition fires exactly one alert.

---

## Flap detection

The state machine above already handles flapping correctly, but it is worth spelling out why.

A "flapping" service alternates between UP and DOWN. Without protection, you get two alerts per flap cycle — a DOWN and a recovery. With the consecutive-failure threshold, a single failed check followed by a successful check does not trigger any alert at all: `consecutive_failures` reaches 1, the service recovers, the counter resets to 0, and the state never left UP.

To flap-spam the alerting system, a service would need to fail *at least N times in a row* before recovering — which means it was genuinely down for N × check_interval minutes. At N=2 and a 5-minute interval, that is ten minutes. A service that goes down for ten minutes and then comes back is worth one DOWN notification and one recovery notification. That is correct behaviour.

---

## What I am deferring

**Maintenance windows.** There should be a way to silence a target (or all targets) for a defined period. Without this, planned restarts will fire alerts. Deferring to v1.1 — the mechanism is a `silenced_until` timestamp in `alert_state`, checked before sending.

**Alert de-duplication across restarts.** If the checker process restarts while a service is DOWN, `alert_state` persists in SQLite, so it will not re-alert for the same DOWN event. This is free from the design.

**The self-monitoring problem.** If Observatory itself goes down, it cannot alert on its own downtime. This is fundamental — you cannot solve it from inside the system. The correct answer is an external uptime check (a second, independent Observer watching Observer). Out of scope for this design.

---

## Config shape

```json
{
  "alerting": {
    "enabled": true,
    "threshold": 2,
    "channels": {
      "telegram": {
        "token": "bot-token-here",
        "chat_id": "-100xxxxxxxxx"
      },
      "webhook": {
        "url": "https://hooks.slack.com/services/...",
        "method": "POST"
      }
    }
  }
}
```

The checker reads this at startup. If `alerting.enabled` is false or the file does not exist, alerting is silently skipped — no behaviour change for existing deployments.

---

## What this looks like when it works

3:47am. Dead Drop goes down. 3:52am, first failed check — `consecutive_failures` = 1, no alert. 3:57am, second failed check — `consecutive_failures` = 2, state flips to DOWN, Telegram notification fires: "🔴 Dead Drop — DOWN (latency timeout, 2 consecutive failures)." 4:03am, service recovers, state flips to UP, notification fires: "🟢 Dead Drop — UP (was down 6 min)."

Two messages. Total. The right amount.

---

*Implementation is next. The above is the contract it has to satisfy.*
