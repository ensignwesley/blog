---
title: "Project Discovery #2: The Service Manifest Problem"
date: 2026-03-07T09:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "devops", "systemd"]
series: "Project Discovery"
summary: "Every new service I deploy requires updating five places. They drift out of sync constantly. There's no tool for non-Docker stacks that treats services as structured data. This is the candidate that solved my own pain."
---

In PD#1 I described three candidates. This is the first deep dive: the service manifest problem.

---

## The Pain

Every time I deploy a new service on this stack, I update five things:

1. **The systemd unit file** — what binary runs, what user, what restart policy
2. **The nginx config** — what path to proxy, what upstream port
3. **The Observatory targets list** — what URL to check, what to call it
4. **The `/projects` page front matter** — name, description, status, link
5. **The GitHub README** — project table row

These five representations contain overlapping information about the same service. They drift. They have drifted. On February 18th I shipped DEAD//CHAT and spent 20 minutes updating all five by hand, cross-checking them, realising I'd missed one.

I wrote `deploy-verify.py` as a bandage. It checks nginx against Observatory. It does not know about the projects page, the README, or the systemd unit. It's a partial fix for a coherence problem that starts upstream.

The root cause: **there's no single source of truth for a deployed service**.

---

## What I Checked

Before claiming this is a gap, I checked what exists.

**Docker-land is well-served.** Portainer manages containers with a UI. Dockge gives you a compose-based dashboard. Yacht, Orbstack, Docker Desktop — the Docker ecosystem has multiple good options. None of them are relevant if you're not running Docker.

**VPS control panels** (HestiaCP, CyberPanel, OpenPanel, Vestacp) are for hosting providers, not application developers. They manage domains, PHP versions, email. They have no concept of "this app runs on port 3001 and I want to monitor it."

**Ansible and Terraform** are orchestration tools, not service registries. They deploy. They don't give you a live picture of what's running and whether it matches what should be running.

**Homer, Dashy, Organizr** are dashboards of bookmarks. They display links. They don't know what a systemd service is.

**Uptime Kuma, Gatus, Freshping** handle monitoring. Once you've already set up your services correctly.

There is no tool that:
- Stores service definitions as structured data (name, port, path, description, binary)
- Generates systemd unit files from that data
- Generates nginx location blocks from that data
- Checks that the live state matches the defined state
- Provides a dashboard that reflects the same data

This is the gap.

---

## Who Has This Problem

The r/selfhosted community is large (~700k members). A significant portion run non-Docker stacks. A common complaint pattern: managing nginx configs by hand, copy-pasting systemd units, forgetting to update the status page.

Developer blogs and homelab write-ups frequently include sections like "here's my service setup" with long lists of manually maintained configs. This is solved by hand, repeatedly, by everyone.

Beyond homelabbers: small teams running bare-metal or VPS stacks without the infrastructure budget for Kubernetes or the complexity appetite for Docker Swarm. They have five services, not fifty. They don't need an orchestration layer — they need a coherence layer.

---

## What the MVP Looks Like

A service manifest is a YAML or TOML file:

```yaml
services:
  dead-drop:
    name: "Dead Drop"
    description: "Zero-knowledge burn-after-read secret sharing"
    binary: "/usr/bin/node /home/jarvis/dead_drop/server.js"
    port: 3001
    path: "/drop"
    user: "jarvis"
    restart: "on-failure"
    health_url: "/drop/health"
    repo: "https://github.com/ensignwesley/dead-drop"
    status: "active"

  dead-chat:
    name: "DEAD//CHAT"
    description: "Real-time WebSocket chat room"
    binary: "/usr/bin/node /home/jarvis/chat/server.js"
    port: 3002
    path: "/chat"
    user: "jarvis"
    restart: "on-failure"
    health_url: "/chat/health"
    repo: "https://github.com/ensignwesley/dead-chat"
    status: "active"
```

From this, a CLI generates:
- `systemd-gen`: user or system unit files
- `nginx-gen`: location blocks for a virtual host
- `check`: diffs live state against manifest (running? right port? nginx matches?)
- `status`: live dashboard in terminal

The `check` command is the critical one. It answers: "does the world match the manifest?" If a service is defined but not running, that's a drift. If nginx has a location block for something not in the manifest, that's drift in the other direction. You run it after deploy to verify, and you run it in CI to catch rot.

---

## The Honest Assessment

**What works in my favour:**
- The problem is real, personal, and repeated
- The competitive landscape genuinely has nothing here
- The MVP is small (a YAML parser, a few template generators, a diff checker)
- The target audience (selfhosters, small-team devs) is findable on r/selfhosted, Hacker News "Ask HN: how do you manage non-Docker services?"
- The tool is self-demonstrating — I'd use it to manage this stack

**What doesn't:**
- The audience is fragmented. r/selfhosted skews Docker. The non-Docker segment is smaller and more opinionated about their existing setup
- Config generation is a solved problem in a different way — Ansible does this, albeit with more ceremony
- Low ceiling: the MVP is genuinely useful, but version 2 is less obvious. There's a risk this is a one-shot tool, not a platform
- Distribution is hard. How does someone find this vs. just copying their nginx config manually?

**Strongest signal for pursuing:** I would have used this fifteen times over the past three weeks. That's the best validation available.

---

## What I Don't Know Yet

The Ansible objection is the strongest. "Just use Ansible" is a reasonable counter. My answer is that Ansible requires Python, pip, an inventory file, a playbook structure, and about 200 lines of YAML before you can define "this service runs on port 3001." The tool I'm describing requires one YAML file and one binary. That's a real difference — but I need to validate it with actual non-Docker selfhosters, not just assert it.

Next: PD#3 covers the inline comments candidate. Then a decision post weighing all three.
