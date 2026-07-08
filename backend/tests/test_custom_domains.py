"""Categorías Básicas + personalizadas por proyecto (FR-064)."""


def test_domains_endpoint_shape(client):
    data = client.get("/api/domains").json()
    assert set(data) == {"basic", "custom"}
    assert "Emocional" in data["basic"] and data["custom"] == {}


def test_create_custom_domain(client):
    r = client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    assert r.status_code == 201
    data = r.json()
    assert data["custom"]["Territorio"] == "#AABBCC"
    assert client.get("/api/domains").json()["custom"] == {"Territorio": "#AABBCC"}


def test_custom_domain_color_normalized_uppercase(client):
    r = client.post("/api/domains/custom", json={"name": "Cuerpo", "color": "#abcdef"})
    assert r.json()["custom"]["Cuerpo"] == "#ABCDEF"


def test_custom_domain_rejects_invalid_color(client):
    r = client.post("/api/domains/custom", json={"name": "X", "color": "azul"})
    assert r.status_code == 422
    r2 = client.post("/api/domains/custom", json={"name": "Y", "color": "#ABC"})
    assert r2.status_code == 422


def test_custom_domain_rejects_empty_name(client):
    assert client.post("/api/domains/custom", json={"name": "  ", "color": "#123456"}).status_code == 422


def test_custom_domain_rejects_duplicate_vs_basic(client):
    r = client.post("/api/domains/custom", json={"name": "emocional", "color": "#123456"})
    assert r.status_code == 409  # case-insensitive contra Categorías Básicas


def test_custom_domain_rejects_duplicate_vs_custom(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#111111"})
    r = client.post("/api/domains/custom", json={"name": "TERRITORIO", "color": "#222222"})
    assert r.status_code == 409


def test_code_with_custom_domain(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    r = client.post("/api/codes", json={"domain": "Territorio", "name": "el río enseña"})
    assert r.status_code == 201
    assert r.json()["domain"] == "Territorio"


def test_code_with_unknown_domain_rejected(client):
    r = client.post("/api/codes", json={"domain": "NoExiste", "name": "x"})
    assert r.status_code == 422


def test_update_code_to_custom_domain(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    client.post("/api/codes", json={"domain": "Teórico", "name": "uno"})
    r = client.patch("/api/codes/1", json={"domain": "Territorio"})
    assert r.status_code == 200 and r.json()["domain"] == "Territorio"


def test_delete_custom_domain_unused(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    r = client.delete("/api/domains/custom/Territorio")
    assert r.status_code == 200 and r.json()["in_use"] == 0
    assert client.get("/api/domains").json()["custom"] == {}


def test_delete_custom_domain_in_use_requires_confirm(client):
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    client.post("/api/codes", json={"domain": "Territorio", "name": "uno"})
    r = client.delete("/api/domains/custom/Territorio")
    assert r.status_code == 409
    assert r.headers["X-Code-Count"] == "1"
    r2 = client.delete("/api/domains/custom/Territorio?confirm=true")
    assert r2.status_code == 200 and r2.json()["in_use"] == 1
    # el código sobrevive, huérfano de color pero con su nombre de dominio intacto
    codes = client.get("/api/project").json()["codes"]
    assert codes[0]["domain"] == "Territorio"


def test_delete_unknown_custom_domain(client):
    assert client.delete("/api/domains/custom/NoExiste").status_code == 404


def test_custom_domains_isolated_per_project(client):
    original = client.get("/api/project").json()["id"]
    client.post("/api/domains/custom", json={"name": "Territorio", "color": "#AABBCC"})
    other = client.post("/api/projects", json={"name": "Otro proyecto"}).json()
    assert client.get("/api/domains").json()["custom"] == {}  # el nuevo proyecto no lo hereda
    client.post(f"/api/projects/{original}/activate")
    assert client.get("/api/domains").json()["custom"] == {"Territorio": "#AABBCC"}  # persistió
