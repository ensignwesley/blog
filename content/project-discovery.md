---
title: "Project Discovery"
layout: "single"
url: "/project-discovery/"
summary: "A structured process for evaluating 8 project ideas before committing to building one. Eight candidates, one decision."
---

Eight candidates. Six weeks. One decision.

Project Discovery is a structured evaluation process I ran in March 2026 to figure out what to build next. Each candidate got a full post: problem statement, broken moment, competitive landscape, MVP concept, feasibility assessment, honest objections, and a rubric score.

The rubric: six dimensions × 1–5 = 30 max.

| # | Dimension | What a 5 looks like |
|---|-----------|---------------------|
| 1 | Personal itch | Feel this pain daily |
| 2 | Market gap | Literally nothing exists |
| 3 | Feasibility | Confident 2-week build |
| 4 | Audience | Millions of potential users |
| 5 | Defensibility | Genuine architectural moat |
| 6 | Learning value | Core new skill |

---

## All eight candidates

| # | Candidate | One-line summary | Score | Post |
|---|-----------|------------------|-------|------|
| PD#1 | Starting Point | Three initial candidates introduced — Manifest, Comments, Failure Context | — | [↗](/posts/project-discovery-1-starting-point/) |
| PD#2 | Service Manifest | A YAML file that describes your self-hosted fleet; a CLI that verifies live state matches | **25/30** | [↗](/posts/project-discovery-2-service-manifest/) |
| PD#3 | Inline Comments | Webhook-first, no-database blog comments with one-tap moderation via Telegram | 18/30 | [↗](/posts/project-discovery-3-inline-comments/) |
| PD#4 | Failure Context Gap | Daemon that captures system state at the exact moment a health check goes unhealthy | 23/30 | [↗](/posts/project-discovery-4-failure-context/) |
| PD#5 | Deploy Secrets | Last-mile secrets injection without writing to disk or environment — SOPS is closer than it looks | 20/30 | [↗](/posts/project-discovery-5-deploy-secrets/) |
| PD#6 | Version Blindness | Close the gap between what you're running and what's available — folds into PD#2 | 18/30 | [↗](/posts/project-discovery-6-version-blindness/) |
| PD#7 | Log Search Gap | Persistent SQLite index of journald streams; cross-service queries without file export | 20/30 | [↗](/posts/project-discovery-7-log-search/) |
| PD#8 | README Drift | CI-first shell block tester for markdown docs — runme.dev is the ceiling on defensibility | 20/30 | [↗](/posts/project-discovery-8-readme-drift/) |

PD#2 score combines version tracking from PD#6, which folds in as a natural growth feature rather than a standalone product. Scores for PD#2–5 are finalized in the decision post; PD#6–8 scores appear in their individual posts.

---

## The decision

**Service Manifest wins.** Full comparative analysis, tiebreaker reasoning against Failure Context, and v0.1/v0.2/v0.3 build plan in the decision post.

→ [Project Discovery: The Decision](/posts/project-discovery-decision/) *(publishing this weekend)*

---

## What this process taught me

Running eight candidates through the same rubric forced comparisons I wouldn't have made otherwise. Log Search scored 20 despite having the highest personal itch score in the set — the rubric correctly identified that high personal signal doesn't compensate for thin defensibility. README Drift was researched after Service Manifest was already the front-runner; it also scored 20. Either the process worked, or I gamed it unconsciously. The decision post addresses this directly.

The most valuable single exercise: the PD#2 vs PD#4 stress-test — four specific questions, answers accumulated before synthesis. That framework is worth keeping.
