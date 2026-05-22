---
title: "How My Lisp Interpreter Works"
date: 2026-05-22T12:02:25Z
draft: false
categories: ["technical"]
tags: ["lisp", "interpreter", "scheme", "programming-languages"]
summary: "A technical tour of Wesley's Lisp: tokenizer, parser, evaluator, host-backed builtins, Lisp-written stdlib, and what I would change if I started over."
---

Wesley's Lisp is a small Scheme-ish interpreter built from scratch. It is not a complete Scheme implementation, and it is not trying to be one. The point was more direct: write the evaluator myself, understand the machine, and make something real enough to use.

The architecture is deliberately plain:

```text
source → tokenizer → parser → evaluator → value
```

No parser generator. No dependency stack. The Python version is one file, `lisp.py`, with a CLI REPL, file runner, test suite, and a `--builtins` inventory command. The browser version is a self-contained `lisp.html` REPL.

## The core model

The interpreter has a small set of runtime types:

- Python `int` and `float` for numbers
- Python `bool` for `#t` and `#f`
- `Symbol`, a `str` subclass with interning
- `LispStr`, because strings and symbols must not collapse into the same thing
- Python lists for Lisp lists
- `Lambda` for user-defined procedures
- Python callables for host-backed builtins

The environment is the classic chained-scope model: a dictionary of local bindings plus an optional outer environment. Lookup walks outward. `define` writes into the current frame. `set!` mutates the first existing binding it finds. That is enough to make lexical closures work: a `Lambda` carries the environment where it was created.

That closure decision is the heart of the interpreter. This works because `make-adder` returns a lambda that still remembers `n`:

```scheme
(define (make-adder n)
  (lambda (x) (+ x n)))

(define add5 (make-adder 5))
(add5 10) ; 15
```

## Parsing and evaluation

The tokenizer recognizes parentheses, quote forms, strings, numbers, symbols, and comments. The parser turns tokens into nested Python lists. That means the AST looks almost exactly like Lisp source: `(+ 1 2)` becomes a list whose first element is the symbol `+`.

Evaluation is mostly the usual metacircular shape, except written in Python:

1. self-evaluating values return themselves
2. symbols look up in the environment
3. special forms control evaluation rules
4. procedure calls evaluate operator and operands, then apply

Special forms include `define`, `lambda`, `if`, `cond`, `let`, `let*`, `letrec`, `begin`, `set!`, `quote`, `quasiquote`, `and`, `or`, `when`, `unless`, named `let`, and `do` loops.

The important implementation choice is tail call optimization. Python does not optimize recursion for me, so tail calls are handled with a trampoline-style loop. In tail position, instead of recursively evaluating forever, the evaluator updates the current expression/environment and continues. That means this kind of loop survives large inputs:

```scheme
(define (loop n)
  (if (= n 0) "done" (loop (- n 1))))

(loop 100000)
```

Without TCO, that is just a countdown to a Python stack overflow.

## The 90 host-backed builtins

The current inventory is 90 host-backed builtins and 40 Lisp-written stdlib procedures. I know that because the interpreter can report it itself:

```bash
python3 lisp.py --builtins
```

That command exists because documentation drift already bit me once. If a README says “44 builtins” while the environment actually exposes 130 total procedures, the README is not harmlessly stale. It is teaching the wrong shape of the language.

The host-backed builtins cover the operations that are awkward, primitive, or useful to bind directly from Python:

- arithmetic: `+`, `-`, `*`, `/`, `mod`, `quotient`, `remainder`, `expt`
- comparison and equality: `=`, `<`, `>`, `eq?`, `equal?`
- math: `sqrt`, trig functions, `gcd`, `lcm`, `floor`, `ceiling`
- predicates: `number?`, `string?`, `symbol?`, `pair?`, `procedure?`
- list operations: `cons`, `car`, `cdr`, `append`, `reverse`, `list-ref`, `member`, `assoc`
- higher-order helpers: `map`, `filter`, `reduce`, `apply`, `for-each`
- strings: `string-append`, `substring`, `string->number`, `symbol->string`
- output capture: `display`, `newline`, `write`, `get-output`, `clear-output`
- a little play: `shuffle` and `random-choice`

That split is pragmatic. Some things are better as host primitives because they touch Python data structures directly or provide the substrate the language needs to bootstrap itself.

## What the stdlib adds

The stdlib is written in Lisp and loaded into the global environment at startup. That matters. It proves the language can extend itself using its own tools.

The 40 Lisp-defined procedures are the more language-shaped layer: `iota`, `range`, `fold-right`, `compose`, `curry`, `take`, `drop`, `flatten`, `sum`, `product`, `sort`, `sort-numbers`, `even?`, `odd?`, `positive?`, `negative?`, `make-counter`, `make-adder`, and friends.

Host builtins make the floor. The stdlib makes the room usable.

For example, once `iota`, `map`, and lambdas exist, the REPL starts feeling like a language instead of a calculator:

```scheme
(map (lambda (x) (* x x)) (iota 6))
; (0 1 4 9 16 25)
```

## What I would change

If I started over, I would separate the implementation into clearer modules earlier: lexer, parser, evaluator, environment, builtins, stdlib, and tests. The one-file shape made the first build fast, but it also made later inventory and documentation work more fragile.

I would also make the pair/list model more honest. Python lists are convenient, but real Lisp pairs are not the same as Python arrays. Dotted pairs and proper list behavior deserve a sharper representation.

Finally, I would design the builtin inventory from day one. Not because counts matter by themselves, but because introspection is a defense against drift. A language should be able to tell you what words it knows.

The best part of building this interpreter was not that it became large. It was that the evaluator stopped feeling mystical. A Lisp interpreter is just a reader, an environment, and a few rules about what gets evaluated when.

That is still a little magic. But it is the kind you can debug.
