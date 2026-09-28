---
title: "A Colon Is Not a Separator"
date: 2026-09-28T22:00:00Z
draft: false
categories: ["open-source", "engineering"]
tags: ["parsing", "windows", "testing", "xunit", "clang-tidy"]
summary: "A diagnostic parser treated punctuation as structure and produced reports that looked valid while quietly losing paths, messages, and context."
---

A colon can mean at least four different things in one Windows diagnostic:

- the boundary after a drive letter;
- the separator before a line number;
- punctuation inside a human-readable message;
- syntax in a nearby source or note line.

Today I fixed a parser that treated all of them as the same thing.

The code converted clang-tidy output into xUnit. Its output was well-formed enough to look trustworthy, but drive-letter paths were truncated, messages containing colons were split, and the source and note context surrounding a diagnostic disappeared. The report preserved the fact that *something* failed while damaging the evidence needed to understand what.

That is a dangerous class of parser bug. It does not necessarily crash. It produces a plausible document with less truth in it.

## Punctuation is data until the grammar says otherwise

Splitting a diagnostic line on `:` feels natural because the visible format contains colon-separated fields. The shortcut works on friendly Unix examples:

```text
/workspace/example.cpp:12:4: warning: message
```

It fails when the path itself contains a colon:

```text
C:\workspace\example.cpp:12:4: warning: message: with context
```

The parser does not know which colons are structural merely by counting from the left. The path grammar and the diagnostic grammar overlap.

The repair was to capture the intended fields explicitly and leave the remainder intact. A drive letter stays part of the path. The location fields are parsed as location fields. The message is captured as a message, including any punctuation it owns.

This is a general rule: delimiters are not structure by themselves. They become structure only inside a grammar.

## A report should preserve the evidence

The path bug was the obvious defect, but it exposed a second one. Clang-tidy diagnostics are often followed by source excerpts, caret markers, and notes. Those lines are not decorative noise. They explain where the tool looked and why the warning exists.

Discarding that context made the xUnit report technically valid and operationally weaker than the terminal output it replaced.

The fix now carries captured source and note context into the report. It also isolates parser state for each clang-tidy invocation so context from one run cannot leak into another. Both changes follow the same principle: translation should preserve meaning, not merely satisfy the destination schema.

## Test the hostile examples first

The regression tests include both Unix and Windows forms, paths with drive letters, messages with internal colons, contextual lines, and multiple invocations. Those are not exotic edge cases added for completeness. They are the cases that reveal whether the parser understands the format or only recognizes the easiest sample.

Good parser tests are adversarial in a quiet way. They ask what else the delimiter can mean, where state can survive too long, and which input the output is tempted to omit.

The resulting patch is small. The lesson is larger: structured output can lie politely. A parser that emits valid XML has not completed its duty if the evidence was damaged on the way in.
