# Development Guide

This guide covers setting up the Local Services Marketplace for local development, running tests, working with migrations, and adding new features.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Python | 3.12+ | Backend development (if running outside Docker) |
| Node.js | 18+ | Admin panel development |
| Flutter | 3.x | Mobile app development |
| ADB | Latest | Android app installation/debugging |

## Backend Development

### Running with Docker (Recommended)

```bash
# Start in dev mode — enables hot-reload and Adminer DB browser
make dev

# View logs
make logs

# Open a shell in the API container
make shell
```

The dev compose overlay (`docker-compose.dev.yml`) adds:
- Hot-reload via uvicorn `--reload` flag
- Adminer at http://localhost:8080 for database browsing

### Running Outside Docker

If you prefer running the backend directly:

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (point to local/docker services)
export DATABASE_URL="postgresql+asyncpg://app:password@localhost:5432/local_services"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/1"
export CELERY_RESULT_BACKEND="redis://localhost:6379/2"
export SECRET_KEY="dev-secret-key"

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You'll still need PostgreSQL and Redis running — start them with:

```bash
docker compose up -d postgres redis
```

### Running Celery Workers

```bash
# In a separate terminal (with venv activated and env vars set)
celery -A app.celery_app:celery worker -l info -c 4

# Celery Beat scheduler (for periodic tasks like booking reminders)
celery -A app.celery_app:celery beat -l info
```

## Admin Panel Development

```bash
cd admin

# Install dependencies
npm install

# Set the API URL
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start dev server
npm run dev
# → http://localhost:3000
```

### Building for Production

```bash
npm run build
npm start
```

## Mobile App Development

### Setup

```bash
cd mobile

# Get Flutter dependencies
flutter pub get

# Run on connected device or emulator
flutter run
```

### Configuration

The app's base URL is configured for Android emulator (`10.0.2.2:8000`). To change it, update the API base URL in the app's core configuration files under `lib/core/`.

### Building APK

```bash
cd mobile
flutter build apk --debug
# Output: build/app/outputs/flutter-apk/app-debug.apk
```

## Database

### Running Migrations

```bash
# Apply all pending migrations
make migrate

# Or from inside the container
docker compose exec api alembic upgrade head
```

### Creating a New Migration

```bash
# Auto-generate from model changes
make migration msg="add_favorites_table"

# Or manually
docker compose exec api alembic revision --autogenerate -m "add_favorites_table"
```

### Rolling Back

```bash
# Roll back one step
docker compose exec api alembic downgrade -1

# Roll back to a specific revision
docker compose exec api alembic downgrade <revision_id>
```

### Accessing the Database

```bash
# PostgreSQL shell
make psql

# Or use Adminer in dev mode
# http://localhost:8080
# Server: postgres, User: app, Password: password, Database: local_services
```

### Creating an Admin User

There is no default admin account. Create one via the database:

```bash
make psql
```

```sql
-- First register a user via the API, then promote to admin:
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

Or use the API to register, then promote:

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "securepassword", "first_name": "Admin"}'

# Then promote via psql
make psql
# UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```

## Running Tests

### Backend Tests

```bash
# Run all tests
make test

# Run with verbose output
docker compose exec api pytest -v

# Run a specific test file
docker compose exec api pytest tests/test_auth.py -v

# Run with coverage
docker compose exec api pytest --cov=app --cov-report=term-missing
```

### Linting

```bash
# Run ruff linter
make lint

# Auto-fix issues
docker compose exec api ruff check app/ --fix
```

### Admin Panel

```bash
cd admin
npm run lint
```

### Mobile Tests

```bash
cd mobile
flutter test
```

## Adding New API Endpoints

Follow this pattern to add a new endpoint module:

### 1. Create the Model

Add a SQLAlchemy model in `backend/app/models/`:

```python
# backend/app/models/favorite.py
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    master_id = Column(UUID(as_uuid=True), ForeignKey("master_profiles.id"), nullable=False)
```

### 2. Create Pydantic Schemas

Add request/response schemas in `backend/app/schemas/`:

```python
# backend/app/schemas/favorite.py
from pydantic import BaseModel
from uuid import UUID

class FavoriteCreate(BaseModel):
    master_id: UUID

class FavoriteResponse(BaseModel):
    id: UUID
    user_id: UUID
    master_id: UUID

    model_config = {"from_attributes": True}
```

### 3. Create the Router

Add route handlers in `backend/app/api/v1/`:

```python
# backend/app/api/v1/favorites.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/", response_model=FavoriteResponse)
async def add_favorite(data: FavoriteCreate, user=Depends(get_current_user)):
    ...
```

### 4. Register the Router

Add the router to the FastAPI app in `backend/app/main.py`:

```python
from app.api.v1.favorites import router as favorites_router
app.include_router(favorites_router, prefix="/api/v1")
```

### 5. Generate Migration

```bash
make migration msg="add_favorites_table"
make migrate
```

### 6. Add Tests

Create tests in `backend/tests/`:

```python
# backend/tests/test_favorites.py
import pytest

class TestFavorites:
    async def test_add_favorite(self, client, auth_headers):
        response = await client.post(
            "/api/v1/favorites/",
            json={"master_id": "..."},
            headers=auth_headers,
        )
        assert response.status_code == 200
```

## Project Conventions

- **API versioning**: All endpoints are under `/api/v1/`
- **Auth**: Use `Depends(get_current_user)` from `app.api.deps` for protected endpoints
- **Admin-only**: Use `Depends(get_current_admin)` for admin endpoints
- **Async**: All database operations use async SQLAlchemy sessions
- **Validation**: Pydantic schemas for all request/response bodies
- **Business logic**: Keep route handlers thin; put logic in `app/services/`
- **Background tasks**: Use Celery tasks in `app/tasks/` for async operations (push notifications, emails)

## Useful Commands Reference

```bash
# Docker
make up              # Start services
make down            # Stop services
make dev             # Dev mode (hot-reload)
make logs            # Tail all logs
make build           # Rebuild images
make shell           # Shell into API container

# Database
make migrate         # Run migrations
make migration msg="desc"  # Create migration
make psql            # PostgreSQL shell

# Testing
make test            # Run tests
make lint            # Run linter
make health          # Health check
```
