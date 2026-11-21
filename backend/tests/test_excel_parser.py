import pytest

from app.imports.parser import ExcelFormatError, ExcelRow, parse_workbook
from tests.factories import HEADER, make_workbook


def test_parses_valid_rows() -> None:
    content = make_workbook(
        [
            HEADER,
            [1, "der Hund", "the dog", None],
            [2, "Feierabend", "end of the workday", "time after work"],
        ]
    )

    rows = parse_workbook(content)

    assert rows == [
        ExcelRow(1, "der Hund", "the dog", None),
        ExcelRow(2, "Feierabend", "end of the workday", "time after work"),
    ]


def test_skips_empty_rows() -> None:
    content = make_workbook(
        [HEADER, [1, "der Hund", "the dog"], [None, None, None], ["", " "]]
    )

    rows = parse_workbook(content)

    assert [row.excel_id for row in rows] == [1]


def test_accepts_columns_in_any_order_and_case_without_description() -> None:
    content = make_workbook(
        [["translation", "ID", "WORD"], ["the cat", 3.0, "die Katze"]]
    )

    rows = parse_workbook(content)

    assert rows == [ExcelRow(3, "die Katze", "the cat", None)]


def test_rejects_missing_required_columns() -> None:
    content = make_workbook([["ID", "Word"], [1, "der Hund"]])

    with pytest.raises(ExcelFormatError) as error:
        parse_workbook(content)

    assert error.value.detail == ["Missing required columns: Translation"]


def test_collects_all_row_errors() -> None:
    content = make_workbook(
        [
            HEADER,
            [1, "der Hund", None],
            ["abc", "die Katze", "the cat"],
            [4, None, "the tree"],
        ]
    )

    with pytest.raises(ExcelFormatError) as error:
        parse_workbook(content)

    assert error.value.detail == [
        "Row 2: Translation is required",
        "Row 3: ID must be a positive whole number",
        "Row 4: Word is required",
    ]


def test_rejects_duplicate_ids() -> None:
    content = make_workbook(
        [HEADER, [1, "der Hund", "the dog"], [1, "das Haus", "the house"]]
    )

    with pytest.raises(ExcelFormatError) as error:
        parse_workbook(content)

    assert error.value.detail == ["Row 3: ID 1 appears more than once"]


def test_rejects_a_file_that_is_not_xlsx() -> None:
    with pytest.raises(ExcelFormatError) as error:
        parse_workbook(b"this is not an excel file")

    assert error.value.detail == ["The file is not a valid .xlsx workbook"]
