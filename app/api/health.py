from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness only: this endpoint does not query PostgreSQL."""
    return {"status": "ok"}
