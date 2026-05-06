import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.db.models import Base
from backend.db.database import get_db


@pytest.fixture(scope="module")
def client():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from backend.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_session(client):
    resp = client.post("/api/sessions", json={"title": "Test Chat"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Test Chat"
    assert "id" in resp.json()


def test_list_sessions(client):
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rename_session(client):
    create = client.post("/api/sessions", json={"title": "Old"})
    sid = create.json()["id"]
    resp = client.put(f"/api/sessions/{sid}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


def test_delete_session(client):
    create = client.post("/api/sessions", json={"title": "ToDelete"})
    sid = create.json()["id"]
    resp = client.delete(f"/api/sessions/{sid}")
    assert resp.status_code == 204


def test_get_messages(client):
    create = client.post("/api/sessions", json={"title": "Msg Test"})
    sid = create.json()["id"]
    resp = client.get(f"/api/sessions/{sid}/messages")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
