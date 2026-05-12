"""
run_extract
───────────
Script chính: đọc .docx → parse → tạo chunks → xuất JSON.

Cách dùng (chạy từ thư mục `preprocessing/`):

    # Xử lý 1 file
    python run_extract.py --file ../data/raw/raw_luat/Nghị-định-168-2024-NĐ-CP.docx

    # Xử lý toàn bộ .docx trong 1 thư mục (và tự động merge sang all_chunks.json)
    python run_extract.py --dir ../data/raw/raw_luat

    # Preview cấu trúc đã parse, KHÔNG xuất JSON
    python run_extract.py --file ../data/raw/raw_luat/Luật-35-2024-QH15.docx --preview

    # Chỉ định thư mục output (mặc định: ../data/processed)
    python run_extract.py --dir ../data/raw/raw_luat --output ../data/processed

    # Chỉ gộp các JSON đã có thành all_chunks.json (không parse lại)
    python run_extract.py --merge --output ../data/processed
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Fix encoding tiếng Việt trên Windows console
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from docx_parser import parse_docx, print_structure
from chunk_builder import build_chunks, build_phuluc_chunks, link_tham_chieu
from doc_registry import get_doc_info


# ─── Xử lý 1 file .docx → JSON ───────────────────────────────────────────────

def process_one_file(file_path: Path, output_dir: Path, preview: bool = False) -> int:
    """
    Pipeline cho 1 file:
        parse .docx → build chunks chính → build chunks phụ lục
        → link tham chiếu → ghi JSON

    Trả về số chunks đã tạo (0 nếu skip do thiếu trong doc_registry, hoặc đang preview).
    """
    file_key = file_path.stem  # tên file không có .docx
    doc_info = get_doc_info(file_key)

    if not doc_info:
        print(f"⚠️  Bỏ qua: '{file_key}' không có trong doc_registry.py")
        print(f"   Hãy thêm key '{file_key}' vào DOCUMENTS trong doc_registry.py")
        return 0

    print(f"📄 Đang xử lý: {file_path.name}")
    print(f"   Số hiệu: {doc_info['so_hieu']}")

    # Parse .docx → cây cấu trúc (Chương → ... → Điểm) + danh sách Phụ lục
    chuong_list, phu_luc_list = parse_docx(str(file_path))

    if preview:
        print_structure(chuong_list, phu_luc_list)
        return 0

    # Build chunks phần chính
    chunks = build_chunks(chuong_list, doc_info)

    # Build chunks phụ lục + link tham chiếu vào chunks chính
    phuluc_chunks = build_phuluc_chunks(phu_luc_list, doc_info)
    if phuluc_chunks:
        link_tham_chieu(chunks, phuluc_chunks)
        chunks.extend(phuluc_chunks)

    print(f"   → {len(chunks)} chunks ({len(chunks) - len(phuluc_chunks)} chính + {len(phuluc_chunks)} phụ lục)")

    # Ghi JSON output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{file_key}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"   → Đã ghi: {output_file}")

    return len(chunks)


# ─── Gộp tất cả JSON thành 1 file ────────────────────────────────────────────

def merge_all_json(output_dir: Path) -> None:
    """Gộp tất cả file JSON trong `output_dir` thành 1 file `all_chunks.json`."""
    all_chunks = []
    json_files = sorted(output_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "all_chunks.json"]

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            all_chunks.extend(chunks)

    merged_file = output_dir / "all_chunks.json"
    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n📦 Đã gộp {len(all_chunks)} chunks từ {len(json_files)} file → {merged_file}")


# ─── CLI entry point ─────────────────────────────────────────────────────────

def main():
    """Parse CLI arguments và điều phối pipeline (1 file / cả thư mục / merge)."""
    parser = argparse.ArgumentParser(description="Trích xuất chunks từ file .docx văn bản pháp luật")
    parser.add_argument("--file",    type=str,                                  help="Đường dẫn 1 file .docx")
    parser.add_argument("--dir",     type=str,                                  help="Thư mục chứa các file .docx")
    parser.add_argument("--output",  type=str, default="../data/processed",     help="Thư mục output JSON")
    parser.add_argument("--preview", action="store_true",                       help="Chỉ xem cấu trúc, không xuất JSON")
    parser.add_argument("--merge",   action="store_true",                       help="Gộp tất cả JSON thành all_chunks.json")
    args = parser.parse_args()

    if not args.file and not args.dir and not args.merge:
        parser.print_help()
        sys.exit(1)

    output_dir = Path(args.output)
    total_chunks = 0

    # Mode 1: xử lý 1 file
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Không tìm thấy file: {file_path}")
            sys.exit(1)
        total_chunks = process_one_file(file_path, output_dir, args.preview)

    # Mode 2: xử lý cả thư mục
    elif args.dir:
        dir_path = Path(args.dir)
        docx_files = sorted(dir_path.glob("*.docx"))
        if not docx_files:
            print(f"❌ Không tìm thấy file .docx trong: {dir_path}")
            sys.exit(1)

        print(f"Tìm thấy {len(docx_files)} file .docx\n")
        for file_path in docx_files:
            count = process_one_file(file_path, output_dir, args.preview)
            total_chunks += count
            print()

    if not args.preview:
        print(f"✅ Tổng: {total_chunks} chunks")

        # Tự động gộp nếu có flag --merge hoặc xử lý nhiều file
        if args.merge or args.dir:
            merge_all_json(output_dir)

        print(f"\n📝 Bước tiếp theo:")
        print(f"   1. Mở các file JSON trong {output_dir} để kiểm tra")
        print(f"   2. Chỉnh sửa noi_dung_tham_chieu cho các chunk cần tham chiếu")
        print(f"   3. Chỉnh sửa hieu_luc cho các điểm bị sửa đổi/bãi bỏ riêng lẻ")
        print(f"   4. Chạy: python run_index.py để đưa vào Qdrant")


if __name__ == "__main__":
    main()
