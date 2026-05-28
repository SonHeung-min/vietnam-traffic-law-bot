"""
run_extract
───────────
Script chính: đọc .docx → parse → tạo chunks → xuất JSON.
Có thể chạy từ bất kỳ thư mục nào (ROOT_DIR tự tính từ vị trí file script).

Cách dùng:

    # Xử lý 1 file
    python preprocessing/run_extract.py --file data/raw/all/Nghị-định-168-2024-NĐ-CP.docx

    # Xử lý toàn bộ .docx trong 1 thư mục (tự động merge thành all_chunks.jsonl)
    python preprocessing/run_extract.py --dir data/raw/all

    # Preview cấu trúc đã parse, KHÔNG xuất JSON
    python preprocessing/run_extract.py --file data/raw/all/Luật-35-2024-QH15.docx --preview

    # Chỉ định thư mục output (mặc định: data/processed/)
    python preprocessing/run_extract.py --dir data/raw/all --output data/processed

    # Chỉ gộp các JSON đã có thành all_chunks.jsonl (không parse lại)
    python preprocessing/run_extract.py --merge --output data/processed
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Import nội bộ hoạt động dù chạy từ root hay từ preprocessing/
HERE = Path(__file__).resolve().parent
ROOT_DIR = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Fix encoding tiếng Việt trên Windows console
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from docx_parser import parse_docx, print_structure
from chunk_builder import build_chunks, link_tham_chieu
from doc_registry import DOCUMENTS


# ─── Xử lý 1 file .docx → JSON ───────────────────────────────────────────────

def process_one_file(file_path: Path, output_dir: Path, preview: bool = False) -> int:
    """
    Pipeline cho 1 file:
        parse .docx → build chunks chính → link tham chiếu phụ lục → ghi JSON

    Trả về số chunks đã tạo (0 nếu skip do thiếu trong doc_registry, hoặc đang preview).
    """
    file_key = file_path.stem  # tên file không có .docx
    doc_info = DOCUMENTS.get(file_key)

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

    # Build chunks phần chính + nhúng nội dung phụ lục vào tham chiếu
    source_file = file_path.resolve().relative_to(ROOT_DIR)
    chunks = build_chunks(chuong_list, doc_info, source_file)
    if phu_luc_list:
        link_tham_chieu(chunks, phu_luc_list)

    print(f"   → {len(chunks)} chunks")

    # Ghi JSON output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{file_key}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"   → Đã ghi: {output_file}")

    return len(chunks)


# ─── Gộp tất cả JSON thành 1 file ────────────────────────────────────────────

def merge_all_json(output_dir: Path) -> None:
    """Gộp tất cả file JSON trong `output_dir` thành `all_chunks.jsonl`."""
    all_chunks = []
    json_files = sorted(output_dir.glob("*.json"))

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            all_chunks.extend(chunks)

    merged_jsonl = output_dir / "all_chunks.jsonl"
    with open(merged_jsonl, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n📦 Đã gộp {len(all_chunks)} chunks từ {len(json_files)} file → {merged_jsonl}")


# ─── CLI entry point ─────────────────────────────────────────────────────────

def main():
    """Parse CLI arguments và điều phối pipeline (1 file / cả thư mục / merge)."""
    parser = argparse.ArgumentParser(description="Trích xuất chunks từ file .docx văn bản pháp luật")
    parser.add_argument("--file",    type=str,                                  help="Đường dẫn 1 file .docx")
    parser.add_argument("--dir",     type=str,                                  help="Thư mục chứa các file .docx")
    parser.add_argument("--preview", action="store_true",                       help="Chỉ xem cấu trúc, không xuất JSON")
    parser.add_argument("--merge",   action="store_true",                       help="Gộp tất cả JSON thành all_chunks.jsonl")
    parser.add_argument("--output",  type=str, default=str(ROOT_DIR / "data" / "processed"),     help="Thư mục output JSON")
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
        print(f"   2. Chỉnh sửa hieu_luc cho các điểm bị sửa đổi/bãi bỏ riêng lẻ")
        print(f"   3. Chạy: python run_index.py để đưa vào Qdrant")


if __name__ == "__main__":
    main()
