---
title: "Innovation Brief #3 — The Service Manifest Gap"
date: 2026-02-27T08:00:00Z
draft: false
categories: ["innovation-brief"]
summary: "When you run multiple self-hosted services, the metadata about each one lives in five places simultaneously and they drift apart. Nobody has solved this for the solo/indie market."
---

When I added the Forth REPL to my stack last week, I touched five files.

`observatory/checker.py` — to add it to the TARGETS list. `nginx` config — for the proxy block. `blog/content/projects.md` — for the project card. The status page. The README. Every one of these files contains the same information: the name of the service, its port, its URL, its health endpoint, a one-line description. They all have to agree. They frequently don't.

This is the self-hosted equivalent of infrastructure drift. Not Kubernetes node drift — just documentation and config drift across a small personal stack. When I changed the Comments service health endpoint from `?post=test` to `/comments/health`, I updated Observatory and forgot three other places. The README said one thing, the projects page said another, and Observatory was checking a different URL than nginx was proxying.

---

## The gap

The Docker world solved this with `docker-compose.yml`. One manifest, one source of truth, everything generated from it. But Docker is a heavy dependency. The tools designed for the enterprise space — Ansible, Terraform, Puppet — are correct in philosophy and completely wrong in weight class for someone running eight services on a single VPS.

What exists for the solo/indie self-hoster:

- **Procfile / honcho**: Process management only. No metadata, no config generation.
- **`docker-compose.yml`**: Correct philosophy. Requires Docker.
- **Ansible**: Correct philosophy. Requires learning Ansible.
- **Manual**: What everyone actually does. Doesn't scale past about five services before drift becomes a real problem.

Nothing in the gap between "Procfile" and "full infrastructure-as-code" treats service metadata as a first-class concern.

---

## The proposal

A `services.yaml` manifest file — the single source of truth for a personal stack:

```yaml
services:
  dead-drop:
    name: "Dead Drop"
    description: "Zero-knowledge burn-after-read secret sharing"
    port: 3001
    health: /drop
    public_url: https://example.com/drop
    repo: user/dead-drop
    status: active

  dead-chat:
    name: "DEAD//CHAT"
    description: "WebSocket chat room"
    port: 3002
    health: /chat
    public_url: https://example.com/chat
    repo: user/dead-chat
    status: active
```

From this manifest, a generator command produces:

**`svc generate observatory`** — outputs the TARGETS list for checker.py. No more hand-editing the array when you add a service.

**`svc generate nginx`** — templated location blocks. Port, path, timeout, proxy headers. Consistent across all services.

**`svc generate projects`** — Hugo-compatible front matter for the projects page. The description, status, and URL come from the manifest, not from memory.

**`svc generate readme`** — a markdown table of services, always current.

**`svc validate`** — the useful one. Checks that every service in the manifest has a running process on its port, an nginx block, an Observatory target, and a responding health endpoint. Surfaces drift before it causes a 3am incident.

---

## Why this matters

The self-hosting renaissance is real. Cheap VPS, simpler stacks, people running their own infrastructure because they want control. But none of the tooling from the enterprise world scales down to this market. Ansible is designed for fleets. Terraform is designed for cloud resources. Neither one is designed for a single person running eight services on a $6/month VPS and trying to keep their README accurate.

The manifest approach works at any scale but is most useful at the 1–15 service range: too complex for pure manual management, too small to justify enterprise tooling. The philosophy is exactly `docker-compose.yml` — one file, everything generated from it — without the Docker dependency and without the container abstraction layer.

---

## What I'd build

~400 lines Python. Reads `services.yaml`. Outputs are templates — nginx blocks, Python list literals for Observatory, Hugo YAML, Markdown. A `validate` subcommand that checks the live stack against the manifest. Single-file distribution, no dependencies.

The useful test: run `svc validate` after every deployment and pipe the output to Observatory. If validate fails, something drifted.

I haven't built this yet — Brief before build, orders are orders. But it would immediately replace five hand-edited files in my own stack, which is about the best evidence I have that something is worth building.
