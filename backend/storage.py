"""Persistencia local de proyectos.

Un archivo JSON UTF-8 por proyecto en el directorio de datos, con escritura
atómica (temp + os.replace): un cierre abrupto deja o la versión anterior o la
nueva, nunca un archivo a medias (research.md D4, FR-025/026).

Corpus voluminosos: cada acción del investigador (codificar, editar, abrir una
pestaña) necesita el proyecto. Releer y validar varios MB de JSON en cada
petición hacía lenta la app con corpus grandes, así que los proyectos se
guardan también en memoria, validados contra la marca de tiempo y el tamaño
del archivo: el disco sigue siendo la única fuente de verdad (si el archivo
cambia por fuera, se relee).
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Optional

from .i18n import tr
from .models import Project, new_id


def base_dir() -> Path:
    """Directorio de datos por plataforma (macOS, Windows, Linux)."""
    env = os.environ.get("CUALIBRE_DATA_DIR")
    if env:
        return Path(env).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "cualibre"
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "cualibre"
    return home / ".local" / "share" / "cualibre"


def projects_dir() -> Path:
    d = base_dir() / "projects"
    d.mkdir(parents=True, exist_ok=True)
    return d


def trash_dir() -> Path:
    """Proyectos eliminados: se mueven aquí en vez de borrarse (Principio V)."""
    d = base_dir() / "papelera"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    """Resultados de análisis reutilizables (spaCy), regenerables en cualquier momento."""
    d = base_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def music_dir() -> Path:
    """Carpeta donde el investigador deposita su música de foco (FR-040)."""
    d = base_dir() / "musica"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_path() -> Path:
    return base_dir() / "config.json"


def _replace_with_retry(src: str, dst: Path) -> None:
    """os.replace con reintentos: en Windows el antivirus, el indexador o
    OneDrive pueden retener el archivo destino unos milisegundos y el reemplazo
    falla con PermissionError aunque nada esté mal."""
    for attempt in range(8):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(0.05 * (attempt + 1))


def _atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".part")
    try:
        if isinstance(content, bytes):
            with os.fdopen(fd, "wb") as f:
                f.write(content)
        else:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        _replace_with_retry(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_config() -> dict:
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_config(config: dict) -> None:
    _atomic_write(_config_path(), json.dumps(config, ensure_ascii=False, indent=2))


# ----- Caché en memoria de proyectos -----

_cache_lock = threading.Lock()
_cache: dict[str, tuple[int, int, Project]] = {}  # ruta -> (mtime_ns, tamaño, proyecto)


def invalidate_cache() -> None:
    """Olvida los proyectos en memoria (tras un error a mitad de una mutación)."""
    with _cache_lock:
        _cache.clear()


def _stamp(path: Path) -> tuple[int, int]:
    st = path.stat()
    return st.st_mtime_ns, st.st_size


def _load_path(path: Path) -> Project:
    key = str(path)
    stamp = _stamp(path)  # FileNotFoundError si no existe
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[:2] == stamp:
            return cached[2]
    project = Project.model_validate_json(path.read_bytes())
    with _cache_lock:
        _cache[key] = (*stamp, project)
    return project


# ----- Respaldos con historial (FR-062) -----
# Copia periódica del proyecto, restaurable. Se guardan comprimidos (.json.gz):
# con corpus grandes, 40 copias sin comprimir ocupaban cientos de MB.

SNAPSHOT_INTERVAL_S = 600  # a lo más un snapshot cada 10 minutos de trabajo
SNAPSHOT_KEEP = 40


def snapshots_dir(project_id: str) -> Path:
    d = base_dir() / "snapshots" / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _snapshot_files(project_id: str) -> list[Path]:
    """Respaldos del proyecto, del más antiguo al más reciente (el nombre es la fecha)."""
    folder = snapshots_dir(project_id)
    files = list(folder.glob("*.json")) + list(folder.glob("*.json.gz"))
    return sorted(files, key=lambda p: p.name[:15])


def _maybe_snapshot(project: Project, force: bool = False) -> bool:
    from datetime import datetime

    existing = _snapshot_files(project.id)
    if not force:
        if existing:
            last = existing[-1].stat().st_mtime
        else:
            try:
                last = datetime.fromisoformat(project.created_at).timestamp()
            except ValueError:
                last = 0
        if time.time() - last < SNAPSHOT_INTERVAL_S:
            return False
    name = datetime.now().strftime("%Y%m%d-%H%M%S") + ".json.gz"
    payload = gzip.compress(project.model_dump_json().encode("utf-8"), compresslevel=6)
    _atomic_write(snapshots_dir(project.id) / name, payload)
    for old in _snapshot_files(project.id)[:-SNAPSHOT_KEEP]:
        old.unlink(missing_ok=True)
    return True


def list_snapshots(project_id: str) -> list[dict]:
    result = []
    for p in reversed(_snapshot_files(project_id)):
        stem = p.name[:15]
        result.append({
            "name": p.name,
            "saved_at": f"{stem[:4]}-{stem[4:6]}-{stem[6:8]} {stem[9:11]}:{stem[11:13]}:{stem[13:15]}",
            "size_kb": p.stat().st_size // 1024,
        })
    return result


def load_snapshot(project_id: str, name: str) -> Optional[Project]:
    if name != Path(name).name:  # sin traversal
        return None
    path = snapshots_dir(project_id) / name
    try:
        raw = path.read_bytes()
        if name.endswith(".gz"):
            raw = gzip.decompress(raw)
        return Project.model_validate_json(raw)
    except (FileNotFoundError, ValueError, OSError):
        return None


# ----- Proyectos -----

def save_project(project: Project) -> None:
    from .models import now_iso

    project.updated_at = now_iso()
    path = projects_dir() / f"{project.id}.json"
    _atomic_write(path, project.model_dump_json(indent=2))
    with _cache_lock:
        _cache[str(path)] = (*_stamp(path), project)
    _maybe_snapshot(project)


def load_project(project_id: str) -> Optional[Project]:
    if project_id != Path(project_id).name:  # sin traversal
        return None
    try:
        return _load_path(projects_dir() / f"{project_id}.json")
    except FileNotFoundError:
        return None


def list_projects() -> list[Project]:
    projects = []
    for path in sorted(projects_dir().glob("*.json")):
        try:
            projects.append(_load_path(path))
        except Exception:
            continue  # archivo ajeno o corrupto: no debe tumbar la app
    projects.sort(key=lambda p: p.created_at)
    return projects


def get_active_project() -> Project:
    """Proyecto activo; si no existe ninguno, crea uno vacío (contracts/api.md)."""
    config = read_config()
    active_id = config.get("active_project_id")
    if active_id:
        project = load_project(active_id)
        if project is not None:
            return project
    existing = list_projects()
    if existing:
        project = existing[0]
    else:
        project = Project(name=tr("default_project_name"))
        save_project(project)
    set_active_project(project.id)
    return project


def set_active_project(project_id: str) -> None:
    config = read_config()
    config["active_project_id"] = project_id
    write_config(config)


def delete_project(project_id: str) -> bool:
    """Mueve el proyecto a la papelera (recuperable a mano) y deja de listarlo."""
    path = projects_dir() / f"{project_id}.json"
    if project_id != Path(project_id).name or not path.exists():
        return False
    stamp = time.strftime("%Y%m%d-%H%M%S")
    _replace_with_retry(str(path), trash_dir() / f"{project_id}-{stamp}.json")
    invalidate_cache()
    config = read_config()
    if config.get("active_project_id") == project_id:
        config.pop("active_project_id", None)
        write_config(config)
    return True


def parse_project_file(data: bytes) -> Project:
    """Lee un proyecto desde un respaldo .zip (FR-070) o un .json suelto.

    Lanza ValueError si el contenido no es un proyecto de Cua-libre."""
    if data[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = [n for n in zf.namelist() if n.endswith(".json") and "/" not in n]
                if not names:
                    raise ValueError("zip sin proyecto")
                name = "proyecto.json" if "proyecto.json" in names else names[0]
                data = zf.read(name)
        except zipfile.BadZipFile as exc:
            raise ValueError("zip dañado") from exc
    if data[:2] == b"\x1f\x8b":  # respaldo del historial (.json.gz)
        data = gzip.decompress(data)
    return Project.model_validate_json(data)


def import_project(project: Project) -> Project:
    """Guarda un proyecto importado con identidad nueva: importar dos veces el
    mismo respaldo nunca sobrescribe el trabajo existente."""
    project.id = new_id()
    taken = {p.name for p in list_projects()}
    if project.name in taken:
        project.name = f"{project.name} {tr('imported_suffix')}"
    save_project(project)
    set_active_project(project.id)
    return project
