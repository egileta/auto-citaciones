#!/usr/bin/env python3
"""Adds each project's subdomain as a custom domain on the Cloudflare Pages project (idempotent)."""
import json
import os
import sys
from pathlib import Path

import requests

PROJECTS_PATH = Path(__file__).resolve().parent.parent / "sites" / "src" / "data" / "projects.json"
API_BASE = "https://api.cloudflare.com/client/v4"


def load_projects():
    with open(PROJECTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_existing_domains(account_id, project_name, token):
    resp = requests.get(
        f"{API_BASE}/accounts/{account_id}/pages/projects/{project_name}/domains",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return {d["name"] for d in resp.json()["result"]}


def add_domain(account_id, project_name, token, domain):
    resp = requests.post(
        f"{API_BASE}/accounts/{account_id}/pages/projects/{project_name}/domains",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": domain},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def sync_subdomains(account_id, project_name, token, projects):
    existing = get_existing_domains(account_id, project_name, token)
    created = []
    for project in projects:
        subdomain = project["subdomain"]
        if subdomain in existing:
            print(f"SKIP (already exists): {subdomain}")
            continue
        add_domain(account_id, project_name, token, subdomain)
        created.append(subdomain)
        print(f"CREATED: {subdomain}")
    return created


def main():
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    project_name = os.environ["CLOUDFLARE_PAGES_PROJECT"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    projects = load_projects()
    sync_subdomains(account_id, project_name, token, projects)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
