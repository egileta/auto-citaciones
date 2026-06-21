# Despliegue de los 3 canales — runbook

Este documento describe cómo está montada la infraestructura de los tres
canales de publicación (Cloudflare Pages, GitHub Pages, Blogger) y los pasos
exactos para reproducirla desde cero. Incluye, al final, los errores reales
con los que nos topamos la primera vez y su causa, para no repetirlos.

## Arquitectura

Un único proyecto Astro (`sites/`) en modo `output: 'static'` se construye
dos veces por despliegue, una por `SITE_TARGET`:

- `SITE_TARGET=cloudflare` → un mismo build se sirve en **3 dominios
  distintos** (`easyseo.easyleads.es`, `newcom.easyleads.es`,
  `arroba.easyleads.es`) desde el **mismo** proyecto de Cloudflare Pages.
  Como el build es idéntico para los tres dominios, una **Cloudflare Pages
  Function** (`sites/functions/_middleware.ts`, lógica pura en
  `sites/src/lib/rewriteHost.ts`) inspecciona el header `Host` en cada
  petición y reescribe `/` → `/<slug>/` para servir el contenido del
  proyecto correcto. Sin esa función, los tres subdominios muestran
  siempre la página "hub" con la lista de los 3 proyectos. Si la petición
  llega ya con el path interno con prefijo (p.ej.
  `easyseo.easyleads.es/easyseo/01-post/`, una fuga típica si alguien
  enlaza directamente al path físico del build), la Function responde con
  un **redirect 301** a la versión limpia (`/01-post/`) en vez de
  reescribir/pasar el contenido — evita servir la misma página en dos URLs
  (contenido duplicado).
- `SITE_TARGET=github` → un build con rutas `/`, `/easyseo/`, `/newcom/`,
  `/arroba/` y posts en `/<slug>/<post>/` (sin segmento `/blog/`), servido
  en GitHub Pages bajo el dominio propio `gh.easyleads.es`.
- **Blogger**: no usa el build de Astro. `scripts/blogger_publish.py` lee
  directamente los `*/*/blogger.md` y los publica vía API.

**URLs de posts:** en los tres canales un post vive en
`<base>/<post-slug>/` (p.ej. `https://easyseo.easyleads.es/01-post/`,
`https://gh.easyleads.es/easyseo/01-post/`) — sin `/blog/` ni doble
prefijo del slug del proyecto.

**Rueda de enlaces (link wheel):** cada post, en los tres canales, incluye
tras su contenido los datos NAP+W del negocio y enlaces a las versiones del
mismo post en los otros canales (`sites/src/lib/linkWheel.ts` para
Cloudflare/GitHub vía `Post.astro`; `build_nap_html`/`build_link_wheel_html`
en `scripts/blogger_publish.py` para Blogger). El enlace a la versión de
Blogger solo aparece una vez que el post ya se publicó allí y quedó
registrado en `data/blogger_published.json` (`sites/src/lib/blogPublished.ts`
lee ese mismo fichero en tiempo de build) — en el primer despliegue de un
post nuevo, ese enlace concreto aparecerá a partir del segundo build.

Cada post tiene **tres ficheros markdown distintos**
(`cloudflare.md`, `github.md`, `blogger.md`) con redacción diferente para
evitar contenido duplicado entre canales (penalización SEO).

**Regla de contenido:** todo enlace de salida en estos markdown, y el campo
`website` de `sites/src/data/projects.json`, deben apuntar al **dominio
real del negocio** (p.ej. `arrobapc.es`), nunca a los subdominios
`*.easyleads.es` ni a `gh.easyleads.es` — esos son solo el hosting de la
citación, no la web del negocio.

## 0. Prerrequisitos del repo

- El repo debe ser **público** (GitHub Pages gratis no funciona en
  privado salvo plan Pro/Team/Enterprise).
- La rama por defecto debe llamarse `main` (el workflow dispara con
  `on: push: branches: [main]`).

## 1. Cloudflare Pages

### 1.1 Crear el proyecto Pages (no un Worker)

El dashboard de Cloudflare ("Workers y Pages") a veces solo ofrece crear
**Workers Services**, no proyectos Pages clásicos, según la cuenta. Si el
botón "Crear proyecto Pages" no aparece, créalo por API:

```bash
curl -X POST -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/pages/projects" \
  -d '{"name":"<nombre-proyecto>","production_branch":"main"}'
```

Verifica que es un proyecto Pages real (no un Worker) comprobando que
aparece en `GET .../pages/projects`, y no solo en `.../workers/scripts`.

### 1.2 Conectar los dominios personalizados

Para cada subdominio:

```bash
curl -X POST -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/pages/projects/<proyecto>/domains" \
  -d '{"name":"<subdominio>.easyleads.es"}'
```

Esto **no crea el registro DNS**. Hay que crearlo también, en la zona
DNS (necesita un token con permiso `Zone > DNS > Edit`, distinto del token
de Pages):

```bash
curl -X POST -H "Authorization: Bearer $CF_DNS_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -d '{"type":"CNAME","name":"<subdominio>","content":"<proyecto>.pages.dev","proxied":true}'
```

Un dominio solo puede estar vinculado a **un** proyecto Cloudflare
(Pages o Worker) a la vez — si vienes de otra configuración, desvincúlalo
primero del proyecto antiguo.

### 1.3 Secrets de GitHub necesarios

- `CLOUDFLARE_API_TOKEN` — scope `Account > Cloudflare Pages > Edit`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_PAGES_PROJECT` — nombre del proyecto Pages

### 1.4 Punto crítico: desplegar las Pages Functions

`cloudflare/pages-action@v1` ejecuta Wrangler, que busca la carpeta
`functions/` **relativa al `workingDirectory`**, no relativa al
`directory` de publicación. El job `deploy-cloudflare` debe ser:

```yaml
- uses: cloudflare/pages-action@v1
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    projectName: ${{ secrets.CLOUDFLARE_PAGES_PROJECT }}
    workingDirectory: sites      # para que encuentre sites/functions
    directory: dist              # relativo a workingDirectory
```

Sin `workingDirectory: sites`, Wrangler busca `./functions` en la raíz del
repo (no existe), la Function nunca se despliega, y todos los subdominios
muestran el mismo contenido (el hub), aunque el deploy aparezca en verde.

## 2. GitHub Pages

### 2.1 Activar Pages

```bash
gh api repos/<owner>/<repo>/pages -X POST -f build_type=workflow
```

Falla con 422 si el repo es privado y no hay plan de pago — hacer el repo
público primero (`gh repo edit --visibility public
--accept-visibility-change-consequences`).

### 2.2 Permisos del job en el workflow

```yaml
deploy-github:
  permissions:
    contents: read
    pages: write
    id-token: write
```

Un bloque `permissions:` en un job de Actions **sustituye por completo**
los permisos del `GITHUB_TOKEN` para ese job — cualquier scope que no se
liste se vuelve `none`, no el valor por defecto del repo. Sin
`contents: read` explícito, `actions/checkout` falla con
"repository not found".

### 2.3 Dominio personalizado

```bash
# DNS (CNAME sin proxy: proxied:false, GitHub necesita validar el host
# directamente para emitir el certificado Let's Encrypt)
curl -X POST -H "Authorization: Bearer $CF_DNS_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -d '{"type":"CNAME","name":"gh","content":"<usuario>.github.io","proxied":false}'

# Dominio personalizado en GitHub Pages
gh api -X PUT repos/<owner>/<repo>/pages -f cname=gh.easyleads.es
```

El workflow escribe el fichero `CNAME` en el build (`echo "gh.easyleads.es"
> sites/dist/CNAME`) — debe coincidir exactamente con el cname configurado.

**El certificado HTTPS no es inmediato.** Tras configurar el dominio,
GitHub tarda entre varios minutos y (en casos raros) una hora en emitir el
certificado. Mientras tanto, HTTP funciona pero HTTPS dará error de
certificado. Comprobar con:

```bash
gh api repos/<owner>/<repo>/pages   # status, https_enforced
curl -I https://gh.easyleads.es/
```

## 3. Blogger

### 3.1 Google Cloud / OAuth

1. Crear proyecto en Google Cloud Console, habilitar **Blogger API v3**.
2. Configurar la pantalla de consentimiento OAuth. **Debe estar en estado
   "In production"**, no "Testing": en Testing, el refresh token caduca a
   los 7 días (`refresh_token_expires_in: 604799`) sin importar
   `access_type=offline`, y solo pueden autorizar los "Test users"
   explícitamente añadidos. Para Blogger (scope no sensible) publicar a
   producción no requiere revisión de seguridad de Google, pero el cambio
   de estado puede tardar de minutos a un par de horas en propagar a los
   servidores de autorización — durante ese tiempo pueden aparecer errores
   genéricos ("That's an error", 400/500) sin relación con la
   configuración real.
3. Crear credenciales OAuth tipo **Desktop app** (cliente ID + secreto).

### 3.2 Obtener el refresh token (flujo manual)

```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=<CLIENT_ID>&
  redirect_uri=http://localhost&
  response_type=code&
  scope=https://www.googleapis.com/auth/blogger&
  access_type=offline&
  prompt=consent
```

Autorizar en el navegador, copiar el parámetro `code=` de la URL de
redirección a `localhost` (dará error de conexión, es esperado — el code
está en la URL igualmente), y canjearlo:

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d client_id=<CLIENT_ID> \
  -d client_secret=<CLIENT_SECRET> \
  -d code=<CODE> \
  -d grant_type=authorization_code \
  -d redirect_uri=http://localhost
```

La respuesta incluye `refresh_token`.

### 3.3 Secrets de GitHub

- `BLOGGER_BLOG_ID`
- `BLOGGER_OAUTH_CLIENT_ID`
- `BLOGGER_OAUTH_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

### 3.4 Punto crítico: permiso de escritura para el tracking file

`scripts/blogger_publish.py` guarda en `data/blogger_published.json` qué
posts ya se publicaron (por `content_hash`), para no duplicarlos. El job
hace `git push` de ese fichero vía `git-auto-commit-action`, así que
necesita:

```yaml
blogger-publish:
  permissions:
    contents: write
```

**Si este push falla** (p.ej. por el permiso por defecto `none`), Blogger
ya habrá publicado los posts correctamente, pero el tracking file seguirá
vacío — en el siguiente run, el script no encontrará los `post_id` en
`published` y los volverá a **insertar como posts nuevos, duplicados**.
Si esto ocurre:

1. Listar los posts del blog vía API
   (`GET /blogs/{blogId}/posts?fetchBodies=false`) y localizar los
   duplicados por título/fecha de publicación.
2. Borrar los más antiguos (los que no están en `data/blogger_published.json`)
   vía `DELETE /blogs/{blogId}/posts/{postId}`.
3. Confirmar que `data/blogger_published.json` en `main` contiene la
   entrada correcta para cada post antes de volver a desplegar.

### 3.5 Limitaciones del conversor markdown→HTML

`markdown_to_html()` en `scripts/blogger_publish.py` es deliberadamente
mínimo: soporta párrafos separados por línea en blanco, `[texto](url)` →
`<a href>`, y `**negrita**`/`*cursiva*`. No soporta encabezados, listas ni
markdown anidado — si se necesita más, ampliar `inline_markdown_to_html`.

## 4. Convención de contenido (los 3 canales)

- `sites/src/data/projects.json` — cada proyecto necesita `slug`,
  `subdomain`, `website` (dominio real del negocio), `name` (razón social
  exacta del negocio — es el dato "N" del NAP, debe coincidir con la que
  usa el negocio en Google Business Profile y demás directorios),
  `tagline`, `description`, `nap` (dirección completa + teléfono) y
  `sameAs`. `validate_projects.py` exige todos estos campos. El JSON-LD
  (`LocalBusiness.url`) y el enlace visible en `Citation.astro` usan
  `project.website`, nunca el subdominio de easyleads.es.
- `Citation.astro` (página raíz de cada subdominio) sigue esta estructura
  fija: h1 = `name`, h2 = `tagline`, párrafo = `description`, h3 "Últimas
  entradas en nuestro blog" + lista de enlaces a posts (de este proyecto y
  de los otros, para indexabilidad cruzada), y **después** h3 "Nuestros
  perfiles en directorios especializados y redes sociales" + lista de
  `sameAs`. El orden importa: los enlaces a blog van antes que los
  perfiles.
- Cada post (`sites/src/content/posts/<slug>/<post>/{cloudflare,github,blogger}.md`)
  debe enlazar, en su CTA final, al `website` real del proyecto. El NAP+W
  y la rueda de enlaces a los otros canales/posts se añaden
  automáticamente al renderizar (ver sección de arquitectura arriba) — no
  hace falta escribirlos a mano en el markdown.

## 5. Verificación end-to-end tras cualquier cambio

```bash
# Cloudflare — cada subdominio debe mostrar su propio contenido
curl -s https://easyseo.easyleads.es/ | grep -o '<h1[^>]*>[^<]*</h1>'

# GitHub Pages
curl -I https://gh.easyleads.es/

# Blogger — el enlace debe ser un <a href> real, no texto markdown
curl -s <url-del-post> | grep -o '<a href="[^"]*">[^<]*</a>'

# CI
gh run list -R <owner>/<repo> -L 1
gh run view <run-id> -R <owner>/<repo>
```
