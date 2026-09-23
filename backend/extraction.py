"""Extracción de texto de PDF, DOCX y TXT (FR-001/003/004, research.md D5)."""

from __future__ import annotations

import io

import docx
import fitz  # PyMuPDF
from docx.table import Table
from docx.text.paragraph import Paragraph

from . import ocr
from .i18n import tr

# Una página con menos texto que esto y con imágenes se trata como escaneada
MIN_PAGE_TEXT = 25


class ExtractionError(Exception):
    """Error de extracción con mensaje apto para el usuario final."""

    def __init__(self, message: str, unsupported: bool = False):
        super().__init__(message)
        self.unsupported = unsupported


SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt"}


def extract_text(filename: str, data: bytes, langs: list[str] | None = None) -> str:
    return extract_document(filename, data, langs)[0]


def extract_document(filename: str, data: bytes,
                     langs: list[str] | None = None) -> tuple[str, list[int]]:
    """Texto del archivo + páginas leídas por OCR (1 = primera).
    langs: idiomas probables del corpus, para orientar el OCR."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ExtractionError(tr("unsupported_file", ext=ext or "?"), unsupported=True)
    ocr_pages: list[int] = []
    try:
        if ext == "pdf":
            text, ocr_pages = _extract_pdf(data, langs or ["es"])
        elif ext == "docx":
            text = _extract_docx(data)
        else:
            text = _extract_txt(data)
    except ExtractionError:
        raise
    except ocr.OcrError as exc:
        raise ExtractionError(tr("ocr_failed", filename=filename, error=str(exc))) from exc
    except Exception as exc:
        raise ExtractionError(tr("unreadable_file", filename=filename)) from exc

    # Saltos de línea de Windows (\r\n) y del Mac clásico (\r) → \n: el Canvas
    # numera líneas y calcula offsets sobre \n.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        key = "no_text" if ocr.available() or ext != "pdf" else "no_text_no_ocr"
        raise ExtractionError(tr(key, filename=filename))
    return text, ocr_pages


def _extract_pdf(data: bytes, langs: list[str]) -> tuple[str, list[int]]:
    """Capa de texto de cada página; las páginas escaneadas (imagen sin texto)
    pasan por el OCR del sistema si está disponible (FR-080)."""
    pages: list[str] = []
    ocr_pages: list[int] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        use_ocr = ocr.available()
        for number, page in enumerate(doc, start=1):
            text = page.get_text()
            if use_ocr and len(text.strip()) < MIN_PAGE_TEXT and page.get_images():
                recognized = ocr.recognize_png(ocr.render_page_png(page), langs)
                if recognized.strip():
                    text = recognized + "\n"
                    ocr_pages.append(number)
            pages.append(text)
    return "\n".join(pages), ocr_pages


def _extract_docx(data: bytes) -> str:
    """Párrafos Y tablas, en el orden en que aparecen: muchas transcripciones
    de entrevista vienen en tablas (hablante | intervención)."""
    document = docx.Document(io.BytesIO(data))
    lines: list[str] = []
    for block in document.element.body.iterchildren():
        tag = block.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lines.append(Paragraph(block, document).text)
        elif tag == "tbl":
            for row in Table(block, document).rows:
                cells: list[str] = []
                for cell in row.cells:
                    value = cell.text.strip()
                    if value and (not cells or cells[-1] != value):  # celdas combinadas
                        cells.append(value)
                if cells:
                    lines.append(" | ".join(cells))
    return "\n".join(lines)


def _extract_txt(data: bytes) -> str:
    # utf-8-sig quita el BOM que agregan el Bloc de notas y Excel en Windows
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252")  # "ANSI" de Windows: comillas tipográficas, guiones
    except UnicodeDecodeError:
        return data.decode("latin-1")
