"""v2.0: biblioteca de literatura, anotaciones, literatura codificada y
referencias (FR-089..092). Ninguna prueba sale a internet: Crossref y OpenAlex
se simulan."""

import io
import zipfile

import fitz
import httpx
import pytest

from backend import library
from backend.models import LitMeta, Person, Project

DOI = "10.1177/1525822X980100020301"
CROSSREF = {"message": {
    "type": "journal-article", "title": ["Codebook Development for Team-Based Qualitative Analysis"],
    "author": [{"family": "MacQueen", "given": "Kathleen M."}, {"family": "McLellan", "given": "Eleanor"},
               {"family": "Kay", "given": "Kelly"}, {"family": "Milstein", "given": "Bobby"}],
    "issued": {"date-parts": [[1998, 5]]}, "container-title": ["CAM Journal"], "volume": "10",
    "issue": "2", "page": "31-36", "publisher": "SAGE Publications", "DOI": DOI,
}}


@pytest.fixture
def crossref(monkeypatch):
    calls = []

    def fake(url, params=None):
        calls.append(url)
        if "crossref" in url and DOI.lower() in url.lower():
            return CROSSREF
        raise httpx.ConnectError("sin red en las pruebas")

    monkeypatch.setattr(library, "_http_get", fake)
    return calls


@pytest.fixture
def offline(monkeypatch):
    def fake(url, params=None):
        raise httpx.ConnectError("sin red")
    monkeypatch.setattr(library, "_http_get", fake)


def make_pdf(text: str, pages: int = 2) -> bytes:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text if i == 0 else f"Página {i + 1}", fontsize=11)
    return doc.tobytes()


def upload(client, name, data, mime="application/pdf"):
    return client.post("/api/library/items", files={"file": (name, data, mime)})


def project(client):
    return client.get("/api/project").json()


# ----- APA 7 -----

def m(**kw):
    return LitMeta(**kw)


def test_apa_article_two_authors_and_doi():
    meta = m(type="article", title="Codebook development", year="1998", container="CAM Journal",
             volume="10", issue="2", pages="31–36", doi="https://doi.org/" + DOI,
             authors=[Person(family="MacQueen", given="Kathleen M."), Person(family="Kay", given="Kelly")])
    assert library.apa(meta, html=False) == (
        "MacQueen, K. M., & Kay, K. (1998). Codebook development. CAM Journal, 10(2), 31–36. "
        f"https://doi.org/{DOI}")
    assert "<em>CAM Journal</em>, <em>10</em>(2)" in library.apa(meta)


def test_apa_initials_hyphens_and_compound_names():
    assert library._initials("Jean-Paul") == "J.-P."
    assert library._initials("María José") == "M. J."
    assert library._initials("K. M.") == "K. M."
    meta = m(type="book", title="Lecturas", year="2020", publisher="Editorial",
             authors=[Person(family="Muñoz-Salinas", given="Yerko"), Person(family="de la Fuente", given="Ana María")])
    assert library.apa(meta, html=False) == (
        "Muñoz-Salinas, Y., & de la Fuente, A. M. (2020). Lecturas. Editorial.")


def test_apa_more_than_twenty_authors():
    authors = [Person(family=f"Autor{i}", given="A") for i in range(1, 23)]
    text = library.apa(m(type="article", title="T", year="2021", authors=authors), html=False)
    assert "Autor19, A., . . . Autor22, A. (2021)" in text and "Autor20" not in text
    twenty = library.apa(m(type="article", title="T", year="2021", authors=authors[:20]), html=False)
    assert "Autor19, A., & Autor20, A. (2021)" in twenty


def test_apa_chapter_book_no_date_no_author_and_question_titles():
    chapter = m(type="chapter", title="La escucha", year="2019", container="Métodos cualitativos",
                pages="10–20", publisher="Graó",
                authors=[Person(family="Pérez", given="Juan")],
                editors=[Person(family="Rojas", given="Ana"), Person(family="Soto", given="Luis")])
    assert library.apa(chapter, "es", html=False) == (
        "Pérez, J. (2019). La escucha. En A. Rojas & L. Soto (Eds.), Métodos cualitativos "
        "(pp. 10–20). Graó.")
    assert "In A. Rojas & L. Soto (Eds.)" in library.apa(chapter, "en", html=False)
    no_date = m(type="book", title="¿Qué es enseñar?", authors=[Person(family="Freire", given="Paulo")])
    assert library.apa(no_date, "es", html=False) == "Freire, P. (s. f.). ¿Qué es enseñar?"
    assert "(n.d.)" in library.apa(no_date, "en", html=False)
    no_author = m(type="report", title="Informe anual", year="2022", publisher="Mineduc")
    assert library.apa(no_author, html=False) == "Informe anual. (2022). Mineduc."
    group = m(type="report", title="Estándares", year="2021", authors=[Person(family="UNESCO")])
    assert library.apa(group, html=False).startswith("UNESCO. (2021). Estándares.")


def test_doi_detection_and_normalization():
    assert library.find_doi("véase https://doi.org/10.1177/1525822X980100020301.") == DOI
    assert library.find_doi("DOI: 10.1590/S1517-97022020460211). Más") == "10.1590/S1517-97022020460211"
    assert library.find_doi("sin identificador") == ""
    assert library.normalize_doi("https://dx.doi.org/10.1/ABC") == "10.1/ABC"
    assert library.normalize_doi("doi: 10.1/x") == "10.1/x"


def test_bibtex_and_ris():
    meta = m(type="article", title="Codebook development", year="1998", container="CAM Journal",
             volume="10", issue="2", pages="31–36", doi=DOI,
             authors=[Person(family="MacQueen", given="Kathleen M.")])
    bib = library.bibtex([meta, meta])
    assert "@article{macqueen1998codebook," in bib and "@article{macqueen1998codebook2," in bib
    assert "pages = {31--36}" in bib and f"doi = {{{DOI}}}" in bib
    ris = library.ris([meta])
    assert "TY  - JOUR" in ris and "AU  - MacQueen, Kathleen M." in ris
    assert "SP  - 31" in ris and "EP  - 36" in ris and ris.rstrip().endswith("ER  -")


# ----- Biblioteca -----

def test_upload_pdf_detects_doi_and_fills_metadata(client, crossref):
    data = make_pdf(f"Texto https://doi.org/{DOI} fin")
    r = upload(client, "macqueen.pdf", data)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["kind"] == "pdf" and item["pages"] == 2 and item["doi_found"] is True
    assert item["meta"]["title"].startswith("Codebook Development") and item["meta"]["year"] == "1998"
    assert item["meta"]["pages"] == "31–36"
    assert item["apa"].startswith("MacQueen, K. M., McLellan, E., Kay, K., &amp; Milstein, B. (1998).")
    # El mismo archivo no se duplica
    again = upload(client, "otra copia.pdf", data)  # mismo archivo, otro nombre
    assert again.status_code == 200 and again.json()["duplicate"] is True
    assert len(client.get("/api/library").json()["items"]) == 1
    # El archivo se sirve tal cual
    pdf = client.get(f"/api/library/items/{item['id']}/file")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_upload_without_internet_keeps_filename_as_title(client, offline):
    r = upload(client, "Freire 1970.pdf", make_pdf("Pedagogía del oprimido 10.1000/xyz123"))
    item = r.json()
    assert r.status_code == 201 and item["meta"]["title"] == "Freire 1970"
    assert item["meta"]["doi"] == "10.1000/xyz123"  # el DOI encontrado se conserva


def test_upload_text_documents_and_unsupported(client, offline):
    r = upload(client, "notas.txt", "La escuela rural enseña.".encode(), "text/plain")
    assert r.status_code == 201 and r.json()["kind"] == "text"
    text = client.get(f"/api/library/items/{r.json()['id']}/text").json()["text"]
    assert text == "La escuela rural enseña."
    assert upload(client, "foto.png", b"\x89PNG", "image/png").status_code == 415


def test_reference_from_doi_and_lookup(client, crossref):
    r = client.post("/api/library/refs", json={"doi": f"https://doi.org/{DOI}"})
    assert r.status_code == 201 and r.json()["kind"] == "ref" and r.json()["has_file"] is False
    assert client.post("/api/library/refs", json={"doi": DOI}).json()["duplicate"] is True
    assert client.post("/api/library/refs", json={"doi": "10.9/nada"}).status_code == 502
    # Ficha editada a mano y vuelta a completar desde el DOI
    item_id = r.json()["id"]
    edited = client.patch(f"/api/library/items/{item_id}", json={"meta": {"type": "article", "title": "Otro"}})
    assert edited.json()["meta"]["title"] == "Otro"
    again = client.post(f"/api/library/items/{item_id}/lookup", json={"doi": DOI})
    assert again.json()["meta"]["title"].startswith("Codebook")


def test_annotations_crud_and_validation(client, offline):
    item = upload(client, "a.pdf", make_pdf("texto")).json()
    base = {"item_id": item["id"], "quote": "texto", "page": 1, "rects": [[0.1, 0.1, 0.2, 0.02]]}
    r = client.post("/api/library/annotations", json={**base, "kind": "underline", "color": "#0066ff"})
    assert r.status_code == 201 and r.json()["color"] == "#0066FF"
    aid = r.json()["id"]
    assert client.patch(f"/api/library/annotations/{aid}", json={"comment": "clave"}).json()["comment"] == "clave"
    assert client.post("/api/library/annotations", json={**base, "rects": []}).status_code == 422
    assert client.post("/api/library/annotations", json={**base, "rects": [[2, 0, 0, 0]]}).status_code == 422
    assert client.post("/api/library/annotations", json={**base, "kind": "dibujo"}).status_code == 422
    text_ann = client.post("/api/library/annotations", json={
        "item_id": item["id"], "quote": "x", "start": 0, "end": 3, "kind": "highlight"})
    assert text_ann.status_code == 201
    listed = client.get(f"/api/library/items/{item['id']}/annotations").json()
    assert len(listed["annotations"]) == 2 and listed["codings"] == []
    assert client.delete(f"/api/library/annotations/{aid}").status_code == 204
    assert client.delete(f"/api/library/annotations/{aid}").status_code == 404


def test_lit_codings_follow_codes_and_stay_separate(client, offline):
    item = upload(client, "a.pdf", make_pdf("La confianza se construye despacio")).json()
    client.post("/api/codes", json={"domain": "Teórico", "name": "confianza"})
    anchor = {"item_id": item["id"], "quote": "La confianza", "page": 1, "rects": [[0.1, 0.1, 0.3, 0.02]]}
    # El código debe existir en el proyecto y la categoría ser válida
    assert client.post("/api/lit-codings", json={**anchor, "name": "nuevo", "domain": "Teórico"}).status_code == 422
    assert client.post("/api/lit-codings", json={**anchor, "name": "confianza", "domain": "Nada"}).status_code == 422
    r = client.post("/api/lit-codings", json={**anchor, "name": "confianza", "domain": "Teórico"})
    assert r.status_code == 201 and r.json()["id"] == 1
    # Separada del corpus: no entra en el CSV de códigos ni en el banco
    csv_rows = client.get("/api/export.csv").content.decode("utf-8-sig").strip().splitlines()
    assert len(csv_rows) == 2 and len(project(client)["codes"]) == 1
    assert client.get("/api/library").json()["items"][0]["codings"] == 1
    # Fusionar lleva los pasajes de literatura al nombre nuevo
    client.post("/api/codes", json={"domain": "Proceso", "name": "credibilidad"})
    client.post("/api/codes/merge", json={"from_name": "confianza", "to_name": "credibilidad"})
    lit = project(client)["lit_codings"][0]
    assert (lit["name"], lit["domain"]) == ("credibilidad", "Proceso")
    # Memo y eliminación
    assert client.patch("/api/lit-codings/1", json={"memo": "teoría"}).json()["memo"] == "teoría"
    assert client.delete("/api/lit-codings/1").status_code == 204
    assert project(client)["lit_codings"] == []


def test_reset_clears_lit_codings_but_not_library(client, offline):
    item = upload(client, "a.pdf", make_pdf("x")).json()
    client.post("/api/codes", json={"domain": "Teórico", "name": "c"})
    client.post("/api/lit-codings", json={"item_id": item["id"], "quote": "x", "page": 1,
                                          "rects": [[0, 0, 0.1, 0.1]], "name": "c", "domain": "Teórico"})
    client.post("/api/project/reset", json={"confirm": True})
    assert project(client)["lit_codings"] == []
    assert len(client.get("/api/library").json()["items"]) == 1


def test_delete_item_asks_and_cleans_every_project(client, offline):
    item = upload(client, "a.pdf", make_pdf("x")).json()
    anchor = {"item_id": item["id"], "quote": "x", "page": 1, "rects": [[0, 0, 0.1, 0.1]]}
    for name in ("Proyecto A", "Proyecto B"):
        client.post("/api/projects", json={"name": name})
        client.post("/api/codes", json={"domain": "Teórico", "name": "c"})
        client.post("/api/lit-codings", json={**anchor, "name": "c", "domain": "Teórico"})
    client.post("/api/library/annotations", json={**anchor, "kind": "highlight"})
    r = client.delete(f"/api/library/items/{item['id']}")
    assert r.status_code == 409 and r.headers["X-Coding-Count"] == "2"
    assert client.delete(f"/api/library/items/{item['id']}?confirm=true").json()["codings"] == 2
    from backend import storage
    assert all(not p.lit_codings for p in storage.list_projects())
    assert client.get("/api/library").json()["items"] == []
    trash = list((library.library_dir() / "papelera").iterdir())
    assert any(p.suffix == ".pdf" for p in trash)  # el archivo va a la papelera, no se borra


def test_bibliography_scopes_and_exports(client, crossref):
    coded = upload(client, "a.pdf", make_pdf(f"https://doi.org/{DOI}")).json()
    upload(client, "b.txt", "otro texto".encode(), "text/plain")
    client.post("/api/codes", json={"domain": "Teórico", "name": "c"})
    client.post("/api/lit-codings", json={"item_id": coded["id"], "quote": "x", "page": 1,
                                          "rects": [[0, 0, 0.1, 0.1]], "name": "c", "domain": "Teórico"})
    every = client.get("/api/library/bibliography").json()["entries"]
    mine = client.get("/api/library/bibliography?scope=project").json()["entries"]
    assert len(every) == 2 and len(mine) == 1 and mine[0]["text"].startswith("MacQueen")
    english = client.get("/api/library/bibliography?scope=project&ui=en").json()["entries"][0]
    assert english["text"] == mine[0]["text"]  # con año y DOI, no cambia de idioma
    bib = client.get("/api/library/export.bib")
    assert bib.status_code == 200 and "@article{macqueen1998codebook" in bib.text
    assert "TY  - JOUR" in client.get("/api/library/export.ris?scope=project").text
    assert client.get("/api/library/export.xyz").status_code == 404
    # El respaldo del proyecto lleva las fichas de la literatura codificada
    with zipfile.ZipFile(io.BytesIO(client.get("/api/export.zip").content)) as zf:
        assert "literatura.json" in zf.namelist()
        assert "MacQueen" in zf.read("literatura.json").decode("utf-8")


def test_old_project_loads_without_lit_fields():
    loaded = Project.model_validate_json('{"id": "a", "name": "viejo"}')
    assert loaded.lit_codings == [] and loaded.next_lit_id == 1


def test_deleting_last_instance_with_literature_asks_and_cleans(client, offline):
    item = upload(client, "a.pdf", make_pdf("x")).json()
    manual = client.post("/api/codes", json={"domain": "Teórico", "name": "teoría"}).json()
    client.post("/api/lit-codings", json={"item_id": item["id"], "quote": "x", "page": 1,
                                          "rects": [[0, 0, 0.1, 0.1]], "name": "teoría", "domain": "Teórico"})
    r = client.delete(f"/api/codes/{manual['id']}")
    assert r.status_code == 409 and r.headers["X-Lit-Count"] == "1"
    assert len(project(client)["lit_codings"]) == 1  # nada cambió
    assert client.delete(f"/api/codes/{manual['id']}?confirm=true").status_code == 204
    data = project(client)
    assert data["codes"] == [] and data["lit_codings"] == []  # nunca quedan huérfanos
    # Si quedan otras instancias del nombre, se borra sin preguntar
    a = client.post("/api/codes", json={"domain": "Teórico", "name": "otra"}).json()
    client.post("/api/codes", json={"domain": "Teórico", "name": "otra"})
    client.post("/api/lit-codings", json={"item_id": item["id"], "quote": "x", "page": 1,
                                          "rects": [[0, 0, 0.1, 0.1]], "name": "otra", "domain": "Teórico"})
    assert client.delete(f"/api/codes/{a['id']}").status_code == 204
    assert len(project(client)["lit_codings"]) == 1


def test_reference_order_ignores_accents():
    names = ["Zúñiga", "Álvarez", "Ortega", "Ñúñez"]
    ordered = sorted((LitMeta(authors=[Person(family=n)]) for n in names), key=library.sort_key)
    assert [m.authors[0].family for m in ordered] == ["Álvarez", "Ñúñez", "Ortega", "Zúñiga"]


def test_scanned_pdf_imports_without_ocr(client, offline, monkeypatch):
    from backend import ocr

    def boom(*args, **kwargs):
        raise AssertionError("la biblioteca no debe hacer OCR")
    monkeypatch.setattr(ocr, "recognize_png", boom)
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), False)
    page.insert_image(fitz.Rect(72, 72, 300, 300), pixmap=pix)
    r = upload(client, "escaneado.pdf", doc.tobytes())
    assert r.status_code == 201 and r.json()["pages"] == 1 and r.json()["meta"]["title"] == "escaneado"


def test_literature_stays_out_of_corpus_analyses(client, nrc_lexicons, offline):
    """FR-091: la literatura codificada no entra en REFI-QDA, sentimiento ni acuerdo."""
    from backend import agreement, qdpx, storage

    client.post("/api/documents", files={"file": ("e.txt", "Siento alegría y miedo.".encode(), "text/plain")})
    doc = project(client)["documents"][0]
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional", "name": "afecto",
                                    "quote": "alegría", "start": 7, "end": 14})
    item = upload(client, "lit.txt", "La alegría y la tristeza en la escuela.".encode(), "text/plain").json()
    client.post("/api/lit-codings", json={"item_id": item["id"], "quote": "La alegría y la tristeza",
                                          "start": 0, "end": 24, "name": "afecto", "domain": "Emocional"})
    xml = zipfile.ZipFile(io.BytesIO(client.get("/api/export.qdpx").content)).read("project.qde").decode()
    assert "La alegría y la tristeza" not in xml
    tones = client.get("/api/sentiment").json()["code_tones"]
    assert tones["afecto"]["n"] == 1  # solo la cita del corpus
    me = storage.get_active_project()
    other = me.model_copy(deep=True)
    other.id = "otro"
    other.lit_codings = []
    result = agreement.compare(me, other)
    assert result["project_a"]["name"] == me.name  # compara solo códigos del corpus
    assert all(row["count_a"] == row["count_b"] for row in result["codes"])
