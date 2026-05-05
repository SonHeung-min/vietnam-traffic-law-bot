"""
Retriever — kết nối Qdrant + embedding cho RAG pipeline.

Schema chunk Qdrant payload (do preprocessing/run_index sinh ra):

    {
        "chunk_id": "35-2024-QH15_d8_k3",
        "van_ban": {"so_hieu": "...", "loai_van_ban": "...", "ngay_ban_hanh": "..."},
        "vi_tri": {"chuong_so": ..., "dieu_so": ..., "khoan_so": ..., "diem": ...},
        "noi_dung": "...",
        "noi_dung_tham_chieu": [chunk_id phụ lục, ...] | None,
        "citation": "Điều 8 Khoản 3, Luật 35/2024/QH15",
        "hieu_luc": {
            "ngay_hieu_luc": "...",
            "ngay_het_hieu_luc": "..." | None,
            "con_hieu_luc": bool,
            "loai_thay_doi": "sua_doi" | "bai_bo" | "thay_the" | None,
            "bi_sua_doi_boi": "<chunk_id sửa đổi>" | None,
            "ghi_chu": ...
        },
        "page_content": "<text dùng để embed>"
    }
"""

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


def get_vectorstore() -> QdrantVectorStore:
    """Kết nối tới collection Qdrant đã được index sẵn bởi run_index.py."""
    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection_name,
        content_payload_key="page_content",
    )


def get_retriever(vectorstore: QdrantVectorStore):
    """
    Similarity search trả top-k chunk có embedding gần nhất với query.
    MMR đã thử nhưng diverse hoá quá mức → bỏ chunk đúng để tránh "trùng".
    """
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 15},
    )