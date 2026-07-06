"""Extracción de texto de PDF, DOCX y TXT (FR-001/003/004, research.md D5)."""

from __future__ import annotations

import io

import docx
import fitz  # PyMuPDF


class ExtractionError(Exception):
    """Error de extracción con mensaje apto para el usuario final."""


SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt"}


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ExtractionError(
            f"Tipo de archivo no soportado: .{ext or '?'} — usa PDF, DOCX o TXT"
        )
    try:
        if ext == "pdf":
            text = _extract_pdf(data)
        elif ext == "docx":
            text = _extract_docx(data)
        else:
            text = _extract_txt(data)
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"No se pudo leer «{filename}»: archivo dañado o ilegible") from exc

    if not text.strip():
        raise ExtractionError(
            f"«{filename}» no contiene texto extraíble (¿PDF escaneado sin capa de texto?)"
        )
    return text


def _extract_pdf(data: bytes) -> str:
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def _extract_docx(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)


def _extract_txt(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")
