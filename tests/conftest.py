"""
Pytest fixtures and configuration for the FastAPI application tests.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


# Store original activities state for resetting between tests
ORIGINAL_ACTIVITIES = {
    name: {
        "description": activity["description"],
        "schedule": activity["schedule"],
        "max_participants": activity["max_participants"],
        "participants": activity["participants"].copy()
    }
    for name, activity in activities.items()
}


@pytest.fixture
def client():
    """Provide a FastAPI TestClient and reset activities before each test."""
    # Reset activities to original state before each test
    activities.clear()
    for name, activity in ORIGINAL_ACTIVITIES.items():
        activities[name] = {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
    
    return TestClient(app)
