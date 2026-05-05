"""
Đọc JSON chunks → embed → upsert vào Qdrant.

Chạy từ thư mục backend/:
    python scripts/run_index.py --input ../data/processed/all_chunks.json
    python scripts/run_index.py --dir   ../data/processed [--reset]
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("run_index")

BATCH_SIZE = 100
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "traffic-law.doantotnghiep.local")


def load_chunks(path: Path) -> list[dict]:
    """Đọc 1 file JSON, hoặc mọi file *.json trong thư mục (trừ amendment_*, all_chunks)."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))

    files = [
        f for f in sorted(path.glob("*.json"))
        if not f.name.startswith("amendment") and f.name != "all_chunks.json"
    ]
    chunks: list[dict] = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        logger.info(f"  + {f.name}: {len(data)} chunks")
        chunks.extend(data)
    return chunks


def build_search_text(c: dict) -> str:
    """Citation + tên Điều/Phụ lục + nội dung — đem đi embed."""
    vt = c.get("vi_tri", {})
    parts = [c.get("citation", "")]
    if vt.get("dieu_ten"):
        parts.append(f"Điều {vt.get('dieu_so', '')}: {vt['dieu_ten']}")
    if vt.get("phu_luc_ten"):
        parts.append(f"Phụ lục {vt.get('phu_luc_so', '')}: {vt['phu_luc_ten']}")
    if vt.get("mau_ten"):
        parts.append(f"Mẫu số {vt.get('mau_so', '')}: {vt['mau_ten']}")
    parts.append(c["noi_dung"])
    return "\n".join(p for p in parts if p)


def main():
    p = argparse.ArgumentParser(description="Index JSON chunks vào Qdrant")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input")
    src.add_argument("--dir")
    p.add_argument("--reset", action="store_true")
    args = p.parse_args()

    raw = load_chunks(Path(args.input or args.dir))
    chunks = [c for c in raw if isinstance(c, dict) and "chunk_id" in c and "noi_dung" in c]
    if (skipped := len(raw) - len(chunks)):
        logger.warning(f"Bỏ qua {skipped} record không đúng schema")
    if not chunks:
        sys.exit("Không có chunk hợp lệ.")
    logger.info(f"Sẽ index {len(chunks)} chunks")

    client = QdrantClient(url=settings.qdrant_url)
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model, api_key=settings.openai_api_key
    )
    collection = settings.qdrant_collection_name
    dim = len(embeddings.embed_query("dim probe"))
    logger.info(f"Embedding {settings.embedding_model} | dim={dim}")

    # Reset / create / verify collection
    if args.reset and client.collection_exists(collection):
        client.delete_collection(collection)
        logger.info(f"Đã xóa collection cũ '{collection}'")
    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        logger.info(f"Tạo collection '{collection}' (dim={dim})")
    elif client.get_collection(collection).config.params.vectors.size != dim:
        sys.exit(f"Dim collection cũ ≠ {dim}. Chạy với --reset.")

    # Embed + upsert theo batch (OpenAI client tự retry 429/timeout 2 lần)
    n = len(chunks)
    for i in range(0, n, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [build_search_text(c) for c in batch]
        vectors = embeddings.embed_documents(texts)
        client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=str(uuid.uuid5(NAMESPACE, c["chunk_id"])),
                    vector=v,
                    payload={"page_content": t, "metadata": c},
                )
                for c, t, v in zip(batch, texts, vectors)
            ],
        )
        logger.info(f"  {min(i + BATCH_SIZE, n)}/{n}")

    logger.info(f"✅ Done. Collection '{collection}': {client.get_collection(collection).points_count} points")


if __name__ == "__main__":
    main()