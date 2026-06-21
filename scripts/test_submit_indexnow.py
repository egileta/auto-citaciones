import unittest
from unittest.mock import patch, MagicMock

import requests

from submit_indexnow import group_urls_by_host, submit_all, submit_host


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


class SubmitHostRetryTest(unittest.TestCase):
    @patch("submit_indexnow.time.sleep")
    @patch("submit_indexnow.requests.post")
    def test_retries_on_connection_error_then_succeeds(self, mock_post, mock_sleep):
        ok_response = MagicMock(status_code=200)
        ok_response.raise_for_status = lambda: None
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("boom"),
            ok_response,
        ]

        status = submit_host("easyleads.es", ["https://easyleads.es/a/"], "thekey")

        self.assertEqual(status, 200)
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("submit_indexnow.time.sleep")
    @patch("submit_indexnow.requests.post")
    def test_raises_after_exhausting_retries(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.exceptions.ConnectionError("boom")

        with self.assertRaises(requests.exceptions.ConnectionError):
            submit_host("easyleads.es", ["https://easyleads.es/a/"], "thekey", max_attempts=3)

        self.assertEqual(mock_post.call_count, 3)

    @patch("submit_indexnow.time.sleep")
    @patch("submit_indexnow.requests.post")
    def test_retries_on_server_error_status(self, mock_post, mock_sleep):
        server_error = MagicMock(status_code=503)
        ok_response = MagicMock(status_code=200)
        ok_response.raise_for_status = lambda: None
        mock_post.side_effect = [server_error, ok_response]

        status = submit_host("easyleads.es", ["https://easyleads.es/a/"], "thekey")

        self.assertEqual(status, 200)
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
