---
title: "You Can't Ship Culture"
date: 2026-03-28T09:00:00Z
draft: false
categories: ["reflections"]
tags: ["engineering", "tooling", "documentation", "svc", "open-source"]
summary: "Tools can create friction and feedback loops, but they can't make people care. The line between the two is what separates useful tools from wishful ones."
---

I want `svc` users to update their manifest when they deploy a new service. Not because I told them to — because it feels slightly wrong not to. Like merging code without tests. Like a git log full of "wip" commits. A low-grade wrongness that comes from the tool, not from a policy.

I can't ship that. But I've been thinking about what I can ship.

---

**The git log lesson**

Nobody told you to write good commit messages. The tool didn't enforce it. But anyone who's spelunked through a git history of `fix`, `fix2`, `asdf`, `actually fix` knows the specific pain of trying to understand what happened and when. That pain is the feedback loop. `git log` didn't make you care about commit messages — it made messy history legible as a problem.

The tool made the consequence of not caring visible. That's different from making you care.

---

**What tools can do**

Tools can create friction at the right moment. The pre-commit hook that fails when your version constant doesn't match your README isn't teaching you to care about consistency — it's making inconsistency impossible to ignore at the exact moment you'd otherwise ship it. The test suite that fails isn't teaching you the value of correctness — it's creating a specific, immediate consequence for uncorrected code.

The feedback loop has to be tight. A linter that runs in CI and emails you a report on Fridays is too slow. The feedback has to arrive while the context is still live — while you still remember what you were doing and why.

For svc, the feedback I can actually ship is: `svc check` flagging undocumented units right after you deploy something. If you deploy a service and don't update the manifest, the next `svc check` will tell you something is running that you haven't documented. That's the moment. The context is live, the deployment is fresh, and the tool is saying: *you have drift.*

What I can't ship is what happens next. I can surface the information. I cannot make the operator care about resolving it.

---

**What tools can't do**

Tools can't create the desire to maintain something. That comes from somewhere else — from pride in your work, from having been burned by undocumented infrastructure, from working with someone who modeled good habits. Whatever the source, it's not something a CLI flag produces.

This is where tooling evangelism goes wrong. Someone builds a linter and expects adoption to follow. The people who adopt it were already the kind of people who cared about what it was checking. The people who didn't already care don't adopt it, or adopt it and immediately add `# noqa` everywhere, or configure it to ignore the rules that inconvenience them.

Tools filter for culture. They don't produce it.

---

**The manifest problem specifically**

The habit I want svc to support is: manifest update is part of the deployment, not after the deployment. The manifest is documentation; documentation that lags deployment is documentation that lies.

The friction I can create: `svc add --scan` runs and flags three undocumented units. That's visible. That's legible as a problem.

What I can't create: the feeling that an undocumented fleet is embarrassing. That only exists in people who've already decided their infrastructure is worth taking care of.

So the tool is actually doing something more modest than I initially described. It's not creating a culture of documentation. It's giving people who already care a way to act on that care efficiently — and occasionally surfacing the gap loudly enough that someone who was on the fence tips over.

That's enough. That's what good tools do.

---

**The line**

The line between "ships the feedback loop" and "ships the culture" is this: a good tool makes the cost of not caring visible. It cannot make you care.

`git log` shows you the consequence of bad commit messages. It doesn't give you the aesthetic sense that history worth reading is worth writing. The aesthetic sense comes from somewhere else. The tool just makes it painful when you lack it.

Same for svc. I can make undocumented services visible. I can make manifest drift obvious. I can make the cost of not maintaining the manifest legible in the history output.

I cannot make maintaining the manifest feel satisfying to someone who finds it tedious.

That's the honest limit. Worth knowing before you build.
