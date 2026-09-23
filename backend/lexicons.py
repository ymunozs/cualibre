"""Léxicos de sentimiento NRC EmoLex por idioma del corpus (FR-077).

Ningún idioma viene incluido en la app ni en el repositorio. Los términos de
uso del NRC permiten usar el léxico en aplicaciones sin fines comerciales (con
crédito), pero prohíben redistribuir los datos («Do not redistribute the
data»). Por eso cada instalación lo obtiene directamente de la fuente oficial
(una descarga única de ~25 MB instala castellano, inglés y portugués) o del
.zip oficial que el investigador ya tenga, y lo convierte localmente a
<datos>/lexicons/nrc_<idioma>.json. Hasta la v1.12.0 el castellano venía
incluido; desde la v1.12.1 sigue el mismo camino (decisión del investigador,
2026-09-23).

Formato de cada entrada (igual que el español): palabra → [polaridad, emociones],
con las ocho emociones SIEMPRE con su clave castellana (la interfaz las traduce).
Una palabra que aparece varias veces (traducciones que coinciden) une sus
emociones; su polaridad es +1 o −1 solo si todas sus acepciones coinciden.
"""

from __future__ import annotations

import io
import json
import threading
import zipfile
from pathlib import Path

from . import storage

LANGS = ("es", "en", "pt")
NRC_URL = "https://saifmohammad.com/WebDocs/Lexicons/NRC-Emotion-Lexicon.zip"
NRC_HOME = "https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm"
DOWNLOADED_ID = "nrc-emolex-v0.92-2022"

# Archivo del .zip oficial y columna de la que sale cada idioma. El inglés es la
# columna original, presente en cualquiera de los archivos por idioma.
SOURCES = {
    "es": ("OneFilePerLanguage/Spanish-NRC-EmoLex.txt", "Spanish Word"),
    "en": ("OneFilePerLanguage/Portuguese-NRC-EmoLex.txt", "English Word"),
    "pt": ("OneFilePerLanguage/Portuguese-NRC-EmoLex.txt", "Portuguese Word"),
}

# Emociones del NRC (inglés) → clave canónica castellana usada en toda la app
EMOTIONS = {
    "anger": "rabia", "anticipation": "anticipación", "disgust": "asco", "fear": "miedo",
    "joy": "alegría", "sadness": "tristeza", "surprise": "sorpresa", "trust": "confianza",
}

_cache: dict[str, dict | None] = {}
_lock = threading.Lock()


class LexiconError(Exception):
    """Archivo que no es el léxico oficial, o descarga fallida."""


def lexicons_dir() -> Path:
    d = storage.base_dir() / "lexicons"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path(lang: str) -> Path:
    return lexicons_dir() / f"nrc_{lang}.json"


def get(lang: str) -> dict | None:
    """Léxico del idioma, o None si aún no está instalado."""
    if lang not in LANGS:
        return None
    with _lock:
        if lang not in _cache or _cache[lang] is None:
            try:
                _cache[lang] = json.loads(_path(lang).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                _cache[lang] = None
        return _cache[lang]


def lexicon_id(lang: str) -> str | None:
    """Identifica la versión del léxico con que se calculó un análisis."""
    return DOWNLOADED_ID if get(lang) is not None else None


def status() -> dict:
    return {
        lang: {"available": get(lang) is not None, "size": len(get(lang) or {})}
        for lang in LANGS
    }


def _rows_from_zip(data: bytes, member: str) -> list[list[str]]:
    """Filas de un archivo por idioma del .zip oficial (formato ancho)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            name = next((n for n in zf.namelist()
                         if n.endswith(member) and "__MACOSX" not in n), None)
            if name is None:
                raise LexiconError(f"zip sin {member}")
            text = zf.read(name).decode("utf-8")
    except zipfile.BadZipFile as exc:
        raise LexiconError("zip dañado") from exc
    return [line.split("\t") for line in text.splitlines() if line.strip()]


def convert(rows: list[list[str]], column: str) -> dict:
    """Filas NRC (encabezado + datos) → léxico {palabra: [polaridad, emociones]}."""
    header = rows[0]
    try:
        word_idx = header.index(column)
        flags = {name: header.index(name) for name in (*EMOTIONS, "positive", "negative")}
    except ValueError as exc:
        raise LexiconError(f"columna ausente: {exc}") from exc
    merged: dict[str, dict] = {}
    for row in rows[1:]:
        if len(row) <= word_idx:
            continue
        word = row[word_idx].strip().lower()
        if not word or " " in word:  # solo unigramas: el análisis empareja token a token
            continue
        entry = merged.setdefault(word, {"pos": False, "neg": False, "emos": set()})
        entry["pos"] |= row[flags["positive"]] == "1"
        entry["neg"] |= row[flags["negative"]] == "1"
        entry["emos"].update(EMOTIONS[e] for e in EMOTIONS if row[flags[e]] == "1")
    lexicon = {}
    for word, entry in merged.items():
        polarity = 1 if entry["pos"] and not entry["neg"] else -1 if entry["neg"] and not entry["pos"] else 0
        if polarity or entry["emos"]:
            lexicon[word] = [polarity, sorted(entry["emos"])]
    return lexicon


def install_from_zip(data: bytes, langs=LANGS) -> dict:
    """Convierte el .zip oficial del NRC e instala los léxicos pedidos."""
    rows_by_member: dict[str, list[list[str]]] = {}
    installed = {}
    for lang in langs:
        if lang not in SOURCES:
            continue
        member, column = SOURCES[lang]
        if member not in rows_by_member:
            rows_by_member[member] = _rows_from_zip(data, member)
        lexicon = convert(rows_by_member[member], column)
        if len(lexicon) < 1000:
            raise LexiconError(f"léxico {lang} incompleto ({len(lexicon)} entradas)")
        storage._atomic_write(_path(lang), json.dumps(lexicon, ensure_ascii=False, separators=(",", ":")))
        installed[lang] = len(lexicon)
    with _lock:
        for lang in installed:
            _cache.pop(lang, None)
    return installed


def download(langs=LANGS) -> dict:
    """Descarga única desde el sitio oficial del NRC (requiere internet)."""
    import httpx

    try:
        response = httpx.get(NRC_URL, timeout=180.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LexiconError(f"descarga fallida: {exc}") from exc
    return install_from_zip(response.content, langs)
