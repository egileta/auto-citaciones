# Proyecto: Sistema de citaciones e indexación multi-canal

> Este archivo es el contexto del proyecto para Claude Code. Describe la
> arquitectura, las decisiones tomadas, las restricciones y el plan de
> construcción. Guardar como `CLAUDE.md` en la raíz del repo.

## Objetivo

Publicar **páginas de citación por proyecto** (mención de entidad/marca con
NAP consistente y datos estructurados) en varios canales, más algunos **posts
de apoyo** que ayuden a que esas citaciones se indexen. El hub principal es un
dominio propio en Cloudflare; GitHub Pages y Blogger son canales secundarios.

El objetivo NO es renting de autoridad ni parasite SEO (Google desacopla la
autoridad de subdominios/secciones desde la actualización de agosto 2025, así
que esa táctica ya no funciona). El objetivo es **citaciones indexables y
consistentes** que refuercen la entidad.

## Principios de diseño (no negociables)

1. **Una cuenta por plataforma**, usada con normalidad. Nada de redes de
   cuentas títere: se detectan en clúster y se caen en bloque, y además no
   aportan valor SEO.
2. **Sustancia mínima única por página.** Nada de plantilla idéntica rellenada
   en masa: eso dispara los filtros de scaled content y se desindexa.
3. **NAP consistente** carácter por carácter en todos los canales
   (Name, Address, Phone).
4. **Datos estructurados** (JSON-LD) en cada página de citación.
5. Los subdominios sirven para **organizar** (por proyecto), no para
   multiplicar autoridad. Subdominios del mismo raíz comparten señal.

## Arquitectura

```
                    tudominio.com (hub, Cloudflare Pages)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  proyecto1.tudominio.com │          gh.tudominio.com ──CNAME──> usuario.github.io
  proyecto2.tudominio.com │
   (Cloudflare DNS/API)   │
                          │
                   blog en Blogger
              (creado a mano una vez;
               entradas vía API v3)
```

### Canal 1 — Cloudflare (hub principal)
- Proyecto Cloudflare Pages ya existente; conectar al dominio real vía
  **Custom domains** en el proyecto (crea el DNS automáticamente si el dominio
  está en Cloudflare).
- Subdominios de proyecto: crear registros DNS vía **Cloudflare API**
  (`POST /zones/{zone_id}/dns_records`) o un wildcard `*.tudominio.com`
  enrutado por Worker. Empezar con registros individuales.
- Contenido generado con un **static site generator** (Astro o Eleventy:
  HTML limpio y rápido, bueno para indexación).

### Canal 2 — GitHub Pages
- Una cuenta, un repo de Pages. Sitio en `usuario.github.io`.
- Para exponerlo como subdominio de marca: archivo `CNAME` en el repo con
  `gh.tudominio.com` + registro CNAME en Cloudflare apuntando a
  `usuario.github.io`.
- Despliegue vía GitHub Actions en push.

### Canal 3 — Blogger
- **La API v3 NO crea blogs.** Crear el blog UNA vez a mano en la interfaz.
- Después, automatizar entradas con la API:
  - OAuth 2.0, scope `https://www.googleapis.com/auth/blogger`
  - `users.self.blogs` → obtener `blogId`
  - `posts.insert` → crear/publicar (status=live) o borrador
  - Manejar cuota con backoff exponencial.

## Plantilla de página de citación

Cada página de citación debe incluir:
- Encabezado con nombre de la entidad.
- 1–3 párrafos de descripción **única y real** (no plantilla).
- Bloque NAP visible y consistente.
- Enlace a la web oficial / hub.
- JSON-LD de entidad. Ejemplo base (`Organization`; usar `LocalBusiness` si
  aplica negocio físico):

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "NOMBRE EXACTO",
  "url": "https://tudominio.com",
  "telephone": "+34 ...",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "...",
    "addressLocality": "...",
    "postalCode": "...",
    "addressCountry": "ES"
  },
  "sameAs": [
    "https://www.linkedin.com/company/...",
    "https://gh.tudominio.com",
    "https://elblog.blogspot.com"
  ]
}
```

`sameAs` cruza todas las menciones de la misma entidad: es lo que une los
canales en el grafo de conocimiento.

## Posts de apoyo

Por proyecto, 1–3 posts con contenido real que aporte algo (no relleno) y que
enlacen de forma natural a la página de citación. Sirven para dar contexto y
ayudar al rastreo.

## Indexación

- `sitemap.xml` por propiedad (o un índice que apunte a los demás).
- Verificar cada propiedad en **Google Search Console**; usar inspección de
  URL → "Solicitar indexación" para URLs clave.
- Activar **IndexNow** (Cloudflare lo integra nativo; lo usan Bing/Yandex)
  para ping automático al publicar.
- La indexación fiable = sustancia + sitemap limpio + envío activo.
  El volumen de hosts NO ayuda.

## Stack técnico propuesto

- **SSG:** Astro (o Eleventy).
- **Hosting hub:** Cloudflare Pages.
- **Infra/DNS:** Cloudflare API.
- **Blogger:** API v3 (cliente Python o Node).
- **Orquestación:** GitHub Actions o cron en el VPS Contabo.
- **Generación de texto (opcional):** Anthropic API.

## Secretos / credenciales necesarios

(Guardar en `.env` local y en GitHub Actions secrets — nunca en el repo.)

- `CLOUDFLARE_API_TOKEN` (scope: editar DNS de la zona)
- `CLOUDFLARE_ZONE_ID`
- `CLOUDFLARE_ACCOUNT_ID`
- `BLOGGER_OAUTH_CLIENT_ID` / `BLOGGER_OAUTH_CLIENT_SECRET` / refresh token
- `ANTHROPIC_API_KEY` (si se genera texto)
- GitHub: token con permiso sobre el repo de Pages

## Estructura de repo propuesta

```
/
├── CLAUDE.md                 # este archivo
├── .env.example
├── sites/                    # SSG (Astro/Eleventy)
│   ├── src/
│   │   ├── data/projects.json     # fuente de verdad por proyecto (NAP, etc.)
│   │   ├── templates/citation.astro
│   │   └── templates/post.astro
│   └── ...
├── scripts/
│   ├── cf_create_subdomain.py     # crea registro DNS vía Cloudflare API
│   ├── blogger_publish.py         # publica entrada vía Blogger API v3
│   └── submit_indexnow.py         # ping IndexNow
├── .github/workflows/
│   └── deploy.yml                 # build + deploy en push
└── README.md
```

## Plan de tareas (orden sugerido para Claude Code)

1. Inicializar el SSG (Astro) con `projects.json` como fuente de verdad
   (un objeto por proyecto: nombre, NAP, descripción, sameAs).
2. Plantilla `citation` que renderice la página + JSON-LD desde cada proyecto.
3. Plantilla `post` para los posts de apoyo.
4. Generación de `sitemap.xml`.
5. `scripts/cf_create_subdomain.py`: crea el registro DNS del subdominio del
   proyecto vía Cloudflare API (idempotente: no duplicar si existe).
6. GitHub Action `deploy.yml`: build + deploy a Cloudflare Pages en push.
7. `scripts/blogger_publish.py`: dado un proyecto, publica su entrada de
   citación en Blogger (OAuth + posts.insert).
8. `scripts/submit_indexnow.py`: ping de las URLs nuevas/actualizadas.
9. Documentar en README el alta manual única: crear el blog de Blogger,
   verificar propiedades en Search Console, configurar el CNAME de GitHub.

## Pasos manuales (una sola vez, fuera de la automatización)

- Crear el blog en Blogger desde la interfaz.
- Autorizar OAuth de Blogger y guardar el refresh token.
- Conectar el dominio real al proyecto Cloudflare Pages (Custom domains).
- Crear el repo de GitHub Pages y su archivo `CNAME`.
- Verificar todas las propiedades en Google Search Console.
