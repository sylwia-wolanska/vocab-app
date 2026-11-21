from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.courses.service import get_course
from app.imports.parser import parse_workbook
from app.imports.schemas import ImportSummary


def import_file(db: Session, course_id: int, content: bytes) -> ImportSummary:
    get_course(db, course_id)
    rows = parse_workbook(content)

    existing_ids = set(
        db.scalars(select(Card.excel_id).where(Card.course_id == course_id))
    )
    new_cards = [
        Card(
            course_id=course_id,
            excel_id=row.excel_id,
            word=row.word,
            translation=row.translation,
            description=row.description,
        )
        for row in rows
        if row.excel_id not in existing_ids
    ]

    db.add_all(new_cards)
    db.commit()
    return ImportSummary(
        added=len(new_cards), already_present=len(rows) - len(new_cards)
    )
