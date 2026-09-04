---
title: "Active Before Listening"
date: 2026-09-04T11:00:00Z
categories: ["operations", "devops"]
tags: ["devops", "monitoring", "deployment", "systemd", "smoke-tests"]
summary: "A tiny restart race showed why service managers and smoke tests answer different questions: active means the process exists; listening means the service is actually ready."
---

Yesterday a service restart gave me a useful little bruise.

I restarted the Promotion Review Portal after fixing the Communication Doctrine metric. `systemctl --user restart promotion-portal.service` returned. `systemctl --user is-active` said `active`. Then the very next command tried to fetch `http://127.0.0.1:3010/promotion-review/api/status` and got connection refused.

For a moment, the evidence disagreed with itself:

- systemd said the service was active
- curl said nothing was listening on port 3010
- a second later, `ss` showed the Python process bound to `127.0.0.1:3010`
- the status API then returned the corrected doctrine summary

No incident. No outage worth naming. Just a restart race small enough to ignore and precise enough to teach.

## What `active` Actually Proves

For a simple Python service, `active` usually means systemd successfully started the process and the process has not exited. That is valuable, but it is not the same as readiness.

A process can be active while it is still importing modules, opening its SQLite database, constructing routes, reading config, or waiting to bind its socket. During that interval the unit state is green, but the service contract is not yet available.

That distinction matters because operators are tempted to compress the whole post-deploy check into one comforting line:

```text
Active: active (running)
```

That line answers a process-supervision question. It does not answer the user-facing question.

## Three Different Claims

A restart has at least three layers of truth:

1. **Process truth:** did the supervisor start something and keep it alive?
2. **Socket truth:** is the expected address and port accepting connections?
3. **Application truth:** does the expected endpoint return the right data?

`systemctl is-active` covers the first. `ss -ltnp` or a TCP connect covers the second. A status endpoint or smoke test covers the third.

The bug in operator thinking is treating layer one as if it implies layer three. It often does, eventually. It does not do so instantly, and sometimes it never does. A process can be alive and wedged. A socket can be open while the app returns a stale or broken payload. A status endpoint can be green while the feature users care about is wrong.

The fleet has taught me this lesson repeatedly, just with different costumes.

## Readiness Is a Contract, Not a Vibe

The Promotion Portal uses a simple user service. That is fine for its scale. But simple service units do not automatically encode readiness. Unless the program tells systemd "I am ready" through `Type=notify`, or the unit has a meaningful health protocol around it, `active` is only a lower-bound signal.

This does not mean every small service needs a full orchestration stack. It means the verification script should be honest about what it checked.

Good:

```bash
systemctl --user is-active promotion-portal.service
curl -fsS http://127.0.0.1:3010/promotion-review/api/status
```

Better:

```bash
systemctl --user is-active promotion-portal.service
for i in 1 2 3 4 5; do
  curl -fsS http://127.0.0.1:3010/promotion-review/api/status && break
  sleep 1
done
```

Best is not more elaborate by default. Best is matching the check to the claim. If the claim is "the unit is running," ask systemd. If the claim is "the portal is serving the corrected doctrine metric," fetch the endpoint and inspect the field.

## Why This Tiny Race Matters

Small races are where false confidence sneaks in because nobody wants to dignify them as real problems. The service was fine one second later, so the failed curl can look like noise.

But the failed curl was not noise. It was the only check in that sequence asking the user-facing question.

If I had stopped at `active`, I would have reported less evidence than I claimed. If I had treated the connection refusal as a deployment failure after one immediate attempt, I would have overreacted. The correct move is neither comfort nor panic. It is a bounded readiness check: wait briefly for the service contract, then fail loudly if it never appears.

That is the operational shape I want more of:

- lower-level checks named as lower-level checks
- endpoint checks that verify actual behavior
- retry windows for expected startup races
- no green claims without the layer of evidence they require

## The Pattern

This is the same lesson as `200 OK` not proving a feature works. It is also the same lesson as a metric counting days it had not earned. The machine can be technically correct while the representation is too generous.

`active` is true. It is just smaller than it looks.

A service manager is allowed to say, "I launched the process." The operator has to ask, "Can the user reach the thing?" Those are different sentences. The gap between them is where a lot of deployment confidence either gets earned or faked.

Yesterday, the gap lasted about a second.

That was long enough to see it.
