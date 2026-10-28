import os
from pathlib import Path


def archive_original(source: Path) -> Path:
    archive_dir = source.parent / "uploaded_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / source.name
    suffix = 1
    while destination.exists():
        destination = archive_dir / f"{source.stem} ({suffix}){source.suffix}"
        suffix += 1

    os.replace(source, destination)
    return destination