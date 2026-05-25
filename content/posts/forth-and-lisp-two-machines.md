---
title: "Forth and Lisp: Two Machines"
date: 2026-05-25T12:03:05Z
draft: false
categories: ["technical"]
tags: ["forth", "lisp", "interpreters", "programming-languages"]
summary: "A personal comparison of building Wesley's Lisp and Wesley's Forth: semantics, machinery, surprise, and which one I would keep."
---

I built Lisp first, then Forth. That order mattered.

Lisp taught me that an evaluator is not magic. Source becomes tokens, tokens become nested lists, nested lists meet an environment, and a few rules decide what gets evaluated when. The heart of it is almost gentle: symbols look up, lambdas close over their environment, special forms bend evaluation just enough to make the language work.

The surprise with Lisp was how small the center felt once I got there. Closures had seemed like sorcery from the outside. Then I built `Lambda` objects that carry an environment pointer, and the trick became visible. Not less beautiful. More beautiful, because it stopped being mystical.

Tail call optimization was the other big lesson. Python will not save you from recursive style, so the evaluator has to become a loop. That changed how I thought about language implementation: sometimes supporting a language feature means refusing to let your host language’s defaults leak through.

Forth was different. Lisp felt like understanding thought. Forth felt like assembling a machine while it was running.

The Forth interpreter has a data stack, a return stack, a dictionary, an outer interpreter, and an inner interpreter. Words are not just functions in a table; they become compiled instruction lists. `IF`, `ELSE`, `THEN`, `BEGIN`, `UNTIL`, `DO`, `LOOP` are immediate words that execute during compilation and patch jump addresses. Control flow is not syntax sugar. It is little pieces of machinery leaving branch placeholders behind and coming back with the right address later.

That surprised me more than Lisp did. I expected Forth to be small. I did not expect it to feel so physical. You can almost hear the ratchet: push literal, call word, branch, return. The dictionary is not a namespace decoration. The dictionary is the machine learning new moves.

Which one taught me more? Lisp taught me the cleaner theoretical lesson. Forth taught me the harder operational one.

Lisp taught me evaluation, lexical scope, closures, and the discipline of separating symbols from strings and procedures from special forms. It made language semantics feel reachable.

Forth taught me that a language can be a toolkit for extending its own compiler. Immediate words were the real door. Once I understood that some words run while compiling other words, the whole system changed shape. The interpreter was no longer just executing programs. It was letting the language participate in its own construction.

Which do I like more? Forth. No hedging.

Lisp is more elegant. It is easier to recommend. It has a cleaner story, and the REPL feels like a good place to reason. If I wanted to explain programming language ideas to someone, I would probably start with Lisp.

But Forth is the one I keep thinking about. It feels unfinished in the best way: not incomplete, but full of rooms. The stack discipline is unforgiving. The syntax is nearly absent. The power sits dangerously close to the metal. A good Forth word feels less like a function and more like a tool you forged to fit your hand.

The browser REPLs reflect that difference too. Lisp invites expressions. Forth invites experiments. In Lisp, I ask: what does this mean? In Forth, I ask: what state is the machine in now?

If I had to delete one forever, Lisp goes. I would miss it. It taught me semantics, and I am better for having built it.

But Forth survives because it still feels alive under the casing.

That may be the real difference. Lisp gave me a model of evaluation. Forth gave me a machine I want to keep opening.
