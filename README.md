# Aegis

Backend-first AI task orchestration with traceability, document context and reviewable outputs.

> Aegis is a technical MVP built for portfolio demos and technical interviews.  
> It focuses on a full workflow - `task -> classification -> agent selection -> execution -> trace -> feedback -> insights` - instead of a single chat response.

## What Is Aegis

Aegis is a full-stack project that shows how an AI-assisted workflow can look when it is treated like product software instead of a chat window.

The core idea is simple:

- a user creates a structured task
- the backend classifies the request
- an agent or execution path is selected
- the run is persisted with status and trace data
- the result can be reviewed, rated and inspected later
- insights aggregate quality signals across runs

It is not presented as a fully production-ready platform. It is presented as a solid, honest portfolio project with real engineering scope.

## Problem It Solves

Many AI demos stop at `prompt -> response`.

Aegis shows a more product-oriented workflow:

- structured task intake instead of free-form chat only
- task classification and routing
- persisted execution lifecycle
- visible execution trace
- output review and lightweight quality scoring
- document upload for retrieval-assisted context
- insights for operational review

That makes it easier to discuss architecture, state, quality control and observability in interviews.

## Core Features

- FastAPI backend with layered service structure
- React + Vite frontend with authenticated product workflow
- session auth for the web app via `HttpOnly` cookie
- task creation, listing, execution and detail views
- persisted execution trace and task metadata
- lightweight output evaluation with rating + comment
- document upload and retrieval-oriented context ingestion
- insights view for failed, low-rated and strong runs
- Docker-based local setup plus backend/frontend test coverage

## Demo Flow

Recommended walkthrough for a 3-5 minute demo:

1. Sign in with the demo user.
2. Create a realistic task from the Tasks page.
3. Execute the task and show state transitions.
4. Open task detail and review the result plus execution trace.
5. Submit feedback on the output quality.
6. Upload a document and explain retrieval-assisted context.
7. Open Insights and show failed vs strong runs.

Detailed script:

- `docs/DEMO_SCRIPT.md`

## Technical Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x |
| Database | PostgreSQL |
| Migrations | Alembic |
| Auth | JWT-based session flow for web app via `HttpOnly` cookie |
| Frontend | React, Vite |
| Infra | Docker Compose, Nginx |
| Testing | `unittest`, Vitest, React Testing Library |
| AI layer | task classification, agent routing, optional LLM provider abstraction |

## Architecture

### Backend

- `backend/app/api/` exposes REST endpoints for auth, tasks, documents, insights, agents and health.
- `backend/app/services/` contains orchestration, classification, selection and document-context logic.
- `backend/app/models/` and `backend/app/schemas/` define persistence and API contracts.
- `backend/app/core/` centralizes config, security and database setup.

### Frontend

- `frontend/src/pages/` contains the product views: auth, dashboard, tasks, task detail, documents and insights.
- `frontend/src/components/` contains shared UI building blocks such as async states, trace rendering and layout.
- `frontend/src/context/` and `frontend/src/hooks/` handle auth, i18n and polling behavior.

### Runtime

- `docker-compose.yml` runs `backend`, `frontend` and `db`.
- `alembic/` is the single migration source of truth.
- local validation uses backend tests, frontend tests, build checks and compose config validation.

## Main Workflow

```txt
task
  -> classification
  -> agent selection
  -> execution
  -> trace persistence
  -> feedback
  -> insights
```

This is the most important part of the project story: Aegis is designed to show an auditable task workflow, not only text generation.

## Screenshots

Screenshot paths are prepared below, but real images still need to be added before publishing the portfolio publicly.

Expected folder:

- `docs/screenshots/`

Prepared placeholders:

![Login](docs/screenshots/login.png)
![Dashboard](docs/screenshots/dashboard.png)
![Tasks List](docs/screenshots/tasks-list.png)
![Create Task](docs/screenshots/create-task.png)
![Task Detail](docs/screenshots/task-detail-trace.png)
![Documents](docs/screenshots/documents-library.png)
![Insights](docs/screenshots/insights.png)

Screenshot capture guide:

- `docs/SCREENSHOT_GUIDE.md`

## Run Locally

### Docker

```bash
cp .env.example .env
docker compose --env-file .env up --build -d
docker compose --env-file .env run --rm backend alembic upgrade head
```

Main URLs:

- frontend: `http://localhost:5173`
- backend: `http://localhost:8000`
- health: `http://localhost:8000/api/v1/health`

### Local Backend + Frontend

```bash
docker compose --env-file .env up -d db

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:AEGIS_ENV_FILE=".env"
python -m alembic -c ..\alembic.ini upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

## Run Tests

### Backend

```bash
cd backend
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

### Frontend

```bash
cd frontend
npm ci
npm run test
npm run build
npm run check:smoke
```

### Compose Config

```bash
docker compose --env-file .env.example config
```

## Demo Seed

To load the local demo user and sample data:

```bash
docker compose --env-file .env run --rm backend alembic upgrade head
docker compose --env-file .env run --rm backend python -m scripts.seed_demo_data
```

## Environment Variables

Keep real secrets only in your local `.env`. Do not commit or share it.

Important variables:

```env
APP_ENV=development
JWT_SECRET_KEY=replace-with-a-long-random-jwt-secret-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30

AUTH_COOKIE_NAME=aegis_access_token
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax

DATABASE_URL=postgresql+psycopg://...

DOCUMENT_ALLOWED_EXTENSIONS=.txt,.md,.csv,.json
DOCUMENT_ALLOWED_MIME_TYPES=text/plain,text/markdown,text/csv,application/json

LLM_PROVIDER=template
LLM_ENABLE_REAL_CALLS=false
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
```

Reference template:

- `.env.example`

## Security And Hardening Applied

- no real `.env` should be committed or shared
- `.env.example` kept as the safe template
- web session moved away from `localStorage` to `HttpOnly` cookie flow
- Alembic used as the migration path instead of runtime schema mutation
- pagination added to core list endpoints
- input validation tightened for auth, tasks and documents
- basic HTTP security headers added
- document upload restrictions and safer defaults added

## Known Limitations

- Aegis is **not** presented as fully production-ready.
- rate limiting is still **in-memory**
- background execution does **not** use a durable queue yet
- Docker runtime still needs to be validated in an environment with a working daemon
- RAG is still MVP-level and does not yet include deep semantic evaluation
- there is no full browser E2E suite such as Playwright or Cypress in the current scope
- current document handling is designed for demo and portfolio flows, not enterprise-scale storage

These are documented intentionally because they show engineering judgment, not weakness.

## Roadmap

- add real portfolio screenshots and a polished public demo path
- expand browser-level E2E coverage for the main workflow
- improve observability and pre-production runtime validation
- evolve background execution toward a durable queue if the project grows

## What This Project Demonstrates

For recruiters, hiring managers and technical reviewers, Aegis demonstrates:

- full-stack product thinking across backend, frontend and docs
- API design and stateful workflow handling
- persistence, traceability and quality review patterns
- pragmatic security hardening for a portfolio-grade app
- documentation discipline and demo preparation
- the ability to scope a project honestly without overselling it

## How To Explain It In An Interview

Short version:

> Aegis is a backend-first AI task orchestration project.  
> Instead of stopping at prompt/response, it shows a full workflow with task intake, routing, execution trace, feedback and insights.

Good talking points:

- why structured tasks are different from a generic chatbot
- why traceability improves trust and debugging
- why feedback and insights make the system more reviewable
- what was hardened already vs what would change before production

Detailed interview notes:

- `docs/INTERVIEW_NOTES.md`

## Additional Documentation

- user guide: `GUIA_USUARIO_NUEVO.md`
- demo script: `docs/DEMO_SCRIPT.md`
- interview notes: `docs/INTERVIEW_NOTES.md`
- screenshot guide: `docs/SCREENSHOT_GUIDE.md`
- testing strategy: `docs/TESTING_STRATEGY.md`
- Railway deployment notes: `docs/DEPLOYMENT_RAILWAY.md`
