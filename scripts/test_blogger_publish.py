import unittest
from unittest.mock import patch, MagicMock

from blogger_publish import parse_frontmatter, markdown_to_html, publish_posts


class ParseFrontmatterTest(unittest.TestCase):
    def test_parses_title_and_body(self):
        text = '---\ntitle: "Hola"\ndate: "2026-01-01"\nproject: "demo"\n---\nCuerpo del post.\n'
        frontmatter, body = parse_frontmatter(text)
        self.assertEqual(frontmatter["title"], "Hola")
        self.assertEqual(body, "Cuerpo del post.")


class MarkdownToHtmlTest(unittest.TestCase):
    def test_wraps_paragraphs(self):
        html = markdown_to_html("Uno.\n\nDos.")
        self.assertEqual(html, "<p>Uno.</p><p>Dos.</p>")

    def test_renders_unordered_list(self):
        html = markdown_to_html("Intro.\n\n- Uno\n- Dos\n- Tres")
        self.assertEqual(html, "<p>Intro.</p><ul><li>Uno</li><li>Dos</li><li>Tres</li></ul>")

    def test_renders_image(self):
        html = markdown_to_html("![Alt text](https://example.com/foto.jpg)")
        self.assertEqual(html, '<p><img src="https://example.com/foto.jpg" alt="Alt text" loading="lazy"></p>')

    def test_list_items_support_inline_markdown(self):
        html = markdown_to_html("- **Negrita** y [enlace](https://example.com)")
        self.assertEqual(
            html,
            '<ul><li><strong>Negrita</strong> y <a href="https://example.com">enlace</a></li></ul>',
        )

    def test_list_item_wrapped_across_lines_is_folded_into_one_item(self):
        html = markdown_to_html("- Uno que\n  sigue en la siguiente línea\n- Dos")
        self.assertEqual(html, "<ul><li>Uno que sigue en la siguiente línea</li><li>Dos</li></ul>")


class PublishPostsTest(unittest.TestCase):
    PROJECTS = {
        "easyseo": {
            "slug": "easyseo",
            "name": "Agencia Easy SEO Local Vizcaya",
            "website": "https://easyseo.example.com",
            "nap": {
                "streetAddress": "Calle Falsa 1",
                "postalCode": "48001",
                "addressLocality": "Bilbao",
                "telephone": "+34600000000",
            },
        }
    }

    def make_post(self, post_id="easyseo/01", content_hash="hash1"):
        return {
            "post_id": post_id,
            "project_slug": "easyseo",
            "post_slug": "01",
            "title": "T",
            "body_markdown": "Body",
            "content_hash": content_hash,
        }

    @patch("blogger_publish.request_with_backoff")
    def test_inserts_new_post(self, mock_request):
        mock_request.return_value = MagicMock(json=lambda: {"url": "https://blog/1", "id": "1"})
        updated = publish_posts("blogid", "token", [self.make_post()], {}, self.PROJECTS)
        self.assertIn("easyseo/01", updated)
        self.assertEqual(updated["easyseo/01"]["blogger_post_url"], "https://blog/1")

    @patch("blogger_publish.request_with_backoff")
    def test_updates_when_hash_changed(self, mock_request):
        published = {"easyseo/01": {"blogger_post_url": "u", "blogger_post_id": "1", "content_hash": "old"}}
        updated = publish_posts("blogid", "token", [self.make_post(content_hash="new")], published, self.PROJECTS)
        self.assertEqual(updated["easyseo/01"]["content_hash"], "new")
        mock_request.assert_called_once()

    @patch("blogger_publish.request_with_backoff")
    def test_skips_when_hash_unchanged(self, mock_request):
        published = {"easyseo/01": {"blogger_post_url": "u", "blogger_post_id": "1", "content_hash": "hash1"}}
        updated = publish_posts("blogid", "token", [self.make_post(content_hash="hash1")], published, self.PROJECTS)
        self.assertEqual(updated, published)
        mock_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
