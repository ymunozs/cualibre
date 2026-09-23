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
