"""CUA-LIBRE STUDIO — servidor FastAPI.

Sirve la SPA (frontend/) y expone la API HTTP/JSON (contracts/api.md).
Toda mutación persiste el proyecto de forma atómica ANTES de responder (FR-025).
"""

from __future__ import annotations

import asyncio
import re
import sys
import threading
import weakref
from pathlib import Path
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import Response

from . import agreement, analysis, dictionary, i18n, lexicons, library, qdpx, storage
from .export import codebook_to_csv, project_to_csv, project_to_zip
from .extraction import ExtractionError, extract_document
from .i18n import tr
from .literature import LiteratureError, search_works
from .models import (
    DOMAINS,
    RELATION_TYPES,
    Board,
    BoardCreate,
    BoardNode,
    BoardUpdate,
    Code,
    CodebookEntry,
    CodebookUpdate,
    CodeCreate,
    CodeMerge,
    CodeUpdate,
    ConfirmPayload,
    CustomDomainCreate,
    Document,
    AnnotationCreate,
    AnnotationUpdate,
    Annotation,
    DoiLookup,
    LexiconOverrides,
    LexiconOverridesUpdate,
    LibraryItem,
    LitCoding,
    LitCodingCreate,
    LitItemUpdate,
    LitMeta,
    Project,
    ProjectCreate,
    Relation,
    RelationCreate,
    now_iso,
    utf16_len,
)
from .nlp import POS_LANGS, STOPWORDS, detect_language, word_frequencies

APP_VERSION = "1.14.1"
CORPUS_LANGS = tuple(STOPWORDS)  # es, en, pt
POS_FILTERS = ("all", "verb", "noun", "adj")


def _node_exists(project: Project, kind: str, name: str) -> bool:
    if kind == "category":
        return name in _all_domains(project)
    return any(c.name == name for c in project.codes)


def _all_boards(project: Project) -> list[Board]:
    return [project.general_board, *project.boards]


def _prune_relations(project: Project) -> None:
    """Elimina relaciones cuyos extremos ya no existen (FR-038): códigos por
    nombre, categorías por clave (FR-085). Los cuadros pierden también los
    nodos huérfanos y los colores de relaciones que ya no están."""
    names = {c.name for c in project.codes}
    domains = _all_domains(project)

    def alive(kind: str, name: str) -> bool:
        return name in domains if kind == "category" else name in names

    project.relations = [
        r for r in project.relations
        if alive(r.source_kind, r.source) and alive(r.target_kind, r.target)
    ]
    relation_ids = {str(r.id) for r in project.relations}
    for board in _all_boards(project):
        board.nodes = [n for n in board.nodes if alive(n.kind, n.name)]
        board.edge_colors = {k: v for k, v in board.edge_colors.items() if k in relation_ids}


def _remap_relations(project: Project, old_name: str, new_name: str) -> None:
    """Al fusionar/renombrar (FR-068), las relaciones migran con el nombre —
    nunca se pierden por una simple fusión. Se descartan solo las que quedan
    reflexivas (A→A) o duplicadas tras el remapeo. Solo se tocan extremos de
    tipo código: una categoría homónima no se renombra (FR-085)."""
    for r in project.relations:
        if r.source_kind == "code" and r.source == old_name:
            r.source = new_name
        if r.target_kind == "code" and r.target == old_name:
            r.target = new_name
    seen: set[tuple] = set()
    deduped = []
    for r in project.relations:
        if (r.source_kind, r.source) == (r.target_kind, r.target):
            continue
        key = (r.source_kind, r.source, r.target_kind, r.target, r.type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    project.relations = deduped
    # Cuadros: el nodo del código fusionado pasa a ser el del destino; si el
    # destino ya estaba en el cuadro, conserva su propia posición y color
    relation_ids = {str(r.id) for r in project.relations}
    for board in _all_boards(project):
        has_target = any(n.kind == "code" and n.name == new_name for n in board.nodes)
        kept = []
        for node in board.nodes:
            if node.kind == "code" and node.name == old_name:
                if has_target:
                    continue
                node.name = new_name
                has_target = True
            kept.append(node)
        board.nodes = kept
        board.edge_colors = {k: v for k, v in board.edge_colors.items() if k in relation_ids}


def _merge_entries(a: CodebookEntry, b: CodebookEntry) -> CodebookEntry:
    """Une dos descripciones sin perder texto: cada apartado conserva ambos."""
    merged = {}
    for field in ("definition", "inclusion", "exclusion", "example"):
        parts = [getattr(a, field).strip(), getattr(b, field).strip()]
        merged[field] = "\n\n".join(dict.fromkeys(p for p in parts if p))
    return CodebookEntry(**merged)


def _migrate_codebook(project: Project, old_name: str, new_name: str) -> None:
    """La descripción de un código viaja con su nombre (FR-084): al fusionar se
    suma a la del destino; nunca se borra."""
    entry = project.codebook.pop(old_name, None)
    if entry is None:
        return
    target = project.codebook.get(new_name)
    project.codebook[new_name] = entry if target is None else _merge_entries(target, entry)


def _all_domains(project: Project) -> dict[str, str]:
    """Categorías Básicas + personalizadas del proyecto (FR-064)."""
    return {**DOMAINS, **project.custom_domains}


def _attachment(filename: str) -> dict[str, str]:
    """Content-Disposition seguro para cualquier nombre (tildes, ñ, ç, emojis):
    versión ASCII de respaldo + filename* UTF-8 (RFC 6266)."""
    ascii_name = filename.encode("ascii", "replace").decode().replace("?", "_")
    return {
        "Content-Disposition":
            f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
    }


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)


# Empaquetado (PyInstaller): los assets viven junto al ejecutable congelado
if getattr(sys, "frozen", False):
    FRONTEND_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "frontend"
else:
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="CUA-LIBRE STUDIO", version=APP_VERSION)
# Modo de ejecución (lo fija run.py): "window" (ventana propia), "browser"
# (navegador, con botón SALIR) o "server" (desarrollo y tests)
app.state.mode = "server"
app.state.window = None
app.state.shutdown = None

# Solo páginas servidas por esta misma app pueden hablarle a la API: bloquea
# que un sitio web cualquiera abierto en el navegador envíe peticiones a
# 127.0.0.1 (CSRF) o use un dominio propio que apunte a 127.0.0.1 (DNS rebinding)
LOCAL_HOSTS = {"127.0.0.1", "localhost", "testserver"}


# ----- Idioma de la interfaz + escrituras en fila -----

_write_locks: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = (
    weakref.WeakKeyDictionary()
)


def _write_lock() -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    lock = _write_locks.get(loop)
    if lock is None:
        lock = _write_locks[loop] = asyncio.Lock()
    return lock


def _host_name(value: str) -> str:
    value = value.split("//", 1)[-1].split("/", 1)[0]
    return value[1:value.index("]")] if value.startswith("[") else value.rsplit(":", 1)[0] \
        if value.count(":") == 1 else value


def _local_request(headers: dict) -> bool:
    host = headers.get(b"host", b"").decode("latin-1")
    if host and _host_name(host) not in LOCAL_HOSTS:
        return False
    origin = headers.get(b"origin", b"").decode("latin-1")
    return not origin or origin == "null" or _host_name(origin) in LOCAL_HOSTS


class InterfaceMiddleware:
    """Dos responsabilidades transversales, en ASGI puro (el idioma queda en
    el mismo contexto que endpoints y validadores):

    1. Idioma: cabecera X-Cua-Lang o parámetro ?ui= (descargas directas).
    2. Escrituras en fila: cada mutación lee, modifica y guarda el proyecto
       completo; dos mutaciones simultáneas podían pisarse y perder una. Si
       una mutación falla a mitad de camino, se olvida el proyecto en memoria
       para volver a leer el disco, que es la fuente de verdad."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.inner(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        if not _local_request(headers):
            await JSONResponse({"detail": "forbidden"}, status_code=403)(scope, receive, send)
            return
        lang = headers.get(b"x-cua-lang", b"").decode("latin-1")
        if not lang:
            lang = parse_qs(scope.get("query_string", b"").decode("latin-1")).get("ui", [""])[0]
        token = i18n.set_lang(lang)
        mutating = scope["method"] not in ("GET", "HEAD", "OPTIONS")
        status = {"code": 200}

        async def tracking_send(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        try:
            if mutating:
                async with _write_lock():
                    await self.inner(scope, receive, tracking_send)
            else:
                await self.inner(scope, receive, tracking_send)
        except Exception:
            if mutating:
                storage.invalidate_cache()
                library.invalidate()
            raise
        finally:
            i18n.reset_lang(token)
        if mutating and status["code"] >= 400:
            storage.invalidate_cache()
            library.invalidate()


app.add_middleware(InterfaceMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Errores de validación legibles y en el idioma de la interfaz."""
    messages: list[str] = []
    for err in exc.errors():
        field = str((err.get("loc") or ["?"])[-1])
        kind = err.get("type", "")
        ctx = err.get("ctx") or {}
        if kind == "value_error" and ctx.get("error"):
            messages.append(str(ctx["error"]))
        elif kind == "string_too_long":
            messages.append(tr("field_too_long", field=field, max=ctx.get("max_length", "?")))
        elif kind in ("missing", "string_too_short"):
            messages.append(tr("field_required", field=field))
        else:
            messages.append(tr("invalid_field", field=field))
    return JSONResponse(status_code=422, content={"detail": "; ".join(dict.fromkeys(messages))})


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
        raise HTTPException(404, tr("project_not_found"))
    project.name = payload.name
    storage.save_project(project)
    return project.summary()


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, confirm: bool = False) -> dict:
    """Elimina un proyecto: se mueve a <datos>/papelera/, nunca se borra del disco."""
    if not confirm:
        raise HTTPException(400, tr("delete_project_needs_confirm"))
    if not storage.delete_project(project_id):
        raise HTTPException(404, tr("project_not_found"))
    active = storage.get_active_project()  # otro proyecto (o uno nuevo vacío)
    return {"deleted": project_id, "active_project_id": active.id}


@app.post("/api/projects/import", status_code=201)
async def import_project(file: UploadFile) -> dict:
    """Importa un respaldo .zip (FR-070) o un proyecto .json como proyecto nuevo."""
    data = await file.read()
    report = None
    try:
        if qdpx.is_qdpx(data):  # REFI-QDA: NVivo, ATLAS.ti, MAXQDA, QualCoder… (FR-079)
            project, report = qdpx.import_qdpx(data, fallback_name=file.filename or "QDPX")
        else:
            project = storage.parse_project_file(data)
    except (ValueError, OSError, qdpx.QdpxError) as exc:
        raise HTTPException(422, tr("import_invalid")) from exc
    if project.corpus_lang is None and project.documents:
        project.corpus_lang = detect_language("\n".join(d.text[:5000] for d in project.documents[:5]))
    project = storage.import_project(project)
    analysis.warm([d.text for d in project.documents], project.corpus_lang or "es")
    body = project.model_dump()
    body["import_report"] = report
    return body


@app.post("/api/projects/{project_id}/activate")
def activate_project(project_id: str) -> Project:
    project = storage.load_project(project_id)
    if project is None:
        raise HTTPException(404, tr("project_not_found"))
    storage.set_active_project(project.id)
    return project


@app.get("/api/project")
def get_active_project() -> Project:
    return storage.get_active_project()


@app.post("/api/projects/example", status_code=201)
def create_example_project() -> Project:
    """Proyecto demo con entrevista ficticia ya codificada (FR-061), en el
    idioma de la interfaz."""
    from .demo import build_example_project

    project = build_example_project()
    project.corpus_lang = i18n.current()  # la entrevista está en el idioma de la interfaz
    storage.save_project(project)
    storage.set_active_project(project.id)
    return project


@app.post("/api/project/reset")
def reset_project(payload: ConfirmPayload) -> Project:
    if not payload.confirm:
        raise HTTPException(400, tr("reset_needs_confirm"))
    project = storage.get_active_project()
    # Red de seguridad: el estado previo queda en el historial (FR-062)
    storage._maybe_snapshot(project, force=True)
    project.documents = []
    project.codes = []
    project.next_code_id = 1
    project.relations = []
    project.next_relation_id = 1
    # El libro de códigos y los cuadros describen los códigos borrados (v1.14)
    project.codebook = {}
    project.category_notes = {}
    project.general_board = Board(id=0)
    project.boards = []
    project.next_board_id = 1
    project.lit_codings = []  # la biblioteca (común) no se toca
    project.next_lit_id = 1
    storage.save_project(project)
    return project


@app.get("/api/snapshots")
def get_snapshots() -> dict:
    """Historial de respaldos del proyecto activo (FR-062)."""
    project = storage.get_active_project()
    return {"snapshots": storage.list_snapshots(project.id)}


@app.post("/api/snapshots/{name}/restore")
def restore_snapshot(name: str, payload: ConfirmPayload) -> Project:
    if not payload.confirm:
        raise HTTPException(400, tr("restore_needs_confirm"))
    current = storage.get_active_project()
    snapshot = storage.load_snapshot(current.id, name)
    if snapshot is None:
        raise HTTPException(404, tr("snapshot_not_found"))
    # Red de seguridad: el estado actual se respalda antes de ser reemplazado
    storage._maybe_snapshot(current, force=True)
    snapshot.id = current.id  # el respaldo ocupa el lugar del proyecto activo
    storage.save_project(snapshot)
    return snapshot


@app.post("/api/project/save")
def save_project_now() -> dict:
    """Guardado explícito (FR-036); fuerza un respaldo con historial (FR-062)."""
    project = storage.get_active_project()
    storage.save_project(project)
    storage._maybe_snapshot(project, force=True)
    return {"updated_at": project.updated_at}


# ----- Documentos -----

@app.post("/api/documents", status_code=201)
async def upload_document(file: UploadFile) -> Document:
    data = await file.read()
    filename = file.filename or tr("default_document_name")
    project = storage.get_active_project()
    hints = [lang for lang in (project.corpus_lang, i18n.current()) if lang]
    try:
        # En un hilo aparte: el OCR de un PDF escaneado puede tomar segundos
        # por página y no debe congelar las demás peticiones
        text, ocr_pages = await run_in_threadpool(extract_document, filename, data, hints)
    except ExtractionError as exc:
        raise HTTPException(415 if exc.unsupported else 422, str(exc)) from exc
    project = storage.get_active_project()
    document = Document(filename=filename, text=text, ocr_pages=ocr_pages)
    project.documents.append(document)
    if project.corpus_lang is None:  # el primer documento propone el idioma del corpus
        project.corpus_lang = detect_language(text)
    storage.save_project(project)
    # El análisis lingüístico se adelanta en segundo plano (sentimiento y
    # foco gramatical quedan listos antes de que el investigador los abra)
    analysis.warm([text], project.corpus_lang)
    return document


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, confirm: bool = False) -> dict:
    project = storage.get_active_project()
    document = next((d for d in project.documents if d.id == doc_id), None)
    if document is None:
        raise HTTPException(404, tr("document_not_found"))
    anchored = [c for c in project.codes if c.doc_id == doc_id]
    if anchored and not confirm:
        raise HTTPException(
            409,
            tr("document_has_codes", n=len(anchored)),
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
    if payload.domain not in _all_domains(project):
        raise HTTPException(422, tr("invalid_domain", name=payload.domain))
    if payload.doc_id is not None:
        document = next((d for d in project.documents if d.id == payload.doc_id), None)
        if document is None:
            raise HTTPException(422, tr("code_document_missing"))
        text_len = utf16_len(document.text)
        if payload.end > text_len:
            raise HTTPException(422, tr("offsets_out_of_range"))
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
        raise HTTPException(404, tr("code_not_found"))
    # Validar TODO antes de tocar nada: una edición inválida no deja cambios a medias
    if payload.domain is not None and payload.domain not in _all_domains(project):
        raise HTTPException(422, tr("invalid_domain", name=payload.domain))
    old_name = code.name
    if payload.name is not None:
        code.name = payload.name
    if payload.domain is not None:
        code.domain = payload.domain
    if payload.memo is not None:
        code.memo = payload.memo
    # Renombrar la última cita de un código: su descripción se va con ella,
    # salvo que el nombre nuevo ya tenga la suya (entonces queda a la vista
    # como descripción sin código, nunca se borra)
    if (code.name != old_name and old_name in project.codebook
            and code.name not in project.codebook
            and not any(c.name == old_name for c in project.codes)):
        project.codebook[code.name] = project.codebook.pop(old_name)
    if code.name != old_name and not any(c.name == old_name for c in project.codes):
        for lit in project.lit_codings:  # FR-091: los pasajes de literatura también
            if lit.name == old_name:
                lit.name = code.name
    _prune_relations(project)
    storage.save_project(project)
    return code


@app.delete("/api/codes/{code_id}", status_code=204)
def delete_code(code_id: int, confirm: bool = False) -> None:
    project = storage.get_active_project()
    code = next((c for c in project.codes if c.id == code_id), None)
    if code is None:
        raise HTTPException(404, tr("code_not_found"))
    # Última instancia de un nombre que tiene pasajes de literatura (FR-091):
    # se pide confirmación y se retiran con él (nunca quedan huérfanos)
    last = not any(c.name == code.name and c.id != code.id for c in project.codes)
    lit = [c for c in project.lit_codings if c.name == code.name] if last else []
    if lit and not confirm:
        raise HTTPException(409, tr("code_has_literature", n=len(lit), name=code.name),
                            headers={"X-Lit-Count": str(len(lit))})
    project.codes = [c for c in project.codes if c.id != code_id]
    if lit:
        project.lit_codings = [c for c in project.lit_codings if c.name != code.name]
    _prune_relations(project)
    storage.save_project(project)


@app.post("/api/codes/merge")
def merge_codes(payload: CodeMerge) -> dict:
    """Fusión/renombre en bloque de códigos por nombre (FR-068, codificación axial)."""
    project = storage.get_active_project()
    sources = [c for c in project.codes if c.name == payload.from_name]
    if not sources:
        raise HTTPException(404, tr("no_codes_named", name=payload.from_name))

    target_domain = payload.domain
    if target_domain is not None and target_domain not in _all_domains(project):
        raise HTTPException(422, tr("invalid_domain", name=target_domain))
    existing_target = [c for c in project.codes if c.name == payload.to_name]
    if target_domain is None and existing_target:
        # Fusión real (to_name ya existía): unifica al dominio del destino
        target_domain = existing_target[0].domain

    for code in sources:
        code.name = payload.to_name
        if target_domain is not None:
            code.domain = target_domain
    if target_domain is not None:
        for code in existing_target:
            code.domain = target_domain

    _remap_relations(project, payload.from_name, payload.to_name)
    _migrate_codebook(project, payload.from_name, payload.to_name)
    for lit in project.lit_codings:  # la literatura codificada se fusiona igual
        if lit.name == payload.from_name:
            lit.name = payload.to_name
        if target_domain is not None and lit.name == payload.to_name:
            lit.domain = target_domain
    storage.save_project(project)
    return {"merged": len(sources), "name": payload.to_name, "domain": target_domain}


# ----- Relaciones entre códigos (FR-038) -----

@app.get("/api/relation-types")
def get_relation_types() -> dict[str, str]:
    return RELATION_TYPES


def _add_endpoints(board: Board, relation: Relation) -> None:
    """Pone en el cuadro los dos extremos de la relación que aún no estén."""
    present = {(n.kind, n.name) for n in board.nodes}
    for kind, name in ((relation.source_kind, relation.source),
                       (relation.target_kind, relation.target)):
        if (kind, name) not in present:
            board.nodes.append(BoardNode(kind=kind, name=name))
            present.add((kind, name))


@app.post("/api/relations", status_code=201)
def create_relation(payload: RelationCreate, response: Response) -> dict:
    """Relación entre códigos y/o categorías (FR-038, FR-085).

    Las relaciones son del proyecto. Si ya existe y se pide desde un cuadro
    propio, no es un error: se trae a ese cuadro (sus dos extremos) y se
    responde 200 con existed=True (FR-088)."""
    project = storage.get_active_project()
    for kind, endpoint in ((payload.source_kind, payload.source),
                           (payload.target_kind, payload.target)):
        if not _node_exists(project, kind, endpoint):
            key = "no_category_named" if kind == "category" else "no_code_named"
            raise HTTPException(422, tr(key, name=endpoint))
    board = None
    if payload.board_id:
        board = next((b for b in project.boards if b.id == payload.board_id), None)
        if board is None:
            raise HTTPException(404, tr("board_not_found"))
    existing = next((r for r in project.relations
                     if r.source == payload.source and r.target == payload.target
                     and r.source_kind == payload.source_kind
                     and r.target_kind == payload.target_kind
                     and r.type == payload.type), None)
    if existing is not None:
        if board is None:
            raise HTTPException(409, tr("relation_exists"))
        _add_endpoints(board, existing)
        storage.save_project(project)
        response.status_code = 200
        return {**existing.model_dump(), "existed": True}
    relation = Relation(
        id=project.next_relation_id,
        source=payload.source,
        target=payload.target,
        type=payload.type,
        source_kind=payload.source_kind,
        target_kind=payload.target_kind,
    )
    project.next_relation_id += 1
    project.relations.append(relation)
    if board is not None:  # el cuadro activo recibe ambos extremos
        _add_endpoints(board, relation)
    storage.save_project(project)
    return {**relation.model_dump(), "existed": False}


@app.post("/api/boards/{board_id}/relations/{relation_id}")
def bring_relation(board_id: int, relation_id: int) -> Board:
    """Trae a un cuadro propio una relación que ya existe (FR-088)."""
    if board_id == 0:
        raise HTTPException(422, tr("board_general_fixed"))
    project = storage.get_active_project()
    board = next((b for b in project.boards if b.id == board_id), None)
    if board is None:
        raise HTTPException(404, tr("board_not_found"))
    relation = next((r for r in project.relations if r.id == relation_id), None)
    if relation is None:
        raise HTTPException(404, tr("relation_not_found"))
    _add_endpoints(board, relation)
    storage.save_project(project)
    return board


@app.post("/api/relations/{relation_id}/reverse")
def reverse_relation(relation_id: int) -> Relation:
    """Invierte el sentido de una relación (A → B pasa a B → A, FR-087). Conserva
    su id: el color que tenga en los cuadros no se pierde."""
    project = storage.get_active_project()
    relation = next((r for r in project.relations if r.id == relation_id), None)
    if relation is None:
        raise HTTPException(404, tr("relation_not_found"))
    if any(r.id != relation.id and r.type == relation.type
           and (r.source_kind, r.source) == (relation.target_kind, relation.target)
           and (r.target_kind, r.target) == (relation.source_kind, relation.source)
           for r in project.relations):
        raise HTTPException(409, tr("relation_exists"))
    relation.source, relation.target = relation.target, relation.source
    relation.source_kind, relation.target_kind = relation.target_kind, relation.source_kind
    storage.save_project(project)
    return relation


@app.delete("/api/relations/{relation_id}", status_code=204)
def delete_relation(relation_id: int) -> None:
    project = storage.get_active_project()
    if not any(r.id == relation_id for r in project.relations):
        raise HTTPException(404, tr("relation_not_found"))
    project.relations = [r for r in project.relations if r.id != relation_id]
    storage.save_project(project)


# ----- Libro de códigos (FR-084) -----

@app.put("/api/codebook")
def save_codebook_entry(payload: CodebookUpdate) -> dict:
    """Guarda la descripción cualitativa de un código o de una categoría.
    Una descripción vacía se retira del libro (no queda una ficha en blanco)."""
    project = storage.get_active_project()
    book = project.category_notes if payload.kind == "category" else project.codebook
    if payload.name not in book and not _node_exists(project, payload.kind, payload.name):
        key = "no_category_named" if payload.kind == "category" else "no_code_named"
        raise HTTPException(422, tr(key, name=payload.name))
    entry = CodebookEntry(
        definition=payload.definition, inclusion=payload.inclusion,
        exclusion=payload.exclusion, example=payload.example, updated_at=now_iso(),
    )
    if entry.is_empty():
        book.pop(payload.name, None)
    else:
        book[payload.name] = entry
    storage.save_project(project)
    return {"kind": payload.kind, "name": payload.name,
            "entry": None if entry.is_empty() else entry.model_dump()}


@app.delete("/api/codebook")
def delete_codebook_entry(kind: str, name: str, confirm: bool = False) -> dict:
    """Retira una descripción (p. ej., la de un código que ya no existe)."""
    if not confirm:
        raise HTTPException(400, tr("codebook_delete_needs_confirm"))
    project = storage.get_active_project()
    book = project.category_notes if kind == "category" else project.codebook
    if name not in book:
        raise HTTPException(404, tr("codebook_entry_not_found", name=name))
    del book[name]
    storage.save_project(project)
    return {"deleted": name}


@app.get("/api/codebook.csv")
def export_codebook_csv() -> Response:
    project = storage.get_active_project()
    return Response(
        content=codebook_to_csv(project),
        media_type="text/csv; charset=utf-8",
        headers=_attachment(f"cualibre_{tr('codebook_file')}_{_safe_name(project.name)}.csv"),
    )


# ----- Cuadros organizadores (FR-085) -----

def _find_board(project: Project, board_id: int) -> Board:
    board = next((b for b in _all_boards(project) if b.id == board_id), None)
    if board is None:
        raise HTTPException(404, tr("board_not_found"))
    return board


@app.post("/api/boards", status_code=201)
def create_board(payload: BoardCreate) -> Board:
    project = storage.get_active_project()
    board = Board(id=project.next_board_id, name=payload.name)
    project.next_board_id += 1
    project.boards.append(board)
    storage.save_project(project)
    return board


@app.put("/api/boards/{board_id}")
def update_board(board_id: int, payload: BoardUpdate) -> Board:
    """Reemplaza nombre, nodos (posición y color), colores de relaciones y
    tono de un cuadro. Solo cambia la vista: los datos (relaciones, colores
    de categoría) no se tocan."""
    project = storage.get_active_project()
    board = _find_board(project, board_id)
    if payload.name is not None:
        name = payload.name.strip()
        if board.id == 0:
            if name:
                raise HTTPException(422, tr("board_general_fixed"))
        elif not name:
            raise HTTPException(422, tr("name_empty"))
        else:
            board.name = name
    nodes, seen = [], set()
    for node in payload.nodes:
        key = (node.kind, node.name)
        if key in seen or not _node_exists(project, node.kind, node.name):
            continue  # duplicados o elementos que ya no existen: se ignoran
        seen.add(key)
        nodes.append(BoardNode(**node.model_dump()))
    board.nodes = nodes
    relation_ids = {str(r.id) for r in project.relations}
    board.edge_colors = {k: v for k, v in payload.edge_colors.items() if k in relation_ids}
    board.show_tone = payload.show_tone
    board.locked = payload.locked
    storage.save_project(project)
    return board


@app.delete("/api/boards/{board_id}")
def delete_board(board_id: int, confirm: bool = False) -> dict:
    """Elimina un cuadro propio. Las relaciones se conservan (viven en el proyecto)."""
    if board_id == 0:
        raise HTTPException(422, tr("board_general_fixed"))
    if not confirm:
        raise HTTPException(400, tr("board_delete_needs_confirm"))
    project = storage.get_active_project()
    _find_board(project, board_id)
    project.boards = [b for b in project.boards if b.id != board_id]
    storage.save_project(project)
    return {"deleted": board_id}


# ----- Biblioteca de literatura (FR-089..092) -----

LIBRARY_EXTENSIONS = {".pdf": "pdf", ".docx": "text", ".doc": "text", ".txt": "text"}


def _item_or_404(lib, item_id: str) -> LibraryItem:
    item = next((i for i in lib.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(404, tr("library_item_not_found"))
    return item


def _item_view(item: LibraryItem, lib, project: Project | None = None) -> dict:
    project = project or storage.get_active_project()
    return {
        **item.model_dump(),
        "has_file": library.file_path(item) is not None,
        "annotations": sum(1 for a in lib.annotations if a.item_id == item.id),
        "codings": sum(1 for c in project.lit_codings if c.item_id == item.id),
        "apa": library.apa(item.meta, i18n.current()),
        "cite": library.short_cite(item.meta, i18n.current()),
    }


@app.get("/api/library")
def get_library() -> dict:
    lib = library.load()
    project = storage.get_active_project()
    items = sorted(lib.items, key=lambda i: library.sort_key(i.meta))
    return {"items": [_item_view(i, lib, project) for i in items]}


@app.post("/api/library/items", status_code=201)
async def add_library_item(file: UploadFile, response: Response) -> dict:
    """Agrega un PDF, DOCX, DOC o TXT a la biblioteca. Si el mismo archivo ya
    estaba, no se duplica: se responde con el existente (duplicate=True)."""
    data = await file.read()
    filename = Path(file.filename or "documento").name
    extension = Path(filename).suffix.lower()
    kind = LIBRARY_EXTENSIONS.get(extension)
    if kind is None:
        raise HTTPException(415, tr("library_unsupported"))
    digest = library.sha1(data)
    lib = library.load()
    existing = next((i for i in lib.items if i.sha1 == digest), None)
    if existing is not None:
        response.status_code = 200
        return {**_item_view(existing, lib), "duplicate": True}
    item = LibraryItem(kind=kind, filename=filename, sha1=digest)
    meta = LitMeta(title=Path(filename).stem)
    if kind == "pdf":  # sin OCR: un PDF escaneado igual se lee (imagen) en el lector
        text, item.pages, info = await run_in_threadpool(library.pdf_text, data)
        if (info.get("title") or "").strip():
            meta.title = info["title"].strip()
    else:
        try:
            text, _ocr = await run_in_threadpool(extract_document, filename, data, None)
        except ExtractionError as exc:
            raise HTTPException(422, str(exc)) from exc
    doi = library.find_doi(text[:20000])
    if doi:
        found = await run_in_threadpool(library.lookup_doi, doi)
        meta = found or meta
        meta.doi = meta.doi or doi
    item.meta = meta
    library.store_file(item, data, extension)
    library.store_text(item.id, text)
    lib = library.load()
    lib.items.append(item)
    library.save(lib)
    return {**_item_view(item, lib), "duplicate": False, "doi_found": bool(doi)}


@app.post("/api/library/refs", status_code=201)
async def add_library_reference(payload: DoiLookup) -> dict:
    """Agrega solo la referencia (sin archivo), p. ej. desde OpenAlex: los
    metadatos salen del DOI."""
    doi = library.normalize_doi(payload.doi)
    if not doi:
        raise HTTPException(422, tr("doi_missing"))
    lib = library.load()
    existing = next((i for i in lib.items
                     if library.normalize_doi(i.meta.doi).lower() == doi.lower()), None)
    if existing is not None:
        return {**_item_view(existing, lib), "duplicate": True}
    meta = await run_in_threadpool(library.lookup_doi, doi)
    if meta is None:
        raise HTTPException(502, tr("doi_lookup_failed"))
    item = LibraryItem(kind="ref", meta=meta)
    lib = library.load()
    lib.items.append(item)
    library.save(lib)
    return {**_item_view(item, lib), "duplicate": False}


@app.patch("/api/library/items/{item_id}")
def update_library_item(item_id: str, payload: LitItemUpdate) -> dict:
    lib = library.load()
    item = _item_or_404(lib, item_id)
    if payload.meta is not None:
        item.meta = payload.meta
    if payload.note is not None:
        item.note = payload.note
    library.save(lib)
    return _item_view(item, lib)


@app.post("/api/library/items/{item_id}/lookup")
async def lookup_library_item(item_id: str, payload: DoiLookup) -> dict:
    """Completa la ficha desde un DOI (el escrito, o el que trae el documento)."""
    lib = library.load()
    item = _item_or_404(lib, item_id)
    doi = library.normalize_doi(payload.doi) or library.find_doi(library.read_text(item_id)[:20000])
    if not doi:
        raise HTTPException(422, tr("doi_missing"))
    meta = await run_in_threadpool(library.lookup_doi, doi)
    if meta is None:
        raise HTTPException(502, tr("doi_lookup_failed"))
    lib = library.load()
    item = _item_or_404(lib, item_id)
    item.meta = meta
    library.save(lib)
    return _item_view(item, lib)


def _codings_by_project(item_id: str) -> list[tuple[Project, int]]:
    out = []
    for project in storage.list_projects():
        n = sum(1 for c in project.lit_codings if c.item_id == item_id)
        if n:
            out.append((project, n))
    return out


@app.delete("/api/library/items/{item_id}")
def delete_library_item(item_id: str, confirm: bool = False) -> dict:
    """Elimina un documento de la biblioteca: su archivo va a la papelera y sus
    anotaciones y pasajes codificados (en todos los proyectos) se retiran."""
    lib = library.load()
    item = _item_or_404(lib, item_id)
    used = _codings_by_project(item_id)
    total = sum(n for _, n in used)
    if not confirm:
        raise HTTPException(409, tr("library_delete_confirm", n=total, projects=len(used)),
                            headers={"X-Coding-Count": str(total)})
    for project, _ in used:
        project.lit_codings = [c for c in project.lit_codings if c.item_id != item_id]
        storage.save_project(project)
    library.trash_files(item)
    lib.items = [i for i in lib.items if i.id != item_id]
    lib.annotations = [a for a in lib.annotations if a.item_id != item_id]
    library.save(lib)
    return {"deleted": item_id, "codings": total}


@app.get("/api/library/items/{item_id}/file")
def library_item_file(item_id: str) -> FileResponse:
    lib = library.load()
    item = _item_or_404(lib, item_id)
    path = library.file_path(item)
    if path is None:
        raise HTTPException(404, tr("library_item_not_found"))
    return FileResponse(path, media_type="application/pdf" if item.kind == "pdf" else None)


@app.get("/api/library/items/{item_id}/text")
def library_item_text(item_id: str) -> dict:
    lib = library.load()
    _item_or_404(lib, item_id)
    return {"text": library.read_text(item_id)}


@app.get("/api/library/items/{item_id}/annotations")
def library_item_annotations(item_id: str) -> dict:
    """Anotaciones de lectura del documento y pasajes codificados en el proyecto activo."""
    lib = library.load()
    _item_or_404(lib, item_id)
    project = storage.get_active_project()
    return {
        "annotations": [a.model_dump() for a in lib.annotations if a.item_id == item_id],
        "codings": [c.model_dump() for c in project.lit_codings if c.item_id == item_id],
    }


@app.post("/api/library/annotations", status_code=201)
def create_annotation(payload: AnnotationCreate) -> Annotation:
    lib = library.load()
    _item_or_404(lib, payload.item_id)
    annotation = Annotation(**payload.model_dump())
    lib.annotations.append(annotation)
    library.save(lib)
    return annotation


@app.patch("/api/library/annotations/{annotation_id}")
def update_annotation(annotation_id: str, payload: AnnotationUpdate) -> Annotation:
    lib = library.load()
    annotation = next((a for a in lib.annotations if a.id == annotation_id), None)
    if annotation is None:
        raise HTTPException(404, tr("annotation_not_found"))
    for field in ("kind", "color", "comment"):
        value = getattr(payload, field)
        if value is not None:
            setattr(annotation, field, value)
    library.save(lib)
    return annotation


@app.delete("/api/library/annotations/{annotation_id}", status_code=204)
def delete_annotation(annotation_id: str) -> None:
    lib = library.load()
    if not any(a.id == annotation_id for a in lib.annotations):
        raise HTTPException(404, tr("annotation_not_found"))
    lib.annotations = [a for a in lib.annotations if a.id != annotation_id]
    library.save(lib)


# ----- Diccionario del lector (FR-093) -----

_item_langs: dict[str, str] = {}


def _item_lang(item_id: str) -> str:
    """Idioma de un documento de la biblioteca (por su texto; se recuerda)."""
    if item_id not in _item_langs:
        text = library.read_text(item_id)[:6000]
        _item_langs[item_id] = detect_language(text) if text.strip() else i18n.current()
    return _item_langs[item_id]


@app.get("/api/dictionary/status")
def dictionary_status() -> dict:
    return {"languages": dictionary.status()}


@app.post("/api/dictionary/download")
def dictionary_download() -> dict:
    """Descarga única (en segundo plano) de los diccionarios que falten."""
    missing = [lang for lang in dictionary.LANGS if not dictionary.installed(lang)]
    started = dictionary.install_all(missing) if missing else False
    return {"started": started, "languages": dictionary.status()}


@app.get("/api/dictionary/lookup")
def dictionary_lookup(word: str, lang: str = "", item_id: str = "") -> dict:
    """Definiciones de una palabra. Sin idioma explícito, el del documento."""
    if lang not in dictionary.LANGS:
        lang = _item_lang(item_id) if item_id else i18n.current()
    if lang not in dictionary.LANGS:
        lang = "es"
    return {**dictionary.lookup(lang, word), "installed": dictionary.installed(lang)}


# ----- Literatura codificada en el proyecto activo (FR-091) -----

@app.post("/api/lit-codings", status_code=201)
def create_lit_coding(payload: LitCodingCreate) -> LitCoding:
    """Codifica un pasaje de la biblioteca con un código del proyecto activo.
    El código debe existir en el proyecto (si es nuevo, la interfaz lo crea
    antes como código manual)."""
    project = storage.get_active_project()
    _item_or_404(library.load(), payload.item_id)
    if payload.domain not in _all_domains(project):
        raise HTTPException(422, tr("invalid_domain", name=payload.domain))
    if not any(c.name == payload.name for c in project.codes):
        raise HTTPException(422, tr("no_code_named", name=payload.name))
    coding = LitCoding(id=project.next_lit_id, **payload.model_dump())
    project.next_lit_id += 1
    project.lit_codings.append(coding)
    storage.save_project(project)
    return coding


class LitCodingUpdate(BaseModel):
    memo: str


@app.patch("/api/lit-codings/{coding_id}")
def update_lit_coding(coding_id: int, payload: LitCodingUpdate) -> LitCoding:
    project = storage.get_active_project()
    coding = next((c for c in project.lit_codings if c.id == coding_id), None)
    if coding is None:
        raise HTTPException(404, tr("lit_coding_not_found"))
    coding.memo = payload.memo
    storage.save_project(project)
    return coding


@app.delete("/api/lit-codings/{coding_id}", status_code=204)
def delete_lit_coding(coding_id: int) -> None:
    project = storage.get_active_project()
    if not any(c.id == coding_id for c in project.lit_codings):
        raise HTTPException(404, tr("lit_coding_not_found"))
    project.lit_codings = [c for c in project.lit_codings if c.id != coding_id]
    storage.save_project(project)


def _bibliography_items(scope: str) -> list[LibraryItem]:
    lib = library.load()
    if scope == "project":
        used = {c.item_id for c in storage.get_active_project().lit_codings}
        items = [i for i in lib.items if i.id in used]
    else:
        items = list(lib.items)
    return sorted(items, key=lambda i: library.sort_key(i.meta))


@app.get("/api/library/bibliography")
def bibliography(scope: str = "all") -> dict:
    """Lista de referencias en APA 7 (scope=project: lo codificado en el proyecto)."""
    lang = i18n.current()
    return {"entries": [{"id": i.id, "html": library.apa(i.meta, lang),
                         "text": library.apa(i.meta, lang, html=False)}
                        for i in _bibliography_items(scope)]}


@app.get("/api/library/export.{fmt}")
def export_bibliography(fmt: str, scope: str = "all") -> Response:
    """Biblioteca en BibTeX o RIS (para Zotero, Mendeley, EndNote…)."""
    metas = [i.meta for i in _bibliography_items(scope)]
    if fmt == "bib":
        content, media = library.bibtex(metas), "application/x-bibtex"
    elif fmt == "ris":
        content, media = library.ris(metas), "application/x-research-info-systems"
    else:
        raise HTTPException(404)
    return Response(content=content.encode("utf-8"), media_type=f"{media}; charset=utf-8",
                    headers=_attachment(f"cualibre_{tr('library_file')}.{fmt}"))


# ----- Categorías -----

@app.get("/api/domains")
def get_domains() -> dict[str, dict[str, str]]:
    """Categorías Básicas (fijas) + personalizadas del proyecto activo (FR-064)."""
    project = storage.get_active_project()
    return {"basic": DOMAINS, "custom": project.custom_domains}


@app.post("/api/domains/custom", status_code=201)
def create_custom_domain(payload: CustomDomainCreate) -> dict[str, dict[str, str]]:
    project = storage.get_active_project()
    # Tampoco puede repetir la etiqueta visible de una Básica en otro idioma
    # («Emotional» ≡ «Emocional»): serían dos categorías indistinguibles.
    taken = {name.lower() for name in _all_domains(project)}
    for key in DOMAINS:
        taken.update(i18n.domain_label(key, lang).lower() for lang in i18n.LANGS)
    if payload.name.lower() in taken:
        raise HTTPException(409, tr("category_exists", name=payload.name))
    project.custom_domains[payload.name] = payload.color
    storage.save_project(project)
    return {"basic": DOMAINS, "custom": project.custom_domains}


@app.delete("/api/domains/custom/{name}")
def delete_custom_domain(name: str, confirm: bool = False) -> dict:
    project = storage.get_active_project()
    if name not in project.custom_domains:
        raise HTTPException(404, tr("custom_category_not_found"))
    in_use = sum(1 for c in project.codes if c.domain == name)
    in_relations = sum(1 for r in project.relations
                       if (r.source_kind, r.source) == ("category", name)
                       or (r.target_kind, r.target) == ("category", name))
    if (in_use or in_relations) and not confirm:
        message = tr("custom_category_in_use", n=in_use, name=name) if in_use \
            else tr("custom_category_has_relations", r=in_relations, name=name)
        raise HTTPException(
            409, message,
            headers={"X-Code-Count": str(in_use), "X-Relation-Count": str(in_relations)},
        )
    del project.custom_domains[name]
    _prune_relations(project)  # relaciones y nodos de cuadro de esa categoría (FR-085)
    storage.save_project(project)
    return {"in_use": in_use, "relations": in_relations}


# ----- Análisis -----

def _pending(response: Response, done: int, total: int) -> dict:
    """Análisis en curso (corpus grande): 202 + avance, la interfaz sondea."""
    response.status_code = 202
    return {"pending": True, "done": done, "total": total}


def _check_corpus_lang(lang: str, pos: str) -> None:
    if lang not in CORPUS_LANGS:
        raise HTTPException(422, tr("corpus_lang_unsupported"))
    if pos not in POS_FILTERS:
        raise HTTPException(422, tr("pos_invalid"))
    if pos != "all" and lang not in POS_LANGS:
        raise HTTPException(422, tr("pos_lang_unsupported"))


@app.get("/api/nlp")
def nlp(response: Response, lang: str = "es", min_len: int = 4, top: int = 50,
        pos: str = "all") -> dict:
    _check_corpus_lang(lang, pos)
    min_len = max(2, min(10, min_len))
    project = storage.get_active_project()
    exclusions = set(project.nlp_exclusions)
    if pos == "all":
        corpus = "\n".join(d.text for d in project.documents)
        words = word_frequencies(corpus, lang=lang, min_len=min_len, top=top,
                                 exclusions=exclusions)
    else:
        from .nlp import pos_counts

        texts = [d.text for d in project.documents]
        ready, done, total = analysis.prepare(texts, lang)
        if not ready:
            return _pending(response, done, total)
        words = pos_counts([analysis.get(t, lang) for t in texts], pos, lang,
                           min_len=min_len, top=top, exclusions=exclusions)
    return {"words": words, "exclusions": project.nlp_exclusions}


@app.get("/api/kwic")
def kwic(response: Response, q: str, lang: str = "es", pos: str = "all",
         window: int = 60) -> dict:
    """Concordancias (KWIC): todas las ocurrencias de una palabra en contexto (FR-063)."""
    if not q.strip():
        raise HTTPException(422, tr("kwic_empty_query"))
    _check_corpus_lang(lang, pos)
    window = max(20, min(160, window))
    project = storage.get_active_project()
    if pos != "all":
        ready, done, total = analysis.prepare([d.text for d in project.documents], lang)
        if not ready:
            return _pending(response, done, total)
    from .nlp import kwic_occurrences

    occurrences = kwic_occurrences(project.documents, q, lang=lang, pos=pos, window=window)
    return {"query": q, "count": len(occurrences), "occurrences": occurrences}


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


@app.get("/api/analysis/status")
def analysis_status(lang: str = "es") -> dict:
    """Cuántos documentos del proyecto activo ya tienen su análisis listo."""
    if lang not in CORPUS_LANGS:
        raise HTTPException(422, tr("corpus_lang_unsupported"))
    texts = [d.text for d in storage.get_active_project().documents]
    done = sum(1 for t in texts if analysis.is_ready(t, lang))
    return {"done": done, "total": len(texts), "ready": done == len(texts)}


@app.get("/api/export.csv")
def export_csv() -> Response:
    project = storage.get_active_project()
    return Response(
        content=project_to_csv(project),
        media_type="text/csv; charset=utf-8",
        headers=_attachment(f"cualibre_{_safe_name(project.name)}.csv"),
    )


@app.get("/api/export.zip")
def export_zip() -> Response:
    """Respaldo completo autocontenido: JSON + CSV + textos del corpus (FR-070)."""
    project = storage.get_active_project()
    return Response(
        content=project_to_zip(project),
        media_type="application/zip",
        headers=_attachment(f"cualibre_{_safe_name(project.name)}_{tr('backup_suffix')}.zip"),
    )


@app.get("/api/literature")
def literature(q: str) -> dict:
    try:
        return {"results": search_works(q)}
    except LiteratureError as exc:
        raise HTTPException(502, str(exc)) from exc


class CorpusLangPayload(BaseModel):
    lang: str


@app.put("/api/project/corpus-lang")
def set_corpus_lang(payload: CorpusLangPayload) -> dict:
    """Idioma del corpus del proyecto (NLP, foco gramatical y sentimiento)."""
    if payload.lang not in CORPUS_LANGS:
        raise HTTPException(422, tr("corpus_lang_unsupported"))
    project = storage.get_active_project()
    project.corpus_lang = payload.lang
    storage.save_project(project)
    analysis.warm([d.text for d in project.documents], payload.lang)
    return {"corpus_lang": payload.lang}


# ----- Léxicos de sentimiento (FR-077) -----

@app.get("/api/lexicons")
def get_lexicons() -> dict:
    return {"lexicons": lexicons.status(), "home": lexicons.NRC_HOME}


def _after_lexicon_install(installed: dict) -> dict:
    project = storage.get_active_project()
    if project.corpus_lang in installed:
        analysis.warm([d.text for d in project.documents], project.corpus_lang)
    return {"installed": installed, "lexicons": lexicons.status()}


@app.post("/api/lexicons/download")
async def download_lexicons() -> dict:
    """Descarga única del léxico oficial del NRC (inglés y portugués)."""
    try:
        installed = await run_in_threadpool(lexicons.download)
    except lexicons.LexiconError as exc:
        raise HTTPException(502, tr("lexicon_download_failed")) from exc
    return _after_lexicon_install(installed)


@app.post("/api/lexicons/import")
async def import_lexicons(file: UploadFile) -> dict:
    """Instala los léxicos desde el .zip oficial del NRC (sin internet)."""
    data = await file.read()
    try:
        installed = await run_in_threadpool(lexicons.install_from_zip, data)
    except lexicons.LexiconError as exc:
        raise HTTPException(422, tr("lexicon_invalid")) from exc
    return _after_lexicon_install(installed)


# ----- Acuerdo entre codificadores (FR-078) -----

def _agreement(other: str) -> dict:
    project = storage.get_active_project()
    other_project = storage.load_project(other)
    if other_project is None or other_project.id == project.id:
        raise HTTPException(404, tr("project_not_found"))
    return agreement.compare(project, other_project)


@app.get("/api/agreement")
def get_agreement(other: str) -> dict:
    return _agreement(other)


@app.get("/api/agreement.csv")
def export_agreement(other: str) -> Response:
    import csv
    import io

    result = _agreement(other)
    labels = {key: tr("agreement_col_" + key) for key in
              ("code", "count_a", "count_b", "agreement", "kappa", "alpha", "band")}
    labels.update({"band_" + b: tr("band_" + b) for b in
                   ("na", "poor", "slight", "fair", "moderate", "substantial", "almost_perfect")})
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow([f"A: {result['project_a']['name']}", f"B: {result['project_b']['name']}"])
    writer.writerows(agreement.to_csv_rows(result, labels))
    name = f"cualibre_{tr('agreement_file')}_{_safe_name(result['project_a']['name'])}.csv"
    return Response(content=("\ufeff" + buffer.getvalue()).encode("utf-8"),
                    media_type="text/csv; charset=utf-8", headers=_attachment(name))


# ----- REFI-QDA (FR-079) -----

@app.get("/api/export.qdpx")
def export_qdpx(profile: str = "standard") -> Response:
    """Proyecto completo en el estándar REFI-QDA (NVivo, ATLAS.ti, MAXQDA…).
    profile=nvivo usa la convención de posiciones de NVivo (ver qdpx.py)."""
    project = storage.get_active_project()
    suffix = "_nvivo" if profile == "nvivo" else ""
    return Response(
        content=qdpx.export_qdpx(project, profile="nvivo" if profile == "nvivo" else "standard"),
        media_type="application/zip",
        headers=_attachment(f"cualibre_{_safe_name(project.name)}{suffix}.qdpx"),
    )


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
        raise HTTPException(404)
    path = storage.music_dir() / filename
    if not path.is_file() or path.suffix.lower() not in MUSIC_EXTENSIONS:
        raise HTTPException(404)
    return FileResponse(path)


# ----- Sentimiento (FR-059) -----

def _top(counter: dict, n: int | None = 15) -> list[dict]:
    """Palabras por frecuencia (n=None: todas). Empates en orden alfabético."""
    ranked = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return [{"word": w, "count": c} for w, c in (ranked if n is None else ranked[:n])]


@app.get("/api/sentiment")
def sentiment(response: Response, lang: str = "") -> dict:
    """Análisis de valencia y emociones por léxico (auditable), en el idioma
    del corpus (FR-077)."""
    from .sentiment import (
        apply_overrides,
        arc_from_records,
        records_between,
        score_records,
        valence,
    )

    project = storage.get_active_project()
    lang = lang or project.corpus_lang or "es"
    if lang not in CORPUS_LANGS:
        raise HTTPException(422, tr("corpus_lang_unsupported"))
    overrides = project.sentiment_overrides.get(lang) or LexiconOverrides()
    info = {"lang": lang, "lexicon_size": len(lexicons.get(lang) or {}),
            "overrides": overrides.model_dump()}
    if not project.documents and not project.codes:
        return {"documents": [], "domains": [], "codes": [], "code_tones": {},
                "words": {"positive": [], "negative": []},
                "polarity_words": {"positivo": [], "negativo": []},
                "emotions": [], "emotion_words": {}, **info}
    if lexicons.get(lang) is None:  # léxico aún no instalado en este equipo
        return {"lexicon_missing": True, **info}

    ready, done, total = analysis.prepare([d.text for d in project.documents], lang)
    if not ready:
        return _pending(response, done, total)

    # Documentos: valencia global + arco emocional
    records_by_doc: dict[str, list] = {}
    documents = []
    all_pos: dict = {}
    all_neg: dict = {}
    all_emos: dict = {}
    all_emotion_words: dict[str, dict[str, int]] = {}
    for doc in project.documents:
        # Ajustes del investigador al léxico (FR-086): repercuten en todo lo que sigue
        records = apply_overrides(doc.text, analysis.get(doc.text, lang), overrides)
        records_by_doc[doc.id] = records
        result = score_records(records)
        documents.append({
            "id": doc.id, "filename": doc.filename,
            "score": result["score"], "matched": result["matched"],
            "arc": arc_from_records(doc.text, records),
        })
        for w, c in result["positives"].items():
            all_pos[w] = all_pos.get(w, 0) + c
        for w, c in result["negatives"].items():
            all_neg[w] = all_neg.get(w, 0) + c
        for e, c in result["emotions"].items():
            all_emos[e] = all_emos.get(e, 0) + c
        for e, words in result["emotion_words"].items():
            bucket = all_emotion_words.setdefault(e, {})
            for w, c in words.items():
                bucket[w] = bucket.get(w, 0) + c

    # Tono por dominio y por código: tokens con carga dentro de cada cita
    offset_maps = {d.id: analysis.OffsetMap(d.text) for d in project.documents}
    starts_by_doc = {doc_id: [r[0] for r in recs] for doc_id, recs in records_by_doc.items()}
    by_domain: dict = {}
    by_code: dict = {}
    by_name: dict = {}  # tono por nombre de código, para el organizador (FR-086)
    for code in project.codes:
        if not (code.doc_id and code.quote) or code.doc_id not in offset_maps:
            continue
        offsets = offset_maps[code.doc_id]
        chunk = records_between(records_by_doc[code.doc_id], offsets.to_cp(code.start),
                                offsets.to_cp(code.end), starts_by_doc[code.doc_id])
        score, _ = valence(chunk)
        by_domain.setdefault(code.domain, []).append(score)
        by_code.setdefault((code.name, code.domain), []).append(score)
        by_name.setdefault(code.name, []).append(score)
    domains = [
        {"domain": d, "score": round(sum(s) / len(s), 3), "n": len(s)}
        for d, s in by_domain.items()
    ]
    codes = sorted(
        ({"name": n, "domain": d, "score": round(sum(s) / len(s), 3), "n": len(s)}
         for (n, d), s in by_code.items()),
        key=lambda x: abs(x["score"]), reverse=True,
    )[:12]

    return {
        "documents": documents,
        "domains": domains,
        "codes": codes,
        "code_tones": {n: {"score": round(sum(s) / len(s), 3), "n": len(s)}
                       for n, s in by_name.items()},
        "words": {"positive": _top(all_pos), "negative": _top(all_neg)},
        # Listas completas (no solo las 15 primeras): el investigador las revisa
        # palabra por palabra para descartar o sumar (FR-086)
        "polarity_words": {"positivo": _top(all_pos, None), "negativo": _top(all_neg, None)},
        "emotions": [
            {"emotion": e, "count": c}
            for e, c in sorted(all_emos.items(), key=lambda x: -x[1])
        ],
        # Trazabilidad por emoción (FR-071): qué palabras exactas la dispararon
        "emotion_words": {e: _top(words, None) for e, words in all_emotion_words.items()},
        **info,
    }


@app.put("/api/sentiment/overrides")
def set_sentiment_overrides(payload: LexiconOverridesUpdate) -> dict:
    """Ajustes del investigador al léxico (FR-086), por proyecto e idioma:
    palabras descartadas de una emoción o polaridad y palabras sumadas."""
    if payload.lang not in CORPUS_LANGS:
        raise HTTPException(422, tr("corpus_lang_unsupported"))
    # Sumar una palabra a una categoría anula su descarte en esa misma categoría
    removed = {cat: [w for w in words if w not in payload.added.get(cat, [])]
               for cat, words in payload.removed.items()}
    overrides = LexiconOverrides(removed={c: w for c, w in removed.items() if w},
                                 added=payload.added)
    project = storage.get_active_project()
    if overrides.is_empty():
        project.sentiment_overrides.pop(payload.lang, None)
    else:
        project.sentiment_overrides[payload.lang] = overrides
    storage.save_project(project)
    return {"lang": payload.lang, "overrides": overrides.model_dump()}


# ----- Manual (FR-052) -----

@app.get("/api/manual")
def get_manual() -> dict:
    from .manual import manual_html

    try:
        return {"html": manual_html(i18n.current())}
    except FileNotFoundError:
        raise HTTPException(404, tr("manual_not_found"))


@app.get("/api/version")
def get_version() -> dict:
    return {"version": APP_VERSION}


# ----- Aplicación de escritorio (FR-081) -----
# La ventana propia no descarga archivos como un navegador: guardar y abrir se
# piden por HTTP al servidor, que muestra el diálogo nativo (Principio IV:
# ningún puente JS↔Python fuera de HTTP).

@app.get("/api/app-info")
def app_info() -> dict:
    from . import ocr

    return {"version": APP_VERSION, "mode": app.state.mode, "ocr": ocr.engine_name()}


@app.post("/api/app/save-file")
async def save_file(file: UploadFile, filename: str = "cualibre") -> dict:
    """Guarda un archivo generado por la interfaz (CSV, ZIP, PNG…) con el
    diálogo «Guardar como» del sistema (solo en la ventana propia)."""
    window = app.state.window
    if window is None:
        raise HTTPException(409, "window mode only")
    data = await file.read()
    import webview

    chosen = await run_in_threadpool(
        window.create_file_dialog, webview.FileDialog.SAVE, "", False, Path(filename).name)
    if not chosen:
        return {"saved": None}
    target = Path(chosen if isinstance(chosen, str) else chosen[0])
    await run_in_threadpool(target.write_bytes, data)
    return {"saved": str(target)}


class HtmlPayload(BaseModel):
    name: str
    html: str


@app.post("/api/app/open-report")
def open_report(payload: HtmlPayload) -> dict:
    """Guarda el reporte académico en <datos>/reportes/ y lo abre en el
    navegador del sistema, que es donde mejor se imprime a PDF."""
    import webbrowser

    folder = storage.base_dir() / "reportes"
    folder.mkdir(parents=True, exist_ok=True)
    stem = "".join(c if c.isalnum() or c in "-_ " else "_" for c in payload.name).strip() or "reporte"
    target = folder / f"{stem} {datetime_stamp()}.html"
    target.write_text(payload.html, encoding="utf-8")
    webbrowser.open(target.resolve().as_uri())
    return {"path": str(target)}


def datetime_stamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H%M")


@app.post("/api/app/quit")
def quit_app(payload: ConfirmPayload) -> dict:
    """Apaga el servidor (modo navegador: no hay ventana que cerrar)."""
    if not payload.confirm or app.state.shutdown is None:
        raise HTTPException(409, "not available")
    threading.Timer(0.3, app.state.shutdown).start()  # después de responder
    return {"quitting": True}


# ----- SPA -----

# Caché de la ventana: tras ACTUALIZAR la app, la ventana (WKWebView, WebView2)
# reutilizaba scripts de la versión anterior guardados en su caché, mezclados
# con la portada nueva: claves sin traducir («tab.libro»), menús ausentes y
# funciones viejas (pasó en v1.14.0). Dos defensas:
# 1. la portada pide cada script y estilo con «?v=<versión>»: tras actualizar
#    son direcciones nuevas, que ninguna caché anterior puede responder;
# 2. todo /static se sirve con «no-cache»: se revalida siempre (barato en local).
_STATIC_REF = re.compile(r'((?:src|href)="/static/[^"?#]+\.(?:js|css))"')


@app.get("/", include_in_schema=False)
def index() -> Response:
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    html = _STATIC_REF.sub(rf'\1?v={APP_VERSION}"', html)
    return Response(html, media_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "no-cache"})


class RevalidatedStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/static", RevalidatedStaticFiles(directory=FRONTEND_DIR), name="static")
