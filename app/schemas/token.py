from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    iat: int
    token_type: Literal["access"]
