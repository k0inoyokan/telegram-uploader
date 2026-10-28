from dataclasses import dataclass
import json
import subprocess
from pathlib import Path


class MediaProbeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MediaInfo:
    format_names: frozenset[str]
    video_codec: str | None
    duration_seconds: float | None

    @property
    def is_h264_mp4(self) -> bool:
        return "mp4" in self.format_names and self.video_codec == "h264"


class MediaProbe:
    def __init__(self, executable: str = "ffprobe") -> None:
        self.executable = executable

    def inspect(self, path: Path) -> MediaInfo:
        command = [
            self.executable,
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration:stream=codec_type,codec_name",
            "-of",
            "json",
            str(path),
        ]
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            details = (error.stderr or "").strip()
            reason = details[-1000:] if details else f"ffprobe exited with code {error.returncode}"
            raise MediaProbeError(f"Cannot inspect {path}: {reason}") from error

        try:
            metadata = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise MediaProbeError(f"ffprobe returned invalid metadata for {path}") from error
        format_data = metadata.get("format", {})
        formats = frozenset(format_data.get("format_name", "").split(","))
        video_codec = next(
            (
                stream.get("codec_name")
                for stream in metadata.get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            None,
        )
        duration_value = format_data.get("duration")
        try:
            duration = float(duration_value) if duration_value is not None else None
        except (TypeError, ValueError):
            duration = None

        if video_codec is None:
            raise MediaProbeError(f"No video stream found in {path}")
        return MediaInfo(formats, video_codec, duration)