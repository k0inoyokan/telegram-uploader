import logging
import subprocess
from pathlib import Path

from uploader.probe import MediaProbe


logger = logging.getLogger(__name__)


class FFmpegTranscoder:
    def __init__(
        self,
        probe: MediaProbe,
        ffmpeg_executable: str = "ffmpeg",
    ) -> None:
        self.probe = probe
        self.ffmpeg_executable = ffmpeg_executable

    def prepare(self, source: Path, work_dir: Path) -> Path:
        info = self.probe.inspect(source)
        if info.is_h264_mp4 and source.suffix.lower() == ".mp4":
            logger.info("Already H.264 MP4; processing skipped: %s", source)
            return source

        work_dir.mkdir(parents=True, exist_ok=True)
        output = work_dir / f"{source.stem}.mp4"
        if info.video_codec == "h264":
            codec_arguments = ["-c", "copy"]
            logger.info("Remuxing H.264 video to MP4: %s", source)
        else:
            codec_arguments = [
                "-c:v",
                "libx264",
                "-crf",
                "22",
                "-preset",
                "fast",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
            ]
            logger.info("Transcoding %s from %s to H.264/AAC", source, info.video_codec)

        command = [
            self.ffmpeg_executable,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            *codec_arguments,
            "-movflags",
            "+faststart",
            str(output),
        ]
        self._run(command)
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg produced no output for {source}")
        return output

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            details = (error.stderr or "").strip()
            raise RuntimeError(f"FFmpeg failed: {details[-4000:]}") from error