from collections.abc import Sequence
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from tests.factories import HEADER, make_workbook

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOG = [1, "der Hund", "the dog", None]
CAT = [2, "die Katze", "the cat", None]


def create_course(client: TestClient) -> int:
    response = client.post(
        "/api/v1/courses",
        json={"name": "German B1", "source_language": "de", "target_language": "pl"},
    )
    course_id: int = response.json()["id"]
    return course_id


def upload(
    client: TestClient,
    course_id: int,
    rows: Sequence[Sequence[object]],
    *,
    dry_run: bool = False,
) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/courses/{course_id}/import",
        params={"dry_run": dry_run},
        files={"file": ("words.xlsx", make_workbook([HEADER, *rows]), XLSX)},
    )
    return response.status_code, response.json()


def summary(**counts: int) -> dict[str, int]:
    result = {
        "added": 0,
        "updated": 0,
        "unchanged": 0,
        "deactivated": 0,
        "reactivated": 0,
    }
    result.update(counts)
    return result


def cards_in_db(db_session: Session) -> list[tuple[int, str, str, bool]]:
    cards = db_session.scalars(select(Card).order_by(Card.excel_id)).all()
    return [
        (card.excel_id, card.word, card.translation, card.is_active) for card in cards
    ]


def test_first_import_adds_all_rows(db_client: TestClient, db_session: Session) -> None:
    course_id = create_course(db_client)

    result = upload(db_client, course_id, [DOG, CAT])

    assert result == (200, summary(added=2))
    assert cards_in_db(db_session) == [
        (1, "der Hund", "the dog", True),
        (2, "die Katze", "the cat", True),
    ]


def test_same_file_again_changes_nothing(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT])

    result = upload(db_client, course_id, [DOG, CAT])

    assert result == (200, summary(unchanged=2))


def test_changed_row_updates_the_same_card(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG])
    card_id = db_session.scalars(select(Card.id)).one()

    result = upload(db_client, course_id, [[1, "der Hund", "the hound", None]])

    assert result == (200, summary(updated=1))
    card = db_session.get(Card, card_id)
    assert card is not None
    assert card.translation == "the hound"


def test_removed_description_counts_as_update(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [[1, "der Hund", "the dog", "a pet"]])

    result = upload(db_client, course_id, [DOG])

    assert result == (200, summary(updated=1))
    assert db_session.scalars(select(Card.description)).one() is None


def test_row_missing_from_file_deactivates_card(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT])

    result = upload(db_client, course_id, [DOG])

    assert result == (200, summary(unchanged=1, deactivated=1))
    assert cards_in_db(db_session) == [
        (1, "der Hund", "the dog", True),
        (2, "die Katze", "the cat", False),
    ]


def test_row_back_in_file_reactivates_card(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT])
    upload(db_client, course_id, [DOG])

    result = upload(db_client, course_id, [DOG, CAT])

    assert result == (200, summary(unchanged=1, reactivated=1))
    assert [active for *_, active in cards_in_db(db_session)] == [True, True]


def test_dry_run_reports_changes_without_saving(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT])

    result = upload(
        db_client, course_id, [[1, "der Hund", "the hound", None]], dry_run=True
    )

    assert result == (200, summary(updated=1, deactivated=1))
    assert cards_in_db(db_session) == [
        (1, "der Hund", "the dog", True),
        (2, "die Katze", "the cat", True),
    ]


def test_invalid_file_returns_422_and_changes_nothing(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)

    result = upload(db_client, course_id, [DOG, [2, "die Katze", None]])

    assert result == (422, {"detail": ["Row 3: Translation is required"]})
    assert cards_in_db(db_session) == []


def test_import_to_missing_course_returns_404(db_client: TestClient) -> None:
    result = upload(db_client, 999999, [DOG])

    assert result == (404, {"detail": "Course 999999 not found"})
