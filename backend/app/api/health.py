from fastapi import APIRouter
from qdrant_client import QdrantClient

from app.config import settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    # Kiểm tra Qdrant
    try:
        QdrantClient(url=settings.qdrant_url).get_collections()
        qdrant_status = "ok"
    except Exception as e:
        qdrant_status = f"error: {e}"

    # Kiểm tra OpenAI API key
    llm_status = "ok" if settings.openai_api_key else "missing API key"

    overall = "ok" if qdrant_status == "ok" and llm_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        qdrant=qdrant_status,
        llm=llm_status,
    )