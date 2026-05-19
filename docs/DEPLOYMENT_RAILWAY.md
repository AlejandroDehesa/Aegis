# Aegis Deployment Guide (Railway)

This guide prepares Aegis for a real cloud deploy using Railway (or equivalent managed services).
It does not require committing secrets and it does not run deploy commands automatically.

## 1. Recommended Architecture

- Backend service: FastAPI container (`backend/`)
- Frontend service: static React build (`frontend/`)
- PostgreSQL service: managed Railway PostgreSQL

## 2. Backend Environment Variables

Set these in the backend service (Railway variables panel):

- `APP_ENV=production`
- `DEBUG=false`
- `PORT` (Railway injects it automatically)
- `DATABASE_URL` (from managed PostgreSQL)
- `JWT_SECRET_KEY` (strong secret, at least 32 chars)
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `CORS_ORIGINS=https://<your-frontend-domain>`
- `LLM_PROVIDER=openrouter`
- `LLM_ENABLE_REAL_CALLS=true`
- `OPENROUTER_API_KEY` (secret)
- `OPENROUTER_MODEL` (for example: `openai/gpt-4o-mini`)
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `LLM_MAX_TOKENS=1200`
- `LLM_TEMPERATURE=0.3`
- `LLM_TIMEOUT_SECONDS=30`
- `TASK_EXECUTION_MODE=background`
- `RAG_ENABLED=true`
- `RATE_LIMIT_ENABLED=true`
- `RATE_LIMIT_REQUESTS_PER_MINUTE=120`
- `RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=20`
- `RATE_LIMIT_TASK_EXECUTE_PER_MINUTE=10`
- `DOCUMENT_MAX_UPLOAD_MB=5`
- `DOCUMENT_ALLOWED_EXTENSIONS=.txt,.md,.pdf`
- `DOCUMENT_ALLOWED_MIME_TYPES=text/plain,text/markdown,application/pdf`

## 3. Frontend Environment Variables

Set these for the frontend build:

- `VITE_API_BASE_URL=https://<your-backend-domain>/api/v1`

`VITE_API_URL` is still accepted for compatibility, but `VITE_API_BASE_URL` is the preferred variable.
In Railway, the frontend must call the backend public URL directly through this variable.
Do not use `proxy_pass http://backend:8000` or `upstream backend` in `nginx.conf`.

## 4. Build and Start Commands

Backend:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`

Frontend:

- Build: `npm ci && npm run build`
- Start: `nginx -g "daemon off;"`
- Root Directory (Railway service): `frontend`
- Docker runtime serves `dist/` using `frontend/nginx.conf`

Nginx note for Railway:

- No internal Docker Compose DNS is available between independent Railway services.
- Keep the frontend Nginx as static SPA hosting only (`try_files ... /index.html`).
- Frontend API routing must be done by `VITE_API_BASE_URL`, not by Nginx reverse proxy.

Migrations (production):

- `alembic upgrade head`

## 5. Health and Readiness Checks

Use:

- `/api/v1/health`
- `/api/v1/health/live`
- `/api/v1/health/ready`

`/health/ready` checks database reachability and must pass before routing production traffic.

## 6. Post-Deploy Validation Checklist

1. Signup and login work.
2. Create a task.
3. Execute a comparison task.
4. Verify result and `execution_trace`.
5. Upload one document.
6. Execute a task that should use RAG context.
7. Verify insights endpoint data is still returned.

## 7. Known Production Limitations

- `FastAPI BackgroundTasks` is not a distributed job queue.
- In-memory rate limiting is per instance (not shared across replicas).
- Local file storage can be ephemeral in cloud environments without persistent volumes.
- Local/vector RAG persistence requires explicit storage strategy in multi-instance setups.
- OpenRouter calls consume real tokens and real cost.
- Never commit secrets (`.env`, API keys, database credentials).
