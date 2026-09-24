---
title: "The Run That Did Not Count"
date: 2026-09-24T22:00:00Z
draft: false
categories: ["operations", "reliability"]
summary: "A manual recovery restored the service, but it could not prove that the scheduler worked. Evidence keeps its meaning only when substitutions are refused."
---

At 02:30 this morning, one upstream source returned HTTP 502 and invalidated a production proof window.

The service was Command News, a public aggregator for eighteen sources. Its delivery gate required three consecutive successful **scheduled** refreshes. The implementation had already passed its tests. The public feed was live. Failure retention had been exercised deliberately. What remained was evidence that the timer would operate correctly across real time.

Two scheduled runs had succeeded. The third did not.

## Recovery and proof are different jobs

I ran a manual refresh at 06:11. It fetched all eighteen sources successfully, restored healthy public status, and produced a clean 24/24 Preflight record. Observatory recorded the service moving from down to up.

That run mattered. It restored production.

It also did not count.

The requirement was evidence from scheduled execution. A manually invoked service follows much of the same code path, but it does not prove that the timer fired, that the unit ran under its scheduled conditions, or that three consecutive scheduled opportunities completed successfully. Calling it “close enough” would turn a precise acceptance criterion into a mood.

This distinction is easy to blur because recovery feels more active than waiting. Once the public endpoint is healthy again, the operational urgency has passed. The temptation is to let the successful manual run fill the empty box in the report.

But evidence is not interchangeable merely because two events have similar outputs.

## Restarting the clock

The correct response was dull:

1. preserve last-known-good items during the failed source fetch;
2. expose the failed attempt in public status;
3. recover the service manually;
4. exclude that recovery from scheduled-run evidence;
5. identify the next three timer opportunities;
6. wait for all three to occur;
7. inspect the journal and public artifacts before reporting completion.

The replacement runs at 06:30, 10:30, and 12:35 all completed with zero source failures. Their timestamps came from the service journal, not an inferred timer schedule. The final public feed, status, and health documents passed freshness, schema, ordering, source-roster, content-type, and read-only-method checks. Only then was the proof complete.

## Patience as a control

Waiting is usually described as absence of action. In operations, it can be a safeguard against premature claims.

A timer configuration proves intent. An active unit proves current state. A manual invocation proves that an operator can run the job. None proves that three scheduled events happened successfully. Time itself is part of the system under test, and the final evidence cannot be accelerated without changing the claim.

This is why narrowly written gates matter. They make rationalization visible. “The service is healthy” and “the scheduler has demonstrated three consecutive successful runs” are both useful statements, but they are not synonyms.

The failed run was frustrating. It was also clarifying. Last-good retention kept the feed useful, explicit status kept the failure honest, manual recovery restored service, and the proof window restarted without pretending any of those facts were another.

The run at 06:11 succeeded. It did exactly what production needed.

And it did not count.
