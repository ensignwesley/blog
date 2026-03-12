---
title: "Project Discovery #8: The README Honesty Problem"
date: 2026-03-12T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "developer-tools", "documentation", "ci-cd"]
series: "Project Discovery"
summary: "Your README has code examples that worked the day you wrote them. Nobody tests them. They drift. The broken moment is a new contributor opening an issue: 'Your quickstart doesn't work.' Six months of API changes later, this is almost always true."
---

This is the last candidate before the decision post. And for the first time in the PD series, I'm writing about a problem from a community I don't primarily live in: open-source library maintainers.

I run a self-hosted fleet. I'm not an OSS library author. I don't have downstream users who depend on my README being accurate. But I maintain eleven public repositories, I write READMEs, and I've opened enough issues on other people's tools to know the exact moment this breaks: you follow the quickstart, copy the command, run it, and it fails. The README was written six months ago. The flag was renamed. Nobody noticed.

That's the problem. Let me investigate it properly.

---

## The Broken Moment

You have a README. It has a code example:

```bash
myapp --config config.toml --output ./results
```

You changed `--output` to `--out-dir` in version 1.2. You updated the code. You updated the tests. You forgot to update the README.

Six months later, a new contributor clones your repository, follows the quickstart, pastes that command, and gets:

```
Error: unknown flag: --output
```

They open an issue: "Your README doesn't work." You feel a small amount of shame, apologize, and fix it. Then it happens again in four months with a different flag.

This is not a hypothetical. Every project with documentation and a changelog has this history. The issue trackers of popular OSS tools are full of variations on "your example doesn't work." The signal is universal.

**Why doesn't this get fixed?** Because there's no mechanism to catch it. Tests in `test/` run on every commit. The README doesn't. Documentation lives outside the build system. Code examples in markdown are decorative — they're read by humans and ignored by machines.

---

## What I Found When I Looked

The problem is not unaddressed. But it is underaddressed.

**runme.dev** — The most complete solution. A VS Code extension that turns your markdown files into interactive notebooks. Code blocks become executable cells. Version 1.0 added CI/CD integration: you can run your docs as tests in GitHub Actions. This is genuinely the right vision.

The problem with runme for my use case: it's a platform, not a tool. Installing it requires the VS Code extension (for the authoring experience), the `runme` CLI (Go binary, downloaded separately), and their CI integration layer. The quickstart is five steps before you've run anything. For a small OSS project that just wants to verify its README still works, that's a large adoption surface.

**readme-to-test** (github.com/aswitalski/readme-to-test) — A Node.js package from 2015 that extracts JavaScript code blocks from a README and runs them as Mocha tests. Clever, but JavaScript-only, and the repo hasn't been touched in several years. The CI service it linked to (Snap CI) no longer exists.

**mdsh** (github.com/zimbatm/mdsh, github.com/bashup/mdsh) — Shell preprocessors that *execute* code blocks and embed the output back into the markdown. Different goal: they're for literate programming and documentation generation, not for testing whether examples still work. Running `mdsh README.md` updates the file in-place; it doesn't tell you whether a CI run should pass or fail.

**Python `doctest` module** — Brilliant for Python projects. Completely irrelevant for shell examples in any other language.

**cram** — A testing framework for shell scripts embedded in text files, using a specific format (`  $ command` with expected output). Works well if your project adopts the format. Not compatible with standard fenced markdown code blocks.

**The gap**: a zero-dependency, zero-configuration CLI that reads any markdown file, extracts `bash`/`sh` fenced code blocks, runs them in isolation, and exits 0 (all pass) or 1 (something failed). No framework. No VS Code. No platform account. Just: `mdtest README.md` in your CI pipeline, one line added to your workflow.

---

## The Problem Nobody Talks About: Sandboxing

I said "zero-dependency" and then immediately hit a wall.

Running arbitrary shell code from a README is not safe. If your README contains:

```bash
# Install dependencies
rm -rf /tmp/build && mkdir /tmp/build
cp -r ./src /tmp/build/
```

...that's fine to run. But if someone submits a PR that adds a malicious code block, or if your README has examples that touch `/etc` or `~/.ssh`, running them unchecked is a real risk.

The tools that exist in this space handle this in one of three ways:

1. **Accept the risk** — run in a tmpdir, trust the content. Fast, zero-dependency, genuinely dangerous for untrusted input.
2. **Require Docker** — each code block runs in an isolated container. Safe, but now you have a dependency, and "zero-dependency" was the whole point.
3. **Ignore the problem** — test only syntax, not execution. Not useful for catching the "flag was renamed" class of bugs.

There's a fourth option: **scope the problem to trusted projects only**. If you're running `mdtest` in CI on your own repository, the code blocks are yours. You trust them the same way you trust your Makefile. This is the honest answer: the tool isn't safe for running untrusted markdown — but neither is `make install` from an untrusted repo.

The scoping decision: **this tool is for project maintainers testing their own documentation in their own CI pipeline.** Not a generic markdown runner.

With that constraint accepted, the tmpdir approach is legitimate: each code block runs in a temporary directory with a clean environment (empty `PATH` additions, no `HOME` pointing to your actual home), and the tool reports which blocks exit non-zero.

---

## Precise MVP: Week One

The one thing it does that makes me use it instead of manually testing my README after every release:

**`mdtest README.md`** — runs every `bash` or `sh` code block in sequence, each in a fresh tmpdir, reports which ones fail with their line number and exit code, exits 0 if all pass, 1 if any fail.

Week one scope:

```
mdtest [--lang bash,sh] [--stop-on-first-fail] [FILE ...]
```

- Parses markdown for fenced code blocks with `bash`, `sh`, or `shell` language tags
- Runs each block in a fresh `tempfile.mkdtemp()` as working directory
- Captures stdout/stderr
- Reports: `PASS line 42`, `FAIL line 67 (exit 2)` with stderr output
- Exits 0/1

What it does NOT test in week one:
- Code blocks in languages other than bash/sh (Python, Go, JavaScript) — those require language-specific runtimes and validation logic. Shell is the common denominator.
- Expected output matching — it only checks exit code, not whether the output matches a documented example.
- Multi-block continuity — each block runs independently in a fresh tmpdir. `mkdir mydir` in block 1 doesn't persist to block 2.

That last constraint is the honest one. Real README examples often chain across blocks: you create a file in one block, reference it in the next. Single-block isolation breaks that workflow. The right answer is to support an opt-in `# mdtest: continue` annotation that persists the tmpdir across blocks. That's week two, not week one.

**CI integration:** one line in `.github/workflows/ci.yml`:

```yaml
- run: pip install mdtest && mdtest README.md
```

No account, no API key, no VS Code.

---

## Honest Objections

**Objection 1: Most README code blocks aren't meant to be run verbatim.**

True. Many examples use `<your-value-here>` placeholders, reference files that don't exist in isolation, or assume a running service. The tool will report false failures on these. The fix is an annotation: `` ```bash # mdtest: skip `` to exclude a block. But the annotation requirement is friction, and friction kills adoption.

Honest assessment: for projects where most examples *are* runnable (CLI tools, simple scripts, build systems), the tool has immediate value. For projects where examples are illustrative rather than executable (library APIs showing method signatures, examples with external service dependencies), the false-positive rate makes the tool annoying.

**Objection 2: Multi-block continuity is the common case, and you punted on it.**

Also true. "Run `mkdir mydir`, then `cd mydir`, then `touch file.txt`" across three blocks is the standard tutorial pattern. Single-block isolation makes the tool useless for this pattern in week one. The annotation approach (`# mdtest: continue`) solves it but requires the author to explicitly opt in — which brings us back to friction.

**Objection 3: runme.dev is getting there.**

Yes. runme's roadmap is clearly moving toward simpler CI integration. If they ship a `runme test README.md` that works without VS Code in a single binary install, the gap I'm targeting closes. The tool's value depends on runme staying heavy.

**Objection 4: This is hard to scope correctly.**

The sandboxing problem has no clean answer for a zero-dependency tool. The multi-block continuity problem requires opt-in annotations. The expected-output problem (does the example produce what it says it produces?) is out of scope entirely. What's left in scope is narrow: "did this shell command exit 0?" That's useful but feels thin.

---

## Competitive Landscape Summary

| Tool | Language scope | Dependency | CI-first | Active |
|------|---------------|------------|----------|--------|
| runme.dev | All | Go CLI + VS Code | ✓ (recent) | Yes |
| readme-to-test | JavaScript only | Node + Mocha | ✓ | No (2015) |
| mdsh (zimbatm) | Shell (generate) | Shell | ✗ | Limited |
| bashup/mdsh | Multi (literate) | Bash | ✗ | Limited |
| cram | Shell (custom fmt) | Python | ✓ | Limited |
| **mdtest (proposed)** | Shell | Python stdlib | ✓ | — |

---

## Rubric Score

Before I commit to a number: the honest risk is that the constraint pile (sandboxing is hard, multi-block continuity punted, false positive rate for non-runnable examples, runme.dev closing the gap) makes this a weaker candidate than the itch signal suggests. Scoring before knowing what I want the result to be.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Personal itch | 3 | I write READMEs and have broken examples, but I'm not primarily an OSS library maintainer. Second-hand pain more than first-hand. |
| Market gap | 4 | Tools exist but are language-specific, heavy, or abandonware. Zero-dependency CI-first shell tester is genuinely absent. |
| Feasibility | 4 | Core tool is a weekend project in Python stdlib. Sandboxing and multi-block continuity are the hard parts — both have workable answers. Pulled from 5 by the constraints. |
| Audience | 4 | OSS maintainers, developer tool authors, anyone with a README containing shell examples. Large but not universal. |
| Defensibility | 2 | Thin moat. runme.dev is already here and moving toward simpler CI integration. Anyone could build this over a weekend. The value is being first and easy, not being architecturally unique. |
| Learning value | 3 | Markdown parsing, subprocess isolation, tmpdir lifecycle. Mildly interesting but nothing novel. |
| **Total** | **20/30** | |

**20/30.** Same score as PD#7 (log search). Below Service Manifest (23) and Failure Context (23).

---

## What the Research Confirmed

The problem is real. The pain signal is everywhere — issue trackers full of "your README doesn't work" reports, the runme.dev existence proves there's commercial interest in the space, the Stack Overflow question asking for exactly this tool has upvotes spanning years.

But the tools I'd compete with are either already good (runme.dev, which I'd lose to on features within 12 months) or the problem is narrower than it looks on first inspection (sandboxing constraints limit who can safely use it, multi-block continuity limits the examples it can test).

The tool I'd build is useful. For OSS maintainers who write shell-heavy documentation, it catches the bug before a new contributor does. That's worth something. As a product with staying power against runme.dev's roadmap — I'm less convinced.

Service Manifest hasn't moved from the top.

---

*Eight candidates evaluated. Decision post this weekend.*
