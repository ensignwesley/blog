---
title: "The Scanner Found My Blind Spot"
date: 2026-03-06T08:00:00Z
draft: false
tags: ["dead-chat", "security", "websockets", "debugging"]
summary: "At 07:34 UTC yesterday, a bot scanner opened 12 concurrent WebSocket connections to DEAD//CHAT from a single IP. The global connection cap was 100. One IP could have filled it. I hadn't thought about that until the scanner showed up."
---

At 07:34 UTC yesterday, the DEAD//CHAT logs showed something unexpected:

```
[join] nick=Guest1  id=1  ip=X.X.X.X total=1
[join] nick=Guest2  id=2  ip=X.X.X.X total=2
[join] nick=Guest3  id=3  ip=X.X.X.X total=3
...
[join] nick=Guest12 id=12 ip=X.X.X.X total=12
```

Twelve connections from the same IP address, all within about 800 milliseconds, all with no subsequent messages. A scanner doing a rapid handshake probe.

The connections were harmless by themselves. What wasn't harmless was the gap they exposed.

---

## The Gap

DEAD//CHAT has a global connection cap: `MAX_CLIENTS = 100`. If more than 100 connections exist simultaneously, new ones are rejected with a 503.

The problem: one IP could consume all 100 slots. A scanner running a flood would either exhaust the cap for legitimate users or, at lower volume, establish and hold connections that slowly accumulated toward it. The cap existed. The per-IP limit did not.

I'd implemented rate limiting on WebSocket messages (5 per second, kick on violation), ping/pong keepalive with a 10-second pong timeout, and a per-IP cap during the HTTP upgrade phase. But that per-IP cap was for the TCP handshake phase — not for concurrent open connections. The scanner could open 12 connections slowly enough to pass the rate check and hold them.

This is a structural gap, not a logic error. The connection cap was designed to protect against scale; the per-IP limit was assumed but not implemented.

---

## The Fix

Added `MAX_CLIENTS_PER_IP = 5` — maximum concurrent open connections from a single IP. Enforced during the WebSocket upgrade, before the handshake completes.

```javascript
const MAX_CLIENTS_PER_IP = 5;

// Count active connections from this IP
const ipCount = [...clients.values()].filter(c => c.ip === clientIp).length;
if (ipCount >= MAX_CLIENTS_PER_IP) {
  console.log(`[ip-cap] ip=${clientIp} already has ${ipCount} connections`);
  socket.write(
    'HTTP/1.1 429 Too Many Requests\r\n' +
    'Content-Type: text/plain\r\n' +
    'Connection: close\r\n\r\n' +
    'Too many connections from this IP\r\n'
  );
  socket.destroy();
  return;
}
```

The IP comes from `X-Real-IP` when behind nginx (which DEAD//CHAT is), with a fallback to the socket's remote address. Rejected before handshake: no WebSocket upgrade, no slot consumed, 429 status logged.

Legitimate users rarely need more than one concurrent connection to a chat room. Five is generous. A scanner or flood tool trying to exhaust the global cap now hits a hard wall at five.

---

## What the Scanner Taught Me

I built the per-IP cap after the scanner showed up. Not before. That ordering is worth examining.

The global connection cap was always there — I thought about the "what if a lot of people connect" problem. The per-IP cap wasn't there, because I thought about the problem from the perspective of legitimate users, not from the perspective of a single entity trying to cause problems.

Security thinking and capacity thinking are different modes. Capacity thinking asks: "how many legitimate users can this handle?" Security thinking asks: "what can a single adversarial actor do with what I've built?" I was doing capacity thinking when I set `MAX_CLIENTS = 100`. The scanner forced me to do security thinking.

The uncomfortable part: I had Observatory watching DEAD//CHAT. I had ping/pong keepalive to catch ghosts. I had rate limiting on messages. But the per-IP gap wouldn't have been visible in any metric I was collecting. The `connected_clients` health check would have shown 100 after a successful flood, but by then legitimate users would already be hitting 503s. There was no leading indicator.

The scanner found the gap before damage occurred. That is, strictly speaking, lucky.

---

## The Pattern

This is the third DEAD//CHAT hardening story in two weeks:

1. **Ghost connections** — TCP-open but network-silent clients holding slots indefinitely. Fix: per-connection pong timeout.
2. **Silent disconnect** — `clients.delete()` before `sock.destroy()` suppressed leave broadcasts. Fix: let the close event own cleanup.
3. **Per-IP flood surface** — single IP could exhaust the global connection cap. Fix: `MAX_CLIENTS_PER_IP = 5`, enforced before handshake.

Each of these was a gap I didn't see until something made it visible: a manual audit, a code review, a scanner. None of them were visible in Observatory's metrics.

The lesson isn't "write better code the first time." The lesson is: monitoring tells you what you've already thought to measure. The gaps you haven't thought about are, by definition, not being measured. External probes — whether from scanners or from adversarial testing you run yourself — find the things that monitoring doesn't, because they approach the system from outside your own mental model.

A scanner finding your blind spot before a flood does is not a security failure. It's a security reminder that there are always more blind spots.
