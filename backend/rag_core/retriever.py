# -*- coding: utf-8 -*-


from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


VI_STOPWORDS = {
    "là", "và", "của", "cho", "các", "có", "được", "trong", "theo",
    "với", "một", "khi", "hoặc", "từ", "này", "đó", "tại", "do",
    "để", "sẽ", "đã", "nếu", "bị", "bởi",
}

DEFAULT_COLLECTION      = "TRAFFIC_LAW"
DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_JSONL = (
    Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "all_chunks.jsonl"
)

# --- Broad query detection ---
TOP_K_BROAD = 25
RE_BROAD = re.compile(
    r"khi nào|liệt kê|có mấy|"
    r"trường hợp nào|các trường hợp|những trường hợp|"
    r"lỗi nào|các lỗi|những lỗi|"
    r"hành vi nào|các hành vi|những hành vi|"
    r"hạng nào|các hạng|những hạng|"
    r"loại nào|các loại|những loại|"
    r"danh sách|điều kiện|bao gồm|gồm những",
    re.IGNORECASE | re.UNICODE,
)



@dataclass
class RetrievedChunk:
    id: int
    score: float
    content: str
    metadata: dict

    def to_dict(self) -> dict:
        """Chuyển chunk thành dict để serialize JSON."""
        return {
            "id": self.id,
            "score": self.score,
            "content": self.content,
            "metadata": self.metadata,
        }

@dataclass(frozen=True)
class LegalRef:
    so_hieu: str | None
    dieu_so: int
    khoan_so: int | None = None
    diem: str | None = None




class HybridRetriever:
    """
    Hybrid retriever: kết hợp Qdrant dense vector và BM25 in-process, hợp nhất bằng RRF.

    Yêu cầu Qdrant collection đã được index bằng SentenceTransformer tương thích
    (vd: intfloat/multilingual-e5-base). Dùng cùng file JSONL với indexer để xây
    BM25 corpus, row index == Qdrant point ID để tránh lớp ánh xạ ID.
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = DEFAULT_COLLECTION,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        jsonl_path: str | Path = DEFAULT_JSONL,
        rrf_k: int = 60,
        candidates_per_retriever: int = 30,
        enable_reranker: bool = False,
        reranker_model: str | None = None,
        rerank_top_n: int = 30,
        sibling_neighbors: int = 2,
    ):
        """Khởi tạo retriever: kết nối Qdrant, load embedding model, xây BM25 corpus."""
        self.collection_name = collection_name
        self.rrf_k = rrf_k
        self.candidates_per_retriever = candidates_per_retriever
        self.jsonl_path = Path(jsonl_path)
        self.enable_reranker = enable_reranker
        self.rerank_top_n = rerank_top_n
        self.sibling_neighbors = sibling_neighbors

        logger.info(f"Connecting Qdrant: {qdrant_url}")
        self.client = QdrantClient(url=qdrant_url)
        self.client.get_collections()  # fail fast if unreachable

        logger.info(f"Loading embedding model: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        self._query_prefix = "query: " if "e5" in embedding_model.lower() else ""    # e5 family requires "query: " prefix at encode time; other models don't.

        self._reranker = None
        if enable_reranker:
            from .reranker import DEFAULT_RERANKER_MODEL, Reranker
            self._reranker = Reranker(model_name=reranker_model or DEFAULT_RERANKER_MODEL)

        self._bm25_index: BM25Okapi | None = None
        self._payloads: list[dict] = []
        self._dieu_to_ids: dict[tuple[str, int], list[int]] = {}
        self._sibling_map: dict[int, list[int]] = {}
        self._is_completion_clause: list[bool] = []
        self._build_bm25_corpus()
        self._build_sibling_map()

    # --- public API ---------------------------------------------------------

    def get_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Tìm top-k chunk liên quan nhất cho câu truy vấn qua hybrid search + RRF."""

        # Dense retrieval từ Qdrant (vector similarity)
        query_vector = self.model.encode(
            self._query_prefix + query, normalize_embeddings=True,
        ).tolist()

        dense_hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=self.candidates_per_retriever,
            with_payload=True,
        )

        # BM25 retrieval từ in-process index
        q_tokens = self._tokenize_vi(query)
        bm25_scores = self._bm25_index.get_scores(q_tokens)
        scored = list(enumerate(bm25_scores))

        bm25_hits = sorted(scored, key=lambda x: x[1], reverse=True)[
            : self.candidates_per_retriever
        ]

        # Tự động mở rộng top_k cho các câu hỏi liệt kê / diện rộng
        k = TOP_K_BROAD if RE_BROAD.search(query) else top_k
        if k != top_k:
            logger.debug("Broad query detected — expanding top_k %d → %d", top_k, k)

        # RRF fusion, sau đó rerank bằng cross-encoder nếu được bật
        fuse_k = max(k, self.rerank_top_n) if self.enable_reranker else k
        fused = self._rrf_fuse(dense_hits, bm25_hits, fuse_k)

        if self.enable_reranker and self._reranker is not None and fused:
            fused = self._reranker.rerank(query, fused, top_k=k)

        result = self._attach_siblings(fused)
        return result



    def get_chunks_by_location(
        self,
        so_hieu: str,
        dieu_so: int,
        khoan_so: int | None = None,
        diem: str | None = None,
    ) -> list[RetrievedChunk]:
        """Tra cứu chunk trực tiếp theo vị trí pháp lý (văn bản / điều / khoản / điểm)."""

        try:
            dieu_int = int(dieu_so)
        except (TypeError, ValueError):
            return []

        row_ids = self._dieu_to_ids.get((so_hieu, dieu_int), [])
        if not row_ids:
            return []

        results: list[RetrievedChunk] = []
        for rid in row_ids:
            pl = self._payloads[rid]
            if khoan_so is not None and pl.get("khoan_so") != khoan_so:
                continue
            if diem is not None and pl.get("diem") != diem:
                continue
            content = pl.get("page_content", "")
            metadata = {key: val for key, val in pl.items() if key != "page_content"}
            results.append(
                RetrievedChunk(id=rid, score=0.0, content=content, metadata=metadata)
            )
        return results

    # --- Explicit reference pass --------------------------------------------
    _FULL_DOC_RE = re.compile(
        r"\b(?P<num>\d+)\s*/\s*(?P<year>\d{4})\s*/\s*(?P<type>[A-ZĐ\-\d]+)\b",
        re.IGNORECASE | re.UNICODE,
    )
    _SHORT_ND_RE = re.compile(
        r"(?:nghị\s*định|nđ|nd)\s*(?P<num>\d+)",
        re.IGNORECASE | re.UNICODE,
    )
    _EXPLICIT_REF_RE = re.compile(
        r"(?:điểm\s+(?P<diem>[a-zđ])\s+)?"
        r"(?:khoản\s+(?P<khoan>\d+)\s+)?"
        r"điều\s+(?P<dieu>\d+)",
        re.IGNORECASE | re.UNICODE,
    )

    def _extract_doc_id(self, text: str) -> str | None:
        """Trích số hiệu văn bản (dạng đầy đủ hoặc viết tắt 'nghị định X') từ chuỗi."""
        full = self._FULL_DOC_RE.search(text.upper())
        if full:
            return (
                f"{full.group('num')}/"
                f"{full.group('year')}/"
                f"{full.group('type').replace(' ', '')}"
            )

        short_nd = self._SHORT_ND_RE.search(text)
        if short_nd:
            doc_num = short_nd.group("num")
            for payload in self._payloads:
                so_hieu = payload.get("so_hieu") or ""
                if so_hieu.startswith(f"{doc_num}/"):
                    return so_hieu

        return None


    def extract_legal_refs(
        self,
        text: str
    ) -> list[LegalRef]:
        """Trích các tham chiếu pháp lý tường minh (vd: 'Khoản 8 Điều 6 Nghị định 168/2024/NĐ-CP')."""
        so_hieu = self._extract_doc_id(text)
        refs: list[LegalRef] = []

        for match in self._EXPLICIT_REF_RE.finditer(text):
            dieu = match.group("dieu")
            if not dieu:
                continue

            khoan = match.groupdict().get("khoan")
            diem = match.groupdict().get("diem")

            ref = LegalRef(
                so_hieu=so_hieu,
                dieu_so=int(dieu),
                khoan_so=int(khoan) if khoan else None,
                diem=diem.lower() if diem else None,
            )

            if ref not in refs:
                refs.append(ref)

        return refs

    def get_chunks_by_explicit_reference(
        self,
        query: str,
        include_siblings: bool = False,
    ) -> list[RetrievedChunk]:
        """Lấy chunk từ các tham chiếu pháp lý tường minh trong câu truy vấn."""
        refs = self.extract_legal_refs(query)
        if not refs:
            return []

        results: list[RetrievedChunk] = []
        seen_ids: set[int] = set()

        for ref in refs:
            for chunk in self.get_chunks_by_location(
                so_hieu=ref.so_hieu,
                dieu_so=ref.dieu_so,
                khoan_so=ref.khoan_so,
                diem=ref.diem,
            ):
                if chunk.id not in seen_ids:
                    results.append(chunk)
                    seen_ids.add(chunk.id)

        if include_siblings and results:
            results = self._attach_siblings(results)

        return results


    # --- BM25 corpus --------------------------------------------------------

    @staticmethod
    def _tokenize_vi(text: str) -> list[str]:
        """Tokenize tiếng Việt đơn giản: lowercase, bỏ dấu câu, lọc stopwords."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
        return [t for t in text.split() if t not in VI_STOPWORDS and len(t) > 1]

    def _build_bm25_corpus(self) -> None:
        """Đọc JSONL, xây BM25 index và payload cache; đồng thời lập chỉ mục điều → row ids."""
        logger.info(f"Building BM25 corpus from: {self.jsonl_path}")
        t0 = time.time()

        tokenized: list[list[str]] = []
        total_tokens = 0

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                c = json.loads(line)
                meta = c.get("metadata")
                content = c.get("page_content")

                tokens = self._tokenize_vi(content)
                tokenized.append(tokens)
                total_tokens += len(tokens)

                content_lower = content.lower()
                self._is_completion_clause.append(
                    any(pat in content_lower for pat in self._SIBLING_PRIORITY_PATTERNS)
                )
                self._payloads.append({
                    "page_content":        content,
                    "chunk_id":            meta.get("chunk_id"),
                    "so_hieu":             meta.get("so_hieu"),
                    "ten_van_ban":         meta.get("ten_van_ban"),
                    "loai_van_ban":        meta.get("loai_van_ban"),
                    "co_quan_ban_hanh":    meta.get("co_quan_ban_hanh"),
                    "ngay_ban_hanh":       meta.get("ngay_ban_hanh"),
                    "ngay_hieu_luc":       meta.get("ngay_hieu_luc"),
                    "ngay_het_hieu_luc":   meta.get("ngay_het_hieu_luc"),
                    "con_hieu_luc":        meta.get("con_hieu_luc"),
                    "chuong_so":           meta.get("chuong_so"),
                    "chuong_ten":          meta.get("chuong_ten"),
                    "muc_so":              meta.get("muc_so"),
                    "muc_ten":             meta.get("muc_ten"),
                    "dieu_so":             meta.get("dieu_so"),
                    "khoan_so":            meta.get("khoan_so"),
                    "diem":                meta.get("diem"),
                    "source_file":         meta.get("source_file"),
                    "dieu_ten":            meta.get("dieu_ten"),
                    "noi_dung_dieu":       meta.get("noi_dung_dieu"),
                    "noi_dung_khoan":      meta.get("noi_dung_khoan"),
                    "noi_dung_diem":       meta.get("noi_dung_diem"),
                    "level":               meta.get("level"),
                    "is_sibling":          meta.get("is_sibling"),
                    "noi_dung_tham_chieu": c.get("noi_dung_tham_chieu"),
                })

                so_hieu = meta.get("so_hieu")
                dieu_so = meta.get("dieu_so")
                if so_hieu and dieu_so:
                    self._dieu_to_ids.setdefault((so_hieu, dieu_so), []).append(
                        len(self._payloads) - 1
                    )

        self._bm25_index = BM25Okapi(tokenized)
        logger.info(
            f"BM25 corpus built: {len(tokenized)} docs, {total_tokens} tokens, "
            f"{time.time() - t0:.2f}s"
        )

    # --- Sibling enrichment -------------------------------------------------

    _SIBLING_PRIORITY_PATTERNS = (
        "còn bị trừ điểm giấy phép",
        "bị trừ điểm giấy phép lái xe",
        "hình thức xử phạt bổ sung",
        "tước quyền sử dụng giấy phép",
        "tịch thu phương tiện",
        "gây tai nạn giao thông",
    )

    def _attach_siblings(
        self, primaries: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """Bổ sung các chunk anh em (cùng điều) vào danh sách kết quả chính."""
        seen_ids: set[int] = {c.id for c in primaries}
        enriched: list[RetrievedChunk] = list(primaries)

        for primary in primaries:
            for rid in self._sibling_map.get(primary.id, []):
                if rid in seen_ids:
                    continue
                pl = self._payloads[rid]
                content = pl.get("page_content", "")
                metadata = {key: val for key, val in pl.items() if key != "page_content"}
                metadata["is_sibling"] = True
                enriched.append(RetrievedChunk(id=rid, score=0.0, content=content, metadata=metadata))
                seen_ids.add(rid)

        return enriched


    def _build_sibling_map(self) -> None:
        """Tính trước danh sách sibling IDs cho từng chunk để query-time chỉ cần lookup."""
        t0 = time.time()
        n = self.sibling_neighbors

        for row_idx, pl in enumerate(self._payloads):
            so_hieu = pl.get("so_hieu")
            dieu_so = pl.get("dieu_so")
            khoan_so = pl.get("khoan_so")
            siblings: list[int] = []

            if not (so_hieu and dieu_so):
                self._sibling_map[row_idx] = siblings
                continue

            for rid in self._dieu_to_ids.get((so_hieu, dieu_so), []):
                if rid == row_idx:
                    continue
                if self._is_completion_clause[rid]:
                    siblings.append(rid)
                elif khoan_so is not None:
                    k = self._payloads[rid].get("khoan_so")
                    if k is not None and 0 < abs(k - khoan_so) <= n:
                        siblings.append(rid)

            self._sibling_map[row_idx] = siblings

        logger.info(
            f"Sibling map built: {len(self._sibling_map)} entries, "
            f"{time.time() - t0:.2f}s"
        )

    # --- RRF fusion ---------------------------------------------------------

    def _rrf_fuse(
        self,
        dense_hits,
        bm25_hits: list[tuple[int, float]],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Kết hợp kết quả dense và BM25 bằng Reciprocal Rank Fusion, trả về top_k chunk."""
        k = self.rrf_k
        scores: dict[int, float] = {}
        payloads: dict[int, dict] = {}

        for rank, h in enumerate(dense_hits, start=1):
            scores[h.id] = scores.get(h.id, 0.0) + 1.0 / (k + rank)
            payloads[h.id] = h.payload

        for rank, (id, _) in enumerate(bm25_hits, start=1):
            scores[id] = scores.get(id, 0.0) + 1.0 / (k + rank)
            payloads.setdefault(id, self._payloads[id])

        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results: list[RetrievedChunk] = []
        for id, score in fused:
            pl = payloads[id]
            content = pl.get("page_content", "")
            metadata = {key: val for key, val in pl.items() if key != "page_content"}
            results.append(RetrievedChunk(id=id, score=score, content=content, metadata=metadata))
        return results