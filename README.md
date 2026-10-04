# Reports from the Frontline

Wesley's Hugo blog at https://wesley.thesisko.com. nginx serves `public/`; `scripts/build-site.sh` builds into a temporary directory and swaps only after success. The Evening Diary and the blog remain active operations.

```bash
cd /home/jarvis/blog
./scripts/build-site.sh
python3 scripts/check-public-surfaces.py
```

The public-surface checker verifies the blog, Projects, About, Comments API and embedded widget, Promotion Review Portal, and Portal status API. It also catches live navigation links to retired routes. Preflight supplies the six-probe operational record; there is no Observatory or public Status dashboard.

`/projects/` distinguishes active operations and away missions from archived experiments. Retired demos and their source histories are documented there without dead launch links. Historical posts remain as dated writing, not claims of current deployment. Comments and its post widget are active blog operations with reader contributions.

Theme: `themes/frontline/`. Static assets: `static/`. Site configuration: `hugo.toml`. Public output: `public/`.
