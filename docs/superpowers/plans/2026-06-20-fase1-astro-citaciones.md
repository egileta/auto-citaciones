# Fase 1: Sitio Astro funcional + automatización multi-canal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the fase 1 functional citation system: an Astro site with citation pages + support posts for 3 real businesses (Easy SEO, Newcom Bilbao, Arroba PC), deployed to Cloudflare Pages (with per-project subdomains via a Host-rewriting middleware) and GitHub Pages, plus automation scripts for Cloudflare subdomain provisioning, Blogger publishing, and IndexNow submission, wired together in a GitHub Actions workflow.

**Architecture:** One Astro project (`sites/`) built twice per push with `SITE_TARGET` set to `cloudflare` or `github`, switching which content variant and base URL is used. `projects.json` is the single source of truth for NAP data, consumed by both the Astro build and the Python automation scripts. A Cloudflare Pages Function rewrites requests by `Host` header so each business gets its own subdomain without separate deploys.

**Tech Stack:** Astro 4 (static output), TypeScript, Vitest, Python 3 (`requests`), GitHub Actions.

## Global Constraints

- Domain: hub at `easyleads.es`; project subdomains `<slug>.easyleads.es`; GitHub Pages at `gh.easyleads.es` (path-based, `gh.easyleads.es/<slug>/`).
- JSON-LD type is `LocalBusiness` (physical businesses), not generic `Organization`.
- NAP fields (`streetAddress`, `addressLocality`, `postalCode`, `addressCountry`, `telephone`) must be byte-identical across all channels — `projects.json` is the only place they are written.
- Post content has 3 independent variants per post (`cloudflare.md`, `github.md`, `blogger.md`) — never share a single file across channels.
- No visual design work in this phase — semantic HTML only.
- Projects for this phase (exact data, already final):
  - `easyseo` / `easyseo.easyleads.es` / Easy SEO / C. Jenaro Oraá Kalea, 3BIS, 2ºC, 48980 Santurtzi / +34 695 50 19 79
  - `newcom` / `newcom.easyleads.es` / Newcom Bilbao / Trauko Kalea, 24, Uribarri, 48007 Bilbao / +34 944 46 65 98
  - `arroba` / `arroba.easyleads.es` / Arroba PC / Juan XXIII Kalea, 5, 48980 Santurtzi / +34 946 12 94 27

---

## Task 1: Scaffold the Astro project

**Files:**
- Create: `sites/package.json`
- Create: `sites/astro.config.mjs`
- Create: `sites/tsconfig.json`
- Create: `sites/vitest.config.ts`
- Create: `sites/src/pages/index.astro` (placeholder, replaced in Task 7)
- Create: `.gitignore` (repo root)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a working `npm run build` and `npm run test` in `sites/`, used by every later task.

- [ ] **Step 1: Create the repo-root `.gitignore`**

```
node_modules/
dist/
.astro/
.env
```

- [ ] **Step 2: Create `sites/package.json`**

```json
{
  "name": "auto-citaciones-site",
  "type": "module",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "postbuild": "node scripts/write-indexnow-key.mjs",
    "preview": "astro preview",
    "test": "vitest run"
  },
  "dependencies": {
    "astro": "^4.16.0"
  },
  "devDependencies": {
    "vitest": "^2.1.4"
  }
}
```

- [ ] **Step 3: Create `sites/astro.config.mjs`**

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
});
```

- [ ] **Step 4: Create `sites/tsconfig.json`**

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": ["src/**/*", "tests/**/*"]
}
```

- [ ] **Step 5: Create `sites/vitest.config.ts`**

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
  },
});
```

- [ ] **Step 6: Create a placeholder `sites/src/pages/index.astro`**

```astro
---
---
<html lang="es">
  <body>
    <h1>Auto Citaciones</h1>
  </body>
</html>
```

- [ ] **Step 7: Install dependencies**

Run: `cd sites && npm install`
Expected: `node_modules/` created, no errors.

- [ ] **Step 8: Verify the build works**

Run: `cd sites && npm run build`
Expected: exits 0, `sites/dist/index.html` exists.

- [ ] **Step 9: Verify the (currently empty) test command works**

Run: `cd sites && npm run test`
Expected: "No test files found" or exits 0 (no test files exist yet — that's fine for this step).

- [ ] **Step 10: Commit**

```bash
git add .gitignore sites/package.json sites/package-lock.json sites/astro.config.mjs sites/tsconfig.json sites/vitest.config.ts sites/src/pages/index.astro
git commit -m "chore: scaffold Astro project"
```

---

## Task 2: `projects.json` data + loader

**Files:**
- Create: `sites/src/data/projects.json`
- Create: `sites/src/lib/projects.ts`
- Test: `sites/tests/projects.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: `Project` type, `projects: Project[]`, `getProjectBySlug(slug: string): Project | undefined`, `getAllSlugs(): string[]` — used by Tasks 4, 6, 7, 8, 11, 12.

- [ ] **Step 1: Create `sites/src/data/projects.json`**

```json
[
  {
    "slug": "easyseo",
    "subdomain": "easyseo.easyleads.es",
    "name": "Easy SEO",
    "description": "Servicios de agencia SEO especializados en captación de leads cualificados y rediseño web para potenciar el SEO local de tus principales servicios.",
    "nap": {
      "streetAddress": "C. Jenaro Oraá Kalea, 3BIS, 2ºC",
      "addressLocality": "Santurtzi",
      "postalCode": "48980",
      "addressCountry": "ES",
      "telephone": "+34 695 50 19 79"
    },
    "sameAs": [
      "https://www.facebook.com/EasySEOvizcaya",
      "https://www.linkedin.com/company/easy-seo-vizcaya",
      "https://x.com/EasySEO_es",
      "https://sites.google.com/view/agencia-seo-local-vizcaya",
      "https://www.cylex.es/santurtzi/easy-seo-disseny-web-santurtzi-14083038.html",
      "https://firmania.es/santurtzi/easy-seo-disseny-web-santurtzi-2389536",
      "https://www.paginasamarillas.es/f/santurtzi/easy-seo-agencia-de-marketing-en-santurce_234650026_000000001.html",
      "https://es.trustpilot.com/review/easyseo.es",
      "https://linktr.ee/easy_seo_local_vizcaya"
    ]
  },
  {
    "slug": "newcom",
    "subdomain": "newcom.easyleads.es",
    "name": "Newcom Bilbao",
    "description": "Reparación de ordenadores, venta de PCs y portátiles nuevos y reacondicionados. Compra venta de juegos y videoconsolas, venta de merchandising gamer y friki.",
    "nap": {
      "streetAddress": "Trauko Kalea, 24, Uribarri",
      "addressLocality": "Bilbao",
      "postalCode": "48007",
      "addressCountry": "ES",
      "telephone": "+34 944 46 65 98"
    },
    "sameAs": [
      "https://www.facebook.com/newcom.bilbao",
      "https://www.instagram.com/newcom.bilbao/",
      "https://www.youtube.com/@newcombilbao"
    ]
  },
  {
    "slug": "arroba",
    "subdomain": "arroba.easyleads.es",
    "name": "Arroba PC",
    "description": "Informática y electrónica en el centro de Santurtzi junto al metro. Venta, reparación y asesoramiento en ordenadores, móviles y consolas. ¡Visítanos!",
    "nap": {
      "streetAddress": "Juan XXIII Kalea, 5",
      "addressLocality": "Santurtzi",
      "postalCode": "48980",
      "addressCountry": "ES",
      "telephone": "+34 946 12 94 27"
    },
    "sameAs": [
      "https://www.facebook.com/PCSanturtzi",
      "https://www.instagram.com/arrobapcsanturtzi"
    ]
  }
]
```

- [ ] **Step 2: Write the failing test `sites/tests/projects.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { projects, getProjectBySlug, getAllSlugs } from '../src/lib/projects';

describe('projects data loader', () => {
  it('loads exactly 3 projects', () => {
    expect(projects).toHaveLength(3);
  });

  it('finds a project by slug', () => {
    const project = getProjectBySlug('easyseo');
    expect(project?.name).toBe('Easy SEO');
    expect(project?.nap.telephone).toBe('+34 695 50 19 79');
  });

  it('returns undefined for unknown slug', () => {
    expect(getProjectBySlug('nope')).toBeUndefined();
  });

  it('returns all slugs in file order', () => {
    expect(getAllSlugs()).toEqual(['easyseo', 'newcom', 'arroba']);
  });

  it('every project has complete NAP data', () => {
    for (const project of projects) {
      expect(project.nap.streetAddress).toBeTruthy();
      expect(project.nap.addressLocality).toBeTruthy();
      expect(project.nap.postalCode).toBeTruthy();
      expect(project.nap.addressCountry).toBe('ES');
      expect(project.nap.telephone).toBeTruthy();
    }
  });
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd sites && npm run test`
Expected: FAIL — `Cannot find module '../src/lib/projects'`.

- [ ] **Step 4: Create `sites/src/lib/projects.ts`**

```ts
import projectsData from '../data/projects.json';

export interface ProjectNap {
  streetAddress: string;
  addressLocality: string;
  postalCode: string;
  addressCountry: string;
  telephone: string;
}

export interface Project {
  slug: string;
  subdomain: string;
  name: string;
  description: string;
  nap: ProjectNap;
  sameAs: string[];
}

export const projects: Project[] = projectsData as Project[];

export function getProjectBySlug(slug: string): Project | undefined {
  return projects.find((project) => project.slug === slug);
}

export function getAllSlugs(): string[] {
  return projects.map((project) => project.slug);
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd sites && npm run test`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add sites/src/data/projects.json sites/src/lib/projects.ts sites/tests/projects.test.ts
git commit -m "feat: add projects.json data and loader"
```

---

## Task 3: `validate_projects.py`

**Files:**
- Create: `scripts/requirements.txt`
- Create: `scripts/validate_projects.py`
- Test: `scripts/test_validate_projects.py`

**Interfaces:**
- Consumes: `sites/src/data/projects.json` (from Task 2).
- Produces: `validate_projects(projects: list) -> bool` (raises `ValidationError`) — used by Task 16 (CI gate) and reusable by Task 13/14 scripts if needed.

- [ ] **Step 1: Create `scripts/requirements.txt`**

```
requests>=2.31
```

- [ ] **Step 2: Write the failing test `scripts/test_validate_projects.py`**

```python
import unittest

from validate_projects import validate_projects, ValidationError


def base_project():
    return {
        "slug": "demo",
        "subdomain": "demo.easyleads.es",
        "name": "Demo",
        "description": "desc",
        "nap": {
            "streetAddress": "Calle 1",
            "addressLocality": "Bilbao",
            "postalCode": "48000",
            "addressCountry": "ES",
            "telephone": "+34 600 00 00 00",
        },
        "sameAs": ["https://example.com"],
    }


class ValidateProjectsTest(unittest.TestCase):
    def test_valid_project_list_passes(self):
        self.assertTrue(validate_projects([base_project()]))

    def test_empty_list_fails(self):
        with self.assertRaises(ValidationError):
            validate_projects([])

    def test_missing_nap_field_fails(self):
        project = base_project()
        del project["nap"]["telephone"]
        with self.assertRaises(ValidationError):
            validate_projects([project])

    def test_duplicate_slug_fails(self):
        with self.assertRaises(ValidationError):
            validate_projects([base_project(), base_project()])

    def test_invalid_same_as_url_fails(self):
        project = base_project()
        project["sameAs"] = ["not-a-url"]
        with self.assertRaises(ValidationError):
            validate_projects([project])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd scripts && python -m unittest test_validate_projects.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_projects'`.

- [ ] **Step 4: Create `scripts/validate_projects.py`**

```python
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
        for field in ["slug", "subdomain", "name", "description", "nap", "sameAs"]:
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd scripts && python -m unittest test_validate_projects.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Run the script against the real data**

Run: `python scripts/validate_projects.py`
Expected: `OK: 3 projects validated`.

- [ ] **Step 7: Commit**

```bash
git add scripts/requirements.txt scripts/validate_projects.py scripts/test_validate_projects.py
git commit -m "feat: add projects.json schema validator"
```

---

## Task 4: JSON-LD builder + base layout + citation template

**Files:**
- Create: `sites/src/lib/jsonld.ts`
- Create: `sites/src/layouts/BaseLayout.astro`
- Create: `sites/src/templates/Citation.astro`
- Test: `sites/tests/jsonld.test.ts`

**Interfaces:**
- Consumes: `Project` type and `getProjectBySlug` from `sites/src/lib/projects.ts` (Task 2).
- Produces: `buildLocalBusinessJsonLd(project: Project, canonicalUrl: string): Record<string, unknown>`; `<BaseLayout title description canonicalUrl jsonLd? />`; `<Citation project canonicalUrl />` — used by Task 6.

- [ ] **Step 1: Write the failing test `sites/tests/jsonld.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { buildLocalBusinessJsonLd } from '../src/lib/jsonld';
import { getProjectBySlug } from '../src/lib/projects';

describe('buildLocalBusinessJsonLd', () => {
  it('builds a LocalBusiness JSON-LD with the project NAP', () => {
    const project = getProjectBySlug('easyseo')!;
    const jsonLd = buildLocalBusinessJsonLd(project, 'https://easyseo.easyleads.es');

    expect(jsonLd['@type']).toBe('LocalBusiness');
    expect(jsonLd.name).toBe('Easy SEO');
    expect(jsonLd.telephone).toBe('+34 695 50 19 79');
    expect((jsonLd.address as Record<string, unknown>).addressCountry).toBe('ES');
    expect(jsonLd.sameAs as string[]).toContain('https://www.linkedin.com/company/easy-seo-vizcaya');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sites && npm run test`
Expected: FAIL — `Cannot find module '../src/lib/jsonld'`.

- [ ] **Step 3: Create `sites/src/lib/jsonld.ts`**

```ts
import type { Project } from './projects';

export function buildLocalBusinessJsonLd(project: Project, canonicalUrl: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: project.name,
    url: canonicalUrl,
    telephone: project.nap.telephone,
    description: project.description,
    address: {
      '@type': 'PostalAddress',
      streetAddress: project.nap.streetAddress,
      addressLocality: project.nap.addressLocality,
      postalCode: project.nap.postalCode,
      addressCountry: project.nap.addressCountry,
    },
    sameAs: project.sameAs,
  };
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sites && npm run test`
Expected: PASS.

- [ ] **Step 5: Create `sites/src/layouts/BaseLayout.astro`**

```astro
---
interface Props {
  title: string;
  description: string;
  canonicalUrl: string;
  jsonLd?: Record<string, unknown>;
}

const { title, description, canonicalUrl, jsonLd } = Astro.props;
---
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content={description} />
    <link rel="canonical" href={canonicalUrl} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:url" content={canonicalUrl} />
    {jsonLd && (
      <script type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
    )}
  </head>
  <body>
    <slot />
  </body>
</html>
```

- [ ] **Step 6: Create `sites/src/templates/Citation.astro`**

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import { buildLocalBusinessJsonLd } from '../lib/jsonld';
import type { Project } from '../lib/projects';

interface Props {
  project: Project;
  canonicalUrl: string;
}

const { project, canonicalUrl } = Astro.props;
const jsonLd = buildLocalBusinessJsonLd(project, canonicalUrl);
---
<BaseLayout
  title={`${project.name} — Información y contacto`}
  description={project.description}
  canonicalUrl={canonicalUrl}
  jsonLd={jsonLd}
>
  <h1>{project.name}</h1>
  <p>{project.description}</p>
  <address>
    {project.nap.streetAddress}<br />
    {project.nap.postalCode} {project.nap.addressLocality}<br />
    Tel: {project.nap.telephone}
  </address>
  <ul>
    {project.sameAs.map((url) => (
      <li><a href={url} rel="me">{url}</a></li>
    ))}
  </ul>
</BaseLayout>
```

- [ ] **Step 7: Verify the build still passes (nothing references these files yet, so this just confirms no syntax errors)**

Run: `cd sites && npm run build`
Expected: exits 0.

- [ ] **Step 8: Commit**

```bash
git add sites/src/lib/jsonld.ts sites/tests/jsonld.test.ts sites/src/layouts/BaseLayout.astro sites/src/templates/Citation.astro
git commit -m "feat: add LocalBusiness JSON-LD builder and citation template"
```

---

## Task 5: Site target (Cloudflare vs GitHub base URLs)

**Files:**
- Create: `sites/src/lib/siteTarget.ts`
- Test: `sites/tests/siteTarget.test.ts`

**Interfaces:**
- Consumes: `process.env.SITE_TARGET` (set by the build command, defaults to `cloudflare`).
- Produces: `SiteTarget = 'cloudflare' | 'github'`; `getSiteTarget(): SiteTarget`; `getHubBaseUrl(target?: SiteTarget): string`; `getProjectBaseUrl(slug: string, target?: SiteTarget): string` — used by Tasks 6, 7, 8, 10.

- [ ] **Step 1: Write the failing test `sites/tests/siteTarget.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { getHubBaseUrl, getProjectBaseUrl } from '../src/lib/siteTarget';

describe('siteTarget base URLs', () => {
  it('cloudflare hub root', () => {
    expect(getHubBaseUrl('cloudflare')).toBe('https://easyleads.es');
  });

  it('github hub root', () => {
    expect(getHubBaseUrl('github')).toBe('https://gh.easyleads.es');
  });

  it('cloudflare project uses a subdomain', () => {
    expect(getProjectBaseUrl('easyseo', 'cloudflare')).toBe('https://easyseo.easyleads.es');
  });

  it('github project uses a path', () => {
    expect(getProjectBaseUrl('easyseo', 'github')).toBe('https://gh.easyleads.es/easyseo');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sites && npm run test`
Expected: FAIL — `Cannot find module '../src/lib/siteTarget'`.

- [ ] **Step 3: Create `sites/src/lib/siteTarget.ts`**

```ts
export type SiteTarget = 'cloudflare' | 'github';

const ROOT_DOMAIN = 'easyleads.es';
const GITHUB_DOMAIN = 'gh.easyleads.es';

export function getSiteTarget(): SiteTarget {
  return process.env.SITE_TARGET === 'github' ? 'github' : 'cloudflare';
}

export function getHubBaseUrl(target: SiteTarget = getSiteTarget()): string {
  return target === 'github' ? `https://${GITHUB_DOMAIN}` : `https://${ROOT_DOMAIN}`;
}

export function getProjectBaseUrl(slug: string, target: SiteTarget = getSiteTarget()): string {
  if (target === 'github') {
    return `https://${GITHUB_DOMAIN}/${slug}`;
  }
  return `https://${slug}.${ROOT_DOMAIN}`;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sites && npm run test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sites/src/lib/siteTarget.ts sites/tests/siteTarget.test.ts
git commit -m "feat: add SITE_TARGET-aware base URL helpers"
```

---

## Task 6: Citation pages (`/<slug>/`)

**Files:**
- Create: `sites/src/pages/[slug]/index.astro`

**Interfaces:**
- Consumes: `projects`, `getAllSlugs` (Task 2); `Citation` template (Task 4); `getProjectBaseUrl` (Task 5).
- Produces: `dist/<slug>/index.html` for each project — consumed by Task 8 (sitemap) and Task 12 (middleware target paths).

- [ ] **Step 1: Create `sites/src/pages/[slug]/index.astro`**

```astro
---
import Citation from '../../templates/Citation.astro';
import { projects, getAllSlugs } from '../../lib/projects';
import { getProjectBaseUrl } from '../../lib/siteTarget';

export function getStaticPaths() {
  return getAllSlugs().map((slug) => ({ params: { slug } }));
}

const { slug } = Astro.params;
const project = projects.find((p) => p.slug === slug)!;
const canonicalUrl = `${getProjectBaseUrl(project.slug)}/`;
---
<Citation project={project} canonicalUrl={canonicalUrl} />
```

- [ ] **Step 2: Build for the cloudflare target and check the output**

Run: `cd sites && npm run build`
Expected: exits 0; `sites/dist/easyseo/index.html`, `sites/dist/newcom/index.html`, `sites/dist/arroba/index.html` exist.

- [ ] **Step 3: Verify NAP and canonical URL for the cloudflare target**

Run: `grep -o 'easyseo.easyleads.es' sites/dist/easyseo/index.html | head -1` and `grep -o '695 50 19 79' sites/dist/easyseo/index.html`
Expected: both commands print a match.

- [ ] **Step 4: Build for the github target and verify the canonical URL changes**

Run (bash): `cd sites && SITE_TARGET=github npm run build && grep -o 'gh.easyleads.es/easyseo' dist/easyseo/index.html`
Expected: prints `gh.easyleads.es/easyseo`.

- [ ] **Step 5: Rebuild for cloudflare to leave a clean default `dist/` and commit**

Run: `cd sites && npm run build`

```bash
git add sites/src/pages/[slug]/index.astro
git commit -m "feat: render citation pages per project"
```

---

## Task 7: Hub index page (`/`)

**Files:**
- Modify: `sites/src/pages/index.astro` (replace the Task 1 placeholder)

**Interfaces:**
- Consumes: `projects` (Task 2); `BaseLayout` (Task 4); `getHubBaseUrl`, `getProjectBaseUrl` (Task 5).
- Produces: `dist/index.html` listing all projects — consumed by Task 8 (sitemap root URL).

- [ ] **Step 1: Replace `sites/src/pages/index.astro`**

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import { projects } from '../lib/projects';
import { getHubBaseUrl, getProjectBaseUrl } from '../lib/siteTarget';

const canonicalUrl = `${getHubBaseUrl()}/`;
---
<BaseLayout
  title="Easyleads — Directorio de proyectos"
  description="Directorio de negocios y proyectos gestionados por Easyleads."
  canonicalUrl={canonicalUrl}
>
  <h1>Proyectos</h1>
  <ul>
    {projects.map((project) => (
      <li>
        <a href={`${getProjectBaseUrl(project.slug)}/`}>{project.name}</a>
      </li>
    ))}
  </ul>
</BaseLayout>
```

- [ ] **Step 2: Build and verify all 3 project names appear**

Run: `cd sites && npm run build && grep -o 'Easy SEO' dist/index.html && grep -o 'Newcom Bilbao' dist/index.html && grep -o 'Arroba PC' dist/index.html`
Expected: each grep prints a match.

- [ ] **Step 3: Verify the links use subdomains for the cloudflare target**

Run: `grep -o 'https://easyseo.easyleads.es/' sites/dist/index.html`
Expected: prints a match.

- [ ] **Step 4: Commit**

```bash
git add sites/src/pages/index.astro
git commit -m "feat: add hub index page listing all projects"
```

---

## Task 8: Sitemap endpoint

**Files:**
- Create: `sites/src/pages/sitemap.xml.ts`

**Interfaces:**
- Consumes: `projects` (Task 2); `getHubBaseUrl`, `getProjectBaseUrl` (Task 5).
- Produces: `dist/sitemap.xml` — extended in Task 10 to include post URLs.

- [ ] **Step 1: Create `sites/src/pages/sitemap.xml.ts`**

```ts
import type { APIRoute } from 'astro';
import { projects } from '../lib/projects';
import { getHubBaseUrl, getProjectBaseUrl } from '../lib/siteTarget';

export const GET: APIRoute = () => {
  const hub = getHubBaseUrl();
  const urls = [`${hub}/`, ...projects.map((p) => `${getProjectBaseUrl(p.slug)}/`)];

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((url) => `  <url><loc>${url}</loc></url>`)
    .join('\n')}\n</urlset>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
```

- [ ] **Step 2: Build and verify the sitemap content**

Run: `cd sites && npm run build && cat dist/sitemap.xml`
Expected: XML containing `https://easyleads.es/`, `https://easyseo.easyleads.es/`, `https://newcom.easyleads.es/`, `https://arroba.easyleads.es/`.

- [ ] **Step 3: Commit**

```bash
git add sites/src/pages/sitemap.xml.ts
git commit -m "feat: generate sitemap.xml from projects data"
```

---

## Task 9: Post loader (`lib/posts.ts`)

**Files:**
- Create: `sites/src/lib/posts.ts`
- Test: `sites/tests/posts.test.ts`

**Interfaces:**
- Consumes: nothing new (pure parsing logic, takes a glob-result map as input).
- Produces: `parsePostPath(path: string): ParsedPostPath | null`; `loadPostsForTarget(modules, target): LoadedPost[]` — used by Task 10's blog page.

- [ ] **Step 1: Write the failing test `sites/tests/posts.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { parsePostPath, loadPostsForTarget } from '../src/lib/posts';

describe('parsePostPath', () => {
  it('parses a valid post path', () => {
    const parsed = parsePostPath('/x/content/posts/easyseo/01-tema/cloudflare.md');
    expect(parsed).toEqual({ projectSlug: 'easyseo', postSlug: '01-tema', channel: 'cloudflare' });
  });

  it('returns null for an unrelated path', () => {
    expect(parsePostPath('/x/content/posts/easyseo/readme.md')).toBeNull();
  });
});

describe('loadPostsForTarget', () => {
  const modules = {
    '/x/content/posts/easyseo/01-tema/cloudflare.md': {
      frontmatter: { title: 'Tema CF', date: '2026-01-01', project: 'easyseo' },
      compiledContent: async () => '<p>cf</p>',
    },
    '/x/content/posts/easyseo/01-tema/github.md': {
      frontmatter: { title: 'Tema GH', date: '2026-01-01', project: 'easyseo' },
      compiledContent: async () => '<p>gh</p>',
    },
    '/x/content/posts/easyseo/01-tema/blogger.md': {
      frontmatter: { title: 'Tema BG', date: '2026-01-01', project: 'easyseo' },
      compiledContent: async () => '<p>bg</p>',
    },
  };

  it('returns only the cloudflare variant for the cloudflare target', () => {
    const posts = loadPostsForTarget(modules, 'cloudflare');
    expect(posts).toHaveLength(1);
    expect(posts[0].frontmatter.title).toBe('Tema CF');
  });

  it('returns only the github variant for the github target', () => {
    const posts = loadPostsForTarget(modules, 'github');
    expect(posts).toHaveLength(1);
    expect(posts[0].frontmatter.title).toBe('Tema GH');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sites && npm run test`
Expected: FAIL — `Cannot find module '../src/lib/posts'`.

- [ ] **Step 3: Create `sites/src/lib/posts.ts`**

```ts
export interface ParsedPostPath {
  projectSlug: string;
  postSlug: string;
  channel: 'cloudflare' | 'github' | 'blogger';
}

export function parsePostPath(path: string): ParsedPostPath | null {
  const match = path.match(/content\/posts\/([^/]+)\/([^/]+)\/(cloudflare|github|blogger)\.md$/);
  if (!match) return null;
  const [, projectSlug, postSlug, channel] = match;
  return { projectSlug, postSlug, channel: channel as ParsedPostPath['channel'] };
}

export interface PostFrontmatter {
  title: string;
  date: string;
  project: string;
}

export interface PostModule {
  frontmatter: PostFrontmatter;
  compiledContent: () => Promise<string>;
}

export interface LoadedPost {
  projectSlug: string;
  postSlug: string;
  frontmatter: PostFrontmatter;
  module: PostModule;
}

const CHANNEL_FOR_TARGET: Record<'cloudflare' | 'github', ParsedPostPath['channel']> = {
  cloudflare: 'cloudflare',
  github: 'github',
};

export function loadPostsForTarget(
  modules: Record<string, PostModule>,
  target: 'cloudflare' | 'github'
): LoadedPost[] {
  const channel = CHANNEL_FOR_TARGET[target];
  const posts: LoadedPost[] = [];

  for (const [path, module] of Object.entries(modules)) {
    const parsed = parsePostPath(path);
    if (!parsed || parsed.channel !== channel) continue;
    posts.push({
      projectSlug: parsed.projectSlug,
      postSlug: parsed.postSlug,
      frontmatter: module.frontmatter,
      module,
    });
  }

  return posts;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sites && npm run test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sites/src/lib/posts.ts sites/tests/posts.test.ts
git commit -m "feat: add post path parser and per-target post loader"
```

---

## Task 10: Seed posts, post template, and blog pages

**Files:**
- Create: `sites/src/content/posts/easyseo/01-como-elegir-agencia-seo-local/{cloudflare,github,blogger}.md`
- Create: `sites/src/content/posts/newcom/01-reparar-o-comprar-nuevo/{cloudflare,github,blogger}.md`
- Create: `sites/src/content/posts/arroba/01-pc-reacondicionado/{cloudflare,github,blogger}.md`
- Create: `sites/src/templates/Post.astro`
- Create: `sites/src/pages/[slug]/blog/[post]/index.astro`
- Modify: `sites/src/pages/sitemap.xml.ts` (add post URLs)

**Interfaces:**
- Consumes: `loadPostsForTarget`, `parsePostPath` (Task 9); `BaseLayout` (Task 4); `getProjectBaseUrl`, `getSiteTarget` (Task 5); `projects` (Task 2).
- Produces: `dist/<slug>/blog/<post>/index.html` for each post; sitemap now includes post URLs.

- [ ] **Step 1: Create the 9 markdown files**

`sites/src/content/posts/easyseo/01-como-elegir-agencia-seo-local/cloudflare.md`:

```markdown
---
title: "Cómo elegir una agencia SEO local en Santurtzi"
date: "2026-06-20"
project: "easyseo"
---

Elegir una agencia SEO local no es lo mismo que contratar una agencia
genérica: en Santurtzi y el resto de Bizkaia, lo que mueve resultados es la
relevancia local — reseñas, citaciones consistentes y contenido pensado para
quien busca el servicio cerca de casa.

En Easy SEO trabajamos la captación de leads cualificados combinando SEO
local con un rediseño web orientado a conversión, no solo a tráfico. Si
quieres revisar cómo está posicionado tu negocio en Santurtzi, puedes
[contactar con Easy SEO](https://easyseo.easyleads.es/).
```

`sites/src/content/posts/easyseo/01-como-elegir-agencia-seo-local/github.md`:

```markdown
---
title: "Cómo elegir una agencia SEO local en Santurtzi"
date: "2026-06-20"
project: "easyseo"
---

No todas las agencias SEO trabajan igual el posicionamiento local. En
Santurtzi y el resto de Bizkaia, lo que marca la diferencia son las
citaciones consistentes, las reseñas reales y un contenido pensado para
quien busca el servicio cerca de casa.

Easy SEO combina SEO local con rediseño web orientado a conversión para
captar leads cualificados, no solo visitas. Más información en
[easyseo.easyleads.es](https://easyseo.easyleads.es/).
```

`sites/src/content/posts/easyseo/01-como-elegir-agencia-seo-local/blogger.md`:

```markdown
---
title: "Cómo elegir una agencia SEO local en Santurtzi"
date: "2026-06-20"
project: "easyseo"
---

Si tienes un negocio en Santurtzi o alrededores, el SEO local es la
diferencia entre aparecer cuando alguien te busca cerca... o no aparecer en
absoluto. Citaciones consistentes y reseñas reales pesan más que el volumen
de contenido.

En Easy SEO ayudamos a negocios de la zona a captar leads cualificados con
SEO local y rediseño web orientado a conversión. Toda la información en
[easyseo.easyleads.es](https://easyseo.easyleads.es/).
```

`sites/src/content/posts/newcom/01-reparar-o-comprar-nuevo/cloudflare.md`:

```markdown
---
title: "Cuándo merece la pena reparar tu ordenador en vez de comprar uno nuevo"
date: "2026-06-20"
project: "newcom"
---

Antes de comprar un ordenador nuevo, vale la pena un diagnóstico: muchos
fallos de lentitud o arranque se solucionan cambiando un disco a SSD o
ampliando RAM, por una fracción del precio de un equipo nuevo.

En Newcom Bilbao, en Uribarri, reparamos ordenadores y también vendemos
equipos nuevos y reacondicionados cuando la reparación ya no compensa. Pasa
por la tienda o consulta en
[newcom.easyleads.es](https://newcom.easyleads.es/).
```

`sites/src/content/posts/newcom/01-reparar-o-comprar-nuevo/github.md`:

```markdown
---
title: "Cuándo merece la pena reparar tu ordenador en vez de comprar uno nuevo"
date: "2026-06-20"
project: "newcom"
---

Un ordenador lento no siempre necesita jubilarse: cambiar el disco duro por
un SSD o ampliar la RAM suele resolver el problema por mucho menos que un
equipo nuevo.

En Newcom Bilbao (Uribarri) reparamos ordenadores y ofrecemos también
equipos nuevos y reacondicionados para cuando la reparación ya no es la
mejor opción. Toda la info en
[newcom.easyleads.es](https://newcom.easyleads.es/).
```

`sites/src/content/posts/newcom/01-reparar-o-comprar-nuevo/blogger.md`:

```markdown
---
title: "Cuándo merece la pena reparar tu ordenador en vez de comprar uno nuevo"
date: "2026-06-20"
project: "newcom"
---

¿Tu ordenador va lento o no arranca bien? Antes de pensar en comprar uno
nuevo, merece la pena revisar si el problema se soluciona con un SSD o más
RAM — suele ser mucho más barato que un equipo nuevo.

Newcom Bilbao, en el barrio de Uribarri, repara ordenadores y también vende
equipos nuevos y reacondicionados. Más detalles en
[newcom.easyleads.es](https://newcom.easyleads.es/).
```

`sites/src/content/posts/arroba/01-pc-reacondicionado/cloudflare.md`:

```markdown
---
title: "Qué revisar antes de comprar un PC reacondicionado"
date: "2026-06-20"
project: "arroba"
---

Un PC reacondicionado puede ser una compra excelente si se ha revisado bien:
estado de la batería (en portátiles), salud del disco, y que los
componentes originales no se hayan cambiado por piezas de menor calidad.

En Arroba PC, junto al metro de Santurtzi, revisamos cada equipo antes de
ponerlo en venta y también compramos y reparamos móviles y consolas. Pásate
por la tienda o consulta en
[arroba.easyleads.es](https://arroba.easyleads.es/).
```

`sites/src/content/posts/arroba/01-pc-reacondicionado/github.md`:

```markdown
---
title: "Qué revisar antes de comprar un PC reacondicionado"
date: "2026-06-20"
project: "arroba"
---

Comprar un PC reacondicionado es una buena opción si está bien revisado:
salud del disco, estado de la batería en portátiles y que no se hayan
cambiado componentes originales por piezas de menor calidad.

Arroba PC, junto al metro de Santurtzi, revisa cada equipo antes de venderlo
y también repara móviles y consolas. Más información en
[arroba.easyleads.es](https://arroba.easyleads.es/).
```

`sites/src/content/posts/arroba/01-pc-reacondicionado/blogger.md`:

```markdown
---
title: "Qué revisar antes de comprar un PC reacondicionado"
date: "2026-06-20"
project: "arroba"
---

Antes de comprar un PC reacondicionado, fíjate en tres cosas: salud del
disco, estado de la batería si es portátil, y que los componentes
originales sigan siendo los de fábrica.

En Arroba PC, junto al metro de Santurtzi, revisamos cada equipo antes de
venderlo y también reparamos móviles y consolas. Toda la info en
[arroba.easyleads.es](https://arroba.easyleads.es/).
```

- [ ] **Step 2: Create `sites/src/templates/Post.astro`**

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import type { LoadedPost } from '../lib/posts';

interface Props {
  post: LoadedPost;
  canonicalUrl: string;
  citationUrl: string;
  html: string;
}

const { post, canonicalUrl, citationUrl, html } = Astro.props;
---
<BaseLayout
  title={post.frontmatter.title}
  description={post.frontmatter.title}
  canonicalUrl={canonicalUrl}
>
  <article>
    <h1>{post.frontmatter.title}</h1>
    <time datetime={post.frontmatter.date}>{post.frontmatter.date}</time>
    <div set:html={html} />
    <p><a href={citationUrl}>Volver a la página de {post.frontmatter.project}</a></p>
  </article>
</BaseLayout>
```

- [ ] **Step 3: Create `sites/src/pages/[slug]/blog/[post]/index.astro`**

```astro
---
import Post from '../../../../templates/Post.astro';
import { loadPostsForTarget, type PostModule, type LoadedPost } from '../../../../lib/posts';
import { getSiteTarget, getProjectBaseUrl } from '../../../../lib/siteTarget';

export async function getStaticPaths() {
  const modules = import.meta.glob<PostModule>('../../../../content/posts/**/*.md', { eager: true });
  const target = getSiteTarget();
  const loaded = loadPostsForTarget(modules, target);
  return loaded.map((post) => ({
    params: { slug: post.projectSlug, post: post.postSlug },
    props: { post },
  }));
}

const { post } = Astro.props as { post: LoadedPost };
const html = await post.module.compiledContent();
const canonicalUrl = `${getProjectBaseUrl(post.projectSlug)}/blog/${post.postSlug}/`;
const citationUrl = `${getProjectBaseUrl(post.projectSlug)}/`;
---
<Post post={post} canonicalUrl={canonicalUrl} citationUrl={citationUrl} html={html} />
```

- [ ] **Step 4: Update `sites/src/pages/sitemap.xml.ts` to include post URLs**

```ts
import type { APIRoute } from 'astro';
import { projects } from '../lib/projects';
import { getHubBaseUrl, getProjectBaseUrl, getSiteTarget } from '../lib/siteTarget';
import { loadPostsForTarget, type PostModule } from '../lib/posts';

export const GET: APIRoute = () => {
  const hub = getHubBaseUrl();
  const target = getSiteTarget();
  const modules = import.meta.glob<PostModule>('../content/posts/**/*.md', { eager: true });
  const posts = loadPostsForTarget(modules, target);

  const urls = [
    `${hub}/`,
    ...projects.map((p) => `${getProjectBaseUrl(p.slug)}/`),
    ...posts.map((p) => `${getProjectBaseUrl(p.projectSlug)}/blog/${p.postSlug}/`),
  ];

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((url) => `  <url><loc>${url}</loc></url>`)
    .join('\n')}\n</urlset>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
```

- [ ] **Step 5: Build and verify the blog pages and sitemap**

Run: `cd sites && npm run build`
Expected: exits 0; `dist/easyseo/blog/01-como-elegir-agencia-seo-local/index.html` exists.

Run: `grep -o 'Cómo elegir una agencia SEO local en Santurtzi' sites/dist/easyseo/blog/01-como-elegir-agencia-seo-local/index.html`
Expected: prints a match.

Run: `grep -c 'blog' sites/dist/sitemap.xml`
Expected: a number greater than 0 (3, one per project's post).

- [ ] **Step 6: Verify the github target uses the github content variant**

Run (bash): `cd sites && SITE_TARGET=github npm run build`
Then: `grep -o 'Newcom Bilbao (Uribarri)' sites/dist/newcom/blog/01-reparar-o-comprar-nuevo/index.html`
Expected: prints a match (this phrase only exists in `github.md`, not `cloudflare.md`).

- [ ] **Step 7: Rebuild for cloudflare to leave a clean default `dist/`**

Run: `cd sites && npm run build`

- [ ] **Step 8: Commit**

```bash
git add sites/src/content/posts sites/src/templates/Post.astro "sites/src/pages/[slug]/blog/[post]/index.astro" sites/src/pages/sitemap.xml.ts
git commit -m "feat: add support posts with per-channel variants and blog pages"
```

---

## Task 11: Host-rewrite logic (`lib/rewriteHost.ts`)

**Files:**
- Create: `sites/src/lib/rewriteHost.ts`
- Test: `sites/tests/rewriteHost.test.ts`

**Interfaces:**
- Consumes: nothing (pure function).
- Produces: `rewritePathForHost(host: string, pathname: string, slugs: string[]): string | null` — used by Task 12's `_middleware.ts`.

- [ ] **Step 1: Write the failing test `sites/tests/rewriteHost.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { rewritePathForHost } from '../src/lib/rewriteHost';

const SLUGS = ['easyseo', 'newcom', 'arroba'];

describe('rewritePathForHost', () => {
  it('rewrites the root path for a known subdomain', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/', SLUGS)).toBe('/easyseo/');
  });

  it('rewrites a nested path for a known subdomain', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/blog/post-1', SLUGS)).toBe(
      '/easyseo/blog/post-1'
    );
  });

  it('does not rewrite the root domain', () => {
    expect(rewritePathForHost('easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('does not rewrite an unknown subdomain', () => {
    expect(rewritePathForHost('unknown.easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('does not double-prefix an already-prefixed path', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/easyseo/blog', SLUGS)).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sites && npm run test`
Expected: FAIL — `Cannot find module '../src/lib/rewriteHost'`.

- [ ] **Step 3: Create `sites/src/lib/rewriteHost.ts`**

```ts
const ROOT_DOMAIN = 'easyleads.es';

export function rewritePathForHost(
  host: string,
  pathname: string,
  slugs: string[]
): string | null {
  const hostname = host.split(':')[0];
  if (hostname === ROOT_DOMAIN) return null;

  const suffix = `.${ROOT_DOMAIN}`;
  if (!hostname.endsWith(suffix)) return null;

  const slug = hostname.slice(0, -suffix.length);
  if (!slugs.includes(slug)) return null;

  if (pathname === `/${slug}` || pathname.startsWith(`/${slug}/`)) {
    return null;
  }

  return pathname === '/' ? `/${slug}/` : `/${slug}${pathname}`;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sites && npm run test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sites/src/lib/rewriteHost.ts sites/tests/rewriteHost.test.ts
git commit -m "feat: add pure Host-based path rewrite logic"
```

---

## Task 12: Cloudflare Pages Function middleware

**Files:**
- Create: `sites/functions/_middleware.ts`

**Interfaces:**
- Consumes: `rewritePathForHost` (Task 11); `getAllSlugs` (Task 2).
- Produces: the actual Cloudflare Pages Function that rewrites subdomain requests at deploy time (not unit-testable — verified manually with `wrangler`).

- [ ] **Step 1: Create `sites/functions/_middleware.ts`**

```ts
import { rewritePathForHost } from '../src/lib/rewriteHost';
import { getAllSlugs } from '../src/lib/projects';

interface PagesEnv {
  ASSETS: { fetch: typeof fetch };
}

interface PagesContext {
  request: Request;
  env: PagesEnv;
  next: () => Promise<Response>;
}

export const onRequest = async (context: PagesContext): Promise<Response> => {
  const url = new URL(context.request.url);
  const newPath = rewritePathForHost(url.hostname, url.pathname, getAllSlugs());

  if (newPath) {
    url.pathname = newPath;
    return context.env.ASSETS.fetch(new Request(url.toString(), context.request));
  }

  return context.next();
};
```

- [ ] **Step 2: Verify the build still includes `functions/` untouched by the Astro build**

Run: `cd sites && npm run build && ls functions/_middleware.ts`
Expected: the file path prints (Astro does not touch `functions/`; it is deployed alongside `dist/` by Cloudflare Pages, which looks for a top-level `functions/` directory next to the output directory).

- [ ] **Step 3: Manually verify the rewrite with Wrangler (one-time, local-only check)**

Run: `cd sites && npx wrangler pages dev dist --compatibility-date=2024-01-01`
Then in another terminal: `curl -H "Host: easyseo.easyleads.es" http://127.0.0.1:8788/`
Expected: response body contains `Easy SEO` (served from `dist/easyseo/index.html` via the rewrite).
Stop the dev server with Ctrl+C when done.

- [ ] **Step 4: Commit**

```bash
git add sites/functions/_middleware.ts
git commit -m "feat: add Cloudflare Pages Function for subdomain rewriting"
```

---

## Task 13: `cf_create_subdomain.py`

**Files:**
- Create: `scripts/cf_create_subdomain.py`
- Test: `scripts/test_cf_create_subdomain.py`

**Interfaces:**
- Consumes: `sites/src/data/projects.json` (Task 2); Cloudflare Pages API.
- Produces: `sync_subdomains(account_id, project_name, token, projects) -> list[str]` (created subdomains) — invoked by `main()`, run manually or from CI in a later phase.

- [ ] **Step 1: Write the failing test `scripts/test_cf_create_subdomain.py`**

```python
import unittest
from unittest.mock import patch, MagicMock

from cf_create_subdomain import sync_subdomains


class SyncSubdomainsTest(unittest.TestCase):
    @patch("cf_create_subdomain.requests.post")
    @patch("cf_create_subdomain.requests.get")
    def test_creates_missing_subdomain_and_skips_existing(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(json=lambda: {"result": [{"name": "newcom.easyleads.es"}]})
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value = MagicMock(json=lambda: {"result": {}})
        mock_post.return_value.raise_for_status = lambda: None

        projects = [
            {"subdomain": "easyseo.easyleads.es"},
            {"subdomain": "newcom.easyleads.es"},
        ]

        created = sync_subdomains("acc", "proj", "token", projects)

        self.assertEqual(created, ["easyseo.easyleads.es"])
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd scripts && python -m unittest test_cf_create_subdomain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cf_create_subdomain'`.

- [ ] **Step 3: Create `scripts/cf_create_subdomain.py`**

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd scripts && python -m unittest test_cf_create_subdomain.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/cf_create_subdomain.py scripts/test_cf_create_subdomain.py
git commit -m "feat: add idempotent Cloudflare Pages subdomain provisioning script"
```

---

## Task 14: `blogger_publish.py`

**Files:**
- Create: `data/blogger_published.json`
- Create: `scripts/blogger_publish.py`
- Test: `scripts/test_blogger_publish.py`

**Interfaces:**
- Consumes: `sites/src/content/posts/*/*/blogger.md` (Task 10); `data/blogger_published.json`; Blogger API v3.
- Produces: `parse_frontmatter(text) -> (dict, str)`; `markdown_to_html(body) -> str`; `publish_posts(blog_id, access_token, posts, published) -> dict` — invoked by `main()`, run from CI in Task 16.

- [ ] **Step 1: Seed `data/blogger_published.json`**

```json
{}
```

- [ ] **Step 2: Write the failing test `scripts/test_blogger_publish.py`**

```python
import unittest
from unittest.mock import patch, MagicMock

from blogger_publish import parse_frontmatter, markdown_to_html, publish_posts


class ParseFrontmatterTest(unittest.TestCase):
    def test_parses_title_and_body(self):
        text = '---\ntitle: "Hola"\ndate: "2026-01-01"\nproject: "demo"\n---\nCuerpo del post.\n'
        frontmatter, body = parse_frontmatter(text)
        self.assertEqual(frontmatter["title"], "Hola")
        self.assertEqual(body, "Cuerpo del post.")


class MarkdownToHtmlTest(unittest.TestCase):
    def test_wraps_paragraphs(self):
        html = markdown_to_html("Uno.\n\nDos.")
        self.assertEqual(html, "<p>Uno.</p><p>Dos.</p>")


class PublishPostsTest(unittest.TestCase):
    def make_post(self, post_id="easyseo/01", content_hash="hash1"):
        return {"post_id": post_id, "title": "T", "body_markdown": "Body", "content_hash": content_hash}

    @patch("blogger_publish.request_with_backoff")
    def test_inserts_new_post(self, mock_request):
        mock_request.return_value = MagicMock(json=lambda: {"url": "https://blog/1", "id": "1"})
        updated = publish_posts("blogid", "token", [self.make_post()], {})
        self.assertIn("easyseo/01", updated)
        self.assertEqual(updated["easyseo/01"]["blogger_post_url"], "https://blog/1")

    @patch("blogger_publish.request_with_backoff")
    def test_updates_when_hash_changed(self, mock_request):
        published = {"easyseo/01": {"blogger_post_url": "u", "blogger_post_id": "1", "content_hash": "old"}}
        updated = publish_posts("blogid", "token", [self.make_post(content_hash="new")], published)
        self.assertEqual(updated["easyseo/01"]["content_hash"], "new")
        mock_request.assert_called_once()

    @patch("blogger_publish.request_with_backoff")
    def test_skips_when_hash_unchanged(self, mock_request):
        published = {"easyseo/01": {"blogger_post_url": "u", "blogger_post_id": "1", "content_hash": "hash1"}}
        updated = publish_posts("blogid", "token", [self.make_post(content_hash="hash1")], published)
        self.assertEqual(updated, published)
        mock_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd scripts && python -m unittest test_blogger_publish.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'blogger_publish'`.

- [ ] **Step 4: Create `scripts/blogger_publish.py`**

```python
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd scripts && python -m unittest test_blogger_publish.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Sanity-check `find_blogger_posts()` against the real seeded content**

Run: `cd scripts && python -c "from blogger_publish import find_blogger_posts; print(len(find_blogger_posts()))"`
Expected: prints `3`.

- [ ] **Step 7: Commit**

```bash
git add data/blogger_published.json scripts/blogger_publish.py scripts/test_blogger_publish.py
git commit -m "feat: add Blogger publish/update script with idempotent tracking"
```

---

## Task 15: `submit_indexnow.py` + IndexNow key file

**Files:**
- Create: `scripts/submit_indexnow.py`
- Create: `sites/scripts/write-indexnow-key.mjs`
- Test: `scripts/test_submit_indexnow.py`

**Interfaces:**
- Consumes: list of changed URLs (CLI args); `INDEXNOW_KEY` env var.
- Produces: `group_urls_by_host(urls) -> dict[str, list[str]]`; `submit_all(urls, key) -> dict[str, int]`; `dist/<key>.txt` written by the npm `postbuild` script (Task 1).

- [ ] **Step 1: Write the failing test `scripts/test_submit_indexnow.py`**

```python
import unittest
from unittest.mock import patch, MagicMock

from submit_indexnow import group_urls_by_host, submit_all


class GroupUrlsByHostTest(unittest.TestCase):
    def test_groups_by_netloc(self):
        urls = [
            "https://easyleads.es/easyseo/",
            "https://easyseo.easyleads.es/",
            "https://gh.easyleads.es/easyseo/",
        ]
        groups = group_urls_by_host(urls)
        self.assertEqual(set(groups.keys()), {"easyleads.es", "easyseo.easyleads.es", "gh.easyleads.es"})


class SubmitAllTest(unittest.TestCase):
    @patch("submit_indexnow.requests.post")
    def test_submits_one_request_per_host(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = lambda: None

        urls = ["https://easyleads.es/a/", "https://gh.easyleads.es/a/"]
        results = submit_all(urls, "thekey")

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(results["easyleads.es"], 200)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd scripts && python -m unittest test_submit_indexnow.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'submit_indexnow'`.

- [ ] **Step 3: Create `scripts/submit_indexnow.py`**

```python
#!/usr/bin/env python3
"""Pings IndexNow for a list of changed URLs, grouped by host."""
import os
import sys
from urllib.parse import urlparse

import requests

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def group_urls_by_host(urls):
    groups = {}
    for url in urls:
        host = urlparse(url).netloc
        groups.setdefault(host, []).append(url)
    return groups


def submit_host(host, urls, key):
    resp = requests.post(
        INDEXNOW_ENDPOINT,
        json={"host": host, "key": key, "urlList": urls},
        timeout=30,
    )
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
    except requests.HTTPError as exc:
        print(f"WARNING: IndexNow submission failed: {exc}", file=sys.stderr)
        sys.exit(0)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd scripts && python -m unittest test_submit_indexnow.py -v`
Expected: PASS.

- [ ] **Step 5: Create `sites/scripts/write-indexnow-key.mjs`**

```js
import { writeFileSync } from 'node:fs';

const key = process.env.INDEXNOW_KEY;
if (!key) {
  console.log('INDEXNOW_KEY not set, skipping key file generation.');
  process.exit(0);
}

writeFileSync(`dist/${key}.txt`, key);
console.log(`Wrote dist/${key}.txt`);
```

- [ ] **Step 6: Verify the postbuild step writes the key file**

Run (bash): `cd sites && INDEXNOW_KEY=test123 npm run build && cat dist/test123.txt`
Expected: prints `test123`.

- [ ] **Step 7: Verify the build still works without the key (no-op, no crash)**

Run: `cd sites && npm run build`
Expected: exits 0, prints `INDEXNOW_KEY not set, skipping key file generation.`.

- [ ] **Step 8: Commit**

```bash
git add scripts/submit_indexnow.py scripts/test_submit_indexnow.py sites/scripts/write-indexnow-key.mjs
git commit -m "feat: add IndexNow submission script and build-time key file generator"
```

---

## Task 16: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: every script and build target from Tasks 1–15.
- Produces: the orchestration that runs on every push to `main`.

- [ ] **Step 1: Create `.github/workflows/deploy.yml`**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/validate_projects.py
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
        working-directory: sites
      - run: npm run build
        working-directory: sites
        env:
          SITE_TARGET: cloudflare
      - run: npm run build
        working-directory: sites
        env:
          SITE_TARGET: github

  deploy-cloudflare:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
        working-directory: sites
      - run: npm run build
        working-directory: sites
        env:
          SITE_TARGET: cloudflare
          INDEXNOW_KEY: ${{ secrets.INDEXNOW_KEY }}
      - uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: ${{ secrets.CLOUDFLARE_PAGES_PROJECT }}
          directory: sites/dist

  deploy-github:
    needs: validate
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
        working-directory: sites
      - run: npm run build
        working-directory: sites
        env:
          SITE_TARGET: github
      - run: echo "gh.easyleads.es" > sites/dist/CNAME
      - uses: actions/upload-pages-artifact@v3
        with:
          path: sites/dist
      - uses: actions/deploy-pages@v4

  blogger-publish:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/blogger_publish.py
        env:
          BLOGGER_BLOG_ID: ${{ secrets.BLOGGER_BLOG_ID }}
          BLOGGER_OAUTH_CLIENT_ID: ${{ secrets.BLOGGER_OAUTH_CLIENT_ID }}
          BLOGGER_OAUTH_CLIENT_SECRET: ${{ secrets.BLOGGER_OAUTH_CLIENT_SECRET }}
          BLOGGER_REFRESH_TOKEN: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: update blogger_published.json"
          file_pattern: data/blogger_published.json

  submit-indexnow:
    needs: [deploy-cloudflare, deploy-github, blogger-publish]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r scripts/requirements.txt
      - run: |
          python scripts/submit_indexnow.py \
            https://easyleads.es/ \
            https://easyseo.easyleads.es/ \
            https://newcom.easyleads.es/ \
            https://arroba.easyleads.es/ \
            https://gh.easyleads.es/
        env:
          INDEXNOW_KEY: ${{ secrets.INDEXNOW_KEY }}
```

- [ ] **Step 2: Verify the YAML is syntactically valid**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml', encoding='utf-8')); print('valid YAML')"`
Expected: prints `valid YAML`.

- [ ] **Step 3: Verify the job graph matches the design (manual checklist)**

Run: `python -c "import yaml; d = yaml.safe_load(open('.github/workflows/deploy.yml', encoding='utf-8')); print(sorted(d['jobs'].keys())); print(d['jobs']['submit-indexnow']['needs'])"`
Expected: prints `['blogger-publish', 'deploy-cloudflare', 'deploy-github', 'submit-indexnow', 'validate']` and `['deploy-cloudflare', 'deploy-github', 'blogger-publish']`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: wire up CI/CD for Cloudflare, GitHub Pages, Blogger and IndexNow"
```

---

## Spec coverage check (self-review)

- Astro site, SEO-friendly templates, JSON-LD `LocalBusiness`, NAP consistency → Tasks 2, 4, 6, 7.
- Posts with 3 independent channel variants → Tasks 9, 10.
- Sitemap → Tasks 8, 10.
- Cloudflare subdomain routing (single project + middleware) → Tasks 11, 12.
- `cf_create_subdomain.py` (idempotent) → Task 13.
- GitHub Pages (same repo, path-based) → Tasks 10 (github variant), 16.
- `blogger_publish.py` (insert/update, idempotent, automatic trigger) → Task 14, wired in Task 16.
- `submit_indexnow.py` + key file → Task 15, wired in Task 16.
- `validate_projects.py` as a CI gate → Task 3, wired in Task 16.
- Independent job failure isolation, `if: always()` on indexnow → Task 16.
- Out of scope (fase 2 design) → not addressed, as intended.

No gaps found against the approved spec.
