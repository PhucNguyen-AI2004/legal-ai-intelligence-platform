import logging
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.document import Document


logger = logging.getLogger("app.document_queue")
JobType = Literal["process", "index"]


class QueueUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class EnqueuedDocumentJob:
    id: str
    document_id: UUID
    job_type: JobType


def enqueue_processing(
    db: Session, queue: Any, document_id: UUID, owner_id: UUID, request_id: str,
) -> EnqueuedDocumentJob:
    document = _get_owned_locked(db, document_id, owner_id)
    if document.status == "processing":
        raise HTTPException(409, "Document is already processing")
    if document.embedding_status == "indexing":
        raise HTTPException(409, "Cannot process a document while it is indexing")
    previous = (
        document.status, document.processing_error, document.embedding_status,
        document.embedding_error, document.embedded_at,
    )
    document.status = "processing"
    document.processing_error = None
    document.embedding_status = "pending"
    document.embedding_error = None
    document.embedded_at = None
    db.commit()
    try:
        job = queue.enqueue(
            "app.workers.document_jobs.process_document_job",
            str(document_id),
            request_id,
            retry=_retry_policy(),
            on_failure=_failure_callback(),
            job_timeout="15m",
            result_ttl=0,
            failure_ttl=86400,
        )
    except Exception:
        db.rollback()
        document = _get_owned_locked(db, document_id, owner_id)
        (
            document.status, document.processing_error, document.embedding_status,
            document.embedding_error, document.embedded_at,
        ) = previous
        db.commit()
        raise QueueUnavailableError from None
    _log_enqueued(job.id, document_id, "process", request_id)
    return EnqueuedDocumentJob(job.id, document_id, "process")


def enqueue_indexing(
    db: Session, queue: Any, document_id: UUID, owner_id: UUID, request_id: str,
) -> EnqueuedDocumentJob:
    document = _get_owned_locked(db, document_id, owner_id)
    if document.status != "processed":
        raise HTTPException(409, "Document must be processed before indexing")
    if document.embedding_status == "indexing":
        raise HTTPException(409, "Document is already indexing")
    previous = (document.embedding_status, document.embedding_error)
    document.embedding_status = "indexing"
    document.embedding_error = None
    db.commit()
    try:
        job = queue.enqueue(
            "app.workers.document_jobs.index_document_job",
            str(document_id),
            request_id,
            retry=_retry_policy(),
            on_failure=_failure_callback(),
            job_timeout="30m",
            result_ttl=0,
            failure_ttl=86400,
        )
    except Exception:
        db.rollback()
        document = _get_owned_locked(db, document_id, owner_id)
        document.embedding_status, document.embedding_error = previous
        db.commit()
        raise QueueUnavailableError from None
    _log_enqueued(job.id, document_id, "index", request_id)
    return EnqueuedDocumentJob(job.id, document_id, "index")


def _get_owned_locked(db: Session, document_id: UUID, owner_id: UUID) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id, Document.owner_id == owner_id
        ).with_for_update()
    )
    if document is None:
        raise HTTPException(404, "Document not found")
    return document


def _log_enqueued(job_id: str, document_id: UUID, job_type: JobType, request_id: str) -> None:
    logger.info(
        "Document job enqueued",
        extra={
            "event": "document_job_enqueued", "request_id": request_id,
            "job_id": job_id, "job_type": job_type, "document_id": str(document_id),
        },
    )


def _retry_policy() -> Any:
    from rq import Retry
    return Retry(max=2, interval=[5, 30])


def _failure_callback() -> Any:
    from app.workers.document_jobs import handle_job_failure
    return handle_job_failure
