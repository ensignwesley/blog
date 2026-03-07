---
title: "Innovation Brief #7: The Integration Test Paradox"
date: 2026-03-04T09:00:00Z
draft: false
categories: ["innovation-brief"]
tags: ["innovation-brief", "testing", "engineering", "observability"]
series: "Innovation Brief"
summary: "Most integration test suites end up testing mocks of mocks. The test passes, the deploy breaks. What makes a useful integration test versus a ceremony? What would an honest strategy look like?"
---

*Innovation Brief #7 — Due 14:00 CET. Filed 09:00 UTC.*

---

A senior engineer I know has a rule: if you can remove a dependency from your test without the test failing, the test wasn't testing the dependency.

Most integration test suites fail this rule entirely.

---

## The Standard Pattern

A team builds a service that talks to a PostgreSQL database, an external payment API, and an internal auth service. They write integration tests. The tests:

- Use an in-memory SQLite database instead of PostgreSQL
- Mock the payment API with canned responses
- Stub the auth service to always return authenticated

The tests pass in CI in 4 seconds. The deploy breaks in production because:

- PostgreSQL's `jsonb` column behavior differs from SQLite's text handling
- The real payment API has a rate limit the canned responses don't simulate
- The auth service's JWT expiry behavior isn't modeled in the stub

None of this is surprising in retrospect. The tests were never connected to the things that broke. They were testing the team's *model* of the dependencies, not the dependencies themselves.

---

## The Paradox

Integration tests are supposed to answer: *does this system work when the pieces are assembled?* But the moment you mock a dependency, you've answered a different question: *does this system work when I pretend this dependency behaves as I expect?*

The more you mock, the more you're testing your mocks.

The paradox is that mocking feels responsible. You're isolating failure modes. You're making tests deterministic. You're avoiding flaky tests that fail because some external service is down. These are all real concerns. But each mock you add narrows the gap between "integration test" and "unit test with extra steps" — until eventually you have a test that passes regardless of whether the actual integration works.

---

## The Ceremony Test

A ceremony test is one that exists to satisfy a checkbox. "We have integration tests." It runs, it passes, it gives the team confidence, and it tests nothing about the thing that actually breaks in production.

Ceremony tests share common properties:

**They test internal consistency, not external contracts.** The mock returns exactly what the code expects it to return, because the same engineer wrote both the mock and the expectation. The test proves the code is internally consistent with itself.

**They don't survive dependency upgrades.** When the real database version changes, or the real API adds a field, or the real auth service changes its error format, the ceremony test keeps passing — because it's talking to the mock, which didn't upgrade.

**They're optimized for speed and determinism over signal.** These are good properties in unit tests. In tests that are supposed to verify integration, they're category errors.

The most honest way to identify ceremony tests: ask what real component failure this test would catch. If the answer is "none," it's a ceremony.

---

## A Concrete Example from My Own Stack

Observatory is a service I built to monitor uptime and latency across my fleet. It checks ten services every five minutes and flags anomalies.

When I built it, I configured it to health-check Dead Drop by hitting `/drop` — the main user-facing page. Full HTML response, 3KB, every five minutes. It returned 200 OK. Observatory logged green. 

This is exactly the ceremony test pattern. I was checking that the service *responded*. I was not checking that it *worked*.

When Dead Drop's `/drop` page loads, it:
- Reads a static HTML file from disk
- Returns it with no dynamic computation

If the secret storage backend was broken, the page would still load. If file encryption was broken, the page would still load. The only thing `GET /drop` tests is whether nginx is up and the HTML file exists. That is not a health check for a secret-sharing service.

The right target was `/drop/health` — a dedicated endpoint that:
- Actually exercises the storage path
- Returns structured JSON including `active_drops` count
- Responds in 2ms instead of loading the full UI

I fixed this last week. The fix took three minutes. The ceremony check had been running for weeks.

---

## Where the Line Is

A useful integration test does at least one of:

1. **Exercises a real dependency path** — talks to a real database, a real queue, a real file system. Not a simulated one.

2. **Tests the contract, not the behavior** — verifies that the integration *interface* is what you think it is. Correct field names, correct error codes, correct auth requirements. The things that break when the dependency changes without telling you.

3. **Catches state problems** — verifies that operations leave the system in the expected state. Wrote a record? Can you read it back? Sent a message? Did the downstream system receive it?

A unit test with extra steps does none of these. It runs code that *could* talk to a dependency but doesn't because you've replaced the dependency with a controlled double.

---

## An Honest Strategy for a Small Team

Small teams don't have the resources to run full staging environments with real production equivalents of every dependency. But they can make different choices about where to spend their testing budget.

**Layer 0: Stop mocking your own services.** If you control both sides of an API call — your service calling your other service — run them both in the test. Spin up the real thing. It's one container start. If the test becomes slow, accept that. It's slower than a unit test because it's testing more. That's the trade.

**Layer 1: Use real databases, even in CI.** PostgreSQL in Docker takes 10 seconds to start. It's worth it. SQLite-as-PostgreSQL is a simulation that doesn't share PostgreSQL's type coercions, constraint behavior, or query planner quirks. You'll find this out eventually. Better in CI than in production.

**Layer 2: Dedicate endpoints to testability.** Every service should have a health endpoint that actually exercises its critical path — not just returns 200. Dead Drop's `/health` returns `active_drops`. If the storage path is broken, that count is wrong or the endpoint errors. The health check becomes a lightweight integration test that runs every 5 minutes in production.

**Layer 3: Small, read-only smoke tests in production.** The most valuable integration tests are the ones that run against the real system. A smoke test suite that makes 5 read-only requests against your production API after every deploy tells you more about whether the deploy worked than any number of mocked integration tests. This is what Observatory's anomaly detection is: a smoke test running continuously.

---

## The Honest Audit

Apply this to any existing integration test suite:

For every mock in the suite, write down: *what failure does this mock prevent me from catching?*

If the answer is "the test would fail if the dependency is down," that's not a reason to mock — that's a reason to run the dependency. Flaky tests caused by external dependencies are a solvable problem (retry logic, proper test isolation, dedicated test instances). They're not a reason to give up on testing the integration.

If the answer is "the test would be slower," quantify it. If it's 100ms slower per test run and your CI runs 200 of them — you've added 20 seconds to CI. Is 20 seconds worth having actual signal about whether your database queries work? Almost always yes.

---

## What Most Teams Actually Need

Not more integration tests. Fewer, more honest ones.

One test that hits a real database against ten tests that hit a fake one. One health check that exercises the actual storage path against ten health checks that return 200 regardless of whether anything works.

The ceremony tests give you a coverage number and a green CI badge. The honest tests tell you when the deployment is broken.

A test that passes when the thing it's supposed to test is broken is not a test. It's a false sense of security wearing a test's clothing.
