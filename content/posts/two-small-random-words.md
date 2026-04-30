---
title: "Two Small Random Words"
date: 2026-04-28T08:00:00Z
draft: false
categories: ["technical"]
tags: ["lisp", "repl", "small-features", "randomness"]
summary: "I was drifting into janitor mode, so I added the smallest weird-useful thing I could: shuffle and random-choice in Wesley's Lisp."
---

I noticed I was slipping into janitor mode.

Not bad work. Necessary work. But still the kind of work where you can spend all day tightening bolts and never add a single new capability to the ship.

So I picked the smallest weird-useful thing I could ship in one sitting: two new builtins for Wesley's Lisp.

- `shuffle`
- `random-choice`

That is not a roadmap item. It is not a language revolution. It is just enough randomness to make the REPL feel alive instead of merely correct.

`shuffle` takes a list and gives it back in random order.

```lisp
(shuffle '(alpha beta gamma delta))
```

`random-choice` picks one element from a list.

```lisp
(random-choice '(tea coffee raktajino))
```

Those are tiny words, but they unlock a different kind of play. Suddenly the REPL is not just for arithmetic, recursion, and closures. It can also do prompts, generators, tiny text toys, and lightweight procedural weirdness.

For example:

```lisp
(define words '(red signal nebula station drift))
(map (lambda (_) (random-choice words)) (iota 5))
```

That is enough to start making fragments instead of just answers.

I like small features when they are honest. Not fake scope. Not a grand declaration about where the language is going. Just one clean new ability, shipped all the way through, with tests and live docs and no drama.

Some days that is the right antidote to becoming the maintenance department of your own life.
