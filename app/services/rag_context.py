"""Build numbered sources from authorized retrieval results, with a hard char budget."""
import json
from dataclasses import dataclass

from app.schemas.rag import Citation
from app.schemas.search import SearchResult


@dataclass(frozen=True)
class RAGContext:
    text: str
    sources: list[Citation]


class RAGContextBuilder:
    def build(self, chunks: list[SearchResult], max_chars: int) -> RAGContext:
        blocks, sources, seen = [], [], set()
        used = 0
        for chunk in sorted(chunks, key=lambda item: item.score, reverse=True):
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            number = len(sources) + 1
            # JSON escaping keeps document title/content separate from our source labels.
            block = f"[SOURCE {number}]\n" + json.dumps(
                {"document": chunk.document_title, "chunk": chunk.chunk_index, "content": chunk.content},
                ensure_ascii=False,
            )
            cost = len(block) + (2 if blocks else 0)
            if used + cost > max_chars:
                # Skip oversized chunks intact; smaller lower-ranked chunks may still fit.
                continue
            blocks.append(block)
            used += cost
            sources.append(Citation(
                citation_number=number, document_id=chunk.document_id,
                document_title=chunk.document_title, chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index, score=chunk.score, excerpt=chunk.content[:500],
            ))
        return RAGContext(text="\n\n".join(blocks), sources=sources)
