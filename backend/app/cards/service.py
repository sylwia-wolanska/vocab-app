from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.courses.service import get_course


def list_cards(
    db: Session,
    course_id: int,
    *,
    search: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Card], int]:
    get_course(db, course_id)

    query = select(Card).where(Card.course_id == course_id)
    if not include_inactive:
        query = query.where(Card.is_active.is_(True))
    if search:
        query = query.where(
            or_(
                Card.word.icontains(search, autoescape=True),
                Card.translation.icontains(search, autoescape=True),
                Card.description.icontains(search, autoescape=True),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    cards = db.scalars(query.order_by(Card.excel_id).limit(limit).offset(offset)).all()
    return list(cards), total
