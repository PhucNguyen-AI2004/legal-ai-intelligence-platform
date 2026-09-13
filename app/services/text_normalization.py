import re
import unicodedata


def normalize_text(text: str) -> str:
    """Preserve case, punctuation, legal numbering and paragraph boundaries."""
    text = unicodedata.normalize("NFC", text.lstrip("\ufeff"))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n\n")
    # PostgreSQL TEXT cannot store NUL. Do not remove other meaningful characters.
    text = text.replace("\x00", "")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
