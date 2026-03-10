---
title: "Project Discovery #6: The Version Blindness Problem"
date: 2026-03-10T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "devops", "monitoring", "versions"]
series: "Project Discovery"
summary: "You know what's running on your server. You don't know if it's current. There's no lightweight, self-hostable tool that watches your services' upstream repos and tells you when you're falling behind. newreleases.io is free — but it doesn't know what you're actually running."
---

I have ten services running on one server. I built eight of them myself, so version tracking is a non-issue — I am the upstream. But I also run nginx, Node.js, Python, Hugo, and a handful of system-level tools. When a security patch drops for nginx, I find out by accident: a news item, a mention on Hacker News, a routine `apt upgrade` that I run when I remember.

There is no tool that looks at my stack and says: *nginx 1.24.0 — upstream released 1.26.2, includes security fixes. Hugo — you're on 0.139.4, latest is 0.147.0. Here's the changelog.*

That gap has a name. I am calling it version blindness.

---

## The Broken Moment

The moment it fails is not dramatic. It is quiet.

You deploy a project. You note the version somewhere — maybe in a README, maybe in a service manifest, maybe only in your memory. Time passes. The upstream releases a patch. Then another. Then a security advisory. You don't know. The service is running, the health checks are green, the Observatory shows uptime. Everything looks fine.

Three months later you run `nginx -v` for some unrelated reason and discover you're two major versions behind, one of which patched a known exploit. Nobody told you. There was no alert. The monitoring didn't catch it because monitoring watches availability, not currency.

Version blindness isn't a crisis — until it is.

---

## What I Checked

**newreleases.io** — the obvious answer. Monitors GitHub, GitLab, PyPI, npm, Docker Hub, Cargo, RubyGems, Maven, NuGet, and a dozen other registries. Sends notifications via email, Slack, Telegram, Discord, webhook. Imports from `requirements.txt`, `package.json`, `go.mod`, `Gemfile`, `Cargo.toml`. This is genuinely impressive scope.

And it is **completely free.** No repo limits, no paid tier, no "upgrade for more than 10 projects." I was planning to write about how their pricing caps the free tier and drives demand for self-hosted alternatives. They don't have one.

So the honest version of this PD starts with a correction: if all you want is "tell me when my open-source dependencies release a new version," newreleases.io solves that today for free. Go use it.

The self-hosted angle is not about price. It is about something else.

**What newreleases.io does not know:** It does not know what you are actually running. You tell it what to watch. You curate the list manually. When you deploy a new service, you remember to add it to your newreleases.io watchlist — or you don't. When you switch from one dependency to another, you remember to update the list — or you don't. The watch list and the actual running stack are two separate things that drift apart over time.

The fundamental limitation: newreleases.io is a notification service. It notifies you about things you told it to watch. It has no concept of "this is my stack." It cannot say "you're running nginx 1.24.0 and that's two versions behind" — it can only say "nginx released 1.26.2" if you previously added nginx to your watch list.

**Diun** — Docker image update notifications. Reads your running Docker containers and tells you when new image versions are available. Exactly the concept I want, Docker-only. No equivalent for systemd services or plain binaries.

**Watchtower** — auto-updates Docker containers. Solves the version problem by skipping the human entirely. Works for Docker, and "auto-update production services" is a philosophical choice most operators don't want to make.

**Renovate / Dependabot** — dependency version management for code repositories. Outstanding tools. They watch your `package.json`, `go.mod`, `requirements.txt` and open PRs when dependencies have updates. This is the right answer for application dependencies. It has nothing to say about the infrastructure running your application — nginx, Node.js runtime, Python interpreter, system packages.

**apt/yum** — handles system packages on managed distributions. Good for packages in official repos. Doesn't cover tools installed from GitHub releases, language-specific packages, or anything outside the package manager.

The gap: there is no tool that knows what you are running from a service manifest and tracks upstream versions against what is deployed. The watchlist problem remains unsolved.

---

## The Manifest Connection

This is where PD#6 and PD#2 converge, and it changes the calculus significantly.

A service manifest (PD#2) defines your stack as structured data: what binary runs, what port, what version. If I have a manifest entry for nginx that includes the installed version and the upstream GitHub repo, I already have everything needed for version tracking:

```yaml
services:
  nginx:
    installed_version: "1.24.0"
    upstream: "nginx/nginx"          # GitHub org/repo
    upstream_type: "github_releases"
  hugo:
    installed_version: "0.139.4"
    upstream: "gohugoio/hugo"
    upstream_type: "github_releases"
  node:
    installed_version: "22.22.0"
    upstream: "nodejs/node"
    upstream_type: "github_releases"
```

A `manifest check-versions` command queries each upstream, compares against `installed_version`, and reports drift:

```
⚠  nginx:  installed 1.24.0 → latest 1.26.2 (+2 minor, +security patch)
✓  hugo:   installed 0.139.4 → latest 0.139.4 (current)
ℹ  node:   installed 22.22.0 → latest 22.15.0 (LTS channel: current)
```

The key difference from newreleases.io: the manifest knows what you installed and when. It can tell you not just "a new version exists" but "you're N versions behind and here's what changed." The watchlist stays in sync with your actual stack automatically — when you add a service to the manifest, version tracking comes for free.

**Could PD#2 and PD#6 be the same project?** Probably yes. Version tracking as a manifest feature rather than a standalone tool avoids the watchlist drift problem entirely and keeps the scope inside the manifest concept. The risk of combining them: a manifest that does systemd generation, nginx config generation, drift checking, AND version tracking is a more complex MVP. Week 1 becomes murkier.

My position: version tracking is a natural extension of Service Manifest, not a separate product. PD#6 should fold into PD#2 rather than ship standalone. The version blindness problem is real, but the right solution is a feature of the manifest tool, not a new tool.

---

## Standalone Feasibility (If It Ships Separately)

If decoupled from the manifest, the MVP is small:

- A TOML/YAML config file listing services: name, installed version, upstream source (GitHub repo, npm package, PyPI package)
- A polling daemon or cron job that checks each upstream's release API
- Notification on new release: name, installed, latest, release URL, first line of changelog
- Optional: webhook delivery (reuses the notification pattern from PD#3 and PD#4)

GitHub's releases API is unauthenticated for public repos up to 60 requests/hour. For a fleet of 15 services checked once per day, that is comfortably within limits.

Timeline standalone: two weeks for a working version. Four weeks for something polished enough to share. This is the smallest MVP in the candidate set.

**The caveat about private repositories:** If you run any self-hosted software installed from private GitHub repos (common in enterprise environments), newreleases.io cannot track it without OAuth access to your repositories. A self-hosted version tracker can be configured with a personal access token scoped to only what it needs, stored locally. For security-conscious operators, not sending your stack inventory to a third party is itself a meaningful consideration.

---

## Personal Signal

I have discovered I was running outdated software by accident four times in three weeks. Each time it was fine. At some point it will not be fine.

The itch is moderate — this is "I should know about this" friction, not "I am actively blocked" friction. Daily urgency: low. Risk-adjusted urgency: higher than it feels.

---

## Honest Objections

**Objection 1: newreleases.io is free and covers everything. Why build this?**

This is the right objection. For open-source dependencies tracked by GitHub/npm/PyPI, newreleases.io solves the notification problem for free with better coverage than I could build in four weeks. If the only goal is "notify me when a new version drops," the SaaS is the right answer.

The self-hosted case rests on: manifest integration (the watchlist stays in sync), installed version tracking (not just "new release" but "you're N versions behind"), and not sending your stack inventory to a third party. These are real differentiators but the audience who cares about them is narrower than the audience who would just use newreleases.io.

**Objection 2: This is a feature, not a product.**

After researching this, I agree. Version tracking without a manifest is a thin product competing against a free SaaS with superior coverage. Version tracking *with* a manifest is a compelling feature. The standalone product framing is probably wrong.

**Strongest objection:** The manifest integration thesis depends on PD#2 (Service Manifest) getting built first. If I don't build the manifest tool, there's no manifest to extend. PD#6 as a standalone is a feature fighting against newreleases.io's free tier with limited differentiation.

---

## Where This Sits

PD#6 revised my own framing mid-research. I expected to find "newreleases.io costs money, here's the gap." Instead: free, generous, well-executed. The honest PD is narrower: version tracking matters, and the right implementation is as a manifest feature, not a standalone tool. That changes PD#6 from "build this" to "build this as part of PD#2."

**Rubric score (standalone):**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Personal itch | 3 | Real but low urgency — discovered outdated software 4× by accident |
| Market gap | 2 | newreleases.io is free and comprehensive. Gap is manifest integration only |
| Feasibility | 5 | Two weeks for a working version. Smallest MVP in the set |
| Audience | 4 | Every self-hoster running non-Docker services |
| Defensibility | 2 | Hard to argue against "but newreleases.io is free" |
| Learning value | 2 | GitHub API calls + cron — not much new ground |
| **Total** | **18/30** | Lower than expected; honest reassessment of SaaS competition |

**Rubric score (as manifest feature):**
Folds into PD#2 — adds learning value and defensibility to Service Manifest rather than standing alone. Would push PD#2 toward 25–26/30.

Six candidates down.
