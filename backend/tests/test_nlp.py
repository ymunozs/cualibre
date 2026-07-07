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


def test_custom_exclusions():
    text = "Entrevistado: la escuela. Entrevistado: la memoria. entrevistadora pregunta"
    result = word_frequencies(text, lang="es", min_len=4,
                              exclusions={"Entrevistado", "ENTREVISTADORA"})
    words = {w["word"] for w in result}
    assert "entrevistado" not in words and "entrevistadora" not in words
    assert "escuela" in words and "memoria" in words


def test_pos_verbs_spanish():
    from backend.nlp import pos_frequencies

    text = "El niño cantó en la escuela. Los niños cantaban felices. La maestra escuchaba la canción."
    verbs = {w["word"]: w["count"] for w in pos_frequencies(text, "es", "verb", min_len=4)}
    assert verbs.get("cantar", 0) >= 2  # cantó + cantaban lematizan a cantar
    assert "escuchar" in verbs
    assert "escuela" not in verbs and "niño" not in verbs


def test_pos_nouns_spanish():
    from backend.nlp import pos_frequencies

    text = "El niño cantó en la escuela grande. La escuela estaba vacía."
    nouns = {w["word"] for w in pos_frequencies(text, "es", "noun", min_len=4)}
    assert "escuela" in nouns and "niño" in nouns
    assert "cantar" not in nouns and "grande" not in nouns


def test_pos_respects_exclusions():
    from backend.nlp import pos_frequencies

    text = "El entrevistado cantó. El entrevistado lloró."
    nouns = {w["word"] for w in pos_frequencies(text, "es", "noun", min_len=4,
                                                exclusions={"entrevistado"})}
    assert "entrevistado" not in nouns
