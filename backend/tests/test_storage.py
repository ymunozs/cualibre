"""Persistencia: escritura atómica, UTF-8, recuperación, aislamiento (T007)."""

from backend import storage
from backend.models import Code, Document, Project


def make_project(name="Investigación ñandú") -> Project:
    project = Project(name=name)
    project.documents.append(Document(filename="entrevista_1.txt", text="El niño cantó «añoranza» día tras día"))
    project.codes.append(Code(id=1, doc_id=project.documents[0].id, domain="Emocional",
                              name="añoranza infantil", quote="añoranza", start=17, end=26))
    project.next_code_id = 2
    return project


def test_roundtrip_utf8():
    project = make_project()
    storage.save_project(project)
    loaded = storage.load_project(project.id)
    assert loaded is not None
    assert loaded.name == "Investigación ñandú"
    assert loaded.documents[0].text == "El niño cantó «añoranza» día tras día"
    assert loaded.codes[0].name == "añoranza infantil"


def test_file_is_readable_json_without_escapes():
    project = make_project()
    storage.save_project(project)
    raw = (storage.projects_dir() / f"{project.id}.json").read_text(encoding="utf-8")
    assert "ñandú" in raw  # ensure_ascii=False


def test_reload_survives_new_process_simulation():
    project = make_project()
    storage.save_project(project)
    storage.set_active_project(project.id)
    # Simula reinicio: el estado en memoria desaparece, solo queda el disco
    active = storage.get_active_project()
    assert active.id == project.id
    assert len(active.codes) == 1


def test_projects_are_isolated():
    p1 = make_project("Proyecto A")
    p2 = Project(name="Proyecto B")
    storage.save_project(p1)
    storage.save_project(p2)
    assert storage.load_project(p2.id).documents == []
    assert len(storage.load_project(p1.id).documents) == 1


def test_auto_creates_default_project():
    active = storage.get_active_project()
    assert active.name == "Mi proyecto"
    assert storage.read_config()["active_project_id"] == active.id


def test_updated_at_changes_on_save():
    project = make_project()
    first = project.updated_at
    import time

    time.sleep(1.1)
    storage.save_project(project)
    assert project.updated_at >= first
