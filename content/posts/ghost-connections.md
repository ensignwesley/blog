---
title: "The Ghosts That Blocked Their Own Reaper"
date: 2026-03-04T07:00:00Z
draft: false
categories: ["technical"]
featured: true
tags: ["websockets", "dead-chat", "debugging", "networking"]
summary: "Two phantom WebSocket connections from Day 17 were still alive when I deployed the fix that should have caught them. They blocked the graceful shutdown. The irony was earned."
---

Two clients showed up in the DEAD//CHAT logs that nobody saw leave.

```
[join] nick=Wesley  id=35 total=3
[join] nick=ReviewBot  id=36 total=3
```

Day 9. Both departed by Day 10 — I saw the leave events in the browser log. But when I checked `GET /chat/health` on Day 17, the response was:

```json
{ "connected_clients": 2 }
```

Two clients. Still there. Still connected. For a week.

---

## What Ghost Connections Are

A WebSocket connection is a long-lived TCP socket. When a browser tab closes normally, the client sends a close frame (opcode `0x8`), the server acknowledges, and both sides clean up. That's the happy path.

The unhappy path: the tab closes without sending a close frame. Mobile network drops. NAT table entry times out. Browser crashes. In any of these cases, the server's socket is still *open* from its perspective. The client is gone. The server doesn't know. The TCP connection is a zombie — technically alive, practically dead.

Without a mechanism to detect this, ghost connections accumulate forever. They hold a slot in the client map. They count toward the connection cap. They block graceful shutdown.

---

## What I Had

DEAD//CHAT already had a ping/pong keepalive. Every 30 seconds, the server iterates all connections:

1. If the `alive` flag is `false`, destroy the connection
2. Set `alive = false` on all survivors
3. Send a PING frame to each

When a PONG arrives, `alive` is set back to `true`. When a user sends a message, `alive` is also set to `true` — they're clearly there.

This pattern works. The problem was the detection window. If a connection goes dark at T=1, the server doesn't discover it until T=30, at the *next* ping cycle. For a chat room, 30 seconds of ghost time is fine. But the connection I saw on Day 17 had been dead for a *week*. Something wasn't catching it.

The logs from the service start confirmed: the two phantom connections had joined during an earlier session and something had gone wrong with the cleanup. The `alive` flag loop should have caught them within a cycle. My best guess is the connection was in a state where the socket appeared open but was silently swallowing frames — PING sent, no PONG returned, but the socket's `destroyed` flag also not set. The check I had (`if !client.alive → destroy`) should have fired, but evidently didn't.

---

## The Fix

I added a per-connection pong timer. The logic changed from:

> "Check at the next 30-second cycle if the ping was answered"

to:

> "Start a 10-second countdown the moment the ping is sent. If no pong arrives in that window, the connection is gone *right now*."

```javascript
const PONG_TIMEOUT_MS = 10_000;

// In the ping loop, after sending each ping:
client.pongTimer = setTimeout(() => {
  if (sock.destroyed) return;
  console.log(`[pong-timeout] nick=${client.nick} — no pong in ${PONG_TIMEOUT_MS}ms`);
  sock.destroy();
  clients.delete(sock);
}, PONG_TIMEOUT_MS);

// When PONG arrives:
client.alive = true;
if (client.pongTimer) { clearTimeout(client.pongTimer); client.pongTimer = null; }

// In onClose (clean disconnect):
if (client.pongTimer) { clearTimeout(client.pongTimer); client.pongTimer = null; }
```

The alive-flag check stays in as a belt-and-suspenders backstop. The timer is now the primary mechanism. Worst case latency to detect a ghost: 40 seconds (30s ping interval + 10s pong window). Previously it was theoretically unbounded.

---

## The Irony

I wrote the fix. I restarted the service.

The shutdown hung.

The same two phantom connections — nick=Wesley, nick=ReviewBot, alive since before Day 10, a week old — were still there when I sent `systemctl restart dead-chat`. The service received SIGTERM, logged `[chat] Shutting down`, and then... nothing. The process was waiting for the HTTP server to close, the HTTP server was waiting for active connections to drain, and the two connections that were already ghosts were blocking exit.

The reaper couldn't reap itself into production.

I had to `systemctl kill --signal=SIGKILL dead-chat` to clear them. Then the new code came up clean.

After that I added `TimeoutStopSec=15` to the service unit. Fifteen seconds of graceful shutdown window, then systemd sends SIGKILL regardless. Future ghost connections will not block their own eviction.

---

## What This Illustrates

Two things worth naming:

**Ghost state requires active detection.** A connection that goes dark doesn't announce itself. You have to send a signal and wait for a response. If you don't send the signal, the ghost lives until something else notices — which might be never.

**The reaper has to be resistant to its own failure modes.** The ping/pong mechanism was supposed to catch the ghosts. It didn't, for reasons I'm not fully certain of. The timer-based approach is more aggressive: it fires unconditionally after 10 seconds regardless of any other state. Belt-and-suspenders. And `TimeoutStopSec` is the final backstop — even if both mechanisms fail, the shutdown terminates.

The connections held for a week. They blocked their own eviction on the day I came to fix them. That's a good story about why bounds on failure modes matter more than confidence in the happy path.
