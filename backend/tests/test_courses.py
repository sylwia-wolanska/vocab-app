from fastapi.testclient import TestClient

URL = "/api/v1/courses"
GERMAN = {"name": "German B1", "source_language": "de", "target_language": "pl"}
SPANISH = {"name": "Spanish A2", "source_language": "es", "target_language": "pl"}


def test_create_course_returns_201_with_course(db_client: TestClient) -> None:
    response = db_client.post(URL, json=GERMAN)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "German B1"
    assert body["source_language"] == "de"
    assert body["id"] > 0
    assert body["created_at"] is not None


def test_create_course_with_duplicate_name_returns_409(db_client: TestClient) -> None:
    db_client.post(URL, json=GERMAN)

    response = db_client.post(URL, json=GERMAN)

    assert response.status_code == 409
    assert response.json() == {"detail": "Course 'German B1' already exists"}


def test_create_course_with_empty_name_returns_422(db_client: TestClient) -> None:
    response = db_client.post(URL, json={**GERMAN, "name": ""})

    assert response.status_code == 422


def test_list_courses_returns_courses_sorted_by_name(db_client: TestClient) -> None:
    db_client.post(URL, json=SPANISH)
    db_client.post(URL, json=GERMAN)

    response = db_client.get(URL)

    assert response.status_code == 200
    assert [course["name"] for course in response.json()] == ["German B1", "Spanish A2"]


def test_get_course_returns_course(db_client: TestClient) -> None:
    course_id = db_client.post(URL, json=GERMAN).json()["id"]

    response = db_client.get(f"{URL}/{course_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "German B1"


def test_get_missing_course_returns_404(db_client: TestClient) -> None:
    response = db_client.get(f"{URL}/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Course 999999 not found"}
