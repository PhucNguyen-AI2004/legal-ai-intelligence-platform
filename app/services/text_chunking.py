from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    char_count: int
    token_estimate: int


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    """Prefer paragraph ends; split long paragraphs at line/word boundaries.

    Overlap uses the suffix of the previous raw window. Stripping whitespace
    can make the visible overlap slightly shorter than the configured value.
    """
    if chunk_size <= 0 or not 0 <= chunk_overlap < chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= chunk_overlap < chunk_size")
    chunks = []
    start = 0
    previous_end = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Always consume new text, rather than repeatedly emitting overlap.
            minimum_end = max(previous_end + 1, start + chunk_overlap + 1)
            for separator in ("\n\n", "\n", " "):
                boundary = text.rfind(separator, minimum_end, end)
                if boundary != -1:
                    end = boundary + len(separator)
                    break
        content = text[start:end].strip()
        if content:
            chunks.append(TextChunk(len(chunks), content, len(content), (len(content) + 3) // 4))
        if end == len(text):
            break
        previous_end = end
        start = end - chunk_overlap
    return chunks
