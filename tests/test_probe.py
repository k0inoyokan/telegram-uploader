import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from uploader.probe import MediaProbe, MediaProbeError


class MediaProbeTests(unittest.TestCase):
    def test_ffprobe_failure_becomes_a_clear_file_specific_error(self) -> None:
        source = Path("incomplete.temp.mp4")
        failure = subprocess.CalledProcessError(
            1,
            ["ffprobe", str(source)],
            stderr="moov atom not found",
        )

        with patch("uploader.probe.subprocess.run", side_effect=failure):
            with self.assertRaisesRegex(
                MediaProbeError,
                r"Cannot inspect incomplete\.temp\.mp4: moov atom not found",
            ):
                MediaProbe().inspect(source)


if __name__ == "__main__":
    unittest.main()