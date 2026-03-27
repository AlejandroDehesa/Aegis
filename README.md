# Aegis

Aegis es una plataforma backend-first para orquestar tareas con agentes de IA:

`tarea -> clasificacion -> seleccion de agente -> ejecucion -> resultado -> historial/traza`

No es un chatbot. El backend es el nucleo y el frontend expone un flujo serio de ejecucion.

## Stack

- Backend: Python + FastAPI + SQLAlchemy 2.0 + Pydantic
- Base de datos: PostgreSQL
- Auth: JWT
- IA: OpenAI API
- Frontend: React + Vite (JavaScript)
- Infra: Docker + Docker Compose

## Estructura

- `backend/app/` API, dominio, servicios, agentes, modelos y esquemas
- `frontend/src/` api, pages, components, hooks, context, router y estilos

## Configuracion por entorno

1. Copia variables base:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

2. Revisa variables clave:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- `FRONTEND_ORIGINS`
- `VITE_API_URL` (debe apuntar al backend con prefijo `/api/v1`)

## Arranque rapido con Docker

Desde la raiz:

```bash
docker compose up --build
```

Servicios:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5432`

Health check:

- `GET http://localhost:8000/api/v1/health`

## Arranque local (sin docker para frontend)

### 1) Backend (con DB en Docker)

```bash
docker compose up -d db
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

## Flujo de demo recomendado

1. Login/registro.
2. Crear una tarea en `/tasks`.
3. Ejecutar la tarea (boton `Execute`) y observar estados (`pending/processing/completed`).
4. Abrir detalle de tarea para revisar resultado y `Execution Trace`.
5. Ir a `/documents`, subir uno o varios documentos.
6. Ejecutar una tarea con contexto documental para ver enriquecimiento RAG.
7. Revisar `Debug Context` en detalle de tarea (si se ejecuto con debug).

## Notas de despliegue base

- El frontend usa `VITE_API_URL` para resolver backend sin URLs hardcodeadas.
- El backend aplica CORS via `FRONTEND_ORIGINS`.
- El contenedor frontend sirve build estatico via Nginx con fallback SPA (`/index.html`).

## Estado del proyecto

Base funcional para portfolio:

- auth + usuarios
- tareas + ejecucion multi-agente
- resultados persistidos + trazabilidad
- documentos + RAG/memoria
- frontend integrado con feedback operativo
