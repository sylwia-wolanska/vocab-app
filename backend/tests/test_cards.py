from typing import Any

from fastapi.testclient import TestClient

from tests.factories import create_course, upload

DOG = [1, "der Hund", "the dog", "a pet"]
CAT = [2, "die Katze", "the cat", None]
HOUSE = [3, "das Haus", "the house", None]
SALE = [4, "der Rabatt", "10% off", None]


def get_cards(
    client: TestClient, course_id: int, **params: str | int | bool
) -> tuple[int, Any]:
    response = client.get(f"/api/v1/courses/{course_id}/cards", params=params)
    return response.status_code, response.json()


def words(body: Any) -> list[str]:
    return [item["word"] for item in body["items"]]


def test_lists_active_cards_in_excel_order(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [SALE, HOUSE, CAT, DOG])

    status, body = get_cards(db_client, course_id)

    assert status == 200
    assert words(body) == ["der Hund", "die Katze", "das Haus", "der Rabatt"]
    assert (body["total"], body["limit"], body["offset"]) == (4, 50, 0)


def test_hides_inactive_cards_unless_requested(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT, HOUSE, SALE])
    upload(db_client, course_id, [DOG, CAT, HOUSE])

    _, active = get_cards(db_client, course_id)
    _, everything = get_cards(db_client, course_id, include_inactive=True)

    assert active["total"] == 3
    assert everything["total"] == 4
    assert everything["items"][-1]["is_active"] is False


def test_search_matches_word_translation_and_description(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT, HOUSE, SALE])

    assert words(get_cards(db_client, course_id, search="HUND")[1]) == ["der Hund"]
    assert words(get_cards(db_client, course_id, search="cat")[1]) == ["die Katze"]
    assert words(get_cards(db_client, course_id, search="pet")[1]) == ["der Hund"]


def test_search_treats_percent_as_text(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT, HOUSE, SALE])

    _, body = get_cards(db_client, course_id, search="%")

    assert words(body) == ["der Rabatt"]


def test_paginates_and_reports_total(db_client: TestClient) -> None:
    course_id = create_course(db_client)
    upload(db_client, course_id, [DOG, CAT, HOUSE, SALE])

    _, body = get_cards(db_client, course_id, limit=2, offset=1)

    assert words(body) == ["die Katze", "das Haus"]
    assert body["total"] == 4


def test_limit_out_of_range_returns_422(db_client: TestClient) -> None:
    course_id = create_course(db_client)

    status, _ = get_cards(db_client, course_id, limit=0)

    assert status == 422


def test_missing_course_returns_404(db_client: TestClient) -> None:
    status, body = get_cards(db_client, 999999)

    assert (status, body) == (404, {"detail": "Course 999999 not found"})
