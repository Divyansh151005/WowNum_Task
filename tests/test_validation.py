"""Validation and error handling tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
headers = {"Authorization": "Bearer demo-key-123"}


def test_correction_validation_missing_fields():
    """Test validation with missing required fields."""
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish"},  # Missing grams
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 422


def test_correction_validation_invalid_grams():
    """Test validation with invalid grams values."""
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 0},  # Invalid: must be >= 1
        "corrected": {"name": "Corrected Dish", "grams": 100},
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 422


def test_correction_validation_extra_fields():
    """Test validation rejects extra fields."""
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
        "extraField": "should be rejected",
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 422


def test_correction_validation_empty_strings():
    """Test validation with empty strings."""
    payload = {
        "imageId": "",  # Empty string should be rejected
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 422


def test_correction_validation_string_length_limits():
    """Test validation with strings exceeding length limits."""
    payload = {
        "imageId": "a" * 201,  # Exceeds 200 char limit
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 422


def test_correction_with_adjustments_validation():
    """Test validation of ingredient adjustments."""
    payload = {
        "imageId": "test123",
        "original": {"name": "Test Dish", "grams": 100},
        "corrected": {"name": "Corrected Dish", "grams": 150},
        "adjustments": [
            {"ingredient": "Salt", "deltaGrams": -5},
            {"ingredient": "Pepper", "deltaGrams": 2, "notes": "Extra spicy"}
        ],
    }
    
    response = client.post("/api/feedback/correction", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["adjustments"]) == 2
    assert data["adjustments"][0]["ingredient"] == "Salt"
    assert data["adjustments"][0]["deltaGrams"] == -5


def test_export_format_validation():
    """Test export format parameter validation."""
    # Valid formats
    for fmt in ["jsonl", "csv"]:
        response = client.get(f"/api/feedback/export?format={fmt}", headers=headers)
        assert response.status_code == 200
    
    # Invalid format
    response = client.get("/api/feedback/export?format=invalid", headers=headers)
    assert response.status_code == 422
