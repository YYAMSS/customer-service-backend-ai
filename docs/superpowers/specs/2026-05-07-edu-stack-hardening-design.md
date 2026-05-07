# Edu Stack Hardening Design

## Goal

Make `edu-frontend`, `edu-service-backend`, and `edu-service-backend-business` reliable to run together locally, then improve verification and maintainability in small, reversible steps.

## Scope

This work covers the education demo stack only:

- `edu-frontend`: Vue/Vite debug UI for chat and business-object sending.
- `edu-service-backend`: FastAPI dialogue backend with chat history and business service integration.
- `edu-service-backend-business`: FastAPI business fact service backed by the education database.

The first implementation phase focuses on issues that affect startup, API compatibility, and local smoke verification. UI restructuring and broad refactoring are deferred until the stack is verified.

## Architecture

The frontend talks to the dialogue backend through `/api/*` and to the business backend through `/edu/*` via Vite proxy. The dialogue backend keeps chat state in its configured database and calls the business backend through `BusinessServiceClient`. The business backend exposes simple read-only course, cohort, and order endpoints over the education database.

Configuration should use the same names as the code reads. Documentation, example env files, and frontend proxy text must describe the same ports and URLs so a local developer can start the three services without guessing.

## First-Phase Requirements

- Align `edu-service-backend/.env.example` with the actual settings read by `atguigu_edu.conf.config.Settings`.
- Keep the default dialogue backend port consistent with `edu-frontend/vite.config.js`.
- Add a concise runbook for starting and smoke-checking all three education services.
- Add lightweight smoke verification that checks route compatibility without requiring a live LLM call.
- Avoid deleting files and avoid broad UI or domain refactors in this phase.

## Later-Phase Requirements

- Add focused tests around request/response schema behavior and route contracts.
- Improve frontend maintainability by extracting API helpers and formatting helpers from `App.vue` if the first-phase checks are stable.
- Improve business backend resilience for database errors and invalid query parameters where it helps local diagnosis.

## Testing Strategy

First phase should rely on commands that are cheap and deterministic:

- `npm run build` in `edu-frontend`.
- Python import/route smoke checks for both FastAPI apps.
- Optional HTTP smoke checks when the services and database are running locally.

LLM-dependent chat behavior should not be part of the required smoke check unless an API key is configured.
