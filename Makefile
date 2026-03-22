.PHONY: up down dev logs build migrate test lint shell

up:
	docker compose up -d

down:
	docker compose down

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

logs:
	docker compose logs -f

build:
	docker compose build

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec api pytest -v

lint:
	docker compose exec api ruff check app/

shell:
	docker compose exec api bash

psql:
	docker compose exec postgres psql -U app -d local_services

health:
	curl -s http://localhost:8000/health | python3 -m json.tool
