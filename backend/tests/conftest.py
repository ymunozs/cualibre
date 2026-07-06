import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Aísla cada test en un directorio de datos temporal."""
    monkeypatch.setenv("CUALIBRE_DATA_DIR", str(tmp_path / "cualibre-data"))
    return tmp_path / "cualibre-data"


@pytest.fixture
def client():
    from backend.app import app

    return TestClient(app)
