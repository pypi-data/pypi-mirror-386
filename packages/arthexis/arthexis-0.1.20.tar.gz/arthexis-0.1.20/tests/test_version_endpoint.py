import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.test import Client, TestCase, override_settings
from django.urls import reverse


class VersionEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("core.views.revision.get_revision", return_value="abcdef1234567890")
    def test_returns_version_and_revision(self, mock_get_revision):
        version_path = Path("VERSION")
        expected_version = (
            version_path.read_text(encoding="utf-8").strip()
            if version_path.exists()
            else ""
        )

        response = self.client.get(reverse("version-info"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"version": expected_version, "revision": "abcdef1234567890"},
        )
        mock_get_revision.assert_called_once()

    @patch("core.views.revision.get_revision", return_value="")
    def test_missing_version_file_returns_empty_values(self, mock_get_revision):
        with tempfile.TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            response = self.client.get(reverse("version-info"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "", "revision": ""})
        mock_get_revision.assert_called_once()
