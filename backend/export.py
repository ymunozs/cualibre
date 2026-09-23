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
from .models import Project


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


def project_to_zip(project: Project) -> bytes:
    """Respaldo autocontenido para reproducibilidad/depósito de datos: el
    proyecto completo (JSON, fidelidad total), el banco en CSV y el texto de
    cada documento del corpus en .txt plano."""
    csv_name = tr("codes_csv_name")
    docs_folder = tr("documents_folder")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("proyecto.json", project.model_dump_json(indent=2))
        zf.writestr(csv_name, project_to_csv(project))
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
            csv=csv_name, docs=docs_folder,
        )
        zf.writestr(tr("readme_name"), readme.encode("utf-8"))
    return buffer.getvalue()
