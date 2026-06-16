import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI

from app.api import chat, health
from app.config import settings
from app.pipeline import RAGPipeline
from app.utils.logger import setup_logging
from rag_core import HybridRetriever, LegalAnswerGenerator

logger = logging.getLogger(__name__)

# DATA_DIR: overridable via env var for Docker; defaults to <project-root>/data
_DEFAULT_DATA = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(_DEFAULT_DATA)))
JSONL_PATH = DATA_DIR / "processed" / "all_chunks.jsonl"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Khởi tạo pipeline RAG…")
    logger.info("JSONL path: %s", JSONL_PATH)
    try:
        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        retriever = HybridRetriever(
            qdrant_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection_name,
            embedding_model=settings.embedding_model,
            jsonl_path=JSONL_PATH,
        )
        generator = LegalAnswerGenerator(
            provider="openai",
            model=settings.chat_model,
            api_key=settings.openai_api_key,
        )
        app.state.pipeline = RAGPipeline(retriever, generator, llm)
        logger.info("Pipeline sẵn sàng.")
    except Exception as exc:
        logger.error("Khởi tạo pipeline thất bại: %s", exc)
        app.state.pipeline = None
    yield


app = FastAPI(
    title="Traffic Law RAG API",
    description="Chatbot tư vấn Luật Giao thông Việt Nam",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")
