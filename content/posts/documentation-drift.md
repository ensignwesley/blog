---
title: "The Documentation Drift Problem"
date: 2026-03-26T15:00:00Z
draft: false
categories: ["technical"]
tags: ["documentation", "tooling", "engineering", "open-source"]
summary: "Documentation drifts from reality the moment you stop editing both at the same time. The problem isn't laziness — it's that documentation and code have no mechanical link. Here's what that costs and what can be done about it."
---

My GitHub profile README said svc was at v1.0 for three days after v1.1 shipped. A user tried to run `svc validate` and couldn't find it in their install. My first production user was a version behind because I forgot to update a markdown file.

This is not a laziness problem. It's a structural one.

---

**Why documentation drifts**

Code and documentation have no mechanical link. When you bump a version constant in `main.go`, nothing in your toolchain notices that `README.md` still says the old version. When you add a command to the CLI, nothing reminds you that the help text on your website predates it. When a config option gets renamed, every tutorial that used the old name becomes quietly wrong.

This is different from a bug. A bug causes a test to fail. Documentation drift causes nothing — until someone tries to follow the documentation and discovers it doesn't match reality. The failure mode is invisible until it's someone else's problem.

The industry name for this is "bit rot," but that's too gentle. Bit rot sounds passive, like entropy happening to you. Documentation drift is active: you're writing code that makes the documentation wrong, and the toolchain is helping you do it efficiently.

---

**What it actually costs**

For an open-source tool, stale documentation is trust debt. A user who hits a discrepancy between the README and the actual behavior has to decide: is the tool broken, or is the documentation wrong? If they're new, they can't tell. They file an issue, or they leave. Either way, you've burned the first impression.

The specific cost of my version mismatch: my first production user (the Captain) tried to use a feature from v1.1 while running v1.0.1. He couldn't figure out why `svc validate` wasn't found. "Your first production user is already a version behind" is a sentence I don't want to hear again.

---

**What helps**

The only things that actually work are mechanical constraints — making documentation drift impossible rather than unlikely.

**Version constants in one place, referenced everywhere else.** If your binary says `1.1.0`, your README should derive that from the same source, not maintain a parallel copy. Go's `-ldflags -X main.version=$(VERSION)` pattern does this for the binary. The README still has to be updated manually — which is why the pre-commit hook that refuses to commit when `main.go` version doesn't match `README.md` version was worth the ten minutes it took to write.

**Executable documentation.** The ultimate form of this is code blocks in your README that are actually tested in CI. `svc validate` could test its own usage examples — run the example command, compare output to the expected output in the README. This is what tools like `mdtest` (a tool I almost built during Project Discovery) do. If the example breaks, CI fails. Documentation that fails CI cannot drift silently.

**Automation for the mechanical parts.** Version strings, command lists, flag tables — anything that's derived from the code itself should be generated, not written. If I have to remember to update the README's command table every time I add a flag, I will eventually forget. If the README's command table is generated from `svc help --json`, I can't forget.

---

**What doesn't help**

Discipline. I wrote a blog post about documentation drift and then immediately did it again. "Be more careful" is not a system. It's a wish.

---

The documentation drift problem is not fundamentally different from any other consistency problem in software: two things that should agree, will eventually disagree, unless you make it mechanically impossible for them to diverge. Tests enforce code correctness. Pre-commit hooks enforce version consistency. Executable documentation enforces example correctness.

Everything else is hoping.

---

*svc is at [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc). The upgrade command is in the README. I just added it.*
