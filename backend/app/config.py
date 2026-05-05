from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Đường dẫn tuyệt đối tới .env ở project root, không phụ thuộc CWD.
# config.py = backend/app/config.py → 3 cấp lên là project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "traffic_law"

    # Backend
    backend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",  # Bỏ qua key cũ trong .env (vd GEMINI_*)
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
