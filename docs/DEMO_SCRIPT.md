# Aegis Demo Script (3-5 min)

Goal: show Aegis as a traceable task workflow, not just a chat response.

## Before You Start

Quick checks:

- `docker compose ps` shows healthy services
- frontend available at `http://localhost:5173`
- backend health available at `http://localhost:8000/api/v1/health`
- demo user ready:
  - email: `demo@aegis.local`
  - password: `Demo12345!`

Suggested framing sentence:

> "Aegis is a backend-first AI task orchestration demo. The point is not only to generate text, but to show a full execution workflow with traceability, persistence and review."

## 1. Login (20-30s)

Open `http://localhost:5173/login` and sign in.

What to say:

- "The web session uses a normal product-style auth flow so I can move through tasks, documents and insights as an authenticated user."

What to show:

- login screen
- optional demo credentials
- transition into the application shell

## 2. Dashboard (20-30s)

Land on the dashboard and set the context.

What to say:

- "This view gives me the high-level demo path: tasks, execution, review, document context and insights."

What to show:

- stats cards
- recent tasks
- recommended walkthrough actions

## 3. Create A Task (40-60s)

Go to `Tasks` and create a realistic request.

Recommended example:

- title: `Compare FastAPI and Django for an internal AI platform`
- description: `Provide a practical comparison for an AI orchestration product: architecture, maintainability, performance and implementation speed. End with a recommendation.`

What to say:

- "I start from a structured task, not from a generic chat prompt. That gives the backend enough context to classify, route and persist the workflow."

## 4. Execute The Task (40-60s)

Run the task from the list or detail view.

What to show:

- status transition
- quick execution control
- automatic refresh while the task is queued or processing

What to say:

- "The important part here is not only the final answer. The system tracks execution state and keeps the run reviewable."

## 5. Open Task Detail And Trace (60-90s)

Open the completed task detail.

What to show:

- task overview
- final result
- execution trace
- evaluation block

Call out:

- `task_type`
- `agent_name`
- timestamps and duration
- trace steps such as classification, selection and execution

Suggested sentence:

> "This is where Aegis becomes more than a text demo. I can inspect what happened during the run, not only what the model returned."

## 6. Submit Feedback (20-30s)

Rate the output and optionally leave a short comment.

What to say:

- "The rating step is intentionally lightweight, but it creates a feedback signal that can later be aggregated in Insights."

## 7. Show Documents / Retrieval Context (30-45s)

Open `Documents`.

What to show:

- upload form
- existing document library
- file or text-based ingestion

What to say:

- "Aegis can ingest supporting context so future tasks can run with retrieval-assisted input instead of relying only on the prompt."

Keep the explanation honest:

- no claims of deep semantic evaluation
- no claims of internet browsing

## 8. Show Insights (30-45s)

Open `Insights`.

What to show:

- top metrics
- distribution snapshot
- quality review queue
- strong results section

What to say:

- "This closes the loop. The system does not only execute work; it also surfaces weak and strong runs so the workflow can be reviewed."

## 9. Closing Statement (15-20s)

Suggested close:

> "Aegis is a technical MVP for portfolio and interviews. It demonstrates a full-stack, backend-first AI workflow with task intake, routing, traceability, feedback and operational review."

Optional follow-up sentence:

> "If this moved toward production, the next steps would be stronger observability, a durable queue and deeper runtime validation."

## Demo Checklist

- login works
- dashboard loads
- task gets created
- task executes
- detail view shows result and trace
- feedback is saved
- document library is visible
- insights page reflects quality signals
