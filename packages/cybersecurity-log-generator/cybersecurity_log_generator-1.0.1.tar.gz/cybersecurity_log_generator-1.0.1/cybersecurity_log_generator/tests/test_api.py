"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from cybersecurity_log_generator.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_supported_types():
    """Test getting supported log types."""
    response = client.get("/types")
    assert response.status_code == 200
    data = response.json()
    assert "log_types" in data
    assert "count" in data
    assert len(data["log_types"]) > 0


def test_get_supported_pillars():
    """Test getting supported pillars."""
    response = client.get("/pillars")
    assert response.status_code == 200
    data = response.json()
    assert "pillars" in data
    assert "count" in data
    assert len(data["pillars"]) > 0


def test_generate_logs():
    """Test log generation endpoint."""
    request_data = {
        "log_type": "ids",
        "count": 5,
        "time_range": "1h"
    }
    
    response = client.post("/generate", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 5
    assert len(data["logs"]) == 5


def test_generate_pillar_logs():
    """Test pillar log generation endpoint."""
    request_data = {
        "pillar": "authentication",
        "count": 5,
        "time_range": "1h"
    }
    
    response = client.post("/pillar", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 5
    assert len(data["logs"]) == 5


def test_generate_logs_invalid_type():
    """Test log generation with invalid log type."""
    request_data = {
        "log_type": "invalid_type",
        "count": 5
    }
    
    response = client.post("/generate", json=request_data)
    assert response.status_code == 400


def test_generate_pillar_logs_invalid_pillar():
    """Test pillar log generation with invalid pillar."""
    request_data = {
        "pillar": "invalid_pillar",
        "count": 5
    }
    
    response = client.post("/pillar", json=request_data)
    assert response.status_code == 400
