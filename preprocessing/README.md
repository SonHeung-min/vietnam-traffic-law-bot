# preprocessing

Pipeline trích xuất văn bản pháp luật giao thông Việt Nam từ `.docx` → JSON chunks → `all_chunks.jsonl`, phục vụ indexing vào Qdrant cho hệ thống RAG.

---

## Mục lục

1. [Cấu trúc thư mục](#1-cấu-trúc-thư-mục)
2. [Cài đặt](#2-cài-đặt)
3. [Cách dùng nhanh](#3-cách-dùng-nhanh)
4. [Các flag CLI](#4-các-flag-cli)
5. [Pipeline hoạt động như thế nào](#5-pipeline-hoạt-động-như-thế-nào)
6. [Quy tắc tách chunk](#6-quy-tắc-tách-chunk)
7. [Schema chunk output](#7-schema-chunk-output)
8. [Thêm văn bản mới](#8-thêm-văn-bản-mới)
9. [Mô tả từng module](#9-mô-tả-từng-module)

---

## 1. Cấu trúc thư mục

```
preprocessing/
├── run_extract.py      # Entry point CLI — điều phối toàn bộ pipeline
├── docx_parser.py      # Parse .docx → cây Chương/Mục/Điều/Khoản/Điểm + Phụ lục
├── chunk_builder.py    # Chuyển cây đã parse → list chunk JSON
├── doc_registry.py     # Registry metadata các văn bản (số hiệu, ngày hiệu lực...)
├── utils.py            # Helper: chuyển số La Mã → số nguyên
├── requirements.txt
└── README.md
```

Luồng dữ liệu:

```
data/raw/all/*.docx
        │
        ▼  run_extract.py
data/processed/<tên-file>.json     ← 1 file JSON per docx
data/processed/all_chunks.jsonl    ← tất cả chunks gộp lại (1 chunk / dòng)
```

---

## 2. Cài đặt

```bash
pip install -r preprocessing/requirements.txt
```

Dependency duy nhất: `python-docx==1.1.2`.

---

## 3. Cách dùng nhanh

Chạy từ **thư mục gốc project** (script tự resolve đường dẫn):

```bash
# Xử lý 1 file
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-168-2024-NĐ-CP.docx

# Xử lý toàn bộ .docx trong thư mục → tự động merge thành all_chunks.jsonl
python preprocessing/run_extract.py --dir data/raw/all

# Chỉ định thư mục output khác
python preprocessing/run_extract.py --dir data/raw/all --output data/processed_v2

# Preview cấu trúc parse (Chương/Điều/Khoản/Điểm), KHÔNG ghi file
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-168-2024-NĐ-CP.docx --preview

# Chỉ gộp các JSON đã có → all_chunks.jsonl (không parse lại)
python preprocessing/run_extract.py --merge --output data/processed
```

---

## 4. Các flag CLI

| Flag | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `--file` | string | — | Đường dẫn 1 file `.docx` cần xử lý |
| `--dir` | string | — | Thư mục chứa các file `.docx` (xử lý tất cả) |
| `--output` | string | `data/processed` | Thư mục ghi JSON output |
| `--preview` | flag | false | In cấu trúc parse, không ghi file |
| `--merge` | flag | false | Gộp tất cả JSON trong `--output` thành `all_chunks.jsonl` |

> Khi dùng `--dir`, `--merge` được gọi tự động sau khi xử lý xong tất cả file.

---

## 5. Pipeline hoạt động như thế nào

```
.docx
  │
  ▼ docx_parser.parse_docx()
  ┌─────────────────────────────────────┐
  │ Cây cấu trúc:                       │
  │   Chuong → Muc → Dieu → Khoan → Diem│
  │   PhuLuc[]                          │
  └─────────────────────────────────────┘
  │
  ▼ chunk_builder.build_chunks()
  list[dict] — mỗi dict là 1 chunk
  │
  ▼ chunk_builder.link_tham_chieu()   ← chỉ chạy nếu có phụ lục
  Scan page_content, nhúng nội dung phụ lục vào noi_dung_tham_chieu
  │
  ▼ json.dump()
  data/processed/<tên-file>.json
  │
  ▼ merge_all_json()                  ← chạy sau khi xử lý hết --dir
  data/processed/all_chunks.jsonl
```

**Parser** dùng state machine: duyệt từng block (Paragraph / Table) theo đúng thứ tự trong document body, nhận diện heading bằng regex, cập nhật con trỏ cấu trúc hiện tại (`current_chuong`, `current_muc`, `current_dieu`, `current_khoan`). Bảng (`<w:tbl>`) được chuyển thành markdown table và gắn vào phần tử cha gần nhất (điểm → khoản → điều).

**Phụ lục** được tách riêng: parser tìm vị trí xuất hiện đầu tiên của `Phụ lục` mà sau đó không còn `Điều` nào nữa — từ đó trở đi là phần phụ lục. Phụ lục không tạo chunk riêng mà được nhúng inline vào chunk phần chính khi có tham chiếu.

---

## 6. Quy tắc tách chunk

| Cấu trúc Điều | Đơn vị chunk |
|---|---|
| Điều có Khoản, Khoản có Điểm | 1 chunk **mỗi Điểm** |
| Điều có Khoản, Khoản không có Điểm | 1 chunk **mỗi Khoản** |
| Điều không có Khoản | 1 chunk **cho cả Điều** |

Mỗi chunk mang theo đầy đủ context cấp trên (tên Chương, tên Mục, tên Điều, nội dung Khoản cha) để truy vấn độc lập mà không mất ngữ cảnh.

**`chunk_id`** format: `{so_hieu_slug}_d{dieu}[_k{khoan}[_d{diem}]]`

Ví dụ:
- `168_2024_NĐ_CP_d7` — Điều 7 (không có khoản)
- `168_2024_NĐ_CP_d7_k3` — Điều 7, Khoản 3 (không có điểm)
- `168_2024_NĐ_CP_d7_k3_da` — Điều 7, Khoản 3, điểm a

`so_hieu_slug` = số hiệu với `/` và `-` thay bằng `_` (vd `168/2024/NĐ-CP` → `168_2024_NĐ_CP`).

---

## 7. Schema chunk output

Mỗi dòng trong `all_chunks.jsonl` có cấu trúc:

```json
{
  "metadata": {
    "chunk_id":          "168_2024_NĐ_CP_d7_k3_da",
    "so_hieu":           "168/2024/NĐ-CP",
    "ten_van_ban":       "Nghị định quy định xử phạt vi phạm hành chính...",
    "loai_van_ban":      "nghi_dinh",
    "co_quan_ban_hanh":  "Chính phủ",
    "ngay_ban_hanh":     "2024-12-26",
    "ngay_hieu_luc":     "2025-01-01",
    "ngay_het_hieu_luc": null,
    "con_hieu_luc":      true,
    "chuong_so":         2,
    "chuong_ten":        "Xử phạt người điều khiển phương tiện...",
    "muc_so":            1,
    "muc_ten":           "Xử phạt người điều khiển xe ô tô",
    "dieu_so":           7,
    "khoan_so":          3,
    "diem":              "a",
    "source_file":       "data/raw/all/Nghị-định-168-2024-NĐ-CP.docx",
    "dieu_ten":          "Xử phạt người điều khiển xe ô tô vi phạm quy tắc giao thông",
    "noi_dung_dieu":     "Phạt người điều khiển xe ô tô thực hiện một trong các hành vi...",
    "noi_dung_khoan":    "Phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng đối với hành vi:",
    "noi_dung_diem":     "Vượt đèn đỏ hoặc đèn vàng khi đèn đã bật;",
    "level":             3,
    "is_sibling":        false
  },
  "page_content":        "Điều 7: Xử phạt người điều khiển xe ô tô...\nPhạt người điều khiển...\n3. Phạt tiền từ 4.000.000...\na. Vượt đèn đỏ...",
  "noi_dung_tham_chieu": []
}
```

### Mô tả các trường

**Trong `metadata`:**

| Trường | Kiểu | Mô tả |
|---|---|---|
| `chunk_id` | string | Định danh duy nhất của chunk |
| `so_hieu` | string | Số hiệu văn bản (vd `168/2024/NĐ-CP`) |
| `ten_van_ban` | string | Tên đầy đủ văn bản |
| `loai_van_ban` | string | `luat` / `nghi_dinh` / `thong_tu` |
| `co_quan_ban_hanh` | string | Cơ quan ban hành |
| `ngay_ban_hanh` | string | Ngày ban hành `YYYY-MM-DD` |
| `ngay_hieu_luc` | string | Ngày có hiệu lực `YYYY-MM-DD` |
| `ngay_het_hieu_luc` | string\|null | Ngày hết hiệu lực (null nếu còn hiệu lực) |
| `con_hieu_luc` | bool | Văn bản có còn hiệu lực không |
| `chuong_so` | int\|null | Số chương |
| `chuong_ten` | string\|null | Tên chương |
| `muc_so` | int\|null | Số mục (null nếu chương không có mục) |
| `muc_ten` | string\|null | Tên mục |
| `dieu_so` | int | Số điều |
| `khoan_so` | int\|null | Số khoản (null nếu chunk level 1) |
| `diem` | string\|null | Ký hiệu điểm — `a`, `b`, `đ`... (null nếu chunk level 1/2) |
| `source_file` | string | Đường dẫn file `.docx` gốc (POSIX, relative to project root) |
| `dieu_ten` | string | Tên điều |
| `noi_dung_dieu` | string | Preamble đầu điều |
| `noi_dung_khoan` | string | Nội dung khoản cha (rỗng nếu level 1) |
| `noi_dung_diem` | string | Nội dung điểm, không có prefix `a)` (rỗng nếu level 1/2) |
| `level` | int | `1` = Điều / `2` = Khoản / `3` = Điểm |
| `is_sibling` | bool | Luôn `false` (dành cho xử lý hậu kỳ nếu cần) |

**Top-level:**

| Trường | Kiểu | Mô tả |
|---|---|---|
| `page_content` | string | Text ghép sẵn để embed: `"Điều X: tên\npreamble\nN. khoản\na. điểm"` |
| `noi_dung_tham_chieu` | list[string] | Nội dung phụ lục được nhúng inline (rỗng nếu không có tham chiếu) |

---

## 8. Thêm văn bản mới

### Bước 1 — Đặt file vào đúng thư mục

```
data/raw/all/<tên-file>.docx
```

Tên file phải **khớp chính xác** với key trong `doc_registry.py` (phân biệt hoa thường, kể cả dấu gạch ngang).

### Bước 2 — Đăng ký trong `doc_registry.py`

Mở `doc_registry.py` và thêm entry vào dict `DOCUMENTS`:

```python
"Nghị-định-XXX-2025-NĐ-CP": {
    "so_hieu":          "XXX/2025/NĐ-CP",
    "ten_van_ban":      "Nghị định quy định về...",
    "loai_van_ban":     "nghi_dinh",   # luat | nghi_dinh | thong_tu
    "co_quan_ban_hanh": "Chính phủ",
    "ngay_ban_hanh":    "2025-XX-XX",
    "ngay_hieu_luc":    "2025-XX-XX",
    "con_hieu_luc":     True,
},
```

> Nếu bỏ qua bước này, script sẽ in cảnh báo và skip file đó.

### Bước 3 — Preview cấu trúc (tuỳ chọn)

```bash
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-XXX-2025-NĐ-CP.docx --preview
```

Kiểm tra parse đúng chưa trước khi ghi file.

### Bước 4 — Chạy

```bash
python preprocessing/run_extract.py --file data/raw/all/Nghị-định-XXX-2025-NĐ-CP.docx
```

---

## 9. Mô tả từng module

### `run_extract.py`

Entry point CLI. Điều phối pipeline: nhận argument → gọi `parse_docx` → `build_chunks` → `link_tham_chieu` → ghi JSON → merge JSONL.

Hàm chính:
- `process_one_file(file_path, output_dir, preview)` — xử lý 1 file `.docx`, trả về số chunks tạo ra
- `merge_all_json(output_dir)` — gộp tất cả `.json` trong thư mục thành `all_chunks.jsonl`

---

### `docx_parser.py`

Đọc file `.docx` bằng `python-docx`, duyệt từng block theo thứ tự document body, nhận diện cấu trúc bằng regex:

| Pattern | Nhận diện |
|---|---|
| `^Chương [IVXLCDM\d]+` | Chương I, Chương 2... |
| `^Mục \d+` | Mục 1, Mục 3... |
| `^Điều \d+\.?` | Điều 7., Điều 38... |
| `^\d+\. ` | 1. Phạt tiền... (khoản) |
| `^[a-zđ]\) ` | a) Vượt đèn đỏ... (điểm) |
| `^Phụ lục` | Phụ lục I, Phụ lục kèm theo... |

Bảng (`<w:tbl>`) được chuyển thành markdown table, deduplicate cell bị merge ngang, rồi gắn vào phần tử cha gần nhất (điểm → khoản → điều).

**Exports:** `parse_docx()`, `print_structure()`, dataclasses `Chuong`, `Muc`, `Dieu`, `Khoan`, `Diem`, `PhuLuc`.

---

### `chunk_builder.py`

Nhận cây dataclass từ `docx_parser` + metadata từ `doc_registry`, tạo ra list dict JSON theo schema chuẩn.

- `build_chunks(chuong_list, doc_info, file_path)` — duyệt cây theo granularity rules, gọi `_build_one_chunk` cho từng lá
- `link_tham_chieu(chunks, phu_luc_list)` — scan `page_content` của mỗi chunk, tìm regex tham chiếu phụ lục, nhúng nội dung phụ lục dưới dạng chuỗi vào `noi_dung_tham_chieu`

Ba trường `noi_dung_dieu / noi_dung_khoan / noi_dung_diem` được giữ **tách riêng trong `metadata`** để `run_index.py` linh hoạt ghép lại khi cần. `page_content` là bản ghép sẵn dùng để embed.

---

### `doc_registry.py`

Dict `DOCUMENTS` — registry các văn bản pháp luật, key = tên file `.docx` không có extension.

Các trường bắt buộc: `so_hieu`, `ten_van_ban`, `loai_van_ban`, `co_quan_ban_hanh`, `ngay_ban_hanh`, `ngay_hieu_luc`, `con_hieu_luc`.

Các văn bản bị bãi bỏ/thay thế được comment out và ghi chú lý do để dễ tra cứu.

---

### `utils.py`

`_roman_to_int(s)` — chuyển chuỗi số La Mã (`"IV"`, `"XII"`) hoặc số Ả Rập (`"3"`) sang `int`. Dùng trong `docx_parser` (số chương) và `chunk_builder` (số phụ lục).
