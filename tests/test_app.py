import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities

# Initial activities data (deep copy to avoid mutations)
initial_activities = copy.deepcopy(activities)

@pytest.fixture(scope="function")
def client():
    # Reset activities to initial state before each test
    global activities
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))
    return TestClient(app)

# Tests for GET /activities
def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Based on current activities
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]

# Tests for POST /activities/{activity_name}/signup
def test_signup_success(client):
    response = client.post("/activities/Chess%20Club/signup?email=new@student.edu")
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@student.edu for Chess Club"}
    # Verify participant was added
    response = client.get("/activities")
    data = response.json()
    assert "new@student.edu" in data["Chess Club"]["participants"]

def test_signup_duplicate(client):
    # Sign up first
    client.post("/activities/Chess%20Club/signup?email=test@student.edu")
    # Try to sign up again
    response = client.post("/activities/Chess%20Club/signup?email=test@student.edu")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_invalid_activity(client):
    response = client.post("/activities/Invalid%20Activity/signup?email=test@student.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_signup_full_capacity(client):
    activity = "Tennis%20Club"  # max_participants: 10, current participants: 1
    # Fill up the activity (9 more spots)
    for i in range(9):
        email = f"student{i}@edu"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    # Now full, try to add one more
    response = client.post(f"/activities/{activity}/signup?email=extra@edu")
    assert response.status_code == 400
    assert "maximum capacity" in response.json()["detail"]

# Tests for DELETE /activities/{activity_name}/signup
def test_unregister_success(client):
    # Sign up first
    client.post("/activities/Chess%20Club/signup?email=test@student.edu")
    # Unregister
    response = client.delete("/activities/Chess%20Club/signup?email=test@student.edu")
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered test@student.edu from Chess Club"}
    # Verify participant was removed
    response = client.get("/activities")
    data = response.json()
    assert "test@student.edu" not in data["Chess Club"]["participants"]

def test_unregister_not_signed_up(client):
    response = client.delete("/activities/Chess%20Club/signup?email=notsigned@edu")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]

def test_unregister_invalid_activity(client):
    response = client.delete("/activities/Invalid%20Activity/signup?email=test@edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]
