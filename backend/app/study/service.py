from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.courses.service import get_course_for_user
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
