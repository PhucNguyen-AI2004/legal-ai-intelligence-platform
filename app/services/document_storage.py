"""Local file validation/storage; no document parsing or text extraction."""
import codecs
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, UploadFile

from app.core.config import Settings

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}
STORAGE_KEY = re.compile(r"[0-9a-f]{32}\.(pdf|docx|txt)(\.deleting)?")
CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class StoredFile:
    original_filename: str
    stored_filename: str
    file_type: str
    mime_type: str
    file_size: int


class DocumentStorage:
    def __init__(self, settings: Settings):
        self.root = settings.storage_directory
        self.max_size = settings.max_upload_size_bytes

    def path_for(self, key: str) -> Path:
        if not STORAGE_KEY.fullmatch(key):
            raise OSError("Invalid document storage key")
        path = self.root / key
        if path.is_symlink() or path.resolve().parent != self.root:
            raise OSError("Unsafe document storage path")
        return path

    def save(self, upload: UploadFile) -> StoredFile:
        name = upload.filename or ""
        if (
            not name or len(name) > 255 or any(c in name for c in '/\\:')
            or any(unicodedata.category(c).startswith("C") for c in name)
        ):
            raise HTTPException(400, "Invalid filename")
        extension = Path(name).suffix.lower()
        if extension not in MIME_TYPES:
            raise HTTPException(415, "Supported file types: PDF, DOCX, TXT")
        canonical_mime = MIME_TYPES[extension]
        supplied_mime = (upload.content_type or "").split(";", 1)[0].strip().lower()
        if supplied_mime not in {"", "application/octet-stream", canonical_mime}:
            raise HTTPException(415, "MIME type does not match file extension")
        if upload.size is not None and upload.size > self.max_size:
            raise HTTPException(413, "File exceeds upload size limit")

        self.root.mkdir(parents=True, exist_ok=True)
        key = f"{uuid4().hex}{extension}"
        path = self.path_for(key)
        size = 0
        decoder = codecs.getincrementaldecoder("utf-8")() if extension == ".txt" else None
        # Exclusive creation never overwrites an existing file or follows a symlink.
        with path.open("xb") as target:
            try:
                upload.file.seek(0)
                while chunk := upload.file.read(CHUNK_SIZE):
                    size += len(chunk)
                    if size > self.max_size:
                        raise HTTPException(413, "File exceeds upload size limit")
                    if size == len(chunk) and extension == ".pdf" and not chunk.startswith(b"%PDF-"):
                        raise HTTPException(415, "File does not have a PDF header")
                    if decoder is not None:
                        if b"\x00" in chunk:
                            raise HTTPException(415, "TXT must contain UTF-8 text")
                        decoder.decode(chunk)
                    target.write(chunk)
                if size == 0:
                    raise HTTPException(400, "Empty file")
                if decoder is not None:
                    decoder.decode(b"", final=True)
                target.flush()
                if extension == ".docx":
                    self._validate_docx(path)
            except BaseException as exc:
                # Close before unlink for Windows compatibility.
                target.close()
                path.unlink(missing_ok=True)
                if isinstance(exc, UnicodeDecodeError):
                    raise HTTPException(415, "TXT must contain UTF-8 text") from None
                raise
        return StoredFile(name, key, extension[1:], canonical_mime, size)

    @staticmethod
    def _validate_docx(path: Path) -> None:
        try:
            with ZipFile(path) as archive:
                # Inspect names only; never extract/decompress untrusted entries.
                if not {"[Content_Types].xml", "word/document.xml"}.issubset(archive.namelist()):
                    raise HTTPException(415, "File does not have a DOCX container")
        except BadZipFile:
            raise HTTPException(415, "File does not have a DOCX container") from None

    def remove(self, key: str) -> None:
        self.path_for(key).unlink(missing_ok=True)

    def stage_delete(self, key: str) -> str | None:
        source = self.path_for(key)
        if not source.exists():
            return None
        staged_key = key + ".deleting"
        staged = self.path_for(staged_key)
        if staged.exists():
            raise OSError("Document deletion already pending")
        source.rename(staged)
        return staged_key

    def restore(self, staged_key: str, key: str) -> None:
        target = self.path_for(key)
        if target.exists():
            raise OSError("Cannot overwrite document during restore")
        self.path_for(staged_key).rename(target)
