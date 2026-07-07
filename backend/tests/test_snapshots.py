"""Respaldos con historial: creación forzada, listado, restauración (FR-062)."""

from backend import storage
from backend.models import Project


def test_no_snapshots_initially(client):
    r = client.get("/api/snapshots")
    assert r.json()["snapshots"] == []


def test_save_creates_forced_snapshot(client):
    client.post("/api/codes", json={"domain": "Teórico", "name": "uno"})
    r = client.post("/api/project/save")
    assert r.status_code == 200
    snaps = client.get("/api/snapshots").json()["snapshots"]
    assert len(snaps) == 1
    assert "saved_at" in snaps[0] and snaps[0]["size_kb"] >= 0


def test_restore_requires_confirmation_and_recovers_state(client):
    client.post("/api/codes", json={"domain": "Teórico", "name": "original"})
    client.post("/api/project/save")  # snapshot con "original"
    snap_name = client.get("/api/snapshots").json()["snapshots"][0]["name"]

    client.post("/api/codes", json={"domain": "Teórico", "name": "nuevo"})
    assert len(client.get("/api/project").json()["codes"]) == 2

    assert client.post(f"/api/snapshots/{snap_name}/restore", json={"confirm": False}).status_code == 400
    r = client.post(f"/api/snapshots/{snap_name}/restore", json={"confirm": True})
    assert r.status_code == 200
    restored = client.get("/api/project").json()
    assert [c["name"] for c in restored["codes"]] == ["original"]


def test_restore_unknown_snapshot(client):
    r = client.post("/api/snapshots/no-existe.json/restore", json={"confirm": True})
    assert r.status_code == 404


def test_restore_rejects_path_traversal(client):
    r = client.post("/api/snapshots/..%2Fconfig.json/restore", json={"confirm": True})
    assert r.status_code == 404


def test_restore_preserves_project_identity(client):
    original_id = client.get("/api/project").json()["id"]
    client.post("/api/project/save")
    snap_name = client.get("/api/snapshots").json()["snapshots"][0]["name"]
    client.post(f"/api/snapshots/{snap_name}/restore", json={"confirm": True})
    assert client.get("/api/project").json()["id"] == original_id


def test_no_immediate_snapshot_for_new_project():
    # Un proyecto recién creado no genera snapshot hasta que pase el intervalo
    # o se fuerce explícitamente (evita ruido al arrancar la app).
    project = Project(name="Throttle test")
    storage.save_project(project)
    assert storage.list_snapshots(project.id) == []


def test_forced_snapshot_ignores_throttle():
    project = Project(name="Force test")
    storage.save_project(project)  # sin snapshot (recién creado)
    created = storage._maybe_snapshot(project, force=True)
    assert created is True
    assert len(storage.list_snapshots(project.id)) == 1
