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
uv run --no-sync python scripts/route_smoke.py

cd ..\edu-service-backend
uv run --no-sync python scripts/route_smoke.py

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

## Notes

- Chat generation may require `LLM_API_KEY`; route smoke checks do not call the LLM.
- `edu-frontend` proxies `/api` to `edu-service-backend` and `/edu` to `edu-service-backend-business`.
