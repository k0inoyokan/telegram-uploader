import os
import unittest
from pathlib import Path
from unittest.mock import patch

from uploader.config import Settings


class SettingsTests(unittest.TestCase):
    def test_reads_env_and_requires_general_topic_id_one(self) -> None:
        values = {
            "API_ID": "12345",
            "API_HASH": "hash",
            "CHAT_ID": "-1001234567890",
            "THREAD_ID": "1",
            "FORWARD_THREAD_ID": "42",
            "SRC_VIDEOS_DIR": "/videos with spaces",
        }
        with patch.dict(os.environ, values, clear=True), patch("uploader.config.load_dotenv"):
            settings = Settings.from_env()

        self.assertEqual(settings.api_id, 12345)
        self.assertEqual(settings.chat_id, -1001234567890)
        self.assertEqual(settings.src_videos_dir, Path("/videos with spaces"))

    def test_rejects_non_general_upload_topic(self) -> None:
        values = {
            "API_ID": "12345",
            "API_HASH": "hash",
            "CHAT_ID": "-1001234567890",
            "THREAD_ID": "2",
            "FORWARD_THREAD_ID": "42",
            "SRC_VIDEOS_DIR": "/videos",
        }
        with patch.dict(os.environ, values, clear=True), patch("uploader.config.load_dotenv"):
            with self.assertRaisesRegex(ValueError, "THREAD_ID must be 1"):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()