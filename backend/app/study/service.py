import random
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.core.exceptions import ConflictError, NotFoundError
from app.courses.service import get_course_for_user
from app.reviews.answers import is_correct
from app.reviews.models import Exercise, Review, ReviewMode
from app.reviews.scheduler import next_schedule, start_learning
from app.study.exercises import build_exercises
from app.study.schemas import LearnExercise, StudyCounts

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
    card = _get_active_card(db, course_id, card_id)
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


def get_learn_round(
    db: Session, user_id: int, course_id: int, rng: random.Random
) -> tuple[list[Card], list[LearnExercise]]:
    get_course_for_user(db, user_id, course_id)
    active = select(Card).where(Card.course_id == course_id, Card.is_active.is_(True))
    cards = list(
        db.scalars(
            active.where(Card.learning_step.is_(None))
            .order_by(Card.excel_id)
            .limit(SESSION_SIZE)
        )
    )
    pool = list(db.scalars(active))
    return cards, build_exercises(cards, pool, rng)


def submit_learn_answer(
    db: Session,
    user_id: int,
    course_id: int,
    card_id: int,
    exercise: Exercise,
    answer: str,
    now: datetime,
) -> tuple[Card, bool, bool]:
    get_course_for_user(db, user_id, course_id)
    card = _get_active_card(db, course_id, card_id)
    if card.learning_step is not None:
        raise ConflictError("Card is already learned")

    expected = (
        card.translation if exercise == Exercise.CHOOSE_TRANSLATION else card.word
    )
    correct = is_correct(answer, expected)
    review = Review(
        card_id=card.id,
        mode=ReviewMode.LEARN,
        exercise=exercise,
        correct=correct,
        answer=answer,
        step_before=None,
        step_after=None,
        reviewed_at=now,
    )
    db.add(review)
    db.flush()

    learned = correct and _has_passed_every_exercise(db, card.id)
    if learned:
        schedule = start_learning(now)
        card.learning_step = schedule.step
        card.recovery_target = schedule.recovery_target
        card.due_at = schedule.due_at
        card.last_reviewed_at = now
        review.step_after = schedule.step

    db.commit()
    return card, correct, learned


def _get_active_card(db: Session, course_id: int, card_id: int) -> Card:
    card = db.scalar(
        select(Card).where(
            Card.id == card_id, Card.course_id == course_id, Card.is_active.is_(True)
        )
    )
    if card is None:
        raise NotFoundError(f"Card {card_id} not found")
    return card


def _has_passed_every_exercise(db: Session, card_id: int) -> bool:
    passed = db.scalars(
        select(Review.exercise)
        .where(
            Review.card_id == card_id,
            Review.mode == ReviewMode.LEARN,
            Review.correct.is_(True),
        )
        .distinct()
    )
    return {Exercise(value) for value in passed} == set(Exercise)
