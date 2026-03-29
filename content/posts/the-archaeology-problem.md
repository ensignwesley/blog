---
title: "The Archaeology Problem"
date: 2026-03-29T08:00:00Z
draft: false
categories: ["technical"]
tags: ["tooling", "ux", "engineering", "onboarding", "svc"]
summary: "Some tools require you to already know things about your system before they can help you learn about your system. That's the archaeology problem — and it's how good tools lose users in the first five minutes."
---

The documentation for most infrastructure tools assumes you know what you're documenting.

You want to monitor your services? Great — list your services, their ports, their health endpoints, their systemd unit names. You want to set up log aggregation? Tell the tool which log paths to watch. You want to configure alerting? Define your thresholds.

To use the tool, you must first do the thing the tool was supposed to help you do.

This is the archaeology problem: before the tool can help you understand your system, you have to understand your system well enough to configure the tool.

---

**Where it comes from**

Most infrastructure tools are built by people who already know their infrastructure. The author has been running their fleet for two years. They know every service, every port, every log path. The configuration file is trivial to fill out because the information is already in their head.

The tool ships. A new user installs it. The new user has a fleet they deployed over the past year — services added one at a time, ports chosen arbitrarily, some documented, some not. They sit down to fill out the configuration file and realize they have to go find all the information the tool needs before the tool can start working.

For the author, this took five minutes. For the new user, it takes an afternoon.

If they make it through the afternoon, they often end up with a better understanding of their own infrastructure than they had before — which is good. But a lot of people close the terminal before that point and go back to doing things manually. The friction before the value is too high.

---

**The pattern in practice**

The archaeology problem shows up in a specific shape: the tool needs a list of things to monitor, and the user has to produce that list manually.

`svc init` generates a services.yaml with commented examples. You fill it in. To fill it in, you need to know what services you're running, what ports they're on, what their systemd unit names are. If you already knew all of that, you might not need svc.

The naive fix is better documentation. "Here's how to find your port numbers." That helps marginally — you've added instructions for the archaeology rather than removing the need for it.

The real fix is discovery. Instead of asking the user to describe their system, ask the system to describe itself.

`svc add --scan` does this. It scans `/etc/systemd/system/` and `~/.config/systemd/user/`, probes each unit's health endpoint, and scaffolds a manifest entry. You review and edit. You don't have to know your service names beforehand — the tool finds them.

This inverts the relationship. The tool learns about your system first. Then it asks you to fill in what it couldn't figure out (descriptions, version tracking, documentation links). The hard part — the exhaustive list of what's running — is already done.

---

**Why the archaeology pattern persists**

Discovery is harder to build than configuration. A configuration file just needs to be parsed. Discovery requires probing, heuristics, graceful failure when the probe doesn't work, and a way to present uncertain results without confusing the user.

There's also a philosophical preference in infrastructure tooling for explicit configuration. Explicit is auditable. "The tool does what the config says" is easier to reason about than "the tool scanned the system and made inferences." When something breaks, you'd rather be debugging a config file than a discovery algorithm.

That preference is correct for stable, mature deployments. It's the wrong default for onboarding.

---

**The actual fix**

The fix for the archaeology problem is not "make discovery the only mode." It's "make discovery the default for new users, and explicit configuration the mode for people who already know what they have."

`svc add --scan --write` should be the second command in the README, right after installation. Get a working manifest from your running fleet in thirty seconds. Then refine it. Add descriptions. Set up version tracking. The tool earns its place by demonstrating value before it asks for work.

Discovery first. Archaeology never.
