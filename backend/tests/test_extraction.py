"""Extracción PDF/DOCX/TXT con fixtures generadas (T015)."""

import io

import docx
import fitz
import pytest

from backend.extraction import ExtractionError, extract_text

SPANISH = "La emoción pedagógica: enseñanza, niñez y añoranza según Vygotski"


def make_pdf(text=SPANISH) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


def make_docx(text=SPANISH) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_txt_utf8():
    assert extract_text("notas.txt", SPANISH.encode("utf-8")) == SPANISH


def test_txt_latin1_fallback():
    text = extract_text("viejo.txt", "añejo".encode("latin-1"))
    assert "añejo" in text


def test_pdf():
    text = extract_text("paper.pdf", make_pdf())
    assert "añoranza" in text and "emoción" in text


def test_docx():
    text = extract_text("tesis.docx", make_docx())
    assert "Vygotski" in text and "niñez" in text


def test_unsupported_extension():
    with pytest.raises(ExtractionError, match="no soportado"):
        extract_text("imagen.png", b"\x89PNG")


def test_corrupt_pdf():
    with pytest.raises(ExtractionError, match="dañado o ilegible"):
        extract_text("roto.pdf", b"esto no es un pdf")


def test_pdf_without_text_layer():
    doc = fitz.open()
    doc.new_page()  # página en blanco: sin capa de texto
    with pytest.raises(ExtractionError, match="escaneado"):
        extract_text("escaneado.pdf", doc.tobytes())
