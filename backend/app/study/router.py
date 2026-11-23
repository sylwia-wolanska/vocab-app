import random

from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.core.clock import Now
from app.db.session import DbSession
from app.study import service
from app.study.schemas import (
    AnswerResult,
    AnswerSubmit,
    CharacterSet,
    FlashCard,
    LearnAnswerResult,
    LearnAnswerSubmit,
    LearnRound,
    StudyCounts,
)

router = APIRouter(prefix="/courses/{course_id}/study", tags=["study"])


@router.get("")
def get_study_counts(
    course_id: int, user: CurrentUser, db: DbSession, now: Now
) -> StudyCounts:
    return service.get_counts(db, user.id, course_id, now)


@router.get("/revise")
def get_revise_round(
    course_id: int, user: CurrentUser, db: DbSession, now: Now
) -> list[FlashCard]:
    cards = service.get_revise_round(db, user.id, course_id, now)
    return [FlashCard.model_validate(card) for card in cards]


@router.post("/revise/{card_id}")
def submit_revise_answer(
    course_id: int,
    card_id: int,
    data: AnswerSubmit,
    user: CurrentUser,
    db: DbSession,
    now: Now,
) -> AnswerResult:
    card, correct = service.submit_revise_answer(
        db, user.id, course_id, card_id, data.answer, now
    )
    assert card.learning_step is not None and card.due_at is not None
    return AnswerResult(
        correct=correct,
        card=FlashCard.model_validate(card),
        step=card.learning_step,
        due_at=card.due_at,
    )


@router.get("/learn")
def get_learn_round(course_id: int, user: CurrentUser, db: DbSession) -> LearnRound:
    cards, exercises = service.get_learn_round(db, user.id, course_id, random.Random())
    return LearnRound(
        cards=[FlashCard.model_validate(card) for card in cards], exercises=exercises
    )


@router.post("/learn/{card_id}")
def submit_learn_answer(
    course_id: int,
    card_id: int,
    data: LearnAnswerSubmit,
    user: CurrentUser,
    db: DbSession,
    now: Now,
) -> LearnAnswerResult:
    card, correct, learned = service.submit_learn_answer(
        db, user.id, course_id, card_id, data.exercise, data.answer, now
    )
    return LearnAnswerResult(
        correct=correct,
        card=FlashCard.model_validate(card),
        learned=learned,
        due_at=card.due_at,
    )


@router.get("/characters")
def get_characters(course_id: int, user: CurrentUser, db: DbSession) -> CharacterSet:
    return CharacterSet(characters=service.get_characters(db, user.id, course_id))
