# Aegis

Aegis es una plataforma backend-first para orquestacion de tareas con agentes de IA.

No es un chatbot. El foco del producto es ejecutar trabajo real con trazabilidad:

`task -> classification -> agent selection -> execution -> result -> trace -> quality feedback`

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

- `api/`: endpoints REST (auth, tasks, documents, agents, health)
- `core/`: config, seguridad, base de datos
- `models/`: entidades SQLAlchemy
- `schemas/`: contratos Pydantic
- `services/`: clasificacion, seleccion de agente, ejecucion, RAG/memoria
- `agents/`: implementaciones de agentes

### Frontend (`frontend/src/`)

- `pages/`: dashboard, tasks, task detail, documents, agents, auth
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

## Demo flow recomendado (5-7 min)

1. Login (o usar usuario demo seed).
2. Ir a `Tasks` y crear tarea con el template de demo.
3. Ejecutar tarea y mostrar cambio de estados con polling.
4. Abrir `Task Detail` y revisar:
   - resultado
   - execution trace
   - debug context (si aplica)
5. Enviar evaluacion de resultado (rating + comentario opcional).
6. Ir a `Documents`, subir contexto y volver a ejecutar una tarea.
7. Mostrar en `Dashboard` metricas, rated tasks y avg rating.

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
python scripts/seed_demo_data.py
```

Credenciales seed:

- email: `demo@aegis.local`
- password: `Demo12345!`

## Highlights tecnicos para entrevista

- Arquitectura backend-first con responsabilidades separadas
- Orquestacion multi-agente con visibilidad de ejecucion
- Persistencia de historial y trazas estructuradas
- RAG + memoria para enriquecer contexto de ejecucion
- Evaluacion ligera de calidad para cerrar loop de producto
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
