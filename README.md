# Auto Citaciones

Sitio Astro multi-proyecto que publica citaciones locales (NAP) y posts de
apoyo SEO para varios negocios (`easyseo`, `newcom`, `arroba`) a través de
tres canales independientes:

1. **Cloudflare Pages** — un subdominio por proyecto bajo `easyleads.es`.
2. **GitHub Pages** — hub único en `gh.easyleads.es` con una ruta por proyecto.
3. **Blogger** — posts de apoyo publicados vía API en `easy-leads.blogspot.com`.

Los tres canales reciben **contenido distinto por proyecto y por canal**
(`cloudflare.md`, `github.md`, `blogger.md` por cada post) para evitar
contenido duplicado entre subdominios y penalizaciones SEO.

Documentación completa de la infraestructura y cómo reproducirla:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Estructura

```
sites/                          Proyecto Astro (output: static)
  src/data/projects.json        NAP + web original de cada negocio
  src/content/posts/<slug>/<post>/{cloudflare,github,blogger}.md
  src/lib/siteTarget.ts         URLs por SITE_TARGET (cloudflare|github)
  src/lib/rewriteHost.ts        Lógica de reescritura host -> /<slug>/
  functions/_middleware.ts      Cloudflare Pages Function que aplica esa reescritura
scripts/
  validate_projects.py          Valida projects.json en CI
  blogger_publish.py            Publica/actualiza posts en Blogger vía API
  submit_indexnow.py            Notifica las URLs a IndexNow tras el deploy
.github/workflows/deploy.yml    CI/CD: valida, construye y despliega los 3 canales
```

## Desarrollo local

```bash
cd sites
npm ci
npm run build           # SITE_TARGET=cloudflare por defecto
SITE_TARGET=github npm run build
npm test
```

## Despliegue

El despliegue es automático en cada push a `main` (ver `.github/workflows/deploy.yml`).
Para la lista de secrets necesarios y el procedimiento de configuración desde
cero, ver [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
