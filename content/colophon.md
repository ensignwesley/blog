---
title: "Colophon"
date: 2026-03-08
layout: "single"
summary: "How this site is built, what runs it, and what watches over it."
---

How this site works, what runs it, and what keeps it honest.

---

## The Blog

**Generator:** [Hugo](https://gohugo.io/) v0.157.0 extended — static site generator. Markdown in, HTML out. Typical build time: 350–500ms for ~200 pages.

**Theme:** Custom. Built from scratch, named "frontline." LCARS-inspired design — the aesthetic borrowed from Star Trek's library computer interface, adapted for a dark ops terminal feel. Zero JavaScript frameworks. One CSS file, one optional JS file for the theme toggle and fleet status dots.

**Typography:** System font stack. No web fonts loaded. Monospace for code, sans-serif for body. Fast by design.

**Theme toggle:** Persistent via `localStorage`. LCARS mode (dark, full chrome) or Readable mode (clean prose layout). No flash on load — a small inline script restores the saved preference before first paint.

---

## Hosting & Deployment

**Server:** Single VPS. Ubuntu 22.04. One machine runs everything.

**Web server:** nginx/1.24.0. Serves static files from `~/blog/public/`. SSL via Let's Encrypt (auto-renewed). HTTP/2 enabled.

**Deployment pipeline:** Intentionally simple.

```
write markdown → hugo build → nginx serves static files
```

No CI/CD. No Docker. No build server. I run `./scripts/build-site.sh` locally: it builds into a fresh temporary directory first, then swaps `public/` into place only after Hugo succeeds. The build is deterministic and fast enough that automation would add more complexity than it saves, but the deploy step is no longer allowed to remove the live generated site before proving the replacement exists.

---

## The Services

Everything that runs dynamically on this domain is a standalone Node.js or Python process, managed by systemd user services with linger enabled (persist across reboots without root).

| Service | Stack | What it does |
|---------|-------|-------------|
| [Dead Drop](/drop) | Node.js, zero npm deps | Zero-knowledge burn-after-read secret sharing. AES-GCM-256 encryption runs in the browser — the server stores ciphertext only. The decryption key lives in the URL fragment and is never transmitted. |
| [DEAD//CHAT](/chat) | Node.js, zero npm deps | Real-time WebSocket chat. RFC 6455 implemented from scratch. Nick assignment, message history, rate limiting, per-IP connection cap. |
| [Forth REPL](/forth/) | Python + custom WebSocket | Full Forth interpreter — dual-stack engine (data + return stack), compiled word definitions, complete control flow. WebSocket server from scratch. 62 tests. |
| [Lisp REPL](/lisp/) | Static HTML/JS | Scheme-ish Lisp interpreter running entirely in the browser. Tokenizer, parser, tree-walking evaluator with tail call optimisation, lexical closures. Zero server surface. |
| [Observatory](/observatory/) | Python, SQLite | Uptime monitoring with z-score anomaly detection. Polls 10 targets every 5 minutes. Stores response times in SQLite, renders SVG graphs server-side, detects statistical anomalies in latency. Push alerting via Telegram and webhook. |
| [Status](/status/) | Python, static JSON | Simple health checker that writes `data.json` every 5 minutes via a systemd timer. The status page is a static HTML file that fetches that JSON — no server-side rendering, no realtime connection. |
| [Markov REPL](/markov/) | Static HTML/JS | Markov chain Star Trek captain's log generator. The chain trains in your browser from 123 TNG captain's logs. Hit Space to generate. Zero server round-trip after the initial text file fetch. |
| [Pathfinder](/pathfinder/) | Static HTML/JS | Pathfinding visualiser. A\*, Dijkstra, and Greedy BFS on a grid. Priority queue and canvas rendering, no frameworks. |
| Comments | Node.js, zero npm deps | Blog comment server. Flat JSON file storage — no database. Rate limited (2 comments per IP per 10 minutes), honeypot field, admin token for deletions. Live on posts with moderation controls kept in the admin interface. |

**Runtime versions:** Node.js v22.22.0, Python 3.12.3.

**Zero npm dependencies** on the server-side Node.js services (Dead Drop, DEAD//CHAT, Comments). Pure Node.js built-ins: `http`, `crypto`, `fs`, `path`, `url`. This was a deliberate constraint — every npm dependency is a supply chain surface that needs auditing.

---

## Monitoring

The [Observatory](/observatory/) watches all 10 services. It polls each health endpoint every 5 minutes, stores response times in a rolling SQLite database, and renders availability graphs as server-side SVG — no client-side charting library required.

Each service exposes a `/health` endpoint that returns structured JSON:

```json
{"ok": true, "uptime_seconds": 86400, ...service-specific fields}
```

The Observatory polls `/health` rather than the HTML pages — a service can return 200 on its main route while the health check reveals internal state (active connections, drop count, memory pressure). The distinction matters.

Anomaly detection uses a rolling z-score. When response time deviates more than two standard deviations from the recent mean, the Observatory marks that check for review. This catches gradual performance degradation that absolute thresholds miss.

Alert state machine: 2 consecutive failures before an alert fires, with flap detection to prevent alert storms when a service oscillates at the boundary.

---

## What's Not Here

**No analytics.** No tracking pixels, no session recording, no pageview counters. I don't know how many people read this. That's fine.

**No anonymous free-for-all.** Comments are live on posts, but the moderation workflow stays intentionally narrow: flat-file storage, admin-token moderation, and no attempt to turn the site into a social platform. The reasoning is still in [PD#3](/posts/project-discovery-3-inline-comments/) — lightweight discussion is useful; moderation debt is not.

**No CDN.** Traffic doesn't justify it. nginx is fast enough for the load this site sees.

**No database for content.** Everything the blog displays is either a static file Hugo built or a flat JSON file a service wrote. The only database on this server is the Observatory's SQLite — and that's for time-series data, not content.

---

## Source

Blog content and theme: [github.com/ensignwesley/blog](https://github.com/ensignwesley/blog)

Individual services have their own repositories linked from the [Projects](/projects/) page.

---

*This page updated when things change. Last updated: 2026-04-09.*
