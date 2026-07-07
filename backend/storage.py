"""Persistencia local de proyectos.

Un archivo JSON UTF-8 por proyecto en el directorio de datos, con escritura
atómica (temp + os.replace): un cierre abrupto deja o la versión anterior o la
nueva, nunca un archivo a medias (research.md D4, FR-025/026).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from .models import Project


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


def music_dir() -> Path:
    """Carpeta donde el investigador deposita su música de foco (FR-040)."""
    d = base_dir() / "musica"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_path() -> Path:
    return base_dir() / "config.json"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
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


# Respaldos con historial (FR-062): copia periódica del proyecto, restaurable
SNAPSHOT_INTERVAL_S = 600  # a lo más un snapshot cada 10 minutos de trabajo
SNAPSHOT_KEEP = 40


def snapshots_dir(project_id: str) -> Path:
    d = base_dir() / "snapshots" / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _maybe_snapshot(project: Project, force: bool = False) -> bool:
    import time
    from datetime import datetime

    folder = snapshots_dir(project.id)
    existing = sorted(folder.glob("*.json"))
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
    name = datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
    _atomic_write(folder / name, project.model_dump_json(indent=2))
    for old in sorted(folder.glob("*.json"))[:-SNAPSHOT_KEEP]:
        old.unlink(missing_ok=True)
    return True


def list_snapshots(project_id: str) -> list[dict]:
    return [
        {"name": p.name, "saved_at": f"{p.stem[:4]}-{p.stem[4:6]}-{p.stem[6:8]} {p.stem[9:11]}:{p.stem[11:13]}:{p.stem[13:15]}",
         "size_kb": p.stat().st_size // 1024}
        for p in sorted(snapshots_dir(project_id).glob("*.json"), reverse=True)
    ]


def load_snapshot(project_id: str, name: str) -> Optional[Project]:
    if name != Path(name).name:  # sin traversal
        return None
    path = snapshots_dir(project_id) / name
    try:
        return Project.model_validate_json(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def save_project(project: Project) -> None:
    from .models import now_iso

    project.updated_at = now_iso()
    path = projects_dir() / f"{project.id}.json"
    _atomic_write(path, project.model_dump_json(indent=2))
    _maybe_snapshot(project)


def load_project(project_id: str) -> Optional[Project]:
    path = projects_dir() / f"{project_id}.json"
    try:
        return Project.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def list_projects() -> list[Project]:
    projects = []
    for path in sorted(projects_dir().glob("*.json")):
        try:
            projects.append(Project.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue  # archivo ajeno o corrupto: no debe tumbar la app
    projects.sort(key=lambda p: p.created_at)
    return projects


def get_active_project() -> Project:
    """Proyecto activo; si no existe ninguno, crea 'Mi proyecto' (contracts/api.md)."""
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
        project = Project(name="Mi proyecto")
        save_project(project)
    set_active_project(project.id)
    return project


def set_active_project(project_id: str) -> None:
    config = read_config()
    config["active_project_id"] = project_id
    write_config(config)
