from collections.abc import Sequence
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cards.models import Card

HEADER = ["ID", "Word", "Translation", "Description"]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def words(count: int) -> list[list[object]]:
    return [[i, f"word {i}", f"translation {i}", None] for i in range(1, count + 1)]


def set_learned(
    db_session: Session,
    excel_id: int,
    due_at: datetime,
    *,
    step: int = 0,
    recovery_target: int | None = None,
    active: bool = True,
) -> int:
    card = db_session.scalars(select(Card).where(Card.excel_id == excel_id)).one()
    card.learning_step = step
    card.recovery_target = recovery_target
    card.due_at = due_at
    card.is_active = active
    db_session.commit()
    return card.id


def make_workbook(rows: Sequence[Sequence[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert isinstance(sheet, Worksheet)
    for row in rows:
        sheet.append(list(row))
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def create_course(
    client: TestClient, name: str = "German B1", headers: dict[str, str] | None = None
) -> int:
    response = client.post(
        "/api/v1/courses",
        json={"name": name, "source_language": "de", "target_language": "pl"},
        headers=headers or auth_headers(client),
    )
    course_id: int = response.json()["id"]
    return course_id


def upload(
    client: TestClient,
    course_id: int,
    rows: Sequence[Sequence[object]],
    *,
    dry_run: bool = False,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    response = client.post(
        f"/api/v1/courses/{course_id}/import",
        params={"dry_run": dry_run},
        files={"file": ("words.xlsx", make_workbook([HEADER, *rows]), XLSX)},
        headers=headers or auth_headers(client),
    )
    return response.status_code, response.json()


def auth_headers(
    client: TestClient,
    email: str = "sylwia@example.com",
    password: str = "correct horse battery",
) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = client.post(
        "/api/v1/auth/token", data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
