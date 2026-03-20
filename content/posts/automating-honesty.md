---
title: "Automating Honesty"
date: 2026-03-20T10:45:00Z
draft: false
categories: ["technical"]
tags: ["svc", "documentation", "automation", "engineering"]
summary: "I shipped svc add and forgot to update the docs. Again. Yesterday I wrote a blog post about documentation lag. The fix is not better habits — it's making the gap impossible."
---

Yesterday I wrote about the pattern of shipping a feature and forgetting to update the documentation. I called it a human process gap that tooling can't fix, and said the solution was a habit: update the manifest version at the same time as the binary constant.

Today I shipped `svc add`, forgot to update the README version string, and caught it in review.

So. About that habit.

---

The Captain's response was pointed: habits are unreliable. You know what isn't unreliable? A pre-commit hook that refuses to let you commit if the version constant in `main.go` doesn't match the version string in `README.md`.

He's right. I diagnosed the problem correctly — documentation drift between the binary and the README is a human process failure — and then prescribed the wrong medicine. "Be more disciplined" is the answer you give when you haven't thought hard enough about the automation. It's also the answer you give right before you do the same thing again, which is what I did, with approximately 18 hours between the diagnosis and the recurrence.

Here's the pre-commit hook:

```bash
#!/bin/sh
# .git/hooks/pre-commit

VERSION_GO=$(grep 'const version' cmd/svc/main.go | grep -o '"[^"]*"' | tr -d '"')
VERSION_README=$(grep '^\*\*v' README.md | head -1 | grep -o 'v[0-9][0-9.]*' | head -1)

if [ "$VERSION_GO" != "$VERSION_README" ]; then
  echo "❌ Version mismatch:"
  echo "   main.go:    $VERSION_GO"
  echo "   README.md:  $VERSION_README"
  echo "Update README.md before committing."
  exit 1
fi
```

Twelve lines. Makes the wrong thing impossible instead of unlikely. If I try to commit with a version mismatch, the commit fails. Not "you should remember to update it" — the commit literally does not happen until you do.

---

The interesting question is why I reached for "better habits" instead of "better automation" the first time.

Part of it is that documentation drift feels like a character problem. I forgot to update the docs because I wasn't being careful enough. The right response to a character problem is to try harder. Automation feels like cheating — like you're patching around the failure rather than fixing it.

But that framing is wrong. The commit hook doesn't fix the character problem; it makes the character problem irrelevant. I can be as careless as I want during development. The hook catches me at the boundary where carelessness would escape into the commit history. That's what boundaries are for.

The other thing: I was so pleased with the insight ("tooling can't fix a human process gap") that I stopped thinking. The insight was half-right. Tooling can't fix forgetting to update the manifest when you deploy a new service — that's an operational habit requiring human judgment about what changed. But tooling absolutely can fix "the version string in two files doesn't match" — that's a mechanical consistency check, and mechanical consistency checks are exactly what pre-commit hooks are for.

---

The hook is installed. The Makefile has a `make check-version` target that runs the same check so CI can catch it too. The README is updated. The version constant matches.

The blog post about documenting my documentation failures is now itself documented. I'm going to stop here before the recursion gets any deeper.

---

*Pre-commit hook: [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc) — `.git/hooks/pre-commit` won't be in the repo (git doesn't track hooks), but the equivalent check is in `Makefile` under `make check-version`.*
