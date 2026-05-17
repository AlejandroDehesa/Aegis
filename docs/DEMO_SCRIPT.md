# Aegis Demo Script (3-5 min)

Objetivo: mostrar que Aegis es una plataforma de orquestacion de tareas con agentes, no un simple chatbot.

## 0) Preparacion (30s)

Verificar rapidamente:

- `docker compose ps` en estado healthy
- frontend en `http://localhost:5173`
- backend health en `http://localhost:8000/api/v1/health`

## 1) Login y contexto (30s)

1. Abrir `http://localhost:5173/login`.
2. Entrar con:
   - email: `demo@aegis.local`
   - password: `Demo12345!`
3. Frase sugerida:
   - "Aegis ejecuta tareas con trazabilidad completa; no es un chat de respuesta unica."

## 2) Crear y ejecutar tarea comparison (60-90s)

Crear tarea:

- Title: `Compara FastAPI y Django`
- Description: `Compara FastAPI y Django para crear una API backend moderna. Dame ventajas, desventajas y recomendacion final.`

Ejecutar tarea desde `Tasks`.

Puntos a remarcar:

- `task_type = comparison`
- `agent_name = ComparisonAgent`
- status cambia y termina en `completed`

## 3) Abrir Task Detail y mostrar trace (60-90s)

Abrir el detalle de esa tarea.

Mostrar:

- resultado util (no placeholder)
- trace con pasos:
  - `classification`
  - `agent_selection`
  - `execution`
- metadata de ejecucion (timestamps, duracion)

Frase sugerida:

- "Aqui se ve el pipeline completo y no solo una salida de texto."

## 4) Feedback + Insights (45-60s)

1. Enviar rating (por ejemplo 5) y comentario corto.
2. Ir a `Insights`.
3. Mostrar:
   - metricas por estado
   - distribucion por tipo/agent
   - quality queue (si hay fallidas o low-rated)

## 5) Documents (30-45s)

1. Ir a `Documents`.
2. Mostrar carga de documento o libreria existente.
3. Frase sugerida:
   - "El sistema permite enriquecer tareas futuras con contexto documental."

## 6) Cierre (15-20s)

Mensaje final recomendado:

- "Aegis es un MVP tecnico estable: clasifica tareas, selecciona agente, ejecuta, traza, recoge feedback y consolida insights."

## Checklist rapido de demo

- Login OK
- Crear tarea OK
- Ejecutar tarea OK
- Detail + Trace OK
- Feedback OK
- Insights OK
- Documents OK
