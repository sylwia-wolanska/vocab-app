from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.reviews.models import Review
from tests.factories import NOW, auth_headers, create_course, set_learned, upload, words

DOG = [1, "der Hund", "the dog", "a pet"]


def learn_url(course_id: int, card_id: int | None = None) -> str:
    url = f"/api/v1/courses/{course_id}/study/learn"
    return url if card_id is None else f"{url}/{card_id}"


def answer(
    client: TestClient, course_id: int, card_id: int, exercise: str, text: str
) -> tuple[int, Any]:
    response = client.post(
        learn_url(course_id, card_id),
        json={"exercise": exercise, "answer": text},
        headers=auth_headers(client),
    )
    return response.status_code, response.json()


def card_id_of(db_session: Session, excel_id: int) -> int:
    return db_session.scalars(select(Card.id).where(Card.excel_id == excel_id)).one()


def learn_dog(frozen_client: TestClient, db_session: Session) -> tuple[int, int]:
    course_id = create_course(frozen_client)
    upload(frozen_client, course_id, [DOG])
    return course_id, card_id_of(db_session, 1)


def test_round_has_up_to_10_new_active_cards_in_excel_order(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(frozen_client)
    all_rows = words(13)
    upload(frozen_client, course_id, all_rows)
    upload(frozen_client, course_id, [row for row in all_rows if row[0] != 3])
    set_learned(db_session, 2, NOW + timedelta(days=1))

    response = frozen_client.get(
        learn_url(course_id), headers=auth_headers(frozen_client)
    )

    body = response.json()
    expected = ["word 1", *[f"word {i}" for i in range(4, 13)]]
    assert [card["word"] for card in body["cards"]] == expected
    assert len(body["exercises"]) == 30
    assert {e["card_id"] for e in body["exercises"]} == {
        card["id"] for card in body["cards"]
    }


def test_three_correct_kinds_learn_the_card(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)

    first = answer(frozen_client, course_id, card_id, "choose_word", "der Hund")
    second = answer(frozen_client, course_id, card_id, "choose_translation", "the dog")
    third = answer(frozen_client, course_id, card_id, "type_word", "  DER hund ")

    assert [result[1]["learned"] for result in (first, second, third)] == [
        False,
        False,
        True,
    ]
    assert datetime.fromisoformat(third[1]["due_at"]) == NOW + timedelta(hours=4)
    card = db_session.get(Card, card_id)
    assert card is not None
    assert (card.learning_step, card.due_at) == (0, NOW + timedelta(hours=4))
    reviews = db_session.scalars(select(Review).order_by(Review.id)).all()
    assert [(r.mode, r.correct, r.step_after) for r in reviews] == [
        ("learn", True, None),
        ("learn", True, None),
        ("learn", True, 0),
    ]


def test_wrong_answer_returns_the_flashcard_and_keeps_the_card_new(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)

    status, body = answer(frozen_client, course_id, card_id, "choose_word", "die Katze")

    assert status == 200
    assert (body["correct"], body["learned"], body["due_at"]) == (False, False, None)
    assert body["card"]["word"] == "der Hund"
    card = db_session.get(Card, card_id)
    assert card is not None
    assert (card.learning_step, card.mistake_count) == (None, 0)


def test_card_is_learned_after_a_mistake_and_a_retry(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)
    answer(frozen_client, course_id, card_id, "choose_word", "die Katze")
    answer(frozen_client, course_id, card_id, "choose_translation", "the dog")
    answer(frozen_client, course_id, card_id, "type_word", "der Hund")

    _, body = answer(frozen_client, course_id, card_id, "choose_word", "der Hund")

    assert body["learned"] is True


def test_repeating_one_kind_does_not_learn_the_card(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)
    answer(frozen_client, course_id, card_id, "choose_word", "der Hund")
    answer(frozen_client, course_id, card_id, "choose_word", "der Hund")

    _, body = answer(frozen_client, course_id, card_id, "choose_translation", "the dog")

    assert body["learned"] is False


def test_choose_translation_is_checked_against_the_translation(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)

    _, body = answer(
        frozen_client, course_id, card_id, "choose_translation", "der Hund"
    )

    assert body["correct"] is False


def test_unknown_exercise_returns_422(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)

    status, _ = answer(frozen_client, course_id, card_id, "dance", "der Hund")

    assert status == 422


def test_already_learned_card_returns_409(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)
    set_learned(db_session, 1, NOW + timedelta(hours=4))

    result = answer(frozen_client, course_id, card_id, "choose_word", "der Hund")

    assert result == (409, {"detail": "Card is already learned"})


def test_learned_card_leaves_learn_new_and_is_not_due_yet(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)
    answer(frozen_client, course_id, card_id, "choose_word", "der Hund")
    answer(frozen_client, course_id, card_id, "choose_translation", "the dog")
    answer(frozen_client, course_id, card_id, "type_word", "der Hund")

    response = frozen_client.get(
        f"/api/v1/courses/{course_id}/study", headers=auth_headers(frozen_client)
    )

    assert response.json() == {"due": 0, "learn_new": 0, "new_total": 0}


def test_learn_requires_login(frozen_client: TestClient) -> None:
    course_id = create_course(frozen_client)

    assert frozen_client.get(learn_url(course_id)).status_code == 401


def test_learn_on_another_users_course_returns_404_and_records_nothing(
    frozen_client: TestClient, db_session: Session
) -> None:
    course_id, card_id = learn_dog(frozen_client, db_session)
    other = auth_headers(frozen_client, "other@example.com")

    round_response = frozen_client.get(learn_url(course_id), headers=other)
    answer_response = frozen_client.post(
        learn_url(course_id, card_id),
        json={"exercise": "choose_word", "answer": "der Hund"},
        headers=other,
    )

    assert (round_response.status_code, answer_response.status_code) == (404, 404)
    assert db_session.scalars(select(Review)).all() == []
