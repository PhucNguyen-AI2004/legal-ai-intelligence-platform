"""Extract text only. No OCR, embeddings, or document modifications."""
from pathlib import Path
from zipfile import ZipFile

# Conservative guardrails, not a substitute for process-level memory/time limits.
MAX_EXTRACTED_CHARACTERS = 5_000_000
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


class ProcessingError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _join_parts(parts) -> str:
    collected = []
    size = 0
    for part in parts:
        size += len(part) + 2
        if size > MAX_EXTRACTED_CHARACTERS:
            raise ProcessingError("Extracted text exceeds the processing limit")
        collected.append(part)
    return "\n\n".join(collected)


def extract_text(file_path: Path, file_type: str) -> str:
    try:
        if file_type == "txt":
            with file_path.open(encoding="utf-8-sig") as source:
                text = source.read(MAX_EXTRACTED_CHARACTERS + 1)
            if len(text) > MAX_EXTRACTED_CHARACTERS:
                raise ProcessingError("Extracted text exceeds the processing limit")
            return text
        if file_type == "docx":
            from docx import Document

            with ZipFile(file_path) as archive:
                if sum(entry.file_size for entry in archive.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise ProcessingError("DOCX exceeds the uncompressed processing limit")
            document = Document(file_path)
            return _join_parts(paragraph.text for paragraph in document.paragraphs)
        if file_type == "pdf":
            from pypdf import PdfReader

            with file_path.open("rb") as source:
                reader = PdfReader(source)
                if reader.is_encrypted:
                    raise ProcessingError("Encrypted PDFs are not supported")
                text = _join_parts(page.extract_text() or "" for page in reader.pages)
            if not text.strip():
                raise ProcessingError("PDF has no extractable text; OCR is not supported")
            return text
        raise ProcessingError("Unsupported document type", 415)
    except ProcessingError:
        raise
    except FileNotFoundError:
        raise ProcessingError("Stored file is missing; upload the document again", 409) from None
    except UnicodeDecodeError:
        raise ProcessingError("TXT is not valid UTF-8") from None
    except ImportError:
        raise ProcessingError("Document extraction dependency is unavailable", 503) from None
    except OSError:
        raise ProcessingError("Stored file cannot be read", 503) from None
    except Exception:
        # Parser diagnostics can contain filesystem paths or document content.
        raise ProcessingError("Document could not be parsed; check the file format") from None
