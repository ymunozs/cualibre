import io
import zipfile

import pytest
from fastapi.testclient import TestClient

# Léxico NRC SINTÉTICO con el formato del .zip oficial: sus términos de uso
# prohíben redistribuir los datos reales, así que el repositorio no los trae.
# Cada fila: palabra inglesa, emociones/polaridad marcadas, portugués, castellano.
NRC_HEADER = ["English Word", "anger", "anticipation", "disgust", "fear", "joy",
              "negative", "positive", "sadness", "surprise", "trust"]
NRC_ROWS = [
    ("joy", {"joy", "anticipation", "trust", "positive"}, "alegria", "alegría"),
    ("love", {"joy", "positive"}, "amor", "amor"),
    ("hope", {"anticipation", "joy", "surprise", "trust", "positive"}, "esperança", "esperanza"),
    ("fear", {"fear", "negative"}, "medo", "miedo"),
    ("sadness", {"sadness", "negative"}, "tristeza", "tristeza"),
    ("abandonment", {"fear", "sadness", "negative"}, "abandono", "abandono"),
    ("weeping", {"sadness", "negative"}, "choro", "llanto"),
    ("bitter", {"anger", "disgust", "sadness", "negative"}, "amargo", "amargo"),
    ("cry", {"sadness", "negative"}, "chorar", "llorar"),
    ("darkness", {"fear", "sadness", "negative"}, "escuridão", "oscuridad"),
    ("nothing", {"sadness", "negative"}, "nada", "nada"),  # negador que el NRC marca negativo
    ("no", {"negative"}, "não", "no"),
]


def fake_nrc_zip(filler: int = 1200) -> bytes:
    rows = list(NRC_ROWS) + [(f"word{i}", {"positive"}, f"palavra{i}", f"palabra{i}")
                             for i in range(filler)]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for member, column, index in (("Portuguese-NRC-EmoLex.txt", "Portuguese Word", 2),
                                      ("Spanish-NRC-EmoLex.txt", "Spanish Word", 3)):
            lines = ["\t".join(NRC_HEADER + [column])]
            for row in rows:
                flags = ["1" if name in row[1] else "0" for name in NRC_HEADER[1:]]
                lines.append("\t".join([row[0], *flags, row[index]]))
            zf.writestr(f"NRC-Emotion-Lexicon/OneFilePerLanguage/{member}", "\n".join(lines))
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def fresh_lexicon_cache():
    from backend import lexicons

    lexicons._cache.clear()
    yield
    lexicons._cache.clear()


@pytest.fixture
def nrc_lexicons(data_dir):
    """Instala el léxico sintético (castellano, inglés y portugués) en los datos del test."""
    from backend import lexicons

    return lexicons.install_from_zip(fake_nrc_zip())


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Aísla cada test en un directorio de datos temporal."""
    monkeypatch.setenv("CUALIBRE_DATA_DIR", str(tmp_path / "cualibre-data"))
    return tmp_path / "cualibre-data"


@pytest.fixture
def client():
    from backend.app import app

    return TestClient(app)
