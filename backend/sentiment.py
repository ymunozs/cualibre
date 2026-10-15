"""Análisis de sentimiento por léxico, auditable y offline (FR-059, FR-077).

Léxico: NRC Emotion Lexicon (EmoLex) v0.92, © 2011 National Research Council
Canada, creado por Saif M. Mohammad y Peter Turney; uso libre para
investigación sin fines comerciales (citar: Mohammad & Turney 2013,
"Crowdsourcing a Word-Emotion Association Lexicon"). Español incluido; inglés
y portugués se obtienen de la fuente oficial en cada equipo (lexicons.py).
Polaridad ±1 y 8 emociones.

Diseño deliberadamente transparente (decisión del investigador 2026-07-07:
léxico antes que transformers): cada puntaje es reconstruible desde las
palabras detectadas, que se reportan siempre junto al número.
Matching por forma Y por lema (spaCy) con inversión por negación en ventana
de 3 tokens ("no", "nunca", "sin"...; "not", "never", "n't"...; "não"...).

Rendimiento: los tokens con carga de cada documento se calculan una sola vez
(analysis.py) y de ellos se derivan valencia, arco y tono por cita.
"""

from __future__ import annotations

import bisect
import re
from collections import Counter

from . import lexicons

NEGATORS = {
    "es": {"no", "ni", "nunca", "jamás", "sin", "tampoco", "nadie", "nada", "ninguno", "ninguna"},
    "en": {"not", "no", "never", "n't", "nor", "neither", "without", "nobody", "nothing",
           "none", "cannot", "hardly"},
    "pt": {"não", "nem", "nunca", "jamais", "sem", "tampouco", "ninguém", "nada",
           "nenhum", "nenhuma"},
}
WINDOW = 3  # tokens hacia atrás donde una negación invierte la polaridad


def sentiment_records(doc, offset: int = 0, lang: str = "es") -> list[list]:
    """Tokens con carga de un doc de spaCy, ya resueltos contra el léxico.

    Cada registro es [posición, polaridad (tras la negación), palabra,
    emociones]. Una palabra negada invierte su polaridad y no aporta
    emociones. La palabra reportada es el lema si el léxico lo conoce."""
    lex = lexicons.get(lang)
    if not lex:
        return []
    negators = NEGATORS.get(lang, set())
    records: list[list] = []
    # Tokens alfabéticos + negadores no alfabéticos ("n't" en inglés): con el
    # castellano la lista es idéntica a la de siempre (todos sus negadores son alfabéticos)
    tokens = [t for t in doc if t.is_alpha or t.lower_ in negators]
    for i, token in enumerate(tokens):
        # Un negador solo invierte lo que sigue: nunca cuenta como palabra con
        # carga («nada» y «não» figuran como negativas en las traducciones del
        # NRC; contarlas duplicaba el efecto de cada negación). Cambio v1.12.
        if not token.is_alpha or token.lower_ in negators:
            continue
        text, lemma = token.text.lower(), token.lemma_.lower()
        entry = lex.get(text) or lex.get(lemma)
        if entry is None:
            continue
        polarity, emos = entry[0], entry[1]
        negated = any(t.text.lower() in negators for t in tokens[max(0, i - WINDOW):i])
        if negated:
            polarity = -polarity
        word = lemma if lex.get(lemma) else text
        records.append([offset + token.idx, polarity, word, [] if negated else list(emos)])
    return records


def negated_starts(doc, offset: int = 0, lang: str = "es") -> list[int]:
    """Posiciones de las palabras que caen bajo una negación (misma ventana y
    los mismos negadores que sentiment_records). Permite aplicar los ajustes
    del investigador al léxico (FR-086) sin volver a pasar el corpus por spaCy."""
    negators = NEGATORS.get(lang, set())
    tokens = [t for t in doc if t.is_alpha or t.lower_ in negators]
    starts = []
    for i, token in enumerate(tokens):
        if not token.is_alpha or token.lower_ in negators:
            continue
        if any(t.text.lower() in negators for t in tokens[max(0, i - WINDOW):i]):
            starts.append(offset + token.idx)
    return starts


POLARITY_CATEGORIES = {"positivo": 1, "negativo": -1}


def _word_pattern(word: str):
    """La palabra exacta, sin importar mayúsculas, entre límites de letras."""
    return re.compile(r"(?<![^\W\d_])" + re.escape(word) + r"(?![^\W\d_])", re.IGNORECASE)


def apply_overrides(text: str, data: dict, overrides) -> list[list]:
    """Tokens con carga tras los ajustes del investigador al léxico (FR-086).

    - Descartar una palabra de una emoción le quita esa emoción; descartarla
      de una polaridad la deja sin polaridad.
    - Sumar una palabra la busca en el texto por forma (literal) o por lema
      (sustantivos, verbos y adjetivos ya lematizados) y le da la emoción o
      polaridad indicada. La negación se respeta igual que en el léxico: una
      palabra negada invierte su polaridad y no aporta emociones.

    data es el análisis guardado del documento (analysis.get). Sin ajustes,
    devuelve los registros tal cual."""
    records = data["sent"]
    if overrides is None or overrides.is_empty():
        return records
    removed: dict[str, set] = {}
    for category, words in overrides.removed.items():
        for word in words:
            removed.setdefault(word, set()).add(category)
    added: dict[str, set] = {}
    for category, words in overrides.added.items():
        for word in words:
            added.setdefault(word, set()).add(category)
    negated = set(data.get("neg", ()))

    # Registro de trabajo: [posición, polaridad base (antes de negar), palabra, emociones, negada]
    work: dict[int, list] = {}
    for position, polarity, word, emos in records:
        is_negated = position in negated
        work[position] = [position, -polarity if is_negated else polarity, word,
                          list(emos), is_negated, set()]
    if added:
        by_lemma: dict[str, list[int]] = {}
        for start, _end, _key, lemma, _form in data.get("pos", ()):
            if lemma in added:
                by_lemma.setdefault(lemma, []).append(start)
        for word, categories in added.items():
            starts = set(by_lemma.get(word, ()))
            starts.update(m.start() for m in _word_pattern(word).finditer(text))
            for start in starts:
                entry = work.get(start)
                if entry is None:  # palabra fuera del léxico: registro nuevo
                    entry = work[start] = [start, 0, word, [], start in negated, set()]
                entry[5] |= categories

    adjusted = []
    for position in sorted(work):
        _, base, word, emos, is_negated, extra = work[position]
        drop = removed.get(word, set())
        extra = extra | added.get(word, set())
        if (base > 0 and "positivo" in drop) or (base < 0 and "negativo" in drop):
            base = 0
        if extra & POLARITY_CATEGORIES.keys():
            base = sum(POLARITY_CATEGORIES[c] for c in extra & POLARITY_CATEGORIES.keys())
        if is_negated:
            polarity, emotions = -base, []
        else:
            polarity = base
            emotions = [e for e in emos if e not in drop]
            emotions += sorted(c for c in extra
                               if c not in POLARITY_CATEGORIES and c not in emotions)
        if polarity or emotions:
            adjusted.append([position, polarity, word, emotions])
    return adjusted


def score_records(records) -> dict:
    """Valencia media, palabras con carga y emociones de un conjunto de tokens.

    emotion_words rastrea, por emoción, qué palabras exactas la dispararon —
    la trazabilidad que permite auditar cada clasificación (FR-071)."""
    positives: Counter = Counter()
    negatives: Counter = Counter()
    emotions: Counter = Counter()
    emotion_words: dict[str, Counter] = {}
    total = 0
    for _pos, polarity, word, emos in records:
        if polarity > 0:
            positives[word] += 1
        elif polarity < 0:
            negatives[word] += 1
        for emo in emos:
            emotions[emo] += 1
            if emo not in emotion_words:
                emotion_words[emo] = Counter()
            emotion_words[emo][word] += 1
        total += polarity
    matched = sum(positives.values()) + sum(negatives.values())
    return {
        "score": round(total / matched, 3) if matched else 0.0,
        "matched": matched,
        "positives": positives,
        "negatives": negatives,
        "emotions": emotions,
        "emotion_words": emotion_words,
    }


def valence(records) -> tuple[float, int]:
    """(valencia media, palabras con carga): lo mismo que score_records para
    arcos y citas, sin armar los contadores de palabras."""
    total = matched = 0
    for record in records:
        polarity = record[1]
        if polarity:
            total += polarity
            matched += 1
    return (round(total / matched, 3) if matched else 0.0), matched


def records_between(records, start: int, end: int, starts: list[int] | None = None) -> list:
    """Tokens con carga cuya posición cae en [start, end) (puntos de código).
    starts: posiciones ya extraídas, para no recalcularlas en cada cita."""
    if starts is None:
        starts = [r[0] for r in records]
    return records[bisect.bisect_left(starts, start):bisect.bisect_left(starts, end)]


def analyze_texts(texts: list[str], lang: str = "es") -> list[dict]:
    """Puntúa una lista de textos (reutiliza los análisis ya calculados)."""
    from . import analysis

    return [score_records(analysis.get(text, lang)["sent"]) for text in texts]


def arc_from_records(text: str, records) -> list[dict]:
    """Arco emocional del relato (idea de syuzhet): valencia por párrafo,
    agrupados en a lo más 40 tramos para que el arco sea legible."""
    spans: list[tuple[int, int]] = []
    position = 0
    for line in text.split("\n"):
        if line.strip():
            spans.append((position, position + len(line)))
        position += len(line) + 1
    if not spans:
        return []
    if len(spans) > 40:
        size = len(spans) // 40 + 1
        spans = [(spans[i][0], spans[min(i + size, len(spans)) - 1][1])
                 for i in range(0, len(spans), size)]
    starts = [r[0] for r in records]
    arc = []
    for i, (start, end) in enumerate(spans):
        chunk = records[bisect.bisect_left(starts, start):bisect.bisect_left(starts, end)]
        score, matched = valence(chunk)
        arc.append({"i": i, "score": score, "matched": matched})
    return arc


def document_arc(text: str, lang: str = "es") -> list[dict]:
    from . import analysis

    return arc_from_records(text, analysis.get(text, lang)["sent"])
