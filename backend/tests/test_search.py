from pathlib import Path


def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_search_from_current_directory_by_name(client, test_env: Path):
    (test_env / "photos").mkdir()
    (test_env / "photos" / "cat.jpg").write_bytes(b"cat")
    (test_env / "notes.txt").write_text("cat inside content does not count", encoding="utf-8")
    login(client)
    response = client.get("/api/files/search", params={"path": "/photos", "q": "cat"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["base_path"] == "/photos"
    assert [entry["path"] for entry in payload["entries"]] == ["/photos/cat.jpg"]
