import unittest
from unittest.mock import patch, MagicMock

from submit_indexnow import group_urls_by_host, submit_all


class GroupUrlsByHostTest(unittest.TestCase):
    def test_groups_by_netloc(self):
        urls = [
            "https://easyleads.es/easyseo/",
            "https://easyseo.easyleads.es/",
            "https://gh.easyleads.es/easyseo/",
        ]
        groups = group_urls_by_host(urls)
        self.assertEqual(set(groups.keys()), {"easyleads.es", "easyseo.easyleads.es", "gh.easyleads.es"})


class SubmitAllTest(unittest.TestCase):
    @patch("submit_indexnow.requests.post")
    def test_submits_one_request_per_host(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = lambda: None

        urls = ["https://easyleads.es/a/", "https://gh.easyleads.es/a/"]
        results = submit_all(urls, "thekey")

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(results["easyleads.es"], 200)


if __name__ == "__main__":
    unittest.main()
