from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.search import SearchRequest, SearchResponse
from app.services.embeddings import EmbeddingBackend, EmbeddingError, get_embedding_service
from app.services.semantic_search import search_documents
from app.core.rate_limit import AiRateLimit

router = APIRouter(tags=["search"])
EmbeddingDependency = Annotated[EmbeddingBackend, Depends(get_embedding_service)]


@router.post("/search", response_model=SearchResponse)
def search(data: SearchRequest, user: CurrentUser, _rate_limit: AiRateLimit, db: DbSession, backend: EmbeddingDependency, response: Response) -> SearchResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        results = search_documents(db, user.id, data, backend)
        return SearchResponse(model_name=backend.model_name, results=results)
    except EmbeddingError as exc:
        raise HTTPException(503, str(exc)) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Vector search database operation failed") from None
