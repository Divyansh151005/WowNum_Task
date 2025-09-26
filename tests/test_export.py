"""Export functionality tests."""

import json
import csv
from io import StringIO
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
headers = {"Authorization": "Bearer demo-key-123"}


def test_jsonl_export_format():
    """Test JSONL export format."""
    # First, create some test data
    payload = {
        "imageId": "export-test-1",
        "original": {"name": "Test Dish 1", "grams": 100},
        "corrected": {"name": "Corrected Dish 1", "grams": 150},
        "adjustments": [{"ingredient": "Salt", "deltaGrams": -5}],
    }
    client.post("/api/feedback/correction", json=payload, headers=headers)
    
    # Test JSONL export
    response = client.get("/api/feedback/export?format=jsonl", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-jsonlines"
    
    # Parse JSONL
    lines = response.text.strip().split('\n')
    assert len(lines) >= 1
    
    # Verify JSON structure
    data = json.loads(lines[0])
    assert "id" in data
    assert "imageId" in data
    assert "original" in data
    assert "corrected" in data
    assert "adjustments" in data
    assert "createdAt" in data


def test_csv_export_format():
    """Test CSV export format."""
    # Test CSV export
    response = client.get("/api/feedback/export?format=csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    
    # Parse CSV
    csv_reader = csv.reader(StringIO(response.text))
    rows = list(csv_reader)
    
    # Check header
    expected_headers = [
        "id", "imageId", "original_name", "original_grams",
        "corrected_name", "corrected_grams", "adjustments", "createdAt"
    ]
    assert rows[0] == expected_headers
    
    # Check data rows
    assert len(rows) >= 2  # Header + at least one data row


def test_export_with_adjustments():
    """Test export includes adjustments data."""
    # Create data with adjustments
    payload = {
        "imageId": "export-test-2",
        "original": {"name": "Test Dish 2", "grams": 200},
        "corrected": {"name": "Corrected Dish 2", "grams": 250},
        "adjustments": [
            {"ingredient": "Salt", "deltaGrams": -10, "notes": "Less salty"},
            {"ingredient": "Pepper", "deltaGrams": 5, "notes": "More spicy"}
        ],
    }
    client.post("/api/feedback/correction", json=payload, headers=headers)
    
    # Test JSONL export
    response = client.get("/api/feedback/export?format=jsonl", headers=headers)
    lines = response.text.strip().split('\n')
    
    # Find our test record
    test_record = None
    for line in lines:
        data = json.loads(line)
        if data["imageId"] == "export-test-2":
            test_record = data
            break
    
    assert test_record is not None
    assert len(test_record["adjustments"]) == 2
    assert test_record["adjustments"][0]["ingredient"] == "Salt"
    assert test_record["adjustments"][0]["deltaGrams"] == -10
    assert test_record["adjustments"][0]["notes"] == "Less salty"


def test_export_empty_database():
    """Test export with empty database."""
    # This test assumes we're using a fresh database
    # In a real scenario, you'd want to clear the database first
    response = client.get("/api/feedback/export?format=jsonl", headers=headers)
    assert response.status_code == 200
    
    # Should return empty JSONL (just empty string)
    assert response.text.strip() == ""
