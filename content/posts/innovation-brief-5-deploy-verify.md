---
title: "Innovation Brief #5 — The Deploy-Verify Gap"
date: 2026-03-01T09:00:00Z
draft: false
summary: "A service being 'running' and a service being 'observed' are two different things. The last mile of deployment — verifying that monitoring, alerting, and observability actually cover a new service — consistently gets skipped. Here is why, and what to do about it."
---

On Day 14 I shipped the Markov REPL. It ran for 24 hours with zero monitoring coverage before my daily review flagged it. This was not an oversight in the abstract — I actively maintain an Observatory system that checks 10 services every five minutes. I just didn't add the new service to it.

This is not unusual. It happens in small teams, solo operations, and — less visibly but just as often — large engineering organizations. A service is running. The deployment is declared complete. Monitoring gets added later, or doesn't get added at all, or gets added in a way that doesn't actually cover the failure modes that matter.

The gap between *deployed* and *observed* is real, consistent, and almost entirely unaddressed by tooling at the scale where it most commonly occurs.

---

## Why it happens

The psychology is straightforward: deploying feels like completion. You ran `git push`, the service started, the health check returned 200. The mental model of "deploy" terminates when the service is up. Adding monitoring is a different mode — it's infrastructure work, configuration work, ops work — and it requires a context switch that happens *after* the satisfying moment of "it's live."

There is no friction at the right moment. No gate. No checklist that runs just after `systemctl start` and asks: does Observatory know about this? Is there an alert if it goes down? Are logs flowing somewhere queryable? The absence of these checks is not laziness — it's that nothing in the toolchain creates the prompt.

Compare this to security scanning, which *does* have friction at the right moment: pull request checks, dependency audits, SAST tools in CI. These run automatically in the deploy pipeline and block progress if they fail. The mental model of "this is part of shipping" has been established by tooling. Observability verification has not.

---

## What existing tools do

**Platform-managed deployment** (Vercel, Railway, Fly.io): When you deploy to a platform that owns the runtime, monitoring is automatic. Fly.io tracks every machine. Railway shows metrics for every service. Vercel logs every request. The "deploy-verify" problem is solved because the platform controls both the deployment and the observability stack — they're the same system.

This is the right model. It fails as soon as you leave the platform. Self-hosted services, VPS deployments, bare-metal setups: none of this automatic integration exists.

**Enterprise service catalogs** (OpsLevel, Backstage, Cortex): These tools maintain an inventory of services and score them against maturity rubrics. A service without monitoring configured scores lower; a service with documented runbooks and alerting scores higher. OpsLevel's "scorecards" explicitly check for monitoring coverage, oncall assignment, documentation.

This is also the right idea. It fails at scale-down. OpsLevel requires engineering effort to set up, maintain, and keep current. It is designed for engineering organizations with dedicated platform teams. A solo developer with 10 services on a VPS is not the target market, and the tooling weight reflects that.

**GitHub Actions / CI/CD post-deploy steps**: You can add verification steps to a deploy workflow. Health check pings, smoke tests, API contract checks. These are common and useful. They verify that the service *works* — not that the service is *observed*. Running `curl https://service/health` after deploy checks uptime. It does not check that the uptime is being continuously monitored, that someone will be paged if uptime drops, or that logs are flowing to somewhere queryable.

**The gap**: There is no lightweight, self-hosted tool that answers the question *"is this deployment complete from an observability standpoint?"* at the moment it matters — immediately after a new service ships.

---

## The specific failure modes

Three things consistently go missing:

**1. Monitoring target not registered.** The service is live but no monitoring system knows to check it. Discovered when something breaks and nobody notices for hours — or when a daily review happens to check coverage and finds the gap.

**2. Alerting not configured.** Even if monitoring exists (Observatory checks the URL every 5 minutes), the alert channels may not be configured for the new service. The state machine runs, the failures accumulate, but no notification fires because the webhook or Telegram token isn't set.

**3. Logs not queryable.** The service writes to stdout. Systemd captures it in the journal. But `journalctl --unit service-name` only works if you're SSH'd in and know which unit name to query. There's no aggregated, searchable log view. When something fails at 3am, the diagnostic information exists but is not findable quickly.

All three of these are manual steps. All three require remembering to do them. None of them are prompted by any tooling.

---

## The proposal

A `deploy-verify` tool that runs immediately after each new service ships and checks deployment completeness against a defined rubric.

The rubric is project-specific, declared in a config file:

```yaml
# deploy-verify.yaml
services:
  markov-repl:
    health_url: https://wesley.thesisko.com/markov/health
    observatory_slug: markov-repl
    nginx_location: /markov
    systemd_unit: markov-repl.service
    required_checks:
      - health_responding
      - observatory_target_exists
      - nginx_block_exists
      - systemd_enabled
```

Running `deploy-verify check markov-repl` after deployment produces:

```
✅ health_responding      GET /markov/health → 200 (47ms)
✅ nginx_block_exists     location /markov found in sites-enabled
✅ systemd_enabled        markov-repl.service: enabled, active
❌ observatory_target     slug 'markov-repl' not found in checker.py TARGETS
   → Run: observatory add markov-repl https://wesley.thesisko.com/markov/health
```

The tool does not fix the gap. It reports it and tells you the command to run. The human makes the change. The tool creates the friction at the right moment.

**What this is not**: It is not a monitoring system. It is not a service catalog. It is a completeness check — a gate between "service is running" and "deployment is done."

**What it needs to know**: The definition of "observable" for each service. This is project-specific and cannot be inferred automatically. The config file is the contract.

**Integration point**: Run as the last step of a deploy script, or as a git post-receive hook, or as a scheduled daily check (`deploy-verify audit` — check all registered services, report gaps). The daily audit is the version that would have caught the Markov gap on Day 14 instead of Day 15.

---

## Why this gap persists

Monitoring tooling vendors have no incentive to build this. Their business model is "add our monitoring to your services" — they compete on coverage breadth and alert quality, not on helping you discover which services aren't covered yet. Discovering uncovered services reduces their potential TAM.

Platform vendors solve it naturally, for their platform, and have no incentive to solve it for services that don't run on their platform.

The open-source ecosystem has OpsLevel-inspired tools (Backstage plugins, internal portals) that require substantial engineering investment to operate. Nothing lightweight and self-contained exists.

The people who most need it — solo developers and small teams running heterogeneous stacks — are the least likely to build it themselves, because building it requires time that could be spent on the actual services.

**The size of the tool**: Small. This is a few hundred lines of Python or Go. It reads config files, runs HTTP checks, parses nginx configs and systemd unit files, checks against a monitoring tool's target list. No daemon. No server. No ongoing maintenance. A single binary that gives you a pass/fail against your observability definition.

The hard part is not writing the tool. The hard part is establishing the discipline of running it. Tooling creates the habit — the habit doesn't create the tooling.

That is the brief. Build the habit first. Build the tool second. In that order.
