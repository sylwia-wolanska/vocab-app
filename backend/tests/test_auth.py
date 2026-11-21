from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User

REGISTER_URL = "/api/v1/auth/register"
PASSWORD = "correct horse battery"


def test_register_returns_201_without_password(db_client: TestClient) -> None:
    response = db_client.post(
        REGISTER_URL, json={"email": "Sylwia@Example.com", "password": PASSWORD}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "sylwia@example.com"
    assert body["is_active"] is True
    assert set(body) == {"id", "email", "is_active", "created_at"}


def test_register_stores_a_hash_not_the_password(
    db_client: TestClient, db_session: Session
) -> None:
    db_client.post(
        REGISTER_URL, json={"email": "sylwia@example.com", "password": PASSWORD}
    )

    user = db_session.scalars(select(User)).one()

    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("$argon2id$")


def test_register_with_existing_email_returns_409(db_client: TestClient) -> None:
    db_client.post(
        REGISTER_URL, json={"email": "sylwia@example.com", "password": PASSWORD}
    )

    response = db_client.post(
        REGISTER_URL, json={"email": "SYLWIA@example.com", "password": PASSWORD}
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


def test_register_with_invalid_email_returns_422(db_client: TestClient) -> None:
    response = db_client.post(
        REGISTER_URL, json={"email": "sylwia@", "password": PASSWORD}
    )

    assert response.status_code == 422


def test_register_with_short_password_returns_422(db_client: TestClient) -> None:
    response = db_client.post(
        REGISTER_URL, json={"email": "sylwia@example.com", "password": "short"}
    )

    assert response.status_code == 422
