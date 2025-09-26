"""Authentication and authorization tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_no_auth():
    """Health endpoint should not require authentication."""
    response = client.get("/api/feedback/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_correction_endpoint_requires_auth():
    """Correction endpoint should require authentication."""
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    response = client.post("/api/feedback/correction", json=payload)
    assert response.status_code == 401


def test_correction_endpoint_with_valid_auth():
    """Correction endpoint should work with valid API key."""
    headers = {"Authorization": "Bearer demo-key-123"}
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["imageId"] == "test123"


def test_correction_endpoint_with_invalid_auth():
    """Correction endpoint should reject invalid API key."""
    headers = {"Authorization": "Bearer invalid-key"}
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 401


def test_export_endpoint_requires_auth():
    """Export endpoint should require authentication."""
    response = client.get("/api/feedback/export")
    assert response.status_code == 401


def test_stats_endpoint_requires_auth():
    """Stats endpoint should require authentication."""
    response = client.get("/api/feedback/stats")
    assert response.status_code == 401
