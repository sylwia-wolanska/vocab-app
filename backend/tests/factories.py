from collections.abc import Sequence
from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

HEADER = ["ID", "Word", "Translation", "Description"]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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
