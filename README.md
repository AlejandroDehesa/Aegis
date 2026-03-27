# Aegis

Aegis es una plataforma backend-first para orquestacion de tareas con agentes de IA.

Flujo principal del producto:

`task -> classification -> agent selection -> execution -> structured result -> trace/history`

Aegis no es un chatbot. El foco es ejecucion de tareas con trazabilidad.

## Stack

- Backend: Python + FastAPI + Pydantic + SQLAlchemy 2.0
- DB: PostgreSQL
- Auth: JWT
- IA: OpenAI API (con RAG + memoria en la implementacion actual)
- Frontend: React + Vite (JavaScript)
- Infra: Docker + Docker Compose + Nginx

## Estructura

- `backend/app/`
- `frontend/src/`
- `backend/scripts/` (utilidades de soporte, por ejemplo semilla demo)

## Variables de entorno

### Archivo raiz `.env`

- `PROJECT_NAME`: nombre del backend
- `DATABASE_URL`: conexion PostgreSQL
- `JWT_SECRET_KEY`: secreto de firma JWT
- `JWT_ALGORITHM`: algoritmo JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`: expiracion de token
- `OPENAI_API_KEY`: clave OpenAI
- `OPENAI_MODEL`: modelo de chat
- `OPENAI_EMBEDDING_MODEL`: modelo de embeddings
- `FRONTEND_ORIGINS`: CORS permitidos (coma-separado)
- `VITE_API_URL`: base URL para build del frontend (`/api/v1` recomendado)

### Archivo `frontend/.env`

- `VITE_API_URL`: base URL del API para el frontend
- `VITE_DEV_PROXY_TARGET`: target del proxy en `vite dev` (default `http://localhost:8000`)

## Arranque rapido (Docker)

1. Copiar variables:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

2. Levantar servicios:

```bash
docker compose up --build
```

3. Endpoints:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`

## Arranque local (dev)

### 1) Base de datos

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

Con la configuracion actual, el frontend usa `VITE_API_URL=/api/v1` y Vite hace proxy a `VITE_DEV_PROXY_TARGET`.

## Flujo de demo recomendado

1. Login o registro.
2. Crear tarea en `/tasks`.
3. Ejecutar tarea y observar estados (`pending`, `processing`, `completed`, `failed`).
4. Abrir detalle para ver resultado y `Execution Trace`.
5. Ir a `/documents` y cargar contenido.
6. Ejecutar nueva tarea para usar contexto RAG.
7. Revisar `Debug Context` (ejecucion con debug).

## Semilla demo (opcional)

Script simple para crear usuario demo y tareas de ejemplo (idempotente):

```bash
cd backend
python scripts/seed_demo_data.py
```

Credenciales demo generadas por el script:

- `demo@aegis.local`
- `Demo12345!`

## Hardening aplicado en frontend

- Manejo consistente de token invalido/expirado
- Limpieza automatica de sesion
- Sincronizacion de sesion entre pestanas
- Manejo global de errores API
- Estados UI consistentes (`loading`, `empty`, `error`, `success`)

## Notas de despliegue

- Nginx sirve frontend y hace proxy de `/api/*` a backend (`backend:8000`) en Compose.
- CORS backend se controla con `FRONTEND_ORIGINS`.
- Mantener `VITE_API_URL=/api/v1` simplifica local, demo y despliegue.
