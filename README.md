# Local Services Marketplace

Marketplace platform connecting clients with local service providers (masters).

## Stack

- **Backend:** FastAPI + PostgreSQL + Redis + Celery
- **Mobile:** Flutter (planned)
- **Admin:** Next.js (planned)
- **Infra:** Docker Compose + Nginx

## Quick Start

```bash
# Copy env file
cp .env.example .env

# Start all services
make up

# Or start in dev mode (hot-reload, adminer)
make dev

# Check health
make health
# → {"status": "ok"}

# Run migrations
make migrate

# Run tests
make test
```

## Services

| Service       | URL                          |
|---------------|------------------------------|
| API           | http://localhost:8000        |
| API Docs      | http://localhost:8000/docs   |
| Nginx         | http://localhost:80          |
| Adminer (dev) | http://localhost:8080        |
| PostgreSQL    | localhost:5432               |
| Redis         | localhost:6379               |

## Project Structure

```
├── backend/          # FastAPI application
├── mobile/           # Flutter app (planned)
├── admin/            # Next.js admin panel (planned)
├── nginx/            # Reverse proxy config
├── docker-compose.yml
├── docker-compose.dev.yml
└── Makefile
```
