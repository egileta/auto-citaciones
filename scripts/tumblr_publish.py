#!/usr/bin/env python3
"""Publishes/updates support posts on Tumblr from the *.md files tagged 'tumblr'."""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_ROOT = REPO_ROOT / "sites" / "src" / "content" / "posts"
PUBLISHED_PATH = REPO_ROOT / "data" / "tumblr_published.json"
BLOGGER_PUBLISHED_PATH = REPO_ROOT / "data" / "blogger_published.json"
PROJECTS_PATH = REPO_ROOT / "sites" / "src" / "data" / "projects.json"
API_BASE = "https://api.tumblr.com/v2"

# Bump when the HTML generated from a post's markdown/project data changes
# (e.g. markdown_to_html or build_nap_html) without the source files
# themselves changing, so already-published posts still get republished.
TEMPLATE_VERSION = "1"


def load_projects():
    projects = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    return {project["slug"]: project for project in projects}


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


def cloudflare_post_url(project_slug, post_slug):
    return f"https://{project_slug}.easyleads.es/{post_slug}/"


def github_post_url(project_slug, post_slug):
    return f"https://gh.easyleads.es/{project_slug}/{post_slug}/"


def read_channel_title(project_slug, post_slug, channel):
    path = POSTS_ROOT / project_slug / post_slug / f"{channel}.md"
    if not path.exists():
        return None
    frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return frontmatter.get("title")


def load_blogger_published():
    if not BLOGGER_PUBLISHED_PATH.exists():
        return {}
    return json.loads(BLOGGER_PUBLISHED_PATH.read_text(encoding="utf-8"))


def build_link_wheel_html(project_slug, post_slug, blogger_published=None):
    """Links to the Cloudflare/GitHub/Blogger versions of this same post,
    using each one's own (deliberately varied) title as anchor text —
    identical anchor text across near-duplicate copies of an article is a
    link-scheme signal, a real per-channel title isn't."""
    if blogger_published is None:
        blogger_published = load_blogger_published()

    links = []
    cf_title = read_channel_title(project_slug, post_slug, "cloudflare")
    if cf_title:
        links.append((cf_title, cloudflare_post_url(project_slug, post_slug)))
    gh_title = read_channel_title(project_slug, post_slug, "github")
    if gh_title:
        links.append((gh_title, github_post_url(project_slug, post_slug)))
    blogger_title = read_channel_title(project_slug, post_slug, "blogger")
    blogger_entry = blogger_published.get(f"{project_slug}/{post_slug}")
    if blogger_title and blogger_entry:
        links.append((blogger_title, blogger_entry["blogger_post_url"]))

    if not links:
        return ""
    items = "".join(f'<li><a href="{url}">{title}</a></li>' for title, url in links)
    return f"<ul>{items}</ul>"


def oauth1_session():
    return OAuth1(
        os.environ["TUMBLR_CONSUMER_KEY"],
        client_secret=os.environ["TUMBLR_CONSUMER_SECRET"],
        resource_owner_key=os.environ["TUMBLR_OAUTH_TOKEN"],
        resource_owner_secret=os.environ["TUMBLR_OAUTH_TOKEN_SECRET"],
    )


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


def find_tumblr_posts(projects):
    posts = []
    for path in sorted(POSTS_ROOT.glob("*/*/tumblr.md")):
        project_slug = path.parent.parent.name
        post_slug = path.parent.name
        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        post_id = f"{project_slug}/{post_slug}"
        project = projects[project_slug]
        sibling_titles = (
            (read_channel_title(project_slug, post_slug, "cloudflare") or "")
            + (read_channel_title(project_slug, post_slug, "github") or "")
            + (read_channel_title(project_slug, post_slug, "blogger") or "")
        )
        hash_basis = text + json.dumps(project, sort_keys=True) + sibling_titles + TEMPLATE_VERSION
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


def publish_posts(blog_identifier, auth, posts, published, projects, blogger_published=None):
    updated = dict(published)

    for post in posts:
        entry = published.get(post["post_id"])
        project = projects[post["project_slug"]]
        html = (
            markdown_to_html(post["body_markdown"])
            + build_nap_html(project)
            + build_link_wheel_html(post["project_slug"], post["post_slug"], blogger_published)
        )
        payload = {"type": "text", "format": "html", "state": "published", "title": post["title"], "body": html}

        if entry is None:
            resp = request_with_backoff(
                requests.post,
                f"{API_BASE}/blog/{blog_identifier}/post",
                auth=auth,
                data=payload,
            )
            data = resp.json()["response"]
            post_id = str(data["id"])
            updated[post["post_id"]] = {
                "tumblr_post_url": f"https://{blog_identifier}/post/{post_id}",
                "tumblr_post_id": post_id,
                "content_hash": post["content_hash"],
            }
            print(f"INSERTED: {post['post_id']}")
        elif entry["content_hash"] != post["content_hash"]:
            request_with_backoff(
                requests.post,
                f"{API_BASE}/blog/{blog_identifier}/post/edit",
                auth=auth,
                data={**payload, "id": entry["tumblr_post_id"]},
            )
            updated[post["post_id"]] = {**entry, "content_hash": post["content_hash"]}
            print(f"UPDATED: {post['post_id']}")
        else:
            print(f"SKIP (unchanged): {post['post_id']}")

    return updated


def main():
    blog_identifier = os.environ["TUMBLR_BLOG_IDENTIFIER"]
    auth = oauth1_session()
    projects = load_projects()
    posts = find_tumblr_posts(projects)
    published = load_published()
    blogger_published = load_blogger_published()
    updated = publish_posts(blog_identifier, auth, posts, published, projects, blogger_published)
    save_published(updated)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
