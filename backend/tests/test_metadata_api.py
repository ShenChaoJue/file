def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_favorites_crud(client):
    login(client)
    add = client.post("/api/metadata/favorites", json={"path": "/Photos"})
    assert add.status_code == 200
    assert client.get("/api/metadata/favorites").json() == [{"path": "/Photos"}]
    delete = client.delete("/api/metadata/favorites", params={"path": "/Photos"})
    assert delete.status_code == 200
    assert client.get("/api/metadata/favorites").json() == []


def test_preferences_round_trip(client):
    login(client)
    response = client.put("/api/metadata/preferences", json={"key": "viewMode", "value": "icon"})
    assert response.status_code == 200
    prefs = client.get("/api/metadata/preferences").json()
    assert prefs == {"viewMode": "icon"}


def test_recent_paths_returns_latest_first(client):
    login(client)
    client.post("/api/metadata/recent", json={"path": "/A"})
    client.post("/api/metadata/recent", json={"path": "/B"})
    assert client.get("/api/metadata/recent").json() == [{"path": "/B"}, {"path": "/A"}]
