# Aegis

Plataforma backend-first para orquestar tareas con agentes IA, con trazabilidad completa de ejecucion.

> Aegis no es un chatbot.  
> Es un MVP tecnico orientado a ejecucion real de tareas: `task -> classification -> agent selection -> execution -> result -> trace -> feedback -> insights`.

## Problema que resuelve

Muchas demos IA se quedan en "prompt -> respuesta".  
Aegis demuestra un flujo de producto mas profesional:

- entrada estructurada de trabajo
- clasificacion de intencion de tarea
- seleccion de agente por tipo
- ejecucion con estado y metadatos
- resultado util para usuario final
- execution trace persistida
- feedback de calidad e insights operativos

## Arquitectura

### Backend (`backend/app/`)

- `api/`: endpoints REST (`auth`, `tasks`, `documents`, `agents`, `insights`, `health`)
- `core/`: configuracion, seguridad y base de datos
- `models/`: entidades SQLAlchemy
- `schemas/`: contratos Pydantic
- `services/`: clasificacion, seleccion, orquestacion, RAG, memoria
- `agents/`: implementaciones de agentes especializados

### Frontend (`frontend/src/`)

- `pages/`: dashboard, tasks, task detail, documents, insights, agents, auth
- `api/`: cliente HTTP y wrappers por recurso
- `context` + `hooks`: auth, i18n y polling
- `components/`: layout, estados async, trace, feedback

### Infra

- Docker Compose con `backend`, `frontend` (Nginx) y `db` (PostgreSQL)
- healthchecks para servicios principales

## Stack tecnico

- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.0
- Database: PostgreSQL
- Auth: JWT
- Frontend: React + Vite
- Infra: Docker Compose + Nginx
- Testing backend: `unittest`
- Testing frontend: Vitest + React Testing Library

## Flujo principal

1. El usuario crea una tarea.
2. El backend clasifica la tarea (comparison, analysis, planning, etc.).
3. Se selecciona agente o pipeline.
4. Se ejecuta y se guarda resultado.
5. Se persiste execution trace por pasos.
6. El usuario revisa detalle, resultado y trace.
7. El usuario valora la calidad (rating + comentario).
8. Insights agrega metricas operativas por usuario.

## Funcionalidades principales

- Auth basica por JWT (signup/login/me)
- Task lifecycle con estado y metadatos
- Clasificacion multilenguaje ES/EN para tipos clave
- Seleccion de agente coherente por `task_type`
- Quality gate basico para evitar outputs placeholder
- Execution trace compatible con formato actual y legacy
- Subida de documentos + chunking + retrieval/fallback
- Insights por usuario para quality review

## Capturas (placeholders)

Agrega screenshots reales para portfolio en `docs/screenshots/` y enlazalos aqui:

- `[Placeholder] Dashboard overview`
- `[Placeholder] Tasks list + execute`
- `[Placeholder] Task detail (result + trace + feedback)`
- `[Placeholder] Insights quality queue`
- `[Placeholder] Documents upload and library`

## Como ejecutar localmente

### Opcion recomendada: Docker

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose up --build -d
```

URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`

### Opcion local (sin contenedores completos)

```bash
docker compose up -d db

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

## Como ejecutar tests

### Backend

```bash
docker compose run --rm backend python -m unittest discover -s tests -t . -p "test_*.py" -v
```

### Frontend

```bash
cd frontend
npm run test
npm run build
npm run check:smoke
```

## Seed demo y reset

### Seed demo

```bash
docker compose run --rm backend python -m scripts.seed_demo_data
```

### Reset demo limpio

```bash
docker compose down -v
docker compose up -d
docker compose run --rm backend python -m scripts.seed_demo_data
```

### Usuario demo

- email: `demo@aegis.local`
- password: `Demo12345!`

## Estado actual

Estado: **MVP tecnico estable para demo y portfolio**.

- backend tests: passing
- frontend tests: passing
- frontend build: passing
- smoke checks: passing
- docker compose: healthy
- seed demo: funcional

No se presenta como "production-ready". Se presenta como base solida demostrable.

## LLM Providers (v0.2 Fase 1)

Aegis incorpora una capa `LLMService -> LLMProvider` con tres providers:

- `template`: provider por defecto, sin llamadas externas, usa fallback seguro.
- `mock`: provider determinista para pruebas unitarias.
- `openrouter`: provider real preparado para OpenRouter (sin activacion por defecto).

Variables recomendadas en `.env` local:

```env
LLM_PROVIDER=template
LLM_ENABLE_REAL_CALLS=false
LLM_TIMEOUT_SECONDS=30
LLM_MAX_TOKENS=1200
LLM_TEMPERATURE=0.3

OPENROUTER_API_KEY=
OPENROUTER_MODEL=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=http://localhost:5173
OPENROUTER_APP_NAME=Aegis
```

Notas de seguridad y alcance:

- `OPENROUTER_API_KEY` solo vive en backend, nunca en frontend.
- Los tests no realizan llamadas reales a OpenRouter.
- Esta fase no implementa RAG nuevo ni ejecucion async.

### Using OpenRouter for real agent intelligence

Por defecto, Aegis usa `LLM_PROVIDER=template` para un modo seguro y sin consumo de tokens.

Para activar inteligencia real en agentes con OpenRouter:

```env
LLM_PROVIDER=openrouter
LLM_ENABLE_REAL_CALLS=true
OPENROUTER_API_KEY=tu_clave
OPENROUTER_MODEL=tu_modelo
```

Notas:

- Los tests siguen usando template/mock y no deben gastar tokens.
- La metadata LLM (`provider`, `model`, `tokens`, `fallback/error`) se guarda en `execution_trace`.
- `OPENROUTER_API_KEY` permanece solo en backend.

### Agent prompt design

- Cada agente tiene prompt especializado (comparison, analysis, planning, summary, research, general).
- Los prompts intentan preservar idioma del usuario (ES/EN) y exigen salida estructurada.
- `ResearchAgent` trabaja solo con contexto disponible y no finge acceso a internet ni fuentes externas.
- Los fallbacks template siguen activos y estructurados para funcionamiento seguro sin llamadas reales.
- La suite de tests automatizada usa template/mock y no llama a OpenRouter real.

### LLM limits and observability (v0.2 Fase 4)

- `LLM_REQUEST_HARD_MAX_TOKENS` limita `max_tokens` efectivo por request.
- `LLM_RETRY_ATTEMPTS` + `LLM_RETRY_BACKOFF_SECONDS` aplican retries controlados solo a errores transitorios del provider real.
- Si OpenRouter falla, Aegis usa fallback template seguro y registra error sanitizado en trace.
- `execution_trace` incluye metadata LLM por paso: provider, model, tokens, estimated_cost, fallback, error, retry_count y latency.
- Se agrega un paso `llm_usage_summary` por tarea con totales de tokens, providers/models usados, fallback global y conteo de errores.
- `estimated_cost` solo se calcula si hay datos suficientes y precios configurados explícitamente.

### Document RAG in task execution (v0.2 Fase 5)

- Flujo: `upload document -> chunking -> embeddings/vector store -> retrieval -> agent prompt context -> execution trace`.
- El retrieval usa `task.title + task.description` y respeta aislamiento por `user_id`.
- El trace incluye un paso `document_retrieval` con chunks recuperados, documentos usados, errores y tamaño de contexto.
- Si no hay resultados o falla retrieval, la tarea continúa con fallback controlado sin bloquear ejecución.
- RAG no navega por internet ni inventa fuentes externas; usa solo documentos del usuario actual.

## Decisiones tecnicas

- Enfoque backend-first para priorizar flujo de ejecucion y trazabilidad.
- Agentes simples y deterministas para demo estable (sin sobrearquitectura).
- Quality gate minimo para evitar "completed" con output inutil.
- Compatibilidad de trace legacy para no romper datos existentes.
- Test strategy por fases para escalar calidad sin frenar velocidad.

## Limitaciones conocidas

- No hay e2e browser completo (Playwright/Cypress) en este alcance.
- Seguridad hardening de produccion no completo (headers/rate-limit/observabilidad avanzada).
- RAG implementado a nivel MVP (sin evaluacion semantica profunda en CI).
- Sin multi-tenant enterprise ni orquestacion distribuida compleja.

## Roadmap (realista)

- P1: consolidar script/capturas de demo para portfolio.
- P2: sumar e2e frontend critico y contratos API adicionales.
- P3: reforzar seguridad y observabilidad para entorno preproduccion.

## Documentacion complementaria

- Guia de uso: `GUIA_USUARIO_NUEVO.md`
- Test strategy: `docs/TESTING_STRATEGY.md`
- Test matrix 1000+: `docs/TEST_MATRIX_1000.md`
- Demo script (3-5 min): `docs/DEMO_SCRIPT.md`
- Notas de entrevista tecnica: `docs/INTERVIEW_NOTES.md`

### Background task execution (v0.2 Fase 6)

- `POST /tasks/{task_id}/execute` soporta ejecucion en segundo plano con `FastAPI BackgroundTasks`.
- Flujo: `pending/failed -> queued -> processing -> completed/failed`.
- Configuracion:
  - `TASK_EXECUTION_MODE=background` para runtime normal.
  - `TASK_EXECUTION_MODE=sync` para suite de tests (determinista, sin polling extra).
- En modo background no se reutiliza la sesion DB de la request; el worker abre su propia sesion.
- Esta fase no usa Celery ni Redis todavia.

### Production hardening foundations (v0.2 Fase 7)

- Request/response hardening:
  - middleware con `X-Request-ID` (se preserva si viene del cliente)
  - logging estructurado basico por request (`method`, `path`, `status`, `duration_ms`)
  - handlers globales de errores con formato consistente:
    - `http_*`
    - `validation_error`
    - `internal_error`
- Rate limiting in-memory (orientado a demo/portfolio):
  - limite general por IP/ruta
  - limite mas estricto para `login/signup`
  - limite especifico para `POST /tasks/{task_id}/execute`
- Upload hardening para documentos:
  - validacion de tamano maximo
  - extensiones y MIME permitidos por config
  - rechazo de nombres peligrosos/path traversal
  - rechazo de archivos vacios
- Health endpoints:
  - `GET /api/v1/health`
  - `GET /api/v1/health/live`
  - `GET /api/v1/health/ready` (readiness con check de DB)
- CI basico en GitHub Actions:
  - backend tests
  - frontend test/build/smoke
- Migraciones:
  - estructura Alembic inicial incluida en repo (`alembic/`, `alembic.ini`)
  - en produccion, preferir Alembic frente a `create_all`.

Configuracion relevante:

```env
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=20
RATE_LIMIT_TASK_EXECUTE_PER_MINUTE=10

DOCUMENT_MAX_UPLOAD_MB=5
DOCUMENT_ALLOWED_EXTENSIONS=.txt,.md,.pdf
DOCUMENT_ALLOWED_MIME_TYPES=text/plain,text/markdown,application/pdf
```

Notas de alcance:

- `BackgroundTasks` no sustituye una cola distribuida.
- El rate limit in-memory no es suficiente para despliegues con multiples replicas.
- El almacenamiento documental actual no es un reemplazo de object storage (S3/GCS).

## Deployment readiness (Fase 8A)

- Backend cloud-ready:
  - usa `PORT` con fallback seguro (`${PORT:-8000}`)
  - endpoint de readiness disponible en `/api/v1/health/ready`
  - CORS configurable por `CORS_ORIGINS` (CSV)
- Frontend cloud-ready:
  - variable recomendada `VITE_API_BASE_URL` para apuntar al backend publico
- Migraciones:
  - en produccion ejecutar `alembic upgrade head`

Guia detallada:

- `docs/DEPLOYMENT_RAILWAY.md`
