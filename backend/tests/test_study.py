from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import NOW, auth_headers, create_course, set_learned, upload, words


def get_counts(client: TestClient, course_id: int) -> object:
    response = client.get(
        f"/api/v1/courses/{course_id}/study", headers=auth_headers(client)
    )
    return response.json()


def test_new_course_has_nothing_due_and_all_words_new(
    frozen_client: TestClient,
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, words(3))

    assert get_counts(frozen_client, course_id) == {
        "due": 0,
        "learn_new": 3,
        "new_total": 3,
    }


def test_learn_new_is_capped_at_10(frozen_client: TestClient) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, words(12))

    assert get_counts(frozen_client, course_id) == {
        "due": 0,
        "learn_new": 10,
        "new_total": 12,
    }


def test_due_counts_active_learned_cards_due_now_or_earlier(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, words(5))
    set_learned(db_session, 1, NOW - timedelta(days=1))
    set_learned(db_session, 2, NOW)
    set_learned(db_session, 3, NOW + timedelta(minutes=1))
    set_learned(db_session, 4, NOW - timedelta(days=1), active=False)

    assert get_counts(frozen_client, course_id) == {
        "due": 2,
        "learn_new": 1,
        "new_total": 1,
    }


def test_study_counts_require_login(frozen_client: TestClient) -> None:
    course_id = create_course(frozen_client)

    response = frozen_client.get(f"/api/v1/courses/{course_id}/study")

    assert response.status_code == 401


def test_study_counts_of_another_users_course_return_404(
    frozen_client: TestClient,
) -> None:
    course_id = create_course(frozen_client)
    other = auth_headers(frozen_client, "other@example.com")

    response = frozen_client.get(f"/api/v1/courses/{course_id}/study", headers=other)

    assert response.status_code == 404
