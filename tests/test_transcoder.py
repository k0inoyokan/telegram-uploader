import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uploader.probe import MediaInfo
from uploader.transcoder import FFmpegTranscoder


class FakeProbe:
    def __init__(self, info: MediaInfo) -> None:
        self.info = info

    def inspect(self, path: Path) -> MediaInfo:
        return self.info


class FFmpegTranscoderTests(unittest.TestCase):
    def test_valid_h264_mp4_is_returned_without_ffmpeg(self) -> None:
        info = MediaInfo(frozenset({"mov", "mp4"}), "h264", 10.0)
        transcoder = FFmpegTranscoder(FakeProbe(info))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clip.mp4"
            source.touch()

            with patch("uploader.transcoder.subprocess.run") as run:
                result = transcoder.prepare(source, Path(directory) / "tmp")

            self.assertEqual(result, source)
            run.assert_not_called()

    def test_non_h264_video_uses_requested_h264_aac_options(self) -> None:
        info = MediaInfo(frozenset({"matroska"}), "hevc", 10.0)
        transcoder = FFmpegTranscoder(FakeProbe(info))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clip.mkv"
            source.touch()
            work_dir = Path(directory) / "tmp"

            def create_output(command: list[str], **kwargs: object) -> None:
                Path(command[-1]).write_bytes(b"encoded")

            with patch("uploader.transcoder.subprocess.run", side_effect=create_output) as run:
                result = transcoder.prepare(source, work_dir)

            command = run.call_args.args[0]
            self.assertEqual(result.name, "clip.mp4")
            self.assertIn("libx264", command)
            self.assertIn("-crf", command)
            self.assertIn("22", command)
            self.assertIn("aac", command)

    def test_h264_in_other_container_is_remuxed_without_reencoding(self) -> None:
        info = MediaInfo(frozenset({"matroska"}), "h264", 10.0)
        transcoder = FFmpegTranscoder(FakeProbe(info))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "clip.mkv"
            source.touch()
            work_dir = Path(directory) / "tmp"

            def create_output(command: list[str], **kwargs: object) -> None:
                Path(command[-1]).write_bytes(b"remuxed")

            with patch("uploader.transcoder.subprocess.run", side_effect=create_output) as run:
                result = transcoder.prepare(source, work_dir)

            command = run.call_args.args[0]
            self.assertEqual(result.name, "clip.mp4")
            self.assertIn("-c", command)
            self.assertIn("copy", command)
            self.assertNotIn("libx264", command)


if __name__ == "__main__":
    unittest.main()