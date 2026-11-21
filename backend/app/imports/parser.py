from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.worksheet import Worksheet

from app.core.exceptions import AppError

COLUMN_TITLES = {"id": "ID", "word": "Word", "translation": "Translation"}
OPTIONAL_COLUMNS = ("description",)
MAX_TEXT_LENGTH = 255


class ExcelFormatError(AppError):
    status_code = 422


@dataclass(frozen=True)
class ExcelRow:
    excel_id: int
    word: str
    translation: str
    description: str | None


def parse_workbook(content: bytes) -> list[ExcelRow]:
    try:
        workbook = load_workbook(BytesIO(content), data_only=True)
    except (BadZipFile, InvalidFileException, KeyError, OSError) as exc:
        raise ExcelFormatError(["The file is not a valid .xlsx workbook"]) from exc

    sheet = workbook.worksheets[0]
    if not isinstance(sheet, Worksheet):
        raise ExcelFormatError(["The first sheet must be a worksheet"])

    rows = sheet.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        raise ExcelFormatError(["The first sheet is empty"])

    columns = _find_columns(header)
    return _parse_rows(rows, columns)


def _find_columns(header: tuple[object, ...]) -> dict[str, int]:
    names = [(_text(cell) or "").lower() for cell in header]
    missing = [title for key, title in COLUMN_TITLES.items() if key not in names]
    if missing:
        raise ExcelFormatError([f"Missing required columns: {', '.join(missing)}"])
    wanted = [*COLUMN_TITLES, *OPTIONAL_COLUMNS]
    return {key: names.index(key) for key in wanted if key in names}


def _parse_rows(
    rows: Iterable[tuple[object, ...]], columns: dict[str, int]
) -> list[ExcelRow]:
    parsed: list[ExcelRow] = []
    errors: list[str] = []
    seen_ids: set[int] = set()

    for row_number, row in enumerate(rows, start=2):
        if all(_text(value) is None for value in row):
            continue

        excel_id = _to_positive_int(_value(row, columns["id"]))
        word = _text(_value(row, columns["word"]))
        translation = _text(_value(row, columns["translation"]))
        description = (
            _text(_value(row, columns["description"]))
            if "description" in columns
            else None
        )

        row_errors: list[str] = []
        if excel_id is None:
            row_errors.append("ID must be a positive whole number")
        elif excel_id in seen_ids:
            row_errors.append(f"ID {excel_id} appears more than once")
        if word is None:
            row_errors.append("Word is required")
        elif len(word) > MAX_TEXT_LENGTH:
            row_errors.append(f"Word is longer than {MAX_TEXT_LENGTH} characters")
        if translation is None:
            row_errors.append("Translation is required")
        elif len(translation) > MAX_TEXT_LENGTH:
            row_errors.append(
                f"Translation is longer than {MAX_TEXT_LENGTH} characters"
            )

        if row_errors or excel_id is None or word is None or translation is None:
            errors.extend(f"Row {row_number}: {error}" for error in row_errors)
            continue

        seen_ids.add(excel_id)
        parsed.append(ExcelRow(excel_id, word, translation, description))

    if errors:
        raise ExcelFormatError(errors)
    return parsed


def _value(row: tuple[object, ...], index: int) -> object:
    return row[index] if index < len(row) else None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    elif isinstance(value, str) and value.strip().isdigit():
        number = int(value.strip())
    else:
        return None
    return number if number > 0 else None
