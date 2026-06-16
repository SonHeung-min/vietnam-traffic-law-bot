from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    pipeline_ready = getattr(request.app.state, "pipeline", None) is not None
    return HealthResponse(status="ok", pipeline_ready=pipeline_ready)
