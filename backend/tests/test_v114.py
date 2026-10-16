"""v1.14: libro de códigos (FR-084), relaciones con categorías y cuadros
organizadores editables (FR-085) y ajustes del léxico de sentimiento (FR-086)."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from backend import analysis, qdpx, storage
from backend.models import Project

XSD = Path(__file__).parent / "data" / "REFI-QDA-Project-1.0.xsd"


def code(client, name, domain="Teórico", **extra):
    r = client.post("/api/codes", json={"domain": domain, "name": name, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def upload(client, text, name="e.txt"):
    r = client.post("/api/documents", files={"file": (name, text.encode("utf-8"), "text/plain")})
    assert r.status_code == 201, r.text
    return r.json()


def project(client):
    return client.get("/api/project").json()


# ----- Compatibilidad -----

def test_project_from_v113_loads_with_defaults():
    old = {"id": "abc", "name": "viejo", "codes": [], "documents": [],
           "relations": [{"id": 1, "source": "a", "target": "b", "type": "asociación"}]}
    loaded = Project.model_validate_json(json.dumps(old))
    assert loaded.codebook == {} and loaded.category_notes == {}
    assert loaded.general_board.id == 0 and loaded.boards == []
    assert loaded.sentiment_overrides == {}
    assert loaded.relations[0].source_kind == "code" and loaded.relations[0].target_kind == "code"


# ----- Libro de códigos (FR-084) -----

def test_codebook_entry_save_clear_and_validation(client):
    code(client, "añoranza")
    entry = {"kind": "code", "name": "añoranza", "definition": "Deseo de volver.",
             "inclusion": "Cuando se evoca el pasado.", "exclusion": "", "example": ""}
    r = client.put("/api/codebook", json=entry)
    assert r.status_code == 200 and r.json()["entry"]["definition"] == "Deseo de volver."
    assert project(client)["codebook"]["añoranza"]["inclusion"] == "Cuando se evoca el pasado."
    # Vaciar todos los apartados retira la ficha
    r = client.put("/api/codebook", json={**entry, "definition": "", "inclusion": "  "})
    assert r.json()["entry"] is None and project(client)["codebook"] == {}
    # Código o categoría inexistente, tipo inválido
    assert client.put("/api/codebook", json={**entry, "name": "nada"}).status_code == 422
    assert client.put("/api/codebook", json={**entry, "kind": "grupo"}).status_code == 422


def test_category_notes_accept_basic_keys_with_slash(client):
    r = client.put("/api/codebook", json={"kind": "category", "name": "Tensión/CHAT",
                                          "definition": "Contradicciones del sistema de actividad."})
    assert r.status_code == 200
    notes = project(client)["category_notes"]
    assert notes["Tensión/CHAT"]["definition"].startswith("Contradicciones")
    assert client.put("/api/codebook", json={"kind": "category", "name": "Inventada",
                                             "definition": "x"}).status_code == 422


def test_codebook_survives_delete_and_undo(client):
    c = code(client, "rito")
    client.put("/api/codebook", json={"kind": "code", "name": "rito", "definition": "Gesto repetido."})
    assert client.delete(f"/api/codes/{c['id']}").status_code == 204
    # La descripción no se pierde aunque el código ya no tenga instancias
    assert project(client)["codebook"]["rito"]["definition"] == "Gesto repetido."
    code(client, "rito")  # recodificar recupera la ficha
    assert project(client)["codebook"]["rito"]["definition"] == "Gesto repetido."
    # Eliminar la descripción huérfana exige confirmación
    assert client.delete("/api/codebook", params={"kind": "code", "name": "rito"}).status_code == 400
    assert client.delete("/api/codebook", params={"kind": "code", "name": "rito",
                                                  "confirm": True}).status_code == 200
    assert project(client)["codebook"] == {}


def test_merge_joins_descriptions_without_losing_text(client):
    code(client, "a")
    code(client, "b")
    client.put("/api/codebook", json={"kind": "code", "name": "a", "definition": "Def A",
                                      "example": "Ej A"})
    client.put("/api/codebook", json={"kind": "code", "name": "b", "definition": "Def B"})
    assert client.post("/api/codes/merge", json={"from_name": "a", "to_name": "b"}).status_code == 200
    book = project(client)["codebook"]
    assert "a" not in book
    assert book["b"]["definition"] == "Def B\n\nDef A" and book["b"]["example"] == "Ej A"


def test_rename_last_instance_carries_description(client):
    c = code(client, "viejo")
    client.put("/api/codebook", json={"kind": "code", "name": "viejo", "definition": "D"})
    client.patch(f"/api/codes/{c['id']}", json={"name": "nuevo"})
    book = project(client)["codebook"]
    assert "viejo" not in book and book["nuevo"]["definition"] == "D"


def test_codebook_csv_and_zip(client):
    code(client, "añoranza", domain="Emocional")
    client.put("/api/codebook", json={"kind": "code", "name": "añoranza",
                                      "definition": "Deseo; con «comillas»"})
    client.put("/api/codebook", json={"kind": "category", "name": "Emocional",
                                      "definition": "Afectos"})
    r = client.get("/api/codebook.csv")
    assert r.status_code == 200
    assert r.content.startswith("﻿".encode("utf-8"))
    text = r.content.decode("utf-8-sig")
    assert "categoría,Emocional" in text and "Deseo; con «comillas»" in text
    english = client.get("/api/codebook.csv?ui=en").content.decode("utf-8-sig")
    assert english.startswith("type,name") and "category,Emotional" in english
    with zipfile.ZipFile(io.BytesIO(client.get("/api/export.zip").content)) as zf:
        assert "libro_de_codigos.csv" in zf.namelist()
        assert "añoranza" in zf.read("libro_de_codigos.csv").decode("utf-8-sig")


def test_reset_clears_codebook_and_boards_after_snapshot(client):
    code(client, "a")
    code(client, "b")
    client.put("/api/codebook", json={"kind": "code", "name": "a", "definition": "D"})
    client.post("/api/boards", json={"name": "Mi cuadro"})
    before = len(client.get("/api/snapshots").json()["snapshots"])
    r = client.post("/api/project/reset", json={"confirm": True})
    assert r.status_code == 200
    data = r.json()
    assert data["codebook"] == {} and data["boards"] == [] and data["next_board_id"] == 1
    assert len(client.get("/api/snapshots").json()["snapshots"]) > before


# ----- Relaciones con categorías y cuadros (FR-085) -----

def test_relation_between_code_and_category(client):
    code(client, "añoranza", domain="Emocional")
    rel = {"source": "añoranza", "target": "Tensión/CHAT", "type": "causalidad",
           "target_kind": "category"}
    r = client.post("/api/relations", json=rel)
    assert r.status_code == 201
    assert r.json()["target_kind"] == "category" and r.json()["source_kind"] == "code"
    assert client.post("/api/relations", json=rel).status_code == 409
    # Categoría inexistente
    assert client.post("/api/relations", json={**rel, "target": "Inventada"}).status_code == 422
    # Editar un código no borra relaciones con categorías (antes, la poda las eliminaba)
    c = project(client)["codes"][0]
    client.patch(f"/api/codes/{c['id']}", json={"memo": "nota"})
    assert len(project(client)["relations"]) == 1


def test_code_and_category_with_same_name_are_distinct(client):
    client.post("/api/domains/custom", json={"name": "Escuela", "color": "#123456"})
    code(client, "Escuela", domain="Escuela")
    r = client.post("/api/relations", json={"source": "Escuela", "target": "Escuela",
                                            "type": "jerarquía", "source_kind": "category"})
    assert r.status_code == 201
    same = client.post("/api/relations", json={"source": "Escuela", "target": "Escuela",
                                               "type": "jerarquía"})
    assert same.status_code == 422  # código consigo mismo
    # Renombrar el código no toca el extremo categoría homónimo
    client.post("/api/codes/merge", json={"from_name": "Escuela", "to_name": "Aula"})
    relation = project(client)["relations"][0]
    assert (relation["source_kind"], relation["source"]) == ("category", "Escuela")
    assert (relation["target_kind"], relation["target"]) == ("code", "Aula")


def test_deleting_custom_category_asks_and_prunes_relations(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#336699"})
    code(client, "mar", domain="Teórico")
    client.post("/api/relations", json={"source": "mar", "target": "Territorio",
                                        "type": "asociación", "target_kind": "category"})
    board = client.post("/api/boards", json={"name": "B"}).json()
    client.put(f"/api/boards/{board['id']}", json={"nodes": [
        {"kind": "category", "name": "Territorio", "x": 10, "y": 20}]})
    r = client.delete("/api/domains/custom/Territorio")
    assert r.status_code == 409 and r.headers["X-Relation-Count"] == "1"
    assert client.delete("/api/domains/custom/Territorio?confirm=true").status_code == 200
    data = project(client)
    assert data["relations"] == []
    assert data["boards"][0]["nodes"] == []


def test_boards_crud_layout_and_colors(client):
    for name in ("a", "b", "c"):
        code(client, name)
    general = project(client)["general_board"]
    assert general["id"] == 0
    board = client.post("/api/boards", json={"name": "Identidad"}).json()
    assert board["id"] == 1 and board["nodes"] == []
    # Crear una relación con el cuadro activo le agrega ambos extremos
    r = client.post("/api/relations", json={"source": "a", "target": "b", "type": "asociación",
                                            "board_id": board["id"]})
    relation_id = r.json()["id"]
    nodes = project(client)["boards"][0]["nodes"]
    assert [(n["kind"], n["name"]) for n in nodes] == [("code", "a"), ("code", "b")]
    # Posiciones, colores, tono; los nodos inexistentes o repetidos se ignoran
    r = client.put(f"/api/boards/{board['id']}", json={
        "name": "Identidad docente",
        "nodes": [{"kind": "code", "name": "a", "x": 100, "y": 50, "color": "#ff0000"},
                  {"kind": "code", "name": "a", "x": 1, "y": 1},
                  {"kind": "code", "name": "fantasma"},
                  {"kind": "category", "name": "Proceso", "x": 300, "y": 200}],
        "edge_colors": {str(relation_id): "#00aa00", "999": "#000000"},
        "show_tone": True})
    assert r.status_code == 200, r.text
    saved = r.json()
    assert saved["name"] == "Identidad docente" and saved["show_tone"] is True
    assert [(n["name"], n["color"]) for n in saved["nodes"]] == [("a", "#FF0000"), ("Proceso", None)]
    assert saved["edge_colors"] == {str(relation_id): "#00AA00"}
    assert client.put(f"/api/boards/{board['id']}", json={
        "nodes": [{"name": "a", "color": "rojo"}]}).status_code == 422
    # El cuadro general guarda posiciones pero no se renombra ni se elimina
    assert client.put("/api/boards/0", json={"nodes": [{"name": "a", "x": 5, "y": 5}]}).status_code == 200
    assert client.put("/api/boards/0", json={"name": "Otro"}).status_code == 422
    assert client.delete("/api/boards/0?confirm=true").status_code == 422
    # Eliminar un cuadro propio pide confirmación y conserva las relaciones
    assert client.delete(f"/api/boards/{board['id']}").status_code == 400
    assert client.delete(f"/api/boards/{board['id']}?confirm=true").status_code == 200
    data = project(client)
    assert data["boards"] == [] and len(data["relations"]) == 1
    assert client.put("/api/boards/7", json={"nodes": []}).status_code == 404
    assert client.post("/api/relations", json={"source": "a", "target": "c", "type": "jerarquía",
                                               "board_id": 7}).status_code == 404


def test_merge_and_delete_update_board_nodes(client):
    code(client, "a")
    code(client, "b")
    c = code(client, "c")
    board = client.post("/api/boards", json={"name": "B"}).json()
    client.put(f"/api/boards/{board['id']}", json={"nodes": [
        {"name": "a", "x": 1, "y": 1}, {"name": "b", "x": 2, "y": 2}, {"name": "c", "x": 3, "y": 3}]})
    client.put("/api/boards/0", json={"nodes": [{"name": "a", "x": 9, "y": 9}]})
    client.post("/api/codes/merge", json={"from_name": "a", "to_name": "b"})
    nodes = project(client)["boards"][0]["nodes"]
    # «b» ya estaba: conserva su posición; «a» desaparece
    assert [(n["name"], n["x"]) for n in nodes] == [("b", 2), ("c", 3)]
    client.post("/api/codes/merge", json={"from_name": "b", "to_name": "d"})
    assert project(client)["general_board"]["nodes"][0]["name"] == "d"  # renombre puro
    client.delete(f"/api/codes/{c['id']}")
    assert [n["name"] for n in project(client)["boards"][0]["nodes"]] == ["d"]


def test_qdpx_export_with_category_relation_and_codebook(client):
    import xmlschema

    upload(client, "La escuela rural cierra.")
    doc = project(client)["documents"][0]
    code(client, "escuela", domain="Descriptivo", doc_id=doc["id"], quote="escuela rural",
         start=3, end=16)
    client.post("/api/relations", json={"source": "escuela", "target": "Crítico",
                                        "type": "contradicción", "target_kind": "category"})
    client.put("/api/codebook", json={"kind": "code", "name": "escuela", "definition": "Lugar"})
    client.put("/api/codebook", json={"kind": "category", "name": "Descriptivo",
                                      "definition": "Hechos"})
    r = client.get("/api/export.qdpx")
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    xml = zf.read("project.qde").decode("utf-8")
    xmlschema.XMLSchema(str(XSD)).validate(xml)
    assert "Definición: Lugar" in xml and "Definición: Hechos" in xml
    assert "<Link " in xml or "<ns0:Link" in xml or "Link guid" in xml
    # Ida y vuelta: relación con categoría y libro de códigos se conservan
    imported, _ = qdpx.import_qdpx(r.content)
    relation = imported.relations[0]
    assert (relation.target_kind, relation.target) == ("category", "Crítico")
    assert imported.codebook["escuela"].definition == "Definición: Lugar"
    assert imported.category_notes["Descriptivo"].definition == "Definición: Hechos"
    # La descripción ya no se copia al memo de la primera cita
    assert imported.codes[0].memo == ""


# ----- Ajustes del léxico de sentimiento (FR-086) -----

TEXT = ("Siento alegría y amor por la escuela.\n"
        "Hay miedo y agobio en la sala.\n"
        "No hay agobio cuando llega la esperanza.")


@pytest.fixture
def corpus(client, nrc_lexicons):
    upload(client, TEXT)
    return project(client)["documents"][0]


def counts(data):
    return {e["emotion"]: e["count"] for e in data["emotions"]}


def test_overrides_remove_emotion_and_polarity(client, corpus):
    base = client.get("/api/sentiment").json()
    assert counts(base)["alegría"] == 3  # alegría, amor, esperanza
    assert any(w["word"] == "alegría" for w in base["emotion_words"]["alegría"])
    r = client.put("/api/sentiment/overrides", json={
        "lang": "es", "removed": {"alegría": ["amor"], "positivo": ["alegría"]}})
    assert r.status_code == 200
    data = client.get("/api/sentiment").json()
    assert counts(data)["alegría"] == 2
    assert all(w["word"] != "amor" for w in data["emotion_words"]["alegría"])
    assert all(w["word"] != "alegría" for w in data["polarity_words"]["positivo"])
    # «alegría» conserva sus emociones aunque pierda la polaridad
    assert any(w["word"] == "alegría" for w in data["emotion_words"]["alegría"])
    assert data["overrides"]["removed"]["alegría"] == ["amor"]
    assert data["documents"][0]["matched"] == base["documents"][0]["matched"] - 1


def test_overrides_add_word_respects_negation(client, corpus):
    r = client.put("/api/sentiment/overrides", json={
        "lang": "es", "added": {"miedo": ["Agobio"], "negativo": ["agobio"]}})
    assert r.status_code == 200 and r.json()["overrides"]["added"]["miedo"] == ["agobio"]
    data = client.get("/api/sentiment").json()
    fear = {w["word"]: w["count"] for w in data["emotion_words"]["miedo"]}
    # Dos menciones de «agobio»: la negada («No hay agobio») no aporta emoción
    assert fear == {"miedo": 1, "agobio": 1}
    negatives = {w["word"]: w["count"] for w in data["polarity_words"]["negativo"]}
    positives = {w["word"]: w["count"] for w in data["polarity_words"]["positivo"]}
    assert negatives.get("agobio") == 1 and positives.get("agobio") == 1  # negada: se invierte


def test_overrides_add_word_matches_inflected_forms_by_lemma(client, nrc_lexicons):
    # «pelear» no aparece literal: solo conjugado; se encuentra por su lema (spaCy)
    upload(client, "Los niños peleaban todos los días. No peleaban los domingos.")
    client.put("/api/sentiment/overrides", json={"lang": "es", "added": {"rabia": ["pelear"]}})
    data = client.get("/api/sentiment").json()
    anger = {w["word"]: w["count"] for w in data["emotion_words"].get("rabia", [])}
    assert anger == {"pelear": 1}  # la segunda mención está negada


def test_overrides_reach_code_tone(client, corpus):
    start = TEXT.index("miedo y agobio")
    code(client, "tensión", domain="Emocional", doc_id=corpus["id"], quote="miedo y agobio",
         start=start, end=start + len("miedo y agobio"))
    before = client.get("/api/sentiment").json()["code_tones"]["tensión"]["score"]
    client.put("/api/sentiment/overrides", json={"lang": "es", "removed": {"negativo": ["miedo"]}})
    after = client.get("/api/sentiment").json()["code_tones"]["tensión"]
    assert before == -1.0 and after == {"score": 0.0, "n": 1}


def test_overrides_validation_and_language_scope(client, corpus):
    bad = client.put("/api/sentiment/overrides", json={"lang": "es", "added": {"amistad": ["x"]}})
    assert bad.status_code == 422
    assert client.put("/api/sentiment/overrides", json={
        "lang": "es", "added": {"miedo": ["dos palabras"]}}).status_code == 422
    assert client.put("/api/sentiment/overrides", json={
        "lang": "xx", "added": {"miedo": ["agobio"]}}).status_code == 422
    # Sumar a una categoría anula el descarte en esa misma categoría
    r = client.put("/api/sentiment/overrides", json={
        "lang": "es", "removed": {"miedo": ["miedo"]}, "added": {"miedo": ["miedo"]}})
    assert r.json()["overrides"]["removed"] == {}
    client.put("/api/sentiment/overrides", json={"lang": "en", "added": {"miedo": ["dread"]}})
    stored = project(client)["sentiment_overrides"]
    assert set(stored) == {"es", "en"}
    client.put("/api/sentiment/overrides", json={"lang": "en"})  # vacío: se retira
    assert set(project(client)["sentiment_overrides"]) == {"es"}


def test_cache_records_negated_positions(nrc_lexicons):
    data = analysis.get("No siento alegría. Siento amor.", "es")
    text = "No siento alegría. Siento amor."
    assert text.index("alegría") in data["neg"] and text.index("amor") not in data["neg"]


def test_overrides_without_changes_return_same_records(nrc_lexicons):
    from backend.models import LexiconOverrides
    from backend.sentiment import apply_overrides

    data = analysis.get(TEXT, "es")
    assert apply_overrides(TEXT, data, LexiconOverrides()) is data["sent"]
    assert apply_overrides(TEXT, data, None) is data["sent"]


# ----- Simbología y organización del cuadro (FR-087) -----

def test_board_shapes_and_locks_round_trip(client):
    code(client, "a")
    code(client, "b")
    board = client.post("/api/boards", json={"name": "B"}).json()
    r = client.put(f"/api/boards/{board['id']}", json={
        "nodes": [{"name": "a", "x": 1, "y": 2, "shape": "box", "locked": True},
                  {"kind": "category", "name": "Proceso", "shape": "diamond"},
                  {"name": "b"}],
        "locked": True})
    assert r.status_code == 200, r.text
    saved = r.json()
    assert saved["locked"] is True
    assert [(n["name"], n["shape"], n["locked"]) for n in saved["nodes"]] == [
        ("a", "box", True), ("Proceso", "diamond", False), ("b", None, False)]
    assert client.put(f"/api/boards/{board['id']}", json={
        "nodes": [{"name": "a", "shape": "estrella"}]}).status_code == 422
    # Fusionar conserva forma y candado del nodo del destino
    client.post("/api/codes/merge", json={"from_name": "b", "to_name": "a"})
    nodes = project(client)["boards"][0]["nodes"]
    assert [(n["name"], n["shape"], n["locked"]) for n in nodes] == [
        ("a", "box", True), ("Proceso", "diamond", False)]
    # Un renombre puro lleva forma y candado con el nombre nuevo
    client.post("/api/codes/merge", json={"from_name": "a", "to_name": "c"})
    node = project(client)["boards"][0]["nodes"][0]
    assert (node["name"], node["shape"], node["locked"]) == ("c", "box", True)


def test_reverse_relation(client):
    code(client, "a")
    rel = client.post("/api/relations", json={"source": "a", "target": "Proceso",
                                              "type": "causalidad", "target_kind": "category"}).json()
    client.put("/api/boards/0", json={"nodes": [], "edge_colors": {str(rel["id"]): "#00aa00"}})
    r = client.post(f"/api/relations/{rel['id']}/reverse")
    assert r.status_code == 200
    out = r.json()
    assert (out["source_kind"], out["source"], out["target_kind"], out["target"]) == (
        "category", "Proceso", "code", "a")
    assert project(client)["general_board"]["edge_colors"] == {str(rel["id"]): "#00AA00"}
    # Si ya existe la relación inversa del mismo tipo, no se duplica
    client.post("/api/relations", json={"source": "a", "target": "Proceso",
                                        "type": "causalidad", "target_kind": "category"})
    assert client.post(f"/api/relations/{rel['id']}/reverse").status_code == 409
    assert client.post("/api/relations/999/reverse").status_code == 404


# ----- Traer relaciones existentes a un cuadro propio (FR-088) -----

def test_existing_relation_is_brought_to_a_custom_board(client):
    code(client, "a")
    code(client, "b")
    rel = {"source": "a", "target": "Proceso", "type": "causalidad", "target_kind": "category"}
    first = client.post("/api/relations", json=rel)
    assert first.status_code == 201 and first.json()["existed"] is False
    board = client.post("/api/boards", json={"name": "Nuevo"}).json()
    # Desde un cuadro propio: no es error, se trae (sus dos extremos) sin duplicarla
    again = client.post("/api/relations", json={**rel, "board_id": board["id"]})
    assert again.status_code == 200 and again.json()["existed"] is True
    assert again.json()["id"] == first.json()["id"]
    data = project(client)
    assert len(data["relations"]) == 1
    assert [(n["kind"], n["name"]) for n in data["boards"][0]["nodes"]] == [("code", "a"), ("category", "Proceso")]
    # Sin cuadro propio sigue siendo un duplicado
    assert client.post("/api/relations", json=rel).status_code == 409


def test_bring_relation_endpoint(client):
    code(client, "a")
    code(client, "b")
    rel = client.post("/api/relations", json={"source": "a", "target": "b", "type": "asociación"}).json()
    board = client.post("/api/boards", json={"name": "Nuevo"}).json()
    client.put(f"/api/boards/{board['id']}", json={"nodes": [{"name": "a", "x": 10, "y": 20, "shape": "box"}]})
    r = client.post(f"/api/boards/{board['id']}/relations/{rel['id']}")
    assert r.status_code == 200
    nodes = r.json()["nodes"]
    # «a» conserva su posición y forma; «b» se suma sin posición (hueco libre)
    assert [(n["name"], n["x"], n["shape"]) for n in nodes] == [("a", 10, "box"), ("b", None, None)]
    assert client.post(f"/api/boards/0/relations/{rel['id']}").status_code == 422
    assert client.post(f"/api/boards/{board['id']}/relations/99").status_code == 404
    assert client.post(f"/api/boards/99/relations/{rel['id']}").status_code == 404
