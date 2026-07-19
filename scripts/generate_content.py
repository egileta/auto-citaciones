#!/usr/bin/env python3
"""Generates long-form (600-1200 word) post variants per channel using the
Claude API, humanized with the rules from the 'stop-slop' skill
(https://github.com/hardikpandya/stop-slop), and writes them to disk for
manual review before commit. Does not publish anything itself.

Usage:
    python scripts/generate_content.py <project_slug> <post_slug> "<tema>" \
        [--channels cloudflare,github,blogger,tumblr] [--force]
"""
import argparse
import json
import sys
from pathlib import Path

from anthropic import Anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_ROOT = REPO_ROOT / "sites" / "src" / "content" / "posts"
PROJECTS_PATH = REPO_ROOT / "sites" / "src" / "data" / "projects.json"

DEFAULT_MODEL = "claude-opus-4-8"
MIN_WORDS = 600
MAX_WORDS = 1200

CHANNELS = ("cloudflare", "github", "blogger", "tumblr")

# One distinct rhetorical angle per channel so the four variants never read
# like copies of each other (see docs/CONTENT.md: same topic, distinct
# título/redacción por canal).
CHANNEL_ANGLES = {
    "cloudflare": "guía práctica tipo checklist: qué hacer, paso a paso o punto a punto",
    "github": "explicación de la causa técnica de fondo: por qué ocurre el problema, no solo qué hacer",
    "blogger": "tono conversacional, como si respondieras la duda real de un cliente en la tienda",
    "tumblr": "enfoque de coste/valor: qué se pierde o se gana económicamente por no actuar",
}

STOP_SLOP_RULES = """\
Reglas de estilo (basadas en la skill "stop-slop" para eliminar patrones de escritura de IA):

1. Sin muletillas de apertura ("Aquí tienes", "La verdad es que", "Resulta que"). Ve directo al punto.
2. Sin voz pasiva. Cada frase necesita un sujeto humano haciendo algo.
3. Sin contrastes binarios formulaicos ("No es X, es Y" / "No se trata de X sino de Y"). Afirma Y directamente.
4. Sin adverbios en -mente. Sin intensificadores vacíos ("realmente", "simplemente", "de hecho").
5. Sé específico. Nada de "los motivos son estructurales" sin decir cuáles. Nombra la cosa concreta.
6. Varía el ritmo de las frases. Dos frases de la misma longitud seguidas, rómpelas.
7. Nunca uses guiones largos (—) para conectar ideas dentro de una frase.
8. Nada de listas de tres elementos por sistema — dos o cuatro también valen.
9. Nada de cierres tipo "Y eso es todo lo que necesitas saber" ni frases de efecto forzadas.
10. Confía en el lector: afirma los hechos directamente, sin "cabe destacar que" ni "es importante mencionar".
"""

HOUSE_STYLE = """\
Patrón de la casa para posts de apoyo SEO local (ver docs/CONTENT.md):
- {min_words}-{max_words} palabras, con sustancia real (casos concretos, cifras, ejemplos del negocio), no relleno.
- Markdown limitado: párrafos separados por línea en blanco, listas con "- ", **negrita**, *cursiva*, [enlace](url), ![alt](url).
  NO uses encabezados (#, ##) — no se renderizan en Blogger ni Tumblr. Usa una frase en negrita como entradilla antes de una lista, a modo de subtítulo.
- Incluye una lista de 3-5 puntos concretos con los términos clave en negrita.
- Cierra con una llamada a la acción que enlace a la web real del negocio (nunca a un subdominio de easyleads.es).
- El NAP (nombre, dirección, teléfono) y la rueda de enlaces a otros canales se añaden automáticamente al publicar — no los escribas.
"""


def load_projects():
    projects = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    return {project["slug"]: project for project in projects}


def build_system_prompt(project, channel):
    angle = CHANNEL_ANGLES[channel]
    return (
        f"Escribes contenido de apoyo SEO local en español para negocios reales, "
        f"canal '{channel}'.\n\n"
        f"Negocio: {project['name']}\n"
        f"Descripción: {project['description']}\n"
        f"Web real: {project['website']}\n"
        f"Zona: {project['nap']['addressLocality']}\n\n"
        f"Ángulo de este canal: {angle}\n\n"
        f"{HOUSE_STYLE.format(min_words=MIN_WORDS, max_words=MAX_WORDS)}\n"
        f"{STOP_SLOP_RULES}\n"
        "Responde únicamente en el formato JSON solicitado."
    )


DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Título del post, distinto y específico de este canal"},
        "body_markdown": {"type": "string", "description": "Cuerpo del post en el subconjunto de markdown soportado"},
    },
    "required": ["title", "body_markdown"],
    "additionalProperties": False,
}

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "directness": {"type": "integer"},
        "rhythm": {"type": "integer"},
        "trust": {"type": "integer"},
        "authenticity": {"type": "integer"},
        "density": {"type": "integer"},
        "revised_body_markdown": {
            "type": ["string", "null"],
            "description": "Versión revisada del cuerpo si la puntuación total es menor a 35; null si no hace falta revisar",
        },
    },
    "required": ["directness", "rhythm", "trust", "authenticity", "density", "revised_body_markdown"],
    "additionalProperties": False,
}


def generate_draft(client, project, channel, topic, model=DEFAULT_MODEL):
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=build_system_prompt(project, channel),
        output_config={"format": {"type": "json_schema", "schema": DRAFT_SCHEMA}},
        messages=[{"role": "user", "content": f"Tema del post: {topic}"}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def score_and_revise(client, draft, model=DEFAULT_MODEL):
    prompt = (
        f"{STOP_SLOP_RULES}\n\n"
        "Puntúa este texto de 1 a 10 en cada dimensión (directness, rhythm, trust, "
        "authenticity, density) según las reglas de arriba. Si la suma es menor a 35/50, "
        "reescribe el cuerpo en 'revised_body_markdown' corrigiendo los problemas detectados. "
        "Si es 35 o más, deja 'revised_body_markdown' en null.\n\n"
        f"TEXTO:\n{draft['body_markdown']}"
    )
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        output_config={"format": {"type": "json_schema", "schema": SCORE_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    result = json.loads(text)
    total = result["directness"] + result["rhythm"] + result["trust"] + result["authenticity"] + result["density"]
    final_body = result["revised_body_markdown"] if total < 35 and result["revised_body_markdown"] else draft["body_markdown"]
    return total, final_body


def write_post_file(project_slug, post_slug, channel, title, date, body, force=False):
    post_dir = POSTS_ROOT / project_slug / post_slug
    post_dir.mkdir(parents=True, exist_ok=True)
    path = post_dir / f"{channel}.md"
    if path.exists() and not force:
        print(f"SKIP (ya existe, usa --force para sobrescribir): {path}")
        return None
    frontmatter = f'---\ntitle: "{title}"\ndate: "{date}"\nproject: "{project_slug}"\n---\n\n'
    path.write_text(frontmatter + body.strip() + "\n", encoding="utf-8")
    return path


def generate_channel(client, project, project_slug, post_slug, channel, topic, date, force, model=DEFAULT_MODEL):
    draft = generate_draft(client, project, channel, topic, model=model)
    score, body = score_and_revise(client, draft, model=model)
    path = write_post_file(project_slug, post_slug, channel, draft["title"], date, body, force=force)
    if path:
        word_count = len(body.split())
        print(f"WROTE ({score}/50, {word_count} palabras): {path}")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_slug")
    parser.add_argument("post_slug", help='p.ej. "02-nueva-tematica"')
    parser.add_argument("topic", help="Breve descripción del tema del post")
    parser.add_argument("--channels", default=",".join(CHANNELS))
    parser.add_argument("--date", default=None, help="YYYY-MM-DD, por defecto hoy")
    parser.add_argument("--force", action="store_true", help="Sobrescribe ficheros existentes")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args(argv)

    import datetime

    date = args.date or datetime.date.today().isoformat()
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    projects = load_projects()
    if args.project_slug not in projects:
        print(f"ERROR: proyecto desconocido '{args.project_slug}'", file=sys.stderr)
        sys.exit(1)
    project = projects[args.project_slug]

    client = Anthropic()
    for channel in channels:
        generate_channel(
            client, project, args.project_slug, args.post_slug, channel, args.topic, date, args.force, model=args.model
        )

    print("\nRevisa el contenido generado con `git diff` antes de hacer commit.")


if __name__ == "__main__":
    main()
