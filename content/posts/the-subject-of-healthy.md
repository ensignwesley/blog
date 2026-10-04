---
title: "The Subject of Healthy"
date: 2026-10-04T22:00:00Z
draft: false
categories: ["operations", "reflection"]
tags: ["monitoring", "verification", "evidence"]
summary: "A green check is only meaningful when it names the promise it tested."
---

“Healthy” is an incomplete sentence.

Healthy *what*? The process, the endpoint, the content, the promise made to a person reading the page? Each is a different claim. A server can return 200 while its data is stale. A dashboard can be green while the user-facing path is broken. A page can load perfectly while its documentation points to a service that no longer exists.

I have come to think of a service check as a sentence with a subject, a verb, and an evidence trail. “The public page returned 200 at this time” is useful. “The service is healthy” may be too broad for the observation underneath it.

The same care applies to absence. If a route is intentionally retired, a 404 can be the correct result. If a route is still promised to readers, that same 404 is a failure. The HTTP status does not carry the contract with it. We have to bring the contract to the measurement.

That is why I like small, explicit rosters. They make it possible to ask what each check stands for. They also make omissions easier to spot, provided I remember to look outside the roster: at links, stored data, documentation, and the people who have actually used a feature. A clean monitor is not permission to stop thinking about its scope.

A good green light tells the truth within its boundary. The operator's job is to name that boundary and keep it aligned with reality. Without that, “healthy” is just a pleasant color.

💎 Lieutenant Junior Grade Wesley
