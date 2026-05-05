import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain.schema import Document

from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.rag.pipeline import get_pipeline
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _doc_to_source(doc: Document) -> SourceDocument:
    """Map Document (Qdrant payload nested) → SourceDocument flat."""
    meta = doc.metadata
    van_ban = meta.get("van_ban") or {}
    vi_tri = meta.get("vi_tri") or {}
    hieu_luc = meta.get("hieu_luc") or {}

    # Ưu tiên noi_dung gốc (sạch) thay vì page_content (đã ghép citation + dieu_ten)
    content = meta.get("noi_dung") or doc.page_content
    preview = content if len(content) <= 300 else content[:300] + "..."

    return SourceDocument(
        chunk_id=meta.get("chunk_id", ""),
        citation=meta.get("citation", ""),
        content_preview=preview,
        so_hieu=van_ban.get("so_hieu", ""),
        loai_van_ban=van_ban.get("loai_van_ban", ""),
        dieu_so=vi_tri.get("dieu_so"),
        dieu_ten=vi_tri.get("dieu_ten"),
        khoan_so=vi_tri.get("khoan_so"),
        diem=vi_tri.get("diem"),
        phu_luc_so=vi_tri.get("phu_luc_so"),
        mau_so=vi_tri.get("mau_so"),
        con_hieu_luc=bool(hieu_luc.get("con_hieu_luc", True)),
        ngay_het_hieu_luc=hieu_luc.get("ngay_het_hieu_luc"),
        loai_thay_doi=hieu_luc.get("loai_thay_doi"),
        bi_sua_doi_boi=hieu_luc.get("bi_sua_doi_boi"),
    )


def _extract_sources(docs: list[Document]) -> list[SourceDocument]:
    """Dedupe theo chunk_id, giữ thứ tự retrieve."""
    seen: set[str] = set()
    sources: list[SourceDocument] = []
    for doc in docs:
        cid = doc.metadata.get("chunk_id", "")
        if cid and cid in seen:
            continue
        if cid:
            seen.add(cid)
        sources.append(_doc_to_source(doc))
    return sources


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Hỏi 1 câu, nhận về câu trả lời đầy đủ + danh sách nguồn."""
    logger.info(f"[{request.session_id}] Q: {request.question[:80]}")
    try:
        pipeline = get_pipeline()
        result = await pipeline.ainvoke(request.question, request.session_id)
        return ChatResponse(
            answer=result["answer"],
            sources=_extract_sources(result.get("source_documents", [])),
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"Loi xu ly cau hoi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream câu trả lời theo Server-Sent Events.

    Event format:
        data: {"sources": [...]}     — gửi 1 lần khi retrieve xong
        data: {"token": "..."}       — token answer (nhiều lần)
        data: [DONE]                 — kết thúc
        data: {"error": "..."}       — nếu có lỗi
    """
    logger.info(f"[{request.session_id}] Stream Q: {request.question[:80]}")

    async def event_stream():
        try:
            pipeline = get_pipeline()
            async for chunk in pipeline.astream(request.question, request.session_id):
                if "context" in chunk:
                    sources = _extract_sources(chunk["context"])
                    payload = {"sources": [s.model_dump() for s in sources]}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                elif "token" in chunk:
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Loi stream: {e}")
            err = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {err}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Xóa lịch sử hội thoại của 1 session."""
    get_pipeline().clear_session(session_id)
    return {"message": f"Đã xóa lịch sử session '{session_id}'"}