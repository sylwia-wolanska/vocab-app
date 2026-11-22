from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.core.clock import utc_now
from app.main import app
from tests.factories import auth_headers, create_course, upload

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def client(db_client: TestClient) -> TestClient:
    app.dependency_overrides[utc_now] = lambda: NOW
    return db_client


def words(count: int) -> list[list[object]]:
    return [[i, f"word {i}", f"translation {i}", None] for i in range(1, count + 1)]


def set_state(
    db_session: Session, excel_id: int, due_at: datetime, *, active: bool = True
) -> None:
    card = db_session.scalars(select(Card).where(Card.excel_id == excel_id)).one()
    card.learning_step = 0
    card.due_at = due_at
    card.is_active = active
    db_session.commit()


def get_counts(client: TestClient, course_id: int) -> object:
    response = client.get(
        f"/api/v1/courses/{course_id}/study", headers=auth_headers(client)
    )
    return response.json()


def test_new_course_has_nothing_due_and_all_words_new(client: TestClient) -> None:
    course_id = create_course(client)
    upload(client, course_id, words(3))

    assert get_counts(client, course_id) == {"due": 0, "learn_new": 3, "new_total": 3}


def test_learn_new_is_capped_at_10(client: TestClient) -> None:
    course_id = create_course(client)
    upload(client, course_id, words(12))

    assert get_counts(client, course_id) == {"due": 0, "learn_new": 10, "new_total": 12}


def test_due_counts_active_learned_cards_due_now_or_earlier(
    client: TestClient, db_session: Session
) -> None:
    course_id = create_course(client)
    upload(client, course_id, words(5))
    set_state(db_session, 1, NOW - timedelta(days=1))
    set_state(db_session, 2, NOW)
    set_state(db_session, 3, NOW + timedelta(minutes=1))
    set_state(db_session, 4, NOW - timedelta(days=1), active=False)

    assert get_counts(client, course_id) == {"due": 2, "learn_new": 1, "new_total": 1}


def test_study_counts_require_login(client: TestClient) -> None:
    course_id = create_course(client)

    response = client.get(f"/api/v1/courses/{course_id}/study")

    assert response.status_code == 401


def test_study_counts_of_another_users_course_return_404(client: TestClient) -> None:
    course_id = create_course(client)
    other = auth_headers(client, "other@example.com")

    response = client.get(f"/api/v1/courses/{course_id}/study", headers=other)

    assert response.status_code == 404
