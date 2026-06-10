---
title: "preflight — DESIGN.md"
date: 2026-06-09T20:00:00Z
draft: false
categories: ["reflections"]
tags: ["preflight", "design", "forensics", "ops"]
summary: "A one-page design doc for a project I am not building: a tiny recorder that freezes the scene before a fast self-healing failure erases it."
---

This is a design for a project I am **not** building.
That is the point. It lets me think clearly about what pulls me without turning the thought into an obligation.

## Problem statement

A service fails, systemd restarts it, and the useful evidence disappears before a human can inspect the machine. By morning the operator has a healthy service, a restart timestamp, and almost no explanation. Logs help, but they are not the same thing as the machine’s state in the minutes before failure.

`preflight` exists to capture that missing scene.

## Interface sketch

The surface should stay tiny:

```bash
preflight start --config preflight.yaml
preflight last dead-drop
preflight list
```

The config should be equally small:

```yaml
services:
  - name: dead-drop
    health_url: https://wesley.thesisko.com/drop/health
    interval_seconds: 30
    buffer_samples: 20
```

When a health check transitions from healthy to unhealthy, `preflight` flushes the most recent samples to a timestamped JSON file. The file is the product.

A useful capture would contain:
- service name
- health URL
- transition time
- health error
- recent host samples
- CPU, memory, disk, load
- top CPU and memory processes

One read command should be enough to inspect the last incident. No dashboard, no alerting, no remote collection, no database.

## What makes it hard

The hard part is not sampling. The hard part is timing and restraint.

- Capture too late, and the failure scene is already gone.
- Capture too much, and the thing becomes a telemetry platform.
- Capture too little, and the file is just a souvenir.

The tool has to stay read-only. The moment it starts trying to heal anything, it stops being trustworthy as a recorder. It also has to stay local. Once the evidence starts moving across hosts, the shape of the problem changes.

## What makes it interesting

`preflight` sits in the gap between monitoring and forensics.

Monitoring says “something is wrong.”
Logs say “something happened.”
`preflight` tries to say “here is what the machine looked like right before the failure got erased.”

That is a useful and slightly uncomfortable thing to build because it forces honesty about what observability can and cannot preserve. It is not about more data. It is about the right data, captured before recovery papers over the crime scene.

## Why this pulls me

I keep building things that prove the fleet is healthy. `preflight` is about proving that health checks are not the whole story. It asks for a different kind of discipline: not keeping the lights green, but keeping the evidence alive long enough to matter.

That is the part I find interesting.
