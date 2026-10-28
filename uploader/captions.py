from html import escape


def build_caption(filename: str, part_number: int | None = None, total_parts: int = 1) -> str:
    if part_number is None:
        return f"🎬 {filename}"
    return f"🎬 <b>Часть {part_number}/{total_parts}:</b> {escape(filename)}"