"""v1.14: diccionario del lector de la biblioteca (FR-093). Datos sintéticos con
el formato real de las fuentes (Wiktextract y Open English WordNet); sin red."""

import gzip
import io
import json
import time
import zipfile

from backend import dictionary


def wiktextract(lang, entries):
    lines = [json.dumps({"word": w, "lang_code": lang, "pos": pos, "pos_title": title,
                         "senses": senses}, ensure_ascii=False) for w, pos, title, senses in entries]
    lines.append(json.dumps({"word": "house", "lang_code": "en", "pos": "noun",
                             "senses": [{"glosses": ["otra lengua: se descarta"]}]}))
    return gzip.compress("\n".join(lines).encode("utf-8"))


ES = [
    ("pelear", "verb", "Verbo intransitivo", [{"glosses": ["Sostener una pugna."]}, {"glosses": ["Luchar, batallar."]}]),
    ("peleaban", "verb", "Forma verbal", [{"glosses": ["Tercera persona del plural del pretérito imperfecto de indicativo de pelear."],
                                          "form_of": [{"word": "pelear"}]}]),
    ("peleamos", "verb", "Forma verbal", [{"glosses": ["Primera persona del plural del presente de pelear."],
                                          "form_of": [{"word": "pelear"}]}]),
    ("agobiado", "verb", "Forma verbal", [{"glosses": ["Participio de agobiar."]}]),
    ("agobiar", "verb", "Verbo transitivo", [{"glosses": ["Causar gran molestia o fatiga."]}]),
]


def wordnet_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("entries-r.json", json.dumps({"run": {
            "n": {"sense": [{"synset": "1-n"}]}, "v": {"form": ["ran"], "sense": [{"synset": "2-v"}]}}}))
        zf.writestr("noun.act.json", json.dumps({"1-n": {"definition": ["a score in baseball"], "partOfSpeech": "n"}}))
        zf.writestr("verb.motion.json", json.dumps({"2-v": {"definition": ["move fast on foot"],
                                                             "example": ["he ran home"], "partOfSpeech": "v"}}))
    return buffer.getvalue()


def test_build_wiktionary_forms_and_templates(data_dir, tmp_path):
    source = tmp_path / "es.gz"
    source.write_bytes(wiktextract("es", ES))
    assert dictionary.build_wiktionary(source, "es", dictionary.db_path("es")) == 2  # solo lemas con sentido propio
    r = dictionary.lookup("es", "Peleaban,")
    assert r["word"] == "peleaban"
    assert r["form_notes"] == ["Tercera persona del plural del pretérito imperfecto de indicativo de pelear."]
    assert r["groups"][0]["headword"] == "pelear" and r["groups"][0]["entries"][0]["senses"][0] == "Sostener una pugna."
    # «Participio de agobiar.» sin vínculo estructurado: se lee del texto
    r = dictionary.lookup("es", "agobiado")
    assert r["form_notes"] == ["Participio de agobiar."] and r["groups"][0]["headword"] == "agobiar"
    # Las descripciones repetidas se guardan como plantilla una sola vez
    import sqlite3
    con = sqlite3.connect(dictionary.db_path("es"))
    assert con.execute("SELECT COUNT(*) FROM forms").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM entries WHERE word = 'house'").fetchone()[0] == 0


def test_build_wordnet_irregular_forms(data_dir, tmp_path):
    source = tmp_path / "wn.zip"
    source.write_bytes(wordnet_zip())
    dictionary.build_wordnet(source, dictionary.db_path("en"))
    r = dictionary.lookup("en", "ran")
    group = r["groups"][0]
    assert group["headword"] == "run" and group["is_lemma"] is True
    assert group["entries"][0]["pos"] == "verb"  # forma flexionada: primero el verbo
    assert group["entries"][0]["senses"][0] == "move fast on foot (e.g., “he ran home”)"
    assert r["license"] == "CC BY 4.0"


def test_download_endpoint_installs_in_background(client, tmp_path):
    payloads = {"es": wiktextract("es", ES), "pt": wiktextract("pt", [("saudade", "noun", "Substantivo",
                [{"glosses": ["memória grata de algo ausente"]}])]), "en": wordnet_zip()}

    def fake_download(url, target, lang):
        target.write_bytes(payloads[lang])

    from backend import dictionary as d
    original = d._download
    d._download = fake_download
    try:
        assert client.get("/api/dictionary/status").json()["languages"]["es"]["installed"] is False
        r = client.post("/api/dictionary/download")
        assert r.status_code == 200
        for _ in range(100):
            langs = client.get("/api/dictionary/status").json()["languages"]
            if all(v["installed"] for v in langs.values()):
                break
            time.sleep(0.05)
        assert all(v["installed"] for v in langs.values())
        assert not list(d.dict_dir().glob("*.download"))  # lo descargado se borra
    finally:
        d._download = original
    pt = client.get("/api/dictionary/lookup", params={"word": "saudade", "lang": "pt"}).json()
    assert pt["groups"][0]["entries"][0]["senses"] == ["memória grata de algo ausente"]
    # Sin idioma: el del documento de la biblioteca
    item = client.post("/api/library/items", files={"file": (
        "n.txt", "La escuela rural no es una escuela pobre y la comunidad sostiene a la escuela.".encode(), "text/plain")}).json()
    auto = client.get("/api/dictionary/lookup", params={"word": "peleaban", "item_id": item["id"]}).json()
    assert auto["lang"] == "es" and auto["groups"][0]["headword"] == "pelear"


def test_download_failure_is_reported(client):
    from backend import dictionary as d

    def broken(url, target, lang):
        raise OSError("sin red")
    d.install("pt", download=broken)
    state = client.get("/api/dictionary/status").json()["languages"]["pt"]
    assert state["installed"] is False and state["progress"]["state"] == "error"
    missing = client.get("/api/dictionary/lookup", params={"word": "casa", "lang": "pt"}).json()
    assert missing["installed"] is False and missing["groups"] == []


def test_lookup_with_spaces_accents_and_symbols_in_the_data_path(monkeypatch, tmp_path):
    """La carpeta real en Mac es «Application Support»; en Windows hay tildes y barras."""
    import sys

    # Windows no admite «?» en nombres de carpeta; tildes, espacios y # sí
    name = "Pérez #1 datos" if sys.platform == "win32" else "Pérez #1 ¿datos?"
    folder = tmp_path / "Application Support" / name
    monkeypatch.setenv("CUALIBRE_DATA_DIR", str(folder))
    source = tmp_path / "es.gz"
    source.write_bytes(wiktextract("es", ES))
    dictionary.build_wiktionary(source, "es", dictionary.db_path("es"))
    assert dictionary.lookup("es", "peleaban")["groups"][0]["headword"] == "pelear"
