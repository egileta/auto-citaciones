# Despliegue de los 4 canales — runbook

Este documento describe cómo está montada la infraestructura de los cuatro
canales de publicación (Cloudflare Pages, GitHub Pages, Blogger, Tumblr) y
los pasos exactos para reproducirla desde cero. Incluye, al final, los
errores reales con los que nos topamos la primera vez y su causa, para no
repetirlos.

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
- **Tumblr**: tampoco usa el build de Astro, mismo patrón que Blogger.
  `scripts/tumblr_publish.py` lee los `*/*/tumblr.md` y los publica vía API
  (OAuth 1.0a, endpoint legacy `/v2/blog/{blog}/post`). Limitación conocida:
  las URLs de Tumblr incluyen el ID numérico del post
  (`https://<blog>/post/<id>`), no hay endpoint para asignar un slug legible.

**URLs de posts:** en los tres canales un post vive en
`<base>/<post-slug>/` (p.ej. `https://easyseo.easyleads.es/01-post/`,
`https://gh.easyleads.es/easyseo/01-post/`) — sin `/blog/` ni doble
prefijo del slug del proyecto.

**Rueda de enlaces (link wheel), con título real como anchor text:** cada
post, en los cuatro canales, incluye tras su contenido los datos NAP+W del
negocio y enlaces a las versiones del mismo post en los otros canales
(`sites/src/lib/linkWheel.ts` → `buildPostLinkWheel()`, usada por
`Post.astro`, excluye el canal actual; `build_link_wheel_html()` en
`scripts/blogger_publish.py` y en `scripts/tumblr_publish.py` para Blogger y
Tumblr respectivamente). La clave es que el texto del enlace **nunca** es
una etiqueta de plataforma ("Versión en Cloudflare Pages") ni el mismo
título con un sufijo ("Título (GitHub)") — es el **título real de esa
versión concreta**, que se escribe deliberadamente distinto en cada
`cloudflare.md`/`github.md`/`blogger.md`/`tumblr.md` del mismo post. Varias
copias casi idénticas de un artículo enlazándose entre sí con el mismo
anchor text es la firma de un link scheme; con un título propio y distinto
por versión, el enlace se lee como una referencia editorial normal, no como
una red de enlaces.

La página raíz de cada proyecto (`sites/src/pages/[slug]/index.astro`)
usa en cambio `buildAllChannelLinks()`: solo lista los posts **propios de
ese proyecto** (nunca los de otros proyectos), cada uno repetido en sus
cuatro variantes de canal con su título real — no excluye el canal actual,
porque esta página no "es" ninguno de los cuatro en particular. Por cada
post nuevo que se añada a un proyecto, aparecerán hasta 4 enlaces más en
su página raíz (menos los que aún no estén publicados en Blogger/Tumblr).

El enlace a la versión de Blogger (o de Tumblr) solo aparece una vez que el
post ya se publicó allí y quedó registrado en `data/blogger_published.json`
(o `data/tumblr_published.json`) — `sites/src/lib/blogPublished.ts` y
`sites/src/lib/tumblrPublished.ts` leen esos ficheros en tiempo de build.
En `.github/workflows/deploy.yml`, los jobs `deploy-cloudflare` y
`deploy-github` dependen de (`needs:`) `blogger-publish` y `tumblr-publish`,
y hacen `checkout` explícito de `ref: main` (en vez del SHA que disparó el
workflow), de forma que si esos jobs publicaron el post y
`git-auto-commit-action` ya actualizó el fichero de tracking en `main`, el
build recoge ese commit antes de generar las páginas: el enlace aparece
**desde el primer despliegue**, sin esperar a un segundo push. `if: always()`
en esos dos jobs evita que un fallo de la API de Blogger o de Tumblr
bloquee el despliegue de los sitios estáticos.

Cada post tiene **cuatro ficheros markdown distintos**
(`cloudflare.md`, `github.md`, `blogger.md`, `tumblr.md`) con **título y
redacción distintos** en cada uno, para evitar contenido duplicado entre
canales (penalización SEO) y para que la rueda de enlaces tenga un anchor
text real y variado en vez de uno genérico.

En `scripts/blogger_publish.py` y `scripts/tumblr_publish.py`,
`read_channel_title()` lee el `title` de los ficheros hermanos del que se
está publicando — por eso el hash de contenido (`find_blogger_posts()` /
`find_tumblr_posts()`) incluye también esos títulos, no solo el texto del
propio fichero: si cambias solo el título de `cloudflare.md`, el post de
Blogger y el de Tumblr deben republicarse igualmente para actualizar el
enlace. `blogger_publish.py` y `tumblr_publish.py` también se leen el
`_published.json` del otro canal para enlazarse entre sí una vez ambos
estén publicados.

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
mínimo: soporta párrafos separados por línea en blanco, listas no
ordenadas (líneas que empiezan por `- ` o `* `), `![alt](url)` →
`<img>`, `[texto](url)` → `<a href>`, y `**negrita**`/`*cursiva*` (estos
últimos también dentro de los `<li>`). No soporta encabezados ni markdown
anidado (listas dentro de listas, etc.) — si se necesita más, ampliar
`block_to_html`/`inline_markdown_to_html`.

### 3.6 Reintentos en `submit_indexnow.py`

El job `submit-indexnow` (al final del workflow) llama a la API pública de
IndexNow, que ha fallado alguna vez en CI con un error de conexión
transitorio (`ConnectionError`/`RemoteDisconnected`, no un error HTTP).
`submit_host()` reintenta con backoff exponencial (1s, 2s, 4s... hasta
`max_attempts=5`) tanto en errores de conexión (`requests.exceptions.
RequestException`) como en respuestas HTTP 429/500/502/503. Si se agotan
los reintentos, `main()` captura el fallo, imprime un `WARNING` en stderr
y termina con código 0 — un fallo de IndexNow nunca debe marcar el deploy
como roto, porque no afecta a que los sitios estén publicados y
accesibles.

## 4. Tumblr

### 4.0 Crear el blog (manual, una sola vez)

Igual que con Blogger, **la API de Tumblr no crea blogs** — hay que crear
el blog a mano una vez desde la interfaz antes de automatizar nada:

1. Si no hay cuenta de Tumblr, crearla en <https://www.tumblr.com/register>.
2. Dentro de la cuenta, crear un blog nuevo (menú de cuenta → "Crear un
   nuevo blog" / icono "+"). El nombre elegido fija el hostname
   (`<nombre>.tumblr.com`) — si el nombre obvio ya está cogido, probar
   variantes (`easyleadses`, `easyleads-es`, etc.). Ese hostname completo
   es el valor de `TUMBLR_BLOG_IDENTIFIER` (sección 4.2).
3. No hace falta configurar tema, título ni nada más del blog — solo que
   exista, para que la API pueda publicar posts en él.

### 4.1 Registrar la app y obtener credenciales OAuth 1.0a

1. Crear una app en <https://www.tumblr.com/oauth/apps> — da un
   **Consumer Key** y un **Consumer Secret**.
2. Tumblr usa OAuth 1.0a para publicar en nombre de un usuario (no hay
   endpoint de creación de posts en OAuth2). El registro de la app incluye
   un "Explore API" que permite generar directamente un **OAuth Token** y
   **OAuth Token Secret** para tu propia cuenta sin implementar el
   three-legged handshake completo — es el atajo recomendado para un blog
   propio (equivalente al flujo manual que ya se usa para el refresh token
   de Blogger).
3. El blog de destino se identifica por su hostname completo, p.ej.
   `easyleads.tumblr.com` (o el dominio personalizado si el blog tiene uno
   configurado) — el mismo que se creó en el paso 4.0.

### 4.2 Secrets de GitHub

- `TUMBLR_BLOG_IDENTIFIER`
- `TUMBLR_CONSUMER_KEY`
- `TUMBLR_CONSUMER_SECRET`
- `TUMBLR_OAUTH_TOKEN`
- `TUMBLR_OAUTH_TOKEN_SECRET`

### 4.3 Mismo punto crítico que Blogger: permiso de escritura para el tracking file

`scripts/tumblr_publish.py` guarda en `data/tumblr_published.json` qué
posts ya se publicaron (por `content_hash`), igual que
`blogger_publish.py`. El job `tumblr-publish` necesita:

```yaml
tumblr-publish:
  permissions:
    contents: write
```

Si este push falla, Tumblr ya habrá publicado los posts pero el tracking
file seguirá vacío, y el siguiente run los duplicará — mismo procedimiento
de recuperación que en 3.4, pero contra la API de Tumblr
(`GET /v2/blog/{blog}/posts` para localizar duplicados,
`POST /v2/blog/{blog}/post/delete` con el `id` para borrarlos).

### 4.4 Endpoint legacy, no NPF

`tumblr_publish.py` usa el endpoint legacy `type=text` (`POST
/v2/blog/{blog}/post` para crear, `POST /v2/blog/{blog}/post/edit` para
editar), no el formato NPF (Neue Post Format) más reciente — sigue soportado
y es más simple para contenido puramente HTML como el que generan
`markdown_to_html()`/`build_nap_html()`/`build_link_wheel_html()`. La
respuesta de creación solo trae el `id` numérico del post, no una URL
completa; la URL se construye como `https://<blog_identifier>/post/<id>`.

## 5. Convención de contenido (los 4 canales)

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
  entradas en nuestro blog" + lista de enlaces **solo a los posts de este
  proyecto**, fanned out en sus 4 canales (propio, GitHub, Blogger, Tumblr)
  con el título real de cada versión, y **después** h3 "Nuestros perfiles
  en directorios especializados y redes sociales" + lista de `sameAs`. El
  orden importa: los enlaces a blog van antes que los perfiles.
- Cada post (`sites/src/content/posts/<slug>/<post>/{cloudflare,github,blogger,tumblr}.md`)
  debe enlazar, en su CTA final, al `website` real del proyecto. El NAP+W
  y la rueda de enlaces a los otros canales se añaden automáticamente al
  renderizar (ver sección de arquitectura arriba) — no hace falta
  escribirlos a mano en el markdown.

## 6. Verificación end-to-end tras cualquier cambio

```bash
# Cloudflare — cada subdominio debe mostrar su propio contenido
curl -s https://easyseo.easyleads.es/ | grep -o '<h1[^>]*>[^<]*</h1>'

# GitHub Pages
curl -I https://gh.easyleads.es/

# Blogger — el enlace debe ser un <a href> real, no texto markdown
curl -s <url-del-post> | grep -o '<a href="[^"]*">[^<]*</a>'

# Tumblr — mismo chequeo
curl -s <url-del-post-en-tumblr> | grep -o '<a href="[^"]*">[^<]*</a>'

# CI
gh run list -R <owner>/<repo> -L 1
gh run view <run-id> -R <owner>/<repo>
```
