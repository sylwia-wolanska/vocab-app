from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.core.exceptions import ConflictError, NotFoundError
from app.courses.service import get_course_for_user
from app.reviews.answers import is_correct
from app.reviews.models import Exercise, Review, ReviewMode
from app.reviews.scheduler import next_schedule
from app.study.schemas import StudyCounts

SESSION_SIZE = 10


def get_counts(db: Session, user_id: int, course_id: int, now: datetime) -> StudyCounts:
    get_course_for_user(db, user_id, course_id)

    active_cards = (
        select(func.count())
        .select_from(Card)
        .where(Card.course_id == course_id, Card.is_active.is_(True))
    )
    due = db.scalar(
        active_cards.where(Card.learning_step.is_not(None), Card.due_at <= now)
    )
    new_total = db.scalar(active_cards.where(Card.learning_step.is_(None)))

    return StudyCounts(
        due=due or 0,
        learn_new=min(SESSION_SIZE, new_total or 0),
        new_total=new_total or 0,
    )


def get_revise_round(
    db: Session, user_id: int, course_id: int, now: datetime
) -> list[Card]:
    get_course_for_user(db, user_id, course_id)
    query = (
        select(Card)
        .where(
            Card.course_id == course_id,
            Card.is_active.is_(True),
            Card.learning_step.is_not(None),
            Card.due_at <= now,
        )
        .order_by(Card.due_at, Card.id)
        .limit(SESSION_SIZE)
    )
    return list(db.scalars(query))


def submit_revise_answer(
    db: Session, user_id: int, course_id: int, card_id: int, answer: str, now: datetime
) -> tuple[Card, bool]:
    get_course_for_user(db, user_id, course_id)
    card = db.scalar(
        select(Card).where(
            Card.id == card_id, Card.course_id == course_id, Card.is_active.is_(True)
        )
    )
    if card is None:
        raise NotFoundError(f"Card {card_id} not found")
    if card.learning_step is None or card.due_at is None or card.due_at > now:
        raise ConflictError("Card is not due for revision")

    correct = is_correct(answer, card.word)
    step_before = card.learning_step
    schedule = next_schedule(
        card.learning_step, card.recovery_target, correct=correct, now=now
    )

    card.learning_step = schedule.step
    card.recovery_target = schedule.recovery_target
    card.due_at = schedule.due_at
    card.last_reviewed_at = now
    if not correct:
        card.mistake_count += 1

    db.add(
        Review(
            card_id=card.id,
            mode=ReviewMode.REVISE,
            exercise=Exercise.TYPE_WORD,
            correct=correct,
            answer=answer,
            step_before=step_before,
            step_after=schedule.step,
            reviewed_at=now,
        )
    )
    db.commit()
    return card, correct
