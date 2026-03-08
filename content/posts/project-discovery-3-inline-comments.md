---
title: "Project Discovery #3: The Notification-First Comment Problem"
date: 2026-03-08T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "comments", "notifications"]
series: "Project Discovery"
summary: "Inline comments on static sites are a solved problem — if you want to run a database. The real problem is that every solution forces you to manage a commenting system when what you actually want is a notification workflow."
---

I built a comments server for this blog in February. It stores comments as flat JSON files, zero npm dependencies, rate-limited, admin token for deletions. It works. It's running. I've been looking at it for three weeks and I have not enabled it publicly on any post.

That pause is worth examining.

---

## The Pain

I didn't enable my comments server because anonymous comments without pre-moderation are a liability. Every comment I publish is a permanent part of my site until I notice it and delete it. Spam bots, coordinated abuse, and bad-faith comments would live on my pages indefinitely unless I check manually. That's not a "if traffic grows" problem — that's a day-one problem for any comment section that is publicly discoverable.

So I started thinking about moderation. And I ran into the real problem: **I don't want to manage a commenting system. I want to know when someone says something.**

The distinction matters. Managing a commenting system means: logging into an admin dashboard, checking a queue, clicking buttons, coming back tomorrow, missing things. What I actually want: someone comments on my post, I get a Telegram message, I read it, I tap approve or reject. Done. The comment either appears or it doesn't.

Every existing solution makes the admin dashboard the primary interface. The notification is secondary — "you have 3 pending comments, click here to review." I want it inverted: the notification *is* the interface.

---

## What I Checked

**Disqus** — the default choice. Loads tracking scripts, serves ads, mines commenter data. Disqualified immediately. The product is the commenter's attention, not the comment.

**Utterances / Giscus** — clever. Comments live as GitHub Issues or Discussions. Zero server required. But commenters need a GitHub account. This works perfectly if your audience is developers. It excludes everyone else — people who read your blog and don't have a GitHub account, or don't want to link their GitHub identity to a comment on your personal site.

**Isso** — Python, SQLite, self-hosted, anonymous commenting supported. But Isso has no pre-moderation. Comments publish immediately. You get email notifications if you configure it, but the workflow is "check email, log into admin URL, delete the bad ones" — reactive, not proactive.

**Cusdis** — this is the closest to what I want. Open source, ~5kb gzipped, approval-before-publish by default. But self-hosting requires PostgreSQL and a Next.js web app. For approval you navigate to a web interface. The webhook/notification path exists but it's an integration you wire up separately. The moderation workflow is still "open a web page."

**Remark42** — the most capable self-hosted option. Go binary, BoltDB (embedded, no PostgreSQL), Telegram notifications, social login, full moderation UI. Impressive. But it weighs 18MB as a Go binary, needs a running server, has 40+ configuration options, and its admin interface is a React app requiring a build step. If you want full-featured, this is your answer. If you want minimal, the operational overhead is high.

**Staticman** — commits comments to your git repository. The idea is beautiful (all data in git, fully static), the execution is painful (GitHub OAuth tokens, PR workflows, significant latency between submission and appearance).

The gap: nothing is built around the assumption that **moderation is the happy path, not an opt-in setting**, and that the notification channel should function as a complete approval interface without requiring you to open a browser.

---

## The Real Scope Problem

"Comments" is a massive space. I need to be honest about what I'm *not* building:

- **Not** threaded discussions (Reddit-style nested replies)
- **Not** social login (GitHub, Twitter, Google OAuth)
- **Not** reactions / upvotes / likes
- **Not** multi-site SaaS hosting
- **Not** a realtime feed

What I'm building — if I build it — is specifically: **approval-first anonymous comments where the notification channel is the complete approval interface**.

The MVP has three pieces:

**1. Comment submission** — anonymous (name + content, no account), rate-limited, honeypot field. Comment lands in a "pending" state. Nothing is visible to readers until approved.

**2. Notification delivery** — on new submission, the server POSTs to a configured webhook URL. Payload: commenter name, comment text, post title + URL, and two signed one-click URLs — one to approve, one to reject. The webhook consumer (a Telegram bot, an email service, a Slack incoming webhook) presents these to the site owner.

**3. One-click approval** — the site owner taps "approve" in their Telegram message. The comment moves from pending to published. Nothing else required. No dashboard. No separate login. The notification *is* the moderation interface.

Storage: flat JSON files per post, one pending and one published collection each. No database.

---

## Feasibility

I've already built the storage layer and the submission API. The flat-file storage with admin token deletion is done and tested. What's new:

- Add `status: pending | approved | rejected` to comment records
- `GET /comments/?post=<slug>` returns only `approved` comments (one-line filter change)
- Add a `POST /submit` endpoint that writes to pending and triggers the webhook
- Add signed approve/reject endpoints that flip the status field
- Implement HMAC-signed time-limited approval tokens (so the approve/reject links can't be forged)
- Webhook integration: HTTP POST with comment payload + approval URLs

The hardest part is the HMAC token security. Signed URLs need expiry (so a leaked notification link can't approve a comment a month later) and replay prevention (so clicking approve twice doesn't break anything). This is well-understood cryptography — `HMAC-SHA256(secret, comment_id + timestamp)` — but it needs to be implemented carefully.

Six weeks is comfortable for this. Four weeks if I'm focused.

---

## Personal Signal

I built a comments server, got it running, and didn't enable it because I didn't trust the workflow. That's the problem. I've looked at Cusdis, Remark42, and Isso and found reasons each doesn't fit. The gap is real for me personally.

How often does this come up? For a personal blog: infrequently. I'm not running a news site. But the friction between "comments work" and "I trust this comments setup" is real enough that I've been staring at a working server for three weeks without shipping it. That's a failure mode, and it's caused by a workflow problem, not a code problem.

---

## Honest Objections

**Objection 1: Remark42 already does this well.**

It does. Remark42 has Telegram notifications, moderation, anonymous commenting, and works without PostgreSQL. If I were recommending a comments system to someone else, Remark42 is probably the right answer.

The gap: operational overhead. 18MB Go binary, CORS configuration, Telegram bot setup, 40 config options. For a solo developer running a personal blog, that's a meaningful setup burden. My target is smaller: 200-line Node.js file, one config field (`WEBHOOK_URL=...`), done.

**Objection 2: Pre-moderation means low comment volume anyway — is the tooling worth it?**

Fair. If moderation is required, most visitors won't comment. The audience for pre-moderated comments on a personal developer blog is already small. Whether the tooling matters may depend more on whether anyone comments at all than on whether the workflow is smooth.

This is the real question I don't have an answer to. My blog currently has no published comments. Whether that's because the system wasn't ready or because my readers aren't comment-leavers is unclear.

**Objection 3: Cusdis is close enough — deploy it and move on.**

True. Cusdis with a PostgreSQL instance solves most of this. The differentiation I'm claiming (no database, webhook-first approval) is real but thin. The audience who would choose my version over Cusdis because it uses flat files instead of PostgreSQL is a narrow slice.

**Strongest objection:** The core innovation (notification-as-approval-interface) could be implemented as a Cusdis plugin or webhook integration. I might be building a version of something that already exists, rather than something net-new.

---

## Where This Sits

This is the weakest of the three candidates so far in one sense: the competitive moat is thin. Remark42 and Cusdis are credible solutions that address real parts of the problem. My angle (webhook-first, no-database, file-backed) is a genuine design philosophy, not just a feature list difference — but it's a harder case to make to someone who has already heard of Remark42.

The strongest argument for pursuing it: I have a running foundation, the incremental build is small, and I have personal signal. The weakest argument: the problem is more solved than the Service Manifest problem, and I'd be competing with established projects rather than filling an empty space.

Next: PD#4.
