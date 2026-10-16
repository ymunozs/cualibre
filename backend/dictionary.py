"""Diccionario del lector de la biblioteca (FR-093): castellano, inglés y portugués.

Como el léxico de sentimiento, no viene incluido: cada equipo lo descarga UNA
vez desde la fuente abierta y lo convierte aquí en una base SQLite compacta
(<datos>/diccionarios/<idioma>.sqlite); el archivo descargado se borra.

Fuentes (abiertas, con atribución en la interfaz):
- Castellano y portugués: Wiktionary en su propio idioma (es.wiktionary y
  pt.wiktionary), en la extracción de Wiktextract publicada por kaikki.org.
  Licencia CC BY-SA 4.0 (y GFDL).
- Inglés: Open English WordNet (edición 2025), CC BY 4.0.

Solo es consulta (Principio VIII): nada se escribe en el proyecto.
"""

from __future__ import annotations

import gzip
import json
import re
import sqlite3
import threading
import zipfile
from pathlib import Path
from typing import Optional

import httpx

from . import storage

LANGS = ("es", "en", "pt")
SOURCES = {
    "es": {"url": "https://kaikki.org/eswiktionary/raw-wiktextract-data.jsonl.gz",
           "name": "Wiktionary (es) · Wiktextract/kaikki.org", "license": "CC BY-SA 4.0",
           "size_mb": 98},
    "pt": {"url": "https://kaikki.org/ptwiktionary/raw-wiktextract-data.jsonl.gz",
           "name": "Wiktionary (pt) · Wiktextract/kaikki.org", "license": "CC BY-SA 4.0",
           "size_mb": 36},
    "en": {"url": "https://github.com/globalwordnet/english-wordnet/releases/download/"
                  "2025-edition/english-wordnet-2025-json.zip",
           "name": "Open English WordNet 2025", "license": "CC BY 4.0", "size_mb": 10},
}
USER_AGENT = "CUA-LIBRE-Studio/2.0 (https://github.com/ymunozs/cualibre)"
MAX_SENSES = 8
WN_POS = {"n": "noun", "v": "verb", "a": "adj", "s": "adj", "r": "adv"}

_lock = threading.Lock()
_progress: dict[str, dict] = {}  # idioma -> {state, done, total, error}
_thread: Optional[threading.Thread] = None


def dict_dir() -> Path:
    d = storage.base_dir() / "diccionarios"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path(lang: str) -> Path:
    return dict_dir() / f"{lang}.sqlite"


def installed(lang: str) -> bool:
    return lang in LANGS and db_path(lang).exists()


def status() -> dict:
    with _lock:
        progress = {k: dict(v) for k, v in _progress.items()}
    return {lang: {"installed": installed(lang), **SOURCES[lang],
                   "progress": progress.get(lang)} for lang in LANGS}


def _set(lang: str, **fields) -> None:
    with _lock:
        _progress.setdefault(lang, {}).update(fields)


# ----- Construcción de las bases -----

def _new_db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE entries (word TEXT, pos TEXT, senses TEXT);
        CREATE TABLE forms (form TEXT, lemma TEXT, descr INTEGER);
        CREATE TABLE descrs (id INTEGER PRIMARY KEY, text TEXT UNIQUE);
    """)
    return con


def _descr_id(con: sqlite3.Connection, cache: dict, text: str) -> Optional[int]:
    """Las descripciones de formas flexionadas se repiten miles de veces
    («Tercera persona del plural del pretérito… de ~»): se guardan una vez."""
    if not text:
        return None
    if text not in cache:
        con.execute("INSERT OR IGNORE INTO descrs(text) VALUES (?)", (text,))
        cache[text] = con.execute("SELECT id FROM descrs WHERE text = ?", (text,)).fetchone()[0]
    return cache[text]


# «Participio de agobiar.», «Forma del plural de casa.», «… do verbo brigar»
FORM_OF_RE = re.compile(r"\b(?:de|do verbo|da|do)\s+([^\W\d_]+)\s*\.?\s*$", re.IGNORECASE)


def _finish(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE INDEX entries_word ON entries(word);
        CREATE INDEX forms_form ON forms(form);
    """)
    con.commit()
    con.close()


def build_wiktionary(source: Path, lang: str, target: Path, on_progress=None) -> int:
    """Base a partir de la extracción de Wiktextract (JSONL comprimido): solo
    las entradas del propio idioma, con sus acepciones y, para las formas
    flexionadas («peleaban»), el lema al que remiten («pelear»)."""
    marker = f'"lang_code": "{lang}"'
    tmp = target.with_suffix(".tmp")
    con = _new_db(tmp)
    descr_cache: dict[str, int] = {}
    count = 0
    with gzip.open(source, "rt", encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            if on_progress and n % 50000 == 0:
                on_progress(n)
            if marker not in line:  # filtro barato antes de interpretar el JSON
                continue
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if data.get("lang_code") != lang:
                continue
            word = (data.get("word") or "").strip()
            if not word:
                continue
            pos = data.get("pos_title") or data.get("pos") or ""
            is_form_entry = pos.lower().startswith("forma") or data.get("pos") == "verb_form"
            senses, lemmas = [], []
            for sense in data.get("senses") or []:
                glosses = sense.get("glosses") or []
                gloss = glosses[-1][:400] if glosses else ""
                found = [(t.get("word") or "").strip() for t in sense.get("form_of") or []]
                if not any(found) and is_form_entry and gloss:
                    match = FORM_OF_RE.search(gloss)
                    found = [match.group(1)] if match else []
                found = [f for f in found if f and f.lower() != word.lower()]
                if found:
                    lemmas += [(f, gloss) for f in found]
                elif gloss:
                    senses.append(gloss)
                if len(senses) >= MAX_SENSES:
                    break
            # Forma flexionada («peleaban»): solo el vínculo al lema y su
            # descripción gramatical como plantilla (el lema trae el significado)
            for lemma, gloss in lemmas:
                template = re.sub(rf"\b{re.escape(lemma)}\b", "~", gloss)[:200]
                con.execute("INSERT INTO forms VALUES (?, ?, ?)",
                            (word.lower(), lemma, _descr_id(con, descr_cache, template)))
            if senses:
                con.execute("INSERT INTO entries VALUES (?, ?, ?)",
                            (word.lower(), pos, json.dumps(senses, ensure_ascii=False)))
                count += 1
    _finish(con)
    tmp.replace(target)
    return count


def build_wordnet(source: Path, target: Path, on_progress=None) -> int:
    """Base a partir de Open English WordNet en JSON: lema → definiciones por
    categoría gramatical, y formas irregulares («ran» → «run»)."""
    tmp = target.with_suffix(".tmp")
    con = _new_db(tmp)
    count = 0
    with zipfile.ZipFile(source) as zf:
        names = zf.namelist()
        synsets: dict[str, dict] = {}
        for name in names:
            if name.endswith(".json") and not name.startswith("entries-"):
                synsets.update(json.loads(zf.read(name)))
        entry_files = [n for n in names if n.startswith("entries-")]
        for i, name in enumerate(entry_files):
            if on_progress:
                on_progress(i)
            for lemma, by_pos in json.loads(zf.read(name)).items():
                for pos_key, info in by_pos.items():
                    senses = []
                    for sense in info.get("sense") or []:
                        syn = synsets.get(sense.get("synset", ""))
                        if syn and syn.get("definition"):
                            text = syn["definition"][0]
                            if syn.get("example"):
                                text += f" (e.g., “{syn['example'][0]}”)"
                            senses.append(text)
                        if len(senses) >= MAX_SENSES:
                            break
                    if senses:
                        con.execute("INSERT INTO entries VALUES (?, ?, ?)",
                                    (lemma.lower(), WN_POS.get(pos_key, pos_key),
                                     json.dumps(senses, ensure_ascii=False)))
                        count += 1
                    for form in info.get("form") or []:
                        con.execute("INSERT INTO forms VALUES (?, ?, NULL)", (form.lower(), lemma))
    _finish(con)
    tmp.replace(target)
    return count


def _download(url: str, target: Path, lang: str) -> None:
    with httpx.Client(timeout=60.0, follow_redirects=True,
                      headers={"User-Agent": USER_AGENT}) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length") or 0)
            done = 0
            _set(lang, state="downloading", done=0, total=total)
            with open(target, "wb") as fh:
                for chunk in response.iter_bytes(1 << 20):
                    fh.write(chunk)
                    done += len(chunk)
                    _set(lang, done=done)


def install(lang: str, download=None) -> None:
    """Descarga y construye un idioma (en el hilo de fondo)."""
    source = SOURCES[lang]
    raw = dict_dir() / f"{lang}.download"
    try:
        (download or _download)(source["url"], raw, lang)
        _set(lang, state="building", done=0, total=0)
        if lang == "en":
            build_wordnet(raw, db_path(lang), lambda n: _set(lang, done=n))
        else:
            build_wiktionary(raw, lang, db_path(lang), lambda n: _set(lang, done=n))
        _set(lang, state="ready", error="")
    except Exception as exc:  # sin red, fuente caída, archivo dañado: se informa
        _set(lang, state="error", error=type(exc).__name__)
    finally:
        raw.unlink(missing_ok=True)


def install_all(langs=LANGS, download=None) -> bool:
    """Lanza la instalación en segundo plano. False si ya hay una en curso."""
    global _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return False
        for lang in langs:
            _progress[lang] = {"state": "queued", "done": 0, "total": 0, "error": ""}

        def run():
            for lang in langs:
                install(lang, download)

        _thread = threading.Thread(target=run, daemon=True)
        _thread.start()
    return True


# ----- Consulta -----

def _query(lang: str, word: str) -> list[dict]:
    con = sqlite3.connect(f"file:{db_path(lang)}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT pos, senses FROM entries WHERE word = ?", (word,)).fetchall()
        return [{"pos": pos, "senses": json.loads(senses)} for pos, senses in rows]
    finally:
        con.close()


def _form_lemmas(lang: str, word: str) -> list[tuple[str, str]]:
    """(lema, descripción gramatical) de una forma flexionada."""
    con = sqlite3.connect(f"file:{db_path(lang)}?mode=ro", uri=True)
    try:
        rows = con.execute("""SELECT f.lemma, d.text FROM forms f
                              LEFT JOIN descrs d ON d.id = f.descr WHERE f.form = ?""",
                           (word,)).fetchall()
        out, seen = [], set()
        for lemma, text in rows:
            key = (lemma, text)
            if key not in seen:
                seen.add(key)
                out.append((lemma, (text or "").replace("~", lemma)))
        return out
    finally:
        con.close()


def _spacy_lemma(lang: str, word: str) -> str:
    try:
        from .nlp import MODEL_LOCK, _get_model

        with MODEL_LOCK:
            doc = _get_model(lang)(word)
        return doc[0].lemma_.lower() if len(doc) else ""
    except Exception:
        return ""


def lookup(lang: str, word: str) -> dict:
    """Definiciones de una palabra: la forma escrita y, si es una forma
    flexionada, también su lema (según el propio diccionario o spaCy)."""
    word = (word or "").strip().strip(".,;:!?¡¿()[]«»“”\"'").lower()
    result = {"lang": lang, "word": word, "groups": [], "source": SOURCES[lang]["name"],
              "license": SOURCES[lang]["license"]}
    if not word or not installed(lang):
        return result
    seen = set()
    forms = _form_lemmas(lang, word)
    notes = [text for _lemma, text in forms if text]
    if notes:  # «peleaban»: Tercera persona del plural del pretérito… de pelear
        result["form_notes"] = list(dict.fromkeys(notes))[:3]
    candidates = [word] + [lemma for lemma, _text in forms]
    lemma = _spacy_lemma(lang, word)
    if lemma:
        candidates.append(lemma)
    for candidate in candidates:
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        entries = _query(lang, key)
        if key != word:  # la palabra escrita era una forma: primero verbos y adjetivos
            rank = {"verb": 0, "adj": 1}
            entries.sort(key=lambda e: rank.get(e["pos"], 2))
        if entries:
            result["groups"].append({"headword": candidate, "is_lemma": key != word,
                                     "entries": entries})
    return result
