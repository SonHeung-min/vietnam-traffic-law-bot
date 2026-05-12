"""
chunk_builder
─────────────
Xây dựng chunks JSON theo schema "raw parts" (các trường nội dung tách riêng).

Mỗi chunk phần chính có 3 trường nội dung độc lập:
    - noi_dung_dieu  : preamble đầu điều (vd "Đối tượng miễn thu phí... bao gồm:")
    - noi_dung_khoan : nội dung đầu khoản (vd "Phạt tiền từ 4.000.000 đồng...")
    - noi_dung_diem  : nội dung 1 điểm (text thuần, KHÔNG có prefix "a)")

Mỗi chunk phụ lục có:
    - noi_dung_phu_luc : phần chung của phụ lục (không thuộc mẫu nào)
    - noi_dung_mau     : nội dung 1 mẫu văn bản cụ thể

Việc ghép thành text cuối cùng để embed được thực hiện ở `run_index.py`
(build_search_text). Như vậy có thể đổi chiến lược chunking / embedding
mà không cần re-parse `.docx`.
"""

import re

from docx_parser import Chuong, Muc, Dieu, Khoan, Diem, PhuLuc
from doc_registry import make_so_hieu_slug
from utils import _roman_to_int


# ─── Regex tìm tham chiếu phụ lục trong nội dung ─────────────────────────────

# Match "Mẫu số 01 Phụ lục III", "Mẫu số 5 Phụ lục VIII"
RE_MAU_PHU_LUC = re.compile(
    r"Mẫu\s+số\s+(\d+\w*)\s+Phụ\s+lục\s+([IVXLCDM]+|\d+)",
    re.IGNORECASE,
)

# Match "Phụ lục II", "Phụ lục III" (không kèm "Mẫu số")
RE_PHU_LUC_REF = re.compile(
    r"Phụ\s+lục\s+([IVXLCDM]+|\d+)",
    re.IGNORECASE,
)


# ─── Helpers build chunk_id & citation ───────────────────────────────────────

def _build_chunk_id(so_hieu_slug: str, dieu_so: int, khoan_so: int | None, diem: str | None) -> str:
    """
    Format chunk_id:
        168-2024-ND-CP_d7_k3_da     (Điều 7, Khoản 3, điểm a)
        168-2024-ND-CP_d7_k10       (Điều 7, Khoản 10, không có điểm)
        168-2024-ND-CP_d7           (Điều 7, không có khoản)
    """
    chunk_id = f"{so_hieu_slug}_d{dieu_so}"
    if khoan_so is not None:
        chunk_id += f"_k{khoan_so}"
    if diem:
        chunk_id += f"_d{diem}"
    return chunk_id


def _build_citation(dieu_so: int, khoan_so: int | None, diem_ky_hieu: str | None, so_hieu: str) -> str:
    """
    Citation theo convention pháp luật Việt Nam (nhỏ → lớn):
        'điểm a khoản 3 Điều 7 Nghị định 168/2024/NĐ-CP'
        'khoản 10 Điều 7 Nghị định 168/2024/NĐ-CP'
        'Điều 1 Luật 35/2024/QH15'
    """
    parts = []
    if diem_ky_hieu:
        parts.append(f"điểm {diem_ky_hieu}")
    if khoan_so is not None:
        parts.append(f"khoản {khoan_so}")
    parts.append(f"Điều {dieu_so}")
    location = " ".join(parts)

    if "QH" in so_hieu:
        prefix = "Luật"
    elif "NĐ-CP" in so_hieu:
        prefix = "Nghị định"
    elif "TT" in so_hieu:
        prefix = "Thông tư"
    else:
        prefix = ""

    return f"{location} {prefix} {so_hieu}".strip()


# ─── Build chunks cho phần chính (Chương → ... → Điểm) ───────────────────────

def build_chunks(
    chuong_list: list[Chuong],
    doc_info: dict,
) -> list[dict]:
    """
    Xây dựng list chunk JSON từ cấu trúc đã parse + thông tin văn bản.

    Mỗi chunk = 1 điểm (hoặc 1 khoản nếu không có điểm; hoặc 1 điều nếu
    không có khoản). Các trường nội dung được giữ TÁCH RIÊNG, không ghép trước.
    """
    so_hieu = doc_info["so_hieu"]
    so_hieu_slug = make_so_hieu_slug(so_hieu)
    ngay_hieu_luc = doc_info.get("ngay_hieu_luc", "")

    chunks = []

    for chuong in chuong_list:
        for muc in chuong.muc_list:
            for dieu in muc.dieu_list:

                if not dieu.khoan_list:
                    # Điều không có khoản → 1 chunk cho cả điều
                    chunks.append(_build_one_chunk(
                        so_hieu=so_hieu,
                        so_hieu_slug=so_hieu_slug,
                        doc_info=doc_info,
                        chuong=chuong, muc=muc, dieu=dieu,
                        khoan=None, diem=None,
                        noi_dung_dieu=dieu.noi_dung,
                        noi_dung_khoan="",
                        noi_dung_diem="",
                        ngay_hieu_luc=ngay_hieu_luc,
                    ))
                    continue

                for khoan in dieu.khoan_list:

                    if khoan.diem_list:
                        # Khoản có điểm → 1 chunk cho mỗi điểm
                        for diem in khoan.diem_list:
                            chunks.append(_build_one_chunk(
                                so_hieu=so_hieu,
                                so_hieu_slug=so_hieu_slug,
                                doc_info=doc_info,
                                chuong=chuong, muc=muc, dieu=dieu,
                                khoan=khoan, diem=diem,
                                noi_dung_dieu=dieu.noi_dung,
                                noi_dung_khoan=khoan.noi_dung,
                                noi_dung_diem=diem.noi_dung,
                                ngay_hieu_luc=ngay_hieu_luc,
                            ))
                    else:
                        # Khoản không có điểm → 1 chunk cho cả khoản
                        chunks.append(_build_one_chunk(
                            so_hieu=so_hieu,
                            so_hieu_slug=so_hieu_slug,
                            doc_info=doc_info,
                            chuong=chuong, muc=muc, dieu=dieu,
                            khoan=khoan, diem=None,
                            noi_dung_dieu=dieu.noi_dung,
                            noi_dung_khoan=khoan.noi_dung,
                            noi_dung_diem="",
                            ngay_hieu_luc=ngay_hieu_luc,
                        ))

    return chunks


def _build_one_chunk(
    *,
    so_hieu: str,
    so_hieu_slug: str,
    doc_info: dict,
    chuong: Chuong,
    muc: Muc,
    dieu: Dieu,
    khoan: Khoan | None,
    diem: Diem | None,
    noi_dung_dieu: str,
    noi_dung_khoan: str,
    noi_dung_diem: str,
    ngay_hieu_luc: str,
) -> dict:
    """Tạo 1 chunk JSON theo schema "raw parts" (3 trường nội dung tách riêng)."""

    diem_ky_hieu = diem.ky_hieu if diem else None
    khoan_so = khoan.so if khoan else None

    hieu_luc = {
        "ngay_hieu_luc":     ngay_hieu_luc,
        "ngay_het_hieu_luc": None,
        "con_hieu_luc":      True,
        "loai_thay_doi":     None,
        "bi_sua_doi_boi":    None,
        "ghi_chu":           None,
    }

    return {
        "chunk_id": _build_chunk_id(so_hieu_slug, dieu.so, khoan_so, diem_ky_hieu),

        "van_ban": {
            "so_hieu":       so_hieu,
            "loai_van_ban":  doc_info["loai_van_ban"],
            "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
        },

        "vi_tri": {
            "chuong_so":  chuong.so,
            "chuong_ten": chuong.ten,
            "muc_so":     muc.so,
            "muc_ten":    muc.ten,
            "dieu_so":    dieu.so,
            "dieu_ten":   dieu.ten,
            "khoan_so":   khoan_so,
            "diem":       diem_ky_hieu,
        },

        "noi_dung_dieu":  noi_dung_dieu or "",
        "noi_dung_khoan": noi_dung_khoan or "",
        "noi_dung_diem":  noi_dung_diem or "",

        "noi_dung_tham_chieu": [],

        "citation": _build_citation(dieu.so, khoan_so, diem_ky_hieu, so_hieu),

        "hieu_luc": hieu_luc,
    }


# ─── Build chunks cho phụ lục ────────────────────────────────────────────────

def build_phuluc_chunks(
    phu_luc_list: list[PhuLuc],
    doc_info: dict,
) -> list[dict]:
    """
    Tạo chunk JSON cho mỗi phụ lục và mẫu văn bản.

    Chunk_id:
        - Phụ lục không có mẫu : 165-2024-ND-CP_pl2
        - Mẫu trong phụ lục    : 165-2024-ND-CP_pl3_m01

    Trường nội dung tách riêng:
        - noi_dung_phu_luc : nội dung chung của phụ lục (không thuộc mẫu nào)
        - noi_dung_mau     : nội dung 1 mẫu cụ thể
    """
    so_hieu = doc_info["so_hieu"]
    so_hieu_slug = make_so_hieu_slug(so_hieu)
    ngay_hieu_luc = doc_info.get("ngay_hieu_luc", "")

    if "QH" in so_hieu:
        prefix = "Luật"
    elif "NĐ-CP" in so_hieu:
        prefix = "Nghị định"
    elif "TT" in so_hieu:
        prefix = "Thông tư"
    else:
        prefix = ""

    hieu_luc = {
        "ngay_hieu_luc":     ngay_hieu_luc,
        "ngay_het_hieu_luc": None,
        "con_hieu_luc":      True,
        "loai_thay_doi":     None,
        "bi_sua_doi_boi":    None,
        "ghi_chu":           None,
    }

    chunks = []

    for pl in phu_luc_list:
        pl_so = pl.so  # đã là int từ parser

        if pl.mau_list:
            # Phụ lục có mẫu → 1 chunk cho mỗi mẫu
            for mau in pl.mau_list:
                chunks.append({
                    "chunk_id": f"{so_hieu_slug}_pl{pl_so}_m{mau.so}",
                    "van_ban": {
                        "so_hieu":       so_hieu,
                        "loai_van_ban":  doc_info["loai_van_ban"],
                        "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
                    },
                    "vi_tri": {
                        "phu_luc_so":  pl_so,
                        "phu_luc_ten": pl.ten,
                        "mau_so":      mau.so,
                        "mau_ten":     mau.ten,
                    },
                    "noi_dung_phu_luc": "",
                    "noi_dung_mau":     mau.noi_dung or "",
                    "noi_dung_tham_chieu": [],
                    "citation": f"Mẫu số {mau.so} Phụ lục {pl_so} {prefix} {so_hieu}".strip(),
                    "hieu_luc": hieu_luc,
                })
        else:
            # Phụ lục không có mẫu → 1 chunk cho cả phụ lục
            chunks.append({
                "chunk_id": f"{so_hieu_slug}_pl{pl_so}",
                "van_ban": {
                    "so_hieu":       so_hieu,
                    "loai_van_ban":  doc_info["loai_van_ban"],
                    "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
                },
                "vi_tri": {
                    "phu_luc_so":  pl_so,
                    "phu_luc_ten": pl.ten,
                    "mau_so":      None,
                    "mau_ten":     None,
                },
                "noi_dung_phu_luc": pl.noi_dung or "",
                "noi_dung_mau":     "",
                "noi_dung_tham_chieu": [],
                "citation": f"Phụ lục {pl_so} {prefix} {so_hieu}".strip(),
                "hieu_luc": hieu_luc,
            })

    return chunks


# ─── Link tham chiếu phụ lục vào chunks phần chính ───────────────────────────

def link_tham_chieu(chunks: list[dict], phuluc_chunks: list[dict]) -> None:
    """
    Scan nội dung mỗi chunk phần chính, tìm tham chiếu phụ lục,
    gán danh sách chunk_id phụ lục vào noi_dung_tham_chieu.

    Sửa trực tiếp (in-place), không trả về.
    """
    # Build lookup: (phu_luc_so, mau_so | None) → chunk_id
    lookup: dict[tuple, str] = {}
    for pc in phuluc_chunks:
        vt = pc["vi_tri"]
        pl_so = vt["phu_luc_so"]
        mau_so = vt.get("mau_so")
        lookup[(pl_so, mau_so)] = pc["chunk_id"]

    for chunk in chunks:
        # Ghép tạm các trường nội dung để scan tham chiếu
        text_parts = [
            chunk.get("noi_dung_dieu", ""),
            chunk.get("noi_dung_khoan", ""),
            chunk.get("noi_dung_diem", ""),
        ]
        text = "\n".join(p for p in text_parts if p)

        refs: list[str] = []
        seen: set[str] = set()

        # Tìm "Mẫu số X Phụ lục Y" trước (cụ thể nhất, ưu tiên)
        for m in RE_MAU_PHU_LUC.finditer(text):
            mau_so = m.group(1)
            pl_so = _roman_to_int(m.group(2))
            cid = lookup.get((pl_so, mau_so)) or lookup.get((pl_so, mau_so.zfill(2)))
            if cid and cid not in seen:
                refs.append(cid)
                seen.add(cid)

        # Tìm "Phụ lục Y" đơn lẻ (không kèm mẫu số)
        for m in RE_PHU_LUC_REF.finditer(text):
            pl_so = _roman_to_int(m.group(1))
            cid = lookup.get((pl_so, None))
            if cid and cid not in seen:
                refs.append(cid)
                seen.add(cid)

        chunk["noi_dung_tham_chieu"] = refs
