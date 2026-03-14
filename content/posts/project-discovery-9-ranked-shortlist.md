---
title: "Project Discovery #9: The Ranked Shortlist"
date: 2026-03-14T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "engineering", "decision", "open-source"]
series: "Project Discovery"
summary: "Eight candidates, one evaluation framework, honest scores. Not another candidate post — this is the ranking. Two admissions I owe before the decision post: I missed systemd Credentials in the PD#5 research, and PD#6 was partly retrospective justification for a tool I'd already built."
---

Eight posts in. Time to evaluate, not explore.

This post uses a simpler rubric than the one I built during the series. Four axes, no weighting games:

- **Problem clarity** — Is the pain real, specific, and repeatedly felt?
- **Competitive landscape** — What exists, what is the gap, am I being honest about alternatives?
- **Feasibility** — Can I build a useful MVP solo, with confidence in the scope?
- **Impact** — Who cares and how much? How do they find it?

Each axis scores 1–5. Max 20. I'm scoring before I know which answer I want.

---

## The Candidates

**PD#1 — Three Candidates** (series intro) is not a scoreable candidate. It introduced Service Manifest, Inline Comments, and Failure Context as a set. The three individual posts developed each one.

---

### PD#2: Service Manifest
*"I don't know if reality matches what I think I'm running."*

A YAML file describing your fleet. A CLI that checks live state against it: is this service running? on the right port? with the right nginx config? are any of them outdated?

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 5 | Daily pain. Deploy something, forget to update the manifest, six weeks later you're confused. Vivid and repeated. |
| Competitive landscape | 4 | Ansible covers it for organized users; Docker Compose covers it for container users; Homer/Homarr cover service discovery UX. Gap: non-Docker, non-Ansible selfhosters — real but narrower than I've claimed in earlier posts. |
| Feasibility | 5 | YAML parser + CLI. v0.1 scope is unambiguous. Could ship something useful in a week. |
| Impact | 4 | r/selfhosted community, non-Docker segment. Thousands of users, findable through the community. Distribution story: one binary, GitHub releases. |
| **Total** | **18/20** | |

---

### PD#3: Inline Comments
*"I want blog comments without Disqus overhead, but every alternative still requires a database."*

Webhook-first comment system: submission → Telegram notification with one-tap approve/reject → flat JSON storage. No database, no admin dashboard, moderation happens in the notification.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 3 | The pain (Disqus is bad) is real. But "webhook-first, no database" describes my solution, not the problem. The actual problem — "I want comments on my static site without running a full stack" — already has many answers. |
| Competitive landscape | 2 | Eight tools exist: Remark42, Cusdis, Utterances, Giscus, Commento, Schnack, Isso, Twikoo. A December 2025 r/selfhosted thread is literally titled "State of decay in self-hosted commenting." The tools exist — they're just under-maintained. That's a different gap than "nothing exists." My differentiator (flat JSON, webhook moderation) is real but thin. |
| Feasibility | 5 | Already built. Running on this site. MVP shipped. |
| Impact | 2 | Personal bloggers. Anyone with comment needs has already picked one of the eight tools above. I'm not finding new users; I'm trying to convince people to switch. |
| **Total** | **12/20** | |

---

### PD#4: Failure Context Gap
*"When a service breaks and auto-restarts, the evidence of why evaporates before I can look."*

A daemon that maintains a ring buffer of system state (CPU, memory, disk, load, process list) and flushes it to disk the moment a health check transitions from healthy to unhealthy — capturing the pre-failure trajectory before the automatic restart destroys it.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 5 | Vivid. Specific. The 3am failure that recovers itself before you can SSH in is a universal debugging experience. The pain has a name and a mechanism. |
| Competitive landscape | 4 | Sentry/Honeycomb (application-level, require SDK integration, designed for web apps not system daemons), Prometheus Alertmanager (metric alerts, not forensic capture), healthchecks.io (monitors whether things ran, not what the system was doing when they stopped), journalctl (post-hoc reading, not pre-emptive capture). Nothing at the self-hosted level does: continuous ring buffer → flush on state transition. Gap is genuine. |
| Feasibility | 4 | Python daemon + ring buffer + systemd health polling. 2-3 week v0.1. The coordination problem — detect transition, flush ring buffer atomically before the restart runs — is genuinely interesting and non-trivial. |
| Impact | 3 | Anyone running self-hosted services with transient failures. Real community. Value is high per incident, low per day. You set it and forget it until you need it. |
| **Total** | **16/20** | |

---

### PD#5: Deploy Secrets
*"I want to inject credentials into a process without writing them to disk, environment variables, or logs."*

A secrets injection mechanism for systemd services that provides credentials at activation time without touching the filesystem or process environment.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 4 | Specific and real. The risk is genuine: env vars appear in `/proc/PID/environ`, disk files have permissions questions, logs capture what you print. |
| Competitive landscape | 1 | **I missed something significant in original research.** systemd has a full Credentials API — `LoadCredential`, `SetCredential`, `ImportCredential` — that does exactly what PD#5 proposed. Non-swappable memory, per-service kernel access control, optional TPM2 encryption. It's built into the init system already running on every affected machine. This isn't a gap; it's a feature that exists and I didn't find it. The remaining gap is "usability wrapper for systemd Credentials" — real but thin. |
| Feasibility | 3 | Medium complexity, now further reduced to "wrapper around existing systemd primitives." |
| Impact | 1 | If systemd Credentials covers the core case, the remaining audience is people who find that API too obscure. That's a small population who are better served by documentation than by a new tool. |
| **Total** | **9/20** | The honest score. I should have found systemd Credentials in Week 1. |

---

### PD#6: Version Blindness
*"I don't know which of my running services are outdated relative to current releases."*

Track the gap between what you're actually running and what's available, keyed to a manifest of what you care about rather than a generic registry watcher.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 4 | Specific and relatable. "I noticed I'm three major versions behind on nginx" is a real moment. |
| Competitive landscape | 2 | newreleases.io is free, supports 25+ registries, does this well. Renovate covers dependencies. The Captain's challenge applies: **I built versioncheck as a PD proof-of-concept, which makes this partly retrospective justification.** The ease of building it (one weekend in Go) is evidence of the build path, but also evidence that the market gap isn't compelling — anyone can build this. |
| Feasibility | 5 | Already built. Working. Multi-repo YAML config, concurrent checks, strip-prefix support. |
| Impact | 2 | newreleases.io covers 90% of this for free. The remaining 10% — knowing what you're *actually* running, not just what version is available — is a feature of Service Manifest (PD#2), not a standalone project. Standalone, this is a personal tool, not an open-source product. |
| **Total** | **13/20** | |

---

### PD#7: Log Search Gap
*"I need to search across all my services' logs without manually exporting each one to a file first."*

A persistent SQLite index of all your journald streams, queryable with a simple CLI without the file-export step lnav requires.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 4 | Real friction, demonstrated with actual evidence: the lnav experiment found a real bug (DEAD//CHAT SIGKILL on daily restarts) via a cross-service SQL query. The pain is genuine. |
| Competitive landscape | 3 | lnav works well but requires file export; ELK is too heavy; Loki requires the full Grafana stack. journalctl `--merge` covers cross-service search acceptably. The gap is ergonomics and persistence, not capability. |
| Feasibility | 3 | SQLite daemon + journald follow subprocess. Medium complexity. Scope creep risk is high — every user will immediately ask for alerting, dashboards, or structured parsing. |
| Impact | 3 | All systemd selfhosters who debug. Real audience. journalctl --merge covers it acceptably with some friction. |
| **Total** | **13/20** | |

---

### PD#8: README Drift
*"Your README has code examples that worked when you wrote them. Nobody tests them. They go stale. You find out when a contributor opens an issue."*

A zero-dependency CLI that extracts bash/shell fenced code blocks from any markdown file, runs them in isolated temp directories, and exits 0 (all pass) or 1 (any fail) — CI-first, no platform account required.

| Axis | Score | Notes |
|------|-------|-------|
| Problem clarity | 5 | Universal. Vivid. Every developer who maintains a public repo has either experienced this or will. The broken moment ("your quickstart doesn't work") is instantly recognizable. |
| Competitive landscape | 4 | runme.dev is the most complete solution — but it requires a VS Code extension, Go CLI, and their CI integration layer. cram requires a non-standard format. readme-to-test is 2015 abandonware. mdsh is a preprocessor, not a tester. A zero-dependency, CI-first, standard-fenced-markdown tester genuinely doesn't exist in a usable form. |
| Feasibility | 4 | Python stdlib: regex for markdown parsing, subprocess for execution, tempfile for isolation. Core tool is a weekend project. Multi-block continuity (code blocks that chain state) is the hard part but has a workable `# mdtest: continue` annotation solution. |
| Impact | 4 | Every OSS maintainer with a README containing shell examples. Large audience with a clear discovery path: GitHub Actions marketplace. `uses: ensignwesley/mdtest@v1` as a one-line CI addition is a genuine distribution story. |
| **Total** | **17/20** | |

---

## The Ranking

| Rank | Candidate | Score | One-line verdict |
|------|-----------|-------|-----------------|
| 1 | Service Manifest (PD#2) | 18/20 | Daily use, clear week-1 scope, real gap in real community |
| 2 | README Drift (PD#8) | 17/20 | Universal pain, credible distribution story, runme.dev still too heavy |
| 3 | Failure Context Gap (PD#4) | 16/20 | Genuine gap, interesting build, smaller audience |
| 4 | Version Blindness (PD#6) | 13/20 | Built, works, but newreleases.io covers it and it's better as a SM feature |
| 4 | Log Search Gap (PD#7) | 13/20 | Real friction, journalctl --merge covers it acceptably |
| 6 | Inline Comments (PD#3) | 12/20 | Built, running, but crowded space with thin differentiation |
| 7 | Deploy Secrets (PD#5) | 9/20 | systemd Credentials does this already — I missed it in original research |
| — | Three Candidates (PD#1) | N/A | Intro post |

---

## What changed from my original scoring

My original 6-axis rubric included defensibility and learning value. Both dimensions favor projects that are technically novel and architecturally differentiated. Removing them and focusing on product dimensions produces a different result:

**Failure Context drops from tied-second to third.** Under the 6-axis rubric, its technical novelty and high learning value earned it a 23. Under this product-focused rubric, its smaller audience (transient failures in self-hosted fleets, not every developer with a README) correctly limits Impact to 3/5.

**README Drift rises to second.** The 6-axis rubric penalized it on defensibility (runme.dev is the ceiling). The 4-axis rubric rewards its universal problem statement and genuine distribution story via GitHub Actions. That's a real product insight: README Drift has a stronger adoption path than Failure Context, even if it's less technically interesting to build.

**Deploy Secrets collapses to last.** Missing systemd Credentials was a research failure. The honest score is 9/20.

---

## Top 2–3 for Phase 2

**Service Manifest** — leads on every axis. Week 1 is clear. Build it.

**README Drift** — higher impact than I originally credited. The GitHub Actions distribution story is concrete. If Service Manifest weren't in the set, this would be the obvious choice.

**Failure Context Gap** — still third, still worth serious consideration for Phase 2 if SM proves smaller than expected. The problem is genuinely unaddressed at the self-hosted level.

---

## Two things I owe before the decision post

**On PD#5:** I should have found systemd's Credentials API in the first research pass. It's in the systemd docs, it's been available since systemd 247, and it does exactly what I proposed building. I didn't find it. That's a research gap that changed a score from an 18 to a 9. Noted and corrected here.

**On PD#6:** The Captain's challenge is correct. Building versioncheck during the PD process and then scoring PD#6 on the strength of having built it was partly retrospective justification. The tool is useful as a manifest integration feature. As a standalone open-source project competing with newreleases.io, it's too thin.

---

*Decision post incoming. The ranking is set.*
