"""CUA-LIBRE STUDIO — servidor FastAPI.

Sirve la SPA (frontend/) y expone la API HTTP/JSON (contracts/api.md).
Toda mutación persiste el proyecto de forma atómica ANTES de responder (FR-025).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import storage
from .extraction import ExtractionError, extract_text
from .export import project_to_csv
from .literature import LiteratureError, search_works
from .models import (
    DOMAINS,
    Code,
    CodeCreate,
    CodeUpdate,
    ConfirmPayload,
    Document,
    Project,
    ProjectCreate,
    utf16_len,
)
from .nlp import word_frequencies

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="CUA-LIBRE STUDIO", version="1.0.0")


# ----- Proyectos -----

@app.get("/api/projects")
def list_projects() -> list[dict]:
    return [p.summary() for p in storage.list_projects()]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    project = Project(name=payload.name)
    storage.save_project(project)
    storage.set_active_project(project.id)
    return project


@app.patch("/api/projects/{project_id}")
def rename_project(project_id: str, payload: ProjectCreate) -> dict:
    project = storage.load_project(project_id)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")
    project.name = payload.name
    storage.save_project(project)
    return project.summary()


@app.post("/api/projects/{project_id}/activate")
def activate_project(project_id: str) -> Project:
    project = storage.load_project(project_id)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")
    storage.set_active_project(project.id)
    return project


@app.get("/api/project")
def get_active_project() -> Project:
    return storage.get_active_project()


@app.post("/api/project/reset")
def reset_project(payload: ConfirmPayload) -> Project:
    if not payload.confirm:
        raise HTTPException(400, "El reinicio requiere confirmación explícita")
    project = storage.get_active_project()
    project.documents = []
    project.codes = []
    project.next_code_id = 1
    storage.save_project(project)
    return project


# ----- Documentos -----

@app.post("/api/documents", status_code=201)
async def upload_document(file: UploadFile) -> Document:
    data = await file.read()
    filename = file.filename or "documento"
    try:
        text = extract_text(filename, data)
    except ExtractionError as exc:
        message = str(exc)
        status = 415 if "no soportado" in message else 422
        raise HTTPException(status, message) from exc
    project = storage.get_active_project()
    document = Document(filename=filename, text=text)
    project.documents.append(document)
    storage.save_project(project)
    return document


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, confirm: bool = False) -> dict:
    project = storage.get_active_project()
    document = next((d for d in project.documents if d.id == doc_id), None)
    if document is None:
        raise HTTPException(404, "Documento no encontrado")
    anchored = [c for c in project.codes if c.doc_id == doc_id]
    if anchored and not confirm:
        raise HTTPException(
            409,
            f"El documento tiene {len(anchored)} código(s) asociado(s) que se perderán. "
            "Repite la operación con confirmación para eliminarlos.",
            headers={"X-Code-Count": str(len(anchored))},
        )
    project.documents = [d for d in project.documents if d.id != doc_id]
    project.codes = [c for c in project.codes if c.doc_id != doc_id]
    storage.save_project(project)
    return {"deleted_codes": len(anchored)}


# ----- Códigos -----

@app.post("/api/codes", status_code=201)
def create_code(payload: CodeCreate) -> Code:
    project = storage.get_active_project()
    if payload.doc_id is not None:
        document = next((d for d in project.documents if d.id == payload.doc_id), None)
        if document is None:
            raise HTTPException(422, "El documento del código no existe en este proyecto")
        text_len = utf16_len(document.text)
        if payload.end > text_len:
            raise HTTPException(422, "Offsets fuera del rango del documento")
    code = Code(
        id=project.next_code_id,
        doc_id=payload.doc_id,
        domain=payload.domain,
        name=payload.name,
        quote=payload.quote,
        start=payload.start,
        end=payload.end,
        memo=payload.memo,
    )
    project.next_code_id += 1
    project.codes.append(code)
    storage.save_project(project)
    return code


@app.patch("/api/codes/{code_id}")
def update_code(code_id: int, payload: CodeUpdate) -> Code:
    project = storage.get_active_project()
    code = next((c for c in project.codes if c.id == code_id), None)
    if code is None:
        raise HTTPException(404, "Código no encontrado")
    if payload.name is not None:
        code.name = payload.name
    if payload.domain is not None:
        code.domain = payload.domain
    if payload.memo is not None:
        code.memo = payload.memo
    storage.save_project(project)
    return code


@app.delete("/api/codes/{code_id}", status_code=204)
def delete_code(code_id: int) -> None:
    project = storage.get_active_project()
    if not any(c.id == code_id for c in project.codes):
        raise HTTPException(404, "Código no encontrado")
    project.codes = [c for c in project.codes if c.id != code_id]
    storage.save_project(project)


# ----- Análisis -----

@app.get("/api/domains")
def get_domains() -> dict[str, str]:
    return DOMAINS


@app.get("/api/nlp")
def nlp(lang: str = "es", min_len: int = 4, top: int = 50) -> dict:
    if lang not in ("es", "en"):
        raise HTTPException(422, "Idioma no soportado: usa 'es' o 'en'")
    min_len = max(2, min(10, min_len))
    project = storage.get_active_project()
    corpus = "\n".join(d.text for d in project.documents)
    return {"words": word_frequencies(corpus, lang=lang, min_len=min_len, top=top)}


@app.get("/api/export.csv")
def export_csv() -> Response:
    project = storage.get_active_project()
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project.name)
    return Response(
        content=project_to_csv(project),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="cualibre_{safe_name}.csv"'
        },
    )


@app.get("/api/literature")
def literature(q: str) -> dict:
    try:
        return {"results": search_works(q)}
    except LiteratureError as exc:
        raise HTTPException(502, str(exc)) from exc


# ----- SPA -----

@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
