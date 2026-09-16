from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import CurrentUser, DbSession, credentials_exception
from app.core.security import create_access_token
from app.core.rate_limit import AuthRateLimit
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.auth import EmailAlreadyRegistered, authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession, _rate_limit: AuthRateLimit) -> User:
    try:
        return register_user(db, data)
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="Email already registered") from None


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: DbSession, response: Response, _rate_limit: AuthRateLimit) -> Token:
    user = authenticate_user(db, data)
    if user is None:
        raise credentials_exception()
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser, response: Response) -> User:
    response.headers["Cache-Control"] = "no-store"
    return user
