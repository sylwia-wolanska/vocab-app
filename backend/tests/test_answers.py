import pytest

from app.reviews.answers import is_correct, normalize_answer

DECOMPOSED_MUEDE = "mu\u0308de"


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("der Hund", "der Hund"),
        ("  der   Hund ", "der Hund"),
        ("DER HUND", "der Hund"),
        ("der\tHund", "der Hund"),
        ("der\u00a0Hund", "der Hund"),
        ("müde", DECOMPOSED_MUEDE),
        ("der Hund", "  der Hund  "),
    ],
    ids=[
        "identical",
        "extra spaces",
        "capitals",
        "tab",
        "non-breaking space",
        "decomposed umlaut",
        "spaces in the expected word",
    ],
)
def test_accepted_answers(answer: str, expected: str) -> None:
    assert is_correct(answer, expected) is True


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("der Hunt", "der Hund"),
        ("mude", "müde"),
        ("strasse", "Straße"),
        ("derHund", "der Hund"),
        ("", "der Hund"),
        ("Wie gehts", "Wie geht's?"),
    ],
    ids=[
        "different letter",
        "missing umlaut",
        "ss instead of sharp s",
        "missing space",
        "empty answer",
        "missing punctuation",
    ],
)
def test_rejected_answers(answer: str, expected: str) -> None:
    assert is_correct(answer, expected) is False


def test_normalize_answer_trims_collapses_and_lowercases() -> None:
    assert normalize_answer("  Der \t  HUND\n") == "der hund"


def test_decomposed_umlaut_looks_equal_but_differs_before_normalizing() -> None:
    assert DECOMPOSED_MUEDE != "müde"
    assert normalize_answer(DECOMPOSED_MUEDE) == "müde"
