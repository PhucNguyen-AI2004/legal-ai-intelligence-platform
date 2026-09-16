import logging
from time import monotonic
from typing import Any
from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.request_context import reset_request_id, set_request_id
from app.db.session import SessionLocal
from app.models.document import Document
from app.services.document_indexing import index_document
from app.services.document_processing import process_document
from app.services.document_storage import DocumentStorage
from app.services.embeddings import get_embedding_service


logger = logging.getLogger("app.document_worker")


class RetryableDocumentJobError(Exception):
    pass


def process_document_job(document_id: str, request_id: str) -> None:
    _run_job(UUID(document_id), request_id, "process")


def index_document_job(document_id: str, request_id: str) -> None:
    _run_job(UUID(document_id), request_id, "index")


def _run_job(document_id: UUID, request_id: str, job_type: str) -> None:
    job = _current_job()
    job_id = job.id if job is not None else "direct"
    attempt = _attempt(job)
    token = set_request_id(request_id)
    started = monotonic()
    logger.info(
        "Document job started",
        extra={"event": "document_job_started", "request_id": request_id, "job_id": job_id,
               "job_type": job_type, "document_id": str(document_id), "attempt": attempt},
    )
    try:
        with SessionLocal() as db:
            document = db.get(Document, document_id)
            if document is None:
                logger.warning(
                    "Document job target missing",
                    extra={"event": "document_job_failed", "request_id": request_id,
                           "job_id": job_id, "job_type": job_type,
                           "document_id": str(document_id), "failure_type": "missing_document"},
                )
                return
            try:
                if job_type == "process":
                    process_document(
                        document.id, document.owner_id, db, DocumentStorage(get_settings()),
                        get_settings(), already_claimed=True,
                    )
                else:
                    index_document(
                        document.id, document.owner_id, db, get_embedding_service(),
                        already_claimed=True,
                    )
            except OperationalError:
                db.rollback()
                raise
            except Exception as exc:
                db.rollback()
                _persist_safe_failure(document_id, job_type)
                logger.error(
                    "Document job failed",
                    extra={"event": "document_job_failed", "request_id": request_id,
                           "job_id": job_id, "job_type": job_type,
                           "document_id": str(document_id), "failure_type": type(exc).__name__},
                )
                return
        logger.info(
            "Document job completed",
            extra={"event": "document_job_completed", "request_id": request_id,
                   "job_id": job_id, "job_type": job_type, "document_id": str(document_id),
                   "duration_ms": round((monotonic() - started) * 1000, 3)},
        )
    except OperationalError:
        logger.warning(
            "Document job retrying",
            extra={"event": "document_job_retrying", "request_id": request_id,
                   "job_id": job_id, "job_type": job_type,
                   "document_id": str(document_id), "attempt": attempt},
        )
        raise RetryableDocumentJobError from None
    finally:
        reset_request_id(token)


def handle_job_failure(job: Any, connection: Any, exception_type: Any, value: Any, traceback: Any) -> None:
    del connection, exception_type, value, traceback
    document_id = UUID(str(job.args[0]))
    request_id = str(job.args[1])
    job_type = "process" if job.func_name.endswith("process_document_job") else "index"
    _persist_safe_failure(document_id, job_type)
    logger.error(
        "Document job exhausted retries",
        extra={"event": "document_job_failed", "request_id": request_id, "job_id": job.id,
               "job_type": job_type, "document_id": str(document_id),
               "failure_type": "retries_exhausted"},
    )


def _persist_safe_failure(document_id: UUID, job_type: str) -> None:
    with SessionLocal() as db:
        document = db.get(Document, document_id, with_for_update=True)
        if document is None:
            return
        if job_type == "process" and document.status == "processing":
            document.status = "failed"
            document.processing_error = "Document processing failed"
        if job_type == "index" and document.embedding_status == "indexing":
            document.embedding_status = "failed"
            document.embedding_error = "Document indexing failed"
        db.commit()


def _current_job() -> Any:
    try:
        from rq import get_current_job
        return get_current_job()
    except ImportError:
        return None


def _attempt(job: Any) -> int:
    if job is None or job.retries_left is None:
        return 1
    return 3 - int(job.retries_left)
