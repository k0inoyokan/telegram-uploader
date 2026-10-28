import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uploader.chunker import FFmpegChunker
from uploader.probe import MediaInfo


class FakeProbe:
    def inspect(self, path: Path) -> MediaInfo:
        return MediaInfo(frozenset({"mp4"}), "h264", 12.0)


class FFmpegChunkerTests(unittest.TestCase):
    def test_retries_with_smaller_segments_until_all_fit(self) -> None:
        chunker = FFmpegChunker(FakeProbe(), max_part_bytes=50)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "large.mp4"
            video.write_bytes(b"x" * 101)
            work_dir = root / "tmp"
            attempts = 0

            def create_chunks(command: list[str], **kwargs: object) -> None:
                nonlocal attempts
                attempts += 1
                pattern = Path(command[-1])
                sizes = [60, 41] if attempts == 1 else [34, 34, 33]
                for index, size in enumerate(sizes):
                    (pattern.parent / f"part_{index:04d}.mp4").write_bytes(b"x" * size)

            with patch("uploader.chunker.subprocess.run", side_effect=create_chunks):
                chunks = chunker.split_if_needed(video, work_dir)

            self.assertEqual(attempts, 2)
            self.assertEqual(len(chunks), 3)
            self.assertTrue(all(chunk.stat().st_size <= 50 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()