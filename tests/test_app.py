from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data_without_caching(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    activities = response.json()
    assert "Art Club" in activities
    assert {"description", "schedule", "max_participants", "participants"} <= set(
        activities["Art Club"]
    )


def test_signup_adds_participant(client):
    email = "student@example.com"

    response = client.post("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert email in client.get("/activities").json()["Art Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "student@example.com"
    signup_url = "/activities/Art Club/signup"
    client.post(signup_url, params={"email": email})

    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown Club/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "student@example.com"
    signup_url = "/activities/Art Club/signup"
    client.post(signup_url, params={"email": email})

    response = client.delete(signup_url, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Art Club"}
    assert email not in client.get("/activities").json()["Art Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown Club/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Art Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
