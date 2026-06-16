from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Đường dẫn tuyệt đối tới .env ở project root, không phụ thuộc CWD.
# config.py = backend/app/config.py → 3 cấp lên là project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    chat_model: str = "gpt-4o-mini"
    embedding_model: str 

    # Qdrant
    qdrant_url: str 
    qdrant_collection_name: str 

    # Backend
    backend_url: str 

    # Thêm model mới: bổ sung 1 entry vào đây, mọi nơi tự đồng bộ.
    EMBEDDING_REGISTRY: ClassVar[dict[str, dict]] = {
        "text-embedding-3-small":         {"dim": 1536, "provider": "openai"},
        "text-embedding-3-large":         {"dim": 3072, "provider": "openai"},
        "intfloat/multilingual-e5-small": {"dim": 384,  "provider": "local"},
        "intfloat/multilingual-e5-base":  {"dim": 768,  "provider": "local"},        
        "intfloat/multilingual-e5-large": {"dim": 1024,  "provider": "local"},
        "BAAI/bge-m3":                    {"dim": 1024, "provider": "local"},
    }

    @computed_field
    @property
    def embedding_dim(self) -> int:
        cfg = self.EMBEDDING_REGISTRY.get(self.embedding_model)
        if cfg is None:
            raise ValueError(
                f"embedding_model '{self.embedding_model}' không có trong registry. "
                f"Các model hợp lệ: {list(self.EMBEDDING_REGISTRY)}"
            )
        return cfg["dim"]

    @computed_field
    @property
    def embedding_provider(self) -> str:
        return self.EMBEDDING_REGISTRY[self.embedding_model]["provider"]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",  # Bỏ qua key cũ trong .env (vd GEMINI_*)
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
