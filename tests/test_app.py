import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def activity_signup_path(activity_name: str) -> str:
    encoded_name = urllib.parse.quote(activity_name, safe="")
    return f"/activities/{encoded_name}/signup"


def test_root_redirects_to_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"


def test_signup_for_activity_success(client):
    email = "new_student@mergington.edu"
    response = client.post(activity_signup_path("Basketball Club"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Basketball Club"}
    assert email in activities["Basketball Club"]["participants"]


def test_signup_for_activity_duplicate_fails(client):
    email = "michael@mergington.edu"
    response = client.post(activity_signup_path("Chess Club"), params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_for_unknown_activity_returns_404(client):
    response = client.post(activity_signup_path("Nonexistent Activity"), params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_from_activity_success(client):
    email = "john@mergington.edu"
    response = client.delete(activity_signup_path("Gym Class"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Gym Class"}
    assert email not in activities["Gym Class"]["participants"]


def test_unregister_missing_participant_returns_404(client):
    response = client.delete(activity_signup_path("Gym Class"), params={"email": "missing@student.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete(activity_signup_path("Nonexistent Activity"), params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
