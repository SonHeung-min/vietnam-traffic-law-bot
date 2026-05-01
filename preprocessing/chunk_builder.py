"""
Xây dựng chunks theo data_schema.md từ cấu trúc đã parse.

Mỗi chunk = 1 điểm (hoặc 1 khoản nếu khoản không có điểm).
noi_dung = đầu khoản (mức phạt) + nội dung điểm.
"""

import re
from collections import OrderedDict
from docx_parser import Chuong, Muc, Dieu, Khoan, Diem, PhuLuc, MauVanBan
from doc_registry import make_so_hieu_slug


# Regex tìm tham chiếu phụ lục trong nội dung
# "Mẫu số 01 Phụ lục III", "Mẫu số 5 Phụ lục VIII", "Phụ lục II"
RE_MAU_PHU_LUC = re.compile(
    r"Mẫu\s+số\s+(\d+\w*)\s+Phụ\s+lục\s+([IVXLCDM]+|\d+)",
    re.IGNORECASE,
)
RE_PHU_LUC_REF = re.compile(
    r"Phụ\s+lục\s+([IVXLCDM]+|\d+)",
    re.IGNORECASE,
)


def _build_chunk_id(so_hieu_slug: str, dieu_so: int, khoan_so: int | None, diem: str | None) -> str:
    """
    Tạo chunk_id theo quy tắc:
    168-2024-ND-CP_d7_k3_da
    168-2024-ND-CP_d7_k10     (nếu không có điểm)
    168-2024-ND-CP_d7          (nếu không có khoản)
    """
    chunk_id = f"{so_hieu_slug}_d{dieu_so}"
    if khoan_so is not None:
        chunk_id += f"_k{khoan_so}"
    if diem:
        chunk_id += f"_d{diem}"
    return chunk_id


def _build_citation(dieu_so: int, khoan_so: int | None, diem: str | None, so_hieu: str) -> str:
    """
    Tạo citation:
    'Điều 7 Khoản 3 Điểm a, Nghị định 168/2024/NĐ-CP'
    'Điều 7 Khoản 10, Nghị định 168/2024/NĐ-CP'
    'Điều 1, Luật 35/2024/QH15'  (nếu không có khoản)
    """
    parts = [f"Điều {dieu_so}"]
    if khoan_so is not None:
        parts.append(f"Khoản {khoan_so}")
    if diem:
        parts.append(f"Điểm {diem}")
    location = " ".join(parts)

    # Tên loại văn bản từ số hiệu
    if "QH" in so_hieu:
        prefix = "Luật"
    elif "NĐ-CP" in so_hieu:
        prefix = "Nghị định"
    elif "TT" in so_hieu:
        prefix = "Thông tư"
    else:
        prefix = ""

    return f"{location}, {prefix} {so_hieu}"


def _build_noi_dung_for_diem(khoan: Khoan, diem: Diem) -> str:
    """
    Ghép: đầu khoản (mức phạt) + nội dung điểm.
    Ví dụ:
        'Phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng...:
        a) Vượt đèn đỏ hoặc đèn vàng khi đã bật;'
    """
    return f"{khoan.noi_dung}\n{diem.ky_hieu}) {diem.noi_dung}"


def build_chunks(
    chuong_list: list[Chuong],
    doc_info: dict,
) -> list[dict]:
    """
    Xây dựng list chunk JSON từ cấu trúc đã parse + thông tin văn bản.

    Args:
        chuong_list: Kết quả từ docx_parser.parse_docx()
        doc_info: Thông tin văn bản từ doc_registry

    Returns:
        list[dict]: Danh sách chunks theo data_schema
    """
    so_hieu = doc_info["so_hieu"]
    so_hieu_slug = make_so_hieu_slug(so_hieu)
    con_hieu_luc = doc_info.get("con_hieu_luc", True)
    ngay_hieu_luc = doc_info.get("ngay_hieu_luc", "")
    thay_the_boi = doc_info.get("thay_the_boi")

    chunks = []

    for chuong in chuong_list:
        for muc in chuong.muc_list:
            for dieu in muc.dieu_list:

                if not dieu.khoan_list:
                    # Điều không có khoản → 1 chunk cho cả điều
                    noi_dung = dieu.noi_dung or dieu.ten
                    chunk = _build_one_chunk(
                        so_hieu=so_hieu,
                        so_hieu_slug=so_hieu_slug,
                        doc_info=doc_info,
                        chuong=chuong,
                        muc=muc,
                        dieu=dieu,
                        khoan=None,
                        diem=None,
                        noi_dung=noi_dung,
                        con_hieu_luc=con_hieu_luc,
                        ngay_hieu_luc=ngay_hieu_luc,
                        thay_the_boi=thay_the_boi,
                    )
                    chunks.append(chunk)
                    continue

                for khoan in dieu.khoan_list:

                    if khoan.diem_list:
                        # Khoản có điểm → tạo 1 chunk cho mỗi điểm
                        for diem in khoan.diem_list:
                            chunk = _build_one_chunk(
                                so_hieu=so_hieu,
                                so_hieu_slug=so_hieu_slug,
                                doc_info=doc_info,
                                chuong=chuong,
                                muc=muc,
                                dieu=dieu,
                                khoan=khoan,
                                diem=diem,
                                noi_dung=_build_noi_dung_for_diem(khoan, diem),
                                con_hieu_luc=con_hieu_luc,
                                ngay_hieu_luc=ngay_hieu_luc,
                                thay_the_boi=thay_the_boi,
                            )
                            chunks.append(chunk)
                    else:
                        # Khoản không có điểm → 1 chunk cho cả khoản
                        chunk = _build_one_chunk(
                            so_hieu=so_hieu,
                            so_hieu_slug=so_hieu_slug,
                            doc_info=doc_info,
                            chuong=chuong,
                            muc=muc,
                            dieu=dieu,
                            khoan=khoan,
                            diem=None,
                            noi_dung=khoan.noi_dung,
                            con_hieu_luc=con_hieu_luc,
                            ngay_hieu_luc=ngay_hieu_luc,
                            thay_the_boi=thay_the_boi,
                        )
                        chunks.append(chunk)

    return chunks


def _build_one_chunk(
    so_hieu: str,
    so_hieu_slug: str,
    doc_info: dict,
    chuong: Chuong,
    muc: Muc,
    dieu: Dieu,
    khoan: Khoan | None,
    diem: Diem | None,
    noi_dung: str,
    con_hieu_luc: bool,
    ngay_hieu_luc: str,
    thay_the_boi: str | None,
) -> dict:
    """Tạo 1 chunk JSON theo đúng data_schema."""

    diem_ky_hieu = diem.ky_hieu if diem else None
    khoan_so = khoan.so if khoan else None

    # Hiệu lực
    hieu_luc = {
        "ngay_hieu_luc": ngay_hieu_luc,
        "ngay_het_hieu_luc": None,
        "con_hieu_luc": True,
        "loai_thay_doi": None,
        "bi_sua_doi_boi": None,
        "ghi_chu": None,
    }

    return {
        "chunk_id": _build_chunk_id(so_hieu_slug, dieu.so, khoan_so, diem_ky_hieu),

        "van_ban": {
            "so_hieu": so_hieu,
            "loai_van_ban": doc_info["loai_van_ban"],
            "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
        },

        "vi_tri": {
            "chuong_so": chuong.so,
            "chuong_ten": chuong.ten,
            "muc_so": muc.so,
            "muc_ten": muc.ten,
            "dieu_so": dieu.so,
            "dieu_ten": dieu.ten,
            "khoan_so": khoan_so,
            "diem": diem_ky_hieu,
        },

        "noi_dung": noi_dung,

        "noi_dung_tham_chieu": None,  # Điền sau khi review JSON

        "citation": _build_citation(dieu.so, khoan_so, diem_ky_hieu, so_hieu),

        "hieu_luc": hieu_luc,
    }


# ── Helper: chuyển La Mã → int (dùng cho tham chiếu phụ lục) ────────────────

def _roman_to_int(roman: str) -> int:
    if roman.isdigit():
        return int(roman)
    roman = roman.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    for i, ch in enumerate(roman):
        if i + 1 < len(roman) and values.get(ch, 0) < values.get(roman[i + 1], 0):
            result -= values.get(ch, 0)
        else:
            result += values.get(ch, 0)
    return result


# ── Build chunks cho phụ lục ────────────────────────────────────────────────

def build_phuluc_chunks(
    phu_luc_list: list[PhuLuc],
    doc_info: dict,
) -> list[dict]:
    """
    Tạo chunk JSON cho mỗi phụ lục và mẫu văn bản.

    Chunk_id format:
      - Phụ lục không có mẫu: 165-2024-ND-CP_pl2
      - Mẫu trong phụ lục:   165-2024-ND-CP_pl3_m01
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
        "ngay_hieu_luc": ngay_hieu_luc,
        "ngay_het_hieu_luc": None,
        "con_hieu_luc": True,
        "loai_thay_doi": None,
        "bi_sua_doi_boi": None,
        "ghi_chu": None,
    }

    chunks = []

    for pl in phu_luc_list:
        pl_so = pl.so  # đã là int từ parser

        if pl.mau_list:
            # Phụ lục có mẫu → 1 chunk cho mỗi mẫu
            for mau in pl.mau_list:
                chunk_id = f"{so_hieu_slug}_pl{pl_so}_m{mau.so}"
                citation = f"Mẫu số {mau.so} Phụ lục {pl_so}, {prefix} {so_hieu}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "van_ban": {
                        "so_hieu": so_hieu,
                        "loai_van_ban": doc_info["loai_van_ban"],
                        "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
                    },
                    "vi_tri": {
                        "phu_luc_so": pl_so,
                        "phu_luc_ten": pl.ten,
                        "mau_so": mau.so,
                        "mau_ten": mau.ten,
                    },
                    "noi_dung": mau.noi_dung,
                    "noi_dung_tham_chieu": None,
                    "citation": citation,
                    "hieu_luc": hieu_luc,
                })
        else:
            # Phụ lục không có mẫu → 1 chunk cho cả phụ lục
            chunk_id = f"{so_hieu_slug}_pl{pl_so}"
            citation = f"Phụ lục {pl_so}, {prefix} {so_hieu}"

            chunks.append({
                "chunk_id": chunk_id,
                "van_ban": {
                    "so_hieu": so_hieu,
                    "loai_van_ban": doc_info["loai_van_ban"],
                    "ngay_ban_hanh": doc_info["ngay_ban_hanh"],
                },
                "vi_tri": {
                    "phu_luc_so": pl_so,
                    "phu_luc_ten": pl.ten,
                    "mau_so": None,
                    "mau_ten": None,
                },
                "noi_dung": pl.noi_dung,
                "noi_dung_tham_chieu": None,
                "citation": citation,
                "hieu_luc": hieu_luc,
            })

    return chunks


# ── Link tham chiếu phụ lục vào chunks phần chính ──────────────────────────

def link_tham_chieu(chunks: list[dict], phuluc_chunks: list[dict]) -> None:
    """
    Scan nội dung mỗi chunk phần chính, tìm tham chiếu phụ lục,
    gán danh sách chunk_id phụ lục vào noi_dung_tham_chieu.

    Sửa trực tiếp (in-place), không trả về.
    """
    # Build lookup: (phu_luc_so, mau_so) → chunk_id
    #               (phu_luc_so, None)   → chunk_id
    lookup: dict[tuple, str] = {}
    for pc in phuluc_chunks:
        vt = pc["vi_tri"]
        pl_so = vt["phu_luc_so"]
        mau_so = vt.get("mau_so")
        lookup[(pl_so, mau_so)] = pc["chunk_id"]

    for chunk in chunks:
        noi_dung = chunk.get("noi_dung", "")
        refs: list[str] = []
        seen: set[str] = set()

        # Tìm "Mẫu số X Phụ lục Y" (cụ thể nhất, ưu tiên trước)
        for m in RE_MAU_PHU_LUC.finditer(noi_dung):
            mau_so = m.group(1)
            pl_so = _roman_to_int(m.group(2))
            # Thử lookup chính xác
            key = (pl_so, mau_so)
            cid = lookup.get(key)
            # Thử thêm zero-pad: "1" → "01"
            if not cid:
                key = (pl_so, mau_so.zfill(2))
                cid = lookup.get(key)
            if cid and cid not in seen:
                refs.append(cid)
                seen.add(cid)

        # Tìm "Phụ lục Y" (không kèm mẫu số)
        for m in RE_PHU_LUC_REF.finditer(noi_dung):
            pl_so = _roman_to_int(m.group(1))
            # Chỉ link nếu KHÔNG đã match cụ thể hơn (Mẫu số X Phụ lục Y)
            key = (pl_so, None)
            cid = lookup.get(key)
            if cid and cid not in seen:
                refs.append(cid)
                seen.add(cid)

        if refs:
            chunk["noi_dung_tham_chieu"] = refs


# # ── Gộp chunks theo Điều ───────────────────────────────────────────────────

# def merge_chunks_by_dieu(chunks: list[dict]) -> list[dict]:
#     """
#     Gộp các chunks cùng Điều thành 1 chunk duy nhất.

#     Input: list chunks JSON (đọc từ file processed).
#     Output: list chunks mới, mỗi chunk = 1 Điều hoàn chỉnh.

#     Nội dung được ghép theo thứ tự: khoản → điểm, phân cách bằng newline.
#     """
#     # Nhóm chunks theo (so_hieu, dieu_so) giữ đúng thứ tự xuất hiện
#     groups: OrderedDict[tuple, list[dict]] = OrderedDict()
#     for chunk in chunks:
#         key = (chunk["van_ban"]["so_hieu"], chunk["vi_tri"]["dieu_so"])
#         groups.setdefault(key, []).append(chunk)

#     merged = []
#     for (_so_hieu, dieu_so), group in groups.items():
#         first = group[0]

#         # Ghép nội dung tất cả chunks trong cùng 1 Điều
#         # Tránh lặp nội dung khoản khi khoản có nhiều điểm:
#         #   chunk điểm có noi_dung = "khoan_text\ndiem_ky) diem_text"
#         #   → chỉ lấy khoan_text 1 lần, rồi ghép từng dòng điểm
#         noi_dung_parts = []
#         seen_khoan: set[int] = set()
#         for c in group:
#             khoan_so = c["vi_tri"]["khoan_so"]
#             diem = c["vi_tri"]["diem"]

#             if khoan_so is None:
#                 # Chunk cấp điều (không có khoản)
#                 noi_dung_parts.append(c["noi_dung"])
#             elif diem:
#                 # Chunk điểm: noi_dung = "khoan_text\ndiem_ky) diem_text"
#                 lines = c["noi_dung"].split("\n", 1)
#                 khoan_text = lines[0]
#                 diem_text = lines[1] if len(lines) > 1 else ""
#                 if khoan_so not in seen_khoan:
#                     seen_khoan.add(khoan_so)
#                     noi_dung_parts.append(f"{khoan_so}. {khoan_text}")
#                 noi_dung_parts.append(f"  {diem_text}")
#             else:
#                 # Chunk khoản (không có điểm)
#                 seen_khoan.add(khoan_so)
#                 noi_dung_parts.append(f"{khoan_so}. {c['noi_dung']}")

#         # Lấy slug từ chunk_id: "35-2024-QH15_d4_k1_da" → "35-2024-QH15"
#         so_hieu_slug = make_so_hieu_slug(first["van_ban"]["so_hieu"])

#         merged.append({
#             "chunk_id": f"{so_hieu_slug}_d{dieu_so}",

#             "van_ban": first["van_ban"],

#             "vi_tri": {
#                 "chuong_so": first["vi_tri"]["chuong_so"],
#                 "chuong_ten": first["vi_tri"]["chuong_ten"],
#                 "muc_so": first["vi_tri"]["muc_so"],
#                 "muc_ten": first["vi_tri"]["muc_ten"],
#                 "dieu_so": dieu_so,
#                 "dieu_ten": first["vi_tri"]["dieu_ten"],
#                 "khoan_so": None,
#                 "diem": None,
#             },

#             "noi_dung": "\n".join(noi_dung_parts),

#             "noi_dung_tham_chieu": None,

#             "citation": f"Điều {dieu_so}, {first['citation'].split(', ', 1)[1]}",

#             "hieu_luc": first["hieu_luc"],
#         })

#     return merged
