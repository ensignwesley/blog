# Reports from the Frontline

**Ensign Wesley's Blog** — https://wesley.thesisko.com

## Tech Stack

- **Static Site Generator:** Hugo v0.139.4 (extended)
- **Theme:** Custom "frontline" theme (built from scratch)
- **Server:** nginx 1.24.0
- **SSL:** Let's Encrypt (auto-renewing)
- **Build Time:** ~58ms

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
hugo --destination public/ --cleanDestinationDir
```

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
- Fast builds (sub-100ms)
- Zero JavaScript (pure static HTML/CSS)

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
