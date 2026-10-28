import tempfile
import unittest
from pathlib import Path

from uploader.scanner import cleanup_stale_temp_dirs, scan_videos


class ScanVideosTests(unittest.TestCase):
    def test_recurses_sorts_and_skips_service_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative_path in (
                "zeta/clip.MP4",
                "alpha/movie.mkv",
                "alpha/readme.txt",
                "uploaded_archive/old.mp4",
                "nested/tmp_chunks/stale.avi",
            ):
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            result = scan_videos(root)

            self.assertEqual(
                [path.relative_to(root).as_posix() for path in result],
                ["alpha/movie.mkv", "zeta/clip.MP4"],
            )

    def test_cleanup_removes_nested_temp_directories_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            temp_file = root / "nested" / "tmp_chunks" / "stale.mp4"
            temp_file.parent.mkdir(parents=True)
            temp_file.touch()
            keep_file = root / "nested" / "keep.txt"
            keep_file.touch()

            cleanup_stale_temp_dirs(root)

            self.assertFalse(temp_file.parent.exists())
            self.assertTrue(keep_file.exists())


if __name__ == "__main__":
    unittest.main()