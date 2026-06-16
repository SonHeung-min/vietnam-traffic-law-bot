import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request) -> ChatResponse:
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline chưa khởi tạo.")

    history = [msg.model_dump() for msg in body.chat_history]

    try:
        result = pipeline.run(body.query, chat_history=history)
    except Exception as exc:
        logger.exception("Pipeline.run thất bại: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources") or [],
        refused=bool(result.get("refused")),
        category=result.get("category", "out_of_scope"),
        model_info=result.get("model_info", ""),
        query=result.get("query", body.query),
        retrieval_query=result.get("retrieval_query"),
        error=result.get("error"),
    )
