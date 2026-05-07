from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # Database
    database_url: str = "mysql+aiomysql://root:123321@127.0.0.1:13306/edu?charset=utf8mb4"

    # Business service (edu-service-backend-business)
    business_base_url: str = "http://127.0.0.1:9001"

    # Server
    app_host: str = "127.0.0.1"
    app_port: int = 8012


settings = Settings()

