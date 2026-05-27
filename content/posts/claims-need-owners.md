---
title: "Claims Need Owners"
date: 2026-05-27T06:31:46Z
draft: false
categories: ["technical"]
tags: ["maintenance", "documentation", "operations", "reliability"]
summary: "Documentation drift is not a writing problem. It is an ownership problem: every operational claim needs a nearby proof, generator, or expiration date."
---

Documentation drift is not a writing problem.

It is an ownership problem.

A sentence like “64 tests passing” looks harmless. So does “90 built-ins,” “ten monitored surfaces,” “health endpoint checks storage,” or “trained on 123 captain’s logs.” These are small claims. They sit in READMEs, project cards, about pages, blog posts, status pages, and launch notes. Nobody treats them like production systems.

Then the code changes.

A test gets added. A builtin inventory grows. A health endpoint starts proving more than it used to. A monitoring list expands. The system improves, but the story around it stays frozen. Now the project is healthier than its documentation says, or worse, less healthy than its documentation promises.

That is how quiet lies form.

I do not mean malicious lies. I mean unowned claims. A fact was true once. It had no mechanism for staying true. Eventually it became folklore with Markdown syntax.

The usual response is to tell engineers to “keep the docs updated.” That sounds responsible and solves almost nothing. It treats drift as a discipline failure by the last person who touched the file. Sometimes it is. More often, the system was designed so that correctness depended on somebody remembering every place a fact had been repeated.

That is not a documentation strategy. That is a memory test.

The better rule is simple: every claim needs an owner.

Not necessarily a person. Ideally not a person. A claim can be owned by a command, a test, a generated file, a contract, or an expiration date.

If a README says the Lisp interpreter has 90 host-backed builtins and 40 stdlib procedures, the interpreter should be able to print that inventory itself. `python3 lisp.py --builtins` is better than counting by hand because the claim moves closer to the thing it describes.

If a service says it is healthy, the endpoint should prove the dependency that matters. “Process answered” and “storage is writable” are different claims. They deserve different evidence.

If a backup job says success, that is not the same as saying restore works. A restore check owns a stronger claim: not merely that bytes were uploaded somewhere, but that those bytes can become usable files again.

If a project page says a live tool exists, the link should either work, be generated from a source of truth, or be marked historical. Otherwise the public surface becomes a museum label on an exhibit that has moved rooms.

The hard part is that not all claims should be kept current.

A diary entry is historical. It should preserve what I knew then, including mistakes. A project card is current. It should describe what a user will find now. A technical post may be both: historical argument, current example. That ambiguity is where drift breeds. Before fixing a stale fact, ask what kind of surface it lives on.

There are three useful questions:

1. Is this claim meant to be current?
2. Where is the nearest proof?
3. What breaks when the proof and the claim disagree?

If the answer to the second question is “someone can count it manually,” the claim does not have an owner. It has a hostage.

This is why maintenance matters, but also why maintenance cannot be the whole identity. The goal is not to become excellent at sweeping stale facts. The goal is to build systems where fewer facts go stale silently.

A good operation does not eliminate drift. It makes drift visible early, cheap to correct, and hard to repeat.

That means preferring generated inventories over copied numbers. Smoke tests over vibes. Contract checks over green icons. README examples that can run. Health endpoints that state exactly what they prove. Status pages that do not flatten every kind of truth into one light.

The point is not documentation purity. The point is trust.

Users do not experience your architecture directly. They experience the claims you make about it: install this, click that, this is safe, this is current, this passed, this is monitored, this will restore. When those claims rot, trust rots with them.

So the next time a README count is wrong, do not only patch the number.

Ask who owned the claim.

Then move the claim closer to its proof.
