# Cómo escribir un post — patrón a seguir

Esta guía es para cuando se añade un post nuevo o se reescribe uno
existente. El "por qué" de la arquitectura (rutas, canales, despliegue)
está en [`DEPLOYMENT.md`](DEPLOYMENT.md); esto es solo el "cómo escribir
el contenido" para que cada iteración futura siga el mismo patrón.

## Estructura de ficheros

Cada post vive en `sites/src/content/posts/<project>/<NN-slug>/` con
**tres ficheros**: `cloudflare.md`, `github.md`, `blogger.md`. Los tres
comparten tema y frontmatter (`date`, `project`), pero **nunca** comparten
título ni redacción — ver más abajo por qué.

```yaml
---
title: "..."
date: "2026-06-20"
project: "easyseo"
---
```

## El título debe variar por canal, no solo el cuerpo

Los tres ficheros de un mismo post se enlazan entre sí automáticamente
(ver "Rueda de enlaces" abajo): la página de cada canal enlaza a las
otras dos versiones, y la página de citación del proyecto las lista las
tres. El **anchor text de esos enlaces es el `title` real de cada
fichero** — por eso cada canal necesita un título propio y distinto, no
una variación cosmética del mismo título. Si los tres títulos fueran
iguales (o solo cambiase el cuerpo), los enlaces leerían igual entre sí,
que es justo la señal de "link scheme" que se quiere evitar.

Ejemplo real (mismo post, mismo tema, tres títulos distintos):

| Canal | Título |
|---|---|
| Cloudflare | "Cuándo merece la pena reparar tu ordenador en vez de comprar uno nuevo" |
| GitHub | "Las dos averías que explican casi todos los ordenadores lentos" |
| Blogger | "¿Reparar o comprar otro? Esto es lo primero que hay que mirar" |

Cada título refleja un ángulo distinto del mismo tema (la pregunta
genérica, la causa técnica, la duda conversacional) — no son sinónimos
del mismo título.

## El cuerpo

- **Largo y con sustancia**: ~300-450 palabras, no 3-4 frases. Un gancho
  humanizado al principio, no una definición de manual.
- **Una frase de transición en negrita** a modo de entradilla antes de la
  lista (sustituye a un subtítulo — Blogger no soporta encabezados, ver
  más abajo).
- **Una lista de 3-5 puntos concretos**, con los términos clave en
  negrita (`**así**`).
- **Una imagen de stock relevante** (ver sección siguiente).
- **Cierre con CTA** enlazando siempre a la web real del negocio
  (`https://easyseo.es`, `https://newcombilbao.es`, `https://arrobapc.es`
  — nunca a un subdominio `*.easyleads.es` ni a `gh.easyleads.es`, esos
  son solo el hosting de la citación).
- Cada uno de los tres ficheros debe tener **ángulo y estructura
  ligeramente distintos** (no solo sinónimos) — mismo objetivo que con
  los títulos: evitar contenido duplicado entre canales.

No hace falta escribir a mano el bloque NAP+web ni la rueda de enlaces:
se añaden automáticamente al renderizar/publicar.

## Markdown soportado — y sus límites

El cuerpo se renderiza con dos motores distintos, y **el más limitado de
los dos manda**:

- **Cloudflare/GitHub** (`sites/`): markdown completo de Astro.
- **Blogger** (`scripts/blogger_publish.py` → `markdown_to_html()`):
  conversor propio, deliberadamente mínimo. Soporta:
  - párrafos separados por línea en blanco,
  - listas no ordenadas (`- ` o `* `, incluso si el ítem ocupa varias
    líneas de fichero),
  - `![alt](url)` → `<img>`,
  - `[texto](url)` → `<a>`,
  - `**negrita**` / `*cursiva*`.
  - **No soporta encabezados** (`#`, `##`...) — si se usan, salen como
    texto plano literal en Blogger. Por eso esta guía usa negrita como
    sustituto de subtítulo, nunca `##`.

Para mantener los tres ficheros visualmente coherentes entre canales, se
escribe **todo** el contenido (cloudflare/github/blogger) usando solo el
subconjunto que soporta Blogger, aunque Astro pueda más.

## Imágenes de stock

Se usan fotos de Unsplash vía URL directa
(`https://images.unsplash.com/photo-XXXXXXXXXXXXX-XXXXXXXXXXXX?w=1200&q=80`).

**Antes de usar una URL, compruébala** — no todos los IDs que parecen
plausibles existen:

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" "https://images.unsplash.com/photo-XXXX...?w=1200&q=80"
# debe dar: 200 image/jpeg
```

Usa una imagen **distinta por canal** dentro del mismo post (no la misma
imagen repetida 3 veces), igual que con el título: ayuda a diferenciar
las tres versiones.

## Rueda de enlaces (automática, no tocar a mano)

- `sites/src/lib/linkWheel.ts` (Astro) y `read_channel_title()` /
  `build_link_wheel_html()` en `scripts/blogger_publish.py` (Blogger)
  leen el `title` real de los ficheros hermanos del mismo post y lo usan
  como anchor text.
- El enlace a la versión de Blogger solo aparece una vez que
  `scripts/blogger_publish.py` lo haya publicado y registrado en
  `data/blogger_published.json` — no antes.
- Si cambias solo el `title` de un fichero (sin tocar el cuerpo), el hash
  de contenido en `find_blogger_posts()` lo detecta igual (incluye los
  títulos de los ficheros hermanos) y se vuelve a publicar en Blogger
  para que el enlace se actualice.

## Antes de dar por terminado un post nuevo

```bash
cd sites && npm test              # vitest
cd ../scripts && python3 -m pytest -q  # pytest

# build real para detectar errores que los tests no cubren
cd ../sites
SITE_TARGET=cloudflare npm run build
SITE_TARGET=github npm run build
```

Y revisa a mano el HTML generado en `dist/` (o, tras desplegar, la URL en
vivo) para confirmar que la rueda de enlaces usa títulos reales y no una
etiqueta de plataforma repetida.
