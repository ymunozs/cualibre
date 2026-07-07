"""Música de foco: listado y servido seguro de pistas locales (FR-040)."""

from backend import storage


def test_empty_music_folder(client):
    data = client.get("/api/music").json()
    assert data["tracks"] == []
    assert data["folder"].endswith("musica")


def test_lists_only_audio_files(client):
    folder = storage.music_dir()
    (folder / "nocturno añil.mp3").write_bytes(b"ID3fake")
    (folder / "lied de foco.m4a").write_bytes(b"fake")
    (folder / "notas.txt").write_bytes(b"no es audio")
    (folder / ".DS_Store").write_bytes(b"")
    tracks = client.get("/api/music").json()["tracks"]
    assert tracks == ["lied de foco.m4a", "nocturno añil.mp3"]


def test_serves_track_bytes(client):
    (storage.music_dir() / "pieza.mp3").write_bytes(b"ID3contenido")
    r = client.get("/api/music/pieza.mp3")
    assert r.status_code == 200
    assert r.content == b"ID3contenido"


def test_rejects_traversal_and_non_audio(client):
    (storage.music_dir() / "pieza.mp3").write_bytes(b"x")
    assert client.get("/api/music/no-existe.mp3").status_code == 404
    assert client.get("/api/music/%2e%2e%2fconfig.json").status_code == 404
    (storage.music_dir() / "config.txt").write_bytes(b"x")
    assert client.get("/api/music/config.txt").status_code == 404
