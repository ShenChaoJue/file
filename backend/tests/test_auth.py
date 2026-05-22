def test_health_endpoint_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_structured_not_found_error(client):
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_first_start_creates_user_from_environment(client):
    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        users = db.query(User).all()
    assert len(users) == 1
    assert users[0].username == "admin"
    assert users[0].password_hash != "secret123"


def test_login_sets_http_only_session_cookie(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
    assert "session" in response.cookies


def test_me_requires_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_me_returns_user_after_login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}


def test_login_rejects_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
