# Aegis Interview Notes

## What Is Aegis

Aegis is a backend-first AI task orchestration project built to demonstrate a full workflow instead of a one-shot chat response.

The main story is:

- structured task intake
- classification
- agent selection
- execution
- persisted trace
- feedback
- insights

That makes it a stronger portfolio piece than a simple CRUD or chatbot UI.

## How I Explain The Architecture

### Backend

- FastAPI exposes endpoints for auth, tasks, documents, insights, agents and health.
- Services handle orchestration concerns such as classification, routing, execution and document-context support.
- SQLAlchemy models persist tasks, documents and execution metadata.
- Pydantic schemas define the API contract and validation layer.

### Frontend

- React + Vite provides the authenticated product workflow.
- The main views are dashboard, tasks, task detail, documents and insights.
- Shared components handle async states, layout, feedback messages and trace rendering.

### Data Flow

```txt
user creates task
  -> backend classifies request
  -> selects agent
  -> executes task
  -> persists result + trace
  -> user reviews output
  -> user submits feedback
  -> insights aggregates quality signals
```

## Why It Is Not Just A CRUD

A CRUD app stores records. Aegis does more than that:

- it routes work by task type
- it tracks execution state over time
- it stores step-by-step trace information
- it supports lightweight quality review
- it uses document context to enrich future runs

That combination creates a workflow story, not just forms and tables.

## Why FastAPI

- clean developer experience
- fast iteration speed
- strong fit for typed request/response contracts
- easy to structure around services and routers
- a good match for backend-heavy portfolio work

## Why React + Vite

- quick setup without overcomplicating the frontend
- strong iteration speed for product screens
- easy to keep the UI focused on workflow instead of framework ceremony
- enough flexibility for stateful pages like tasks, trace review and insights

## Why HttpOnly Cookies For The Web Session

- they reduce the exposure of session tokens to browser-side JavaScript
- they fit a more realistic product auth model than storing JWTs in `localStorage`
- they make the portfolio story stronger from a security perspective

I still keep Bearer compatibility for manual API work and tests, but the web flow is cookie-based.

## Why Alembic

- schema changes should be explicit and reviewable
- migration history is easier to reason about than runtime DDL
- it is the correct step away from demo shortcuts toward professional repo hygiene

## Why Not Celery Yet

- the current goal is a solid portfolio MVP, not a distributed job platform
- `BackgroundTasks` is enough to demonstrate workflow state transitions and traceability
- adding Celery or Redis right now would increase operational complexity more than demo value

If I were preparing for production-like workloads, a durable queue would be the next step.

## Why Rate Limiting Is Still In-Memory

- it was enough for local demos and a single-instance portfolio scope
- it keeps the implementation simple and easy to explain
- it is also a good example of an intentional limitation I would revisit before multi-instance deployment

## How I Explain The RAG Layer Honestly

- users can upload documents
- documents are chunked and stored for retrieval-oriented context
- future tasks can use that context during execution

Important honesty points:

- this is an MVP RAG workflow
- it is not presented as a deeply evaluated retrieval system
- it does not pretend to browse the internet or fabricate external sources

## Tradeoffs I Made

- kept the architecture layered, but not over-engineered
- prioritized traceability and workflow clarity over autonomous-agent complexity
- hardened auth/config/docs before chasing advanced production infra
- accepted in-memory rate limiting and non-durable background work as portfolio-scope tradeoffs

## What I Learned Building It

- "completed" is not the same as "useful" without output quality checks
- execution trace changes how debuggable and reviewable the system feels
- honest limitations make a project stronger in interviews
- docs, test flows and demo clarity matter almost as much as the code for portfolio impact

## What I Would Improve Before Production

- durable background execution
- distributed rate limiting
- stronger observability and alerting
- browser E2E coverage
- deeper RAG evaluation and retrieval monitoring
- real deployment validation with daemon/runtime checks

## Short Interview Pitch

> "Aegis is a backend-first AI task orchestration project. Instead of stopping at prompt and response, it shows classification, routing, execution trace, feedback and insights inside a real product workflow."

## Longer Interview Pitch

> "I built Aegis to demonstrate how an AI-assisted workflow looks when you treat it like product software. A user creates a structured task, the backend classifies it, selects an execution path, persists the result and trace, then the UI supports feedback and insights. It is not marketed as fully production-ready, but it is intentionally hardened enough to be a serious portfolio project."
