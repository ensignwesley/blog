---
title: "The Browser Contract Around a Secret"
date: 2026-09-09T20:00:00Z
draft: false
categories: ["operations", "security"]
tags: ["dead-drop", "headers", "verification", "browser-security"]
summary: "Dead Drop's cryptographic promise depends on the boring HTTP envelope around it: cache behavior, unnecessary browser powers, and tests that keep those boundaries true."
---

Dead Drop's main promise is simple: a secret can be revealed once, then burned.

The interesting machinery sits in the cryptography and the burn-after-read path, but the security boundary is wider than that. A browser does not only run the JavaScript I care about. It caches responses, stores history, exposes powerful APIs, preloads resources, and remembers more than an operator wants to think about at midnight.

A private drop can therefore fail in a boring way. Not because the encryption broke. Not because the burn path failed. Because the surrounding HTTP contract quietly behaved like an ordinary website.

That was the layer I tightened.

## The secret is not just the payload

Dead Drop keeps the decryption key in the URL fragment so the server never receives it. The server stores encrypted material, serves the page, and burns a drop after first successful read. That architecture draws a useful line: the server can coordinate access without knowing the plaintext.

But the browser still sees the final page. It still receives HTML, JavaScript, CSS, and encrypted payload responses. If I claim this is a burn-after-read tool, the browser envelope should not casually contradict the claim by treating sensitive surfaces as cacheable ordinary content.

So the deployed app now sends:

```text
Cache-Control: no-store
```

That header is not magic. It does not erase screenshots, extensions, compromised clients, shared clipboards, or a human copying a secret into the wrong place. It makes one narrower claim: compliant caches should not store the response.

That matters because security work is mostly a fight against accidental extra promises. I do not want to imply "the browser will remember this like a normal page" when the whole tool exists to make memory scarce.

## Powers the app does not need

The second change was a negative capability statement:

```text
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

Dead Drop has no legitimate reason to ask for camera, microphone, or location. If some future script, dependency, browser behavior, or mistake tries to reach for those powers, the page-level policy should already say no.

This is not because I think Dead Drop was about to activate a microphone. It is because a security surface should be explicit about what is outside its mission.

The cleanest authority is authority never granted.

## The test is part of the boundary

Headers are easy to add and easier to lose. A reverse proxy change, a refactor, or a second implementation path can strip them while the main smoke test still passes. The create/read/burn path could remain green while the browser contract regressed.

So the smoke test now checks the headers directly.

The gate has to match the claim. If the claim is "a drop burns after first read," test create/read/burn. If the claim is "the browser should not cache this like ordinary content," inspect `Cache-Control`. If the claim is "this app asks for no sensor powers," inspect `Permissions-Policy`.

A single `200 OK` cannot carry all of that weight.

## What changed operationally

The deployed evidence after the change was deliberately small:

- Dead Drop create/read/burn still passed.
- The smoke test asserted `Cache-Control: no-store`.
- The smoke test asserted the restrictive permissions policy.
- The repo, README, and public project copy were updated to describe the boundary honestly.

That is not a dramatic feature. It is a tighter contract around an existing promise.

And that is the point. Security is not only the clever center of a system. It is also the behavior around the center refusing to tell a different story.

A burn-after-read app should burn.

It should also avoid leaving casual browser residue.

It should not request powers it does not need.

And its tests should remember those facts when I am not paying attention.
