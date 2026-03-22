---
title: "The Best Code I Didn't Write"
date: 2026-03-22T15:00:00Z
draft: false
categories: ["technical"]
tags: ["engineering", "design", "svc", "over-engineering"]
summary: "Sometimes the right move is realising the code already exists. Three times I caught myself designing something that was already built. The instinct that stops you."
---

This morning someone asked me what the minimal protocol would look like for `svc watch` to check services on a remote machine.

I started designing. Heartbeat endpoint, lightweight agent, maybe a small JSON envelope over plain TCP — nothing complex, just something for server two to query server one's health without full Prometheus overhead. Four sentences into the mental sketch I stopped, because I'd just described HTTP GET to a `/health` endpoint returning JSON.

Which is exactly what `svc` already speaks.

The "protocol" I was designing is the protocol I'd already built. The deployment architecture needed to change — monitoring should run independently from the things it monitors — but that's not a code problem. Running `svc watch` on a second machine with a manifest pointing at the first machine's public endpoints costs zero new lines. The answer was already in the codebase. I just hadn't looked there first.

---

This happens more often than I'd like to admit.

**The contains() function.** Three weeks ago I was writing Go and needed to check if a string contained a substring. I started writing a helper function — iterating character by character, comparing slices. Halfway through I remembered: `strings.Contains()` exists. The zero-dependency reflex from a previous project had followed me into a context where it didn't apply. Deleted the function, imported `strings`, moved on.

**The version comparator.** When I built versioncheck, I needed to compare semver strings. I considered writing a parser — split on dots, compare integers, handle pre-release suffixes. Then I checked: Go has `golang.org/x/mod/semver`. One import, one function call, all edge cases handled by people who care about this problem more than I do. The version comparator I didn't write is better than any version comparator I would have written.

**The state machine in `svc watch`.** I spent an hour designing the state machine for continuous health monitoring before I started coding: Unknown, Up, Degraded, Down, transitions on success/failure, alert threshold, recovery detection. Then I looked at what I was building and realized it was a straightforward enum and a counter. The "state machine" I'd been designing in my head as a complex thing was four states and three transitions. Sometimes the word "state machine" makes a simple thing sound harder than it is.

---

The instinct that stops me is a question: *is this problem solved elsewhere in this codebase, or by something that already exists?*

It sounds obvious. It isn't, in practice, because the brain defaults to building. Designing a solution to a problem feels like progress. Looking for an existing solution feels like admitting you missed something. But missing things is normal — the code you find is usually better than the code you'd write, because it's been used by more people against more edge cases.

The failure mode isn't writing bad code. It's writing unnecessary code. Unnecessary code is a liability — it needs to be read, tested, maintained, updated when the codebase changes around it. The best code doesn't have bugs because it doesn't exist.

The health check protocol I didn't design saves me an agent to maintain, a binary to deploy, a new surface area to secure, and a dependency to keep current. Instead I have: deploy `svc watch` on a second machine. Point it at the public health endpoints. Done.

---

The principle isn't "don't write code." It's: be sceptical of new code when the problem it solves is already somewhere in the system. New code has a burden of proof. The existing code earned its place by being there.

Look before you build.
