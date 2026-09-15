from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT")
DbSession = Annotated[Session, Depends(get_db)]


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: DbSession,
) -> User:
    if credentials is None:
        raise credentials_exception()
    try:
        payload = decode_access_token(credentials.credentials)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception() from None

    user = db.get(User, payload.sub)
    if user is None:
        raise credentials_exception()
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


CurrentAdmin = Annotated[User, Depends(require_admin)]
