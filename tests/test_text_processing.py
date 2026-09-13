import unicodedata

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services.text_extraction import ProcessingError, extract_text
from app.services.text_normalization import normalize_text
from app.services.text_chunking import chunk_text


def test_txt_extraction_handles_bom_and_vietnamese(tmp_path):
    path = tmp_path / "law.txt"
    path.write_text("Điều 1. Phạm vi điều chỉnh", encoding="utf-8-sig")
    assert extract_text(path, "txt") == "Điều 1. Phạm vi điều chỉnh"


def test_invalid_utf8_is_a_safe_error(tmp_path):
    path = tmp_path / "private.txt"
    path.write_bytes(b"\xff")
    with pytest.raises(ProcessingError) as exc:
        extract_text(path, "txt")
    assert exc.value.message == "TXT is not valid UTF-8"
    assert str(path) not in str(exc.value)


def test_docx_extraction_preserves_paragraph_order(tmp_path, docx_bytes):
    path = tmp_path / "law.docx"
    path.write_bytes(docx_bytes)
    assert extract_text(path, "docx") == "Điều 1. Phạm vi điều chỉnh\n\nKhoản 2. Quyền và nghĩa vụ."


def test_pdf_extracts_pages_in_order(tmp_path, pdf_bytes):
    path = tmp_path / "law.pdf"
    path.write_bytes(pdf_bytes)
    text = extract_text(path, "pdf")
    assert text.index("Article 1. Scope.") < text.index("Article 2. Duties.")


def test_pdf_without_text_reports_no_ocr(tmp_path, blank_pdf_bytes):
    path = tmp_path / "scan.pdf"
    path.write_bytes(blank_pdf_bytes)
    with pytest.raises(ProcessingError, match="OCR is not supported"):
        extract_text(path, "pdf")


def test_conservative_normalization():
    source = "\ufeff  Điều 1.   Phạm vi\t điều chỉnh\r\n\r\n \r\nKhoản 2.  A; B!  \rDòng tiếp.\x00"
    expected = "Điều 1. Phạm vi điều chỉnh\n\nKhoản 2. A; B!\nDòng tiếp."
    assert normalize_text(unicodedata.normalize("NFD", source)) == expected
    assert normalize_text(expected) == expected
    assert normalize_text("Điều 1.\u2029Khoản 2.\u2028Dòng tiếp.") == "Điều 1.\n\nKhoản 2.\nDòng tiếp."


@pytest.mark.parametrize("text", ["", " \n\n\t "])
def test_chunking_never_returns_empty_chunks(text):
    assert chunk_text(text, 20, 5) == []


def test_chunking_prefers_paragraph_boundary():
    text = "A" * 30 + "\n\n" + "B" * 30 + "\n\n" + "C" * 30
    chunks = chunk_text(text, 80, 10)
    assert chunks[0].content == "A" * 30 + "\n\n" + "B" * 30
    assert chunks[-1].content.endswith("C" * 30)
    assert all(0 < chunk.char_count <= 80 for chunk in chunks)


def test_overlap_indexes_and_last_chunk():
    text = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chunks = chunk_text(text, 12, 4)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    for left, right in zip(chunks, chunks[1:]):
        assert left.content[-4:] == right.content[:4]
    assert chunks[-1].content.endswith("XYZ")
    assert all(chunk.char_count == len(chunk.content) for chunk in chunks)
    assert all(chunk.token_estimate == (len(chunk.content) + 3) // 4 for chunk in chunks)


def test_long_paragraph_splits_at_word_boundaries():
    text = " ".join(f"word{i}" for i in range(50))
    chunks = chunk_text(text, 50, 0)
    assert " ".join(chunk.content for chunk in chunks) == text


@pytest.mark.parametrize("size,overlap", [(0,0), (10,10), (10,11), (10,-1)])
def test_invalid_chunk_configuration(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("text", size, overlap)


@pytest.mark.parametrize("overrides", [
    {"chunk_size": 0}, {"chunk_overlap": -1},
    {"chunk_size": 200, "chunk_overlap": 200},
    {"chunk_size": 200, "chunk_overlap": 201},
])
def test_settings_validate_chunk_relationship(overrides):
    with pytest.raises(ValidationError):
        Settings(**overrides)
