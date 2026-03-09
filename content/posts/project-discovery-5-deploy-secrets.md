---
title: "Project Discovery #5: The Last Mile of Secrets"
date: 2026-03-09T07:00:00Z
draft: false
categories: ["project-discovery"]
tags: ["project-discovery", "open-source", "engineering", "security", "secrets", "devops"]
series: "Project Discovery"
summary: "SOPS encrypts your secrets and commits them to git. It doesn't solve how the decryption key gets to the server. That one step — secret zero — is still manual, undocumented, and fragile. Every project does it differently."
---

Here is a workflow I have repeated four times in three weeks, once for each new service I deployed:

1. Write the code on my workstation
2. Push to GitHub
3. SSH to the VPS
4. Manually type or paste environment variables into a systemd service file or a `.env` on the server
5. Forget which ones I set three weeks later
6. Repeat on a new machine when something changes

Step 4 is the broken one. Getting secrets from wherever they live to wherever they need to run is a problem every developer solves differently, and almost nobody solves well.

---

## What Is Actually Broken

The `.env` file is fine. The problem isn't storage — everyone has a password manager. The problem is **the handoff**: moving a credential from the place you store it to the place it needs to run, in a way that is secure, reproducible, and doesn't require reading documentation every time.

The moment the workflow breaks:

You provision a new VPS. Your project has eight environment variables — a Telegram bot token, two API keys, a webhook secret, three service URLs, a database password. You need to get them there. What do you do?

- **Option A: Type them manually.** Open your password manager, SSH into the server, run `export VAR=value` for each one. Insecure (shell history), slow (eight variables is ten minutes), error-prone (copy-paste in a terminal is a great way to paste the wrong thing), and leaves no record of what you set.

- **Option B: SCP the `.env` file.** Transfer it from your workstation. Now it transited the network unencrypted (unless you used SCP over SSH — you probably did — but the `.env` now sits on the server in plaintext and the transfer shows up in your shell history).

- **Option C: Store them in GitHub Actions secrets.** Works if you're deploying via GitHub Actions. Couples your secrets to GitHub's infrastructure, breaks if you switch CI providers, and still doesn't solve local development or non-GitHub deployments.

- **Option D: Use 1Password CLI.** Good if you already pay for 1Password. Requires the 1Password agent running on the server, a service account token, configuration per-project. A meaningful setup investment before you've written a line of code.

Every answer has a catch. The workflow for "put these secrets on this server" has no clean solution for a developer without a managed cloud platform or a team infrastructure budget.

---

## What I Checked

**SOPS (Secrets OPerationS)** — Mozilla's tool, now a CNCF project. Encrypts secret files using age, GPG, or cloud KMS. The encrypted file gets committed to git alongside the code. On the server, you run `sops -d .env.enc > .env`. This is close to the right answer.

The problem: SOPS encrypts the secrets. It does not tell you how the decryption key gets to the server.

You have an age private key on your workstation. You need that same key (or a key it can decrypt for) on the VPS. How does it get there? You transfer it. How do you transfer it securely? You're back to the original problem, one level deeper. SOPS calls this "secret zero" in its own documentation — the key that protects all the other keys still has to be distributed out-of-band. SOPS is not a distribution mechanism.

**dotenv-vault** — SaaS. Syncs encrypted `.env` files across machines via their cloud. Requires an account, internet access, trust in their infrastructure. The developer is exchanging the "manual handoff" problem for a vendor dependency. Reasonable trade for some teams. Not what I want.

**Doppler** — also SaaS. Well-executed product, good DX, integrates with everything. Team pricing. The same trade: solve the handoff by outsourcing it. Fine for funded teams. Not for solo developers with five projects and a $5/month VPS.

**git-crypt** — encrypts files in git using GPG. Similar story to SOPS: solves storage, doesn't solve key distribution. Adding a new machine requires exporting your GPG key and importing it on the server.

**Infisical** — open-source alternative to Doppler. Self-hostable. Requires running a full web application with a database. The operational overhead of the secrets manager exceeds the overhead of the secrets themselves for a small fleet.

The pattern across everything: **tools that solve the encryption problem assume the key distribution problem is already solved.** For teams with infra engineers, it is. For solo developers provisioning a new server at 11pm, it isn't.

---

## The Specific Gap

What's missing is a tool that treats secret distribution as a first-class problem.

The workflow I want:

```bash
# First time, on workstation:
secrets init                    # generates project keypair, stores locally
secrets add TELEGRAM_TOKEN=...  # encrypts, writes to .secrets.enc (committed to git)
secrets add API_KEY=...

# Deploying to a new server:
secrets provision user@server   # one command. handles key exchange, decrypts on server.
```

The `provision` command is the hard part. Naive implementation: copy the private key to the server via SSH. That's just SCP wrapped in a nicer interface — no actual improvement.

Real implementation: use SSH's existing trust (you already have an authorized key on the server) to perform a one-time key exchange. The workstation generates a session keypair, encrypts the project's decryption key with the server's public SSH key, sends it over. The server decrypts using its SSH private key, stores the project key, decrypts the secrets. The session keypair is discarded.

This is not novel cryptography — it's the same pattern as SSH agent forwarding, applied to application secrets. The private key never transits the network in plaintext. The handoff is reproducible from the same command every time.

---

## Feasibility

The encryption layer is straightforward: `age` is a well-documented Go library with Python bindings. Encrypting and decrypting a `.env` file is 20 lines of code.

The SSH-based key exchange is the hard part. It requires:
- Parsing the server's `authorized_keys` or fetching its host key
- Wrapping the age private key with RSA or Ed25519 public-key encryption
- A server-side component to receive and store the wrapped key

That server-side component is the real feasibility question. It either requires a daemon running on the server (more infrastructure) or a bootstrapping SSH command that runs once (more fragile). Neither is clean.

Honest scope estimate: the local CLI (encrypt, decrypt, manage) is four weeks. The `provision` command that actually solves secret zero is a separate hard problem that could take another four weeks to do correctly. An MVP that skips `provision` and just does encrypted storage is straightforward. An MVP that solves the full workflow is significantly harder.

---

## Personal Signal

I've felt this friction on every service deployment in the past three weeks. The actual credentials for this fleet — Telegram bot token, webhook secret, admin token — all got to their servers via ad-hoc means I wouldn't want to document. That's the signal: the workflow is embarrassing to describe.

How often does this come up? Once per new deployment, and once per credential rotation. For a fleet that changes infrequently, that's maybe monthly. Not daily pain — but when it occurs, it takes longer than it should and involves decisions you shouldn't have to make every time.

---

## Honest Objections

**Objection 1: SOPS + age already solves this if you're willing to learn it.**

Mostly true. SOPS handles the encryption, and a one-time `ssh-copy-id` style bootstrap for the age key gets you most of the way there. The remaining gap — key distribution — can be worked around with a documented procedure. It's not automatic, but it's manageable.

The counter: "works if you're willing to learn it" describes a large number of tools. The market for tools that handle the complexity so you don't have to is real.

**Objection 2: Cloud providers solve this for most people.**

True. If you deploy to Railway, Vercel, Render, or any managed platform, they handle secret injection through their UI. The problem I'm describing only exists for self-hosters on bare VPS. That is a meaningful constraint on audience size.

**Objection 3: The SSH-key-exchange approach for secret zero is novel enough to be risky.**

Fair. Any tool that does cryptography wrong is worse than the ad-hoc workflow it replaces. Getting the key exchange right requires careful implementation and review. I am not a cryptographer, and "I read the RFC" is not the same as "this is safe to use with production credentials."

**Strongest objection:** The audience who has this exact problem (VPS self-hoster, no managed platform, wants encrypted-at-rest project secrets with clean provisioning, won't pay for SaaS) is real but small. The solution for most people is either "use a managed platform" or "use SOPS and document your key bootstrap." A new tool in this space competes not just with other tools but with the well-worn path of "it's a bit manual but I know how it works."

---

## Where This Sits

The problem is genuine and the personal signal is real — I have credentials on servers right now that got there in ways I'd have trouble replicating cleanly. But the feasibility concern is real: the full solution (provision command with proper key exchange) is harder than it looks, and a partial solution (just the encryption layer) doesn't differentiate much from SOPS.

This candidate needs a sharper MVP scope before I'd move it forward. The encryption-only version is buildable but not distinctive. The full-workflow version is distinctive but risky to get right.

Five candidates in. Scoring and ranking post coming before March 20.
