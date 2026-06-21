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
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Para arrancar el proyecto en un
equipo nuevo (stack local, credenciales), ver
[`docs/SETUP.md`](docs/SETUP.md).

## Estructura

```
sites/                          Proyecto Astro (output: static)
  src/data/projects.json        NAP + web original de cada negocio
  src/content/posts/<slug>/<post>/{cloudflare,github,blogger}.md
  src/lib/siteTarget.ts         URLs por SITE_TARGET (cloudflare|github)
  src/lib/rewriteHost.ts        Reescritura host -> /<slug>/, o redirect 301
                                 si la petición llega con el path ya prefijado
  src/lib/linkWheel.ts          Enlaces cruzados entre canales para cada post
  src/lib/blogPublished.ts      Lee data/blogger_published.json en build time
  functions/_middleware.ts      Cloudflare Pages Function que aplica esa reescritura
data/blogger_published.json    Registro slug/post -> URL de Blogger (idempotencia)
scripts/
  validate_projects.py          Valida projects.json en CI
  blogger_publish.py            Publica/actualiza posts en Blogger vía API
                                 (incluye NAP+W y rueda de enlaces)
  submit_indexnow.py            Notifica las URLs a IndexNow tras el deploy
.github/workflows/deploy.yml    CI/CD: valida, construye y despliega los 3 canales
```

Las URLs de posts son planas en los 3 canales (`<base>/<post-slug>/`, sin
`/blog/`). Detalle completo de la arquitectura, el fix de contenido
duplicado y la rueda de enlaces en [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

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
