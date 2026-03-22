# Local Services Marketplace

A marketplace platform connecting clients with local service providers (masters). Clients browse a catalog of services, book appointments, pay online, chat with masters, and leave reviews. Masters manage their profiles, services, schedules, and earnings. Admins oversee the platform through a dedicated web panel.

## Architecture

The project is a monorepo with three components:

| Component | Path | Technology |
|-----------|------|------------|
| **Backend API** | `/backend` | FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Redis 7, Celery |
| **Mobile App** | `/mobile` | Flutter 3.x (Riverpod, Dio, go_router) |
| **Admin Panel** | `/admin` | Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Recharts |

```
Clients (Flutter App)          Admin (Next.js)
        │                           │
        └───────── NGINX ───────────┘
                     │
              FastAPI :8000
         ┌───────────┼───────────┐
     PostgreSQL    Redis      MinIO/S3
                     │
              Celery Workers
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend framework | FastAPI | Async API, auto OpenAPI docs, WebSocket support |
| ORM | SQLAlchemy 2.0 + Alembic | Async database access, migrations |
| Database | PostgreSQL 16 | Primary data store (JSONB for flexible fields) |
| Cache / Broker | Redis 7 | Session cache, Celery broker, WebSocket pub/sub |
| Task queue | Celery | Async push notifications, payment callbacks, reminders |
| Payments | YuKassa API v3 | Hold/capture pattern for marketplace payments |
| Push notifications | Firebase Cloud Messaging | Cross-platform push delivery |
| File storage | MinIO (dev) / S3 (prod) | Avatars, portfolio images, chat attachments |
| Mobile | Flutter 3.x | Single codebase for iOS & Android |
| Mobile state | Riverpod | Compile-safe, testable state management |
| Admin UI | Next.js 14 + Tailwind + shadcn/ui | Server-rendered admin dashboard |
| Auth | JWT (HS256) | Access token 15min / refresh token 30 days |
| Reverse proxy | Nginx | SSL termination, routing |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- (Optional) Android device/emulator + ADB for mobile app

### Setup

```bash
# Clone the repository
git clone https://github.com/vkrasnovid/local-services.git
cd local-services

# Create environment file
cp .env.example .env
# Edit .env with your values (defaults work for local dev)

# Start all services
make up

# Run database migrations
make migrate

# Verify everything is running
make health
# → {"status": "ok"}
```

### Development Mode

```bash
# Start with hot-reload and Adminer (DB browser)
make dev
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| API (via Nginx) | http://localhost | Production-like access |
| API (direct) | http://localhost:8000 | Direct FastAPI access |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| Admin Panel | http://localhost:3000 | Admin web interface |
| Adminer (dev only) | http://localhost:8080 | Database browser |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache & message broker |

## API Documentation

Interactive Swagger UI is available at **http://localhost:8000/docs** when the backend is running. It documents all 47+ endpoints across these modules:

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Auth | `/api/v1/auth/*` | Registration, login, JWT refresh, password reset |
| Categories | `/api/v1/categories/*` | Service categories CRUD |
| Masters | `/api/v1/masters/*` | Master profiles, search, filters |
| Bookings | `/api/v1/bookings/*` | Booking lifecycle management |
| Slots | `/api/v1/slots/*` | Time slot management |
| Payments | `/api/v1/payments/*` | YuKassa payments, refunds, payouts |
| Chat | `/api/v1/chat/*` | Chat rooms and message history |
| Reviews | `/api/v1/reviews/*` | Reviews CRUD, master replies |
| Notifications | `/api/v1/notifications/*` | In-app notification center |
| Upload | `/api/v1/upload/*` | File uploads (images) |
| Admin | `/api/v1/admin/*` | Dashboard stats, user management, moderation |
| Webhooks | `/api/v1/webhooks/*` | YuKassa payment webhooks |

WebSocket endpoint for real-time chat: `ws://localhost:8000/ws/chat?token=<jwt>`

## Mobile App

The Flutter mobile app is available as a pre-built debug APK.

### Install on Android Emulator

```bash
adb install app-debug.apk
```

### Install on Physical Device

```bash
adb -s <device-id> install app-debug.apk
```

The debug APK connects to `http://10.0.2.2:8000` (Android emulator's localhost alias). For physical devices, update the base URL in the app configuration to point to your backend server.

### Key Screens

Login / Registration → Catalog → Master Profile → Service Booking → Payment → Chat → Reviews → My Bookings → Profile Settings

## Admin Panel

Access the admin panel at **http://localhost:3000**. It requires admin credentials to log in.

### Pages

| Page | Description |
|------|-------------|
| Dashboard | Key metrics: registrations, bookings, revenue |
| Users | User list, search, block/unblock, role management |
| Masters | Verification queue: view documents, approve/reject |
| Reviews | Moderation: hide/show reviews |
| Categories | Service categories CRUD |
| Transactions | Payment history, payout management |
| Bookings | Booking overview and management |

### Default Admin Account

An admin account must be created manually via the API or database. See [DEVELOPMENT.md](./DEVELOPMENT.md) for instructions.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | `info` | Logging level |
| `DATABASE_URL` | `postgresql+asyncpg://app:password@postgres:5432/local_services` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery result backend URL |
| `SECRET_KEY` | `change-me-to-random-256-bit-hex` | JWT signing key (**change in production**) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `YUKASSA_SHOP_ID` | — | YuKassa shop ID for payments |
| `YUKASSA_SECRET_KEY` | — | YuKassa secret key |
| `FCM_SERVER_KEY` | — | Firebase Cloud Messaging server key |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | CORS allowed origins |
| `PLATFORM_FEE_PERCENT` | `10` | Platform commission percentage |

## Project Structure

```
local-services/
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── main.py         # App entrypoint, CORS, lifespan
│   │   ├── config.py       # Pydantic Settings
│   │   ├── database.py     # Async engine & session
│   │   ├── celery_app.py   # Celery configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── api/v1/         # Route handlers (13 modules)
│   │   ├── services/       # Business logic layer
│   │   ├── tasks/          # Celery async tasks
│   │   └── ws/             # WebSocket handlers
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── mobile/                 # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── core/           # Config, theme, routing
│   │   ├── features/       # Feature modules (screens + providers)
│   │   └── shared/         # Shared widgets & utilities
│   ├── android/
│   ├── ios/
│   └── pubspec.yaml
├── admin/                  # Next.js admin panel
│   ├── src/app/
│   │   ├── (auth)/         # Login page
│   │   ├── (dashboard)/    # Dashboard, users, masters, reviews,
│   │   │                   # categories, transactions, bookings
│   │   └── api/            # API route handlers
│   ├── package.json
│   └── tailwind.config.ts
├── nginx/                  # Nginx reverse proxy config
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Dev overrides (hot-reload, Adminer)
├── Makefile                # Common commands
├── .env.example            # Environment template
└── app-debug.apk           # Pre-built Android debug APK
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services in background |
| `make down` | Stop all services |
| `make dev` | Start in dev mode (hot-reload, Adminer) |
| `make build` | Rebuild Docker images |
| `make logs` | Tail service logs |
| `make migrate` | Run Alembic migrations |
| `make migration msg="description"` | Create new migration |
| `make test` | Run backend tests |
| `make lint` | Run ruff linter |
| `make shell` | Open bash in API container |
| `make psql` | Open PostgreSQL shell |
| `make health` | Check API health endpoint |

## License

Private — all rights reserved.
