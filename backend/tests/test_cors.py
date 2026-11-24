from fastapi.testclient import TestClient

PREFLIGHT = {"Access-Control-Request-Method": "GET"}


def test_cors_allows_the_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health", headers={"Origin": "http://localhost:5173", **PREFLIGHT}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_does_not_allow_other_origins(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health", headers={"Origin": "https://evil.example", **PREFLIGHT}
    )

    assert "access-control-allow-origin" not in response.headers
