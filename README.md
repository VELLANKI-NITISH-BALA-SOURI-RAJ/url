# Production URL Shortener Build Notes

## ⚙️ Tech Stack

### Backend
- **Framework**: FastAPI (High-performance async Python framework)
- **Language**: Python 3
- **ORM**: SQLAlchemy with Asyncio support
- **Database Migrations**: Alembic
- **Database Engine**: SQLite (via `aiosqlite` for local dev) or PostgreSQL (via `asyncpg` for production)
- **Caching & Rate Limiting**: Redis
- **Data Validation**: Pydantic
- **Password Hashing**: Passlib (Bcrypt)

### Frontend
- **Structure**: Vanilla HTML5
- **Styling**: Plain CSS (Glassmorphism design, custom animations)
- **Logic**: Vanilla JavaScript
- **Typography**: Google Fonts (Outfit)
- **Icons**: Lucide Icons
- **Utilities**: QRCode.js

### Testing
- **Unit & Integration Tests**: Pytest
- **Async HTTP Client**: HTTPX
- **Load Testing**: Locust

### DevOps & Deployment
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git & GitHub

## 📂 Folder Structure

```text
/
├── alembic/              # Database migration configurations and scripts
├── app/                  # Main FastAPI backend application
│   ├── api/              # API routers and endpoints (v1)
│   ├── core/             # Core configuration and utilities
│   ├── db/               # Database session management
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas for data validation
│   ├── services/         # Business logic and caching
│   └── main.py           # FastAPI application entry point
├── frontend/             # Vanilla HTML/CSS/JS frontend
│   └── index.html        # Main user interface
├── tests/                # Pytest suites for automated testing
│   ├── conftest.py       # Pytest fixtures
│   └── test_url.py       # API integration tests
├── docker-compose.yml    # Docker services configuration
├── Dockerfile            # Application container image definition
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Python dependencies
└── setup_local.ps1       # Windows setup script for local development
```

## Key Architecture Decisions

### 1. ID Generation Strategy (Base62)
- We use the database's auto-incrementing BigInt ID as the source of truth.
- The ID is encoded to Base62 (`0-9a-zA-Z`), which provides compact and unique short codes.
- **Example**: ID `1` -> `1`, ID `12345` -> `3D7`.
- **Scaling Note**: For multi-region master-master setups, we would swap this for a Snowflake ID generator (Time-based unique ID) to avoid global lock contention.

### 2. Caching Strategy
- **Read-First**: Hits Redis before touching PostgreSQL.
- **Expiration**: Hot URLs are cached for 24 hours.
- **Backfill**: On a cache miss, the system fetches from DB and immediately hydrates Redis for the next requester.

### 3. Redirection Performance
- The redirection logic uses 301 (Permanent) or 302 (Found) status codes.
- Analytics logging is decoupled using `FastAPI BackgroundTasks`. The user receives the `Location` header immediately, while the analytics write happens asynchronously.

### 4. Rate Limiting
- Implemented using Redis `INCR` and `EXPIRE`. 
- Limits clients to 100 requests per minute by default.

### 5. Analytics
- Captures IP, User-Agent, and Referrer.
- Stored in a separate table with a foreign key to the URL.

## How to Run locally

### Option 1: Docker (Recommended)
1. Ensure you have Docker Desktop installed and running.
2. Run: `docker compose up --build`
3. The API will be available at `http://localhost:8000`
4. Documentation will be at `http://localhost:8000/docs`

### Option 2: Local Script (If Docker is not available)
1. Run `.\setup_local.ps1` to create a virtual environment and set up SQLite/Memory Redis.
2. Run `.\venv\Scripts\python -m uvicorn app.main:app --reload`

## How to Test

### 1. Automated Tests (Pytest)
This project uses `pytest` and `httpx` for integration testing. These tests use an in-memory SQLite database.
1. Activate your virtual environment: `.\venv\Scripts\activate`
2. Run tests: `pytest`

### 2. Manual Testing (Swagger UI)
1. Start the server (using Docker or local script).
2. Navigate to `http://localhost:8000/docs` in your browser.
3. Use the "Try it out" buttons to test the endpoints:
   - `POST /shorten`: Create a short URL.
   - `GET /{short_code}`: Test the redirection.
   - `GET /api/v1/{short_code}/stats`: View click analytics.

## API Endpoints
- `POST /shorten`: Input `{ "long_url": "..." }` -> Output `{ "short_url": "..." }`
- `GET /{short_code}`: Redirects to the long URL.
- `GET /api/v1/{short_code}/stats`: Returns click counts and last 10 visits.

