"""v1.12: sentimiento y foco gramatical en inglés y portugués, OCR de PDF
escaneados, acuerdo entre codificadores e intercambio REFI-QDA (FR-077..081)."""

import io
import zipfile
from pathlib import Path

import fitz
import pytest

from backend import agreement, analysis, lexicons, ocr, qdpx, storage
from backend.extraction import extract_document
from backend.models import Code, Document, Project, Relation
from backend.nlp import detect_language

XSD = Path(__file__).parent / "data" / "REFI-QDA-Project-1.0.xsd"


# ----- Léxicos: se genera un .zip mínimo con el formato del NRC (no se redistribuye el real) -----

HEADER = ["English Word", "anger", "anticipation", "disgust", "fear", "joy", "negative",
          "positive", "sadness", "surprise", "trust", "Portuguese Word"]


def fake_nrc_zip(extra_rows: int = 1200) -> bytes:
    rows = [HEADER,
            ["joy", "0", "1", "0", "0", "1", "0", "1", "0", "0", "1", "alegria"],
            ["fear", "0", "0", "0", "1", "0", "1", "0", "0", "0", "0", "medo"],
            ["sadness", "0", "0", "0", "0", "0", "1", "0", "1", "0", "0", "tristeza"],
            ["love", "0", "0", "0", "0", "1", "0", "1", "0", "0", "0", "amor"],
            ["hope", "0", "1", "0", "0", "1", "0", "1", "0", "1", "1", "esperança"],
            ["cry", "0", "0", "0", "0", "0", "1", "0", "1", "0", "0", "chorar"]]
    rows += [[f"word{i}", "0", "0", "0", "0", "0", "0", "1", "0", "0", "0", f"palavra{i}"]
             for i in range(extra_rows)]
    text = "\n".join("\t".join(r) for r in rows)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("NRC-Emotion-Lexicon/OneFilePerLanguage/Portuguese-NRC-EmoLex.txt", text)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def fresh_lexicons():
    lexicons._cache.clear()
    yield
    lexicons._cache.clear()


@pytest.fixture
def lexicons_installed(client):
    r = client.post("/api/lexicons/import",
                    files={"file": ("NRC-Emotion-Lexicon.zip", fake_nrc_zip(), "application/zip")})
    assert r.status_code == 200
    return r.json()


def upload(client, text, name="e.txt"):
    return client.post("/api/documents", files={"file": (name, text.encode("utf-8"), "text/plain")})


def test_spanish_lexicon_is_bundled_and_others_are_not(client):
    status = client.get("/api/lexicons").json()["lexicons"]
    assert status["es"]["available"] and status["es"]["bundled"]
    assert not status["en"]["available"] and not status["pt"]["available"]


def test_sentiment_reports_missing_lexicon(client):
    upload(client, "I felt joy and hope.")
    client.put("/api/project/corpus-lang", json={"lang": "en"})
    data = client.get("/api/sentiment").json()
    assert data["lexicon_missing"] is True and data["lang"] == "en"


def test_import_official_zip_rejects_other_files(client):
    r = client.post("/api/lexicons/import", files={"file": ("x.zip", b"PKnope", "application/zip")},
                    headers={"X-Cua-Lang": "en"})
    assert r.status_code == 422 and "NRC" in r.json()["detail"]


def test_conversion_keeps_canonical_emotion_keys():
    raw = zipfile.ZipFile(io.BytesIO(fake_nrc_zip())).read(
        "NRC-Emotion-Lexicon/OneFilePerLanguage/Portuguese-NRC-EmoLex.txt").decode()
    pt = lexicons.convert([line.split("\t") for line in raw.splitlines()], "Portuguese Word")
    assert pt["medo"] == [-1, ["miedo"]]
    assert pt["esperança"] == [1, ["alegría", "anticipación", "confianza", "sorpresa"]]


def test_english_sentiment_arc_emotions_and_negation(client, lexicons_installed):
    assert lexicons_installed["installed"]["en"] > 1000
    upload(client, "I felt joy and love.\nThen fear and sadness.")
    client.put("/api/project/corpus-lang", json={"lang": "en"})
    data = client.get("/api/sentiment").json()
    assert data["lang"] == "en"
    arc = data["documents"][0]["arc"]
    assert arc[0]["score"] > 0 > arc[1]["score"]
    assert any(e["emotion"] == "miedo" for e in data["emotions"])  # clave canónica
    from backend.sentiment import analyze_texts

    assert analyze_texts(["I don't feel joy."], "en")[0]["score"] < 0  # "n't" niega


def test_portuguese_sentiment_by_lemma_and_negation(client, lexicons_installed):
    from backend.sentiment import analyze_texts

    result = analyze_texts(["A criança chorava de medo, sem esperança."], "pt")[0]
    assert result["negatives"].get("chorar") == 1  # "chorava" encontrada por su lema
    assert result["negatives"].get("medo") == 1
    assert "esperança" in result["negatives"]  # "sem esperança": polaridad invertida


def test_installing_a_lexicon_invalidates_cached_analysis(client):
    before = analysis.get("I felt joy today.", "en")
    assert before["sent"] == [] and before["lex"] is None
    client.post("/api/lexicons/import", files={"file": ("n.zip", fake_nrc_zip(), "application/zip")})
    after = analysis.get("I felt joy today.", "en")
    assert after["lex"] == lexicons.DOWNLOADED_ID and after["sent"]


# ----- Idioma del corpus -----

def test_detect_language():
    assert detect_language("La escuela rural quedaba lejos y los niños llegaban con frío.") == "es"
    assert detect_language("The rural school was far away and the children arrived cold.") == "en"
    assert detect_language("A escola rural ficava longe e as crianças não chegavam.") == "pt"


def test_first_document_sets_corpus_language(client):
    upload(client, "A escola não era pobre, você sabe, era outra forma de conhecer.")
    assert client.get("/api/project").json()["corpus_lang"] == "pt"
    assert client.put("/api/project/corpus-lang", json={"lang": "fr"}).status_code == 422


def test_demo_sets_corpus_language(client):
    project = client.post("/api/projects/example", headers={"X-Cua-Lang": "en"}).json()
    assert project["corpus_lang"] == "en"


# ----- OCR -----

def scanned_pdf(text: str) -> bytes:
    src = fitz.open()
    page = src.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 520, 300), text, fontsize=13, fontname="Times-Roman")
    pix = page.get_pixmap(dpi=200)
    out = fitz.open()
    new = out.new_page(width=page.rect.width, height=page.rect.height)
    new.insert_image(new.rect, stream=pix.tobytes("png"))
    return out.tobytes()


@pytest.mark.skipif(not ocr.available(), reason="sin motor de OCR en este sistema")
def test_scanned_pdf_is_read_by_ocr(client):
    pdf = scanned_pdf("La escuela rural quedaba a tres horas del pueblo.")
    r = client.post("/api/documents", files={"file": ("escaneo.pdf", pdf, "application/pdf")})
    assert r.status_code == 201
    doc = r.json()
    assert doc["ocr_pages"] == [1]
    assert "escuela rural" in doc["text"]


def test_pdf_with_text_layer_does_not_use_ocr():
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Texto con capa de texto original, suficientemente largo.")
    text, pages = extract_document("normal.pdf", doc.tobytes(), ["es"])
    assert pages == [] and "capa de texto" in text


def test_scanned_pdf_without_ocr_explains_why(monkeypatch, client):
    monkeypatch.setattr(ocr, "available", lambda: False)
    r = client.post("/api/documents", files={"file": ("e.pdf", scanned_pdf("Hola"), "application/pdf")},
                    headers={"X-Cua-Lang": "en"})
    assert r.status_code == 422 and "OCR is not available" in r.json()["detail"]


# ----- Acuerdo entre codificadores -----

def test_statistics_match_hand_calculation():
    # 100 unidades; A codifica [0,40), B [20,60): ambos 20, solo A 20, solo B 20, ninguno 40
    s = agreement.statistics(20, 20, 20, 100)
    assert s["agreement"] == 0.6
    assert s["kappa"] == pytest.approx(0.167, abs=0.001)  # (0,6 − 0,52) / 0,48
    assert s["alpha"] == pytest.approx(0.171, abs=0.001)  # 1 − 0,4 / 0,4824
    perfect = agreement.statistics(30, 0, 0, 100)
    assert perfect["kappa"] == 1.0 and perfect["alpha"] == 1.0


def two_coders() -> tuple[Project, Project]:
    text = "0123456789" * 10  # 100 caracteres
    a, b = Project(name="Coder A"), Project(name="Coder B")
    da, db = Document(filename="e1.txt", text=text), Document(filename="renombrado.txt", text=text)
    a.documents.append(da)
    b.documents.append(db)
    a.codes.append(Code(id=1, doc_id=da.id, domain="Proceso", name="espera", quote="x", start=0, end=40))
    b.codes.append(Code(id=1, doc_id=db.id, domain="Proceso", name="espera", quote="x", start=20, end=60))
    b.codes.append(Code(id=2, doc_id=db.id, domain="Teórico", name="solo B", quote="x", start=70, end=80))
    return a, b


def test_compare_matches_documents_by_text_and_lists_disagreements():
    a, b = two_coders()
    result = agreement.compare(a, b)
    assert len(result["shared_documents"]) == 1  # el nombre del archivo no importa
    espera = next(c for c in result["codes"] if c["name"] == "espera")
    assert espera["kappa"] == pytest.approx(0.167, abs=0.001)
    assert sorted((d["who"], d["start"], d["end"]) for d in espera["disagreements"]) == \
        [("a", 0, 20), ("b", 40, 60)]
    solo_b = next(c for c in result["codes"] if c["name"] == "solo B")
    assert solo_b["count_a"] == 0 and solo_b["kappa"] == 0.0


def test_overlapping_quotes_of_same_code_count_once():
    a, b = two_coders()
    a.codes.append(Code(id=9, doc_id=a.documents[0].id, domain="Proceso", name="espera",
                        quote="x", start=10, end=30))  # dentro de [0,40)
    espera = next(c for c in agreement.compare(a, b)["codes"] if c["name"] == "espera")
    assert espera["only_a"] == 20 and espera["both"] == 20


def test_agreement_endpoint_and_csv(client):
    a, b = two_coders()
    storage.save_project(a)
    storage.save_project(b)
    storage.set_active_project(a.id)
    r = client.get(f"/api/agreement?other={b.id}")
    assert r.status_code == 200 and r.json()["project_b"]["name"] == "Coder B"
    csv_text = client.get(f"/api/agreement.csv?other={b.id}&ui=en").content.decode("utf-8-sig")
    assert "cohen_kappa" in csv_text and "espera" in csv_text
    assert client.get(f"/api/agreement?other={a.id}").status_code == 404  # consigo mismo no


# ----- REFI-QDA (.qdpx) -----

def rich_project() -> Project:
    text = "Entrevista 😀: la escuela rural era el corazón de la comunidad.\nFin."
    p = Project(name="Proyecto ñandú")
    d = Document(filename="entrevista.txt", text=text)
    p.documents.append(d)
    p.custom_domains["Mi categoría"] = "#123ABC"

    def u16(s):
        return len(s.encode("utf-16-le")) // 2

    start = u16(text[:text.index("la escuela")])
    heart = u16(text[:text.index("corazón")])
    p.codes += [
        Code(id=1, doc_id=d.id, domain="Relacional", name="comunidad", quote="la escuela rural",
             start=start, end=start + len("la escuela rural"), memo="memo de la cita"),
        Code(id=2, doc_id=d.id, domain="Mi categoría", name="corazón", quote="corazón",
             start=heart, end=heart + 7),
        Code(id=3, doc_id=None, domain="Método", name="nota", memo="código manual"),
    ]
    p.next_code_id = 4
    p.relations.append(Relation(id=1, source="comunidad", target="corazón", type="causalidad"))
    return p


def test_qdpx_export_is_valid_against_official_schema():
    import xmlschema

    zf = zipfile.ZipFile(io.BytesIO(qdpx.export_qdpx(rich_project())))
    assert "project.qde" in zf.namelist()
    assert any(n.startswith("sources/") and n.endswith(".txt") for n in zf.namelist())
    xmlschema.XMLSchema(str(XSD)).validate(zf.read("project.qde").decode("utf-8"))


def test_qdpx_positions_are_unicode_codepoints():
    from xml.etree import ElementTree as ET

    zf = zipfile.ZipFile(io.BytesIO(qdpx.export_qdpx(rich_project())))
    root = ET.fromstring(zf.read("project.qde"))
    source = next(root.iter(qdpx.Q + "TextSource"))
    text = zf.read("sources/" + source.get("plainTextPath")[len("internal://"):]).decode("utf-8")
    selections = {s.get("name"): (int(s.get("startPosition")), int(s.get("endPosition")))
                  for s in root.iter(qdpx.Q + "PlainTextSelection")}
    start, end = selections["la escuela rural"]
    assert text[start:end] == "la escuela rural"  # tras el emoji: puntos de código, no UTF-16


def test_qdpx_roundtrip_preserves_codes_memos_and_relations():
    original = rich_project()
    imported, report = qdpx.import_qdpx(qdpx.export_qdpx(original))
    assert report["sources"] == 1 and report["selections"] == 2
    doc = imported.documents[0]
    assert doc.text == original.documents[0].text
    by_name = {c.name: c for c in imported.codes}
    comunidad = by_name["comunidad"]
    js = doc.text.encode("utf-16-le")
    assert js[comunidad.start * 2:comunidad.end * 2].decode("utf-16-le") == "la escuela rural"
    assert comunidad.domain == "Relacional" and comunidad.memo == "memo de la cita"
    assert by_name["corazón"].domain == "Mi categoría"
    assert imported.custom_domains["Mi categoría"] == "#123ABC"
    assert by_name["nota"].doc_id is None and by_name["nota"].memo == "código manual"
    assert [(r.source, r.target, r.type) for r in imported.relations] == \
        [("comunidad", "corazón", "causalidad")]


QDE_FROM_OTHER_SOFTWARE = """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="De NVivo">
 <CodeBook><Codes>
  <Code guid="00000000-0000-0000-0000-000000000001" name="Temas" isCodable="false" color="#F00">
   <Code guid="00000000-0000-0000-0000-000000000002" name="Escuela" isCodable="true">
    <Code guid="00000000-0000-0000-0000-000000000003" name="Ruralidad" isCodable="true"/>
   </Code>
  </Code>
  <Code guid="00000000-0000-0000-0000-000000000004" name="Suelto" isCodable="true"><Description>def</Description></Code>
 </Codes></CodeBook>
 <Sources>
  <TextSource guid="00000000-0000-0000-0000-000000000010" name="t1">
   <PlainTextContent>La escuela rural.</PlainTextContent>
   <PlainTextSelection guid="00000000-0000-0000-0000-000000000011" startPosition="3" endPosition="16">
    <Coding guid="00000000-0000-0000-0000-000000000012"><CodeRef targetGUID="00000000-0000-0000-0000-000000000003"/></Coding>
   </PlainTextSelection>
  </TextSource>
  <PictureSource guid="00000000-0000-0000-0000-000000000020" name="foto" path="internal://x.png"/>
 </Sources>
</Project>"""


def test_qdpx_import_from_other_software_shapes():
    # Tres niveles, código sin padre, PlainTextContent en línea y una fuente de imagen
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("project.qde", QDE_FROM_OTHER_SOFTWARE)
    project, report = qdpx.import_qdpx(buffer.getvalue())
    assert report["sources"] == 1 and report["skipped_sources"] == 1
    code = next(c for c in project.codes if c.doc_id)
    assert (code.name, code.domain, code.quote) == ("Ruralidad", "Temas", "escuela rural")
    assert project.custom_domains["Temas"] == "#FF0000"
    assert ("Escuela", "Ruralidad", "jerarquía") in \
        [(r.source, r.target, r.type) for r in project.relations]
    suelto = next(c for c in project.codes if c.name == "Suelto")
    assert suelto.doc_id is None and suelto.domain == qdpx.IMPORT_CATEGORY and suelto.memo == "def"


def test_qdpx_import_endpoint(client):
    r = client.post("/api/projects/import",
                    files={"file": ("p.qdpx", qdpx.export_qdpx(rich_project()), "application/zip")})
    assert r.status_code == 201
    body = r.json()
    assert body["import_report"]["selections"] == 2
    assert body["corpus_lang"] == "es"
    assert client.get("/api/export.qdpx").status_code == 200


def test_negators_never_count_as_charged_words():
    from backend.sentiment import analyze_texts

    # «nada» es negativa en la traducción del NRC, pero aquí solo niega
    result = analyze_texts(["No siento nada de alegría."], "es")[0]
    assert "nada" not in result["negatives"]


# ----- Aplicación de escritorio y seguridad local (FR-081) -----

def test_app_info_reports_mode_and_ocr(client):
    info = client.get("/api/app-info").json()
    assert info["mode"] == "server" and info["version"]
    assert info["ocr"] == ocr.engine_name()


def test_other_websites_cannot_use_the_api(client):
    # Un sitio web abierto en el navegador no puede escribir en los proyectos (CSRF)
    r = client.post("/api/project/save", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    # Ni usar un dominio propio que apunte a 127.0.0.1 (DNS rebinding)
    assert client.get("/api/project", headers={"Host": "evil.example:8734"}).status_code == 403
    assert client.post("/api/project/save", headers={"Origin": "http://127.0.0.1:8734"}).status_code == 200


def test_quit_and_save_dialog_only_where_they_make_sense(client):
    assert client.post("/api/app/quit", json={"confirm": True}).status_code == 409  # sin run.py
    r = client.post("/api/app/save-file?filename=x.csv", files={"file": ("x.csv", b"a", "text/csv")})
    assert r.status_code == 409  # sin ventana propia


def test_qdpx_empty_categories_do_not_become_codes():
    project = rich_project()
    project.custom_domains["Vacía"] = "#ABCDEF"  # categoría propia sin códigos
    imported, _ = qdpx.import_qdpx(qdpx.export_qdpx(project))
    assert imported.custom_domains["Vacía"] == "#ABCDEF"
    assert {c.name for c in imported.codes} == {"comunidad", "corazón", "nota"}


# ----- Convenciones de posición (hallazgo con una exportación real de NVivo 12.6) -----

def nvivo_style_qdpx() -> tuple[bytes, str]:
    """Texto con emojis y saltos de línea, posiciones como las escribe NVivo
    para Windows: unidades UTF-16 y cada salto de línea contado como 2."""
    lines = [f"Comentario {i} 😀 con la palabra escuela y algo más 👍" for i in range(40)]
    text = "\n".join(lines)
    positions = qdpx.Positions(text, 2, 2)
    selections = []
    for n, i in enumerate(range(5, 40, 5)):
        start = text.index(f"Comentario {i} ")
        end = start + len(lines[i])
        selections.append(
            f'<PlainTextSelection guid="00000000-0000-0000-0000-0000000001{n:02d}" '
            f'startPosition="{positions.to_units(start)}" endPosition="{positions.to_units(end)}">'
            f'<Coding guid="00000000-0000-0000-0000-0000000002{n:02d}">'
            f'<CodeRef targetGUID="00000000-0000-0000-0000-000000000003"/></Coding></PlainTextSelection>')
    qde = f"""<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="NVivo" origin="NVivo for Windows 12.6">
 <CodeBook><Codes><Code guid="00000000-0000-0000-0000-000000000003" name="línea" isCodable="true"/></Codes></CodeBook>
 <Sources><TextSource guid="00000000-0000-0000-0000-000000000010" name="yt" plainTextPath="internal://a.txt">
  {''.join(selections)}
 </TextSource></Sources></Project>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("project.qde", qde)
        zf.writestr("sources/a.txt", "﻿" + text)  # NVivo agrega BOM
    return buffer.getvalue(), text


def test_import_detects_nvivo_position_convention():
    data, _ = nvivo_style_qdpx()
    project, report = qdpx.import_qdpx(data)
    assert report["conventions"] == ["nvivo"]
    for code in (c for c in project.codes if c.doc_id):
        assert code.quote.startswith("Comentario ") and code.quote.endswith("👍")


def test_nvivo_profile_export_roundtrip_and_schema():
    import xmlschema

    project = rich_project()
    data = qdpx.export_qdpx(project, profile="nvivo")
    zf = zipfile.ZipFile(io.BytesIO(data))
    xmlschema.XMLSchema(str(XSD)).validate(zf.read("project.qde").decode("utf-8"))
    source = next(n for n in zf.namelist() if n.startswith("sources/"))
    assert b"\r\n" in zf.read(source)  # NVivo espera saltos de línea de Windows
    imported, report = qdpx.import_qdpx(data)
    assert imported.documents[0].text == project.documents[0].text  # vuelve a \n
    assert {c.quote for c in imported.codes if c.doc_id} == {"la escuela rural", "corazón"}


def test_crlf_source_is_normalized_and_quotes_keep_their_place():
    text = "Primera línea\r\nSegunda línea con escuela\r\nTercera"
    start = text.index("escuela")
    qde = f"""<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="CRLF">
 <CodeBook><Codes><Code guid="00000000-0000-0000-0000-000000000003" name="lugar" isCodable="true"/></Codes></CodeBook>
 <Sources><TextSource guid="00000000-0000-0000-0000-000000000010" name="t" plainTextPath="internal://b.txt">
  <PlainTextSelection guid="00000000-0000-0000-0000-000000000011" startPosition="{start}" endPosition="{start + 7}">
   <Coding guid="00000000-0000-0000-0000-000000000012"><CodeRef targetGUID="00000000-0000-0000-0000-000000000003"/></Coding>
  </PlainTextSelection></TextSource></Sources></Project>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("project.qde", qde)
        zf.writestr("sources/b.txt", text)
    project, _ = qdpx.import_qdpx(buffer.getvalue())
    doc, code = project.documents[0], next(c for c in project.codes if c.doc_id)
    assert "\r" not in doc.text
    assert doc.text[code.start:code.end] == "escuela" == code.quote
