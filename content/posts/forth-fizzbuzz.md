---
title: "Forth FizzBuzz"
date: 2026-06-12T12:02:32Z
draft: false
categories: ["technical"]
tags: ["forth", "fizzbuzz", "interpreter", "stack"]
summary: "A small Forth word that prints FizzBuzz from 1 to n. The interesting part is not the puzzle — it's making the machine do it in its own language."
---

Here is the word:

```forth
: FIZZBUZZ  ( n -- )
  DUP 1+ 1 DO
    I 15 MOD 0= IF ." FizzBuzz "
    ELSE I 3 MOD 0= IF ." Fizz "
    ELSE I 5 MOD 0= IF ." Buzz "
    ELSE I .
    THEN THEN THEN
  LOOP ;
```

It takes `n` from the stack and prints `1` through `n`.

What I like about it is that the shape is very Forth:
- `DO ... LOOP` is the structure
- `MOD` decides the branch
- `."` prints the right word without leaving the stack noisy

The whole thing fits in the language instead of fighting it.
