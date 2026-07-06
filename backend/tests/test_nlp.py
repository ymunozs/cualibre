"""NLP: stopwords por idioma, longitud mínima, conteos exactos (T035)."""

from backend.nlp import word_frequencies


def test_spanish_stopwords_excluded():
    text = "para este niño la escuela es la escuela de las emociones"
    words = {w["word"] for w in word_frequencies(text, lang="es", min_len=2)}
    assert "para" not in words and "este" not in words and "las" not in words
    assert "escuela" in words and "emociones" in words


def test_english_stopwords_excluded():
    text = "the teacher and the child were learning about learning"
    words = {w["word"] for w in word_frequencies(text, lang="en", min_len=2)}
    assert "the" not in words and "and" not in words and "were" not in words
    assert "learning" in words


def test_min_length_filter():
    text = "sol mar montaña cordillera"
    words = {w["word"] for w in word_frequencies(text, lang="es", min_len=4)}
    assert "sol" not in words and "mar" not in words
    assert "cordillera" in words


def test_exact_counts_and_order():
    text = "código código código memo memo cita"
    result = word_frequencies(text, lang="es", min_len=4)
    assert result[0] == {"word": "código", "count": 3}
    assert result[1] == {"word": "memo", "count": 2}


def test_empty_corpus():
    assert word_frequencies("", lang="es") == []


def test_digits_excluded():
    result = word_frequencies("2026 2026 análisis", lang="es", min_len=4)
    assert all(w["word"] != "2026" for w in result)
