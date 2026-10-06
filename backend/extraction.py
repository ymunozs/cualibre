"""Extracción de texto de PDF, DOCX, DOC y TXT (FR-001/003/004/082, research.md D5)."""

from __future__ import annotations

import io

import docx
import fitz  # PyMuPDF
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from . import legacy_doc, ocr
from .i18n import tr

# Una página con menos texto que esto y con imágenes se trata como escaneada
MIN_PAGE_TEXT = 25


class ExtractionError(Exception):
    """Error de extracción con mensaje apto para el usuario final."""

    def __init__(self, message: str, unsupported: bool = False):
        super().__init__(message)
        self.unsupported = unsupported


SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}


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
        elif ext in ("docx", "doc"):
            text = _extract_word(data, filename, ext)
        else:
            text = _extract_txt(data)
    except ExtractionError:
        raise
    except legacy_doc.LegacyDocError as exc:
        raise ExtractionError(str(exc)) from exc
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


def _extract_word(data: bytes, filename: str, ext: str) -> str:
    """Word en cualquiera de sus formatos. Manda el contenido y no la extensión:
    hay .doc que por dentro son .docx o RTF, y .docx antiguos renombrados."""
    kind = legacy_doc.sniff(data)
    if kind == "zip" or (kind == "unknown" and ext == "docx"):
        return _extract_docx(data)
    return legacy_doc.extract(data, filename)


def _extract_docx(data: bytes) -> str:
    """Párrafos Y tablas, en el orden en que aparecen: muchas transcripciones
    de entrevista vienen en tablas (hablante | intervención). Al final, las
    notas (al pie y finales) y los cuadros de texto, igual que en los .doc."""
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
    stories = ["\n".join(lines), _docx_notes(document, "footnotes"),
               _docx_notes(document, "endnotes"), _docx_textboxes(document)]
    return "\n\n".join(story for story in stories if story.strip())


_NOTE_SEPARATORS = ("separator", "continuationSeparator", "continuationNotice")
_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"


def _docx_notes(document, kind: str) -> str:
    """Notas al pie («footnotes») o finales («endnotes»): cada tipo vive en un
    archivo propio dentro del .docx."""
    for rel in document.part.rels.values():
        if rel.is_external or not rel.reltype.endswith("/" + kind):
            continue
        lines: list[str] = []
        for note in parse_xml(rel.target_part.blob):
            if note.get(qn("w:type")) in _NOTE_SEPARATORS:
                continue  # la raya que separa las notas del texto
            lines.extend(Paragraph(p, document).text for p in note.iter(qn("w:p")))
        return "\n".join(lines)
    return ""


def _docx_textboxes(document) -> str:
    lines: list[str] = []
    for box in document.element.body.iter(qn("w:txbxContent")):
        # Word guarda cada cuadro dos veces (formato actual + copia para
        # versiones antiguas): se lee una sola
        if any(ancestor.tag == _FALLBACK for ancestor in box.iterancestors()):
            continue
        lines.extend(Paragraph(p, document).text for p in box.iter(qn("w:p")))
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
