# Estrategia De Testing De Aegis

## Objetivo
Maximizar confianza de demo y estabilidad con foco en regresiones críticas sin sobreingeniería.

## Fases de automatización
1. Fase P0: clasificación, selección de agente, calidad de output, pipeline, trace, auth, ownership, seed, contrato task detail, health backend.
2. Fase P1: feedback, insights, upload de documentos, fallback RAG, smoke/build frontend, health frontend en Compose.
3. Fase P2: cobertura de contratos ampliados y escenarios negativos de integración.
4. Fase P3: E2E browser y performance sistemática en CI.

## Comandos recomendados
```bash
docker compose --env-file .env.example config
cd backend && python -m unittest discover -s tests -t . -p "test_*.py" -v
cd ../frontend && npm ci && npm run test && npm run build && npm run check:smoke
docker compose --env-file .env up --build -d
docker compose --env-file .env run --rm backend alembic upgrade head
docker compose --env-file .env run --rm backend python -m scripts.seed_demo_data
```

## Aislamiento LLM en tests
- La suite backend fuerza `LLM_PROVIDER=template` y `LLM_ENABLE_REAL_CALLS=false` desde `backend/tests/__init__.py`.
- Esto evita que los tests dependan del `.env` local y bloquea llamadas reales a OpenRouter durante `unittest discover`.
- La validación real de OpenRouter se realiza de forma manual y controlada en la fase 2.1, nunca en la suite automática.
- Nunca incluir `OPENROUTER_API_KEY` en Git, README o artefactos de test.

## Auth Y Sesión
- La sesión web usa cookie `HttpOnly`; el frontend no debe persistir JWT en `localStorage`.
- Mantener `Authorization: Bearer` solo como compatibilidad de tests/API manual cuando sea necesario.

## Hardening De API Y Producto
- `GET /tasks` y `GET /documents` usan paginación mínima por `limit`/`offset`.
- El rate limiting sigue siendo in-memory en esta fase; se valida como contrato de demo, no como solución distribuida.
- Los formatos documentales soportados en runtime son `.txt`, `.md`, `.csv`, `.json`.

## Reset De Demo Local
```bash
docker compose --env-file .env down -v
docker compose --env-file .env up -d
docker compose --env-file .env run --rm backend alembic upgrade head
docker compose --env-file .env run --rm backend python -m scripts.seed_demo_data
```

## Distribución de la matriz ideal
| Área | Casos |
|---|---|
| A - Boot, health y configuración | 40 |
| B - Auth y usuarios | 80 |
| C - Task CRUD | 90 |
| D - Clasificacion ES/EN | 120 |
| E - Agent selection | 70 |
| F - Agent output quality | 100 |
| G - Execution pipeline | 100 |
| H - Execution trace | 90 |
| I - Feedback y rating | 50 |
| J - Insights | 70 |
| K - Documents upload | 80 |
| L - RAG retrieval | 90 |
| M - API contract backend/frontend | 80 |
| N - Frontend unit/component | 80 |
| O - Frontend e2e/user flows | 90 |
| P - Docker, DevOps y scripts | 60 |
| Q - Security básica | 70 |
| R - Seed y demo data | 40 |
| S - Internacionalizacion y UX copy | 40 |
| T - Regression bugs conocidos | 60 |
| **Total** | **1500** |
