# Fase 1: Sitio funcional con Astro + automatización multi-canal

> Spec de diseño. Fase 2 (diseño visual/UI) queda fuera de alcance: aquí solo
> se busca un sitio funcional, semánticamente correcto y SEO-friendly.

## Objetivo

Construir la fase 1 funcional del sistema de citaciones descrito en
`CLAUDE.md`: páginas de citación + posts de apoyo para 3 proyectos reales,
publicados en 3 canales (Cloudflare Pages, GitHub Pages, Blogger), con
generación de sitemap, datos estructurados JSON-LD, y automatización de
DNS/subdominios, publicación en Blogger e indexación (IndexNow).

## Datos de los proyectos (reales, van directo a `projects.json`)

Dominio del hub: **easyleads.es**

| slug | subdominio | nombre | dirección | teléfono |
|---|---|---|---|---|
| easyseo | easyseo.easyleads.es | Easy SEO | C. Jenaro Oraá Kalea, 3BIS, 2ºC, 48980 Santurtzi, Biscay | 695 50 19 79 |
| newcom | newcom.easyleads.es | Newcom Bilbao | Trauko Kalea, 24, Uribarri, 48007 Bilbao, Bizkaia | 944 46 65 98 |
| arroba | arroba.easyleads.es | Arroba PC | Juan XXIII Kalea, 5, 48980 Santurtzi, Bizkaia | 946 12 94 27 |

Descripciones y `sameAs` de cada proyecto: ver mensaje del usuario en la
conversación de diseño (se trasladan literalmente a `projects.json`).

Tipo de JSON-LD: **`LocalBusiness`** (son negocios físicos reales), no
`Organization` genérico.

## Arquitectura general

Un solo repo, un solo build de Astro (`output: 'static'`), parametrizado por
`SITE_TARGET` (`cloudflare` | `github`), que alimenta 3 canales:

```
                         easyleads.es (Cloudflare Pages, 1 proyecto)
                                    │
                    Pages Function _middleware.ts
                    (reescribe por Host → /<slug>/*)
                                    │
        ┌───────────────┬───────────────┬───────────────┐
        │               │               │               │
easyseo.easyleads.es newcom.easyleads.es arroba.easyleads.es  easyleads.es/ (índice)
   → /easyseo/*        → /newcom/*       → /arroba/*

GitHub Pages (mismo repo, mismo build con SITE_TARGET=github)
   gh.easyleads.es/easyseo/   gh.easyleads.es/newcom/   gh.easyleads.es/arroba/

Blogger (1 blog, creado a mano)
   posts.insert/update por cada post de apoyo (variante "blogger"),
   enlazando a la página de citación de su proyecto
```

- Cloudflare es el hub: cada negocio tiene su subdominio propio gracias al
  middleware de reescritura por `Host`.
- GitHub Pages sirve por rutas (no necesita middleware: el build ya está
  organizado en carpetas `/slug/`).
- Blogger no consume el HTML de Astro: el script de publicación lee
  directamente el markdown fuente.

## Modelo de datos

```
sites/
├── src/
│   ├── data/
│   │   └── projects.json
│   └── content/
│       └── posts/
│           ├── easyseo/<post-slug>/{cloudflare,github,blogger}.md
│           ├── newcom/<post-slug>/{cloudflare,github,blogger}.md
│           └── arroba/<post-slug>/{cloudflare,github,blogger}.md
```

- `projects.json`: array de `{ slug, subdomain, name, description, nap:
  {streetAddress, addressLocality, postalCode, addressCountry, telephone},
  sameAs: [] }`. Única fuente de verdad del NAP — garantiza consistencia
  carácter por carácter en los 3 canales.
- Cada post de apoyo es una carpeta con 3 variantes de contenido
  (`cloudflare.md`, `github.md`, `blogger.md`), mismo frontmatter base
  (`title`, `date`, `project`), cuerpo editable de forma independiente.
  Empiezan como copias casi idénticas y se diferencian con el tiempo para
  mejorar originalidad/indexabilidad.
- La página de citación (NAP + JSON-LD) **no varía** por canal: ahí la
  prioridad es la consistencia, no la originalidad.

## Plantillas Astro (v1 simple, SEO-friendly, sin diseño visual)

```
sites/src/
├── pages/
│   ├── index.astro                      # listado de proyectos (hub root)
│   ├── [slug]/
│   │   ├── index.astro                  # página de citación del proyecto
│   │   └── blog/[post]/index.astro      # posts de apoyo
│   └── sitemap.xml.ts                   # sitemap dinámico
├── layouts/
│   └── BaseLayout.astro                 # SEO: title, meta description, canonical, OG, slot JSON-LD
└── templates/
    ├── Citation.astro                   # NAP + JSON-LD LocalBusiness + descripción
    └── Post.astro                       # post + enlace a la citación de su proyecto
```

Mínimos SEO v1:
- HTML semántico: `<h1>` único con el nombre de la entidad, `<address>` para
  el NAP visible.
- `<title>` y `<meta name="description">` únicos por página.
- `<link rel="canonical">` a la URL del subdominio/dominio correspondiente.
- JSON-LD `LocalBusiness` embebido con `sameAs` completo.
- Posts enlazan con `<a>` normal (sin JS) a la página de citación.
- `sitemap.xml` por target (`easyleads.es` y `gh.easyleads.es`).

## Cloudflare: subdominios + middleware de reescritura

```
sites/
├── astro.config.mjs        # output: 'static'
└── functions/
    └── _middleware.ts      # Pages Function — reescribe por Host

scripts/
└── cf_create_subdomain.py
```

- `_middleware.ts`: lee el header `Host`; si coincide con `<slug>.easyleads.es`,
  reescribe internamente añadiendo el prefijo `/<slug>` (la URL visible no
  cambia para el usuario); si es el dominio raíz, sirve tal cual.
- `cf_create_subdomain.py`: por cada proyecto en `projects.json`, llama a
  `POST /accounts/{account_id}/pages/projects/{project_name}/domains` de la
  API de Cloudflare Pages. Idempotente: antes de crear, `GET` de dominios
  existentes y omite si ya está. Esto crea el DNS automáticamente (zona ya
  está en Cloudflare).

## GitHub Pages + CI/CD

```
.github/workflows/
└── deploy.yml
```

- Mismo repo (no uno separado) para GitHub Pages, usando "Pages from
  Actions".
- `SITE_TARGET` controla: variante de post usada (`cloudflare.md` vs
  `github.md`) y la `site` base de Astro (canonical/sitemap).
- Jobs del workflow (en cada push a `main`), independientes entre sí:
  1. `validate` — `scripts/validate_projects.py` (esquema de `projects.json`:
     slug único, NAP completo, `sameAs` son URLs válidas) + `astro build`
     para ambos `SITE_TARGET` como gate.
  2. `deploy-cloudflare` — build `SITE_TARGET=cloudflare` → deploy a
     Cloudflare Pages.
  3. `deploy-github` — build `SITE_TARGET=github` → genera `dist/CNAME` con
     `gh.easyleads.es` → deploy a GitHub Pages.
  4. `blogger-publish` — corre `scripts/blogger_publish.py` automáticamente
     en cada push.
  5. `submit-indexnow` — `needs` de los 3 anteriores, `if: always()`; solo
     notifica los despliegues que tuvieron éxito; un fallo aquí no rompe el
     build (es un plus, no la fuente de verdad de indexación).

## Blogger: script de publicación

```
scripts/
└── blogger_publish.py
```

- OAuth2 con refresh token en secretos (`BLOGGER_OAUTH_CLIENT_ID/SECRET`,
  `BLOGGER_REFRESH_TOKEN`); intercambia por access token en cada ejecución,
  sin flujo interactivo en CI.
- Idempotencia y ediciones posteriores: registro en
  `data/blogger_published.json` (`post_id → {blogger_post_url, content_hash}`),
  commiteado al repo. Si el post no está registrado → `posts.insert`
  (`status=live`). Si está registrado pero el hash del `.md` cambió →
  `posts.update`. Esto permite editar posts de Blogger después de publicados.
- Backoff exponencial ante 429/5xx (cuota); falla rápido y explícito ante
  4xx de validación (no reintenta a ciegas).
- Contenido: markdown → HTML simple + enlace final a la página de citación
  del proyecto (`https://<subdominio>.easyleads.es`).

## IndexNow

```
scripts/
└── submit_indexnow.py
```

- `POST https://api.indexnow.org/indexnow` con `host`, `key` y la lista de
  URLs cambiadas (diff de `content/`/`data/` desde el job de CI) — una
  llamada por dominio (`easyleads.es`, `gh.easyleads.es`).
- Archivo de verificación `<key>.txt` servido en la raíz de cada propiedad,
  generado en build desde `INDEXNOW_KEY`.
- Cloudflare ya integra IndexNow nativo en el dashboard para su propio
  dominio; este script cubre además GitHub Pages, que no lo tiene.

## Manejo de errores

- Los jobs `deploy-cloudflare`, `deploy-github`, `blogger-publish` no se
  bloquean entre sí: un fallo de Blogger por cuota no impide los otros dos
  despliegues.
- `validate` corre primero y bloquea todo el pipeline si `projects.json` es
  inválido — no se publican citaciones con NAP incompleto/inconsistente.
- Reintentos solo ante errores transitorios (429/5xx); fallo rápido ante 4xx.

## Testing (fase 1)

- Vitest: middleware de reescritura por Host (subdominio conocido,
  desconocido, dominio raíz) y validador de `projects.json`.
- Gate de CI: `astro build` sin errores para ambos `SITE_TARGET`.
- Sin tests de integración reales contra Cloudflare/Blogger en fase 1 — se
  prueban manualmente una vez antes de automatizar el push.

## Fuera de alcance (fase 2)

- Diseño visual, sistema de estilos, componentes de UI pulidos.
- Wildcard DNS vía Worker (se usa el enfoque de custom domain por proyecto).
- Más de 3 proyectos / escalado del modelo de datos.
