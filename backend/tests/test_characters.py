import pytest
from fastapi.testclient import TestClient

from app.study.characters import graphemes, special_characters
from tests.factories import auth_headers, create_course, upload

X_WITH_DOT_AND_MACRON = "x\u0323\u0304"


@pytest.mark.parametrize(
    ("words", "expected"),
    [
        (["der Hund", "müde", "die Straße", "Äpfel"], ["ß", "ä", "ü"]),
        (["dog", "cat 2", "it's ok?"], []),
        (["ḥabīb", "ʿarabī", "šams"], ["ī", "š", "ʿ", "ḥ"]),
        (["Привет"], ["в", "е", "и", "п", "р", "т"]),
        (["ねこ"], ["こ", "ね"]),
        (["mu\u0308de"], ["ü"]),
        ([f"a{X_WITH_DOT_AND_MACRON}b"], [X_WITH_DOT_AND_MACRON]),
        (["Ärger", "ärger"], ["ä"]),
        (["der\u00a0Hund"], []),
    ],
    ids=[
        "german",
        "only ascii",
        "arabic romanization",
        "cyrillic",
        "kana",
        "decomposed umlaut",
        "letter with two marks",
        "capitals deduplicated",
        "non-breaking space",
    ],
)
def test_special_characters(words: list[str], expected: list[str]) -> None:
    assert special_characters(words) == expected


def test_graphemes_keep_marks_with_their_letter() -> None:
    assert graphemes(f"a{X_WITH_DOT_AND_MACRON}b") == ["a", X_WITH_DOT_AND_MACRON, "b"]


def get_characters(client: TestClient, course_id: int) -> object:
    response = client.get(
        f"/api/v1/courses/{course_id}/study/characters", headers=auth_headers(client)
    )
    return response.json()


def test_characters_follow_the_uploaded_file(db_client: TestClient) -> None:
    course_id = create_course(db_client)

    upload(db_client, course_id, [[1, "müde", "tired"]])
    after_first = get_characters(db_client, course_id)
    upload(db_client, course_id, [[1, "müde", "tired"], [2, "die Straße", "street"]])
    after_second = get_characters(db_client, course_id)
    upload(db_client, course_id, [[2, "die Straße", "street"]])
    after_removal = get_characters(db_client, course_id)

    assert after_first == {"characters": ["ü"]}
    assert after_second == {"characters": ["ß", "ü"]}
    assert after_removal == {"characters": ["ß"]}


def test_characters_require_login(db_client: TestClient) -> None:
    course_id = create_course(db_client)

    response = db_client.get(f"/api/v1/courses/{course_id}/study/characters")

    assert response.status_code == 401


def test_characters_of_another_users_course_return_404(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    other = auth_headers(db_client, "other@example.com")

    response = db_client.get(
        f"/api/v1/courses/{course_id}/study/characters", headers=other
    )

    assert response.status_code == 404
