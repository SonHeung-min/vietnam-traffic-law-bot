# preprocessing

Pipeline trích xuất văn bản pháp luật từ `.docx` → chunks JSON → `all_chunks.jsonl`.

---

## Mục lục

1. [Cấu trúc thư mục](#1-cấu-trúc-thư-mục)
2. [Cài đặt](#2-cài-đặt)
3. [Cách dùng nhanh](#3-cách-dùng-nhanh)
4. [Các flag CLI](#4-các-flag-cli)
5. [Pipeline hoạt động như thế nào](#5-pipeline-hoạt-động-như-thế-nào)
6. [Schema chunk output](#6-schema-chunk-output)
7. [Thêm văn bản mới](#7-thêm-văn-bản-mới)
8. [Mô tả từng module](#8-mô-tả-từng-module)
9. [Câu hỏi thường gặp](#9-câu-hỏi-thường-gặp)

---

## 1. Cấu trúc thư mục

```
preprocessing/
├── run_extract.py      # Entry point CLI — orchestrate toàn bộ pipeline
├── docx_parser.py      # Parse .docx → cây Chương/Mục/Điều/Khoản/Điểm + Phụ lục
├── chunk_builder.py    # Chuyển cây đã parse → list chunk JSON
├── doc_registry.py     # Registry metadata ~40 văn bản (số hiệu, ngày hiệu lực...)
├── utils.py            # Helper dùng chung (chuyển số La Mã → số nguyên)
├── requirements.txt
└── README.md
```

Input/Output:

```
data/raw/all/*.docx
        │
        ▼  run_extract.py
data/processed/<tên-file>.json     ← 1 file per docx
data/processed/all_chunks.jsonl    ← gộp tất cả (1 chunk/dòng)
```

---

## 2. Cài đặt

```bash
pip install -r preprocessing/requirements.txt
```

Dependency duy nhất: `python-docx==1.1.2`.

---

## 3. Cách dùng nhanh

Chạy từ **thư mục gốc project** (hoặc bất kỳ đâu — script tự resolve path):

```bash
# Xử lý 1 file
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-168-2024-NĐ-CP.docx

# Xử lý toàn bộ .docx trong 1 thư mục → tự động merge thành all_chunks.jsonl
python preprocessing/run_extract.py --dir data/raw/all

# Preview cấu trúc parse (Chương/Điều/Khoản/Điểm), KHÔNG ghi file
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-168-2024-NĐ-CP.docx --preview

# Chỉ gộp các JSON đã có → all_chunks.jsonl (không parse lại)
python preprocessing/run_extract.py --merge

# Chỉ định thư mục output khác
python preprocessing/run_extract.py --dir data/raw/all --output data/processed_v2
```

---

## 4. Các flag CLI

| Flag | Kiểu | Mặc định | Mô tả |
|------|------|----------|-------|
| `--file` | string | — | Đường dẫn 1 file `.docx` cần xử lý |
| `--dir` | string | — | Thư mục chứa các file `.docx` (xử lý tất cả) |
| `--output` | string | `data/processed` | Thư mục ghi JSON output |
| `--preview` | flag | false | In cấu trúc parse, không ghi file |
| `--merge` | flag | false | Gộp tất cả JSON trong `--output` thành `all_chunks.jsonl` |

> Khi dùng `--dir`, `--merge` được gọi tự động sau khi xử lý xong.

---

## 5. Pipeline hoạt động như thế nào

```
.docx
  │
  ▼ docx_parser.parse_docx()
  Cây cấu trúc:
    Chuong → Muc → Dieu → Khoan → Diem
    PhuLuc[]
  │
  ▼ chunk_builder.build_chunks()
  list[dict] — mỗi dict là 1 chunk (nội dung tách riêng)
  │
  ▼ chunk_builder.link_tham_chieu()   (nếu có phụ lục)
  Nhúng nội dung phụ lục vào noi_dung_tham_chieu của chunk tương ứng
  │
  ▼ json.dump()
  <tên-file>.json
```

### Quy tắc tách chunk (granularity)

| Cấu trúc điều | Số chunk tạo ra |
|---|---|
| Điều có khoản, khoản có điểm | 1 chunk **mỗi điểm** |
| Điều có khoản, khoản không có điểm | 1 chunk **mỗi khoản** |
| Điều không có khoản | 1 chunk **cho cả điều** |

### Phụ lục

Phụ lục không tạo chunk riêng. Khi một chunk phần chính có tham chiếu đến phụ lục
(vd _"Phụ lục II"_, _"Phụ lục kèm theo Nghị định này"_), nội dung phụ lục được
**nhúng trực tiếp** vào trường `noi_dung_tham_chieu` của chunk đó.

---

## 6. Schema chunk output

Xem chi tiết tại [`docs/data_schema.md`](../docs/data_schema.md).

Tóm tắt nhanh:

```json
{
  "metadata": {
    "chunk_id":           "168_2024_NĐ_CP_d7_k3_da",
    "so_hieu":            "168/2024/NĐ-CP",
    "ten_van_ban":        "Nghị định quy định xử phạt vi phạm hành chính...",
    "loai_van_ban":       "nghi_dinh",
    "co_quan_ban_hanh":   "Chính phủ",
    "ngay_ban_hanh":      "2024-12-26",
    "ngay_hieu_luc":      "2025-01-01",
    "ngay_het_hieu_luc":  null,
    "con_hieu_luc":       true,
    "chuong_so":          2,
    "chuong_ten":         "Xử phạt người điều khiển phương tiện...",
    "muc_so":             1,
    "muc_ten":            "Xử phạt người điều khiển xe ô tô",
    "dieu_so":            7,
    "khoan_so":           3,
    "diem":               "a",
    "source_file":        "data/raw/all/Nghị-định-168-2024-NĐ-CP.docx"
  },
  "dieu_ten":             "Xử phạt người điều khiển xe ô tô vi phạm quy tắc giao thông",
  "noi_dung_dieu":        "Phạt người điều khiển xe ô tô thực hiện một trong các hành vi...",
  "noi_dung_khoan":       "Phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng đối với hành vi:",
  "noi_dung_diem":        "Vượt đèn đỏ hoặc đèn vàng khi đã bật;",
  "noi_dung_tham_chieu":  []
}
```

**`chunk_id`** format: `{so_hieu_slug}_d{dieu}[_k{khoan}[_d{diem}]]`  
`so_hieu_slug` = số hiệu với `/` và `-` thay bằng `_` (vd `168/2024/NĐ-CP` → `168_2024_NĐ_CP`).

---

## 7. Thêm văn bản mới

### Bước 1 — Đặt file vào đúng thư mục

```
data/raw/all/<tên-file>.docx
```

Tên file phải **khớp chính xác** với key trong `doc_registry.py`.

### Bước 2 — Đăng ký trong `doc_registry.py`

Mở `doc_registry.py` và thêm entry vào dict `DOCUMENTS`:

```python
"Nghị-định-XXX-2025-NĐ-CP": {
    "so_hieu":          "XXX/2025/NĐ-CP",
    "ten_van_ban":      "Nghị định quy định về...",
    "loai_van_ban":     "nghi_dinh",        # luat | nghi_dinh | thong_tu
    "co_quan_ban_hanh": "Chính phủ",
    "ngay_ban_hanh":    "2025-XX-XX",
    "ngay_hieu_luc":    "2025-XX-XX",
    "con_hieu_luc":     True,
},
```

> Nếu bỏ qua bước này, script sẽ in cảnh báo và skip file đó.

### Bước 3 — Chạy

```bash
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-XXX-2025-NĐ-CP.docx
```

Kiểm tra output bằng `--preview` trước nếu muốn xem cấu trúc parse:

```bash
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-XXX-2025-NĐ-CP.docx --preview
```

---

## 8. Mô tả từng module

### `docx_parser.py`

Đọc file `.docx` bằng `python-docx`, duyệt từng block (Paragraph / Table) và nhận diện
heading theo regex:

| Pattern | Ví dụ |
|---------|-------|
| `^Chương [IVXLCDM\d]+` | `Chương I`, `Chương 2` |
| `^Mục \d+` | `Mục 1`, `Mục 3` |
| `^Điều \d+\.?` | `Điều 7.`, `Điều 38` |
| `^\d+\. ` | `1. Phạt tiền...` (khoản) |
| `^[a-zđ]\) ` | `a) Vượt đèn đỏ...` (điểm) |
| `^Phụ lục` | `Phụ lục I`, `Phụ lục kèm theo` |

Bảng (`<w:tbl>`) được chuyển thành markdown table và gắn vào phần tử cha gần nhất
(điểm → khoản → điều).

Phụ lục được tách riêng: script tìm vị trí xuất hiện đầu tiên của `Phụ lục` mà sau đó
không còn `Điều` nào nữa → từ đó trở đi là phần phụ lục.

**Exports:** `parse_docx()`, `print_structure()`, dataclasses `Chuong Muc Dieu Khoan Diem PhuLuc`.

---

### `chunk_builder.py`

Nhận cây dataclass từ `docx_parser` + metadata từ `doc_registry`, tạo ra list dict JSON.

- `build_chunks(chuong_list, doc_info, file_path)` — duyệt cây, gọi `_build_one_chunk` cho từng lá.
- `link_tham_chieu(chunks, phu_luc_list)` — scan `noi_dung_*` của mỗi chunk, tìm regex phụ lục,
  nhúng object `{phu_luc_so, phu_luc_ten, noi_dung}` vào `noi_dung_tham_chieu`.

Nội dung ba trường `noi_dung_dieu / noi_dung_khoan / noi_dung_diem` được giữ **tách riêng**
để `run_index.py` linh hoạt ghép khi build search text cho embedding.

---

### `doc_registry.py`

Dict `DOCUMENTS` — registry ~40 văn bản, key = tên file `.docx` không có extension.

Các trường bắt buộc cho mỗi entry: `so_hieu`, `ten_van_ban`, `loai_van_ban`,
`co_quan_ban_hanh`, `ngay_ban_hanh`, `ngay_hieu_luc`, `con_hieu_luc`.

---

### `utils.py`

`_roman_to_int(s)` — chuyển chuỗi La Mã (`"IV"`, `"XII"`) hoặc số Ả Rập (`"3"`) sang `int`.
Dùng trong `docx_parser` (số chương) và `chunk_builder` (số phụ lục).

---
