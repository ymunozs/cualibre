"""Concordancias (KWIC): coincidencias literales y por lema, en contexto (FR-063)."""

from backend.models import Document
from backend.nlp import kwic_occurrences


def make_doc(text, filename="doc.txt", doc_id="d1"):
    return Document(id=doc_id, filename=filename, text=text)


def test_literal_match_with_context():
    doc = make_doc("La escuela rural fue mi hogar. Volví a la escuela años después.")
    results = kwic_occurrences([doc], "escuela", pos="all")
    assert len(results) == 2
    assert results[0]["match"] == "escuela"
    assert results[0]["before"].endswith("La ")
    assert results[0]["after"].startswith(" rural")
    assert results[0]["doc_id"] == "d1" and results[0]["filename"] == "doc.txt"


def test_literal_match_case_insensitive():
    doc = make_doc("ESCUELA rural, la Escuela y la escuela.")
    results = kwic_occurrences([doc], "escuela", pos="all")
    assert len(results) == 3
    assert results[0]["match"] == "ESCUELA"


def test_offsets_are_exact():
    doc = make_doc("El niño cantó en la escuela grande de la villa.")
    results = kwic_occurrences([doc], "escuela", pos="all")
    start, end = results[0]["start"], results[0]["end"]
    assert doc.text[start:end] == "escuela"


def test_word_boundary_no_partial_match():
    doc = make_doc("La escuelita no es lo mismo que la escuela.")
    results = kwic_occurrences([doc], "escuela", pos="all")
    assert len(results) == 1  # "escuelita" no debe matchear


def test_empty_query_returns_empty():
    doc = make_doc("Cualquier texto.")
    assert kwic_occurrences([doc], "", pos="all") == []
    assert kwic_occurrences([doc], "   ", pos="all") == []


def test_no_matches():
    doc = make_doc("Un texto que no contiene la palabra buscada.")
    assert kwic_occurrences([doc], "inexistente", pos="all") == []


def test_pos_verb_matches_by_lemma_with_real_text():
    doc = make_doc("El niño cantó en la escuela. Los niños cantaban felices.")
    results = kwic_occurrences([doc], "cantar", lang="es", pos="verb")
    matches = sorted(r["match"] for r in results)
    assert matches == ["cantaban", "cantó"]
    for r in results:
        assert doc.text[r["start"]:r["end"]] == r["match"]


def test_pos_noun_excludes_other_categories():
    doc = make_doc("El niño cantó en la escuela grande.")
    results = kwic_occurrences([doc], "cantar", lang="es", pos="noun")
    assert results == []  # "cantar" no es sustantivo en este texto


def test_multiple_documents_preserve_identity():
    doc1 = make_doc("La escuela del pueblo.", filename="a.txt", doc_id="d1")
    doc2 = make_doc("Otra escuela distinta.", filename="b.txt", doc_id="d2")
    results = kwic_occurrences([doc1, doc2], "escuela", pos="all")
    assert {r["filename"] for r in results} == {"a.txt", "b.txt"}
    assert {r["doc_id"] for r in results} == {"d1", "d2"}


def test_limit_caps_total_results():
    text = " ".join(["escuela"] * 20)
    doc = make_doc(text)
    results = kwic_occurrences([doc], "escuela", pos="all", limit=5)
    assert len(results) == 5


def test_window_size_respected():
    doc = make_doc("x" * 100 + " escuela " + "y" * 100)
    results = kwic_occurrences([doc], "escuela", pos="all", window=10)
    assert len(results[0]["before"]) == 10
    assert len(results[0]["after"]) == 10
