import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import generate_content
from generate_content import (
    generate_draft,
    score_and_revise,
    write_post_file,
    generate_channel,
)


def fake_response(payload):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps(payload))])


PROJECT = {
    "slug": "easyseo",
    "name": "Agencia Easy SEO Local Vizcaya",
    "description": "Servicios de agencia SEO.",
    "website": "https://easyseo.example.com",
    "nap": {"addressLocality": "Santurtzi"},
}


class GenerateDraftTest(unittest.TestCase):
    def test_parses_title_and_body_from_json_response(self):
        client = MagicMock()
        client.messages.create.return_value = fake_response(
            {"title": "Un título", "body_markdown": "Cuerpo del post."}
        )
        draft = generate_draft(client, PROJECT, "cloudflare", "tema de prueba")
        self.assertEqual(draft["title"], "Un título")
        self.assertEqual(draft["body_markdown"], "Cuerpo del post.")
        kwargs = client.messages.create.call_args.kwargs
        self.assertIn("cloudflare", kwargs["system"])
        self.assertEqual(kwargs["output_config"]["format"]["type"], "json_schema")


class ScoreAndReviseTest(unittest.TestCase):
    def test_keeps_original_when_score_is_high(self):
        client = MagicMock()
        client.messages.create.return_value = fake_response(
            {
                "directness": 8,
                "rhythm": 8,
                "trust": 8,
                "authenticity": 8,
                "density": 8,
                "revised_body_markdown": None,
            }
        )
        draft = {"body_markdown": "Texto original."}
        total, body = score_and_revise(client, draft)
        self.assertEqual(total, 40)
        self.assertEqual(body, "Texto original.")

    def test_uses_revision_when_score_is_low(self):
        client = MagicMock()
        client.messages.create.return_value = fake_response(
            {
                "directness": 3,
                "rhythm": 3,
                "trust": 3,
                "authenticity": 3,
                "density": 3,
                "revised_body_markdown": "Texto reescrito.",
            }
        )
        draft = {"body_markdown": "Texto original."}
        total, body = score_and_revise(client, draft)
        self.assertEqual(total, 15)
        self.assertEqual(body, "Texto reescrito.")


class WritePostFileTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        patcher = patch.object(generate_content, "POSTS_ROOT", Path(self.tmpdir.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmpdir.cleanup)

    def test_writes_frontmatter_and_body(self):
        path = write_post_file("easyseo", "02-tema", "cloudflare", "Título", "2026-07-19", "Cuerpo.\n")
        self.assertIsNotNone(path)
        text = path.read_text(encoding="utf-8")
        self.assertIn('title: "Título"', text)
        self.assertIn('project: "easyseo"', text)
        self.assertIn("Cuerpo.", text)

    def test_skips_existing_file_without_force(self):
        write_post_file("easyseo", "02-tema", "cloudflare", "Título", "2026-07-19", "Original.")
        path = write_post_file("easyseo", "02-tema", "cloudflare", "Otro", "2026-07-19", "Nuevo.", force=False)
        self.assertIsNone(path)
        existing = Path(self.tmpdir.name) / "easyseo" / "02-tema" / "cloudflare.md"
        self.assertIn("Original.", existing.read_text(encoding="utf-8"))

    def test_force_overwrites_existing_file(self):
        write_post_file("easyseo", "02-tema", "cloudflare", "Título", "2026-07-19", "Original.")
        path = write_post_file("easyseo", "02-tema", "cloudflare", "Otro", "2026-07-19", "Nuevo.", force=True)
        self.assertIsNotNone(path)
        self.assertIn("Nuevo.", path.read_text(encoding="utf-8"))


class GenerateChannelTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        patcher = patch.object(generate_content, "POSTS_ROOT", Path(self.tmpdir.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmpdir.cleanup)

    def test_generates_and_writes_a_channel_variant(self):
        client = MagicMock()
        client.messages.create.side_effect = [
            fake_response({"title": "Título CF", "body_markdown": "Cuerpo largo del post."}),
            fake_response(
                {
                    "directness": 9,
                    "rhythm": 9,
                    "trust": 9,
                    "authenticity": 9,
                    "density": 9,
                    "revised_body_markdown": None,
                }
            ),
        ]
        path = generate_channel(client, PROJECT, "easyseo", "02-tema", "cloudflare", "tema", "2026-07-19", False)
        self.assertIsNotNone(path)
        self.assertIn("Título CF", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
