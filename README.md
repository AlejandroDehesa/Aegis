# Aegis

**Aegis** es una plataforma full-stack de orquestación de tareas con IA, diseñada con enfoque **backend-first**, trazabilidad de ejecución, contexto documental y resultados revisables.

A diferencia de una demo basada únicamente en `prompt -> respuesta`, Aegis modela un flujo más cercano a un producto real:

```txt
tarea
  -> clasificación
  -> selección de agente
  -> ejecución
  -> persistencia de resultado y traza
  -> feedback
  -> insights
```

El proyecto está planteado como un **MVP técnico desplegado**, con una arquitectura pensada para ser clara, modular y evolutiva.

---

## Índice

* [Qué es Aegis](#qué-es-aegis)
* [Problema que aborda](#problema-que-aborda)
* [Capturas](#capturas)
* [Funcionalidades principales](#funcionalidades-principales)
* [Stack técnico](#stack-técnico)
* [Arquitectura](#arquitectura)
* [Flujo de ejecución](#flujo-de-ejecución)
* [Calidad y trazabilidad](#calidad-y-trazabilidad)
* [RAG y documentos](#rag-y-documentos)
* [Seguridad aplicada](#seguridad-aplicada)
* [Ejecución local](#ejecución-local)
* [Tests](#tests)
* [Variables de entorno](#variables-de-entorno)
* [Documentación adicional](#documentación-adicional)
* [Decisiones técnicas destacadas](#decisiones-técnicas-destacadas)
* [Limitaciones conocidas](#limitaciones-conocidas)
* [Roadmap](#roadmap)
* [Autor](#autor)

---

## Qué es Aegis

Aegis es una aplicación full-stack que permite crear, ejecutar y revisar tareas asistidas por IA dentro de un flujo controlado.

La aplicación permite:

* crear tareas estructuradas;
* clasificar automáticamente el tipo de solicitud;
* seleccionar un agente o pipeline de ejecución;
* ejecutar la tarea mediante una capa de IA configurable;
* persistir resultado, estado y trazabilidad;
* revisar la salida generada;
* enviar feedback de calidad;
* consultar insights operativos;
* usar documentos como contexto adicional mediante RAG.

El objetivo técnico del proyecto es demostrar cómo integrar IA en una aplicación real sin reducirlo todo a una caja de chat.

---

## Problema que aborda

Muchas integraciones de IA se limitan a enviar un prompt a un modelo y mostrar una respuesta.

Aegis propone un enfoque más estructurado:

```txt
entrada estructurada
  -> lógica backend
  -> clasificación
  -> ejecución trazable
  -> resultado revisable
  -> feedback
  -> métricas
```

Esto permite trabajar aspectos importantes en aplicaciones con IA:

* control del flujo de ejecución;
* trazabilidad de cada paso;
* validación mínima de calidad;
* persistencia de resultados;
* separación entre frontend, backend, agentes y servicios;
* integración documental mediante recuperación de contexto;
* evolución futura hacia colas, observabilidad y evaluaciones más avanzadas.

---

## Capturas

### Login

![Login](docs/screenshots/login.png)

### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

### Crear tarea

![Crear tarea](docs/screenshots/create-task.png)

### Listado de tareas

![Listado de tareas](docs/screenshots/tasks-list.png)

### Detalle de tarea con resultado y traza

![Detalle de tarea](docs/screenshots/task-detail-trace.png)

### Biblioteca documental

![Documentos](docs/screenshots/documents-library.png)

### Insights

![Insights](docs/screenshots/insights.png)

---

## Funcionalidades principales

* Registro e inicio de sesión.
* Sesión web mediante cookie `HttpOnly`.
* Creación, listado, detalle y ejecución de tareas.
* Clasificación automática del tipo de tarea.
* Selección de agente o pipeline según la tarea.
* Integración con proveedor LLM configurable.
* Ejecución con estados, timestamps y duración.
* Persistencia de resultado y traza de ejecución.
* Quality gate básico para evitar salidas vacías o incompletas.
* Feedback del usuario sobre la respuesta generada.
* Vista de insights para revisar señales de calidad y operación.
* Subida de documentos.
* Contexto documental mediante RAG.
* Migraciones versionadas con Alembic.
* Tests backend y frontend.
* Despliegue separado de backend y frontend.

---

## Stack técnico

| Capa             | Tecnología                              |
| ---------------- | --------------------------------------- |
| Backend          | Python, FastAPI, Pydantic               |
| ORM              | SQLAlchemy 2.x                          |
| Base de datos    | PostgreSQL                              |
| Migraciones      | Alembic                                 |
| Frontend         | React, Vite                             |
| Autenticación    | JWT + cookie `HttpOnly`                 |
| IA               | OpenRouter / proveedor LLM configurable |
| RAG              | PostgreSQL + pgvector                   |
| Infraestructura  | Docker, Docker Compose, Nginx           |
| Testing backend  | `unittest`                              |
| Testing frontend | Vitest, React Testing Library           |
| Deploy           | Railway                                 |

---

## Arquitectura

### Backend

El backend está organizado por capas para separar responsabilidades:

```txt
backend/app/
  api/          -> endpoints REST
  core/         -> configuración, seguridad y base de datos
  models/       -> modelos SQLAlchemy
  schemas/      -> contratos Pydantic
  services/     -> lógica de negocio y orquestación
  agents/       -> agentes especializados
```

Responsabilidades principales:

* `api/`: expone rutas de auth, tasks, documents, agents, insights y health.
* `services/`: contiene clasificación, selección de agente, ejecución, RAG y lógica de tareas.
* `models/`: define las entidades persistidas con SQLAlchemy.
* `schemas/`: valida entradas y salidas de API mediante Pydantic.
* `core/`: centraliza configuración, seguridad, sesión y conexión a base de datos.
* `agents/`: contiene la lógica de agentes especializados.

### Frontend

El frontend está diseñado como una aplicación de producto simple y funcional:

```txt
frontend/src/
  pages/        -> vistas principales
  components/   -> componentes reutilizables
  context/      -> contexto de autenticación
  hooks/        -> hooks de estado y polling
  api/          -> cliente HTTP
```

Vistas principales:

* Login.
* Dashboard.
* Tareas.
* Detalle de tarea.
* Documentos.
* Insights.

### Runtime

```txt
frontend
  -> React + Vite
  -> Nginx

backend
  -> FastAPI
  -> SQLAlchemy
  -> Alembic

database
  -> PostgreSQL
  -> pgvector
```

---

## Flujo de ejecución

Cuando un usuario crea y ejecuta una tarea, Aegis sigue este flujo:

```txt
1. El usuario crea una tarea.
2. El backend valida la entrada.
3. El sistema clasifica el tipo de tarea.
4. Se selecciona el agente o pipeline adecuado.
5. Se recupera contexto documental si aplica.
6. El agente ejecuta la tarea.
7. Se genera un resultado.
8. Se valida la calidad mínima de la salida.
9. Se persiste el resultado.
10. Se guarda la traza de ejecución.
11. El usuario revisa y valora la salida.
12. Insights agrega señales de calidad y operación.
```

La traza de ejecución permite inspeccionar qué ocurrió durante la tarea, no solo ver el resultado final.

---

## Calidad y trazabilidad

Aegis incorpora una capa básica de control de calidad para evitar que una tarea aparezca como completada si la salida no cumple unos mínimos.

Ejemplos de validación:

* salida vacía;
* salida demasiado corta;
* respuestas genéricas;
* placeholders;
* ausencia de partes obligatorias según el tipo de tarea;
* falta de recomendación en tareas comparativas;
* falta de estructura mínima en tareas de planificación o análisis.

Esto permite diferenciar entre una ejecución técnicamente completada y una salida realmente útil.

---

## RAG y documentos

Aegis permite subir documentos para aportar contexto a futuras ejecuciones.

Flujo documental:

```txt
documento
  -> validación
  -> almacenamiento
  -> división en chunks
  -> generación o almacenamiento de embeddings
  -> recuperación de contexto
  -> uso durante la ejecución de tareas
```

El sistema RAG actual está planteado como una implementación de nivel MVP. Su objetivo es demostrar el flujo de recuperación y uso de contexto documental dentro de una aplicación completa.

---

## Seguridad aplicada

Aegis incluye medidas de hardening razonables para un MVP técnico:

* sesión web mediante cookie `HttpOnly`;
* abandono de `localStorage` para el token de sesión;
* compatibilidad Bearer para tests y uso manual de API;
* validación de variables sensibles;
* `.env.example` seguro con placeholders;
* separación entre configuración local y producción;
* headers HTTP básicos de seguridad;
* validaciones de entrada en tareas, feedback y documentos;
* paginación en endpoints principales;
* migraciones explícitas con Alembic;
* eliminación de mutación de esquema en runtime normal.

---

## Ejecución local

### Requisitos

* Python 3.12+
* Node.js 20+
* Docker
* Docker Compose

### Ejecución con Docker

```bash
cp .env.example .env
docker compose --env-file .env up --build -d
docker compose --env-file .env run --rm backend alembic upgrade head
```

URLs principales:

```txt
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Health:   http://localhost:8000/api/v1/health
```

### Backend y frontend en local

Levantar base de datos:

```bash
docker compose --env-file .env up -d db
```

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:AEGIS_ENV_FILE=".env"
python -m alembic -c ..\alembic.ini upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## Tests

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

### Validación de Docker Compose

```bash
docker compose --env-file .env.example config
```

---

## Seed de demo

Para cargar usuario demo y datos de ejemplo:

```bash
docker compose --env-file .env run --rm backend alembic upgrade head
docker compose --env-file .env run --rm backend python -m scripts.seed_demo_data
```

---

## Variables de entorno

Los secretos reales deben vivir solo en `.env` local o en el panel de variables del proveedor cloud.

No deben subirse al repositorio.

Variables principales:

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
LLM_MAX_TOKENS=2000
```

Plantilla de referencia:

```txt
.env.example
```

---

## Documentación adicional

| Documento                    | Descripción                              |
| ---------------------------- | ---------------------------------------- |
| `GUIA_USUARIO_NUEVO.md`      | Guía de uso del proyecto                 |
| `docs/DEMO_SCRIPT.md`        | Guion de demo                            |
| `docs/INTERVIEW_NOTES.md`    | Notas técnicas y decisiones del proyecto |
| `docs/SCREENSHOT_GUIDE.md`   | Guía para capturas consistentes          |
| `docs/TESTING_STRATEGY.md`   | Estrategia de testing                    |
| `docs/DEPLOYMENT_RAILWAY.md` | Notas de despliegue en Railway           |

---

## Decisiones técnicas destacadas

Aegis está construido con una serie de decisiones pensadas para mantener el proyecto simple, trazable y evolutivo:

* enfoque **backend-first** para priorizar la lógica de negocio y la orquestación;
* separación por capas entre API, servicios, modelos, schemas, agentes y configuración;
* uso de migraciones con Alembic como fuente de verdad del esquema;
* autenticación web mediante cookie `HttpOnly`;
* integración con proveedor LLM externo a través de una capa configurable;
* trazabilidad persistida para revisar qué ocurre durante cada ejecución;
* quality gate básico para evitar resultados vacíos o incompletos;
* documentación explícita de limitaciones y tradeoffs.

---

## Valor técnico del proyecto

Aegis demuestra la construcción de una aplicación full-stack con IA aplicada más allá de una simple interfaz de chat.

El proyecto integra:

* API REST con FastAPI;
* persistencia con PostgreSQL y SQLAlchemy;
* migraciones versionadas con Alembic;
* frontend funcional con React y Vite;
* autenticación basada en sesión web;
* ejecución de tareas con estado;
* agentes especializados;
* contexto documental mediante RAG;
* validación de calidad de resultados;
* testing backend y frontend;
* despliegue cloud con Railway.

El objetivo no es presentar una plataforma enterprise final, sino una base técnica sólida, desplegada y preparada para evolucionar.

---

## Limitaciones conocidas

Aegis documenta sus limitaciones de forma explícita:

* no es una plataforma enterprise completamente lista para producción;
* `FastAPI BackgroundTasks` no sustituye a una cola durable como Celery, RQ o BullMQ;
* el rate limiting actual es in-memory;
* no existe todavía una suite E2E completa de navegador;
* RAG está en nivel MVP y no tiene evaluación semántica profunda;
* la observabilidad es básica;
* el manejo documental está pensado para demo y evolución técnica, no para almacenamiento enterprise a gran escala.

Estas limitaciones forman parte de las decisiones técnicas actuales y marcan una evolución natural hacia producción.

---

## Roadmap

Posibles mejoras futuras:

* añadir suite E2E con Playwright o Cypress;
* evolucionar ejecución background hacia una cola durable;
* incorporar observabilidad avanzada;
* mejorar evaluación de calidad de respuestas;
* ampliar métricas de uso y coste LLM;
* reforzar permisos y roles de usuario;
* mejorar evaluación de retrieval en RAG;
* preparar despliegue production-like más completo.

---

## Estado del proyecto

```txt
Estado: MVP técnico desplegado.
Objetivo: demostrar arquitectura, trazabilidad, integración IA y criterio técnico.
Producción enterprise: fuera de alcance en esta versión.
```

---

## Autor

Desarrollado por **Alejandro Dehesa**.
