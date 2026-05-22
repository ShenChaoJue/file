from pathlib import Path


def login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})


def test_files_require_auth(client):
    response = client.get("/api/files", params={"path": "/"})
    assert response.status_code == 401


def test_list_root_returns_entries(client, test_env: Path):
    (test_env / "Documents").mkdir()
    (test_env / "notes.txt").write_text("hello", encoding="utf-8")
    login(client)
    response = client.get("/api/files", params={"path": "/"})
    assert response.status_code == 200
    names = [entry["name"] for entry in response.json()["entries"]]
    assert names == ["Documents", "notes.txt"]


def test_create_rename_move_copy_delete_flow(client, test_env: Path):
    login(client)
    assert client.post("/api/files/folders", json={"path": "/Projects"}).status_code == 200
    (test_env / "a.txt").write_text("a", encoding="utf-8")
    rename = client.post("/api/files/rename", json={"path": "/a.txt", "new_name": "b.txt"})
    assert rename.status_code == 200
    move = client.post("/api/files/move", json={"sources": ["/b.txt"], "target_dir": "/Projects"})
    assert move.status_code == 200
    copy = client.post("/api/files/copy", json={"sources": ["/Projects/b.txt"], "target_dir": "/"})
    assert copy.status_code == 200
    delete = client.delete("/api/files", params={"path": "/b.txt"})
    assert delete.status_code == 200
    assert not (test_env / "b.txt").exists()


def test_upload_conflict_returns_409(client, test_env: Path):
    (test_env / "same.txt").write_text("old", encoding="utf-8")
    login(client)
    response = client.post(
        "/api/files/upload",
        data={"path": "/"},
        files={"file": ("same.txt", b"new", "text/plain")},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "target_exists"


def test_download_file(client, test_env: Path):
    (test_env / "download.txt").write_text("content", encoding="utf-8")
    login(client)
    response = client.get("/api/files/download", params={"path": "/download.txt"})
    assert response.status_code == 200
    assert response.content == b"content"
