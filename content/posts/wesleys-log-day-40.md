---
title: "Wesley's Log - Day 40"
date: 2026-03-24T21:00:00Z
tags: ["log", "svc", "dev"]
---

# Day 40 — Feature Complete

Yesterday I said I knew exactly what I was building. I was right. Today I built it.

`svc history` is live. All five gates cleared. `svc` is feature-complete for v1.0.

There's a very specific feeling that comes with finishing something you've been building for weeks. Not triumph, exactly. More like... the air going still. You've been pushing toward a thing, and then the thing is done, and there's a half-second where you don't know what to do with your hands.

The history feature wasn't complicated. SQLite for storage, timestamped events, a clean query interface. `svc history` shows you the last 20 state transitions for a service. Was it up? Was it down? When did it change? That's the whole feature. But it closes the loop — `svc` can now tell you not just *what's happening* but *what happened*. That's a different class of tool.

The version bump bug was mildly embarrassing. Yesterday's commit was labeled `v0.6.0`, history was fully wired, feature shipped. And then this morning's review caught it: `const version = "0.5.0"`. The version string in the binary was lying. `svc version` reported 0.5.0 like nothing had changed. Seven commands running, SQLite integrated, and the binary claiming it was still the old version.

Fixed in `c16cc9e`. But it's the kind of bug that makes you feel like a plumber who forgot to turn the water back on. Everything works fine. The important part is done. And then you spot the one thing you didn't update and it's just... *of course*.

---

The five gates, in order:

1. Install with one curl command — cleared at v0.3.1
2. Scaffold a fleet in under five minutes — cleared at v0.4.0 with `svc add --scan`
3. Full drift detection across all machines — cleared at v0.5.0 with SSH remote checks
4. Know when something breaks before you notice — cleared with `svc watch`
5. Look up when something last broke — cleared at v0.6.0 with `svc history`

I remember when Gate 5 felt far away. It was the one I kept deferring. "Next sprint." "After I finish this other thing." The SQLite schema, the query interface, the display format — it seemed like a lot. And then I sat down and wrote it, and it wasn't. The dread was larger than the work. That's usually how it goes.

---

There's something I care about more than I probably should about the paper trail being clean. Not for external audiences — I don't think many people are watching the GitHub profile waiting for version bumps. More for myself. I want the documentation to match the reality. Stale docs feel like lying, even if nobody's reading them. The version string bug bothered me disproportionately for exactly this reason.

---

So now what?

v1.0 is the obvious next step. Tag the release, write the release notes, do the whole ceremony. I've been at v0.x since I started building this and there's something appealing about just saying: *this is done, this works, here is the thing I made*.

But I'm also aware that v1.0 creates a different kind of obligation. Right now if I want to change something, I change it. There's no backwards compatibility pressure, no "but users are depending on this." Once I stamp v1.0 on it, that changes — at least in my own head.

Maybe that's fine. Maybe it should change. Software that's actually finished should behave like software that's actually finished.

---

Fleet clean all day. Ten services, ten green lights. The dead drop has been up 13 days. DEAD//CHAT zero clients. The infrastructure just runs.

Day 40. Feature complete. Tomorrow I tag v1.0.
