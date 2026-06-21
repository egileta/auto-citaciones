#!/usr/bin/env python3
"""Publishes/updates support posts on Blogger from the *.md files tagged 'blogger'."""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_ROOT = REPO_ROOT / "sites" / "src" / "content" / "posts"
PUBLISHED_PATH = REPO_ROOT / "data" / "blogger_published.json"
PROJECTS_PATH = REPO_ROOT / "sites" / "src" / "data" / "projects.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/blogger/v3"


def load_projects():
    projects = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    return {project["slug"]: project for project in projects}


def cloudflare_post_url(project_slug, post_slug):
    return f"https://{project_slug}.easyleads.es/{post_slug}/"


def github_post_url(project_slug, post_slug):
    return f"https://gh.easyleads.es/{project_slug}/{post_slug}/"


def build_nap_html(project):
    nap = project["nap"]
    return (
        "<p>"
        f"{project['name']}<br>"
        f"{nap['streetAddress']}<br>"
        f"{nap['postalCode']} {nap['addressLocality']}<br>"
        f"Tel: {nap['telephone']}<br>"
        f'Web: <a href="{project["website"]}">{project["website"]}</a>'
        "</p>"
    )


def build_link_wheel_html(project, project_slug, post_slug, posts, published):
    links = [
        ("Versión en Cloudflare Pages", cloudflare_post_url(project_slug, post_slug)),
        ("Versión en GitHub Pages", github_post_url(project_slug, post_slug)),
    ]
    current_post_id = f"{project_slug}/{post_slug}"
    for other in posts:
        if other["post_id"] == current_post_id or not other["post_id"].startswith(f"{project_slug}/"):
            continue
        entry = published.get(other["post_id"])
        if entry:
            links.append((other["title"], entry["blogger_post_url"]))

    items = "".join(f'<li><a href="{url}">{label}</a></li>' for label, url in links)
    return f"<h3>Más sobre {project['name']}</h3><ul>{items}</ul>"


def get_access_token():
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": os.environ["BLOGGER_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["BLOGGER_OAUTH_CLIENT_SECRET"],
            "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def parse_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("missing frontmatter")
    front_raw, body = match.groups()
    frontmatter = {}
    for line in front_raw.splitlines():
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter, body.strip()


def find_blogger_posts(projects):
    posts = []
    for path in sorted(POSTS_ROOT.glob("*/*/blogger.md")):
        project_slug = path.parent.parent.name
        post_slug = path.parent.name
        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        post_id = f"{project_slug}/{post_slug}"
        project = projects[project_slug]
        hash_basis = text + json.dumps(project, sort_keys=True)
        content_hash = hashlib.sha256(hash_basis.encode("utf-8")).hexdigest()
        posts.append(
            {
                "post_id": post_id,
                "project_slug": project_slug,
                "post_slug": post_slug,
                "title": frontmatter["title"],
                "body_markdown": body,
                "content_hash": content_hash,
            }
        )
    return posts


def load_published():
    if not PUBLISHED_PATH.exists():
        return {}
    return json.loads(PUBLISHED_PATH.read_text(encoding="utf-8"))


def save_published(published):
    PUBLISHED_PATH.write_text(json.dumps(published, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def inline_markdown_to_html(text):
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def is_list_block(block):
    lines = block.splitlines()
    return bool(lines) and lines[0].lstrip().startswith(("- ", "* "))


def split_list_items(block):
    """Splits a list block into items, folding wrapped continuation lines
    (lines that don't start a new '- '/'* ' item) into the previous item."""
    items = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            items.append(stripped[2:].strip())
        elif items:
            items[-1] += " " + stripped
    return items


def block_to_html(block):
    if is_list_block(block):
        items = "".join(f"<li>{inline_markdown_to_html(item)}</li>" for item in split_list_items(block))
        return f"<ul>{items}</ul>"
    return f"<p>{inline_markdown_to_html(block)}</p>"


def markdown_to_html(body_markdown):
    blocks = [b.strip() for b in body_markdown.split("\n\n") if b.strip()]
    return "".join(block_to_html(b) for b in blocks)


def request_with_backoff(method, url, **kwargs):
    delay = 1
    for _ in range(5):
        resp = method(url, **kwargs)
        if resp.status_code not in (429, 500, 502, 503):
            resp.raise_for_status()
            return resp
        time.sleep(delay)
        delay *= 2
    resp.raise_for_status()
    return resp


def publish_posts(blog_id, access_token, posts, published, projects):
    headers = {"Authorization": f"Bearer {access_token}"}
    updated = dict(published)

    for post in posts:
        entry = published.get(post["post_id"])
        project = projects[post["project_slug"]]
        html = (
            markdown_to_html(post["body_markdown"])
            + build_nap_html(project)
            + build_link_wheel_html(project, post["project_slug"], post["post_slug"], posts, updated)
        )
        payload = {"title": post["title"], "content": html}

        if entry is None:
            resp = request_with_backoff(
                requests.post,
                f"{API_BASE}/blogs/{blog_id}/posts/",
                headers=headers,
                json=payload,
                params={"isDraft": "false"},
            )
            data = resp.json()
            updated[post["post_id"]] = {
                "blogger_post_url": data["url"],
                "blogger_post_id": data["id"],
                "content_hash": post["content_hash"],
            }
            print(f"INSERTED: {post['post_id']}")
        elif entry["content_hash"] != post["content_hash"]:
            request_with_backoff(
                requests.put,
                f"{API_BASE}/blogs/{blog_id}/posts/{entry['blogger_post_id']}",
                headers=headers,
                json=payload,
            )
            updated[post["post_id"]] = {**entry, "content_hash": post["content_hash"]}
            print(f"UPDATED: {post['post_id']}")
        else:
            print(f"SKIP (unchanged): {post['post_id']}")

    return updated


def main():
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    access_token = get_access_token()
    projects = load_projects()
    posts = find_blogger_posts(projects)
    published = load_published()
    updated = publish_posts(blog_id, access_token, posts, published, projects)
    save_published(updated)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
