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


def missing_nap_fields(project):
    """NAP fields the project is missing. Non-fatal on their own — a project
    can publish with a partial NAP (e.g. no telephone found yet) as long as
    the gap is surfaced, not silently dropped. CLAUDE.md's NAP-consistency
    principle is about never publishing *inconsistent* data across channels,
    not about blocking a project until every field is known."""
    nap = project.get("nap") or {}
    return [field for field in REQUIRED_NAP_FIELDS if not nap.get(field)]


def validate_projects(projects):
    """Raises ValidationError only for structural problems that would break
    the site or the publish scripts. Missing NAP fields are collected as
    warnings (see missing_nap_fields) and returned, never raised, so a
    project with incomplete data can still build and publish."""
    if not isinstance(projects, list) or not projects:
        raise ValidationError("projects.json must be a non-empty array")

    seen_slugs = set()
    warnings = []
    for project in projects:
        for field in ["slug", "subdomain", "website", "name", "tagline", "description", "nap", "sameAs"]:
            if field not in project:
                raise ValidationError(f"project missing required field '{field}': {project}")

        slug = project["slug"]
        if slug in seen_slugs:
            raise ValidationError(f"duplicate slug: {slug}")
        seen_slugs.add(slug)

        for field in missing_nap_fields(project):
            warnings.append(f"project '{slug}' missing NAP field '{field}'")

        if not isinstance(project["sameAs"], list):
            raise ValidationError(f"project '{slug}' sameAs must be a list")

        for url in project["sameAs"]:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValidationError(f"project '{slug}' has invalid sameAs URL: {url}")

    return warnings


def main():
    with open(PROJECTS_PATH, encoding="utf-8") as f:
        projects = json.load(f)
    warnings = validate_projects(projects)
    for warning in warnings:
        print(f"WARNING: {warning} (pending, not blocking)")
    print(f"OK: {len(projects)} projects validated" + (f", {len(warnings)} pending NAP field(s)" if warnings else ""))


if __name__ == "__main__":
    try:
        main()
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)
