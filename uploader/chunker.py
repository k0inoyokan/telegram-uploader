import logging
import math
import subprocess
from pathlib import Path

from uploader.probe import MediaProbe


logger = logging.getLogger(__name__)
MAX_PART_BYTES = int(3.9 * 1000**3)


class FFmpegChunker:
    def __init__(
        self,
        probe: MediaProbe,
        ffmpeg_executable: str = "ffmpeg",
        max_part_bytes: int = MAX_PART_BYTES,
        max_attempts: int = 8,
    ) -> None:
        self.probe = probe
        self.ffmpeg_executable = ffmpeg_executable
        self.max_part_bytes = max_part_bytes
        self.max_attempts = max_attempts

    def split_if_needed(self, video: Path, work_dir: Path) -> list[Path]:
        if video.stat().st_size <= self.max_part_bytes:
            return [video]

        info = self.probe.inspect(video)
        if not info.duration_seconds or info.duration_seconds <= 0:
            raise ValueError(f"Cannot split video with unknown duration: {video}")

        work_dir.mkdir(parents=True, exist_ok=True)
        segment_count = max(2, math.ceil(video.stat().st_size / self.max_part_bytes))
        for attempt in range(1, self.max_attempts + 1):
            self._remove_previous_chunks(work_dir)
            segment_time = info.duration_seconds / segment_count
            self._create_segments(video, work_dir, segment_time)
            chunks = sorted(work_dir.glob("part_*.mp4"))
            if not chunks:
                raise RuntimeError(f"FFmpeg did not create chunks for {video}")

            oversized = [chunk for chunk in chunks if chunk.stat().st_size >= self.max_part_bytes]
            if not oversized:
                logger.info("Split %s into %d parts", video, len(chunks))
                return chunks

            logger.warning(
                "Some chunks exceed the size limit on attempt %d; splitting more finely",
                attempt,
            )
            segment_count *= 2

        self._remove_previous_chunks(work_dir)
        raise RuntimeError(
            f"Could not create chunks below {self.max_part_bytes} bytes for {video}"
        )

    def _create_segments(self, video: Path, work_dir: Path, segment_time: float) -> None:
        command = [
            self.ffmpeg_executable,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c",
            "copy",
            "-f",
            "segment",
            "-segment_time",
            f"{segment_time:.6f}",
            "-reset_timestamps",
            "1",
            "-segment_format",
            "mp4",
            "-segment_format_options",
            "movflags=+faststart",
            str(work_dir / "part_%04d.mp4"),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            details = (error.stderr or "").strip()
            raise RuntimeError(f"FFmpeg chunking failed: {details[-4000:]}") from error

    @staticmethod
    def _remove_previous_chunks(work_dir: Path) -> None:
        for chunk in work_dir.glob("part_*.mp4"):
            chunk.unlink(missing_ok=True)