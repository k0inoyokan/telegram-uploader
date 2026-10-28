import asyncio
import logging
import tempfile
from pathlib import Path

from python_socks import ProxyType
from telethon import TelegramClient

from uploader.archiver import archive_original
from uploader.chunker import FFmpegChunker
from uploader.config import Settings
from uploader.probe import MediaProbe, MediaProbeError
from uploader.scanner import cleanup_stale_temp_dirs, scan_videos
from uploader.telegram_uploader import TelegramUploader
from uploader.transcoder import FFmpegTranscoder


logger = logging.getLogger(__name__)
SCAN_INTERVAL_SECONDS = 600


class DiagnosticTelegramClient(TelegramClient):
    async def send_code_request(
        self,
        phone: str,
        *,
        force_sms: bool = False,
        _retry_count: int = 0,
    ):
        sent_code = await super().send_code_request(
            phone,
            force_sms=force_sms,
            _retry_count=_retry_count,
        )
        logger.info(
            "Telegram login code delivery type: %s",
            type(sent_code.type).__name__,
        )
        return sent_code


class UploaderService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        probe = MediaProbe()
        self.transcoder = FFmpegTranscoder(probe)
        self.chunker = FFmpegChunker(probe)

    async def run_forever(self) -> None:
        cleanup_stale_temp_dirs(self.settings.src_videos_dir)
        proxy = (ProxyType.SOCKS5, "127.0.0.1", 9050, None, None, True)
        client = DiagnosticTelegramClient(
            str(Path("data") / "telegram_uploader"),
            self.settings.api_id,
            self.settings.api_hash,
            proxy=proxy,
            app_version="9.3.1",
            device_model="Samsung Galaxy S23 Ultra",
            system_version="Android 13",
            lang_code="ru",
            system_lang_code="ru",
        )
        async with client:
            await client.start()
            telegram_uploader = TelegramUploader(client, self.settings)
            logger.info("Telegram uploader started; scanning every %d seconds", SCAN_INTERVAL_SECONDS)
            while True:
                await self._scan_once(telegram_uploader)
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)

    async def _scan_once(self, telegram_uploader: TelegramUploader) -> None:
        try:
            videos = scan_videos(self.settings.src_videos_dir)
            logger.info("Found %d video(s)", len(videos))
        except Exception:
            logger.exception("Could not scan source directory")
            return

        for source in videos:
            try:
                await self._process_file(source, telegram_uploader)
            except MediaProbeError as error:
                logger.warning("Cannot process %s; it will be retried next scan: %s", source, error)
            except Exception:
                logger.exception("Failed to process %s; it will be retried next scan", source)

    async def _process_file(
        self,
        source: Path,
        telegram_uploader: TelegramUploader,
    ) -> None:
        temp_root = source.parent / "tmp_chunks"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="upload-", dir=temp_root) as directory:
            work_dir = Path(directory)
            video = await asyncio.to_thread(self.transcoder.prepare, source, work_dir)
            parts = await asyncio.to_thread(self.chunker.split_if_needed, video, work_dir)
            await telegram_uploader.send_parts(parts, f"{source.stem}.mp4")
            archived_path = archive_original(source)
            logger.info("Upload complete; archived original to %s", archived_path)