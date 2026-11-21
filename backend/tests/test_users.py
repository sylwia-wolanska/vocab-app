import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.security import hash_password, verify_password
from app.users import service

PASSWORD = "correct horse battery"


def test_hash_is_not_the_password_and_verifies() -> None:
    hashed = hash_password(PASSWORD)

    assert hashed != PASSWORD
    assert hashed.startswith("$argon2id$")
    assert verify_password(PASSWORD, hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_same_password_gives_different_hashes() -> None:
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_create_user_stores_lowercase_email_and_hash(db_session: Session) -> None:
    user = service.create_user(db_session, "  Sylwia@Example.COM ", PASSWORD)

    assert user.id > 0
    assert user.email == "sylwia@example.com"
    assert user.hashed_password != PASSWORD
    assert user.is_active is True


def test_create_user_with_existing_email_in_other_case_raises_conflict(
    db_session: Session,
) -> None:
    service.create_user(db_session, "sylwia@example.com", PASSWORD)

    with pytest.raises(ConflictError):
        service.create_user(db_session, "SYLWIA@example.com", "another password")


def test_authenticate_returns_user_for_correct_password(db_session: Session) -> None:
    created = service.create_user(db_session, "sylwia@example.com", PASSWORD)

    user = service.authenticate(db_session, "Sylwia@Example.com", PASSWORD)

    assert user is not None
    assert user.id == created.id


def test_authenticate_returns_none_for_wrong_password(db_session: Session) -> None:
    service.create_user(db_session, "sylwia@example.com", PASSWORD)

    assert (
        service.authenticate(db_session, "sylwia@example.com", "wrong password") is None
    )


def test_authenticate_returns_none_for_unknown_email(db_session: Session) -> None:
    assert service.authenticate(db_session, "nobody@example.com", PASSWORD) is None


def test_authenticate_returns_none_for_inactive_user(db_session: Session) -> None:
    user = service.create_user(db_session, "sylwia@example.com", PASSWORD)
    user.is_active = False
    db_session.commit()

    assert service.authenticate(db_session, "sylwia@example.com", PASSWORD) is None
