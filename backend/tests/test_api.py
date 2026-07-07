"""Contrato HTTP completo (T008, T017, T021, T028, T031, T044)."""

import httpx
import pytest

from backend.tests.test_extraction import make_docx, make_pdf


# ----- Proyectos (T008) -----

def test_default_project_autocreated(client):
    project = client.get("/api/project").json()
    assert project["name"] == "Mi proyecto"
    assert project["documents"] == [] and project["codes"] == []


def test_project_lifecycle(client):
    created = client.post("/api/projects", json={"name": "Tesis doctoral"})
    assert created.status_code == 201
    pid = created.json()["id"]

    renamed = client.patch(f"/api/projects/{pid}", json={"name": "Tesis final"})
    assert renamed.json()["name"] == "Tesis final"

    listed = client.get("/api/projects").json()
    assert any(p["name"] == "Tesis final" for p in listed)

    activated = client.post(f"/api/projects/{pid}/activate")
    assert activated.status_code == 200
    assert client.get("/api/project").json()["id"] == pid


def test_project_name_validation(client):
    assert client.post("/api/projects", json={"name": "   "}).status_code == 422


def test_reset_requires_confirmation(client):
    assert client.post("/api/project/reset", json={"confirm": False}).status_code == 400
    assert client.post("/api/project/reset", json={}).status_code == 400
    assert client.post("/api/project/reset", json={"confirm": True}).status_code == 200


# ----- Documentos (T017) -----

def upload_txt(client, name="entrevista.txt", text="La añoranza del niño es profunda y persistente"):
    return client.post("/api/documents", files={"file": (name, text.encode("utf-8"), "text/plain")})


def test_upload_three_formats(client):
    assert upload_txt(client).status_code == 201
    pdf = client.post("/api/documents", files={"file": ("paper.pdf", make_pdf(), "application/pdf")})
    assert pdf.status_code == 201
    dx = client.post("/api/documents", files={"file": ("tesis.docx", make_docx(), "application/octet-stream")})
    assert dx.status_code == 201
    docs = client.get("/api/project").json()["documents"]
    assert [d["filename"] for d in docs] == ["entrevista.txt", "paper.pdf", "tesis.docx"]
    assert "añoranza" in docs[0]["text"]


def test_upload_unsupported_type(client):
    r = client.post("/api/documents", files={"file": ("foto.png", b"\x89PNG", "image/png")})
    assert r.status_code == 415
    assert client.get("/api/project").json()["documents"] == []


def test_upload_corrupt_keeps_corpus_intact(client):
    upload_txt(client)
    r = client.post("/api/documents", files={"file": ("roto.pdf", b"no es pdf", "application/pdf")})
    assert r.status_code == 422
    assert len(client.get("/api/project").json()["documents"]) == 1


def make_code_payload(doc_id, **overrides):
    payload = {"doc_id": doc_id, "domain": "Emocional", "name": "añoranza",
               "quote": "añoranza", "start": 3, "end": 11, "memo": ""}
    payload.update(overrides)
    return payload


def test_delete_document_without_codes(client):
    doc = upload_txt(client).json()
    r = client.delete(f"/api/documents/{doc['id']}")
    assert r.status_code == 200 and r.json()["deleted_codes"] == 0


def test_delete_document_with_codes_requires_confirm(client):
    doc = upload_txt(client).json()
    client.post("/api/codes", json=make_code_payload(doc["id"]))
    r = client.delete(f"/api/documents/{doc['id']}")
    assert r.status_code == 409
    assert r.headers["X-Code-Count"] == "1"
    r2 = client.delete(f"/api/documents/{doc['id']}?confirm=true")
    assert r2.status_code == 200 and r2.json()["deleted_codes"] == 1
    project = client.get("/api/project").json()
    assert project["documents"] == [] and project["codes"] == []


# ----- Códigos (T021, T031) -----

def test_create_anchored_code(client):
    doc = upload_txt(client).json()
    r = client.post("/api/codes", json=make_code_payload(doc["id"]))
    assert r.status_code == 201
    code = r.json()
    assert code["id"] == 1 and code["domain"] == "Emocional"
    # Persistido de inmediato
    assert client.get("/api/project").json()["codes"][0]["name"] == "añoranza"


def test_create_code_validations(client):
    doc = upload_txt(client).json()
    base = make_code_payload(doc["id"])
    assert client.post("/api/codes", json={**base, "domain": "Inventado"}).status_code == 422
    assert client.post("/api/codes", json={**base, "name": "  "}).status_code == 422
    assert client.post("/api/codes", json={**base, "start": 5, "end": 5}).status_code == 422
    assert client.post("/api/codes", json={**base, "start": -1}).status_code == 422
    assert client.post("/api/codes", json={**base, "end": 10_000}).status_code == 422
    assert client.post("/api/codes", json={**base, "doc_id": "inexistente"}).status_code == 422


def test_manual_code(client):
    r = client.post("/api/codes", json={"domain": "Teórico", "name": "mediación", "memo": "ver Vygotski"})
    assert r.status_code == 201
    code = r.json()
    assert code["doc_id"] is None and code["start"] is None and code["quote"] == ""
    # Manual con offsets → inválido
    bad = client.post("/api/codes", json={"domain": "Teórico", "name": "x", "start": 0, "end": 3})
    assert bad.status_code == 422


def test_code_ids_never_reused(client):
    client.post("/api/codes", json={"domain": "Teórico", "name": "uno"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "dos"})
    client.delete("/api/codes/2")
    third = client.post("/api/codes", json={"domain": "Teórico", "name": "tres"}).json()
    assert third["id"] == 3


def test_update_code(client):
    doc = upload_txt(client).json()
    code = client.post("/api/codes", json=make_code_payload(doc["id"])).json()
    r = client.patch(f"/api/codes/{code['id']}",
                     json={"name": "nostalgia", "domain": "Crítico", "memo": "revisar"})
    updated = r.json()
    assert updated["name"] == "nostalgia" and updated["domain"] == "Crítico"
    # Anclaje inmutable: PATCH no acepta offsets (se ignoran campos extra)
    assert updated["start"] == 3 and updated["end"] == 11


def test_update_code_invalid_domain(client):
    client.post("/api/codes", json={"domain": "Teórico", "name": "uno"})
    assert client.patch("/api/codes/1", json={"domain": "Falso"}).status_code == 422


def test_delete_code(client):
    client.post("/api/codes", json={"domain": "Teórico", "name": "uno"})
    assert client.delete("/api/codes/1").status_code == 204
    assert client.delete("/api/codes/1").status_code == 404
    assert client.get("/api/project").json()["codes"] == []


# ----- Persistencia y aislamiento (T028) -----

def test_state_survives_app_restart(client):
    doc = upload_txt(client).json()
    client.post("/api/codes", json=make_code_payload(doc["id"]))
    # Nuevo cliente = nuevo "proceso" sobre el mismo disco
    from backend.app import app
    from fastapi.testclient import TestClient

    fresh = TestClient(app)
    project = fresh.get("/api/project").json()
    assert len(project["documents"]) == 1 and len(project["codes"]) == 1


def test_projects_isolated_via_api(client):
    upload_txt(client)
    second = client.post("/api/projects", json={"name": "Otro estudio"}).json()
    assert client.get("/api/project").json()["documents"] == []
    projects = {p["name"]: p for p in client.get("/api/projects").json()}
    assert projects["Mi proyecto"]["doc_count"] == 1
    assert projects["Otro estudio"]["doc_count"] == 0


# ----- NLP endpoint -----

def test_nlp_endpoint(client):
    upload_txt(client, text="escuela escuela escuela emociones emociones para con del")
    words = client.get("/api/nlp?lang=es&min_len=4").json()["words"]
    assert words[0] == {"word": "escuela", "count": 3}
    assert all(w["word"] != "para" for w in words)
    assert client.get("/api/nlp?lang=fr").status_code == 422


# ----- Export endpoint -----

def test_export_endpoint(client):
    doc = upload_txt(client).json()
    client.post("/api/codes", json=make_code_payload(doc["id"], name="añoranza, viva"))
    r = client.get("/api/export.csv")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    body = r.content.decode("utf-8-sig")
    assert "añoranza, viva" in body


# ----- Literatura (T044, transporte mockeado) -----

def test_literature_maps_results(client, monkeypatch):
    def fake_search(query, client=None):
        return [{"title": "Vygotsky and Emotions", "year": 2019, "cited_by_count": 42,
                 "doi": "https://doi.org/10.1000/xyz"}]

    monkeypatch.setattr("backend.app.search_works", fake_search)
    r = client.get("/api/literature?q=vygotsky")
    assert r.json()["results"][0]["cited_by_count"] == 42


def test_literature_network_failure(client, monkeypatch):
    from backend.literature import LiteratureError

    def fail(query, client=None):
        raise LiteratureError("No se pudo consultar OpenAlex (¿hay conexión a internet?). Tu trabajo local no se ve afectado.")

    monkeypatch.setattr("backend.app.search_works", fail)
    r = client.get("/api/literature?q=x")
    assert r.status_code == 502
    assert "internet" in r.json()["detail"]


def test_literature_client_maps_openalex_payload(monkeypatch):
    from backend.literature import search_works

    payload = {"results": [{"display_name": "T", "publication_year": 2020,
                            "cited_by_count": 7, "doi": "https://doi.org/10/abc"}]}

    def handler(request):
        assert request.url.host == "api.openalex.org"
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        results = search_works("test", client=http_client)
    assert results == [{"title": "T", "year": 2020, "cited_by_count": 7,
                        "doi": "https://doi.org/10/abc"}]


def test_nlp_exclusions_persist_and_apply(client):
    upload_txt(client, text="Entrevistado dice escuela escuela Entrevistado dice música")
    r = client.put("/api/nlp/exclusions", json={"words": ["Entrevistado", "  dice ", ""]})
    assert r.json()["exclusions"] == ["Entrevistado", "dice"]
    data = client.get("/api/nlp?lang=es&min_len=4").json()
    words = {w["word"] for w in data["words"]}
    assert "entrevistado" not in words and "dice" not in words
    assert "escuela" in words
    assert data["exclusions"] == ["Entrevistado", "dice"]
    # persistido en el proyecto
    assert client.get("/api/project").json()["nlp_exclusions"] == ["Entrevistado", "dice"]


def test_manual_endpoint(client):
    r = client.get("/api/manual")
    assert r.status_code == 200
    html = r.json()["html"]
    assert "<h1>" in html and "Manual de uso" in html
    assert "<table" in html and "Nube Negra" in html


def test_nlp_pos_endpoint(client):
    upload_txt(client, text="El niño cantó en la escuela. Los niños cantaban felices.")
    verbs = client.get("/api/nlp?lang=es&min_len=4&pos=verb").json()["words"]
    assert any(w["word"] == "cantar" for w in verbs)
    assert all(w["word"] != "escuela" for w in verbs)
    assert client.get("/api/nlp?pos=adverbio").status_code == 422
