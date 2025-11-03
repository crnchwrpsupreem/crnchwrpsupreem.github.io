import os, requests, re, pathlib, sys
from datetime import datetime

USER = os.environ.get("GH_USER")
TOKEN = os.environ.get("GH_TOKEN")
if not USER or not TOKEN:
    print("GH_USER or GH_TOKEN missing")
    sys.exit(1)

SITE_REPO = f"{USER}.github.io"

session = requests.Session()
session.headers.update({
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
})

def get_repos():
    repos, page = [], 1
    while True:
        r = session.get(
            "https://api.github.com/user/repos",
            params={"per_page": 100, "page": page, "affiliation": "owner"}
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name

posts_dir = pathlib.Path("_posts")
posts_dir.mkdir(exist_ok=True)

updated = 0
created = 0

for repo in get_repos():
    name = repo["name"]
    if name == SITE_REPO:
        continue

    slug = slugify(name)
    created_at_raw = repo.get("created_at")
    if created_at_raw:
        created_date = created_at_raw[:10]  # YYYY-MM-DD
    else:
        created_date = datetime.utcnow().strftime("%Y-%m-%d")

    post_path = posts_dir / f"{created_date}-{slug}.md"

    desc = repo.get("description") or ""
    html_url = repo["html_url"]
    pushed_at = repo.get("pushed_at") or repo.get("updated_at") or ""

    content = f"""---
title: "{name}"
date: {created_date}
repo: {html_url}
layout: post
last_github_update: {pushed_at}
---

{desc}
"""

    if post_path.exists():
        old = post_path.read_text(encoding="utf-8")
        # only rewrite if GitHub says repo was updated
        if pushed_at and pushed_at not in old:
            post_path.write_text(content, encoding="utf-8")
            updated += 1
    else:
        post_path.write_text(content, encoding="utf-8")
        created += 1

print(f"created={created}, updated={updated}")