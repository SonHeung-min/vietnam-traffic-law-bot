"""
RAG pipeline: retrieve → stuff vào prompt → LLM trả lời.
Hỗ trợ multi-turn chat history theo session_id.
"""

from functools import lru_cache
from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from app.config import settings
from app.rag.retriever import get_retriever, get_vectorstore
from app.rag.prompt_templates import get_qa_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    def __init__(self):
        logger.info("Khoi tao RAG pipeline...")

        self.llm = ChatOpenAI(
            model=settings.chat_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_tokens=2048,
        )

        vectorstore = get_vectorstore()
        retriever = get_retriever(vectorstore)
        prompt = get_qa_prompt()

        combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
        self.rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

        self._histories: dict[str, ChatMessageHistory] = {}
        logger.info("RAG pipeline san sang.")

    # ── Session history ────────────────────────────────────────────────

    def _get_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self._histories:
            self._histories[session_id] = ChatMessageHistory()
        return self._histories[session_id]

    def clear_session(self, session_id: str) -> None:
        self._histories.pop(session_id, None)
        logger.info(f"Da xoa session: {session_id}")

    def _recent_messages(self, session_id: str, limit: int = 10):
        return self._get_history(session_id).messages[-limit:]

    # ── Inference ──────────────────────────────────────────────────────

    async def ainvoke(self, question: str, session_id: str) -> dict:
        """
        Trả response 1 lần (non-streaming).

        Returns:
            {"answer": str, "source_documents": list[Document]}
        """
        history = self._get_history(session_id)
        result = await self.rag_chain.ainvoke({
            "input": question,
            "chat_history": self._recent_messages(session_id),
        })

        history.add_user_message(question)
        history.add_ai_message(result["answer"])

        return {
            "answer": result["answer"],
            "source_documents": result.get("context", []),
        }

    async def astream(self, question: str, session_id: str) -> AsyncIterator[dict]:
        """
        Stream từng token + context. Yield dict:
            {"token": "..."}     — từng token answer
            {"context": [...]}   — danh sách Document đã retrieve (gửi 1 lần)
        Sau khi stream xong, lưu cả lượt vào history.
        """
        full_answer = ""
        sent_context = False

        async for chunk in self.rag_chain.astream({
            "input": question,
            "chat_history": self._recent_messages(session_id),
        }):
            if "context" in chunk and not sent_context:
                yield {"context": chunk["context"]}
                sent_context = True
            if answer_part := chunk.get("answer"):
                full_answer += answer_part
                yield {"token": answer_part}

        history = self._get_history(session_id)
        history.add_user_message(question)
        history.add_ai_message(full_answer)


@lru_cache
def get_pipeline() -> RAGPipeline:
    """Lazy singleton — khởi tạo lần đầu khi có request đầu tiên."""
    return RAGPipeline()