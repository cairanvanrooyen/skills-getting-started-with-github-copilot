"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


def test_root_redirects_to_static_index(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Signed up newstudent@mergington.edu for Chess Club"
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test signup when already registered"""
    response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_from_activity_success(client):
    """Test successful unregister from an activity"""
    response = client.post("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Unregistered michael@mergington.edu from Chess Club"
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.post("/activities/NonExistent/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_not_registered(client):
    """Test unregister when not registered"""
    response = client.post("/activities/Chess%20Club/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not registered for this activity"


def test_full_signup_unregister_flow(client):
    """Test complete flow of signing up and unregistering"""
    email = "testflow@mergington.edu"
    activity = "Programming Class"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify signup
    after_signup = client.get("/activities")
    after_signup_count = len(after_signup.json()[activity]["participants"])
    assert after_signup_count == initial_count + 1
    assert email in after_signup.json()[activity]["participants"]
    
    # Unregister
    unregister_response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    
    # Verify unregister
    after_unregister = client.get("/activities")
    after_unregister_count = len(after_unregister.json()[activity]["participants"])
    assert after_unregister_count == initial_count
    assert email not in after_unregister.json()[activity]["participants"]
