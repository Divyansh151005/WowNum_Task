# WowNom Feedback → Retraining Collector (FastAPI)

Production-like backend for collecting user corrections from a food detection/classification workflow. Stores feedback in SQLite, streams exports (JSONL/CSV), and exposes simple stats for retraining.

- Language/Framework: Python 3.10+, FastAPI, SQLAlchemy 2.x
- Storage: SQLite (file `feedback.db` by default)
- Validation: Pydantic v2
- Tests: pytest + FastAPI TestClient

## Quick Start

Using virtualenv + pip:

```bash
cd /Users/divyanshbarodiya/Desktop/WowNum1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health: `GET http://localhost:8000/healthz`

Run tests:

```bash
PYTHONPATH=. pytest -q
```

## Configuration

- `DATABASE_URL`: SQLAlchemy URL for the feedback DB.
  - Default: `sqlite:///./feedback.db`
  - Example: `export DATABASE_URL=sqlite:////tmp/feedback.db`

## Project Structure

```
WowNum1/
  app/
    main.py                 # FastAPI app factory + router include + DB init
    routers/
      __init__.py
      feedback.py           # Models, Pydantic schemas, endpoints
  data/
    taxonomy.json           # Shared test data (not used by endpoints but included)
  tests/
    test_feedback.py        # E2E tests using TestClient
  requirements.txt
  pyproject.toml            # Poetry (optional)
  README.md
```

## API Reference

Base URL: `http://localhost:8000`

### Health

- `GET /healthz`
- 200 OK → `{ "status": "ok" }`

### Submit a Correction

- `POST /api/feedback/correction`
- Description: Store a user correction with optional per-ingredient adjustments.
- Request body (JSON):

```json
{
  "imageId": "abc123",
  "original": { "name": "Fried Rice", "grams": 250 },
  "corrected": { "name": "Tonkotsu Ramen", "grams": 420 },
  "adjustments": [
    { "ingredient": "Egg", "deltaGrams": -20 },
    { "ingredient": "Noodles", "deltaGrams": 50 }
  ]
}
```

- Validation rules:
  - `imageId`: non-empty string (≤ 200 chars)
  - `original.name`, `corrected.name`: non-empty strings (≤ 200 chars)
  - `original.grams`, `corrected.grams`: integers in [1, 10000]
  - `adjustments`: optional array; objects are stored as-is (JSON)
  - Extra/unknown fields are rejected

- Responses:
  - 201 Created → stored record

```json
{
  "id": 1,
  "imageId": "abc123",
  "original": { "name": "Fried Rice", "grams": 250 },
  "corrected": { "name": "Tonkotsu Ramen", "grams": 420 },
  "adjustments": [
    { "ingredient": "Egg", "deltaGrams": -20 },
    { "ingredient": "Noodles", "deltaGrams": 50 }
  ],
  "createdAt": "2025-09-24T20:39:45.524905Z"
}
```

- 422 Unprocessable Entity on validation errors.

- Sample curl:

```bash
curl -s -X POST http://localhost:8000/api/feedback/correction \
  -H 'Content-Type: application/json' \
  -d '{"imageId":"abc123","original":{"name":"Fried Rice","grams":250},"corrected":{"name":"Tonkotsu Ramen","grams":420},"adjustments":[{"ingredient":"Egg","deltaGrams":-20}]}' | jq .
```

### Export Corrections

- `GET /api/feedback/export?format=jsonl|csv`
- Streams all corrections ordered by insertion.
- JSONL example (media-type `application/x-jsonlines`):

```
{"id":1,"imageId":"abc123","original":{"name":"Fried Rice","grams":250},"corrected":{"name":"Tonkotsu Ramen","grams":420},"adjustments":[{"ingredient":"Egg","deltaGrams":-20}],"createdAt":"2025-09-24T20:39:45.524905Z"}
{"id":2,...}
```

- CSV example (media-type `text/csv`):

```
id,imageId,original_name,original_grams,corrected_name,corrected_grams,adjustments,createdAt
1,abc123,Fried Rice,250,Tonkotsu Ramen,420,"[{""ingredient"":""Egg"",""deltaGrams"":-20}]",2025-09-24T20:39:45.524905Z
```

- Sample curl:

```bash
curl -s http://localhost:8000/api/feedback/export?format=jsonl | head
curl -s http://localhost:8000/api/feedback/export?format=csv | column -t -s,
```

### Stats (Top Corrected Labels)

- `GET /api/feedback/stats`
- Returns top 5 corrected labels and counts:

```json
{ "top5": [ { "label": "Tonkotsu Ramen", "count": 12 } ] }
```

- Sample curl:

```bash
curl -s http://localhost:8000/api/feedback/stats | jq .
```

## Data Model

Table: `feedback_corrections`

- `id` INTEGER PRIMARY KEY
- `image_id` TEXT NOT NULL
- `original_name` TEXT NOT NULL
- `original_grams` INTEGER NOT NULL
- `corrected_name` TEXT NOT NULL (indexed)
- `corrected_grams` INTEGER NOT NULL
- `adjustments_json` TEXT NULL (JSON string)
- `created_at` DATETIME NOT NULL (indexed, UTC)

Schema migrations: a lightweight migration adds `adjustments_json` if missing at startup.

## Development Notes

- OpenAPI docs available at `/docs` and `/redoc` while server is running.
- CORS is enabled for all origins for simplicity.
- The repository includes `data/taxonomy.json` as shared test data; the collector endpoints do not depend on it.

## Troubleshooting

- Tests cannot import `app`:
  - Run tests with `PYTHONPATH=.` (as shown above).
- DB table not found after schema changes:
  - The app auto-creates tables and applies a lightweight migration on startup. Delete `feedback.db` if needed: `rm -f feedback.db`.
- Port already in use:
  - Use a different port: `uvicorn app.main:app --reload --port 8001`

## Submission

- Push to a public GitHub repo and email:
  - Subject: `Backend Mini Project – <Your Name> – Feedback Collector`
  - To: `hello@wownom.com`
  - Include repo link and optional Loom/screenshots.

---

MIT-licensed sample; adjust as needed.
# WowNum_Task
