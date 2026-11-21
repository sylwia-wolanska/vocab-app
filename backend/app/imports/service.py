from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from app.courses.service import get_course
from app.imports.parser import ExcelRow, parse_workbook
from app.imports.schemas import ImportSummary


def import_file(
    db: Session, course_id: int, content: bytes, *, dry_run: bool = False
) -> ImportSummary:
    get_course(db, course_id)
    rows = parse_workbook(content)

    cards = {
        card.excel_id: card
        for card in db.scalars(select(Card).where(Card.course_id == course_id))
    }
    summary = ImportSummary()

    for row in rows:
        card = cards.get(row.excel_id)
        if card is None:
            db.add(
                Card(
                    course_id=course_id,
                    excel_id=row.excel_id,
                    word=row.word,
                    translation=row.translation,
                    description=row.description,
                )
            )
            summary.added += 1
            continue

        changed = _apply_row(card, row)
        if not card.is_active:
            card.is_active = True
            summary.reactivated += 1
        elif changed:
            summary.updated += 1
        else:
            summary.unchanged += 1

    file_ids = {row.excel_id for row in rows}
    for excel_id, card in cards.items():
        if excel_id not in file_ids and card.is_active:
            card.is_active = False
            summary.deactivated += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return summary


def _apply_row(card: Card, row: ExcelRow) -> bool:
    current = (card.word, card.translation, card.description)
    incoming = (row.word, row.translation, row.description)
    if current == incoming:
        return False
    card.word, card.translation, card.description = incoming
    return True
