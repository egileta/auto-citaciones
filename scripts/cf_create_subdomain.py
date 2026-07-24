#!/usr/bin/env python3
"""Adds each project's subdomain as a custom domain on the Cloudflare Pages
project, and points it at the project with a proxied CNAME DNS record
(both idempotent).

Registering a domain with Pages does NOT create its DNS record on its own —
that requires zone-level DNS edit rights, which CLOUDFLARE_API_TOKEN (a
Pages-only scoped token) doesn't have. Without the DNS step below, a newly
"created" custom domain never actually resolves.
"""
import json
import os
import sys
from pathlib import Path

import requests

PROJECTS_PATH = Path(__file__).resolve().parent.parent / "sites" / "src" / "data" / "projects.json"
API_BASE = "https://api.cloudflare.com/client/v4"
PAGES_DEV_TARGET_SUFFIX = ".pages.dev"


def load_projects():
    with open(PROJECTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_existing_pages_domains(account_id, project_name, token):
    resp = requests.get(
        f"{API_BASE}/accounts/{account_id}/pages/projects/{project_name}/domains",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return {d["name"] for d in resp.json()["result"]}


def add_pages_domain(account_id, project_name, token, domain):
    resp = requests.post(
        f"{API_BASE}/accounts/{account_id}/pages/projects/{project_name}/domains",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": domain},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_existing_dns_records(zone_id, dns_token):
    resp = requests.get(
        f"{API_BASE}/zones/{zone_id}/dns_records",
        headers={"Authorization": f"Bearer {dns_token}"},
        params={"type": "CNAME", "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    return {r["name"]: r for r in resp.json()["result"]}


def add_dns_cname(zone_id, dns_token, subdomain, target):
    resp = requests.post(
        f"{API_BASE}/zones/{zone_id}/dns_records",
        headers={"Authorization": f"Bearer {dns_token}"},
        json={"type": "CNAME", "name": subdomain, "content": target, "proxied": True, "ttl": 1},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def sync_subdomains(account_id, project_name, token, projects, zone_id=None, dns_token=None):
    existing_pages_domains = get_existing_pages_domains(account_id, project_name, token)
    pages_dev_target = f"{project_name}{PAGES_DEV_TARGET_SUFFIX}"
    existing_dns = get_existing_dns_records(zone_id, dns_token) if zone_id and dns_token else {}

    created = []
    for project in projects:
        subdomain = project["subdomain"]

        if subdomain in existing_pages_domains:
            print(f"SKIP (Pages domain already exists): {subdomain}")
        else:
            add_pages_domain(account_id, project_name, token, subdomain)
            print(f"CREATED (Pages domain): {subdomain}")
            created.append(subdomain)

        if not zone_id or not dns_token:
            continue
        if subdomain in existing_dns:
            print(f"SKIP (DNS record already exists): {subdomain}")
        else:
            add_dns_cname(zone_id, dns_token, subdomain, pages_dev_target)
            print(f"CREATED (DNS CNAME): {subdomain} -> {pages_dev_target}")

    return created


def main():
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    project_name = os.environ["CLOUDFLARE_PAGES_PROJECT"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
    dns_token = os.environ.get("CLOUDFLARE_DNS_TOKEN")
    if not zone_id or not dns_token:
        print(
            "WARNING: CLOUDFLARE_ZONE_ID/CLOUDFLARE_DNS_TOKEN not set — "
            "will register Pages custom domains but skip creating their DNS "
            "records, so new subdomains won't resolve until that's added.",
            file=sys.stderr,
        )
    projects = load_projects()
    sync_subdomains(account_id, project_name, token, projects, zone_id=zone_id, dns_token=dns_token)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
