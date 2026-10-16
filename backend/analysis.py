"""Análisis lingüístico por documento: una sola pasada de spaCy, reutilizada.

Antes, cada consulta de foco gramatical (NLP) y de sentimiento volvía a pasar
TODO el corpus por spaCy: con un corpus de ~3,7 millones de caracteres eso
tomaba 35 s (verbos) y 95 s (sentimiento) en cada clic. Como el texto de un
documento no cambia después de importarlo, su análisis se calcula una vez y
se guarda:

- en memoria (LRU), para las consultas de la sesión;
- en disco (<datos>/cache/<idioma>-<huella>.json), para las sesiones
  siguientes. La huella es un hash del texto: si el texto cambia, la entrada
  simplemente deja de usarse. Borrar la carpeta cache/ es siempre seguro.

Cada análisis guarda los tokens con categoría gramatical (para frecuencias y
concordancias por lema), los tokens con carga emocional ya resueltos contra
el léxico NRC (para valencia, arco y tono por cita) y las posiciones que caen
bajo una negación (para aplicar los ajustes del investigador al léxico sin
volver a analizar, FR-086). Todos
los números que muestra la app se reconstruyen desde esas listas: siguen
siendo auditables (Principio VIII).

Corpus grandes: si falta analizar mucho texto, el trabajo corre en un hilo de
fondo y la API responde 202 con el avance, para que la interfaz muestre
«Analizando corpus: 12 de 60 documentos» en vez de congelarse.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import re
import sys
import threading
from collections import OrderedDict

from . import lexicons, storage

# 2: sentimiento en inglés y portugués; 3: negadores sin carga propia (v1.12);
# 4: posiciones negadas, para los ajustes del léxico (v1.14)
CACHE_VERSION = 4
CHUNK_CHARS = 100_000  # spaCy procesa por tramos: acota memoria y evita max_length
SYNC_LIMIT_CHARS = 250_000  # por debajo, se analiza en la misma petición

POS_KEYS = {"VERB": "verb", "NOUN": "noun", "PROPN": "noun", "ADJ": "adj"}

_ASTRAL = re.compile("[\U00010000-\U0010FFFF]")

_MEM_MAX = 256
_mem: "OrderedDict[tuple[str, str], dict]" = OrderedDict()
_mem_lock = threading.Lock()
_key_locks: dict[tuple[str, str], threading.Lock] = {}
_background: dict[str, threading.Thread] = {}
_background_texts: dict[str, list[str]] = {}


def digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:20]


def _disk_path(key: tuple[str, str]):
    lang, dg = key
    return storage.cache_dir() / f"{lang}-{dg}.json"


def _read_disk(key: tuple[str, str]) -> dict | None:
    try:
        data = json.loads(_disk_path(key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if _valid(data, key[0]) else None


def _valid(data: dict, lang: str) -> bool:
    """Un análisis sirve si es de esta versión y se hizo con el léxico que hay
    ahora (instalar el léxico inglés invalida los análisis hechos sin él)."""
    return data.get("v") == CACHE_VERSION and data.get("lex") == lexicons.lexicon_id(lang)


def _write_disk(key: tuple[str, str], data: dict) -> None:
    try:
        storage._atomic_write(
            _disk_path(key), json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )
    except OSError:
        pass  # la caché es un acelerador: si no se puede escribir, se recalcula


def _chunks(text: str):
    """Tramos de a lo más CHUNK_CHARS, cortados en un salto de línea o espacio."""
    start, n = 0, len(text)
    while start < n:
        end = min(n, start + CHUNK_CHARS)
        if end < n:
            cut = text.rfind("\n", start + CHUNK_CHARS // 2, end)
            if cut == -1:
                cut = text.rfind(" ", start + CHUNK_CHARS // 2, end)
            if cut != -1:
                end = cut + 1
        yield start, text[start:end]
        start = end


def _compute(text: str, lang: str) -> dict:
    from .nlp import MODEL_LOCK, _get_model
    from .sentiment import negated_starts, sentiment_records

    pos: list[list] = []
    sent: list[list] = []
    neg: list[int] = []
    lex_id = lexicons.lexicon_id(lang)
    chunks = list(_chunks(text))
    with MODEL_LOCK:
        model = _get_model(lang)
        for (offset, _), doc in zip(chunks, model.pipe([c for _, c in chunks], batch_size=4)):
            for token in doc:
                key = POS_KEYS.get(token.pos_)
                if key and token.is_alpha:
                    start = offset + token.idx
                    pos.append([start, start + len(token.text), key,
                                token.lemma_.lower().strip(), token.text.lower()])
            if lex_id:  # sin léxico instalado para el idioma no hay sentimiento
                sent.extend(sentiment_records(doc, offset, lang))
                neg.extend(negated_starts(doc, offset, lang))
    return {"v": CACHE_VERSION, "lex": lex_id, "pos": pos, "sent": sent, "neg": neg}


def _remember(key: tuple[str, str], data: dict) -> None:
    with _mem_lock:
        _mem[key] = data
        _mem.move_to_end(key)
        while len(_mem) > _MEM_MAX:
            _mem.popitem(last=False)


def get(text: str, lang: str) -> dict:
    """Análisis del texto (memoria → disco → cálculo). Seguro entre hilos."""
    key = (lang, digest(text))
    with _mem_lock:
        if key in _mem and _valid(_mem[key], lang):
            _mem.move_to_end(key)
            return _mem[key]
        lock = _key_locks.setdefault(key, threading.Lock())
    with lock:  # dos peticiones sobre el mismo texto calculan una sola vez
        with _mem_lock:
            if key in _mem and _valid(_mem[key], lang):
                return _mem[key]
        data = _read_disk(key)
        if data is None:
            data = _compute(text, lang)
            _write_disk(key, data)
        _remember(key, data)
    return data


def is_ready(text: str, lang: str) -> bool:
    key = (lang, digest(text))
    with _mem_lock:
        if key in _mem and _valid(_mem[key], lang):
            return True
    return _read_disk(key) is not None if _disk_path(key).exists() else False


def _run_background(texts: list[str], lang: str) -> None:
    for text in texts:
        try:
            get(text, lang)
        except Exception as exc:  # un documento problemático no debe colgar el sondeo
            print(f"[cualibre] análisis fallido ({lang}): {exc!r}", file=sys.stderr)
            _remember((lang, digest(text)),
                      {"v": CACHE_VERSION, "lex": lexicons.lexicon_id(lang), "pos": [], "sent": [],
                       "neg": []})


def _background_running(lang: str) -> bool:
    thread = _background.get(lang)
    return thread is not None and thread.is_alive()


def _background_backlog(lang: str) -> int:
    """Caracteres que el hilo de fondo aún no termina de analizar."""
    if not _background_running(lang):
        return 0
    return sum(len(t) for t in _background_texts.get(lang, []) if not is_ready(t, lang))


def warm(texts: list[str], lang: str) -> None:
    """Analiza en segundo plano lo que falte (p. ej., justo después de importar)."""
    missing = [t for t in texts if not is_ready(t, lang)]
    if missing and not _background_running(lang):
        thread = threading.Thread(target=_run_background, args=(missing, lang), daemon=True)
        _background[lang] = thread
        _background_texts[lang] = missing
        thread.start()


def prepare(texts: list[str], lang: str) -> tuple[bool, int, int]:
    """¿Están listos todos los análisis? → (listo, documentos listos, total).

    Si falta poco texto se calcula aquí mismo; si falta mucho, se lanza en
    segundo plano y quien llama responde «pendiente» con el avance."""
    total = len(texts)
    missing = [t for t in texts if not is_ready(t, lang)]
    if not missing:
        return True, total, total
    pending_chars = sum(len(t) for t in missing) + _background_backlog(lang)
    if pending_chars <= SYNC_LIMIT_CHARS:
        for text in missing:  # si el hilo de fondo ya lo está calculando, se espera
            get(text, lang)
        return True, total, total
    warm(missing, lang)
    return False, total - sum(1 for t in missing if not is_ready(t, lang)), total


# ----- Offsets: el frontend (JS) cuenta en UTF-16, Python en puntos de código -----
# Solo difieren si el texto trae caracteres fuera del plano básico (emojis,
# frecuentes en transcripciones de WhatsApp). Sin conversión, el salto
# «IR AL CANVAS» de las concordancias caía corrido tras cada emoji.

def _astral_positions(text: str) -> list[int]:
    return [m.start() for m in _ASTRAL.finditer(text)]


class OffsetMap:
    """Conversión puntos de código ↔ UTF-16 para UN texto (se arma una vez)."""

    def __init__(self, text: str):
        self.astral = _astral_positions(text)
        self.shifted = [a + k for k, a in enumerate(self.astral)]  # posición UTF-16

    def to_utf16(self, cp: int) -> int:
        return cp + bisect.bisect_left(self.astral, cp) if self.astral else cp

    def to_cp(self, unit: int) -> int:
        return unit - bisect.bisect_left(self.shifted, unit) if self.shifted else unit


def cp_to_utf16(text: str, cp: int) -> int:
    return OffsetMap(text).to_utf16(cp)


def utf16_to_cp(text: str, unit: int) -> int:
    return OffsetMap(text).to_cp(unit)
