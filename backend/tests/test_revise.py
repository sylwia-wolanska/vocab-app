from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.reviews.models import Review
from tests.factories import NOW, auth_headers, create_course, set_learned, upload, words

DOG = [1, "der Hund", "the dog", "a pet"]


def revise_url(course_id: int, card_id: int | None = None) -> str:
    url = f"/api/v1/courses/{course_id}/study/revise"
    return url if card_id is None else f"{url}/{card_id}"


def answer(
    client: TestClient, course_id: int, card_id: int, text: str
) -> tuple[int, Any]:
    response = client.post(
        revise_url(course_id, card_id),
        json={"answer": text},
        headers=auth_headers(client),
    )
    return response.status_code, response.json()


def test_round_returns_up_to_10_due_cards_most_overdue_first(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, words(13))
    for excel_id in range(1, 12):
        set_learned(db_session, excel_id, NOW - timedelta(hours=excel_id))
    set_learned(db_session, 12, NOW + timedelta(hours=1))

    response = frozen_client.get(
        revise_url(course_id), headers=auth_headers(frozen_client)
    )

    assert response.status_code == 200
    assert [card["word"] for card in response.json()] == [
        f"word {i}" for i in range(11, 1, -1)
    ]


def test_round_cards_include_prompt_and_answer(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW)

    response = frozen_client.get(
        revise_url(course_id), headers=auth_headers(frozen_client)
    )

    assert response.json() == [
        {
            "id": card_id,
            "word": "der Hund",
            "translation": "the dog",
            "description": "a pet",
        }
    ]


def test_correct_answer_moves_one_step_up_and_is_recorded(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW)

    status, body = answer(frozen_client, course_id, card_id, "  DER   hund ")

    assert status == 200
    assert (body["correct"], body["step"]) == (True, 1)
    assert datetime.fromisoformat(body["due_at"]) == NOW + timedelta(hours=8)
    review = db_session.scalars(select(Review)).one()
    assert (review.mode, review.exercise, review.correct) == (
        "revise",
        "type_word",
        True,
    )
    assert (review.step_before, review.step_after) == (0, 1)
    card = db_session.get(Card, card_id)
    assert card is not None
    assert (card.last_reviewed_at, card.mistake_count) == (NOW, 0)


def test_wrong_answer_restarts_at_4_hours_and_returns_the_flashcard(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW, step=6)

    status, body = answer(frozen_client, course_id, card_id, "die Katze")

    assert status == 200
    assert (body["correct"], body["step"]) == (False, 0)
    assert datetime.fromisoformat(body["due_at"]) == NOW + timedelta(hours=4)
    assert body["card"] == {
        "id": card_id,
        "word": "der Hund",
        "translation": "the dog",
        "description": "a pet",
    }
    card = db_session.get(Card, card_id)
    assert card is not None
    assert (card.recovery_target, card.mistake_count) == (6, 1)


def test_answering_the_same_card_twice_returns_409(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW)
    answer(frozen_client, course_id, card_id, "der Hund")

    result = answer(frozen_client, course_id, card_id, "der Hund")

    assert result == (409, {"detail": "Card is not due for revision"})


def test_card_not_due_yet_returns_409(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW + timedelta(minutes=1))

    result = answer(frozen_client, course_id, card_id, "der Hund")

    assert result == (409, {"detail": "Card is not due for revision"})


def test_card_never_learned_returns_409_and_records_nothing(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = db_session.scalars(select(Card.id)).one()

    result = answer(frozen_client, course_id, card_id, "der Hund")

    assert result == (409, {"detail": "Card is not due for revision"})
    assert db_session.scalars(select(Review)).all() == []


def test_card_from_another_course_returns_404(
    frozen_client: TestClient, db_session: Session
) -> None:
    first = create_course(frozen_client)
    upload(frozen_client, first, [DOG])
    card_id = set_learned(db_session, 1, NOW)
    second = create_course(frozen_client, name="Spanish A2")

    result = answer(frozen_client, second, card_id, "der Hund")

    assert result == (404, {"detail": f"Card {card_id} not found"})


def test_revise_requires_login(frozen_client: TestClient) -> None:
    course_id = create_course(frozen_client)

    assert frozen_client.get(revise_url(course_id)).status_code == 401
    assert (
        frozen_client.post(revise_url(course_id, 1), json={"answer": "x"}).status_code
        == 401
    )


def test_revise_on_another_users_course_returns_404_and_records_nothing(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    card_id = set_learned(db_session, 1, NOW)
    other = auth_headers(frozen_client, "other@example.com")

    round_response = frozen_client.get(revise_url(course_id), headers=other)
    answer_response = frozen_client.post(
        revise_url(course_id, card_id), json={"answer": "der Hund"}, headers=other
    )

    assert (round_response.status_code, answer_response.status_code) == (404, 404)
    assert db_session.scalars(select(Review)).all() == []
