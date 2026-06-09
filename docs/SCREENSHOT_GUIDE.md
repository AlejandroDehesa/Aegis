# Aegis Screenshot Guide

Use this guide to capture consistent, portfolio-ready screenshots once the demo data is available locally.

Do not create fake screenshots. Only capture the real running UI.

## General Rules

- Use a clean browser window.
- Prefer desktop width around `1440px`.
- Keep the UI in a single language for the whole README set.
- Use realistic demo data, not lorem ipsum.
- Avoid exposing local file paths, secrets, browser extensions or unrelated tabs.
- Keep the sidebar visible unless the screenshot would be clearer without it.
- Save images as `.png`.

Recommended size:

- `1440x900` or `1600x1000`

Recommended folder:

- `docs/screenshots/`

## 1. Login

- File name: `login.png`
- What should be visible:
  - hero panel
  - login form
  - optional demo credentials note
- Demo data:
  - `demo@aegis.local`
- Do not show:
  - typed password in plain view
  - browser password managers

## 2. Dashboard

- File name: `dashboard.png`
- What should be visible:
  - stats cards
  - recommended demo flow
  - recent tasks
- Demo data:
  - at least 3 seeded tasks
  - at least 1 rated task
- Do not show:
  - empty dashboard unless the README explicitly discusses empty-state UX

## 3. Tasks List

- File name: `tasks-list.png`
- What should be visible:
  - task list
  - status badges
  - timing / rating pills
  - quick actions
- Demo data:
  - one completed task
  - one processing or queued task if possible
  - one failed or unrated task if possible
- Do not show:
  - unrealistic or repetitive task titles

## 4. Create Task

- File name: `create-task.png`
- What should be visible:
  - create task form
  - realistic task title and description
- Demo data:
  - example title: `Compare FastAPI and Django for an internal AI platform`
  - example description focused on architecture, maintainability and speed
- Do not show:
  - empty placeholder-only form if you can avoid it

## 5. Task Detail With Result And Trace

- File name: `task-detail-trace.png`
- What should be visible:
  - task summary
  - final result
  - execution trace
  - evaluation block
- Demo data:
  - a completed task with a useful result
  - trace entries for classification, selection and execution
- Do not show:
  - placeholder output
  - collapsed debug-only content as the main focus

## 6. Documents Upload And Library

- File name: `documents-library.png`
- What should be visible:
  - upload panel
  - existing document list
  - chunk count or source metadata
- Demo data:
  - one architecture note
  - one product or deployment note
- Do not show:
  - local absolute file paths
  - unsupported file types

## 7. Insights

- File name: `insights.png`
- What should be visible:
  - top metrics
  - distribution snapshot
  - quality review queue or strong results
- Demo data:
  - at least one rated task
  - ideally one weak and one strong output
- Do not show:
  - all-zero cards if you can avoid them

## 8. Optional Health Or CI

- File name: `health-or-ci.png`
- What should be visible:
  - health endpoint response, or
  - GitHub Actions green checks if already available
- Demo data:
  - only real local output or real repository CI
- Do not show:
  - redacted fake dashboards
  - unrelated terminal noise

## Final Check Before Publishing

- Confirm all screenshots match the final README wording.
- Check that file names match the README image paths exactly.
- Open the rendered `README.md` in GitHub preview and verify image layout.
