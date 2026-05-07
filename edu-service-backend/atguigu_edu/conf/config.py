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
    database_url: str = "sqlite+aiosqlite:///./edu_dialogue_state.db"

    # Education API (placeholder)
    edu_api_base_url: str = "http://localhost:9001"

    # Server
    app_host: str = "127.0.0.1"
    app_port: int = 8010


settings = Settings()

