# Working Flow Documentation

## System Overview

The WowNom Feedback Collector is a production-ready FastAPI backend that processes food detection corrections through a structured workflow. Here's how the system works end-to-end.

## Complete Working Flow

### 1. System Initialization

```
┌─────────────────────────────────────────────────────────────┐
│                    System Startup                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Load environment variables                               │
│ 2. Initialize database connection                           │
│ 3. Run Alembic migrations                                  │
│ 4. Load taxonomy data from JSON                            │
│ 5. Start FastAPI application                               │
│ 6. Setup security middleware (CORS, Auth)                  │
└─────────────────────────────────────────────────────────────┘
```

**Commands:**
```bash
# Start the system
uvicorn app.main:app --reload

# Check health
curl http://localhost:8000/healthz
# Response: {"status": "ok"}
```

### 2. User Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication                          │
├─────────────────────────────────────────────────────────────┤
│ Client Request → API Key Check → User Validation → Access  │
└─────────────────────────────────────────────────────────────┘
```

**Process:**
1. Client sends request with `Authorization: Bearer demo-key-123`
2. System validates API key against known keys
3. If valid, request proceeds; if invalid, returns 403 Forbidden

**Example:**
```bash
# Valid request
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/health

# Invalid request  
curl -H "Authorization: Bearer invalid-key" \
  http://localhost:8000/api/feedback/health
# Response: 403 Forbidden
```

### 3. Feedback Collection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                Feedback Collection Process                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive correction request                              │
│ 2. Validate authentication                                │
│ 3. Validate input data (Pydantic)                         │
│ 4. Create main correction record                           │
│ 5. Process ingredient adjustments                          │
│ 6. Store in database (transaction)                        │
│ 7. Return complete record to client                       │
└─────────────────────────────────────────────────────────────┘
```

**Step-by-Step Process:**

#### Step 1: Client Sends Correction
```bash
curl -X POST http://localhost:8000/api/feedback/correction \
  -H "Authorization: Bearer demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "imageId": "img_12345",
    "original": {"name": "Fried Rice", "grams": 250},
    "corrected": {"name": "Tonkotsu Ramen", "grams": 420},
    "adjustments": [
      {"ingredient": "Egg", "deltaGrams": -20, "notes": "Less egg"},
      {"ingredient": "Noodles", "deltaGrams": 50, "notes": "More noodles"}
    ]
  }'
```

#### Step 2: System Processing
1. **Authentication**: Verify API key
2. **Validation**: Check all required fields and data types
3. **Database Transaction**:
   - Insert into `feedback_corrections` table
   - Insert into `ingredient_adjustments` table (if provided)
   - Commit transaction

#### Step 3: Response
```json
{
  "id": 1,
  "imageId": "img_12345",
  "original": {"name": "Fried Rice", "grams": 250},
  "corrected": {"name": "Tonkotsu Ramen", "grams": 420},
  "adjustments": [
    {"ingredient": "Egg", "deltaGrams": -20, "notes": "Less egg"},
    {"ingredient": "Noodles", "deltaGrams": 50, "notes": "More noodles"}
  ],
  "createdAt": "2025-09-26T15:46:47.876837Z"
}
```

### 4. Data Export Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Export Process                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive export request                                  │
│ 2. Validate authentication                                │
│ 3. Query database with eager loading                      │
│ 4. Stream results in requested format                     │
│ 5. Return chunked response                                │
└─────────────────────────────────────────────────────────────┘
```

**Export Formats:**

#### JSONL Export
```bash
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/export?format=jsonl
```

**Response (streaming):**
```jsonl
{"id":1,"imageId":"img_12345","original":{"name":"Fried Rice","grams":250},"corrected":{"name":"Tonkotsu Ramen","grams":420},"adjustments":[{"ingredient":"Egg","deltaGrams":-20,"notes":"Less egg"}],"createdAt":"2025-09-26T15:46:47.876837Z"}
{"id":2,"imageId":"img_67890","original":{"name":"Caesar Salad","grams":150},"corrected":{"name":"Greek Salad","grams":180},"adjustments":[],"createdAt":"2025-09-26T15:47:12.123456Z"}
```

#### CSV Export
```bash
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/export?format=csv
```

**Response (streaming):**
```csv
id,imageId,original_name,original_grams,corrected_name,corrected_grams,adjustments,createdAt
1,img_12345,Fried Rice,250,Tonkotsu Ramen,420,"[{""ingredient"":""Egg"",""deltaGrams"":-20,""notes"":""Less egg""}]",2025-09-26T15:46:47.876837Z
2,img_67890,Caesar Salad,150,Greek Salad,180,"[]",2025-09-26T15:47:12.123456Z
```

### 5. Statistics Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                Statistics Generation Process               │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive stats request                                   │
│ 2. Validate authentication                                │
│ 3. Query database for corrections                         │
│ 4. Group by corrected_name                                │
│ 5. Count occurrences                                      │
│ 6. Sort by count (descending)                             │
│ 7. Return top 5 results                                   │
└─────────────────────────────────────────────────────────────┘
```

**Request:**
```bash
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/stats
```

**Response:**
```json
{
  "top5": [
    {"label": "Tonkotsu Ramen", "count": 12},
    {"label": "Fried Rice", "count": 8},
    {"label": "Caesar Salad", "count": 5},
    {"label": "Greek Salad", "count": 3},
    {"label": "Chicken Adobo", "count": 2}
  ]
}
```

## Database Operations Flow

### Data Storage Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Operations                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  feedback_corrections (Main Table)                         │
│  ├── id (Primary Key)                                      │
│  ├── image_id (Indexed)                                    │
│  ├── original_name, original_grams                         │
│  ├── corrected_name (Indexed)                              │
│  ├── corrected_grams                                       │
│  └── created_at (Indexed)                                  │
│                                                             │
│  ingredient_adjustments (Related Table)                    │
│  ├── id (Primary Key)                                      │
│  ├── correction_id (Foreign Key)                           │
│  ├── ingredient                                            │
│  ├── delta_grams                                           │
│  └── notes                                                 │
│                                                             │
│  dish_taxonomy (Reference Table)                           │
│  ├── id (Primary Key)                                      │
│  ├── name (Canonical name)                                 │
│  ├── aliases (JSON array)                                  │
│  ├── ingredients (JSON array)                              │
│  └── macros_per_100g (JSON object)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Transaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Transaction Process                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Begin Transaction                                       │
│ 2. Insert feedback_correction                              │
│ 3. Get generated ID                                        │
│ 4. Insert ingredient_adjustments (if any)                  │
│ 5. Commit Transaction                                      │
│ 6. Return Success                                          │
│                                                             │
│ On Error:                                                  │
│ 1. Rollback Transaction                                    │
│ 2. Return Error Response                                   │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

### Validation Errors (422)
```
┌─────────────────────────────────────────────────────────────┐
│                    Validation Process                      │
├─────────────────────────────────────────────────────────────┤
│ Input Data → Pydantic Validation → Error Details → 422     │
└─────────────────────────────────────────────────────────────┘
```

**Example Error Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "imageId"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### Authentication Errors (403)
```
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Process                    │
├─────────────────────────────────────────────────────────────┤
│ Request → Check API Key → Invalid Key → 403 Forbidden      │
└─────────────────────────────────────────────────────────────┘
```

### Database Errors (500)
```
┌─────────────────────────────────────────────────────────────┐
│                   Database Process                         │
├─────────────────────────────────────────────────────────────┤
│ Query → Database Error → Rollback → 500 Internal Error     │
└─────────────────────────────────────────────────────────────┘
```

## Security Flow

### Request Security Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  Security Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│ 1. CORS Check (Origin validation)                          │
│ 2. Authentication (API Key validation)                     │
│ 3. Input Validation (Pydantic schemas)                     │
│ 4. SQL Injection Prevention (SQLAlchemy ORM)               │
│ 5. Rate Limiting (Per-endpoint limits)                     │
└─────────────────────────────────────────────────────────────┘
```

### CORS Configuration
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",    # Development frontend
    "http://localhost:8080",    # Development admin
    "https://yourdomain.com"    # Production frontend
]
```

## Performance Flow

### Streaming Export Process

```
┌─────────────────────────────────────────────────────────────┐
│                  Streaming Export                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Query database with cursor                              │
│ 2. Process records one by one                             │
│ 3. Format as JSONL/CSV                                     │
│ 4. Stream chunks to client                                 │
│ 5. Close database connection                               │
└─────────────────────────────────────────────────────────────┘
```

**Memory Efficiency:**
- No loading entire dataset into memory
- Chunked transfer encoding
- Database cursor streaming
- Generator-based processing

## Monitoring Flow

### Health Check Process

```
┌─────────────────────────────────────────────────────────────┐
│                   Health Monitoring                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Check database connectivity                             │
│ 2. Verify authentication system                            │
│ 3. Test core functionality                                 │
│ 4. Return status report                                    │
└─────────────────────────────────────────────────────────────┘
```

**Health Endpoints:**
- `GET /healthz` - Basic health check
- `GET /api/feedback/health` - Detailed health status

## Testing Flow

### Automated Testing Process

```
┌─────────────────────────────────────────────────────────────┐
│                  Testing Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Unit Tests (Individual components)                      │
│ 2. Integration Tests (API endpoints)                       │
│ 3. Security Tests (Authentication/Validation)              │
│ 4. Performance Tests (Load/Stress)                         │
│ 5. Database Tests (Migrations/Queries)                     │
└─────────────────────────────────────────────────────────────┘
```

**Test Categories:**
- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end API testing
- **Security Tests**: Authentication and validation
- **Performance Tests**: Load and stress testing
- **Database Tests**: Migration and query testing

## Deployment Flow

### Production Deployment Process

```
┌─────────────────────────────────────────────────────────────┐
│                 Deployment Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Environment Setup (Variables)                           │
│ 2. Database Migration (Alembic)                            │
│ 3. Application Startup (FastAPI)                           │
│ 4. Health Check Verification                               │
│ 5. Load Balancer Configuration                             │
│ 6. Monitoring Setup                                        │
└─────────────────────────────────────────────────────────────┘
```

**Deployment Commands:**
```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:pass@db:5432/feedback"
export SECRET_KEY="$(openssl rand -hex 32)"
export ALLOWED_ORIGINS="https://yourdomain.com"

# 2. Run migrations
alembic upgrade head

# 3. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Verify deployment
curl http://localhost:8000/healthz
```

## Complete End-to-End Example

### Scenario: User Corrects Food Detection

1. **User Action**: User sees "Fried Rice" detected, but it's actually "Tonkotsu Ramen"
2. **Client Request**: Mobile app sends correction with adjustments
3. **System Processing**: 
   - Validates API key
   - Validates input data
   - Stores correction and adjustments
   - Returns confirmation
4. **Data Export**: Admin exports all corrections for retraining
5. **Analytics**: System shows most corrected dishes

**Complete Request/Response Cycle:**
```bash
# 1. Submit correction
curl -X POST http://localhost:8000/api/feedback/correction \
  -H "Authorization: Bearer demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "imageId": "img_12345",
    "original": {"name": "Fried Rice", "grams": 250},
    "corrected": {"name": "Tonkotsu Ramen", "grams": 420},
    "adjustments": [
      {"ingredient": "Egg", "deltaGrams": -20, "notes": "Less egg"},
      {"ingredient": "Noodles", "deltaGrams": 50, "notes": "More noodles"}
    ]
  }'

# Response: 201 Created with full record

# 2. Export data
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/export?format=jsonl

# Response: Streaming JSONL data

# 3. Get statistics
curl -H "Authorization: Bearer demo-key-123" \
  http://localhost:8000/api/feedback/stats

# Response: Top 5 corrected labels
```

This working flow demonstrates how the system processes food detection corrections from initial submission through data export and analytics, providing a complete feedback loop for ML model retraining.
