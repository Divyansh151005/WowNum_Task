from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_post_and_export_and_stats():
    payload = {
        "imageId": "abc123",
        "original": {"name": "Fried Rice", "grams": 250},
        "corrected": {"name": "Tonkotsu Ramen", "grams": 420},
        "adjustments": [
            {"ingredient": "Egg", "deltaGrams": -20},
            {"ingredient": "Noodles", "deltaGrams": 50}
        ],
    }
    r = client.post("/api/feedback/correction", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["imageId"] == "abc123"
    assert body["original"]["name"] == "Fried Rice"
    assert body["corrected"]["name"] == "Tonkotsu Ramen"
    assert isinstance(body.get("adjustments"), list)

    r2 = client.get("/api/feedback/export?format=jsonl")
    assert r2.status_code == 200
    lines = r2.text.strip().splitlines()
    assert len(lines) >= 1
    # Ensure adjustments field present in JSONL
    assert '"adjustments"' in lines[-1]

    r3 = client.get("/api/feedback/stats")
    assert r3.status_code == 200
    data = r3.json()
    assert "top5" in data
    assert any(item["label"] == "Tonkotsu Ramen" for item in data["top5"]) 


