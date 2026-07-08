"""Exportación CSV (FR-021/022) y respaldo completo en .zip (FR-070)."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime

from .models import Project

COLUMNS = ["id", "fecha", "documento", "dominio", "codigo", "cita", "memo"]


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_. " else "_" for c in name).strip() or "documento"


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


def project_to_zip(project: Project) -> bytes:
    """Respaldo autocontenido para reproducibilidad/dep\u00f3sito de datos: el
    proyecto completo (JSON, fidelidad total), el banco en CSV y el texto de
    cada documento del corpus en .txt plano."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("proyecto.json", project.model_dump_json(indent=2))
        zf.writestr("codigos.csv", project_to_csv(project))
        used_names: set[str] = set()
        for doc in project.documents:
            base = _safe_filename(doc.filename)
            name = base
            i = 1
            while name in used_names:  # dos documentos con el mismo nombre sanitizado
                i += 1
                name = f"{base} ({i})"
            used_names.add(name)
            zf.writestr(f"documentos/{name}.txt", doc.text.encode("utf-8"))
        readme = (
            f"CUA-LIBRE STUDIO \u2014 Respaldo completo del proyecto \u00ab{project.name}\u00bb\n"
            f"Exportado: {datetime.now().isoformat(timespec='seconds')}\n\n"
            "Contenido:\n"
            "- proyecto.json  \u2192 el proyecto completo (corpus, c\u00f3digos, relaciones,\n"
            "                   memos, categor\u00edas propias). Fidelidad total: copia este\n"
            "                   archivo a la carpeta de proyectos de Cua-libre para\n"
            "                   reabrirlo tal cual qued\u00f3.\n"
            "- codigos.csv    \u2192 el banco de c\u00f3digos en una tabla (UTF-8, abre en Excel).\n"
            "- documentos/    \u2192 el texto de cada documento del corpus, en .txt plano.\n\n"
            "Generado por CUA-LIBRE STUDIO \u2014 https://github.com/ymunozs/cualibre\n"
        )
        zf.writestr("LEEME.txt", readme.encode("utf-8"))
    return buffer.getvalue()
