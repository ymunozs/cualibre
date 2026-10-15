"""Exportación CSV (FR-021/022) y respaldo completo en .zip (FR-070).

Encabezados, nombres de archivo y etiquetas de las Categorías Básicas salen en
el idioma de la interfaz; proyecto.json conserva siempre los datos tal cual
(claves internas), para que el respaldo se pueda reimportar en cualquier idioma.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime

from .i18n import domain_label, tr
from .models import DOMAINS, CodebookEntry, Project


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_. " else "_" for c in name).strip() or "documento"


def project_to_csv(project: Project) -> bytes:
    doc_names = {d.id: d.filename for d in project.documents}
    manual = tr("manual_origin")
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(tr("csv_columns").split("|"))
    for code in project.codes:
        writer.writerow([
            code.id,
            code.created_at,
            doc_names.get(code.doc_id, manual) if code.doc_id else manual,
            domain_label(code.domain),
            code.name,
            code.quote,
            code.memo,
        ])
    # BOM U+FEFF: Excel solo reconoce UTF-8 si el archivo abre con él
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def codebook_rows(project: Project) -> list[dict]:
    """Libro de códigos completo (FR-084): cada categoría en uso o descrita y
    cada código del banco, con su descripción (vacía si aún no se escribe).
    Las descripciones de códigos que ya no tienen citas se conservan al final:
    nunca se pierde texto escrito por el investigador."""
    quotes: dict[str, int] = {}
    categories_of: dict[str, list[str]] = {}
    for code in project.codes:
        if code.doc_id:
            quotes[code.name] = quotes.get(code.name, 0) + 1
        domains = categories_of.setdefault(code.name, [])
        if code.domain not in domains:
            domains.append(code.domain)
    in_use = {c.domain for c in project.codes}
    category_keys = [k for k in [*DOMAINS, *project.custom_domains]
                     if k in in_use or k in project.category_notes]
    category_keys += [k for k in project.category_notes if k not in category_keys]
    rows = []
    for key in category_keys:
        entry = project.category_notes.get(key) or CodebookEntry()
        n = sum(1 for c in project.codes if c.domain == key and c.doc_id)
        rows.append({"kind": "category", "name": key, "label": domain_label(key),
                     "categories": [], "quotes": n, "entry": entry})
    for name in categories_of:
        rows.append({"kind": "code", "name": name, "label": name,
                     "categories": categories_of[name], "quotes": quotes.get(name, 0),
                     "entry": project.codebook.get(name) or CodebookEntry()})
    for name, entry in project.codebook.items():
        if name not in categories_of and not entry.is_empty():
            rows.append({"kind": "orphan", "name": name, "label": name,
                         "categories": [], "quotes": 0, "entry": entry})
    return rows


def codebook_to_csv(project: Project) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(tr("codebook_csv_columns").split("|"))
    for row in codebook_rows(project):
        entry = row["entry"]
        writer.writerow([
            tr("codebook_kind_" + row["kind"]),
            row["label"],
            "; ".join(domain_label(d) for d in row["categories"]),
            row["quotes"],
            entry.definition,
            entry.inclusion,
            entry.exclusion,
            entry.example,
            entry.updated_at if not entry.is_empty() else "",
        ])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def codebook_text(entry: CodebookEntry) -> str:
    """Descripción en texto plano, con sus apartados rotulados (para REFI-QDA)."""
    parts = []
    for field in ("definition", "inclusion", "exclusion", "example"):
        value = getattr(entry, field).strip()
        if value:
            parts.append(f"{tr('codebook_label_' + field)}: {value}")
    return "\n\n".join(parts)


def project_to_zip(project: Project) -> bytes:
    """Respaldo autocontenido para reproducibilidad/depósito de datos: el
    proyecto completo (JSON, fidelidad total), el banco en CSV y el texto de
    cada documento del corpus en .txt plano."""
    csv_name = tr("codes_csv_name")
    book_name = tr("codebook_csv_name")
    docs_folder = tr("documents_folder")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("proyecto.json", project.model_dump_json(indent=2))
        zf.writestr(csv_name, project_to_csv(project))
        zf.writestr(book_name, codebook_to_csv(project))
        used_names: set[str] = set()
        for doc in project.documents:
            base = _safe_filename(doc.filename)
            name = base
            i = 1
            while name in used_names:  # dos documentos con el mismo nombre sanitizado
                i += 1
                name = f"{base} ({i})"
            used_names.add(name)
            zf.writestr(f"{docs_folder}/{name}.txt", doc.text.encode("utf-8"))
        readme = tr(
            "readme_body", name=project.name,
            date=datetime.now().isoformat(timespec="seconds"),
            csv=csv_name, book=book_name, docs=docs_folder,
        )
        zf.writestr(tr("readme_name"), readme.encode("utf-8"))
    return buffer.getvalue()
