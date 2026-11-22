from fastapi.testclient import TestClient

from tests.factories import auth_headers

URL = "/api/v1/courses"
GERMAN = {"name": "German B1", "source_language": "de", "target_language": "pl"}
SPANISH = {"name": "Spanish A2", "source_language": "es", "target_language": "pl"}


def test_create_course_returns_201_with_course(db_client: TestClient) -> None:
    headers = auth_headers(db_client)

    response = db_client.post(URL, json=GERMAN, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "German B1"
    assert body["id"] > 0


def test_create_course_with_duplicate_name_returns_409(db_client: TestClient) -> None:
    headers = auth_headers(db_client)
    db_client.post(URL, json=GERMAN, headers=headers)

    response = db_client.post(URL, json=GERMAN, headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Course 'German B1' already exists"}


def test_create_course_with_empty_name_returns_422(db_client: TestClient) -> None:
    headers = auth_headers(db_client)

    response = db_client.post(URL, json={**GERMAN, "name": ""}, headers=headers)

    assert response.status_code == 422


def test_list_courses_returns_own_courses_sorted_by_name(db_client: TestClient) -> None:
    headers = auth_headers(db_client)
    db_client.post(URL, json=SPANISH, headers=headers)
    db_client.post(URL, json=GERMAN, headers=headers)

    response = db_client.get(URL, headers=headers)

    assert [course["name"] for course in response.json()] == ["German B1", "Spanish A2"]


def test_get_course_returns_course(db_client: TestClient) -> None:
    headers = auth_headers(db_client)
    course_id = db_client.post(URL, json=GERMAN, headers=headers).json()["id"]

    response = db_client.get(f"{URL}/{course_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "German B1"


def test_get_missing_course_returns_404(db_client: TestClient) -> None:
    headers = auth_headers(db_client)

    response = db_client.get(f"{URL}/999999", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Course 999999 not found"}


def test_courses_require_login(db_client: TestClient) -> None:
    assert db_client.get(URL).status_code == 401
    assert db_client.post(URL, json=GERMAN).status_code == 401
    assert db_client.get(f"{URL}/1").status_code == 401


def test_users_see_only_their_own_courses(db_client: TestClient) -> None:
    owner = auth_headers(db_client, "owner@example.com")
    other = auth_headers(db_client, "other@example.com")
    course_id = db_client.post(URL, json=GERMAN, headers=owner).json()["id"]

    other_list = db_client.get(URL, headers=other)
    other_get = db_client.get(f"{URL}/{course_id}", headers=other)

    assert other_list.json() == []
    assert other_get.status_code == 404


def test_different_users_can_use_the_same_course_name(db_client: TestClient) -> None:
    owner = auth_headers(db_client, "owner@example.com")
    other = auth_headers(db_client, "other@example.com")

    first = db_client.post(URL, json=GERMAN, headers=owner)
    second = db_client.post(URL, json=GERMAN, headers=other)

    assert (first.status_code, second.status_code) == (201, 201)
