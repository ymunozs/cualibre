"""CSV: BOM, escapado RFC 4180, UTF-8 íntegro, roundtrip (T041)."""

import csv
import io

from backend.export import project_to_csv
from backend.models import Code, Document, Project


def make_project() -> Project:
    project = Project(name="Exportación")
    doc = Document(filename="entrevista.txt", text="irrelevante para el CSV")
    project.documents.append(doc)
    project.codes = [
        Code(id=1, doc_id=doc.id, domain="Emocional", name="añoranza, dura",
             quote='Dijo: "no vuelvo más"\ny lloró', start=0, end=5, memo="memo con ñ"),
        Code(id=2, doc_id=None, domain="Teórico", name="mediación", quote="", memo=""),
    ]
    return project


def test_bom_present():
    data = project_to_csv(make_project())
    assert data.startswith("﻿".encode("utf-8"))


def test_roundtrip_with_quotes_commas_newlines():
    data = project_to_csv(make_project())
    text = data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == ["id", "fecha", "documento", "dominio", "codigo", "cita", "memo"]
    assert len(rows) == 3
    fila1 = rows[1]
    assert fila1[3] == "Emocional"
    assert fila1[4] == "añoranza, dura"
    assert fila1[5] == 'Dijo: "no vuelvo más"\ny lloró'
    assert fila1[6] == "memo con ñ"


def test_manual_code_shows_manual_origin():
    data = project_to_csv(make_project())
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows[2][2] == "Manual"


def test_anchored_code_shows_filename():
    data = project_to_csv(make_project())
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows[1][2] == "entrevista.txt"
