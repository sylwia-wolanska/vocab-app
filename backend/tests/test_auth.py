import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.users.models import User
from tests.factories import auth_headers

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


TOKEN_URL = "/api/v1/auth/token"
ME_URL = "/api/v1/auth/me"


def register_and_login(client: TestClient, password: str = PASSWORD) -> TestClient:
    client.post(
        REGISTER_URL, json={"email": "sylwia@example.com", "password": PASSWORD}
    )
    return client


def test_login_returns_bearer_token(db_client: TestClient) -> None:
    register_and_login(db_client)

    response = db_client.post(
        TOKEN_URL, data={"username": "Sylwia@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2


def test_login_with_wrong_password_returns_401(db_client: TestClient) -> None:
    register_and_login(db_client)

    response = db_client.post(
        TOKEN_URL, data={"username": "sylwia@example.com", "password": "wrong password"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_with_unknown_email_returns_same_401(db_client: TestClient) -> None:
    response = db_client.post(
        TOKEN_URL, data={"username": "nobody@example.com", "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_me_returns_current_user(db_client: TestClient) -> None:
    headers = auth_headers(db_client)

    response = db_client.get(ME_URL, headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "sylwia@example.com"


def test_me_without_token_returns_401(db_client: TestClient) -> None:
    response = db_client.get(ME_URL)

    assert response.status_code == 401


def test_me_with_tampered_token_returns_401(db_client: TestClient) -> None:
    headers = auth_headers(db_client)
    tampered = {"Authorization": headers["Authorization"][:-2] + "xx"}

    response = db_client.get(ME_URL, headers=tampered)

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_me_with_expired_token_returns_401(
    db_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    auth_headers(db_client)
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    user_id = db_client.post(
        TOKEN_URL, data={"username": "sylwia@example.com", "password": PASSWORD}
    ).json()["access_token"]
    assert user_id

    response = db_client.get(ME_URL, headers={"Authorization": f"Bearer {user_id}"})

    assert response.status_code == 401


def test_token_for_unknown_user_returns_401(db_client: TestClient) -> None:
    token = create_access_token("999999")

    response = db_client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
