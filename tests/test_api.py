from fastapi.testclient import TestClient
from sqlalchemy import text
from app.backend.main import create_app


def test_health_capabilities_and_no_publish_endpoint(database):
    _, directory, _ = database
    with TestClient(create_app(directory)) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["publishing_enabled"] is False
        platforms = client.get("/api/platforms").json()
        assert len(platforms) == 6
        assert all(p["publishing"] == "unsupported" for p in platforms)
        assert client.post("/api/publish", json={}).status_code == 404
        assert client.get("/api/health", headers={"Host": "attacker.example"}).status_code == 400


def test_missing_database_or_wrong_migration_is_not_healthy(database, tmp_path):
    engine, directory, _ = database
    with engine.begin() as c:
        c.execute(text("UPDATE alembic_version SET version_num='wrong'"))
    with TestClient(create_app(directory)) as client:
        assert client.get("/api/health").status_code == 503
    with TestClient(create_app(tmp_path / "not-created")) as client:
        assert client.get("/api/health").status_code == 503
