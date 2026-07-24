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

    @patch("cf_create_subdomain.requests.post")
    @patch("cf_create_subdomain.requests.get")
    def test_creates_dns_record_for_new_subdomain_when_zone_given(self, mock_get, mock_post):
        # First GET is Pages domains (both already registered), second GET is
        # DNS records (only "newcom" already has one) — "easyseo" needs both
        # a Pages custom domain skip *and* a DNS record created.
        mock_get.side_effect = [
            MagicMock(
                json=lambda: {"result": [{"name": "easyseo.easyleads.es"}, {"name": "newcom.easyleads.es"}]},
                raise_for_status=lambda: None,
            ),
            MagicMock(
                json=lambda: {"result": [{"name": "newcom.easyleads.es", "content": "proj.pages.dev"}]},
                raise_for_status=lambda: None,
            ),
        ]
        mock_post.return_value = MagicMock(json=lambda: {"result": {}})
        mock_post.return_value.raise_for_status = lambda: None

        projects = [
            {"subdomain": "easyseo.easyleads.es"},
            {"subdomain": "newcom.easyleads.es"},
        ]

        created = sync_subdomains("acc", "proj", "token", projects, zone_id="zone", dns_token="dnstoken")

        self.assertEqual(created, [])  # both Pages domains already existed
        mock_post.assert_called_once_with(
            "https://api.cloudflare.com/client/v4/zones/zone/dns_records",
            headers={"Authorization": "Bearer dnstoken"},
            json={"type": "CNAME", "name": "easyseo.easyleads.es", "content": "proj.pages.dev", "proxied": True, "ttl": 1},
            timeout=30,
        )


if __name__ == "__main__":
    unittest.main()
