"""CUA-LIBRE STUDIO — servidor FastAPI.

Sirve la SPA (frontend/) y expone la API HTTP/JSON (contracts/api.md).
Toda mutación persiste el proyecto de forma atómica ANTES de responder (FR-025).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import storage
from .extraction import ExtractionError, extract_text
from .export import project_to_csv
from .literature import LiteratureError, search_works
from .models import (
    DOMAINS,
    RELATION_TYPES,
    Code,
    CodeCreate,
    CodeUpdate,
    ConfirmPayload,
    Document,
    Project,
    ProjectCreate,
    Relation,
    RelationCreate,
    utf16_len,
)


def _prune_relations(project: Project) -> None:
    """Elimina relaciones cuyos códigos ya no existen por nombre (FR-038)."""
    names = {c.name for c in project.codes}
    project.relations = [
        r for r in project.relations if r.source in names and r.target in names
    ]
from .nlp import word_frequencies

# Empaquetado (PyInstaller): los assets viven junto al ejecutable congelado
if getattr(sys, "frozen", False):
    FRONTEND_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "frontend"
else:
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


@app.post("/api/projects/example", status_code=201)
def create_example_project() -> Project:
    """Proyecto demo con entrevista ficticia ya codificada (FR-061)."""
    from .demo import build_example_project

    project = build_example_project()
    storage.save_project(project)
    storage.set_active_project(project.id)
    return project


@app.post("/api/project/reset")
def reset_project(payload: ConfirmPayload) -> Project:
    if not payload.confirm:
        raise HTTPException(400, "El reinicio requiere confirmación explícita")
    project = storage.get_active_project()
    project.documents = []
    project.codes = []
    project.next_code_id = 1
    project.relations = []
    project.next_relation_id = 1
    storage.save_project(project)
    return project


@app.post("/api/project/save")
def save_project_now() -> dict:
    """Guardado explícito (FR-036). El autoguardado (FR-025) sigue vigente."""
    project = storage.get_active_project()
    storage.save_project(project)
    return {"updated_at": project.updated_at}


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
    _prune_relations(project)
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
    _prune_relations(project)
    storage.save_project(project)
    return code


@app.delete("/api/codes/{code_id}", status_code=204)
def delete_code(code_id: int) -> None:
    project = storage.get_active_project()
    if not any(c.id == code_id for c in project.codes):
        raise HTTPException(404, "Código no encontrado")
    project.codes = [c for c in project.codes if c.id != code_id]
    _prune_relations(project)
    storage.save_project(project)


# ----- Relaciones entre códigos (FR-038) -----

@app.get("/api/relation-types")
def get_relation_types() -> dict[str, str]:
    return RELATION_TYPES


@app.post("/api/relations", status_code=201)
def create_relation(payload: RelationCreate) -> Relation:
    project = storage.get_active_project()
    names = {c.name for c in project.codes}
    for endpoint in (payload.source, payload.target):
        if endpoint not in names:
            raise HTTPException(422, f"No existe un código llamado «{endpoint}»")
    if any(r.source == payload.source and r.target == payload.target
           and r.type == payload.type for r in project.relations):
        raise HTTPException(409, "Esa relación ya existe")
    relation = Relation(
        id=project.next_relation_id,
        source=payload.source,
        target=payload.target,
        type=payload.type,
    )
    project.next_relation_id += 1
    project.relations.append(relation)
    storage.save_project(project)
    return relation


@app.delete("/api/relations/{relation_id}", status_code=204)
def delete_relation(relation_id: int) -> None:
    project = storage.get_active_project()
    if not any(r.id == relation_id for r in project.relations):
        raise HTTPException(404, "Relación no encontrada")
    project.relations = [r for r in project.relations if r.id != relation_id]
    storage.save_project(project)


# ----- Análisis -----

@app.get("/api/domains")
def get_domains() -> dict[str, str]:
    return DOMAINS


@app.get("/api/nlp")
def nlp(lang: str = "es", min_len: int = 4, top: int = 50, pos: str = "all") -> dict:
    if lang not in ("es", "en"):
        raise HTTPException(422, "Idioma no soportado: usa 'es' o 'en'")
    if pos not in ("all", "verb", "noun", "adj"):
        raise HTTPException(422, "Filtro gramatical inválido: usa all, verb, noun o adj")
    min_len = max(2, min(10, min_len))
    project = storage.get_active_project()
    corpus = "\n".join(d.text for d in project.documents)
    exclusions = set(project.nlp_exclusions)
    if pos == "all":
        words = word_frequencies(corpus, lang=lang, min_len=min_len, top=top,
                                 exclusions=exclusions)
    else:
        from .nlp import pos_frequencies

        words = pos_frequencies(corpus, lang=lang, pos=pos, min_len=min_len,
                                top=top, exclusions=exclusions)
    return {"words": words, "exclusions": project.nlp_exclusions}


class ExclusionsPayload(BaseModel):
    words: list[str]


@app.put("/api/nlp/exclusions")
def set_nlp_exclusions(payload: ExclusionsPayload) -> dict:
    """Palabras que el investigador omite del conteo (FR-048), por proyecto."""
    project = storage.get_active_project()
    cleaned = sorted({w.strip() for w in payload.words if w.strip()})
    project.nlp_exclusions = cleaned
    storage.save_project(project)
    return {"exclusions": cleaned}


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


# ----- Música de foco (FR-040) -----

MUSIC_EXTENSIONS = {".mp3", ".m4a", ".aac", ".ogg", ".wav", ".flac"}


@app.get("/api/music")
def list_music() -> dict:
    folder = storage.music_dir()
    tracks = sorted(
        f.name for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in MUSIC_EXTENSIONS
    )
    return {"folder": str(folder), "tracks": tracks}


@app.get("/api/music/{filename}")
def serve_music(filename: str) -> FileResponse:
    # Sin traversal: el nombre debe ser exactamente una entrada de la carpeta
    if filename != Path(filename).name:
        raise HTTPException(404, "Pista no encontrada")
    path = storage.music_dir() / filename
    if not path.is_file() or path.suffix.lower() not in MUSIC_EXTENSIONS:
        raise HTTPException(404, "Pista no encontrada")
    return FileResponse(path)


# ----- Sentimiento (FR-059) -----

@app.get("/api/sentiment")
def sentiment() -> dict:
    """Análisis de valencia y emociones por léxico (español, auditable)."""
    from .sentiment import analyze_texts, document_arc

    project = storage.get_active_project()
    if not project.documents and not project.codes:
        return {"documents": [], "domains": [], "codes": [], "words": {"positive": [], "negative": []}, "emotions": []}

    # Documentos: valencia global + arco emocional
    doc_results = analyze_texts([d.text for d in project.documents])
    documents = []
    all_pos: dict = {}
    all_neg: dict = {}
    all_emos: dict = {}
    for doc, result in zip(project.documents, doc_results):
        documents.append({
            "id": doc.id, "filename": doc.filename,
            "score": result["score"], "matched": result["matched"],
            "arc": document_arc(doc.text),
        })
        for w, c in result["positives"].items():
            all_pos[w] = all_pos.get(w, 0) + c
        for w, c in result["negatives"].items():
            all_neg[w] = all_neg.get(w, 0) + c
        for e, c in result["emotions"].items():
            all_emos[e] = all_emos.get(e, 0) + c

    # Tono por dominio y por código (sobre las citas ancladas)
    anchored = [c for c in project.codes if c.doc_id and c.quote]
    domains: list = []
    codes: list = []
    if anchored:
        quote_results = analyze_texts([c.quote for c in anchored])
        by_domain: dict = {}
        by_code: dict = {}
        for code, result in zip(anchored, quote_results):
            by_domain.setdefault(code.domain, []).append(result["score"])
            by_code.setdefault((code.name, code.domain), []).append(result["score"])
        domains = [
            {"domain": d, "score": round(sum(s) / len(s), 3), "n": len(s)}
            for d, s in by_domain.items()
        ]
        codes = sorted(
            ({"name": n, "domain": d, "score": round(sum(s) / len(s), 3), "n": len(s)}
             for (n, d), s in by_code.items()),
            key=lambda x: abs(x["score"]), reverse=True,
        )[:12]

    top = lambda counter: [
        {"word": w, "count": c}
        for w, c in sorted(counter.items(), key=lambda x: -x[1])[:15]
    ]
    return {
        "documents": documents,
        "domains": domains,
        "codes": codes,
        "words": {"positive": top(all_pos), "negative": top(all_neg)},
        "emotions": [
            {"emotion": e, "count": c}
            for e, c in sorted(all_emos.items(), key=lambda x: -x[1])
        ],
    }


# ----- Manual (FR-052) -----

@app.get("/api/manual")
def get_manual() -> dict:
    from .manual import manual_html

    try:
        return {"html": manual_html()}
    except FileNotFoundError:
        raise HTTPException(404, "MANUAL.md no encontrado")


# ----- SPA -----

@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
