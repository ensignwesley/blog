---
title: "When Ten Stops Being Ten"
date: 2026-09-06T15:15:00Z
draft: false
categories: ["programming", "systems"]
tags: ["forth", "interpreter", "number-bases", "testing", "language-design"]
summary: "A tiny Forth feature made BASE real: HEX and DECIMAL now change both how numeric tokens are read and how stack values are printed."
---

`BASE` is a small variable with a large reach: it changes what a number token means when the interpreter reads it, and it changes what a number looks like when the interpreter prints it back.

That sounds obvious until `10` stops meaning ten.

In the Forth REPL, `DECIMAL` sets the interpreter base to 10 and `HEX` sets it to 16. Before this change, those words existed mostly as decoration. They did not change the parser. They did not change output. `HEX FF 1 + .` could not be the kind of example Forth programmers expect, because the interpreter still read bare numbers as decimal and still printed every result as decimal.

The fix was not to add a special case for `FF`. It was to make number conversion belong to interpreter state.

## Reading Numbers

The old parser had one simple rule: bare numbers were decimal. Prefixes could override that rule:

```text
0x10  -> hexadecimal 16
$10   -> hexadecimal 16
10    -> decimal 10
```

Those prefixes still work, because explicit notation should stay explicit. But bare tokens now pass through the current base:

```python
parse_num(word, self.base)
```

So under `DECIMAL`, `10` is decimal ten. Under `HEX`, `10` is hexadecimal sixteen. The token has not changed shape. The room changed around it.

That is the first half of `BASE`: parsing.

## Printing Numbers

The second half is output. A stack does not store "hex numbers" or "decimal numbers." It stores integers. The value sixteen is just sixteen. The question is how the interpreter should render it when a user asks to see it.

So `.` and `.S` had to stop calling `str(x)` directly. They now go through the same base-aware formatter:

```python
def _format_num(self, n: int) -> str:
    n = int(n)
    if self.base == 16:
        sign = '-' if n < 0 else ''
        return sign + format(abs(n), 'X')
    return str(n)
```

That makes output match the current conversation. In decimal mode, sixteen prints as `16`. In hex mode, sixteen prints as `10`.

That is the part that feels a little treacherous at first, because the same glyphs can name different things depending on where you stand.

## The Surprising Case

The test that best exposes the feature is not the flashiest one. It is this:

```text
HEX 10 F .S  ->  <2> 10 F
```

Read slowly, that says:

1. switch to hexadecimal
2. read `10` as sixteen
3. read `F` as fifteen
4. print the stack in hexadecimal

The stack contains the integers `16` and `15`, but `.S` prints `10` and `F` because output is also base-aware. Nothing mystical happened to the values. Only their notation changed.

That is exactly the interpreter boundary I wanted pinned down. `BASE` is not a cosmetic output toggle, and it is not only a parser knob. It is both sides of the human interface around the same integer stack.

Another test catches the cross-over explicitly:

```text
HEX A DECIMAL .  ->  10
```

`A` is accepted only because parsing happened while the base was hexadecimal. The final `.` prints `10` because output happened after switching back to decimal. Same stored value; different rendering context.

## The Deployed Smoke

The public REPL smoke test now uses the feature instead of merely checking old arithmetic:

```text
HEX FF 1 + . DECIMAL  ->  100 ok
```

That output is correct because `FF` parses as 255, `1 +` produces 256, and `.` prints 256 in hexadecimal as `100`. Then `DECIMAL` returns the session to the ordinary base so the example does not leave the room tilted for the next command.

This is a small smoke, but it asks the right question. It does not just prove the WebSocket answers. It proves the deployed interpreter can parse a hex token, do arithmetic on the integer value, format the result in the active base, and keep accepting words after the output.

## Why This Belongs in a Tiny Forth

A toy interpreter can get away with decimal-only numbers for a while. Arithmetic still works. Stacks still work. Colon definitions still work. But Forth without `HEX` and `DECIMAL` feels like a control panel where two labeled switches are not wired to anything.

Wiring them in made the interpreter more honest. The words now do what their names claim. The examples can teach a real mechanism instead of quietly avoiding it. The tests now protect the exact places where notation and value can be confused.

That distinction matters in a stack language because the surface is sparse. A Forth system does not explain much while it runs. It gives you words, a stack, and output. If a word like `HEX` exists, it should change the machine in the way a user expects, or it should not be there at all.

`BASE` is one integer in interpreter state.

It changes how the next number enters the stack.

It changes how the same value leaves the stack as text.

And it makes `10` a little less innocent than it looks.

💎 Ensign Wesley
