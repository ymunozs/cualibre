"""Biblioteca de literatura (FR-089..092): común a todos los proyectos.

- Archivos en <datos>/biblioteca/archivos/ (copias: el original de la persona no
  se toca), texto extraído en <datos>/biblioteca/textos/, y fichas y anotaciones
  de lectura en <datos>/biblioteca/biblioteca.json (escritura atómica, como los
  proyectos). Un documento eliminado se mueve a <datos>/biblioteca/papelera/.
- Metadatos: el DOI se busca en el propio documento y se consulta Crossref (y
  OpenAlex si Crossref no responde). Es opcional: sin internet, la ficha se
  completa a mano.
- Referencias en APA 7, BibTeX y RIS, sin dependencias externas.
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
from pathlib import Path
from typing import Optional

import httpx

from . import storage
from .i18n import tr
from .models import LibraryItem, Library, LitMeta, Person

USER_AGENT = "CUA-LIBRE-Studio/2.0 (https://github.com/ymunozs/cualibre)"
TIMEOUT = 8.0


# ----- Almacenamiento -----

def library_dir() -> Path:
    d = storage.base_dir() / "biblioteca"
    for sub in ("archivos", "textos", "papelera"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def _json_path() -> Path:
    return library_dir() / "biblioteca.json"


_lock = threading.Lock()
_cache: dict[str, tuple[int, int, Library]] = {}


def load() -> Library:
    path = _json_path()
    if not path.exists():
        return Library()
    st = path.stat()
    stamp = (st.st_mtime_ns, st.st_size)
    with _lock:
        cached = _cache.get(str(path))
        if cached and cached[:2] == stamp:
            return cached[2]
    library = Library.model_validate_json(path.read_bytes())
    with _lock:
        _cache[str(path)] = (*stamp, library)
    return library


def save(library: Library) -> None:
    path = _json_path()
    storage._atomic_write(path, library.model_dump_json(indent=1))
    st = path.stat()
    with _lock:
        _cache[str(path)] = (st.st_mtime_ns, st.st_size, library)


def invalidate() -> None:
    with _lock:
        _cache.clear()


def _safe_id(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{32}", value or ""))


def file_path(item: LibraryItem) -> Optional[Path]:
    """Ruta del archivo guardado (nunca fuera de la carpeta: sin traversal)."""
    if not item.file or item.file != Path(item.file).name:
        return None
    path = library_dir() / "archivos" / item.file
    return path if path.is_file() else None


def text_path(item_id: str) -> Optional[Path]:
    if not _safe_id(item_id):
        return None
    return library_dir() / "textos" / f"{item_id}.txt"


def read_text(item_id: str) -> str:
    path = text_path(item_id)
    try:
        return path.read_text(encoding="utf-8") if path else ""
    except FileNotFoundError:
        return ""


def store_file(item: LibraryItem, data: bytes, extension: str) -> None:
    item.file = f"{item.id}{extension}"
    storage._atomic_write(library_dir() / "archivos" / item.file, data)


def store_text(item_id: str, text: str) -> None:
    path = text_path(item_id)
    if path:
        storage._atomic_write(path, text)


def trash_files(item: LibraryItem) -> None:
    """Mueve archivo y texto a la papelera de la biblioteca (Principio V)."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    trash = library_dir() / "papelera"
    source = file_path(item)
    if source:
        storage._replace_with_retry(str(source), trash / f"{stamp}-{item.file}")
    text = text_path(item.id)
    if text and text.exists():
        storage._replace_with_retry(str(text), trash / f"{stamp}-{item.id}.txt")


def pdf_text(data: bytes) -> tuple[str, int, dict]:
    """Capa de texto, páginas y metadatos de un PDF, SIN OCR: en la biblioteca
    el texto solo sirve para hallar el DOI, y el OCR de un libro escaneado
    tomaría minutos (el lector muestra la imagen igual)."""
    import fitz

    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
            return text, doc.page_count, dict(doc.metadata or {})
    except Exception:
        return "", 0, {}


def sort_key(meta: LitMeta) -> tuple:
    """Orden alfabético de la lista de referencias, sin que las tildes la
    alteren («Álvarez» antes que «Zúñiga»)."""
    import unicodedata

    def plain(text: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", text or "")
                       if not unicodedata.combining(c)).casefold()

    first = meta.authors[0].family if meta.authors else meta.title
    return (plain(first), meta.year, plain(meta.title))


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


# ----- DOI y metadatos -----

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)


def find_doi(text: str) -> str:
    """Primer DOI del texto (sin la puntuación que suele pegarse al final)."""
    match = DOI_RE.search(text or "")
    if not match:
        return ""
    return match.group(1).rstrip(".,;:)]}>'\"").strip()


def normalize_doi(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def _http_get(url: str, params: dict | None = None) -> dict:
    """GET con tiempo límite; aislado para poder reemplazarlo en los tests."""
    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT},
                      follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


CROSSREF_TYPES = {"journal-article": "article", "book": "book", "monograph": "book",
                  "edited-book": "book", "reference-book": "book", "book-chapter": "chapter",
                  "book-section": "chapter", "book-part": "chapter", "dissertation": "thesis",
                  "report": "report", "posted-content": "other"}


def _persons(entries) -> list[Person]:
    out = []
    for e in entries or []:
        if e.get("family"):
            out.append(Person(family=e["family"].strip(), given=(e.get("given") or "").strip()))
        elif e.get("name"):  # autor institucional
            out.append(Person(family=e["name"].strip()))
    return out


def _clean(text: str) -> str:
    """Crossref entrega a veces entidades y etiquetas HTML («Quality &amp;
    Quantity», «<i>Homo</i> sapiens»): texto plano, sin espacios dobles."""
    import html

    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def _from_crossref(message: dict) -> LitMeta:
    date = (message.get("issued") or message.get("published-print")
            or message.get("published-online") or {}).get("date-parts") or [[None]]
    year = str(date[0][0]) if date and date[0] and date[0][0] else ""
    first = lambda key: (message.get(key) or [""])[0] if isinstance(message.get(key), list) else (message.get(key) or "")
    title = _clean(first("title"))
    subtitle = _clean(first("subtitle"))
    if subtitle and subtitle.lower() not in title.lower():  # APA: «Título: Subtítulo»
        # …salvo que el título termine en ? o !: «Are Enough? An Experiment…»
        joiner = " " if title.rstrip().endswith(("?", "!")) else ": "
        title = f"{title.rstrip(':').rstrip()}{joiner}{subtitle}"
    return LitMeta(
        type=CROSSREF_TYPES.get(message.get("type", ""), "other"),
        title=title,
        authors=_persons(message.get("author")),
        editors=_persons(message.get("editor")),
        year=year,
        container=_clean(first("container-title")),
        volume=str(message.get("volume") or ""),
        issue=str(message.get("issue") or ""),
        pages=str(message.get("page") or "").replace("-", "–"),
        publisher=_clean(message.get("publisher") or ""),
        doi=message.get("DOI") or "",
        url="",
        isbn=first("ISBN"),
    )


OPENALEX_TYPES = {"article": "article", "book": "book", "book-chapter": "chapter",
                  "dissertation": "thesis", "report": "report"}


def _from_openalex(work: dict) -> LitMeta:
    authors = []
    for a in work.get("authorships") or []:
        name = ((a.get("author") or {}).get("display_name") or "").strip()
        if not name:
            continue
        parts = name.rsplit(" ", 1)
        authors.append(Person(family=parts[-1], given=parts[0] if len(parts) > 1 else ""))
    biblio = work.get("biblio") or {}
    pages = "–".join(p for p in (biblio.get("first_page"), biblio.get("last_page")) if p)
    source = ((work.get("primary_location") or {}).get("source") or {})
    return LitMeta(
        type=OPENALEX_TYPES.get(work.get("type", ""), "other"),
        title=work.get("display_name") or "",
        authors=authors,
        year=str(work.get("publication_year") or ""),
        container=source.get("display_name") or "",
        volume=str(biblio.get("volume") or ""),
        issue=str(biblio.get("issue") or ""),
        pages=pages,
        publisher=source.get("host_organization_name") or "",
        doi=normalize_doi(work.get("doi") or ""),
    )


def lookup_doi(doi: str) -> Optional[LitMeta]:
    """Metadatos de un DOI: Crossref primero, OpenAlex si falla; None sin red."""
    doi = normalize_doi(doi)
    if not doi:
        return None
    try:
        return _from_crossref(_http_get(f"https://api.crossref.org/works/{doi}")["message"])
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        pass
    try:
        return _from_openalex(_http_get(f"https://api.openalex.org/works/doi:{doi}"))
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return None


# ----- Referencias: APA 7, BibTeX, RIS -----

TERMS = {
    "es": {"nd": "s. f.", "in": "En", "ed": "Ed.", "eds": "Eds.", "pp": "pp.", "thesis": "Tesis"},
    "en": {"nd": "n.d.", "in": "In", "ed": "Ed.", "eds": "Eds.", "pp": "pp.", "thesis": "Thesis"},
    "pt": {"nd": "s.d.", "in": "In", "ed": "Ed.", "eds": "Eds.", "pp": "pp.", "thesis": "Tese"},
}


def _initials(given: str) -> str:
    """«Kathleen M.» → «K. M.»; «Jean-Paul» → «J.-P.»; «María José» → «M. J.»."""
    out = []
    for word in given.replace(".", ". ").split():
        if not word.strip("."):
            continue
        parts = [p for p in word.split("-") if p.strip(".")]
        out.append("-".join(p.strip(".")[0].upper() + "." for p in parts))
    return " ".join(out)


def _person_apa(p: Person) -> str:
    return f"{p.family}, {_initials(p.given)}" if p.given.strip() else p.family


def _people_apa(people: list[Person]) -> str:
    names = [_person_apa(p) for p in people if p.family.strip()]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) <= 20:
        return ", ".join(names[:-1]) + ", & " + names[-1]
    return ", ".join(names[:19]) + ", . . . " + names[-1]  # APA 7: 19 primeros, … y el último


def _editors_apa(people: list[Person]) -> str:
    names = [(f"{_initials(p.given)} {p.family}" if p.given.strip() else p.family)
             for p in people if p.family.strip()]
    if len(names) <= 1:
        return names[0] if names else ""
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return ", ".join(names[:-1]) + ", & " + names[-1]


def _end(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "?", "!")) else text + "."


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def apa(meta: LitMeta, lang: str = "es", html: bool = True) -> str:
    """Referencia en APA 7. Los títulos se respetan tal cual (no se cambia la
    capitalización automáticamente: es una decisión de quien escribe)."""
    t = TERMS.get(lang, TERMS["es"])
    e = _esc if html else (lambda s: s)
    ital = (lambda s: f"<em>{e(s)}</em>") if html else (lambda s: s)
    year = f"({e(meta.year) or t['nd']})."
    authors = _people_apa(meta.authors)
    title = meta.title.strip() or "?"
    tail = []
    if meta.doi:
        tail.append(f"https://doi.org/{e(normalize_doi(meta.doi))}")
    elif meta.url:
        tail.append(e(meta.url))

    if meta.type == "article":
        title_part = e(_end(title))
        source = ""
        if meta.container:
            source = ital(meta.container)
            if meta.volume:
                source += ", " + ital(meta.volume)
                if meta.issue:
                    source += f"({e(meta.issue)})"
            elif meta.issue:
                source += f", ({e(meta.issue)})"
            if meta.pages:
                source += f", {e(meta.pages)}"
            source += "."
        body = [title_part, source]
    elif meta.type == "chapter":
        editors = _editors_apa(meta.editors)
        ed = f" ({t['eds'] if len(meta.editors) > 1 else t['ed']})" if editors else ""
        book = ital(meta.container) if meta.container else ""
        pages = f" ({t['pp']} {e(meta.pages)})" if meta.pages else ""
        where = f"{t['in']} {e(editors)}{ed}, " if editors else f"{t['in']} "
        body = [e(_end(title)), f"{where}{book}{pages}." if book else "",
                e(_end(meta.publisher)) if meta.publisher else ""]
    else:  # libro, tesis, informe, otro: título en cursiva
        title_html = ital(title) + ("" if title.endswith(("?", "!")) else ".")
        body = [title_html, e(_end(meta.publisher)) if meta.publisher else ""]

    if authors:
        parts = [e(_end(authors)) if not authors.endswith(".") else e(authors), year]
    else:  # sin autor: el título pasa al lugar del autor
        parts = [body.pop(0), year]
    parts += [b for b in body if b] + tail
    return " ".join(p for p in parts if p).strip()


BIBTEX_TYPES = {"article": "article", "book": "book", "chapter": "incollection",
                "thesis": "phdthesis", "report": "techreport", "other": "misc"}
RIS_TYPES = {"article": "JOUR", "book": "BOOK", "chapter": "CHAP", "thesis": "THES",
             "report": "RPRT", "other": "GEN"}


def _bib_key(meta: LitMeta, taken: set[str]) -> str:
    base = meta.authors[0].family if meta.authors else (meta.title.split() or ["ref"])[0]
    base = re.sub(r"[^A-Za-z0-9]", "", base.encode("ascii", "ignore").decode()) or "ref"
    word = re.sub(r"[^A-Za-z]", "", (meta.title.split() or [""])[0].encode("ascii", "ignore").decode())
    key = f"{base}{meta.year}{word}".lower() or "ref"
    unique, n = key, 1
    while unique in taken:
        n += 1
        unique = f"{key}{n}"
    taken.add(unique)
    return unique


def bibtex(metas: list[LitMeta]) -> str:
    clean = lambda s: (s or "").replace("{", "").replace("}", "")
    taken: set[str] = set()
    out = []
    for meta in metas:
        fields = {
            "author": " and ".join(f"{clean(p.family)}, {clean(p.given)}".rstrip(", ")
                                   for p in meta.authors),
            "editor": " and ".join(f"{clean(p.family)}, {clean(p.given)}".rstrip(", ")
                                   for p in meta.editors),
            "title": clean(meta.title),
            ("journal" if meta.type == "article" else "booktitle"): clean(meta.container),
            "year": clean(meta.year), "volume": clean(meta.volume), "number": clean(meta.issue),
            "pages": clean(meta.pages).replace("–", "--"), "publisher": clean(meta.publisher),
            "doi": normalize_doi(meta.doi), "url": clean(meta.url), "isbn": clean(meta.isbn),
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        out.append(f"@{BIBTEX_TYPES.get(meta.type, 'misc')}{{{_bib_key(meta, taken)},\n{body}\n}}")
    return "\n\n".join(out) + "\n"


def ris(metas: list[LitMeta]) -> str:
    out = []
    for meta in metas:
        lines = [f"TY  - {RIS_TYPES.get(meta.type, 'GEN')}"]
        lines += [f"AU  - {p.family}, {p.given}".rstrip(", ") for p in meta.authors]
        lines += [f"ED  - {p.family}, {p.given}".rstrip(", ") for p in meta.editors]
        pairs = [("TI", meta.title), ("T2", meta.container), ("PY", meta.year),
                 ("VL", meta.volume), ("IS", meta.issue), ("PB", meta.publisher),
                 ("DO", normalize_doi(meta.doi)), ("UR", meta.url), ("SN", meta.isbn)]
        if meta.pages:
            first, _, last = meta.pages.replace("–", "-").partition("-")
            pairs += [("SP", first.strip()), ("EP", last.strip())]
        lines += [f"{tag}  - {value}" for tag, value in pairs if value]
        lines.append("ER  - ")
        out.append("\r\n".join(lines))
    return "\r\n\r\n".join(out) + "\r\n"


def short_cite(meta: LitMeta, lang: str = "es") -> str:
    """Cita breve para el cuaderno de lectura y el libro de códigos: (Apellido, año)."""
    t = TERMS.get(lang, TERMS["es"])
    names = [p.family for p in meta.authors if p.family]
    if not names:
        who = meta.title[:40] or "?"
    elif len(names) == 1:
        who = names[0]
    elif len(names) == 2:
        who = f"{names[0]} & {names[1]}"
    else:
        who = f"{names[0]} et al."
    return f"{who}, {meta.year or t['nd']}"
