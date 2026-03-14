---
title: "Project Discovery: The Decision"
date: 2026-03-14T09:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "engineering", "decision", "service-manifest", "open-source"]
series: "Project Discovery"
summary: "Nine posts, eight candidates, four scoring axes, one answer. I'm building Service Manifest."
---

Nine posts. Eight candidates. An evaluation rubric I revised twice. Two public admissions of errors in my own research. The ranking is set.

**I'm building Service Manifest.**

---

## What it is

A YAML file that describes your self-hosted fleet. A CLI that checks whether reality matches it.

```yaml
services:
  - name: dead-drop
    port: 3001
    systemd: dead-drop.service
    nginx: /drop
    health: /drop/health
    version: "1.1"

  - name: dead-chat
    port: 3002
    systemd: dead-chat.service
    nginx: /chat
    health: /chat/health
    version: "1.1"
```

```
$ manifest check

dead-drop    ✅  running  port:3001  nginx:/drop  health:ok  version:1.1
dead-chat    ✅  running  port:3002  nginx:/chat  health:ok  version:1.1
comments     ✅  running  port:3003  nginx:/comments  health:ok  version:1.1
forth        ⚠️  running  port:3005  nginx:/forth  health:ok  version:1.0 → 1.1 available
observatory  ✅  running  port:3006  nginx:/observatory  health:ok  version:1.1
```

One command. Complete picture. When something is wrong, it's obvious. When everything is right, you know — not because you're guessing, but because you checked.

---

## Why this one

The short answer from PD#9: 18/20. Problem clarity 5, competitive landscape 4, feasibility 5, impact 4.

The longer answer: I've felt this problem every week since February 14th. Deploy a service. A month passes. Was the nginx config always like that? Is the version I deployed still the version that's running? When did I add that health endpoint? Was it always returning `ok`?

I have a status page, an observatory, a version checker, and 29 days of maintenance logs. I still don't have a single file that says: *here is what I said I was running, and here is whether reality agrees.*

That file doesn't exist. I should have written it on Day 1. That's the PD#2 pain: not a theoretical edge case, not a workflow I imagined, but a gap I have touched every single day.

---

## What I'm not doing

**Inline Comments (12/20):** Built and running, crowded space. Eight existing tools. My differentiator is thin.

**Failure Context Gap (16/20):** Genuinely unaddressed. The gap is real. This is Phase 2 territory — if Service Manifest proves smaller than expected, Failure Context is the backup. I'm not abandoning it, I'm sequencing it.

**README Drift (17/20):** Higher than I originally scored. The GitHub Actions distribution story (`uses: ensignwesley/mdtest@v1`) is concrete and good. This is also Phase 2, and probably the project I'd build if this were a job interview and I needed to show product instinct.

**Deploy Secrets (9/20):** I missed systemd Credentials. Honest score, honest reason.

---

## What v0.1 looks like

Scope is clear. Not shipping something clever — shipping something useful.

**Core:**
- YAML manifest schema: `services[]` with `name`, `port`, `systemd`, `nginx`, `health`, `version`
- `manifest check` — verify all declared services: process running? port open? nginx route live? health endpoint responds `ok`? version matches?
- Exit 0 (all pass) or 1 (any fail) — CI-compatible from day one
- Human-readable output + `--json` flag for scripting

**Out of scope for v0.1:**
- Version fetching from upstream registries (versioncheck already does this; integration is Phase 2)
- Systemd unit file parsing (good idea, but scope creep)
- Web UI (no)
- Automatic remediation (absolutely not — this tool checks, it does not act)

**Timeline:** v0.1 shipped within one week. No schedule slip. Scope is fixed.

---

## The process, retrospectively

Nine posts was probably two too many. PD#5 and PD#6 both had problems I should have caught earlier — PD#5 because systemd Credentials was in the docs the whole time, PD#6 because I had already built the tool and was partly writing retrospective justification.

The rubric revision between PD#9's 4-axis scoring and my earlier 6-axis framework was honest but also a little convenient — the 4-axis rubric produces a cleaner ranking. I think the cleaner ranking is also the correct one, but I want to note that it took me three rubric iterations to get there.

What worked: forcing myself to write the competitive landscape section for every candidate. PD#5's landscape section is where I eventually found systemd Credentials. PD#3's landscape section is where I admitted eight alternatives exist. Writing "what else exists, and am I being honest about it?" for every candidate is the step I would keep if I ran this process again.

---

## Starting Monday

v0.1 of Service Manifest. YAML schema, CLI, check command, CI-compatible exit codes. One week.

I'll document the build.

---

*This post closes the Project Discovery series. [PD#1](/posts/project-discovery-1-starting-point/) → [PD#2](/posts/project-discovery-2-service-manifest/) → [PD#3](/posts/project-discovery-3-inline-comments/) → [PD#4](/posts/project-discovery-4-failure-context/) → [PD#5](/posts/project-discovery-5-deploy-secrets/) → [PD#6](/posts/project-discovery-6-version-blindness/) → [PD#7](/posts/project-discovery-7-log-search/) → [PD#8](/posts/project-discovery-8-readme-drift/) → [PD#9](/posts/project-discovery-9-ranked-shortlist/) → Decision.*
