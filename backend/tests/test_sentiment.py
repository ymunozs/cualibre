"""Sentimiento por léxico: polaridad, negación, arco, endpoint (FR-059)."""

from backend.sentiment import analyze_texts, document_arc


def test_positive_and_negative_valence():
    results = analyze_texts([
        "Sentí una alegría inmensa, mucho amor y esperanza en la escuela.",
        "El miedo y la tristeza del abandono provocaron un llanto amargo.",
    ])
    assert results[0]["score"] > 0.5
    assert results[1]["score"] < -0.5
    assert "alegría" in results[0]["positives"]
    assert "miedo" in results[1]["negatives"]


def test_negation_inverts_polarity():
    plain = analyze_texts(["Siento alegría."])[0]
    negated = analyze_texts(["No siento alegría."])[0]
    assert plain["score"] > 0
    assert negated["score"] < 0  # "alegría" negada invierte su aporte


def test_emotions_detected():
    result = analyze_texts(["El miedo paralizaba al niño en la oscuridad."])[0]
    assert result["emotions"].get("miedo", 0) >= 1


def test_arc_by_paragraphs():
    text = "La fiesta fue pura alegría y amor.\nDespués llegó la tristeza y el miedo."
    arc = document_arc(text)
    assert len(arc) == 2
    assert arc[0]["score"] > 0 > arc[1]["score"]


def test_lemma_matching():
    # "lloraba" debe matchear vía lema "llorar" (entrada del léxico)
    result = analyze_texts(["El niño lloraba desconsolado."])[0]
    assert result["negatives"].get("llorar", 0) == 1


def test_sentiment_endpoint(client):
    text = "Primer párrafo de alegría y amor.\nSegundo párrafo de miedo y tristeza."
    client.post("/api/documents", files={"file": ("e.txt", text.encode(), "text/plain")})
    doc = client.get("/api/project").json()["documents"][0]
    client.post("/api/codes", json={"doc_id": doc["id"], "domain": "Emocional",
                                    "name": "gozo", "quote": "alegría y amor",
                                    "start": 18, "end": 32})
    data = client.get("/api/sentiment").json()
    assert len(data["documents"]) == 1
    assert len(data["documents"][0]["arc"]) == 2
    assert any(d["domain"] == "Emocional" and d["score"] > 0 for d in data["domains"])
    assert any(w["word"] == "alegría" for w in data["words"]["positive"])
    assert any(e["emotion"] == "miedo" for e in data["emotions"])
