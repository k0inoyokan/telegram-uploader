import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telethon import TelegramClient

from uploader.service import DiagnosticTelegramClient


class AuthDiagnosticsTests(unittest.IsolatedAsyncioTestCase):
    async def test_logs_delivery_type_without_logging_code_or_phone(self) -> None:
        sent_code = SimpleNamespace(type=SimpleNamespace())
        client = DiagnosticTelegramClient("/tmp/test-session", 12345, "test-hash")

        with (
            patch.object(
                TelegramClient,
                "send_code_request",
                new=AsyncMock(return_value=sent_code),
            ),
            self.assertLogs("uploader.service", level=logging.INFO) as captured,
        ):
            result = await client.send_code_request("+10000000000")

        self.assertIs(result, sent_code)
        self.assertIn("Telegram login code delivery type: SimpleNamespace", captured.output[0])
        self.assertNotIn("+10000000000", captured.output[0])
        self.assertNotIn("test-hash", captured.output[0])


if __name__ == "__main__":
    unittest.main()