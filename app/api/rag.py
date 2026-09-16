from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import AiRateLimit
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.embeddings import EmbeddingBackend, EmbeddingError, get_embedding_service
from app.services.llm import LLMError, LLMProvider, get_llm_provider
from app.services.rag import ask_question

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=RAGResponse)
def ask(data: RAGRequest, user: CurrentUser, _rate_limit: AiRateLimit, db: DbSession, response: Response,
        embeddings: Annotated[EmbeddingBackend, Depends(get_embedding_service)],
        provider: Annotated[LLMProvider, Depends(get_llm_provider)]) -> RAGResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return ask_question(db, user.id, data, embeddings, provider, get_settings())
    except (LLMError, EmbeddingError) as exc:
        raise HTTPException(503, str(exc)) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "RAG retrieval database operation failed") from None
