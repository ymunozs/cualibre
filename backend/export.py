"""Exportación CSV UTF-8 con BOM compatible con Excel (FR-021/022)."""

from __future__ import annotations

import csv
import io

from .models import Project

COLUMNS = ["id", "fecha", "documento", "dominio", "codigo", "cita", "memo"]


def project_to_csv(project: Project) -> bytes:
    doc_names = {d.id: d.filename for d in project.documents}
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for code in project.codes:
        writer.writerow([
            code.id,
            code.created_at,
            doc_names.get(code.doc_id, "Manual") if code.doc_id else "Manual",
            code.domain,
            code.name,
            code.quote,
            code.memo,
        ])
    # BOM U+FEFF: Excel solo reconoce UTF-8 si el archivo abre con él
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")
