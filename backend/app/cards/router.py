from typing import Annotated

from fastapi import APIRouter, Query

from app.cards import service
from app.cards.schemas import CardPage, CardRead
from app.db.session import DbSession

router = APIRouter(prefix="/courses/{course_id}/cards", tags=["cards"])


@router.get("")
def list_cards(
    course_id: int,
    db: DbSession,
    search: Annotated[str | None, Query(max_length=100)] = None,
    include_inactive: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CardPage:
    term = search.strip() if search else None
    cards, total = service.list_cards(
        db,
        course_id,
        search=term or None,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    return CardPage(
        items=[CardRead.model_validate(card) for card in cards],
        total=total,
        limit=limit,
        offset=offset,
    )
