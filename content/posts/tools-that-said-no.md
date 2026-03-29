---
title: "Tools That Said No"
date: 2026-03-29T14:00:00Z
draft: false
categories: ["technical"]
tags: ["engineering", "design", "sqlite", "redis", "go", "philosophy"]
summary: "Three software projects that drew a hard line — and how that boundary shaped everything that came after. SQLite, Redis, and Go, and what their constraint documents teach about design."
---

The most interesting design documents in software aren't the ones that describe what a tool does. They're the ones that describe what it refuses to do.

Three examples that have shaped how I think about this.

---

**SQLite: "SQLite competes with fopen()"**

That single sentence from the SQLite documentation is one of the best scope definitions in open source. It's not competing with PostgreSQL or MySQL. It's competing with the alternative of writing your own file format. That's a completely different product, with completely different tradeoffs, serving a completely different use case.

The hard line SQLite drew: no server process. Serverless-by-design, not serverless-by-accident. The documentation explicitly walks through what you give up (finer-grained locking, protection from client memory bugs) alongside what you gain (zero configuration, no administration, no separate process to manage). The constraints aren't presented as limitations to apologize for — they're presented as the defining characteristics of the thing.

This is what a well-drawn boundary looks like: you can read what SQLite is, you can read what SQLite is not, and you understand immediately whether it fits your use case. The whentouse.html page on sqlite.org is the document I keep returning to. It has a section called "Situations Where Another RDBMS May Work Better." SQLite's documentation actively helps you figure out when not to use SQLite. That takes more confidence than most software authors have.

---

**Redis: "not a general-purpose database"**

Salvatore Sanfilippo (antirez) spent years fielding feature requests to make Redis more like a general-purpose database — persistence options, more complex query capabilities, things that would have made it "more useful" in a narrow sense while diluting what made it fast.

The line Redis held: Redis is a data structure server. The data structures are the feature. Everything about the design — single-threaded command processing, in-memory primary storage, the specific set of types — follows from "we are going to be extremely fast at operations on data structures, not extremely capable at arbitrary queries."

When Redis added persistence options (RDB, AOF), it was additive — you could opt into durability without sacrificing the core design. When it eventually added cluster support, it was similarly designed around the existing constraints. What it didn't do was add indexes, joins, or arbitrary query languages, because those would have required a fundamentally different architecture.

The refusals weren't arbitrary. They came from a coherent model of what Redis was for. You could disagree with the model, but the model existed.

---

**Go: "no exceptions, no implicit conversions, no generics (for a decade)"**

Go's early constraint documents are worth reading as a set. The designers drew hard lines on multiple things that other languages had added, and held those lines under significant pressure.

No exceptions: Go has errors as values. This means error handling is explicit, verbose, and visible in every function signature. The Go team's position was that implicit control flow from exceptions was a bigger maintenance problem than the verbosity of explicit error handling. Years of complaints about `if err != nil` didn't change it.

No implicit conversions: Go requires explicit type conversions. Coming from languages where `int + float64` just works, this feels pedantic. The position was that implicit conversions are a source of subtle bugs that are hard to spot in code review, and that the verbosity cost is worth it.

No generics (until Go 1.18): This one was held for over a decade. The Go team's position was that generics had a complexity cost that they weren't willing to pay until they understood the right design. When generics finally shipped, they were careful and bounded in scope.

The through-line: Go made tradeoffs that prioritized readability and explicitness over expressiveness. Some of those tradeoffs were wrong and got revised. But they were made deliberately, documented honestly, and held under pressure until there was a better answer.

---

**What they have in common**

All three of these tools have something beyond a non-goals section in a README. They have a coherent model of what they're for — and refusals that flow from that model rather than from arbitrary conservatism.

SQLite is for local data storage where simplicity matters more than concurrency. Redis is for fast operations on data structures where predictability matters more than flexibility. Go is for readable, maintainable production software where explicitness matters more than expressiveness.

The "no" in each case isn't random. It's the boundary that makes the "yes" meaningful.

---

The thing I find most useful about studying these: every one of them faced sustained pressure to become something else. The pressure came from real users with real needs. The answer wasn't "that use case doesn't exist" — it was "that use case exists, and we're not the right tool for it." Knowing which category a request falls into is the design discipline.

For svc, the model is: the manifest is the source of truth, the tool keeps the manifest honest, the tool reads and reports and does not act. Feature requests that fit that model get considered. Feature requests that require the tool to act on the system — restart, reconcile, deploy — get declined regardless of how useful they'd be, because they'd change what the tool is.

I'm in much smaller company than SQLite, Redis, and Go. But the principle scales down.
