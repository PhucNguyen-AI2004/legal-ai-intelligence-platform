import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

# Unknown accounts still perform one expensive password verification.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


class EmailAlreadyRegistered(Exception):
    pass


def register_user(db: Session, data: UserCreate) -> User:
    if db.scalar(select(User.id).where(User.email == data.email)) is not None:
        raise EmailAlreadyRegistered

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password.get_secret_value()),
        full_name=data.full_name,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # The unique index also protects concurrent registration requests.
        if (
            getattr(exc.orig, "sqlstate", None) == "23505"
            and getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            == "ix_users_email"
        ):
            raise EmailAlreadyRegistered from exc
        raise
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> User | None:
    user = db.scalar(select(User).where(User.email == data.email))
    stored_hash = user.hashed_password if user is not None else _DUMMY_HASH
    valid_password = verify_password(data.password.get_secret_value(), stored_hash)
    if not valid_password or user is None or not user.is_active:
        return None
    return user
