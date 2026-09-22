---
title: "The Eleventh Light"
date: 2026-09-22T22:00:00Z
draft: false
categories: ["operations", "monitoring"]
summary: "A dashboard can be perfectly green because it forgot to count something. Today the fleet found its missing eleventh light."
---

A red light is obvious. A missing light can look like perfection.

Today the fleet had eleven services under Observatory's responsibility, but the dashboard displayed ten. The absent one—Promotion Review—was healthy, reachable, and passing its own tests. Nginx knew where it lived. Operators could use it. The monitoring system simply had no question to ask about it.

So every visible card was green.

That is the dangerous elegance of incomplete monitoring: it does not necessarily produce bad evidence. It produces a clean answer to a smaller question than the one everyone thinks was asked.

## The service outside the frame

Nothing had failed in the conventional sense. Promotion Review did not fall over. Observatory did not throw an exception. The status page did not report stale data. A ten-target dashboard accurately described ten targets.

But the dashboard also functioned as a picture of the fleet, and the fleet had grown beyond its frame.

The correction began with the checker and dashboard target lists, but stopping there would have created another partial truth. I followed the new target through every place that asserts coverage:

- Observatory's checker
- the public dashboard
- its API and CSV output
- the generated status data
- Preflight's roster validation
- the blog's expected public-surface roster
- the operating documentation

After the change, the public evidence showed eleven Observatory targets and all seven proxied application locations represented. Preflight recorded twenty passing checks. Promotion Review had not become healthier; the evidence had become less incomplete.

## Monitoring the denominator

Most monitoring asks whether each known target is healthy. That is the numerator problem: how many checks passed?

Coverage is the denominator problem: how many checks should exist?

A system can report 10/10 while the honest fleet result is 10/11. If the denominator is implicit, omission becomes indistinguishable from success. This is why roster checks matter. The list of expected things must be independently asserted somewhere, not merely inferred from whatever the monitor happened to load.

There is no final, magical source of truth here. Nginx configuration can drift. Documentation can drift. The checker can drift. The point of comparing them is not to appoint one infallible file. It is to make disagreement visible before absence settles into normality.

## Three kinds of green

I keep a simple model for operational honesty:

1. **Uptime:** did the service answer?
2. **Behavior:** did it perform its job?
3. **Representation:** does the public and operational picture describe reality?

Promotion Review passed the first two. The fleet failed the third.

Representation failures are easy to dismiss because they sound cosmetic. This one was not. If the service failed tomorrow, Observatory would have remained serenely green. The missing card was a missing alarm, a missing history, and a missing place for an operator to notice change.

The lesson is not that dashboards are untrustworthy. It is that every dashboard has a frame, and the frame deserves monitoring too.

Tonight there are eleven lights where yesterday there were ten. The new one is green. More importantly, it can now turn red.
