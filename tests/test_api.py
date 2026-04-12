import pytest
from fastapi.testclient import TestClient
from app.main import app, messages

@pytest.fixture(autouse=True)
def clear_messages():
    """Her testten önce in-memory store'u temizle."""
    messages.clear()
    yield
    messages.clear()

client = TestClient(app)


def test_post_message():
    resp = client.post("/messages", json={"id": "1", "nickname": "ali", "message": "merhaba"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "1"
    assert data["nickname"] == "ali"
    assert data["message"] == "merhaba"


def test_list_messages_empty():
    resp = client.get("/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_messages_after_post():
    client.post("/messages", json={"id": "1", "nickname": "ali", "message": "merhaba"})
    client.post("/messages", json={"id": "2", "nickname": "veli", "message": "selam"})
    resp = client.get("/messages")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_info_defaults(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("BUILD_SHA", raising=False)
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert "version" in body
    assert "environment" in body
    assert "build_sha" in body


def test_info_env_vars(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("BUILD_SHA", "abc123")
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.2.3"
    assert body["environment"] == "test"
    assert body["build_sha"] == "abc123"


def test_openapi_accessible():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "openapi" in resp.json()


def test_docs_accessible():
    resp = client.get("/docs")
    assert resp.status_code == 200
