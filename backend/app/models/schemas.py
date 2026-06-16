from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    sources: list[dict[str, Any]] = []


class ChatRequest(BaseModel):
    query: str
    chat_history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    refused: bool
    category: str
    model_info: str
    query: str
    retrieval_query: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    pipeline_ready: bool
