# Vocab App

A personal spaced-repetition vocabulary app, similar to Memrise. Each language course is synced from its own Excel file: new words are added, corrected words are updated, and removed words are deactivated, with learning progress kept.

## Tech stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Tooling:** uv, Ruff, pytest, Docker Compose, GitHub Actions
- **Planned:** React + TypeScript frontend, FSRS scheduling, AWS deployment

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Getting started

```bash
# 1. Start the database
docker compose up -d db

# 2. Configure the backend
cd backend
cp .env.example .env

# 3. Install dependencies
uv sync
uv run pre-commit install

# 4. Run the API
uv run fastapi dev app/main.py
```

API docs: http://127.0.0.1:8000/docs

## Running checks

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest
```

## Project structure

```
vocab-app/
├── .github/workflows/   # CI pipeline
├── backend/
│   │   ├── app/
│   │   ├── cards/       # card model (later: schemas, service, router)
│   │   ├── core/        # settings, logging
│   │   ├── courses/     # course model (later: schemas, service, router)
│   │   ├── db/          # engine, session, Base, mixins
│   │   ├── health/      # liveness and readiness checks
│   │   └── main.py      # application entry point
│   ├── migrations/      # Alembic migrations
│   ├── tests/
│   └── pyproject.toml
└── docker-compose.yaml  # local PostgreSQL
```

## Workflow

- Every change starts as an issue: `[VOC-n] Title`
- Branch naming: `type/VOC-n-short-description` (e.g. `feat/VOC-4-cards-table`)
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
- Changes reach `main` only through a pull request with passing CI, merged with squash

## Database migrations

```bash
cd backend
uv run alembic upgrade head                            # apply all migrations
uv run alembic revision --autogenerate -m "message"    # create a migration from model changes
uv run alembic current                                 # show the current version
```
