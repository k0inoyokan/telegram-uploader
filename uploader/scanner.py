import os
import shutil
from pathlib import Path


VIDEO_EXTENSIONS = frozenset(
    {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".3gp"}
)
IGNORED_DIRECTORIES = frozenset({"uploaded_archive", "tmp_chunks"})


def scan_videos(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Video source directory does not exist: {root}")

    videos: list[Path] = []
    for current, directories, files in os.walk(root):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        )
        for filename in files:
            path = Path(current) / filename
            if path.suffix.lower() in VIDEO_EXTENSIONS:
                videos.append(path)

    return sorted(
        videos,
        key=lambda path: (
            path.relative_to(root).as_posix().casefold(),
            path.relative_to(root).as_posix(),
        ),
    )


def cleanup_stale_temp_dirs(root: Path) -> None:
    root = root.expanduser().resolve()
    for current, directories, _ in os.walk(root):
        if "tmp_chunks" in directories:
            temp_dir = Path(current) / "tmp_chunks"
            if temp_dir.is_symlink():
                temp_dir.unlink()
            else:
                shutil.rmtree(temp_dir)
            directories.remove("tmp_chunks")