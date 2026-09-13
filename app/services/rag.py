import logging
import re
from time import monotonic
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.embeddings import EmbeddingBackend
from app.services.llm import LLMError, LLMProvider
from app.services.rag_context import RAGContextBuilder
from app.services.rag_prompt import SYSTEM_PROMPT
from app.services.semantic_search import search_documents

logger = logging.getLogger("uvicorn.error")
NO_CONTEXT = "Tôi chưa tìm thấy đủ thông tin trong các tài liệu đã được lập chỉ mục để trả lời câu hỏi này."


def ask_question(db: Session, owner_id: UUID, request: RAGRequest, embeddings: EmbeddingBackend,
                 provider: LLMProvider, settings: Settings) -> RAGResponse:
    started = monotonic()
    outcome = "success"
    logger.info("RAG request started")
    try:
        chunks = search_documents(db, owner_id, request.search_request(), embeddings)
        context = RAGContextBuilder().build(
            [chunk for chunk in chunks if chunk.score >= settings.rag_min_similarity],
            settings.rag_max_context_chars,
        )
        logger.info("RAG retrieval: retrieved=%s used=%s", len(chunks), len(context.sources))
        if not context.sources:
            return RAGResponse(answer=NO_CONTEXT, grounded=False, citations=[], model=None,
                               retrieved_chunks=len(chunks), used_chunks=0)
        answer = provider.generate_answer(system_prompt=SYSTEM_PROMPT, question=request.question, context=context.text)
        if not isinstance(answer, str) or not answer.strip():
            raise LLMError("LLM provider returned an empty answer")
        # Backend metadata only; unsupported bracket formats do not count as citations.
        references = [value for value in re.findall(r"\[([^\[\]\r\n]*)\]", answer)
                      if re.search(r"\d", value)]
        valid = {str(source.citation_number): source for source in context.sources}
        if any(reference not in valid for reference in references):
            # Fail closed rather than retaining unsupported claims after deleting [99].
            return RAGResponse(answer=NO_CONTEXT, grounded=False, citations=[], model=settings.llm_model,
                               retrieved_chunks=len(chunks), used_chunks=len(context.sources))
        citations = [source for number, source in valid.items() if number in references]
        return RAGResponse(answer=answer.strip(), grounded=bool(citations), citations=citations,
                           model=settings.llm_model, retrieved_chunks=len(chunks), used_chunks=len(context.sources))
    except Exception as exc:
        outcome = "failure"
        logger.warning("RAG failed: error_type=%s", type(exc).__name__)
        raise
    finally:
        logger.info("RAG request finished: outcome=%s duration_seconds=%.3f", outcome, monotonic() - started)
