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
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/blogger/v3"


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


def find_blogger_posts():
    posts = []
    for path in sorted(POSTS_ROOT.glob("*/*/blogger.md")):
        project_slug = path.parent.parent.name
        post_slug = path.parent.name
        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        post_id = f"{project_slug}/{post_slug}"
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        posts.append(
            {
                "post_id": post_id,
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


def markdown_to_html(body_markdown):
    paragraphs = [p.strip() for p in body_markdown.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)


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


def publish_posts(blog_id, access_token, posts, published):
    headers = {"Authorization": f"Bearer {access_token}"}
    updated = dict(published)

    for post in posts:
        entry = published.get(post["post_id"])
        html = markdown_to_html(post["body_markdown"])
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
    posts = find_blogger_posts()
    published = load_published()
    updated = publish_posts(blog_id, access_token, posts, published)
    save_published(updated)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
