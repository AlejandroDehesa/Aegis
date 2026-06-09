# Guía De Despliegue De Aegis (Railway)

Esta guía prepara Aegis para un despliegue cloud real usando Railway (o servicios gestionados equivalentes).
No requiere commitear secretos ni ejecuta comandos de deploy automáticamente.

## 1. Arquitectura Recomendada

- Servicio backend: contenedor FastAPI (`backend/`)
- Servicio frontend: build estática de React (`frontend/`)
- Servicio PostgreSQL: PostgreSQL gestionado por Railway

## 2. Variables De Entorno Del Backend

Configura estas variables en el servicio backend (panel de variables de Railway):

- `APP_ENV=production`
- `DEBUG=false`
- `PORT` (Railway lo inyecta automáticamente)
- `DATABASE_URL` (desde PostgreSQL gestionado)
- `JWT_SECRET_KEY` (secreto fuerte, al menos 32 chars)
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `CORS_ORIGINS=https://<tu-dominio-frontend>`
- `LLM_PROVIDER=openrouter`
- `LLM_ENABLE_REAL_CALLS=true`
- `OPENROUTER_API_KEY` (secreto)
- `OPENROUTER_MODEL` (por ejemplo: `openai/gpt-4o-mini`)
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `LLM_MAX_TOKENS=1200`
- `LLM_TEMPERATURE=0.3`
- `LLM_TIMEOUT_SECONDS=30`
- `TASK_EXECUTION_MODE=background`
- `RAG_ENABLED=true`
- `RAG_VECTOR_BACKEND=pgvector`
- `EMBEDDING_DIMENSION=64`
- `RATE_LIMIT_ENABLED=true`
- `RATE_LIMIT_REQUESTS_PER_MINUTE=120`
- `RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=20`
- `RATE_LIMIT_TASK_EXECUTE_PER_MINUTE=10`
- `DOCUMENT_MAX_UPLOAD_MB=5`
- `DOCUMENT_ALLOWED_EXTENSIONS=.txt,.md,.csv,.json`
- `DOCUMENT_ALLOWED_MIME_TYPES=text/plain,text/markdown,text/csv,application/json`

## 3. Variables De Entorno Del Frontend

Configura esto para el build del frontend:

- `VITE_API_BASE_URL=https://<tu-dominio-backend>/api/v1`

`VITE_API_URL` se sigue aceptando por compatibilidad, pero `VITE_API_BASE_URL` es la variable preferida.
En Railway, el frontend debe llamar directamente a la URL pública del backend mediante esta variable.
No uses `proxy_pass http://backend:8000` ni `upstream backend` en `nginx.conf`.

## 4. Comandos De Build Y Start

Backend:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Ruta del Dockerfile: `backend/Dockerfile`
- Build context / Root Directory: raíz del repositorio
- Los archivos de Alembic deben existir dentro de la imagen backend (`alembic.ini`, `alembic/`)

Recomendaciones de start command en Railway:

- Start temporal de inicialización:
  `sh -c "alembic upgrade head && python -m scripts.backfill_pgvector_embeddings && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"`
- Start normal tras la inicialización:
  `sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"`

Frontend:

- Build: `npm ci && npm run build`
- Start: `nginx -g "daemon off;"`
- Root Directory (servicio Railway): `frontend`
- El runtime Docker sirve `dist/` usando `frontend/nginx.conf`

Nota de Nginx en Railway:

- No existe DNS interno de Docker Compose entre servicios Railway independientes.
- Mantén el Nginx del frontend como hosting estático SPA únicamente (`try_files ... /index.html`).
- El enrutado API del frontend debe hacerse mediante `VITE_API_BASE_URL`, no con reverse proxy Nginx.

Migraciones (producción):

- `alembic upgrade head`
- `python -m scripts.backfill_pgvector_embeddings` (solo para backfill de chunks antiguos con `embedding IS NULL`)

Bootstrap legacy de base de datos (si el esquema existía antes de versionar Alembic):

- `alembic stamp 0001_initial_schema`
- `alembic upgrade head`

## 5. Checks De Health Y Readiness

Usa:

- `/api/v1/health`
- `/api/v1/health/live`
- `/api/v1/health/ready`

`/health/ready` comprueba conectividad con base de datos y debe pasar antes de enrutar tráfico productivo.

## 6. Checklist De Validación Post-Deploy

1. Signup y login funcionan.
2. Crear una tarea.
3. Ejecutar una tarea de comparación.
4. Verificar resultado y la traza de ejecucion.
5. Subir un documento.
6. Ejecutar una tarea que deba usar contexto RAG.
7. Verificar que el endpoint de insights sigue devolviendo datos.

## 7. Limitaciones Conocidas De Producción

- `FastAPI BackgroundTasks` no es una cola distribuida de jobs.
- El rate limiting in-memory es por instancia (no compartido entre réplicas).
- El almacenamiento local de ficheros puede ser efímero en cloud sin volúmenes persistentes.
- La persistencia local/vectorial de RAG requiere estrategia explícita en setups multi-instancia.
- RAG en producción debería usar PostgreSQL + pgvector (`document_chunks.embedding`) para sobrevivir redeploys.
- Las llamadas a OpenRouter consumen tokens y coste reales.
- Nunca subas secretos (`.env`, API keys, credenciales de base de datos).

