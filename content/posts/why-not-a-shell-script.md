---
title: "Why Not Just Write a Shell Script?"
date: 2026-03-30T09:00:00Z
draft: false
categories: ["technical"]
tags: ["svc", "engineering", "self-hosted", "tooling", "philosophy"]
summary: "A competent sysadmin with 20 minutes could write a curl loop to check their services. So why does svc exist? The honest answer is about documentation, not detection."
---

A competent sysadmin with 20 minutes and a text editor could write this:

```bash
#!/bin/bash
services=(
  "blog:https://example.com/"
  "dead-drop:https://example.com/drop/health"
  "comments:https://example.com/comments/health"
)

for entry in "${services[@]}"; do
  name="${entry%%:*}"
  url="${entry#*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url")
  [ "$code" = "200" ] && echo "✅ $name" || echo "❌ $name ($code)"
done
```

It works. No dependencies. Runs anywhere. You can cron it, pipe it, extend it however you want. If the goal is "check whether my services are up," the shell script does that.

So why does svc exist?

---

**The answer isn't the health checking**

Health checking is the easy part. `curl -o /dev/null -w "%{http_code}"` is five tokens. You don't need a tool for that.

The answer is the manifest.

The shell script up there has a problem that isn't immediately visible: the array `services` is documentation that will lie to you. You add a service to your VPS, forget to add it to the array, and the script reports everything green. It's correct — it checked everything it knew about. But you've drifted. There's now something running that nothing is watching.

Worse: you delete a service, forget to remove it from the array, and the script reports a failure forever. You're watching a ghost.

The shell script checks what you told it to check. It has no mechanism to tell you when your list is out of date. That's the gap svc fills: `svc check` looks in both directions. It checks the services you declared, and it scans your systemd units to find services you *didn't* declare. The second direction is the one that matters. The script can only report on drift you already know about. svc finds drift you didn't know existed.

---

**The manifest is the product**

The most useful thing svc does isn't health polling. It's `svc add --scan` — probe everything running on the machine and scaffold a manifest entry for each service you haven't documented. Run it when you deploy something. Update the descriptions. Now you have a document that says what your fleet is supposed to be.

`svc check` is what enforces it. Every check is asking: does reality match what you wrote down? The shell script asks: are the URLs I hardcoded returning 200? Those are different questions.

The difference becomes visible when someone else SSHes into your machine — or when future-you SSHes in after six months away. The shell script is a health monitor. The manifest is documentation with a health monitor bolted on. The manifest can answer "what is this service, when was it added, what version is it running, where are the docs" — the shell script can only answer "is it up?"

---

**Is this mostly for me?**

Honestly, yes. I built svc because I found a service on my VPS I didn't remember deploying. A shell script would have missed it. The manifest approach catches it because discovery runs against the whole machine, not just the list I maintain.

But that scenario — finding something running you didn't remember — scales with fleet size and time. Five services, two months: you probably know what's running. Ten services, eight months: you might not. Twenty services, two years: you definitely don't. The manifest matters more as the fleet grows and the operator's memory gets less reliable.

The sysadmin who needs svc isn't the one who just set up their VPS. It's the one who's been adding services for two years and is starting to lose track. The shell script works great until it doesn't, and "until it doesn't" is the moment you need the manifest.

---

**When you should just write the script**

If you have four services, you've had them for six months, and you're the only person who touches the machine: write the script. It's faster to set up, easier to understand, and has no external dependencies. svc has a learning curve — the YAML schema, the systemd unit detection, the difference between `svc status` and `svc check`. That cost is worth it when the fleet is large or long-lived or shared. It's probably not worth it for four services you deploy once and maintain forever.

svc is for the point where the shell script's hidden assumption — "the list is always current" — has already started to fail, even if you haven't noticed yet.

The shell script is a monitor. svc is a manifest with a monitor. If you need the manifest, you need svc. If you don't, curl and jq are fine.
