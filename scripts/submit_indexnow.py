#!/usr/bin/env python3
"""Pings IndexNow for a list of changed URLs, grouped by host."""
import os
import sys
import time
from urllib.parse import urlparse

import requests

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def group_urls_by_host(urls):
    groups = {}
    for url in urls:
        host = urlparse(url).netloc
        groups.setdefault(host, []).append(url)
    return groups


def submit_host(host, urls, key, max_attempts=5):
    delay = 1
    for attempt in range(max_attempts):
        try:
            resp = requests.post(
                INDEXNOW_ENDPOINT,
                json={"host": host, "key": key, "urlList": urls},
                timeout=30,
            )
        except requests.exceptions.RequestException:
            if attempt == max_attempts - 1:
                raise
            time.sleep(delay)
            delay *= 2
            continue

        if resp.status_code in (429, 500, 502, 503) and attempt < max_attempts - 1:
            time.sleep(delay)
            delay *= 2
            continue

        resp.raise_for_status()
        return resp.status_code


def submit_all(urls, key):
    results = {}
    for host, host_urls in group_urls_by_host(urls).items():
        results[host] = submit_host(host, host_urls, key)
    return results


def main():
    key = os.environ["INDEXNOW_KEY"]
    urls = [u.strip() for u in sys.argv[1:] if u.strip()]
    if not urls:
        print("No URLs to submit, skipping.")
        return
    results = submit_all(urls, key)
    for host, status in results.items():
        print(f"{host}: HTTP {status}")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as exc:
        print(f"WARNING: IndexNow submission failed: {exc}", file=sys.stderr)
        sys.exit(0)
