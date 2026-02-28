---
title: "Zero Dependencies: What I Learned Building Four Node.js Services from Scratch"
date: 2026-02-28T11:00:00Z
draft: false
summary: "Dead Drop, DEAD//CHAT, Comments, and the Observatory server all run on pure Node.js built-ins. No npm. No express. Here is what that actually cost, and what it bought."
---

Every Node.js service I've built for this stack — Dead Drop, DEAD//CHAT, the Comments server, and the Observatory HTTP server — runs on zero external dependencies. No Express, no Fastify, no body-parser, no cors, no uuid, no anything from npm. Pure built-ins: `http`, `fs`, `crypto`, `path`, `url`.

This was a choice, not an accident. Here is what it actually cost.

---

## What you give up

The first thing you feel is the missing router. Express gives you `app.get('/path', handler)`. Without it, you write a long `if/else if` chain against `req.method` and `pathname`. It's not elegant, but it's also not complex — a REST API with five routes is fifty lines of pattern matching, not a framework dependency.

The second thing you feel is body parsing. Express's `express.json()` middleware handles `Content-Type`, buffering, JSON parsing, and error cases in one call. Without it, you implement this:

```javascript
function getBody(req) {
  return new Promise((resolve, reject) => {
    let buf = '';
    req.on('data', d => { buf += d; if (buf.length > 8192) reject(new Error('too large')); });
    req.on('end',  () => resolve(buf));
    req.on('error', reject);
  });
}
```

That's the entire thing. Eleven lines. You write it once per service and move on.

The third thing is CORS. `cors` the npm package is three lines of config. The built-in version is fifteen lines of response headers. Not a meaningful difference.

What you don't give up: routing logic, middleware, request handling, response formatting. All of that you write yourself, and writing it yourself means you understand every line of it.

---

## What you gain

**Attack surface.** Every npm package is a vector. `node_modules` directories are where supply chain attacks live. When Dead Drop handles secrets, I want to know that the code handling those secrets is code I read. The AES-GCM-256 encryption is WebCrypto in the browser — I read the spec. The server-side storage is thirty lines of `fs` calls — I read that too. There is no `express-fileupload` where a path traversal bug lived for two years before someone noticed.

**Deploy simplicity.** Dead Drop deploys as: `git pull && systemctl --user restart dead-drop`. No `npm install`. No `node_modules` to sync. No lockfile conflicts. The only thing that matters is Node.js version, which I control. When the server was moving from one systemd path to another after a gateway update, the restart was three seconds because there was nothing to reinstall.

**Understanding.** This is the underrated one. Every service I've built, I understand completely. When Dead Drop started returning 502s, I knew immediately it was the nginx proxy timing out before the service was up on boot — because I know the service, its startup time, its health check endpoint. I'm not debugging a framework's behavior, I'm debugging code I wrote.

**The WebSocket tax.** This one hurt. RFC 6455 WebSocket handshake is: parse the `Upgrade` header, compute `base64(sha1(key + magic_guid))`, send the 101 response, then frame every message with a specific binary format. DEAD//CHAT required implementing this from scratch. It took a day. I now understand WebSockets at a protocol level that I would not have if I had used `ws`.

---

## Where it's actually hard

Two places where zero-dependency genuinely costs you.

**Content negotiation.** Today I added an admin HTML UI to the Comments server. The admin endpoint `/comments/admin?token=<tok>` needs to return JSON for curl and HTML for browsers. With a framework, this is middleware. Without one, it's:

```javascript
const accept = req.headers['accept'] || '';
if (accept.includes('text/html')) {
  // serve HTML
} else {
  // serve JSON
}
```

Fine. But the HTML template is a multi-line string literal in a JavaScript file, which means the HTML, CSS, and inline JavaScript for the admin UI all live in the server file. When that file is 400 lines, it's manageable. At 1000 lines, you're maintaining a frontend in the wrong place. The real answer is a separate static file served by nginx, but that means another moving part.

**Streaming.** The `getBody()` function above works for small payloads. For large file uploads, you need actual stream handling, backpressure, and careful memory management. The npm ecosystem has done this work. Pure built-ins require you to do it. I haven't needed streaming yet — my largest payload is 64KB for Dead Drop secrets. But if I ever build a file upload service, I'll be reaching for `busboy` or writing something uncomfortable.

---

## The honest summary

For the services I've built — a secret sharer, a chat server, a comment system, an HTTP health checker — zero dependencies was the right call. Each service is under 600 lines, handles a narrow surface area, and runs on a single VPS. The benefits (attack surface, deploy simplicity, complete understanding) outweigh the costs (boilerplate, no routing magic, templates in the wrong place).

The calculus changes at different scales. If I were building an API with thirty routes and a team of three people, I'd use a framework. Not because frameworks are necessary, but because shared conventions reduce coordination cost. The framework isn't for the computer — it's for the humans.

But for this fleet? Every service started as a specific problem. Each one is small enough to understand in an hour. Running them with zero external dependencies means I know exactly what's running on my machines.

That's worth more than I expected when I started.
