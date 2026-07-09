"""Análisis de sentimiento por léxico, auditable y offline (FR-059).

Léxico: NRC Emotion Lexicon (EmoLex) v0.92, © 2011 National Research Council
Canada, creado por Saif M. Mohammad y Peter Turney — traducción al español
incluida en la distribución oficial; uso libre para investigación (citar:
Mohammad & Turney 2013, "Crowdsourcing a Word-Emotion Association Lexicon").
5.094 unigramas con polaridad ±1 y 8 emociones.

Diseño deliberadamente transparente (decisión del investigador 2026-07-07:
léxico antes que transformers): cada puntaje es reconstruible desde las
palabras detectadas, que se reportan siempre junto al número.
Matching por forma Y por lema (spaCy) con inversión por negación en ventana
de 3 tokens ("no", "nunca", "sin"...).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

NEGATORS = {"no", "ni", "nunca", "jamás", "sin", "tampoco", "nadie", "nada", "ninguno", "ninguna"}
WINDOW = 3  # tokens hacia atrás donde una negación invierte la polaridad

_LEXICON: dict | None = None


def _lexicon_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "data_nrc_es.json"
    return Path(__file__).resolve().parent / "data_nrc_es.json"


def _lexicon() -> dict:
    global _LEXICON
    if _LEXICON is None:
        _LEXICON = json.loads(_lexicon_path().read_text(encoding="utf-8"))
    return _LEXICON


def _model():
    from .nlp import _get_model

    return _get_model("es")


def _score_doc(doc) -> dict:
    """Puntúa un doc de spaCy: valencia media, palabras con carga y emociones.

    emotion_words rastrea, por emoción, qué palabras exactas la dispararon —
    la trazabilidad que permite auditar cada clasificación (FR-071)."""
    lex = _lexicon()
    positives: Counter = Counter()
    negatives: Counter = Counter()
    emotions: Counter = Counter()
    emotion_words: dict[str, Counter] = {}
    total = 0
    tokens = [t for t in doc if t.is_alpha]
    for i, token in enumerate(tokens):
        entry = lex.get(token.text.lower()) or lex.get(token.lemma_.lower())
        if entry is None:
            continue
        polarity, emos = entry[0], entry[1]
        negated = any(t.text.lower() in NEGATORS for t in tokens[max(0, i - WINDOW):i])
        if negated:
            polarity = -polarity
        word = token.lemma_.lower() if lex.get(token.lemma_.lower()) else token.text.lower()
        if polarity > 0:
            positives[word] += 1
        elif polarity < 0:
            negatives[word] += 1
        if not negated:
            for emo in emos:
                emotions[emo] += 1
                emotion_words.setdefault(emo, Counter())[word] += 1
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


def analyze_texts(texts: list[str]) -> list[dict]:
    """Puntúa una lista de textos en lote (reutiliza el pipe de spaCy)."""
    model = _model()
    return [_score_doc(doc) for doc in model.pipe(texts, batch_size=32)]


def document_arc(text: str) -> list[dict]:
    """Arco emocional del relato (idea de syuzhet): valencia por párrafo."""
    paragraphs = [p for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []
    # Agrupar en máximo 40 tramos para que el arco sea legible
    if len(paragraphs) > 40:
        size = len(paragraphs) // 40 + 1
        paragraphs = ["\n".join(paragraphs[i:i + size]) for i in range(0, len(paragraphs), size)]
    return [
        {"i": i, "score": r["score"], "matched": r["matched"]}
        for i, r in enumerate(analyze_texts(paragraphs))
    ]
