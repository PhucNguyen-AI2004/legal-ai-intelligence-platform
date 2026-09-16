from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DocumentJobAccepted(BaseModel):
    document_id: UUID
    job_id: str
    job_type: Literal["process", "index"]
    status: Literal["queued"] = "queued"
