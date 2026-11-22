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

# set SECRET_KEY in backend/.env to the output of:
openssl rand -hex 32

# 3. Install dependencies
uv sync
uv run pre-commit install

# 4. Run the API
uv run fastapi dev app/main.py
```

API docs: http://127.0.0.1:8000/docs

## Running checks

Tests need the database running (`docker compose up -d db`) and, once, a test database:
`docker compose exec db createdb -U vocab vocab_test`

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

## Excel format

Each course is imported from its own `.xlsx` file. The first sheet needs a header row:

| ID | Word | Translation | Description |
|----|------|-------------|-------------|
| 1  | der Hund | the dog | |

- `ID`, `Word` and `Translation` are required; `Description` is optional.
- IDs are positive whole numbers, unique within the file.
- Column order and capitalisation don't matter; empty rows are skipped.
- One invalid row rejects the whole file, with a list of all errors.

Upload: `POST /api/v1/courses/{course_id}/import` with the file as form field `file`.
Every upload syncs the course with the file:

| Row in the file | Result |
|---|---|
| New ID | card added |
| Same ID, changed text | card updated, learning progress kept |
| ID missing from the file | card deactivated, learning progress kept |
| ID back in the file | card reactivated |

Add `?dry_run=true` to see the summary without saving anything.

## Main endpoints

| Method and path | Purpose |
|---|---|
| `POST /api/v1/auth/register` | Create an account (email, password of 8-128 characters) |
| `POST /api/v1/courses` | Create a course |
| `GET /api/v1/courses` | List courses |
| `GET /api/v1/courses/{id}` | Get one course |
| `POST /api/v1/courses/{id}/import` | Upload the course's Excel file (`?dry_run=true` to preview) |
| `GET /api/v1/courses/{id}/cards` | List cards: `search`, `include_inactive`, `limit`, `offset` |
| `POST /api/v1/auth/token` | Log in (form fields `username` = email, `password`); returns a bearer token |
| `GET /api/v1/auth/me` | The logged-in user (header `Authorization: Bearer <token>`) |

Full interactive documentation: `/docs`.
Course, card and import endpoints require `Authorization: Bearer <token>`. Users only see their own courses; another user's course returns 404.
