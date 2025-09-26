"""Rate limiting tests."""

import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
headers = {"Authorization": "Bearer demo-key-123"}


def test_correction_rate_limiting():
    """Test rate limiting on correction endpoint."""
    payload = {
        "imageId": "rate-test",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    # Make requests up to the limit (10/minute)
    responses = []
    for i in range(12):  # Try to exceed the limit
        response = client.post("/api/feedback/correction", json=payload, headers=headers)
        responses.append(response.status_code)
    
    # First 10 should succeed, 11th and 12th should be rate limited
    success_count = sum(1 for status in responses if status == 201)
    rate_limited_count = sum(1 for status in responses if status == 429)
    
    assert success_count >= 10  # At least 10 should succeed
    assert rate_limited_count >= 1  # At least 1 should be rate limited


def test_export_rate_limiting():
    """Test rate limiting on export endpoint."""
    # Make requests up to the limit (5/minute)
    responses = []
    for i in range(7):  # Try to exceed the limit
        response = client.get("/api/feedback/export?format=jsonl", headers=headers)
        responses.append(response.status_code)
    
    # First 5 should succeed, 6th and 7th should be rate limited
    success_count = sum(1 for status in responses if status == 200)
    rate_limited_count = sum(1 for status in responses if status == 429)
    
    assert success_count >= 5  # At least 5 should succeed
    assert rate_limited_count >= 1  # At least 1 should be rate limited


def test_stats_rate_limiting():
    """Test rate limiting on stats endpoint."""
    # Make requests up to the limit (30/minute)
    responses = []
    for i in range(32):  # Try to exceed the limit
        response = client.get("/api/feedback/stats", headers=headers)
        responses.append(response.status_code)
    
    # First 30 should succeed, 31st and 32nd should be rate limited
    success_count = sum(1 for status in responses if status == 200)
    rate_limited_count = sum(1 for status in responses if status == 429)
    
    assert success_count >= 30  # At least 30 should succeed
    assert rate_limited_count >= 1  # At least 1 should be rate limited
