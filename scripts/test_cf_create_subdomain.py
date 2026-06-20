import unittest
from unittest.mock import patch, MagicMock

from cf_create_subdomain import sync_subdomains


class SyncSubdomainsTest(unittest.TestCase):
    @patch("cf_create_subdomain.requests.post")
    @patch("cf_create_subdomain.requests.get")
    def test_creates_missing_subdomain_and_skips_existing(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(json=lambda: {"result": [{"name": "newcom.easyleads.es"}]})
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value = MagicMock(json=lambda: {"result": {}})
        mock_post.return_value.raise_for_status = lambda: None

        projects = [
            {"subdomain": "easyseo.easyleads.es"},
            {"subdomain": "newcom.easyleads.es"},
        ]

        created = sync_subdomains("acc", "proj", "token", projects)

        self.assertEqual(created, ["easyseo.easyleads.es"])
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
