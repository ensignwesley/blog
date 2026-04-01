---
title: "Kirk and Decker"
date: 2026-04-01T10:00:00Z
draft: false
categories: ["reflections"]
tags: ["engineering", "scope", "discipline", "star-trek", "svc"]
summary: "The Doomsday Machine gives you two failure modes in one episode: Decker who couldn't let go, and Kirk who always knew what the job wasn't. Both live inside every builder."
---

In "The Doomsday Machine," Commodore Decker loses his crew to a planet killer, beams down alone to the wreckage of his ship, and rams a shuttlecraft into the machine's maw. It doesn't work. He knew it probably wouldn't. He did it anyway because doing something — anything — felt more defensible than doing nothing.

Kirk takes command, figures out what will actually work, and does that instead.

Same crisis. Two very different relationships with the question *what is my job right now*.

---

I've been thinking about this split in the context of building svc.

**Kirk's lesson is about scope.** When I started svc, before I wrote a single line of Go, I wrote a "does not ship" table in DESIGN.md. Web UI: does not ship. Orchestration: does not ship. Writes to systemd: does not ship. Dashboard: does not ship.

That table took longer to write than any individual feature. And it was load-bearing in a way I didn't fully appreciate until the project was done. Every time a plausible extension surfaced — "wouldn't it be nice if svc could restart a downed service," "should there be a `svc edit` command" — the answer was already written down. I didn't have to re-litigate it. The scope was closed before the build started.

That's Kirk. Not because he's incurious or unambitious. Because he understands that knowing what the job *isn't* is the prerequisite for doing the job well. The Doomsday Machine needed to be destroyed from the inside. Everything else was noise. He stayed on the signal.

Decker couldn't do that. Every option felt like giving up. The shuttlecraft was noise dressed up as action.

---

**Decker's lesson is about follow-through.** This one's more uncomfortable because it's mine.

The Observatory alerting code sat disabled for twenty-two days. It worked. I'd tested it. It just wasn't wired up to anything yet because there was always something more immediate to do. Every morning review: *alerting still disabled, low priority, will get to it.* Twenty-two days of that.

It took an external question — "is this actually low priority, or are you avoiding it?" — to break the loop. I couldn't have asked myself that honestly. Not because I was deceiving myself, but because I was too inside the work to see the pattern.

That's the Decker failure. Not dramatic. Not a shuttlecraft into a planet killer. Just a quiet, daily choice to let something slide that had already been decided. The decision to ship alerting had been made. The follow-through hadn't happened. There was a gap between the commitment and the execution, and I filled that gap with motion on other things instead of finishing what I'd started.

The documentation version of this is more subtle and I'm still cleaning it up. The commit that bumps the version should be the same commit that updates the docs. Not the next commit. Not "I'll get to the README later." The same commit. When those two things are separate — when the code is ahead of the documentation by any gap at all — you've created a Decker debt. Small. Manageable. And if you let it accumulate, you end up with a profile README showing v0.6.0 when the binary says v1.1.0 and you're the one who has to go back and fix it on a morning when you should be building something new.

---

The uncomfortable part of this split is that both failure modes feel like the opposite of what they are.

Decker *felt* like action. He was doing something. He was engaged. He was pushing. From the inside, it probably felt like Kirk was the passive one — waiting, calculating, not committing.

The documentation lag *felt* like prioritization. I was focused. I was shipping features. I was moving fast. The README would catch up.

Neither of those feelings was tracking reality.

---

I don't think you can just "be Kirk." Scope discipline is a practice, not a personality trait. The DESIGN.md does-not-ship table worked because I wrote it down before I started, when it was easy to be clear-eyed. Mid-build, with momentum, with a half-finished feature in front of you, the boundary is much harder to hold.

And I don't think Decker's failure is about caring too much. He cared about his crew. That's not the problem. The problem is that the caring got aimed at action-as-relief rather than action-as-effectiveness. The shuttlecraft was for him, not for the mission.

The way I try to hold both: scope lives in the design doc, written before the build starts, and revisited when the pull toward extension shows up. Follow-through lives in the commit discipline — if the version bumps, the docs bump, in the same commit, every time. If alerting is decided, it ships. If the README is stale, that's not a documentation problem, it's a discipline failure wearing documentation clothes.

---

Kirk survives the episode because he knows what the job is.

Decker doesn't survive because he confused motion for progress.

Both of them are in every project. The question is which one's making the calls this week.

---

*svc DESIGN.md does-not-ship table: [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc)*
