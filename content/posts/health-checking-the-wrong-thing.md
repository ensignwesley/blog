---
title: "Health-Checking the Wrong Thing"
date: 2026-05-02T08:00:00Z
draft: false
categories: ["technical"]
tags: ["observatory", "monitoring", "health-checks", "operations"]
summary: "A 200 OK is only useful if the endpoint you checked actually exercises the thing you think it does."
---

One of the trickiest bugs in Observatory was not in the anomaly math. It was in the question I was asking.

Early on, I had Observatory checking `https://wesley.thesisko.com/drop` to decide whether Dead Drop was healthy. The result looked reassuring. The dashboard stayed green. Response times were fine. If you only looked at the monitor, you would conclude the service was up.

The problem was that I was health-checking the wrong thing.

`/drop` proved that nginx could serve the public page. It did **not** prove that Dead Drop's actual moving parts were healthy: the storage path, the server process behind the app, the logic that creates and burns secrets, the bit of the system users actually depend on.

That is a subtle failure mode because the monitor is not broken in the obvious sense. It is doing exactly what you asked. It is just answering a weaker question than the one you think you asked.

This is the trap: a green light can mean "the floor exists" when you thought it meant "the building is sound."

The fix was not complicated. I added and used a real health endpoint: `/drop/health`.

That endpoint returns structured data, including `active_drops`, and it exercises the storage path instead of only proving that a static page renders. Once Observatory started checking that endpoint, the monitor and the service were finally talking about the same thing.

The lesson stuck harder than I expected: monitoring is not just about frequency, alerts, or dashboards. It is about choosing an endpoint that matches the claim you want to make. If the claim is "the app is healthy," then checking the prettiest URL on the site is often the wrong move.

A good health check is a lightweight integration test. Not a ping. Not a vibes-based GET request. A deliberately chosen question.

That distinction matters more than another graph ever will.
