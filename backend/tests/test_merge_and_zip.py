"""Fusión de códigos en bloque (FR-068) y respaldo completo en .zip (FR-070)."""

import io
import json
import zipfile


def seed(client, doc_text="La escuela y el río enseñan mucho al niño."):
    doc = client.post("/api/documents",
                      files={"file": ("e.txt", doc_text.encode(), "text/plain")}).json()
    return doc


# ----- Fusión / renombre -----

def test_merge_pure_rename_preserves_domain(client):
    doc = seed(client)
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional",
                                    "name": "el río enseña", "quote": "río",
                                    "start": doc["text"].index("río"),
                                    "end": doc["text"].index("río") + 3})
    r = client.post("/api/codes/merge", json={"from_name": "el río enseña",
                                              "to_name": "conocimiento situado"})
    assert r.status_code == 200
    data = r.json()
    assert data == {"merged": 1, "name": "conocimiento situado", "domain": None}
    code = client.get("/api/project").json()["codes"][0]
    assert code["name"] == "conocimiento situado"
    assert code["domain"] == "Emocional"  # renombre puro: dominio intacto


def test_merge_into_existing_adopts_target_domain(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "B"})
    r = client.post("/api/codes/merge", json={"from_name": "A", "to_name": "B"})
    assert r.json() == {"merged": 1, "name": "B", "domain": "Teórico"}
    codes = client.get("/api/project").json()["codes"]
    assert all(c["name"] == "B" and c["domain"] == "Teórico" for c in codes)


def test_merge_with_explicit_domain_override(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "B"})
    r = client.post("/api/codes/merge",
                    json={"from_name": "A", "to_name": "B", "domain": "Crítico"})
    assert r.json()["domain"] == "Crítico"
    codes = client.get("/api/project").json()["codes"]
    assert all(c["domain"] == "Crítico" for c in codes)


def test_merge_multiple_instances(client):
    for i in range(3):
        client.post("/api/codes", json={"domain": "Emocional", "name": "viejo"})
    r = client.post("/api/codes/merge", json={"from_name": "viejo", "to_name": "nuevo"})
    assert r.json()["merged"] == 3


def test_merge_unknown_source_404(client):
    r = client.post("/api/codes/merge", json={"from_name": "NoExiste", "to_name": "X"})
    assert r.status_code == 404


def test_merge_same_name_rejected(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    r = client.post("/api/codes/merge", json={"from_name": "A", "to_name": "A"})
    assert r.status_code == 422


def test_merge_invalid_explicit_domain(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    r = client.post("/api/codes/merge",
                    json={"from_name": "A", "to_name": "B", "domain": "Inventado"})
    assert r.status_code == 422


def test_merge_remaps_relations_instead_of_deleting(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "B"})
    client.post("/api/relations", json={"source": "A", "target": "B", "type": "asociación"})
    client.post("/api/codes/merge", json={"from_name": "A", "to_name": "C"})
    relations = client.get("/api/project").json()["relations"]
    assert len(relations) == 1
    assert relations[0]["source"] == "C" and relations[0]["target"] == "B"


def test_merge_drops_reflexive_relation_after_remap(client):
    client.post("/api/codes", json={"domain": "Emocional", "name": "A"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "B"})
    client.post("/api/relations", json={"source": "A", "target": "B", "type": "causalidad"})
    # Fusionar B dentro de A: la relación A→B se vuelve A→A y debe descartarse
    client.post("/api/codes/merge", json={"from_name": "B", "to_name": "A"})
    assert client.get("/api/project").json()["relations"] == []


# ----- Export .zip -----

def test_export_zip_contains_expected_files(client):
    doc = seed(client)
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional",
                                    "name": "añoranza", "quote": "escuela",
                                    "start": doc["text"].index("escuela"),
                                    "end": doc["text"].index("escuela") + 7,
                                    "memo": "revisar"})
    r = client.get("/api/export.zip")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    assert r.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert "proyecto.json" in names
    assert "codigos.csv" in names
    assert "LEEME.txt" in names
    assert any(n.startswith("documentos/") and n.endswith(".txt") for n in names)


def test_export_zip_json_is_full_fidelity(client):
    doc = seed(client)
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional",
                                    "name": "código", "quote": "río",
                                    "start": doc["text"].index("río"),
                                    "end": doc["text"].index("río") + 3})
    project_before = client.get("/api/project").json()
    zf = zipfile.ZipFile(io.BytesIO(client.get("/api/export.zip").content))
    project_from_zip = json.loads(zf.read("proyecto.json"))
    assert project_from_zip["id"] == project_before["id"]
    assert project_from_zip["codes"][0]["name"] == "código"


def test_export_zip_document_text_matches(client):
    text = "Contenido íntegro con tildes y ñ del documento."
    seed(client, text)
    zf = zipfile.ZipFile(io.BytesIO(client.get("/api/export.zip").content))
    doc_files = [n for n in zf.namelist() if n.startswith("documentos/")]
    assert len(doc_files) == 1
    assert zf.read(doc_files[0]).decode("utf-8") == text


def test_export_zip_handles_duplicate_filenames(client):
    client.post("/api/documents", files={"file": ("a.txt", b"uno", "text/plain")})
    client.post("/api/documents", files={"file": ("a.txt", b"dos", "text/plain")})
    zf = zipfile.ZipFile(io.BytesIO(client.get("/api/export.zip").content))
    doc_files = sorted(n for n in zf.namelist() if n.startswith("documentos/"))
    assert len(doc_files) == 2
    assert doc_files[0] != doc_files[1]
