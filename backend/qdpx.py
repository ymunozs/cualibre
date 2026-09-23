"""Intercambio de proyectos con otros programas de análisis cualitativo (FR-079).

Formato REFI-QDA 1.0 (.qdpx), el estándar abierto que leen y escriben NVivo,
ATLAS.ti, MAXQDA, QualCoder y otros: un .zip con `project.qde` (XML, esquema
urn:QDA-XML:project:1.0) y la carpeta `sources/` con el texto de cada fuente.

Correspondencias Cua-libre → REFI-QDA
- Categorías (Básicas y propias) → códigos padre no codificables, con su color.
- Cada código (nombre + categoría) → código hijo codificable.
- Cada cita anclada → PlainTextSelection con su Coding. Posiciones en puntos
  de código Unicode desde 0 (sección 10.2 del estándar); fin exclusivo, como
  QualCoder. El Canvas trabaja en UTF-16: se convierte en ambos sentidos.
- Memo de una cita → Note (PlainTextContent) referida desde la selección.
- Código manual (sin cita) → código del libro con su memo en Description.
- Relaciones → Links entre códigos (dirección OneWay, nombre = tipo).

Posiciones: el estándar cuenta puntos de código con saltos de línea de un
carácter, pero NVivo para Windows cuenta unidades UTF-16 (un emoji vale 2) y
cada salto de línea como \r\n (2). Verificado con una exportación real de
NVivo 12.6: 97/97 citas exactas con su convención, 12/97 con la del estándar.
Por eso la importación DETECTA la convención de cada fuente (la que produce
cortes limpios en límites de palabra) y la exportación ofrece dos perfiles:
«standard» (ATLAS.ti, MAXQDA, QualCoder) y «nvivo» (texto con \r\n y
posiciones UTF-16).

REFI-QDA → Cua-libre
- TextSource (plainTextPath interno o PlainTextContent) y PDFSource con
  representación de texto → documentos. Imágenes, audio y video se omiten y
  se informa cuántos.
- El código de primer nivel de cada rama pasa a ser la categoría; los niveles
  intermedios se conservan como relaciones de jerarquía. Un código de primer
  nivel sin padre queda en la categoría propia «QDPX».
"""

from __future__ import annotations

import bisect
import io
import uuid
import zipfile
from datetime import datetime
from xml.etree import ElementTree as ET

from .i18n import DOMAIN_LABELS, domain_label
from .models import DOMAINS, Code, Document, Project, Relation, now_iso, utf16_len

NS = "urn:QDA-XML:project:1.0"
Q = "{%s}" % NS
IMPORT_CATEGORY = "QDPX"
IMPORT_COLOR = "#7A6F9B"
RELATION_NAMES = {"jerarquía": "jerarquía", "asociación": "asociación",
                  "causalidad": "causalidad", "contradicción": "contradicción"}


class QdpxError(Exception):
    """El archivo no es un proyecto REFI-QDA legible."""


def _guid() -> str:
    return str(uuid.uuid4()).upper()


# Convenciones de posición: (unidades por salto de línea, unidades por carácter fuera del BMP)
CONVENTIONS = {"standard": (1, 1), "nvivo": (2, 2), "utf16": (1, 2), "crlf": (2, 1)}


class Positions:
    """Traduce entre índices de Python (puntos de código) y las unidades de
    una convención de posiciones, para UN texto."""

    def __init__(self, text: str, newline_units: int = 1, astral_units: int = 1):
        self.text = text
        self.units: list[int] = []  # unidad acumulada al inicio de cada carácter
        total = 0
        for char in text:
            self.units.append(total)
            total += newline_units if char == "\n" else (astral_units if ord(char) > 0xFFFF else 1)
        self.units.append(total)

    def to_cp(self, unit: int) -> int:
        return min(len(self.text), bisect.bisect_left(self.units, unit))

    def to_units(self, cp: int) -> int:
        return self.units[max(0, min(cp, len(self.text)))]


def _clean_cut(text: str, start: int, end: int) -> bool:
    """¿La cita empieza y termina en un límite de palabra o de línea?"""
    return (start == 0 or not text[start - 1].isalnum() or not text[start].isalnum()) and \
        (end >= len(text) or not text[end].isalnum() or not text[end - 1].isalnum())


def detect_convention(text: str, spans: list[tuple[int, int]]) -> str:
    """Convención cuyas posiciones cortan mejor el texto (empate → estándar)."""
    sample = spans[:300]
    best, best_score = "standard", -1
    for name, (nl, astral) in CONVENTIONS.items():
        if (nl > 1 and "\n" not in text) or (astral > 1 and len(text) == utf16_len(text)):
            continue  # indistinguible del estándar para este texto
        positions = Positions(text, nl, astral)
        score = sum(1 for s, e in sample
                    if positions.to_cp(e) > positions.to_cp(s)
                    and _clean_cut(text, positions.to_cp(s), positions.to_cp(e)))
        if score > best_score:
            best, best_score = name, score
    return best


def _u16_to_cp(text: str, unit: int) -> int:
    from .analysis import OffsetMap

    return OffsetMap(text).to_cp(unit)


def _stamp(value: str | None) -> str:
    """Fecha ISO local de Cua-libre → xsd:dateTime."""
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%dT%H:%M:%S") if value else ""
    except ValueError:
        return ""


# ----- Exportar -----

def export_qdpx(project: Project, user_name: str = "Cua-libre", profile: str = "standard") -> bytes:
    """profile: «standard» (estándar REFI-QDA) o «nvivo» (convención de NVivo)."""
    ET.register_namespace("", NS)
    nvivo = profile == "nvivo"
    user_guid = _guid()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    root = ET.Element(Q + "Project", {
        "name": project.name, "origin": "CUA-LIBRE STUDIO",
        "creatingUserGUID": user_guid, "creationDateTime": now,
    })
    users = ET.SubElement(root, Q + "Users")
    ET.SubElement(users, Q + "User", {"guid": user_guid, "name": user_name})

    colors = {**DOMAINS, **project.custom_domains}
    # Libro de códigos: categoría → códigos (nombre) con su color
    tree: dict[str, dict[str, list[Code]]] = {}
    for code in project.codes:
        tree.setdefault(code.domain, {}).setdefault(code.name, []).append(code)
    for domain in project.custom_domains:  # las categorías propias, aunque estén vacías
        tree.setdefault(domain, {})
    code_guid: dict[tuple[str, str], str] = {}
    first_guid_by_name: dict[str, str] = {}
    codebook = ET.SubElement(root, Q + "CodeBook")
    codes_el = ET.SubElement(codebook, Q + "Codes")
    for domain, by_name in tree.items():
        color = colors.get(domain, "#999999")
        parent = ET.SubElement(codes_el, Q + "Code", {  # etiqueta en el idioma de la interfaz
            "guid": _guid(), "name": domain_label(domain), "isCodable": "false", "color": color})
        for name, instances in by_name.items():
            guid = _guid()
            code_guid[(domain, name)] = guid
            first_guid_by_name.setdefault(name, guid)
            child = ET.SubElement(parent, Q + "Code", {
                "guid": guid, "name": name, "isCodable": "true", "color": color})
            manual_memos = [c.memo for c in instances if not c.doc_id and c.memo]
            if manual_memos:
                ET.SubElement(child, Q + "Description").text = "\n\n".join(manual_memos)

    notes: list[tuple[str, str, str]] = []  # (guid, texto, fecha)
    files: dict[str, bytes] = {}
    sources = ET.SubElement(root, Q + "Sources") if project.documents else None
    for doc in project.documents:
        file_guid = _guid()
        # NVivo espera saltos de línea de Windows y cuenta cada uno como 2
        files[f"sources/{file_guid}.txt"] = (doc.text.replace("\n", "\r\n") if nvivo
                                             else doc.text).encode("utf-8")
        positions = Positions(doc.text, *CONVENTIONS[profile if nvivo else "standard"])
        source = ET.SubElement(sources, Q + "TextSource", {
            "guid": _guid(), "name": doc.filename,
            "plainTextPath": f"internal://{file_guid}.txt",
            "creatingUser": user_guid, "creationDateTime": _stamp(doc.imported_at) or now,
        })
        for code in project.codes:
            if code.doc_id != doc.id or code.start is None:
                continue
            start = positions.to_units(_u16_to_cp(doc.text, code.start))
            end = positions.to_units(_u16_to_cp(doc.text, code.end))
            created = _stamp(code.created_at) or now
            selection = ET.SubElement(source, Q + "PlainTextSelection", {
                "guid": _guid(), "name": code.quote[:60],
                "startPosition": str(start), "endPosition": str(end),
                "creatingUser": user_guid, "creationDateTime": created,
            })
            coding = ET.SubElement(selection, Q + "Coding", {
                "guid": _guid(), "creatingUser": user_guid, "creationDateTime": created})
            ET.SubElement(coding, Q + "CodeRef", {"targetGUID": code_guid[(code.domain, code.name)]})
            if code.memo:
                note_guid = _guid()
                notes.append((note_guid, code.memo, created))
                ET.SubElement(selection, Q + "NoteRef", {"targetGUID": note_guid})

    if notes:
        notes_el = ET.SubElement(root, Q + "Notes")
        for guid, text, created in notes:
            note = ET.SubElement(notes_el, Q + "Note", {
                "guid": guid, "name": "Memo", "creatingUser": user_guid, "creationDateTime": created})
            ET.SubElement(note, Q + "PlainTextContent").text = text

    links = [r for r in project.relations
             if r.source in first_guid_by_name and r.target in first_guid_by_name]
    if links:
        links_el = ET.SubElement(root, Q + "Links")
        for relation in links:
            ET.SubElement(links_el, Q + "Link", {
                "guid": _guid(), "name": relation.type, "direction": "OneWay",
                "originGUID": first_guid_by_name[relation.source],
                "targetGUID": first_guid_by_name[relation.target],
            })

    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.qde", xml)
        for path, data in files.items():
            zf.writestr(path, data)
    return buffer.getvalue()


# ----- Importar -----

def _normalize_newlines(doc: Document, codes: list[Code]) -> None:
    """\r\n y \r → \n (el Canvas trabaja con \n), trasladando las citas ya ancladas."""
    from .analysis import OffsetMap

    old = doc.text
    old_u16 = OffsetMap(old)
    removed_before = []  # cuántos \r quedan eliminados antes de cada punto de código
    count = 0
    for index, char in enumerate(old):
        removed_before.append(count)
        if char == "\r" and index + 1 < len(old) and old[index + 1] == "\n":
            count += 1
    removed_before.append(count)
    new = old.replace("\r\n", "\n").replace("\r", "\n")
    new_u16 = OffsetMap(new)
    for code in codes:
        for attr in ("start", "end"):
            cp = old_u16.to_cp(getattr(code, attr))
            setattr(code, attr, new_u16.to_utf16(cp - removed_before[cp]))
        code.quote = code.quote.replace("\r\n", "\n").replace("\r", "\n")
    doc.text = new


def is_qdpx(data: bytes) -> bool:
    if data[:2] != b"PK":
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return any(n.lower().endswith(".qde") for n in zf.namelist())
    except zipfile.BadZipFile:
        return False


def _basic_domain(name: str) -> str | None:
    """¿El nombre corresponde a una Categoría Básica (en cualquier idioma)?"""
    lowered = name.strip().lower()
    for key, labels in DOMAIN_LABELS.items():
        if lowered in {key.lower(), *(label.lower() for label in labels.values())}:
            return key
    return None


def import_qdpx(data: bytes, fallback_name: str = "QDPX") -> tuple[Project, dict]:
    """Proyecto Cua-libre desde un .qdpx + informe de lo que no se pudo traer."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        qde_name = next(n for n in zf.namelist() if n.lower().endswith(".qde"))
        root = ET.fromstring(zf.read(qde_name))
    except (zipfile.BadZipFile, StopIteration, ET.ParseError) as exc:
        raise QdpxError(str(exc)) from exc
    if root.tag != Q + "Project":
        raise QdpxError("no es un proyecto QDA-XML 1.0")

    def read_internal(path: str | None) -> str | None:
        if not path or not path.startswith("internal://"):
            return None
        target = path[len("internal://"):].lower()
        for name in zf.namelist():
            if name.lower().endswith("sources/" + target) or name.lower() == target:
                raw = zf.read(name)
                for encoding in ("utf-8-sig", "utf-16", "cp1252"):
                    try:
                        return raw.decode(encoding)
                    except UnicodeDecodeError:
                        continue
        return None

    project = Project(name=root.get("name") or fallback_name)
    report = {"sources": 0, "skipped_sources": 0, "selections": 0, "skipped_selections": 0,
              "codes": 0, "relations": 0, "conventions": set(), "origin": root.get("origin", "")}

    # Libro de códigos: guid → (nombre, categoría, color); jerarquía intermedia → relaciones
    codes: dict[str, dict] = {}
    hierarchy: list[tuple[str, str]] = []

    def walk(element, top: tuple[str, str] | None, parent_name: str | None):
        for code_el in element.findall(Q + "Code"):
            name = (code_el.get("name") or "").strip() or "?"
            color = (code_el.get("color") or "").upper()
            if len(color) == 4:  # #RGB → #RRGGBB
                color = "#" + "".join(ch * 2 for ch in color[1:])
            description = (code_el.findtext(Q + "Description") or "").strip()
            if top is None:
                domain_key = _basic_domain(name)
                branch = (domain_key or name, color or IMPORT_COLOR)
                has_children = bool(code_el.findall(Q + "Code"))
                if not has_children and code_el.get("isCodable") == "false":
                    # Categoría vacía: se conserva como categoría, no como código
                    if not domain_key:
                        project.custom_domains.setdefault(name, color or IMPORT_COLOR)
                    continue
                if not domain_key and has_children:
                    project.custom_domains.setdefault(name, color or IMPORT_COLOR)
                codes[code_el.get("guid", "").upper()] = {
                    "name": name, "domain": branch[0] if code_el.findall(Q + "Code") else None,
                    "color": color, "description": description, "top": True}
                walk(code_el, branch, name)
            else:
                codes[code_el.get("guid", "").upper()] = {
                    "name": name, "domain": top[0], "color": color,
                    "description": description, "top": False}
                if parent_name and parent_name != top[0]:
                    hierarchy.append((parent_name, name))
                walk(code_el, top, name)

    codebook = root.find(Q + "CodeBook/" + Q + "Codes")
    if codebook is not None:
        walk(codebook, None, None)
    # Códigos de primer nivel sin hijos: van a la categoría propia «QDPX»
    for info in codes.values():
        if info["top"] and info["domain"] is None:
            info["domain"] = IMPORT_CATEGORY
            project.custom_domains.setdefault(IMPORT_CATEGORY, IMPORT_COLOR)

    notes = {n.get("guid", "").upper(): (n.findtext(Q + "PlainTextContent") or "").strip()
             for n in root.iter(Q + "Note")}
    used_codes: set[str] = set()

    def add_selections(doc: Document, container) -> None:
        from .analysis import OffsetMap

        raw = []
        for selection in container.findall(Q + "PlainTextSelection"):
            try:
                raw.append((selection, int(selection.get("startPosition")),
                            int(selection.get("endPosition"))))
            except (TypeError, ValueError):
                report["skipped_selections"] += 1
        convention = detect_convention(doc.text, [(s, e) for _, s, e in raw])
        report["conventions"].add(convention)
        positions = Positions(doc.text, *CONVENTIONS[convention])
        u16 = OffsetMap(doc.text)
        for selection, start_units, end_units in raw:
            start_cp = positions.to_cp(max(0, start_units))
            end_cp = positions.to_cp(end_units)
            if end_cp <= start_cp:
                report["skipped_selections"] += 1
                continue
            memo_parts = [(selection.findtext(Q + "Description") or "").strip()]
            memo_parts += [notes.get(ref.get("targetGUID", "").upper(), "")
                           for ref in selection.findall(Q + "NoteRef")]
            memo = "\n\n".join(p for p in memo_parts if p)
            codings = selection.findall(Q + "Coding")
            if not codings:
                report["skipped_selections"] += 1
                continue
            for coding in codings:
                ref = coding.find(Q + "CodeRef")
                info = codes.get((ref.get("targetGUID") if ref is not None else "").upper())
                if info is None:
                    report["skipped_selections"] += 1
                    continue
                used_codes.add(info["name"])
                project.codes.append(Code(
                    id=project.next_code_id, doc_id=doc.id, domain=info["domain"],
                    name=info["name"], quote=doc.text[start_cp:end_cp],
                    start=u16.to_utf16(start_cp), end=u16.to_utf16(end_cp),
                    memo=memo, created_at=(selection.get("creationDateTime") or "")[:19] or now_iso(),
                ))
                project.next_code_id += 1
                report["selections"] += 1

    sources = root.find(Q + "Sources")
    for source in list(sources) if sources is not None else []:
        kind = source.tag.replace(Q, "")
        text = None
        container = source
        if kind == "TextSource":
            text = source.findtext(Q + "PlainTextContent")
            if text is None:
                text = read_internal(source.get("plainTextPath"))
        elif kind == "PDFSource":
            representation = source.find(Q + "Representation")
            if representation is not None:
                text = representation.findtext(Q + "PlainTextContent") or \
                    read_internal(representation.get("plainTextPath"))
                container = representation
        if not text:
            report["skipped_sources"] += 1
            continue
        doc = Document(filename=source.get("name") or f"{kind}.txt", text=text)
        project.documents.append(doc)
        report["sources"] += 1
        before = len(project.codes)
        add_selections(doc, container)
        if "\r" in doc.text:
            _normalize_newlines(doc, project.codes[before:])

    # Códigos del libro sin citas → códigos manuales (conservan su descripción)
    for info in codes.values():
        is_parent_category = info["top"] and info["domain"] != IMPORT_CATEGORY \
            and info["domain"] in (project.custom_domains | DOMAINS)
        if info["name"] in used_codes or is_parent_category:
            continue
        project.codes.append(Code(id=project.next_code_id, doc_id=None, domain=info["domain"],
                                  name=info["name"], memo=info["description"]))
        project.next_code_id += 1
    report["codes"] = len({c.name for c in project.codes})

    # Descripciones del libro en la primera cita de cada código sin memo
    for info in codes.values():
        if not info["description"]:
            continue
        first = next((c for c in project.codes if c.name == info["name"] and c.doc_id), None)
        if first is not None and not first.memo:
            first.memo = info["description"]

    names = {c.name for c in project.codes}
    by_guid = {guid: info["name"] for guid, info in codes.items()}
    links = root.find(Q + "Links")
    candidates = [(parent, child, "jerarquía") for parent, child in hierarchy]
    for link in list(links) if links is not None else []:
        source_name = by_guid.get((link.get("originGUID") or "").upper())
        target_name = by_guid.get((link.get("targetGUID") or "").upper())
        kind = RELATION_NAMES.get((link.get("name") or "").strip().lower(), "asociación")
        candidates.append((source_name, target_name, kind))
    seen = set()
    for source_name, target_name, kind in candidates:
        key = (source_name, target_name, kind)
        if source_name in names and target_name in names and source_name != target_name \
                and key not in seen:
            seen.add(key)
            project.relations.append(Relation(id=project.next_relation_id, source=source_name,
                                              target=target_name, type=kind))
            project.next_relation_id += 1
    report["relations"] = len(project.relations)
    report["conventions"] = sorted(report["conventions"])
    return project, report
