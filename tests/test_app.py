"""
Tests for the FastAPI Mergington High School activities application.

Covers signup and deletion endpoints with validation scenarios.
"""

import pytest


class TestGetActivities:
    """Test cases for GET /activities endpoint."""
    
    def test_get_activities_returns_list(self, client):
        """Verify GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
        
        # Verify activity structure
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_happy_path(self, client):
        """Test successful signup to an activity."""
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify student was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_signup_duplicate_email(self, client):
        """Test signup fails when student already signed up for activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_activity_full(self, client):
        """Test signup fails when activity has reached max capacity."""
        activity_name = "Chess Club"  # max_participants = 12
        
        # Get current participant count
        activities_response = client.get("/activities")
        activity = activities_response.json()[activity_name]
        initial_count = len(activity["participants"])
        
        # Fill up the activity
        for i in range(activity["max_participants"] - initial_count):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Next signup should fail
        email = "fullstudent@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRemoveParticipant:
    """Test cases for DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_remove_participant_happy_path(self, client):
        """Test successful removal of a participant from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify student was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_remove_nonexistent_participant(self, client):
        """Test removal fails when participant is not in the activity."""
        email = "notinactivity@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_from_nonexistent_activity(self, client):
        """Test removal fails when activity does not exist."""
        response = client.delete(
            "/activities/Nonexistent Club/participants",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""
    
    def test_signup_then_remove_roundtrip(self, client):
        """Test signing up then removing a student."""
        email = "integration@mergington.edu"
        activity_name = "Art Studio"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        assert remove_response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_multiple_signups_independent(self, client):
        """Test that signups to different activities are independent."""
        email = "multiactivity@mergington.edu"
        activities_list = ["Chess Club", "Art Studio", "Drama Club"]
        
        # Sign up to multiple activities
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify signup in all activities
        activities_response = client.get("/activities")
        for activity_name in activities_list:
            assert email in activities_response.json()[activity_name]["participants"]
        
        # Remove from one activity
        client.delete(
            f"/activities/{activities_list[0]}/participants",
            params={"email": email}
        )
        
        # Verify only removed from first activity
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activities_list[0]]["participants"]
        assert email in activities_response.json()[activities_list[1]]["participants"]
        assert email in activities_response.json()[activities_list[2]]["participants"]
