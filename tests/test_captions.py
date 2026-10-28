import unittest

from uploader.captions import build_caption


class BuildCaptionTests(unittest.TestCase):
    def test_single_file_caption_is_exact(self) -> None:
        self.assertEqual(build_caption("clip.mp4"), "🎬 clip.mp4")

    def test_part_caption_escapes_filename_for_html(self) -> None:
        self.assertEqual(
            build_caption("a&b.mp4", 2, 4),
            "🎬 <b>Часть 2/4:</b> a&amp;b.mp4",
        )


if __name__ == "__main__":
    unittest.main()