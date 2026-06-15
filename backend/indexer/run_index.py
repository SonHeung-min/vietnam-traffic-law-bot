# -*- coding: utf-8 -*-
"""
run_index.py — Indexing Pipeline cho RAG Pháp luật Giao thông VN
================================================================
TASK 1: Tạo / reset Qdrant collection + payload indexes
TASK 2: Đọc all_chunks.jsonl → embed (OpenAI) → upsert Qdrant

QUAN TRỌNG — Point ID:
    id = row index trong JSONL (integer 0-based).
    Retriever build BM25 từ cùng JSONL theo cùng thứ tự
    → BM25 array index tự align với Qdrant point ID, không cần bảng ánh xạ.

Chạy từ backend/:
    python indexer/run_index.py
    python indexer/run_index.py --reset
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import PROJECT_ROOT, settings

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

QDRANT_URL          = settings.qdrant_url
COLLECTION          = settings.qdrant_collection_name
EMBEDDING_MODEL     = settings.embedding_model
EMBEDDING_REGISTRY  = settings.EMBEDDING_REGISTRY
PROVIDER            = EMBEDDING_REGISTRY[EMBEDDING_MODEL]["provider"]
VECTOR_SIZE         = EMBEDDING_REGISTRY[EMBEDDING_MODEL]["dim"]

BATCH_SIZE      = 50
JSONL_PATH      = PROJECT_ROOT / "data" / "processed" / "all_chunks.jsonl"

LOG_DIR = PROJECT_ROOT / "backend" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / f"indexer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedder factory
# ---------------------------------------------------------------------------
def build_embedder(model: str, provider: str):
    """Trả về callable embed(texts) → list[list[float]] thống nhất cho cả 2 provider."""
    if provider == "openai":
        openai_client = OpenAI(api_key=settings.openai_api_key)
        def embed(texts: list[str]) -> list[list[float]]:
            return [d.embedding for d in openai_client.embeddings.create(model=model, input=texts).data]
    else:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Đang tải local model: {model} ...")
        st = SentenceTransformer(model)
        prefix = "passage: " if "e5" in model.lower() else ""
        def embed(texts: list[str]) -> list[list[float]]:
            return st.encode([prefix + t for t in texts], normalize_embeddings=True).tolist()
    return embed


# ===================================================================
# TASK 1: Tạo / reset Qdrant collection
# ===================================================================
def setup_collection(client: QdrantClient, dim: int, reset: bool) -> None:
    if reset and client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
        logger.info(f"Đã xóa collection '{COLLECTION}'")

    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        logger.info(f"Tạo collection '{COLLECTION}' (dim={dim}, Cosine)")
        logger.info(f"Collection '{COLLECTION}' đã sẵn sàng.\n")
    else:
        logger.info(f"Collection '{COLLECTION}' đã tồn tại. Dùng --reset để tạo lại.")


# ===================================================================
# TASK 2: Đọc JSONL → embed → upsert
# ===================================================================
def index_chunks(client: QdrantClient, embed) -> None:
    # Đọc JSONL
    chunks = []
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    total = len(chunks)
    logger.info(f"Đọc {total} chunks từ {JSONL_PATH}")
    logger.info(f"Bắt đầu embed + upsert {total} chunks (batch={BATCH_SIZE})...")

    current_source = None
    source_count   = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        # Extract texts for embedding
        texts = [c.get("page_content") for c in batch]

        # Embed batch
        vectors = embed(texts)

        # Build points (id = row index trong JSONL)
        batch_points = []
        for j, (c, text, vec) in enumerate(zip(batch, texts, vectors)):
            meta = c["metadata"]

            # Log khi chuyển sang source_file mới
            src = meta.get("source_file", "")
            if src != current_source:
                if current_source is not None:
                    logger.info(f"    [{current_source}] → {source_count} points")
                current_source = src
                source_count   = 0
            source_count += 1

            batch_points.append(PointStruct(
                id      = i + j,
                vector  = vec,
                payload = {
                    "page_content":        text,
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
                },
            ))

        client.upsert(collection_name=COLLECTION, points=batch_points)


    # Log source_file cuối cùng
    if current_source:
        logger.info(f"    [{current_source}] → {source_count} points")

    logger.info(f"Upsert hoàn tất")
    logger.info(f"Points trong Qdrant: {client.get_collection(COLLECTION).points_count}\n")




def main() -> None:
    parser = argparse.ArgumentParser(description="Indexing Pipeline — RAG Pháp luật Giao thông VN")
    parser.add_argument("--reset",           action="store_true", help="Xóa và tạo lại collection")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("QDRANT INDEXING PIPELINE")
    logger.info("=" * 60)

    # Kết nối Qdrant
    logger.info(f"Kết nối Qdrant: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.get_collections()
        logger.info("Kết nối Qdrant thành công!\n")
    except Exception as e:
        logger.error(f"Không thể kết nối Qdrant: {e}")
        logger.error("Hãy chạy: docker compose up -d qdrant")
        sys.exit(1)


    embed    = build_embedder(EMBEDDING_MODEL, PROVIDER)
    logger.info(f"Embedding model: {EMBEDDING_MODEL} | provider={PROVIDER} | dim={VECTOR_SIZE}\n")

    # TASK 1
    setup_collection(client, VECTOR_SIZE, args.reset)

    # TASK 2
    if not JSONL_PATH.exists():
        sys.exit(f"Không tìm thấy JSONL: {JSONL_PATH}")
    index_chunks(client, embed)
    

    logger.info("\nPIPELINE HOÀN TẤT.")


if __name__ == "__main__":
    main()
