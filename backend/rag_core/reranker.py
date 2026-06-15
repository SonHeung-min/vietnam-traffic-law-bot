# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from sentence_transformers import CrossEncoder

from rag_core.retriever import RetrievedChunk

logger = logging.getLogger(__name__)


DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"


class Reranker:
    """Cross-encoder reranker on top of hybrid retrieval.

    Loaded lazily on first .rerank() call so that import-time cost
    stays at zero when the reranker is disabled.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        device: str | None = None,
        max_length: int = 512,
    ):
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self._model: CrossEncoder | None = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        logger.info(
            "Loading cross-encoder reranker: %s (device=%s)",
            self.model_name, self.device or "auto",
        )
        self._model = CrossEncoder(
            self.model_name,
            max_length=self.max_length,
            device=self.device,
        )

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []
        if top_k >= len(chunks):
            top_k = len(chunks)

        self._ensure_loaded()
        pairs = [(query, c.content) for c in chunks]
        scores = self._model.predict(pairs, show_progress_bar=False)

        rescored = list(zip(chunks, scores))
        rescored.sort(key=lambda x: float(x[1]), reverse=True)

        out: list[RetrievedChunk] = []
        for chunk, score in rescored[:top_k]:
            chunk.score = float(score)
            out.append(chunk)
        return out
