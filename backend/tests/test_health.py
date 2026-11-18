from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app


class WorkingSession:
    def execute(self, *args, **kwargs):
        return None


class BrokenSession:
    def execute(self, *args, **kwargs):
        raise SQLAlchemyError("database is down")


def test_liveness_returns_ok(client: TestClient):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ok_when_database_responds(client: TestClient):
    app.dependency_overrides[get_db] = lambda: WorkingSession()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_readiness_returns_503_when_database_is_down(client: TestClient):
    app.dependency_overrides[get_db] = lambda: BrokenSession()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
