# Bitácora del proyecto

Registro vivo de cómo ha evolucionado el sistema de citaciones: mapa de
dominios/subdominios, mecánica de la rueda de enlaces, cómo se agregan los
sitemaps vía `robots.txt`, y un histórico fechado de altas de proyectos y
cambios relevantes.

> Actualizar este archivo (nueva entrada en el log al final) cada vez que se
> añada un proyecto, se complete/corrija su `sameAs`, o cambie algún
> mecanismo de la rueda de enlaces o del sitemap/robots.

## Mapa de dominios

- **Hub (apex):** `easyleads.es` — repo privado **separado**
  `egileta/easy-leads` (Astro, se despliega vía la integración nativa de
  Cloudflare Pages con git, no por la CI de este repo). Su
  `public/robots.txt` está **mantenido a mano**, no se genera desde
  `sites/src/data/projects.json` — ver `docs/DEPLOYMENT.md`.
- **Canal 1 — Cloudflare, por proyecto:** `<slug>.easyleads.es` (DNS CNAME +
  Pages custom domain, creados por `scripts/cf_create_subdomain.py`,
  idempotente).
- **Canal 2 — GitHub Pages, compartido:** `gh.easyleads.es`, rutas
  `gh.easyleads.es/<slug>/`.
- **Canal 3 — Blogger, compartido:** `blogger.easyleads.es`.
- **Canal 4 — Tumblr, compartido:** `easyleadsblog.tumblr.com`.
- Cada proyecto tiene además su **web de negocio real** (`website` en
  `projects.json`), que es el ancla NAP definitiva, no generada por este
  pipeline.

## Mecánica de la rueda de enlaces (fix 2026-08-27)

En la página de citación raíz de cada proyecto
(`sites/src/pages/[slug]/index.astro` → `sites/src/templates/Citation.astro`)
hay dos bloques de enlaces con propósitos distintos:

- **"Últimas entradas"** = solo el/los post(s) de apoyo de **este** canal
  (`buildOwnChannelLinks` en `sites/src/lib/linkWheel.ts`). Cada canal
  muestra aquí únicamente su propia copia del post.
- **"Perfiles en directorios..."** = el resto de la rueda: el otro target
  SSG + Blogger + Tumblr (`buildPostLinkWheel`), concatenado con
  `project.sameAs` (perfiles externos reales). Es el prop `directoryLinks`,
  construido en `index.astro` y renderizado por `Citation.astro`.

Antes del fix, "Últimas entradas" usaba `buildAllChannelLinks` (los 4
canales de cada post mezclados) y "Perfiles" solo mostraba `sameAs` — un
proyecto con `sameAs` vacío (como amalau) parecía no tener ningún perfil de
directorio en las páginas raíz, aunque las páginas de post individuales
(que ya usaban `buildPostLinkWheel`) estaban correctas. Ver commit
`8889c8d`.

## Agregación de sitemaps vía robots.txt

**No existe un único sitemap-de-sitemaps** que liste todos los subdominios
de proyecto. El punto de agregación es `https://easyleads.es/robots.txt`
(mantenido a mano en el repo `easy-leads`), que lista una línea `Sitemap:`
por canal:

```
Sitemap: https://easyleads.es/sitemap-index.xml   ← solo páginas propias del hub
Sitemap: https://<slug>.easyleads.es/sitemap.xml  ← una por proyecto
Sitemap: https://gh.easyleads.es/sitemap.xml
Sitemap: https://blogger.easyleads.es/sitemap.xml
Sitemap: https://easyleadsblog.tumblr.com/sitemap.xml
```

`easyleads.es/sitemap-index.xml` es el sitemap autogenerado por Astro **solo
del hub** (home + posts del blog del propio hub) — no agrega los
subdominios de proyecto. Verificado en vivo el 2026-08-27 con `curl`.

**Cómo aplicar:** al añadir un proyecto nuevo, su línea `Sitemap:` debe
añadirse a mano en `easy-leads/public/robots.txt` (repo y push aparte) — la
CI de este repo nunca lo toca.

## Registro de proyectos (estado a 2026-08-27)

| slug | website | sameAs | teléfono | notas |
|---|---|---|---|---|
| easyseo | easyseo.es | 9 | ✓ | primer proyecto, citación de la propia agencia |
| newcom | newcombilbao.es | 3 | ✓ | |
| arroba | arrobapc.es | 2 | ✓ | |
| erpopensource | opensourceerp.org | 2 | *(vacío)* | entidad tipo organización (Tryton Foundation), sin teléfono por diseño |
| fotobizkaia | xn--fotobarrea-19a.com | 1 | ✓ | |
| amalau | amalau.es | 5 | ✓ | `sameAs` añadido 2026-08-27 (TripAdvisor, Facebook, EspacioRural, ClubRural, GuiaRural); **discrepancia de teléfono** sin resolver: los directorios públicos muestran `605 77 19 33`, `projects.json` tiene `+34 695 50 19 79` — decisión del usuario 2026-08-27: mantener `695 50 19 79` (se asume línea actual/nueva) |
| pasteleriasanturtzi | pasteleriasanturtzi.com | 2 | ✓ | |

Los 7 proyectos tienen al menos un post de apoyo publicado en los 4 canales
— ver `data/blogger_published.json` y `data/tumblr_published.json` para las
URLs publicadas por post.

## Histórico de altas y cambios

- **2026-06** (`322fc80`): `projects.json` + loader inicial.
- **2026-06** (`29592df`, `ec742a9`): los enlaces NAP pasan a apuntar a las
  webs reales de negocio en vez de a los subdominios de easyleads.es; se
  introduce la rueda de enlaces cruzada entre canales.
- **2026-07-24** (`9c1c13d`): alta en lote de erpopensource, fotobizkaia y
  pasteleriasanturtzi. Mismo día se corrige el gotcha de DNS en
  `cf_create_subdomain.py` (el script solo registraba el dominio custom en
  Cloudflare Pages, no creaba el CNAME) y se detecta/corrige que
  `easy-leads/public/robots.txt` no tenía las líneas `Sitemap:` de los
  proyectos nuevos (commit `945be1f` en ese repo).
- **2026-08** (`4fa1c9f`): alta de amalau (directorio de casas rurales
  Euskadi), `sameAs` queda vacío en el momento del alta.
- **2026-08-27** (`8889c8d`): fix del reparto de secciones de la rueda de
  enlaces (ver arriba) + alta de los 5 perfiles reales de `sameAs` de
  amalau, localizados por búsqueda/verificación web en vivo (se descarta
  TopRural — ahora redirige 301 a VRBO y ya no existe como directorio
  propio; se descartan Nekatur y Ecoturismo.com — 404, listados de baja).
