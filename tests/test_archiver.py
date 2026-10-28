import tempfile
import unittest
from pathlib import Path

from uploader.archiver import archive_original


class ArchiveOriginalTests(unittest.TestCase):
    def test_archives_beside_source_and_keeps_name_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "nested"
            source_dir.mkdir()
            archive = source_dir / "uploaded_archive"
            archive.mkdir()
            (archive / "clip.mkv").write_text("older upload", encoding="utf-8")
            source = source_dir / "clip.mkv"
            source.write_text("new upload", encoding="utf-8")

            destination = archive_original(source)

            self.assertEqual(destination, archive / "clip (1).mkv")
            self.assertFalse(source.exists())
            self.assertEqual(destination.read_text(encoding="utf-8"), "new upload")


if __name__ == "__main__":
    unittest.main()