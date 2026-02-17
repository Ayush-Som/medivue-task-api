# MediVue Task Management API

Task Management API built with FastAPI, PostgreSQL, SQLAlchemy (async), and Docker Compose.

## Features
- Create tasks with priority, due date, and tags
- Filter tasks by completed, priority, and tags (matches ANY tag)
- Pagination with limit/offset and total count
- Soft delete
- Consistent error shape for validation failures
- Tests using pytest + httpx

## Tech Stack
- Python 3.10+
- FastAPI
- PostgreSQL (Docker)
- SQLAlchemy 2.x async + asyncpg
- pytest + httpx

## Run locally (Docker)
1. Copy env example (optional)
   - `cp .env.example .env`
2. Start services
   - `docker compose up --build`
3. Open docs
   - http://localhost:8000/docs

## API Endpoints
- POST /tasks
- GET /tasks (filters: completed, priority, tags CSV, pagination limit/offset)
- GET /tasks/{id}
- PATCH /tasks/{id}
- DELETE /tasks/{id}

## Design Decisions

### Tagging implementation
Used a normalized many-to-many join table (tasks <-> tags) for:
- Referential integrity and reusability of tags
- Efficient querying and indexing for filters
- Better scalability than storing tags as JSONB/ARRAY for this use case

Trade-offs:
- Join table adds an extra table and joins
- But enables clean constraints, indexes, and flexible tag queries

### Delete strategy
Soft delete using `is_deleted` flag.
Reason:
- Safer for auditability and recoverability, which fits healthcare-adjacent systems
- Avoids accidental loss of data

### Indexing
Indexes on:
- tasks.priority
- tasks.completed
- tasks.due_date
- tasks.is_deleted
- tags.name
Composite index on (priority, completed, is_deleted)

## Testing
Run tests locally (not inside Docker):
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `pytest -q`

Tests use SQLite (aiosqlite) for speed and isolation.
Production uses PostgreSQL via docker-compose.

## Production Readiness Improvements
- Alembic migrations (instead of create_all on startup)
- Auth (JWT) + role-based access control
- Structured logging and audit logs
- Observability: metrics and tracing
- Rate limiting and request size limits
- Background jobs for reminders and due-date notifications
- Input hardening and security scanning in CI
- CI/CD pipeline with tests, linting, container builds

## Example Usage

Create a task:

curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare report",
    "description": "Quarterly analytics",
    "priority": 3,
    "due_date": "2030-01-01",
    "tags": ["work", "urgent"]
  }'

Filter by tag:

GET /tasks?tags=work

