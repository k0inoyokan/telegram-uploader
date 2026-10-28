import asyncio
import logging

from uploader.config import Settings
from uploader.service import UploaderService


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    asyncio.run(UploaderService(settings).run_forever())


if __name__ == "__main__":
    main()