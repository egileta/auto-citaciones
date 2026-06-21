#!/usr/bin/env python3
"""Validates sites/src/data/projects.json against the schema required by CLAUDE.md."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECTS_PATH = Path(__file__).resolve().parent.parent / "sites" / "src" / "data" / "projects.json"

REQUIRED_NAP_FIELDS = ["streetAddress", "addressLocality", "postalCode", "addressCountry", "telephone"]


class ValidationError(Exception):
    pass


def validate_projects(projects):
    if not isinstance(projects, list) or not projects:
        raise ValidationError("projects.json must be a non-empty array")

    seen_slugs = set()
    for project in projects:
        for field in ["slug", "subdomain", "website", "name", "tagline", "description", "nap", "sameAs"]:
            if field not in project:
                raise ValidationError(f"project missing required field '{field}': {project}")

        slug = project["slug"]
        if slug in seen_slugs:
            raise ValidationError(f"duplicate slug: {slug}")
        seen_slugs.add(slug)

        nap = project["nap"]
        for field in REQUIRED_NAP_FIELDS:
            if not nap.get(field):
                raise ValidationError(f"project '{slug}' missing NAP field '{field}'")

        if not isinstance(project["sameAs"], list):
            raise ValidationError(f"project '{slug}' sameAs must be a list")

        for url in project["sameAs"]:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValidationError(f"project '{slug}' has invalid sameAs URL: {url}")

    return True


def main():
    with open(PROJECTS_PATH, encoding="utf-8") as f:
        projects = json.load(f)
    validate_projects(projects)
    print(f"OK: {len(projects)} projects validated")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)
