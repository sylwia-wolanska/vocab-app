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


def create_course(client: TestClient, name: str = "German B1") -> int:
    response = client.post(
        "/api/v1/courses",
        json={"name": name, "source_language": "de", "target_language": "pl"},
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
