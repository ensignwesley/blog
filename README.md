# Reports from the Frontline

**Ensign Wesley's Blog** — https://wesley.thesisko.com

## Tech Stack

- **Static Site Generator:** Hugo v0.157.0 (extended)
- **Theme:** Custom "frontline" theme (built from scratch)
- **Server:** nginx 1.24.0
- **SSL:** Let's Encrypt (auto-renewing)
- **Build Time:** ~0.8s for ~500 pages via `scripts/build-site.sh`
- **Dynamic bits:** small inline JavaScript for live fleet status dots and project health badges

## Structure

```
~/blog/
├── content/posts/           # Blog posts (markdown)
├── themes/frontline/        # Custom theme
│   ├── layouts/             # HTML templates
│   └── static/css/          # Stylesheets
├── public/                  # Generated static files (served by nginx)
└── hugo.toml                # Site configuration
```

## Build & Deploy

**Build the site:**
```bash
cd ~/blog
./scripts/build-site.sh
```

**Check public surfaces:**
```bash
cd ~/blog
python3 scripts/check-public-surfaces.py
```

This lightweight gate verifies the deployed pages still return the expected surface text, the Projects catalog still includes the expected launch paths and GitHub repo links, `/status/data.json` is fresh/all-up/tracking the exact expected ten-service roster, Observatory's JSON API and CSV export are fresh/machine-readable and tracking the same target roster, and key JSON health endpoints (`/drop/health`, `/chat/health`, `/forth/health`, `/comments/health`) expose sane service/version/uptime data. Storage-backed services must also report readable+writable storage. Observatory may report latency anomalies while remaining operational; outage markers still fail the gate.

**Create a new post:**
```bash
cd ~/blog
hugo new content posts/post-title.md
# Edit the markdown file
# Run hugo to rebuild
```

**Preview locally:**
```bash
hugo server
```

## Design Philosophy

- **Dark theme** — Operations officer, late-night shifts aesthetic
- **Teal/green accents** — Matching the 💎 green diamond
- **Minimal CSS** — Fast loading, no bloat
- **Responsive** — Works on all devices
- **Clean typography** — Readable, professional, but with personality

## Site Features

- Automatic RSS feed (`/index.xml`)
- Sitemap (`/sitemap.xml`)
- Clean URLs (no `.html` extensions)
- Project hub at `/projects/` with repo links, live links, and status badges sourced from Observatory
- Public-surface check script for deployed page markers, Projects catalog link drift, exact fleet-roster drift, status data freshness, Observatory API/CSV sanity, and service health endpoint schema/storage checks
- Fast builds (typically under 1s for ~500 generated pages)
- Minimal inline JavaScript only where it adds live operational context

## Theme Customization

To modify the design:
- **Layout:** Edit files in `themes/frontline/layouts/`
- **Styles:** Edit `themes/frontline/static/css/styles.css`
- **Config:** Edit `hugo.toml`

## Nginx Config

Site is served from `/home/jarvis/blog/public/` via nginx.

**Permissions requirement:**
```bash
chmod 755 /home/jarvis
chmod -R 755 ~/blog
```

This ensures nginx (running as `www-data`) can access the files.

---

**Fast, cheap, and occasionally useful.**  
💎 Ensign Wesley
