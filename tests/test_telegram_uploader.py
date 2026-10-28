import asyncio
from io import StringIO
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from uploader.config import Settings
from uploader.telegram_uploader import TelegramUploader


class TelegramUploaderTests(unittest.TestCase):
    def test_progress_callback_logs_each_percent_and_transferred_bytes(self) -> None:
        callback = TelegramUploader._progress_callback("Upload 1/1: clip.mp4")

        with patch("uploader.telegram_uploader.sys.stdout", new_callable=StringIO) as output:
            callback(0, 1000)
            callback(9, 1000)
            callback(10, 1000)
            callback(19, 1000)
            callback(20, 1000)
            callback(1000, 1000)

        progress = output.getvalue()
        self.assertEqual(progress.count("\n"), 1)
        self.assertEqual(progress.count("\r"), 4)
        self.assertIn("0%", progress)
        self.assertIn("1%", progress)
        self.assertIn("2%", progress)
        self.assertIn("100%", progress)
        self.assertIn("MiB", progress)

    def test_sends_original_and_unattributed_media_copy_to_topics(self) -> None:
        media = object()
        client = SimpleNamespace(send_file=AsyncMock(return_value=SimpleNamespace(media=media)))
        settings = Settings(1, "hash", -100123, 1, 42, Path("/videos"))
        uploader = TelegramUploader(client, settings)

        asyncio.run(uploader.send_parts([Path("part.mp4")], "clip.mp4"))

        self.assertEqual(client.send_file.await_count, 2)
        original_call, copy_call = client.send_file.await_args_list
        self.assertEqual(original_call.kwargs["reply_to"], 1)
        self.assertIsNone(original_call.kwargs["parse_mode"])
        self.assertEqual(original_call.kwargs["caption"], "🎬 clip.mp4")
        self.assertIs(copy_call.args[1], media)
        self.assertEqual(copy_call.kwargs["reply_to"], 42)
        self.assertEqual(copy_call.kwargs["caption"], "🎬 clip.mp4")


if __name__ == "__main__":
    unittest.main()