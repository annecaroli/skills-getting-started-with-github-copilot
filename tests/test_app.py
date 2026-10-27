import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


ACTIVITY = "Test Activity"
PARTICIPANT = "student@example.edu"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(
        activities,
        ACTIVITY,
        {
            "description": "Activity used by API tests",
            "schedule": "Mondays",
            "max_participants": 10,
            "participants": [],
        },
    )
    return TestClient(app)


def test_get_activities_returns_activity_and_disables_caching(client):
    # Arrange
    expected_participants = []

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()[ACTIVITY]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    expected_message = f"Signed up {PARTICIPANT} for {ACTIVITY}"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY}/signup",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    assert PARTICIPANT in activities[ACTIVITY]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    client.post(f"/activities/{ACTIVITY}/signup", params={"email": PARTICIPANT})

    # Act
    response = client.post(
        f"/activities/{ACTIVITY}/signup",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[ACTIVITY]["participants"].count(PARTICIPANT) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_removes_participant(client):
    # Arrange
    activities[ACTIVITY]["participants"].append(PARTICIPANT)
    expected_message = f"Unregistered {PARTICIPANT} from {ACTIVITY}"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY}/participants",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    assert PARTICIPANT not in activities[ACTIVITY]["participants"]


def test_delete_rejects_participant_not_registered(client):
    # Arrange
    expected_detail = "Student is not signed up for this activity"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY}/participants",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail


def test_delete_rejects_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/participants",
        params={"email": PARTICIPANT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
