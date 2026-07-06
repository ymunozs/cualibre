"""Relaciones entre códigos y guardado explícito (T051, FR-036/038)."""


def seed_codes(client, names=("añoranza", "escuela", "mediación")):
    for name in names:
        client.post("/api/codes", json={"domain": "Teórico", "name": name})


def test_save_endpoint(client):
    r = client.post("/api/project/save")
    assert r.status_code == 200
    assert "updated_at" in r.json()


def test_relation_types_endpoint(client):
    types = client.get("/api/relation-types").json()
    assert set(types) == {"jerarquía", "asociación", "causalidad", "contradicción"}


def test_create_and_delete_relation(client):
    seed_codes(client)
    r = client.post("/api/relations", json={"source": "añoranza", "target": "escuela", "type": "asociación"})
    assert r.status_code == 201
    relation = r.json()
    assert relation["id"] == 1
    assert len(client.get("/api/project").json()["relations"]) == 1
    assert client.delete(f"/api/relations/{relation['id']}").status_code == 204
    assert client.get("/api/project").json()["relations"] == []
    assert client.delete("/api/relations/99").status_code == 404


def test_relation_validations(client):
    seed_codes(client)
    base = {"source": "añoranza", "target": "escuela", "type": "asociación"}
    assert client.post("/api/relations", json={**base, "type": "amistad"}).status_code == 422
    assert client.post("/api/relations", json={**base, "target": "añoranza"}).status_code == 422
    assert client.post("/api/relations", json={**base, "source": "inexistente"}).status_code == 422
    assert client.post("/api/relations", json=base).status_code == 201
    assert client.post("/api/relations", json=base).status_code == 409  # duplicado exacto
    # mismo par con otro tipo sí es válido
    assert client.post("/api/relations", json={**base, "type": "causalidad"}).status_code == 201


def test_relations_pruned_on_code_delete(client):
    seed_codes(client)
    client.post("/api/relations", json={"source": "añoranza", "target": "escuela", "type": "jerarquía"})
    codes = client.get("/api/project").json()["codes"]
    escuela_id = next(c["id"] for c in codes if c["name"] == "escuela")
    client.delete(f"/api/codes/{escuela_id}")
    assert client.get("/api/project").json()["relations"] == []


def test_relations_survive_rename_of_other_instances(client):
    # dos instancias con el mismo nombre: renombrar una no borra la relación
    seed_codes(client, ("añoranza", "escuela"))
    client.post("/api/codes", json={"domain": "Emocional", "name": "añoranza"})
    client.post("/api/relations", json={"source": "añoranza", "target": "escuela", "type": "asociación"})
    client.patch("/api/codes/1", json={"name": "nostalgia"})
    # sigue existiendo otra instancia llamada "añoranza" → la relación se conserva
    assert len(client.get("/api/project").json()["relations"]) == 1
    client.patch("/api/codes/3", json={"name": "morriña"})
    # ya no queda ninguna "añoranza" → poda
    assert client.get("/api/project").json()["relations"] == []


def test_relations_pruned_on_document_delete(client):
    text = "La añoranza del niño es profunda y persistente"
    doc = client.post("/api/documents",
                      files={"file": ("e.txt", text.encode(), "text/plain")}).json()
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional",
                                    "name": "anclado", "quote": "añoranza", "start": 3, "end": 11})
    client.post("/api/codes", json={"domain": "Teórico", "name": "libre"})
    client.post("/api/relations", json={"source": "anclado", "target": "libre", "type": "causalidad"})
    client.delete(f"/api/documents/{doc['id']}?confirm=true")
    assert client.get("/api/project").json()["relations"] == []


def test_reset_clears_relations(client):
    seed_codes(client)
    client.post("/api/relations", json={"source": "añoranza", "target": "escuela", "type": "asociación"})
    client.post("/api/project/reset", json={"confirm": True})
    project = client.get("/api/project").json()
    assert project["relations"] == [] and project["next_relation_id"] == 1
