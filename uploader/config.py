from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(f"Required environment variable {name} is not set")
    return value.strip()


def _chat_id(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


@dataclass(frozen=True, slots=True)
class Settings:
    api_id: int
    api_hash: str
    chat_id: int | str
    thread_id: int
    forward_thread_id: int
    src_videos_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        try:
            api_id = int(_required("API_ID"))
            thread_id = int(_required("THREAD_ID"))
            forward_thread_id = int(_required("FORWARD_THREAD_ID"))
        except ValueError as error:
            raise ValueError(f"Invalid integer configuration: {error}") from error
        if thread_id != 1:
            raise ValueError("THREAD_ID must be 1 for the Telegram General topic")

        return cls(
            api_id=api_id,
            api_hash=_required("API_HASH"),
            chat_id=_chat_id(_required("CHAT_ID")),
            thread_id=thread_id,
            forward_thread_id=forward_thread_id,
            src_videos_dir=Path(_required("SRC_VIDEOS_DIR")).expanduser(),
        )