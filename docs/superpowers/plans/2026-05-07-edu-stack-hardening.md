# Edu Stack Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the education frontend, dialogue backend, and business backend easier to start, verify, and maintain together.

**Architecture:** Keep the existing Vue/Vite + FastAPI split. First align local configuration and route contracts, then add deterministic smoke checks, then improve focused maintainability without changing the product flow.

**Tech Stack:** Vue 3, Vite, FastAPI, Pydantic v2, SQLAlchemy, uv, npm.

---

## File Structure

- Modify `edu-service-backend/.env.example`: align variable names and default ports with `Settings`.
- Create `docs/edu-stack-local-runbook.md`: one runbook for starting and verifying the three education services.
- Create `edu-service-backend/scripts/route_smoke.py`: import the dialogue FastAPI app and validate expected routes.
- Create `edu-service-backend-business/scripts/route_smoke.py`: import the business FastAPI app and validate expected routes.
- Modify `edu-service-backend/pyproject.toml`: add optional script entry if the existing project style supports it.
- Modify `edu-service-backend-business/pyproject.toml`: add optional script entry if the existing project style supports it.
- Modify `edu-frontend/package.json`: add a lightweight check script only if it maps to an existing command such as `vite build`.

## Task 1: Align Dialogue Backend Example Environment

**Files:**
- Modify: `edu-service-backend/.env.example`

- [ ] **Step 1: Update settings names and defaults**

Replace the stale business URL and port names with names read by `atguigu_edu.conf.config.Settings`:

```dotenv
## LLM
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4.1-mini
LLM_BASE_URL=https://api.openai.com/v1

## Database (SQLite for dev)
DATABASE_URL=sqlite+aiosqlite:///./edu_dialogue_state.db

## Education business API
BUSINESS_BASE_URL=http://127.0.0.1:9001

## Server
APP_HOST=127.0.0.1
APP_PORT=8012
```

- [ ] **Step 2: Verify setting loading**

Run:

```powershell
cd edu-service-backend
uv run python -c "from atguigu_edu.conf.config import settings; print(settings.app_port, settings.business_base_url)"
```

Expected output includes:

```text
8012 http://127.0.0.1:9001
```

## Task 2: Add Route Smoke Checks

**Files:**
- Create: `edu-service-backend/scripts/route_smoke.py`
- Create: `edu-service-backend-business/scripts/route_smoke.py`

- [ ] **Step 1: Add dialogue backend route smoke**

Create `edu-service-backend/scripts/route_smoke.py`:

```python
from __future__ import annotations

from atguigu_edu.api.app import app


EXPECTED_ROUTES = {
    ("POST", "/api/chat"),
    ("GET", "/api/chat/history"),
}


def main() -> None:
    actual_routes = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    missing = sorted(EXPECTED_ROUTES - actual_routes)
    if missing:
        raise SystemExit(f"Missing dialogue backend routes: {missing}")
    print("Dialogue backend route smoke passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add business backend route smoke**

Create `edu-service-backend-business/scripts/route_smoke.py`:

```python
from __future__ import annotations

from app.app import app


EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("GET", "/students/{student_id}/courses"),
    ("GET", "/students/{student_id}/cohorts"),
    ("GET", "/students/{student_id}/orders"),
    ("GET", "/courses/{series_code}"),
    ("GET", "/cohorts/{cohort_code}"),
    ("GET", "/orders/{order_no}"),
}


def main() -> None:
    actual_routes = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    missing = sorted(EXPECTED_ROUTES - actual_routes)
    if missing:
        raise SystemExit(f"Missing business backend routes: {missing}")
    print("Business backend route smoke passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run route smoke checks**

Run:

```powershell
cd edu-service-backend
uv run python scripts/route_smoke.py
cd ..\edu-service-backend-business
uv run python scripts/route_smoke.py
```

Expected output:

```text
Dialogue backend route smoke passed.
Business backend route smoke passed.
```

## Task 3: Add Local Runbook

**Files:**
- Create: `docs/edu-stack-local-runbook.md`

- [ ] **Step 1: Document service order and ports**

Create a runbook that states:

```markdown
# Education Stack Local Runbook

## Services

- `edu-service-backend-business`: business fact API on `http://127.0.0.1:9001`.
- `edu-service-backend`: dialogue API on `http://127.0.0.1:8012`.
- `edu-frontend`: Vite UI on `http://127.0.0.1:5174`.

## Start Order

1. Start the education database required by `edu-service-backend-business`.
2. Start the business API:

   ```powershell
   cd edu-service-backend-business
   uv sync
   uv run uvicorn app.app:app --reload --host 127.0.0.1 --port 9001
   ```

3. Start the dialogue API:

   ```powershell
   cd edu-service-backend
   uv sync
   uv run uvicorn atguigu_edu.api.app:app --reload --host 127.0.0.1 --port 8012
   ```

4. Start the frontend:

   ```powershell
   cd edu-frontend
   npm install
   npm run dev
   ```

## Required Smoke Checks

```powershell
cd edu-service-backend-business
uv run python scripts/route_smoke.py

cd ..\edu-service-backend
uv run python scripts/route_smoke.py

cd ..\edu-frontend
npm run build
```

## Optional HTTP Checks

When the business API and database are running:

```powershell
Invoke-RestMethod http://127.0.0.1:9001/health
Invoke-RestMethod "http://127.0.0.1:9001/students/student_001/courses?limit=3"
```

When the dialogue API is running:

```powershell
Invoke-RestMethod "http://127.0.0.1:8012/api/chat/history?sender_id=student_001"
```
```

- [ ] **Step 2: Check for stale documentation**

Search for stale port references in non-generated docs:

```powershell
rg "8010|EDU_API_BASE_URL|localhost:9001" -g "!**/node_modules/**" -g "!**/uv.lock"
```

Update only education stack docs or examples that conflict with the current code.

## Task 4: Verify Frontend Build

**Files:**
- Modify: `edu-frontend/package.json` only if adding a script is useful.

- [ ] **Step 1: Run existing frontend build**

Run:

```powershell
cd edu-frontend
npm run build
```

Expected result:

```text
✓ built
```

- [ ] **Step 2: Add a check script if build succeeds**

If `npm run build` is the only available deterministic frontend verification, add:

```json
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview",
  "check": "vite build"
}
```

Then run:

```powershell
npm run check
```

Expected result:

```text
✓ built
```

## Task 5: Final Verification

**Files:**
- Review changed files only.

- [ ] **Step 1: Run all deterministic checks**

Run:

```powershell
cd edu-service-backend
uv run python scripts/route_smoke.py

cd ..\edu-service-backend-business
uv run python scripts/route_smoke.py

cd ..\edu-frontend
npm run build
```

Expected route smoke output:

```text
Dialogue backend route smoke passed.
Business backend route smoke passed.
```

Expected frontend output includes:

```text
✓ built
```

- [ ] **Step 2: Inspect git diff**

Run:

```powershell
git diff -- edu-service-backend/.env.example edu-service-backend/scripts/route_smoke.py edu-service-backend-business/scripts/route_smoke.py docs/edu-stack-local-runbook.md edu-frontend/package.json
```

Expected: only configuration alignment, smoke scripts, runbook, and optional frontend check script are changed.

## Self-Review

- Spec coverage: Task 1 covers configuration alignment; Task 2 covers route compatibility; Task 3 covers local runbook; Task 4 and Task 5 cover deterministic verification.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: route paths match the currently inspected FastAPI route definitions; frontend script names match `package.json`.
