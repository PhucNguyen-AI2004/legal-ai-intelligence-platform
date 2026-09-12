from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(
    str(get_settings().database_url),
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Use with Depends(get_db); the caller owns commit boundaries."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
