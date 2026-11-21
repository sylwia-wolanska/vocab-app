from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card
from tests.factories import HEADER, make_workbook

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def create_course(client: TestClient) -> int:
    response = client.post(
        "/api/v1/courses",
        json={"name": "German B1", "source_language": "de", "target_language": "pl"},
    )
    course_id: int = response.json()["id"]
    return course_id


def upload(client: TestClient, course_id: int, content: bytes) -> dict[str, object]:
    response = client.post(
        f"/api/v1/courses/{course_id}/import",
        files={"file": ("words.xlsx", content, XLSX)},
    )
    return {"status": response.status_code, "body": response.json()}


def test_import_adds_all_rows_to_an_empty_course(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    content = make_workbook(
        [HEADER, [1, "der Hund", "the dog", None], [2, "die Katze", "the cat", "a pet"]]
    )

    result = upload(db_client, course_id, content)

    assert result == {"status": 200, "body": {"added": 2, "already_present": 0}}
    cards = db_session.scalars(select(Card).order_by(Card.excel_id)).all()
    assert [(card.excel_id, card.word, card.description) for card in cards] == [
        (1, "der Hund", None),
        (2, "die Katze", "a pet"),
    ]


def test_import_again_adds_only_new_rows(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, make_workbook([HEADER, [1, "der Hund", "the dog"]]))
    content = make_workbook(
        [HEADER, [1, "der Hund", "the dog"], [2, "das Haus", "the house"]]
    )

    result = upload(db_client, course_id, content)

    assert result == {"status": 200, "body": {"added": 1, "already_present": 1}}


def test_import_with_invalid_rows_returns_422_and_adds_nothing(
    db_client: TestClient, db_session: Session
) -> None:
    course_id = create_course(db_client)
    content = make_workbook(
        [HEADER, [1, "der Hund", "the dog"], [2, "die Katze", None]]
    )

    result = upload(db_client, course_id, content)

    assert result == {
        "status": 422,
        "body": {"detail": ["Row 3: Translation is required"]},
    }
    assert db_session.scalars(select(Card)).all() == []


def test_import_to_a_missing_course_returns_404(db_client: TestClient) -> None:
    content = make_workbook([HEADER, [1, "der Hund", "the dog"]])

    result = upload(db_client, 999999, content)

    assert result == {"status": 404, "body": {"detail": "Course 999999 not found"}}
