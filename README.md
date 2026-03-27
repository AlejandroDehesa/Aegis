# Aegis

Aegis is a backend-first AI task orchestration platform for real execution workflows:

`task -> classification -> agent selection -> execution -> structured result -> trace -> evaluation`

Aegis is not a chatbot. The goal is operational task runs with persistence, traceability and practical quality review.

## Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.0
- Database: PostgreSQL
- Auth: JWT
- AI: OpenAI API + RAG + lightweight memory
- Frontend: React + Vite (JavaScript)
- Infra: Docker, Docker Compose, Nginx

## Architecture

- `backend/app/`: API, domain, services, models, schemas, agents
- `frontend/src/`: pages, API client, context, hooks, components, styles
- `backend/scripts/`: demo helper scripts

## What makes this portfolio-ready

- End-to-end task orchestration with visible lifecycle
- Multi-agent execution with trace output
- Document ingestion + retrieval context
- Lightweight quality evaluation for completed task outputs
- Environment-aware frontend/backend integration and containerized demo flow

## Environment variables

### Root `.env`

- `PROJECT_NAME`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `FRONTEND_ORIGINS`
- `VITE_API_URL`

### `frontend/.env`

- `VITE_API_URL`
- `VITE_DEV_PROXY_TARGET`

## Quick start (Docker)

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`

## Local development

### 1) Database

```bash
docker compose up -d db
```

### 2) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

## Final demo flow (recommended)

1. Login (or register).
2. Create a task in `Tasks`.
3. Execute the task and observe status progression.
4. Open task detail to inspect result + execution trace.
5. Submit quality evaluation (`rating + optional comment`).
6. Upload documents in `Documents`.
7. Execute a new task to demonstrate RAG-enriched output.

## Demo seed data (optional)

```bash
cd backend
python scripts/seed_demo_data.py
```

Seed script creates/keeps demo account and sample tasks.

- email: `demo@aegis.local`
- password: `Demo12345!`

## Deployment notes

- Frontend is served by Nginx.
- `/api/*` is proxied to backend inside Compose.
- CORS is controlled by `FRONTEND_ORIGINS`.
- Compose includes health checks for db/backend/frontend startup reliability.

## Interview highlights

- Backend-first architecture with clear separation of concerns
- Practical AI orchestration instead of chatbot UX
- Persistent task history and structured execution traces
- Lightweight output evaluation loop for quality visibility
- Demo-ready developer experience and packaging

## Screenshots (placeholders)

Add screenshots in this section before publishing your portfolio:

- Dashboard overview
- Task detail with trace and evaluation
- Documents + RAG workflow
