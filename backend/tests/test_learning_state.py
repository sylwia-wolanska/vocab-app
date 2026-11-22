import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.reviews.models import Exercise, Review, ReviewMode
from tests.factories import create_course, upload


def create_card(client: TestClient, db_session: Session) -> Card:
    course_id = create_course(client)
    upload(client, course_id, [[1, "der Hund", "the dog", None]])
    return db_session.scalars(select(Card)).one()


def test_imported_cards_start_unlearned(
    db_client: TestClient, db_session: Session
) -> None:
    card = create_card(db_client, db_session)

    assert card.learning_step is None
    assert card.recovery_target is None
    assert card.due_at is None
    assert card.mistake_count == 0


@pytest.mark.parametrize("mode", list(ReviewMode))
@pytest.mark.parametrize("exercise", list(Exercise))
def test_database_accepts_every_enum_value(
    db_client: TestClient, db_session: Session, mode: ReviewMode, exercise: Exercise
) -> None:
    card = create_card(db_client, db_session)

    db_session.add(
        Review(
            card_id=card.id,
            mode=mode,
            exercise=exercise,
            correct=True,
            answer="der Hund",
        )
    )
    db_session.commit()

    assert db_session.scalars(select(Review)).one().reviewed_at is not None


def test_database_rejects_unknown_mode(
    db_client: TestClient, db_session: Session
) -> None:
    card = create_card(db_client, db_session)

    db_session.add(
        Review(
            card_id=card.id,
            mode="sleep",
            exercise="type_word",
            correct=True,
            answer="x",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
