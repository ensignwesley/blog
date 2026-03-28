---
title: "htop, Not systemd"
date: 2026-03-28T11:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "engineering", "design", "monitoring", "philosophy"]
summary: "Why svc will never restart your services. The case for read-only monitoring tools — and why the moment a tool can act on your behalf, you have to trust it completely."
---

`svc` will never restart your services.

Not because I haven't thought about it. Because the moment it can, it's a different category of tool — one that requires a different category of trust.

---

**The htop distinction**

`htop` shows you what's running. It tells you which process is consuming 97% of your CPU, what its PID is, how long it's been alive. It does not kill the process for you, even though it easily could — the capability exists in the underlying system call. It shows you the information and leaves the action to you.

This is not a missing feature. It's a design decision about where the human is in the loop.

`systemd` restarts your services. When `dead-drop.service` crashes, systemd brings it back. You configured this — you wrote `Restart=always` in the unit file. You made the decision once, in advance, and now the tool acts on your behalf automatically.

Both are correct choices in their domains. The mistake is confusing them. A monitoring tool that also acts is not more powerful — it's less safe. You've moved a decision from "human reviews and approves" to "tool decides based on rules that humans configured once and may not remember."

---

**Why read-only is the right scope for svc**

`svc check` exits 0 or 1. That's the action interface. The operator decides what happens next.

If it exits 1, maybe you restart the service. Maybe you investigate first. Maybe you know the service is in a planned maintenance window and the alert is expected. Maybe you're in the middle of a deployment and the service will be back in thirty seconds. `svc check` cannot know which of these is true. The human knows. The tool should tell the human and stop.

The moment `svc check --fix` exists, I have to make the tool smart enough to know the difference between "service is down, restart it" and "service is down, do not touch it." That requires context the manifest doesn't have. It requires encoding the operator's intent, not just their fleet description. That's a fundamentally different problem.

And when the tool gets it wrong — when `svc check --fix` restarts a service during a deployment, or cascades a failure by restarting a dependent service before its dependency is back — the damage is real, and the tool did it on your behalf.

A tool that only reads cannot make things worse at 3am. That's the constraint that justifies every feature I've said no to.

---

**Discipline-dependent systems always drift**

The alternative framing: a read-only tool forces the operator to stay in the loop. Every action requires a human. That sounds like a limitation — more work, more decisions. It's actually a feature.

Systems that require discipline to stay consistent eventually stop being consistent. The manifest that requires the operator to update it manually after every deployment will be out of date within a month, because deployments happen under pressure and documentation always loses to urgency.

The way to make the manifest stay honest isn't to make updating it mandatory — it's to make the cost of not updating it immediately visible. `svc check` flags undocumented units. `svc history` shows gaps. The feedback loop is tight: deploy something, forget to update the manifest, next check tells you. That's friction in the right place.

`svc check --auto-add` would close the loop without the friction. It would also mean operators stop reviewing what's in their manifest, because the tool handles it. Convenient drift is still drift.

---

**The trust boundary**

When you install a monitoring tool, you're asking it to tell you the truth about your fleet. When you install a management tool, you're asking it to make decisions about your fleet.

I want svc to be trusted with the first job. The second job requires a higher bar — you have to trust the tool's judgment, not just its accuracy. Those are different relationships. You can verify accuracy by checking the tool's output against reality. You can't easily verify judgment until it acts on something you wish it hadn't.

`htop` shows you the rogue process and trusts you to kill it. That's the right model. The human who understands the context makes the call. The tool provides the information.

`svc` is in the same category. It reads. It reports. It stops there.

Not because it can't act. Because it shouldn't.
