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

## Frontend

Requires Node 24 (see `frontend/.nvmrc`).

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Checks:

```bash
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
```

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
├── frontend/            # React + TypeScript (Vite, Tailwind)
│   └── src/
│       └── pages/       # one component per page
└── docker-compose.yaml  # local PostgreSQL
```

## Workflow

- Every change starts as an issue: `[VOC-n] Title`
- Branch naming: `type/VOC-n-short-description` (e.g. `feat/VOC-4-cards-table`)
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
- Changes reach `main` only through a pull request with passing CI, merged with squash
- CI runs two jobs on every pull request: `backend` (Ruff, mypy, migrations, pytest) and `frontend` (ESLint, Prettier, tsc, Vitest, build); both must pass

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

## Review schedule

| Step | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Next review in | 4 h | 8 h | 1 day | 2 days | 4 days | 1 week | 2 weeks | 1 month | 2 months | 4 months | 6 months |

- After Learn, a word starts at step 0.
- Correct: one step up; step 10 repeats every 6 months.
- Wrong: back to step 0; the failed step becomes the recovery target.
- While recovering, each correct answer moves two steps up, never past the target; then one step at a time again.
- A month is 30 days.

## Answer check

A typed answer is correct when it matches the expected word after both are normalized:
Unicode NFC, surrounding and repeated whitespace collapsed, lowercase.
Accents, letters such as ß, and punctuation must match.

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
| `GET /api/v1/courses/{id}/study` | Counts for the course page: `due` (Revise), `learn_new` (up to 10), `new_total` |
| `GET /api/v1/courses/{id}/study/revise` | Revise round: up to 10 due cards, most overdue first |
| `POST /api/v1/courses/{id}/study/revise/{card_id}` | Answer a card (`{"answer": "..."}`): checked, recorded, rescheduled |
| `GET /api/v1/courses/{id}/study/learn` | Learn round: up to 10 new cards, 3 shuffled exercises each |
| `POST /api/v1/courses/{id}/study/learn/{card_id}` | Answer an exercise (`{"exercise": "...", "answer": "..."}`); all three kinds correct = learned, due in 4 hours |
| `GET /api/v1/courses/{id}/study/characters` | Keys for the on-screen keyboard: non-ASCII characters in the course's words, lowercase, letters kept with their marks |

Full interactive documentation: `/docs`.
Course, card and import endpoints require `Authorization: Bearer <token>`. Users only see their own courses; another user's course returns 404.
