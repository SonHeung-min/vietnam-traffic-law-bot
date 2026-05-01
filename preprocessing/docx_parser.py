"""
Parse file .docx và trích xuất cấu trúc phân cấp:
    Chương → Mục → Điều → Khoản → Điểm

Dùng regex nhận diện heading theo quy tắc văn bản pháp luật VN.
"""

import re
from dataclasses import dataclass, field
from docx import Document
from docx.table import Table
from docx.oxml.ns import qn


# ── Regex patterns ───────────────────────────────────────────────────────────

# Chương I, Chương II, Chương 1, Chương 2...
RE_CHUONG = re.compile(
    r"^Chương\s+([IVXLCDM]+|\d+)[.\s]*[-–—]?\s*(.*)",
    re.IGNORECASE,
)

# Mục 1, Mục 2...
RE_MUC = re.compile(
    r"^Mục\s+(\d+)[.\s]*[-–—]?\s*(.*)",
    re.IGNORECASE,
)

# Điều 1, Điều 2... (có thể có dấu . sau số)
RE_DIEU = re.compile(
    r"^Điều\s+(\d+)\.?\s*(.*)",
)

# 1. Phạt tiền..., 2. Phạt cảnh cáo... (khoản)
RE_KHOAN = re.compile(
    r"^(\d+)\.\s+(.*)",
)

# a) Vượt đèn đỏ..., b) Không chấp hành... (điểm)
RE_DIEM = re.compile(
    r"^([a-zđ])\)\s+(.*)",
)

# Phụ lục I, Phụ lục II, Phụ lục 1...
RE_PHU_LUC = re.compile(
    r"^Phụ\s+lục\s+([IVXLCDM]+|\d+)\b\s*(.*)",
    re.IGNORECASE,
)

# Mẫu số 01, Mẫu số 1...
RE_MAU_SO = re.compile(
    r"^Mẫu\s+số\s+(\d+\w*)[.:]\s*(.*)",
    re.IGNORECASE,
)


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Diem:
    ky_hieu: str       # "a", "b", "c"
    noi_dung: str      # text của điểm


@dataclass
class Khoan:
    so: int            # 1, 2, 3
    noi_dung: str      # text đầu khoản (mức phạt)
    diem_list: list[Diem] = field(default_factory=list)


@dataclass
class Dieu:
    so: int            # 1, 2, 3
    ten: str           # tên điều
    noi_dung: str = ""
    khoan_list: list[Khoan] = field(default_factory=list)
    raw_text: str = ""  # toàn bộ text gốc


@dataclass
class Muc:
    so: int | None     # số mục, None nếu không có mục
    ten: str | None
    dieu_list: list[Dieu] = field(default_factory=list)


@dataclass
class Chuong:
    so: int | str      # số chương (có thể là La Mã hoặc Ả Rập)
    ten: str
    muc_list: list[Muc] = field(default_factory=list)


@dataclass
class MauVanBan:
    so: str            # "01", "02", ...
    ten: str           # tên mẫu
    noi_dung: str = "" # nội dung mẫu (text + bảng)


@dataclass
class PhuLuc:
    so: int | str      # số phụ lục (La Mã hoặc Ả Rập)
    ten: str           # tên phụ lục
    noi_dung: str = "" # nội dung chung (không thuộc mẫu nào)
    mau_list: list[MauVanBan] = field(default_factory=list)


# ── Helper ───────────────────────────────────────────────────────────────────

def _table_to_text(table: Table) -> str:
    """
    Chuyển bảng trong .docx thành dạng markdown table chuẩn.
    Ví dụ:
        | STT | Hành vi | Mức phạt |
        | --- | --- | --- |
        | 1 | Vi phạm A | 2.000.000 |
    """
    rows = []
    for row in table.rows:
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
    if not rows:
        return ""
    # Chèn separator line sau header row
    num_cols = len(table.rows[0].cells)
    separator = "| " + " | ".join(["---"] * num_cols) + " |"
    rows.insert(1, separator)
    return "\n".join(rows)


def _iter_block_items(doc):
    """
    Duyệt tất cả block-level elements trong document body theo đúng thứ tự.
    Trả về từng element là Paragraph hoặc Table object.
    """
    from docx.text.paragraph import Paragraph

    for child in doc.element.body:
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def _roman_to_int(roman: str) -> int:
    """Chuyển số La Mã sang số nguyên. Nếu đã là số thì trả về luôn."""
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


# ── Main parser ──────────────────────────────────────────────────────────────

def parse_docx(file_path: str) -> tuple[list[Chuong], list[PhuLuc]]:
    """
    Đọc file .docx và trả về:
      - danh sách Chương (phần chính): Chương → Mục → Điều → Khoản → Điểm
      - danh sách Phụ lục: PhuLuc → MauVanBan
    """
    doc = Document(file_path)
    blocks = list(_iter_block_items(doc))

    # ── Tìm vị trí bắt đầu phụ lục ─────────────────────────────────────
    phu_luc_start = len(blocks)
    for i, block in enumerate(blocks):
        if isinstance(block, Table):
            continue
        line = block.text.strip()
        if RE_PHU_LUC.match(line):
            phu_luc_start = i
            break

    # ── Parse phần chính (trước phụ lục) ─────────────────────────────────
    chuong_list = _parse_phan_chinh(blocks[:phu_luc_start])

    # ── Parse phần phụ lục ───────────────────────────────────────────────
    phu_luc_list = _parse_phu_luc(blocks[phu_luc_start:])

    return chuong_list, phu_luc_list


def _parse_phan_chinh(blocks) -> list[Chuong]:
    """Parse phần chính của văn bản (Chương → Mục → Điều → Khoản → Điểm)."""

    chuong_list: list[Chuong] = []

    current_chuong: Chuong | None = None
    current_muc: Muc | None = None
    current_dieu: Dieu | None = None
    current_khoan: Khoan | None = None

    reading_chuong_ten = False
    reading_muc_ten = False

    for block in blocks:

        # ── Nếu block là Table → chuyển thành text và ghép vào phần hiện tại ──
        if isinstance(block, Table):
            table_text = _table_to_text(block)
            if not table_text:
                continue
            if current_khoan and current_khoan.diem_list:
                current_khoan.diem_list[-1].noi_dung += "\n" + table_text
            elif current_khoan:
                current_khoan.noi_dung += "\n" + table_text
            elif current_dieu:
                if current_dieu.noi_dung:
                    current_dieu.noi_dung += "\n" + table_text
                else:
                    current_dieu.noi_dung = table_text
            continue

        # ── Block là Paragraph ──
        line = block.text.strip()
        if not line:
            continue

        # Nếu đang đọc tên mục, kiểm tra xem dòng này có phải heading mới không
        if reading_muc_ten:
            is_heading = (
                RE_MUC.match(line)
                or RE_DIEU.match(line)
            )
            if not is_heading:
                if current_muc.ten:
                    current_muc.ten += " " + line
                else:
                    current_muc.ten = line
                continue
            else:
                reading_muc_ten = False

        # Nếu đang đọc tên chương, kiểm tra xem dòng này có phải heading mới không
        if reading_chuong_ten:
            is_heading = (
                RE_MUC.match(line)
                or RE_DIEU.match(line)
                or RE_KHOAN.match(line)
            )
            if not is_heading:
                if current_chuong.ten:
                    current_chuong.ten += " " + line
                else:
                    current_chuong.ten = line
                continue
            else:
                reading_chuong_ten = False

        # ── Chương ───────────────────────────────────────────────────────
        m = RE_CHUONG.match(line)
        if m:
            so_raw, ten = m.group(1), m.group(2).strip()
            so = _roman_to_int(so_raw)
            current_chuong = Chuong(so=so, ten=ten)
            chuong_list.append(current_chuong)
            current_muc = Muc(so=None, ten=None)
            current_chuong.muc_list.append(current_muc)
            current_dieu = None
            current_khoan = None
            reading_chuong_ten = True
            continue

        # ── Mục ──────────────────────────────────────────────────────────
        m = RE_MUC.match(line)
        if m and current_chuong:
            so, ten = int(m.group(1)), m.group(2).strip()
            if (current_chuong.muc_list
                    and current_chuong.muc_list[-1].so is None
                    and not current_chuong.muc_list[-1].dieu_list):
                current_chuong.muc_list.pop()
            current_muc = Muc(so=so, ten=ten)
            current_chuong.muc_list.append(current_muc)
            current_dieu = None
            current_khoan = None
            reading_muc_ten = True
            continue

        # ── Điều ─────────────────────────────────────────────────────────
        m = RE_DIEU.match(line)
        if m:
            so, ten = int(m.group(1)), m.group(2).strip()
            current_dieu = Dieu(so=so, ten=ten)
            if not current_chuong:
                current_chuong = Chuong(so=0, ten="")
                chuong_list.append(current_chuong)
                current_muc = Muc(so=None, ten=None)
                current_chuong.muc_list.append(current_muc)
            if not current_muc:
                current_muc = Muc(so=None, ten=None)
                current_chuong.muc_list.append(current_muc)
            current_muc.dieu_list.append(current_dieu)
            current_khoan = None
            continue

        # ── Khoản ────────────────────────────────────────────────────────
        m = RE_KHOAN.match(line)
        if m and current_dieu:
            so, noi_dung = int(m.group(1)), m.group(2).strip()
            current_khoan = Khoan(so=so, noi_dung=noi_dung)
            current_dieu.khoan_list.append(current_khoan)
            continue

        # ── Điểm ─────────────────────────────────────────────────────────
        m = RE_DIEM.match(line)
        if m and current_khoan:
            ky_hieu, noi_dung = m.group(1), m.group(2).strip()
            current_khoan.diem_list.append(Diem(ky_hieu=ky_hieu, noi_dung=noi_dung))
            continue

        # ── Dòng tiếp nối ────────────────────────────────────────────────
        if current_khoan and current_khoan.diem_list:
            current_khoan.diem_list[-1].noi_dung += " " + line
        elif current_khoan:
            current_khoan.noi_dung += " " + line
        elif current_dieu:
            if current_dieu.noi_dung:
                current_dieu.noi_dung += " " + line
            else:
                current_dieu.noi_dung = line

    return chuong_list


def _parse_phu_luc(blocks) -> list[PhuLuc]:
    """Parse phần phụ lục: Phụ lục → Mẫu số."""

    phu_luc_list: list[PhuLuc] = []
    current_pl: PhuLuc | None = None
    current_mau: MauVanBan | None = None

    for block in blocks:

        # ── Table ────────────────────────────────────────────────────────
        if isinstance(block, Table):
            table_text = _table_to_text(block)
            if not table_text:
                continue
            if current_mau:
                if current_mau.noi_dung:
                    current_mau.noi_dung += "\n" + table_text
                else:
                    current_mau.noi_dung = table_text
            elif current_pl:
                if current_pl.noi_dung:
                    current_pl.noi_dung += "\n" + table_text
                else:
                    current_pl.noi_dung = table_text
            continue

        # ── Paragraph ────────────────────────────────────────────────────
        line = block.text.strip()
        if not line:
            continue

        # ── Phụ lục mới ──────────────────────────────────────────────────
        m = RE_PHU_LUC.match(line)
        if m:
            so_raw, ten = m.group(1), m.group(2).strip()
            so = _roman_to_int(so_raw)
            current_pl = PhuLuc(so=so, ten=ten)
            phu_luc_list.append(current_pl)
            current_mau = None
            continue

        # ── Mẫu số mới ──────────────────────────────────────────────────
        m = RE_MAU_SO.match(line)
        if m and current_pl:
            so, ten = m.group(1), m.group(2).strip()
            current_mau = MauVanBan(so=so, ten=ten)
            current_pl.mau_list.append(current_mau)
            continue

        # ── Dòng tiếp nối ────────────────────────────────────────────────
        if current_mau:
            if current_mau.noi_dung:
                current_mau.noi_dung += " " + line
            else:
                current_mau.noi_dung = line
        elif current_pl:
            if current_pl.noi_dung:
                current_pl.noi_dung += " " + line
            else:
                current_pl.noi_dung = line

    return phu_luc_list


def print_structure(chuong_list: list[Chuong], phu_luc_list: list[PhuLuc] | None = None) -> None:
    """In cấu trúc đã parse ra để kiểm tra."""
    for ch in chuong_list:
        print(f"Chương {ch.so}: {ch.ten}")
        for muc in ch.muc_list:
            if muc.so:
                print(f"  Mục {muc.so}: {muc.ten}")
            for dieu in muc.dieu_list:
                if not dieu.khoan_list:
                    print(f"    Điều {dieu.so}: {dieu.ten[:60]}...")
                    print(f"      {dieu.noi_dung[:60]}...")
                    continue

                print(f"    Điều {dieu.so}: {dieu.ten[:60]}...")
                for khoan in dieu.khoan_list:
                    diem_count = len(khoan.diem_list)
                    print(f"      Khoản {khoan.so}: {khoan.noi_dung[:50]}... ({diem_count} điểm)")
                    for d in khoan.diem_list:
                        print(f"        {d.ky_hieu}) {d.noi_dung[:50]}...")

    if phu_luc_list:
        print("\n" + "=" * 60)
        print("PHỤ LỤC")
        print("=" * 60)
        for pl in phu_luc_list:
            print(f"\nPhụ lục {pl.so}: {pl.ten[:]}")
            if pl.noi_dung:
                print(f"  Nội dung: {pl.noi_dung[:]}...")
            for mau in pl.mau_list:
                print(f"  Mẫu số {mau.so}: {mau.ten[:]}...")
                if mau.noi_dung:
                    print(f"    {mau.noi_dung[:]}...")


if __name__ == "__main__":
    # Test với file mẫu
    chuong_list, phu_luc_list = parse_docx("../data/raw/Luật-36-2024-QH15.docx")
    print_structure(chuong_list, phu_luc_list)
