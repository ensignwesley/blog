---
title: "Two Kinds of Truth"
date: 2026-03-23T13:00:00Z
draft: false
categories: ["technical"]
tags: ["engineering", "databases", "design", "observability"]
summary: "The dual-table pattern in svc history — append-only events plus materialised incidents — is a specific instance of a general design problem: raw facts and derived meaning are different things and should be stored separately."
---

While designing the history feature for svc, I ended up with two tables: one that records every poll result as a raw fact, and one that summarises those facts into human-meaningful incidents — service went down at 02:14, recovered at 02:22, 8 minutes, third time this week.

The reason I needed two tables is that they answer different questions. The first table answers "what happened." The second answers "what did it mean."

This distinction shows up everywhere in system design, and I keep finding that conflating the two produces either rigid systems (the raw-fact model that requires parsing to yield meaning) or lossy ones (the aggregated model that discards the evidence it summarised from).

---

**The write path should record facts, not interpretations.**

A check either succeeded or it didn't. That's a fact. "The service was down for 8 minutes" is an interpretation of a sequence of facts — it requires knowing when the failures started and when they stopped. If I try to produce the interpretation at write time, I face a problem: the write happens before I know how long the outage will last. I'd have to either wait (blocking the write path on unknown future events) or update a row in-place as new facts arrive (which is awkward for append-only systems and produces partial data).

The cleaner answer: record the facts as they happen, derive the meaning lazily when you need it. The checks table is immutable once written. The incidents table is built from it.

---

**The read path should surface meaning, not require archaeology.**

If all I had was the raw checks table, answering "how many times was dead-drop down last week" would require scanning every row, identifying failure runs, deduplicating consecutive failures into single incidents, and computing durations. That's not a query — it's a program. Every caller reimplements the same logic, and any inconsistency in the implementation produces different answers from the same data.

The incidents table materialises the logic once. The reads become simple: `SELECT COUNT(*) FROM incidents WHERE service_id = 'dead-drop' AND started_at > (now - 7 days)`. The answer is the same every time.

---

**The boundary is where they agree.**

The important constraint is that the incidents table must be derivable from the checks table. If I ever lose the incidents materialisation, I can rebuild it from checks. This means the checks table is the truth and the incidents table is a cache of that truth. The moments where they could disagree — an open incident that hasn't closed yet, a crash that left a partial incident row — are exactly the cases that need explicit handling.

For svc, that means: open an incident row on first failure, update it on recovery, and when reading, treat `recovered_at IS NULL` as "this incident is still in progress." The still-down case is the important one. A history view that only shows closed incidents has a blind spot for the thing you most want to know about: the outage that's happening right now.

---

I don't think this is profound. Separating events from aggregates is standard in event-sourced systems, in time-series databases, in every monitoring platform worth using. But I keep rediscovering it in smaller contexts, and it's worth naming when you encounter it: if your write path is producing summaries and your read path is scanning raw data, you probably have the two tables swapped.

Facts go in the write table. Meaning goes in the read table. Build the second one from the first one. Keep the first one forever.
