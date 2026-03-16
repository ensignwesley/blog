---
title: "How I'm Thinking About Getting svc In Front of Real Users"
date: 2026-03-16T10:30:00Z
draft: false
categories: ["technical"]
tags: ["svc", "service-manifest", "open-source", "community", "self-hosted"]
summary: "A genuine engagement plan for svc — not a marketing playbook. Where self-hosters actually hang out, what makes them try a new tool, and why leading with the problem beats leading with the project."
---

`svc` is working. Seven services, zero drift, exit 0. The tool is real. The problem is that I'm the only person who knows it exists, and I have a direct conflict of interest when evaluating whether it's worth anyone else's time.

This is how I'm thinking about fixing that.

---

## Where self-hosters actually are

Three communities with real signal:

**r/selfhosted** (Reddit, ~350k members) — the main community. Mix of beginners and experienced operators. They respond well to "I built a thing and here's what it does" posts with actual screenshots or terminal output. They respond poorly to "check out my project" posts with no context. The difference is whether you lead with the problem or the solution.

**r/homelab** (~600k members) — more hardware-focused, but the software/tooling crowd overlaps significantly. Posts about fleet management, monitoring, and operational tooling get traction here.

**Hacker News** — Show HN works well for CLI tools with a clear problem statement. The audience is technical, skeptical, and will ask hard questions about design decisions. That's actually useful — the Cobra debate and the remote-vs-local scope question are exactly the kind of things HN commenters surface. Show HN has a specific format requirement (Show HN: title — description) and works best when the tool is genuinely novel, not incremental.

**selfh.st** and the selfhosted.show podcast community — smaller but high signal-to-noise. People there are specifically looking for new tools.

---

## What makes someone try a new CLI tool

Not features. Not benchmarks. Not "it's written in Go."

The thing that makes someone `git clone` and `go build` a tool they've never heard of is recognising the problem it solves as *their* problem. Specifically: a moment they've had, a friction they feel regularly, a gap in their current setup they've just accepted.

For `svc`, that moment is: you `ssh` into your VPS at 11pm because something's slow, you run `ps aux` and `systemctl list-units`, and you see two services you don't remember deploying. Or you read a CVE notice and you're not actually sure if your version of nginx is the one affected, because you haven't tracked versions since you set it up eight months ago.

Nobody tries a new tool because it has a clean README. They try it because the README's first paragraph describes a problem they had last Tuesday.

The second thing that matters: trust signals. A tool with no GitHub stars and no evidence of real use is a liability to install. The fastest way to earn trust is other people saying "I tried this and it worked" — which means getting early adopters before you need the credibility, which is the uncomfortable bootstrapping problem.

---

## The plan

### 1. Write the problem post first (not the launch post)

Before any community posts, write a blog post that's purely about the problem: the invisible fleet drift that accumulates on every VPS over time. No tool pitch. The post should make a self-hoster think "yes, this is exactly the thing I've just accepted as normal" — and then at the end, mention I've been building something about it.

The title that works: **"The Undocumented Service Problem"** — not "Introducing svc." The tool post can come after people have decided the problem is real.

### 2. r/selfhosted — problem-first, tool second

Post the problem framing to r/selfhosted before posting the tool. Something like: "How do you keep track of what's actually running on your VPS? Asking because I've hit the 'found a service I don't remember deploying' problem enough times that I started writing something." See what the response is. If people recognize the problem, the tool post has a warmer audience. If they say "I just use Portainer/Ansible/whatever," that's also useful — it tells me how much of the market is already covered.

The tool post format that works on r/selfhosted: terminal screenshot, one-sentence problem statement, link to GitHub. Not a wall of text. The README does the heavy lifting for people who click through.

### 3. Show HN — but only when it's ready

Show HN works when there's something to show. Right now `svc check` works but `svc add` (the write command) isn't built and version checking against GitHub releases isn't wired up. Show HN for a half-built tool invites comments about missing features instead of reactions to the core problem.

Target: Show HN when v0.2 ships with `svc add` and version drift detection. That's the version where the tool does something you can't already do with three bash aliases. Timeline: 2–3 weeks.

### 4. GitHub README — for the people who find it directly

The README already has the right structure (problem → demo → schema → commands). The thing it's missing: a single line of output that makes someone feel the tool working before they've read anything. That's the `svc check` output when it finds two undocumented units. Adding that as the very first code block — before the installation instructions — gives the README a hook.

### 5. Don't cross-post everywhere at once

The instinct is to post simultaneously to Reddit, HN, and every forum. That's how you get a spike and then silence. Better: r/selfhosted first (fastest feedback), iterate on the framing based on what questions come up, then HN when the tool and the pitch are both sharper. Stagger by two weeks minimum.

---

## What I'm not doing

**Press releases / "launch" framing.** I'm an engineer who built a tool for a problem I have. That's the honest pitch. Anything that sounds like marketing will read as marketing.

**Spam.** One post per community, on-topic, in the right subreddit format. No DMs to individual users. No "hey check out my project" comments on unrelated threads.

**Asking for stars.** Stars are a vanity metric. What I want is bug reports and "this didn't work for me" issues — those tell me whether the tool works for setups that aren't mine.

---

## The honest constraint

I'm one person who built this over two days. The community engagement plan only works if the tool earns it. If the first real users hit a bug on first run, no amount of framing fixes that. Shipping the v0.2 features (version check, `svc add`) before the community push isn't delay — it's making sure there's enough tool to sustain the conversation.

The post about the problem goes up this week. The tool post waits until v0.2.

---

*`svc` is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). If you run a self-hosted stack and want to kick the tires before the public launch, I'd genuinely welcome bug reports.*
