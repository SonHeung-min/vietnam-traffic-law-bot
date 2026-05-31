"""
chunk_builder
─────────────
Xây dựng list chunk JSON từ cây cấu trúc đã parse.

Schema mỗi chunk:
    {
        "metadata": {
            "chunk_id"          : slug định danh duy nhất  (vd "168_2024_NĐ_CP_d7_k3_da")
            "so_hieu"           : số hiệu văn bản          (vd "168/2024/NĐ-CP")
            "ten_van_ban"       : tên văn bản
            "loai_van_ban"      : "luat" | "nghi_dinh" | "thong_tu"
            "co_quan_ban_hanh"  : cơ quan ban hành
            "ngay_ban_hanh"     : "YYYY-MM-DD"
            "ngay_hieu_luc"     : "YYYY-MM-DD"
            "ngay_het_hieu_luc" : "YYYY-MM-DD" | null
            "con_hieu_luc"      : bool
            "chuong_so"         : int | None
            "chuong_ten"        : str | None
            "muc_so"            : int | None
            "muc_ten"           : str | None
            "dieu_so"           : int
            "khoan_so"          : int | None
            "diem"              : str | None  (ký hiệu điểm, vd "a", "b", "đ")
            "source_file"       : đường dẫn file .docx gốc (relative to project root, POSIX)
            "dieu_ten"          : tên điều
            "noi_dung_dieu"     : preamble đầu điều        (vd "Điều này quy định...")
            "noi_dung_khoan"    : nội dung đầu khoản       (vd "Phạt tiền từ 4.000.000...")
            "noi_dung_diem"     : nội dung điểm, không có prefix "a)"
            "level"             : 1 (chỉ Điều) | 2 (Khoản) | 3 (Điểm)
            "is_sibling"        : bool — False mặc định
        },
        "page_content"          : str — text ghép sẵn để embed:
                                    "Điều X: tên(\npreamble)\nN. khoản\na. điểm"
        "noi_dung_tham_chieu"   : list[str] — phụ lục được nhúng inline
                                    (do link_tham_chieu() điền sau khi build)
    }

Granularity: 1 chunk = 1 điểm (nếu có) → 1 khoản (nếu không có điểm) → 1 điều (nếu không có khoản).
3 trường nội dung (dieu/khoan/diem) nằm trong metadata.
"""

import re
from pathlib import Path
from docx_parser import Chuong, Muc, Dieu, Khoan, Diem, PhuLuc
from utils import _roman_to_int


# ─── Regex tìm tham chiếu phụ lục trong nội dung ─────────────────────────────

# Match "Phụ lục II", "Phụ lục số 02"...
RE_PHU_LUC_REF = re.compile(
    r"Phụ\s+lục(?:\s+số)?\s+([IVXLCDM]+|\d+)",
    re.IGNORECASE,
)

# Match "Phụ lục kèm theo", "Phụ lục ban hành kèm theo" — phụ lục không đánh số
RE_PHU_LUC_KEM_THEO = re.compile(
    r"Phụ\s+lục\s+(?:ban\s+hành\s+)?kèm\s+theo",
    re.IGNORECASE,
)


# ─── Helpers build chunk_id & citation ───────────────────────────────────────

def _build_chunk_id(so_hieu_slug: str, dieu_so: int, khoan_so: int | None, diem: str | None) -> str:
    """
    Format chunk_id:
        168_2024_ND_CP_d7_k3_da     (Điều 7, Khoản 3, điểm a)
        168_2024_ND_CP_d7_k10       (Điều 7, Khoản 10, không có điểm)
        168_2024_ND_CP_d7           (Điều 7, không có khoản)
    """
    chunk_id = f"{so_hieu_slug}_d{dieu_so}"
    if khoan_so is not None:
        chunk_id += f"_k{khoan_so}"
    if diem:
        chunk_id += f"_d{diem}"
    return chunk_id


# ─── Build chunks cho phần chính (Chương → ... → Điểm) ───────────────────────

def build_chunks(
    chuong_list: list[Chuong],
    doc_info: dict,
    file_path: Path,
) -> list[dict]:
    """
    Xây dựng list chunk JSON từ cấu trúc đã parse + thông tin văn bản.

    Mỗi chunk = 1 điểm (hoặc 1 khoản nếu không có điểm; hoặc 1 điều nếu
    không có khoản). Các trường nội dung được giữ TÁCH RIÊNG, không ghép trước.
    """

    chunks = []

    for chuong in chuong_list:
        for muc in chuong.muc_list:
            for dieu in muc.dieu_list:

                if not dieu.khoan_list:
                    # Điều không có khoản → 1 chunk cho cả điều
                    chunks.append(_build_one_chunk(
                        doc_info=doc_info,
                        source_file=file_path,
                        chuong=chuong, muc=muc, dieu=dieu,
                        khoan=None, diem=None,
                        noi_dung_dieu=dieu.noi_dung,
                        noi_dung_khoan="",
                        noi_dung_diem="",
                    ))
                    continue

                for khoan in dieu.khoan_list:

                    if khoan.diem_list:
                        # Khoản có điểm → 1 chunk cho mỗi điểm
                        for diem in khoan.diem_list:
                            chunks.append(_build_one_chunk(
                                doc_info=doc_info,
                                source_file=file_path,
                                chuong=chuong, muc=muc, dieu=dieu,
                                khoan=khoan, diem=diem,
                                noi_dung_dieu=dieu.noi_dung,
                                noi_dung_khoan=khoan.noi_dung,
                                noi_dung_diem=diem.noi_dung,
                            ))
                    else:
                        # Khoản không có điểm → 1 chunk cho cả khoản
                        chunks.append(_build_one_chunk(
                            doc_info=doc_info,
                            source_file=file_path,
                            chuong=chuong, muc=muc, dieu=dieu,
                            khoan=khoan, diem=None,
                            noi_dung_dieu=dieu.noi_dung,
                            noi_dung_khoan=khoan.noi_dung,
                            noi_dung_diem="",
                        ))

    return chunks


def _build_one_chunk(
    *,
    doc_info: dict,
    source_file: Path,
    chuong: Chuong,
    muc: Muc,
    dieu: Dieu,
    khoan: Khoan | None,
    diem: Diem | None,
    noi_dung_dieu: str,
    noi_dung_khoan: str,
    noi_dung_diem: str,
) -> dict:
    """Tạo 1 chunk JSON theo schema hiện tại: metadata chứa toàn bộ thông tin
    (kể cả 3 trường nội dung dieu/khoan/diem), page_content ghép sẵn để embed."""

    so_hieu_slug = doc_info["so_hieu"].replace("/", "_").replace("-", "_")
    diem_ky_hieu = diem.ky_hieu if diem else None
    khoan_so = khoan.so if khoan else None
    dieu_so = dieu.so
    chunk_id = _build_chunk_id(so_hieu_slug, dieu_so, khoan_so, diem_ky_hieu)

    return {
        "metadata": {
            "chunk_id": chunk_id,

            # Thông tin văn bản
            "so_hieu":             doc_info.get("so_hieu", ""),
            "ten_van_ban":         doc_info.get("ten_van_ban", ""),
            "loai_van_ban":        doc_info.get("loai_van_ban", ""),
            "co_quan_ban_hanh":    doc_info.get("co_quan_ban_hanh", ""),
            "ngay_ban_hanh":       doc_info.get("ngay_ban_hanh", ""),
            "ngay_hieu_luc":       doc_info.get("ngay_hieu_luc", ""),
            "ngay_het_hieu_luc":   None,
            "con_hieu_luc":        doc_info.get("con_hieu_luc", True),

            # Thông tin vị trí trong văn bản
            "chuong_so":  chuong.so,
            "chuong_ten": chuong.ten,
            "muc_so":     muc.so,
            "muc_ten":    muc.ten,
            "dieu_so":    dieu.so,
            "khoan_so":   khoan_so,
            "diem":       diem_ky_hieu,

            "source_file": Path(source_file).as_posix(),
                    
            # Nội dung
            "dieu_ten":   dieu.ten,
            "noi_dung_dieu":  noi_dung_dieu or "",
            "noi_dung_khoan": noi_dung_khoan or "",
            "noi_dung_diem":  noi_dung_diem or "",

            # Level
            "level": 3 if noi_dung_diem else (2 if noi_dung_khoan else 1),

            # Trường anh em cùng điều
            "is_sibling": False
        },

        "page_content": "\n".join(
            [
                f"Điều {dieu.so}: {dieu.ten}" + (f"\n{noi_dung_dieu}" if noi_dung_dieu else ""),
                f"{khoan.so}. {noi_dung_khoan}" if khoan else "",
                f"{diem.ky_hieu}. {noi_dung_diem}" if diem else ""
            ]
        ),

        "noi_dung_tham_chieu": [],
    }


# ─── Link tham chiếu phụ lục vào chunks phần chính ───────────────────────────

def link_tham_chieu(chunks: list[dict], phu_luc_list: list[PhuLuc]) -> None:
    """
    Scan page_content của mỗi chunk, tìm tham chiếu phụ lục (có số hoặc kèm theo),
    nhúng nội dung phụ lục tương ứng dưới dạng chuỗi vào noi_dung_tham_chieu.

    Sửa trực tiếp (in-place), không trả về.
    """
    # Build lookup: phu_luc_so → PhuLuc object
    lookup: dict[int | None, PhuLuc] = {}
    for pl in phu_luc_list:
        lookup[pl.so] = pl

    for chunk in chunks:
        text = chunk.get("page_content", "")

        refs: list[dict] = []
        seen: set[int | None] = set()

        # Phụ lục có số: "Phụ lục II", "Phụ lục số 02"...
        for m in RE_PHU_LUC_REF.finditer(text):
            pl_so_raw = m.group(1)
            pl_so = _roman_to_int(pl_so_raw)
            pl = lookup.get(pl_so)
            if pl and pl_so not in seen:
                refs.append(f"Phụ lục {pl_so_raw}: {pl.ten} {pl.noi_dung}")
                seen.add(pl_so)

        # Phụ lục không đánh số: "Phụ lục kèm theo Nghị định này"
        if RE_PHU_LUC_KEM_THEO.search(text):
            pl = lookup.get(None)
            if pl and None not in seen:
                refs.append(f"Phụ lục kèm theo: {pl.ten} {pl.noi_dung}")
                seen.add(None)

        chunk["noi_dung_tham_chieu"] = refs
