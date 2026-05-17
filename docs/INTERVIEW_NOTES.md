# Aegis Interview Notes

## 1) Que es Aegis

Aegis es una plataforma backend-first para orquestar tareas con agentes IA y trazabilidad de ejecucion.

## 2) Por que no es un chatbot

Un chatbot suele terminar en prompt/respuesta.  
Aegis trabaja con flujo de tarea persistido:

- task input estructurado
- clasificacion
- seleccion de agente
- ejecucion
- resultado
- trace
- feedback
- insights

## 3) Como funciona el backend

El backend (FastAPI) expone endpoints de:

- auth (`signup`, `login`, `me`)
- tasks (`create`, `list`, `detail`, `execute`, `feedback`, `trace`)
- documents (`upload`, `list`, `delete`)
- insights (`overview`)
- health

La logica de dominio esta en servicios (`classifier`, `selector`, `orchestrator`, `executor`, `rag/memory`).

## 4) Como funciona la clasificacion

La clasificacion usa reglas por keywords con normalizacion de texto (case/acentos/simbolos).

Tipos principales:

- comparison
- summary
- research
- analysis
- planning
- general

Prioriza evitar falsos "general" en casos obvios.

## 5) Como se seleccionan agentes

`task_type` se mapea a un agente catalogado:

- comparison -> ComparisonAgent
- summary -> SummaryAgent
- research -> ResearchAgent
- analysis -> AnalysisAgent
- planning -> PlanningAgent
- general -> GeneralAssistantAgent

Si hay tipo desconocido, fallback seguro a general.

## 6) Como se guarda la execution trace

Cada ejecucion persiste pasos estructurados:

- `step_name`
- `agent_name`
- `status`
- `short_summary`
- timestamps y duracion cuando aplica

Ademas se mantiene compatibilidad con formatos legacy para evitar roturas en lectura.

## 7) Como se validan resultados

Antes de marcar `completed`, hay quality gate basico:

- output no vacio
- longitud minima razonable
- bloqueo de lenguaje placeholder (ej. "future expansion", "stub", "TODO")
- checks de contenido minimo por tipo (comparison/analysis/planning)

Si falla, la tarea se marca `failed`.

## 8) Como se testea

Backend:

- `unittest` con cobertura critica de auth, tasks, classification, agent selection, output quality, execution trace, seed, insights, documents/RAG basico.

Frontend:

- Vitest + React Testing Library para unit/component minimo:
  - ProtectedRoute
  - AuthPage
  - TasksPage
  - TaskDetailPage
  - InsightsPage
  - DocumentsPage

Apoyos:

- `npm run build`
- `npm run check:smoke`
- Docker healthchecks

## 9) Que aprendi construyendolo

- Que "status=completed" no implica valor real si no hay quality checks.
- Que la trazabilidad operativa (trace + feedback + insights) cambia la calidad percibida del producto.
- Que small, explicit architecture decisions dan estabilidad sin sobreingenieria.

## 10) Que mejoraria en produccion

- e2e browser tests (Playwright/Cypress) para flujos completos.
- observabilidad mas fuerte (structured logs, metrics, alerting).
- hardening de seguridad y politicas de rate limiting.
- evaluacion mas profunda de calidad RAG/retrieval.

## 11) Mensaje corto para recruiter

"Aegis es un MVP tecnico de orquestacion de tareas IA con ejecucion trazable, calidad validada y demo reproducible en Docker. No pretende ser enterprise-ready, pero si una base solida y profesional."
