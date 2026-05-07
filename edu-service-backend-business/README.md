# edu business service

这是一个配套 `edu-service-backend` 使用的教育业务服务示例（仿 `ecommerce-service-backend` 的实现风格）。

## 启动方式（本地开发）

```powershell
cd edu-service-backend-business
uv sync
uv run uvicorn app.app:app --reload --port 9001
```

环境变量见 `.env.example`。

