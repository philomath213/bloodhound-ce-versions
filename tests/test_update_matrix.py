"""Offline unit tests for update_matrix.py (network calls are mocked)."""

import unittest
from unittest import mock

import update_matrix


def make_response(json_data, links=None):
    response = mock.Mock()
    response.json.return_value = json_data
    response.links = links or {}
    response.raise_for_status.return_value = None
    return response


class IsValidSemverTest(unittest.TestCase):
    def test_accepts_plain_semver(self):
        self.assertTrue(update_matrix.is_valid_semver("8.5.2"))

    def test_rejects_other_tags(self):
        for tag in ["latest", "v8.5.2", "8.5", "8.5.2-rc1", "edge"]:
            self.assertFalse(update_matrix.is_valid_semver(tag), tag)


class GetAllTagsTest(unittest.TestCase):
    @mock.patch("update_matrix.requests.get")
    def test_follows_link_pagination(self, mock_get):
        mock_get.side_effect = [
            make_response({"token": "abc"}),
            make_response(
                {"tags": ["8.0.0", "8.1.0"]},
                links={"next": {"url": "/v2/specterops/bloodhound/tags/list?last=8.1.0&n=2"}},
            ),
            make_response({"tags": ["latest"]}),
        ]

        tags = update_matrix.get_all_tags("specterops/bloodhound", page_size=2)

        self.assertEqual(tags, ["8.0.0", "8.1.0", "latest"])
        self.assertIn("auth.docker.io", mock_get.call_args_list[0].args[0])
        self.assertEqual(
            mock_get.call_args_list[2].args[0],
            "https://registry-1.docker.io/v2/specterops/bloodhound/tags/list?last=8.1.0&n=2",
        )
        for call in mock_get.call_args_list[1:]:
            self.assertEqual(call.kwargs["headers"], {"Authorization": "Bearer abc"})


class GetCollectorVersionsTest(unittest.TestCase):
    @mock.patch("update_matrix.requests.get")
    def test_extracts_versions_from_amd64_layers(self, mock_get):
        mock_get.return_value = make_response([
            {
                "architecture": "arm64",
                "os": "linux",
                "layers": [{"instruction": "ARG SHARPHOUND_VERSION=wrong"}],
            },
            {
                "architecture": "amd64",
                "os": "linux",
                "layers": [
                    {"instruction": "ARG SHARPHOUND_VERSION=v2.9.0"},
                    {"instruction": "RUN something"},
                    {"instruction": "ARG AZUREHOUND_VERSION=v2.8.3"},
                ],
            },
        ])

        versions = update_matrix.get_collector_versions("specterops/bloodhound", "8.5.2")

        self.assertEqual(versions, {"SHARPHOUND_VERSION": "v2.9.0", "AZUREHOUND_VERSION": "v2.8.3"})

    @mock.patch("update_matrix.requests.get")
    def test_returns_none_without_version_args(self, mock_get):
        mock_get.return_value = make_response([
            {"architecture": "amd64", "os": "linux", "layers": [{"instruction": "RUN something"}]},
        ])

        self.assertIsNone(update_matrix.get_collector_versions("specterops/bloodhound", "8.5.2"))


if __name__ == "__main__":
    unittest.main()
