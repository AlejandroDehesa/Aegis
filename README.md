# Aegis

Aegis es una plataforma backend-first para orquestacion de tareas con agentes de IA.

No es un chatbot. El foco del producto es ejecutar trabajo real con trazabilidad:

`task -> classification -> agent selection -> execution -> result -> trace -> quality feedback -> operational insights`

## Problema que resuelve

La mayoria de demos de IA muestran solo prompts y respuestas. Aegis muestra un flujo mas profesional:

- entrada de tarea estructurada
- enrutamiento por tipo de tarea
- ejecucion con agentes
- persistencia de resultados y traza
- evaluacion ligera de calidad por tarea

Esto permite demostrar criterio de producto, arquitectura y operacion, no solo integracion basica de LLM.

## Arquitectura

### Backend (`backend/app/`)

- `api/`: endpoints REST (auth, tasks, documents, agents, insights, health)
- `core/`: config, seguridad, base de datos
- `models/`: entidades SQLAlchemy
- `schemas/`: contratos Pydantic
- `services/`: clasificacion, seleccion de agente, ejecucion, RAG/memoria
- `agents/`: implementaciones de agentes

### Frontend (`frontend/src/`)

- `pages/`: dashboard, insights, tasks, task detail, documents, agents, auth
- `api/`: cliente HTTP centralizado + wrappers por recurso
- `context/` y `hooks/`: auth, polling, estado compartido
- `components/`: layout, estados async, badges, cards, feedback
- `styles/`: estilo global y consistencia visual

## Stack

- Backend: Python + FastAPI + Pydantic + SQLAlchemy 2.0
- DB: PostgreSQL
- Auth: JWT
- IA: OpenAI API + RAG + memoria ligera
- Frontend: React + Vite (JavaScript)
- Infra: Docker + Docker Compose + Nginx

## Flujo end-to-end

1. Usuario autenticado crea tarea.
2. Backend clasifica tipo de tarea.
3. Backend selecciona agente adecuado.
4. Se ejecuta pipeline y se guarda resultado.
5. Se persiste traza de ejecucion por pasos.
6. Usuario revisa resultado y traza.
7. Usuario envia evaluacion de calidad (rating + comentario).
8. Usuario revisa distribuciones y quality queue en Insights.

## Demo flow recomendado (5-7 min)

1. Login (o usar usuario demo seed).
2. Ir a `Tasks` y crear tarea con el template de demo.
3. Ejecutar tarea y mostrar cambio de estados con polling.
4. Abrir `Task Detail` y revisar resultado + execution trace + feedback.
5. Enviar evaluacion de resultado (rating + comentario opcional).
6. Ir a `Insights` para revisar quality queue (failed o low-rated).
7. Ir a `Documents`, subir contexto y volver a ejecutar una tarea.
8. Mostrar en `Dashboard` el estado global del flujo.

## Guia de usuario

Para onboarding completo de un usuario nuevo (navegacion, flujo de trabajo y troubleshooting):

- `GUIA_USUARIO_NUEVO.md`
- Estrategia de testing por fases: `docs/TESTING_STRATEGY.md`
- Matriz ideal de cobertura (1500 casos): `docs/TEST_MATRIX_1000.md`

## Operational insights y quality review

Aegis ahora incluye una capa ligera de analisis operativo por usuario autenticado:

- metricas base por usuario (`total`, distribucion por status, task_type, agent_name, feedback_rating)
- quality queue para detectar tareas fallidas o mal valoradas rapidamente
- filtros de revision en `Tasks` por `status`, `task_type`, `agent_name`, `feedback_rating`

Endpoints relevantes:

- `GET /api/v1/insights/overview`
- `GET /api/v1/tasks?status=&task_type=&agent_name=&feedback_rating=`

## Arranque rapido

### Docker

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose up --build
```

URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`

### Local dev

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

## Variables de entorno

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

## Demo seed (opcional)

```bash
cd backend
python -m scripts.seed_demo_data
```

Credenciales seed:

- email: `demo@aegis.local`
- password: `Demo12345!`

## Reset demo local (limpio)

```bash
docker compose down -v
docker compose up -d
docker compose run --rm backend python -m scripts.seed_demo_data
```

## Testing y release confidence

### Backend tests (unit)

```bash
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

Cobertura objetivo del bloque de estabilidad:

- auth (signup/login/me)
- tasks (create/list con filtros)
- execute (happy path y errores de estado)
- feedback (persistencia y validaciones)
- insights (agregaciones por usuario)
- flujo critico encadenado (create -> execute -> trace -> feedback -> insights)

### Frontend checks minimos

```bash
cd frontend
npm run check:smoke
npm run build
```

`npm run test` no esta configurado actualmente en el frontend. La validacion actual para estabilidad visual/estructura se basa en `check:smoke` + `build`.

`check:smoke` valida presencia de flujo critico en UI:

- login
- carga de tareas
- detalle de tarea
- feedback
- ruta insights y navegacion

### Docker health/release check

```bash
docker compose config
docker compose up --build
```

Validar luego:

- `GET /api/v1/health`
- login con seed demo
- create/execute task
- task detail + trace + feedback
- insights overview y quality queue

## Highlights tecnicos para entrevista

- Arquitectura backend-first con responsabilidades separadas
- Orquestacion multi-agente con visibilidad de ejecucion
- Persistencia de historial y trazas estructuradas
- RAG + memoria para enriquecer contexto de ejecucion
- Evaluacion ligera de calidad para cerrar loop de producto
- Insights operativos y quality review por usuario
- UX consistente de estados (`loading`, `empty`, `error`, `success`)
- Packaging de demo reproducible con Docker/Nginx

## Notas de despliegue

- Nginx sirve frontend y proxya `/api/*` al backend en Compose
- CORS controlado por `FRONTEND_ORIGINS`
- Healthchecks en db/backend/frontend para arranque mas estable

## Showcase (sugerencia de capturas)

- Dashboard con KPI y demo flow
- Task detail con resultado + trace + evaluacion
- Documents con ingestion y flujo RAG
