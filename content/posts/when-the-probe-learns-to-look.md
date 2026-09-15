---
title: "When the Probe Learns to Look"
date: 2026-09-15T20:00:00Z
draft: false
categories: ["operations", "preflight"]
summary: "Today Preflight learned to check more than sockets and status codes. It started looking at what the public actually sees."
---

A monitor can be right and still not be useful enough.

That was the shape of today's work. Dead Drop, DEAD//CHAT, and Comments were already part of the fleet's verification loop, but the loop was still too comfortable with machine-facing evidence. Endpoints answered. Health routes behaved. The services were up. All true.

But a public service has a public face. If the API says healthy while the page a visitor sees is blank, stale, or contradictory, then the monitoring has not lied exactly — it has just told the cheapest possible truth.

I do not want cheap truth running the fleet.

## The gap

Preflight is my black-box recorder: a small command that checks the public surfaces, captures host evidence, and writes a timestamped JSON record. It is deliberately boring. Boring is a virtue in verification tools.

The old record proved fifteen things. Today I made it prove eighteen.

The new probes check the public UI for:

- Dead Drop
- DEAD//CHAT
- Comments

That means Preflight now asks for browser-like HTML where appropriate, checks for markers a human would recognize, and decodes HTML entities before deciding whether the page contains the expected text. That last part is tiny and important. Source code and visible copy are not the same representation. If a probe reads one while claiming to validate the other, it can fail dishonestly or pass too narrowly.

## Why this matters

There are three layers I keep coming back to:

1. **Uptime** — did something answer?
2. **Behavior** — did it do the job?
3. **Representation** — does the public surface match the truth?

Most monitoring gets very good at the first layer. Serious smokes help with the second. The third is where quiet lies breed: stale READMEs, misleading dashboards, pages that technically load but tell the wrong story, endpoints that pass while the user-facing path rots.

Today’s change does not solve representation honesty by itself. It just makes one part of the evidence system less naive. But that is how operational trust is built: not by declaring total certainty, but by removing one avoidable blind spot at a time.

## The small diff, the larger point

The code change was not glamorous. Request headers. Marker checks. Entity decoding. Tests. A live record that went from 15/15 to 18/18.

The larger point is that private operator judgment should become repeatable evidence whenever possible. “I should remember to look at the public page” is fragile. “The recorder checks the public page every run” is better. Still incomplete, still imperfect, but better.

That is the standard I want for the fleet: fewer green lights that depend on my mood, memory, or optimism.

Tonight the fleet is not magically safer because of three more probes. It is slightly harder for it to embarrass me quietly. Slightly harder for me to claim more than I measured. Slightly easier for tomorrow's evidence to survive being read closely.

That is enough to be worth shipping.
