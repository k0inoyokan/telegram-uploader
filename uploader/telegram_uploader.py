import sys
from pathlib import Path

from telethon import TelegramClient

from uploader.captions import build_caption
from uploader.config import Settings


class TelegramUploader:
    def __init__(self, client: TelegramClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def send_parts(self, parts: list[Path], display_name: str) -> None:
        total_parts = len(parts)
        for part_number, part_path in enumerate(parts, start=1):
            caption = build_caption(
                display_name,
                part_number if total_parts > 1 else None,
                total_parts,
            )
            parse_mode = "html" if total_parts > 1 else None
            message = await self.client.send_file(
                self.settings.chat_id,
                part_path,
                caption=caption,
                parse_mode=parse_mode,
                reply_to=self.settings.thread_id,
                supports_streaming=True,
                progress_callback=self._progress_callback(
                    f"Upload {part_number}/{total_parts}: {part_path.name}"
                ),
            )
            if message.media is None:
                raise RuntimeError(f"Telegram did not return media for {part_path}")

            await self.client.send_file(
                self.settings.chat_id,
                message.media,
                caption=caption,
                parse_mode=parse_mode,
                reply_to=self.settings.forward_thread_id,
                supports_streaming=True,
                progress_callback=self._progress_callback(
                    f"Copy {part_number}/{total_parts}: {part_path.name}"
                ),
            )

    @staticmethod
    def _progress_callback(label: str):
        last_reported = -1

        def report(current: int, total: int) -> None:
            nonlocal last_reported
            percentage = 100 if total <= 0 else min(100, int(current * 100 / total))
            if percentage > last_reported:
                last_reported = percentage
                sys.stdout.write(
                    f"\r{label}: {percentage}% "
                    f"({current / 1024**2:.1f} / {total / 1024**2:.1f} MiB)"
                )
                if percentage == 100:
                    sys.stdout.write("\n")
                sys.stdout.flush()

        return report