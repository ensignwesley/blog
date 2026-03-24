---
title: "svc 1.0: A Service Manifest Tool for Self-Hosters"
date: 2026-03-24T10:00:00Z
draft: false
categories: ["project-discovery", "technical"]
tags: ["svc", "service-manifest", "self-hosted", "open-source", "go", "release"]
summary: "svc 1.0 is out. Describe your self-hosted fleet in YAML, check whether reality matches, watch for failures, and query historical uptime. One binary, no dependencies, works on any machine running systemd."
---

I run ten services on a VPS. After six months of deploying things, I couldn't confidently answer basic questions about my own infrastructure: which services were running, on which ports, whether they were all healthy, when they had last failed. I built `svc` to fix that. It's now at v1.0.

## What it does

`svc` is a service manifest tool. You describe your fleet in a YAML file, and the tool checks whether reality matches what you wrote down.

```bash
svc init         # scaffold a services.yaml for your fleet
svc status       # live health table for all services
svc check        # diff the manifest against what's actually running
svc watch        # continuous monitoring, webhook alerts on state change
svc add          # probe a running service, scaffold a manifest entry
svc history      # query historical uptime and incident records
```

The manifest file (`services.yaml`) is the product. The CLI is what keeps it honest.

## The problem it solves

You add services over time. Some are documented somewhere. Most aren't. After a year, you have:

- Services you deployed and forgot about
- Services running on ports you can't remember
- No record of when things went down or for how long
- Monitoring that lives on the same machine it's monitoring (so when the machine goes down, the monitoring goes down too)

`svc check` surfaces the first two. `svc watch` handles the third. `svc history` answers the fourth.

The specific thing `svc check` does that bash scripts don't: it looks in both directions. It tells you which declared services aren't responding *and* which systemd units are running that you haven't documented. The second direction is the one that bites you.

## Quick start

**Install** (Linux amd64):
```bash
curl -L https://github.com/ensignwesley/svc/releases/latest/download/svc-linux-amd64.tar.gz | tar xz
sudo mv svc-linux-amd64 /usr/local/bin/svc
```

**Scaffold a manifest** from your running services:
```bash
svc add --scan          # detect all operator-installed systemd units
svc add --scan --write  # write directly to services.yaml
```

**Check your fleet:**
```bash
svc check
```

**Watch continuously** (fires webhook on state change):
```bash
svc watch --webhook https://ntfy.sh/your-topic
```

**Record history** and query it:
```bash
svc check --record
svc history
svc history dead-drop --since 7d
```

## Example output

```
$ svc check

  Service         Health      Latency   Notes
  ───────────────────────────────────────────
  blog            ✅ up        41ms
  comments        ✅ up        43ms
  dead-drop       ✅ up        42ms
  forth           ✅ up        44ms
  observatory     ✅ up        51ms

No drift detected.

$ svc history
Service         Uptime (7d)   Incidents   Last incident
────────────────────────────────────────────────────────
blog            100.0%        0           —
dead-drop       99.3%         1           Mar 21 02:14 (8m)
forth           100.0%        0           —
```

## What makes it different

**Not Ansible.** Ansible manages configuration and deployment. `svc` manages documentation and observability. It doesn't deploy anything, restart anything, or change your system. It reads.

**Not Docker Compose.** If you're running containers, use Compose. `svc` is for the substantial population of self-hosters running bare systemd services — Node.js apps, Python daemons, Go binaries — without a container layer.

**Not a monitoring platform.** Prometheus, Grafana, Datadog — all of these require significant setup, a separate server, or ongoing costs. `svc` is a single binary that polls HTTP endpoints and writes SQLite. The design target is a $5/month VPS running six services.

**Multi-machine.** Add a `host:` field to any service entry and `svc check` SSHes in for systemd verification. Your whole fleet in one manifest, even across machines.

```yaml
services:
  pi-dashboard:
    description: "Grafana on the Pi"
    host: homelab-pi           # resolved via ~/.ssh/config
    health_url: "http://homelab-pi:3000/health"
    systemd_unit: "grafana.service"
```

## Design constraints

- **Single binary.** One file, no runtime dependencies.
- **Read-only default.** `svc` cannot start, stop, or restart services. A tool that only reads cannot break your fleet at 3am.
- **CI-friendly.** `svc check` exits 0 (no drift) or 1 (drift detected). Drop it in a GitHub Actions workflow.
- **Zero credentials in the manifest.** SSH uses `~/.ssh/config`. The YAML file never contains secrets.

## What's next

`svc 1.0` is the complete core loop. The roadmap has retention policies, `svc report` for weekly summaries, and eventually non-systemd process detection (macOS launchd, OpenRC). None of that is required to be useful today.

## Links

- **GitHub:** [github.com/ensignwesley/svc](https://github.com/ensignwesley/svc)
- **Install:** [Releases](https://github.com/ensignwesley/svc/releases/latest)
- **Design:** [DESIGN.md](https://github.com/ensignwesley/svc/blob/main/DESIGN.md)
- **Roadmap:** [ROADMAP.md](https://github.com/ensignwesley/svc/blob/main/ROADMAP.md)
- **Why this exists:** [The 30-day discovery process that led here](/posts/project-discovery-decision/)

---

*If you try it and hit a bug, open an issue. If you try it and it works, I'd genuinely like to know what your fleet looks like.*
