"""
Parse luật sửa đổi (.docx) → danh sách lệnh sửa đổi (amendment commands).

Luật sửa đổi có cấu trúc:
    Điều X. Sửa đổi, bổ sung một số điều của Luật <tên luật>
        1. Sửa đổi, bổ sung khoản Y Điều Z như sau: "..."
        2. Thay thế cụm từ "A" bằng cụm từ "B" tại ...
        3. Bãi bỏ khoản Y Điều Z.

Output: list[AmendmentCommand] — mỗi lệnh chứa:
    - luat_bi_sua: số hiệu luật bị sửa
    - loai: sua_doi | bo_sung | thay_the_tu | bo_cum_tu | bai_bo
    - vi_tri: dict xác định vị trí (dieu, khoan, diem)
    - noi_dung_moi: nội dung thay thế (nếu có)
    - ghi_chu: nguồn gốc sửa đổi
"""

import re
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from docx import Document


# ── Mapping: tên luật trong Điều heading → số hiệu ─────────────────────────

LUAT_MAPPING = {
    "Luật Cảnh vệ": "13/2017/QH14",
    "Luật Nhập cảnh, xuất cảnh, quá cảnh, cư trú của người nước ngoài tại Việt Nam": "47/2014/QH13",
    "Luật Xuất cảnh, nhập cảnh của công dân Việt Nam": "49/2019/QH14",
    "Luật Cư trú": "68/2020/QH14",
    "Luật Căn cước": "26/2023/QH15",
    "Luật Lực lượng tham gia bảo vệ an ninh, trật tự ở cơ sở": "30/2023/QH15",
    "Luật Trật tự, an toàn giao thông đường bộ": "36/2024/QH15",
    "Luật Đường bộ": "35/2024/QH15",
    "Luật Quản lý, sử dụng vũ khí, vật liệu nổ và công cụ hỗ trợ": "14/2017/QH14",
    "Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ": "55/2024/QH15",
}


# ── Data class ──────────────────────────────────────────────────────────────

@dataclass
class AmendmentCommand:
    luat_bi_sua: str                 # số hiệu luật bị sửa, vd "35/2024/QH15"
    loai: str                        # sua_doi | bo_sung | thay_the_tu | bo_cum_tu | bai_bo
    vi_tri: list[dict]               # list vị trí bị ảnh hưởng [{dieu, khoan, diem}, ...]
    noi_dung_moi: str | None = None  # nội dung thay thế (trong ngoặc kép)
    tu_cu: str | None = None         # cụm từ cũ (cho thay_the_tu, bo_cum_tu)
    tu_moi: str | None = None        # cụm từ mới (cho thay_the_tu)
    ghi_chu: str = ""                # nguồn gốc, vd "Điều 8 khoản 1, Luật 118/2025/QH15"


# ── Regex patterns ──────────────────────────────────────────────────────────

# Nhận diện Điều cấp cao: "Điều 8. Sửa đổi, bổ sung một số điều của Luật Đường bộ"
RE_DIEU_SUA_DOI = re.compile(
    r"^Điều\s+(\d+)\.\s+Sửa đổi,\s+bổ sung một số điều của\s+(.+)"
)

# Khoản cấp 1: "1. Sửa đổi...", "2. Thay thế...", "10. Bãi bỏ..."
RE_KHOAN_CAP1 = re.compile(r"^(\d+)\.\s+(.*)")

# Điểm cấp con: "a) Sửa đổi...", "b) Bổ sung..."
RE_DIEM_CON = re.compile(r"^([a-zđ])\)\s+(.*)")

# ── Pattern phân loại lệnh ─────────────────────────────────────────────────

# "Sửa đổi, bổ sung khoản 6 Điều 2 như sau:"
RE_SUA_KHOAN = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+khoản\s+(\d+\w*)\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung Điều 8 như sau:" (cả điều)
RE_SUA_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+Điều\s+(\d+\w*)\s+(?:và Điều\s+(\d+\w*)\s+)?như sau"
)

# "Sửa đổi, bổ sung một số điểm, khoản của Điều 5 như sau:"
RE_SUA_NHIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+một số\s+(?:điểm|khoản|điểm, khoản|khoản, điều|điểm của các khoản|điểm, khoản của|khoản của)\s+.*?Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung một số khoản của Điều 34 như sau:"
RE_SUA_NHIEU_KHOAN = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+một số khoản của\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung điểm c khoản 1 như sau:" (sub-item, không có Điều)
RE_SUA_DIEM = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+điểm\s+([a-zđ])\s+khoản\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung điểm c khoản 4 Điều 75 như sau:" (có cả Điều)
RE_SUA_DIEM_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+điểm\s+([a-zđ])\s+khoản\s+(\d+\w*)\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung điểm a và điểm b khoản 1 Điều 39 như sau:"
RE_SUA_NHIEU_DIEM_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+điểm\s+([a-zđ])\s+và điểm\s+([a-zđ])\s+khoản\s+(\d+\w*)\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung điểm c và điểm d như sau:" (sub-item, không có khoản/Điều)
RE_SUA_NHIEU_DIEM_SUB = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+điểm\s+([a-zđ])\s+và điểm\s+([a-zđ])\s+như sau"
)

# "Sửa đổi, bổ sung khoản 2 và khoản 3 Điều 35 như sau:"
RE_SUA_NHIEU_KHOAN_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+khoản\s+(\d+\w*)(?:\s+và khoản\s+(\d+\w*))?\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung khoản 18 và bổ sung khoản 18a vào sau khoản 18 Điều 9 như sau:"
RE_SUA_VA_BOSUNG_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+khoản\s+(\d+\w*).*?bổ sung\s+khoản\s+(\d+\w*)\s+vào sau.*?Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung khoản 7, khoản 8 và bổ sung khoản 9 vào sau khoản 8 như sau:" (sub-item)
RE_SUA_VA_BOSUNG_SUB = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+khoản\s+([\d\w,\s]+?)(?:\s+và bổ sung\s+khoản\s+(\d+\w*)\s+vào sau.*?)?\s*như sau"
)

# "Bổ sung khoản 22 và khoản 23 vào sau khoản 21 Điều 8 như sau:"
RE_BOSUNG_KHOAN = re.compile(
    r"[Bb]ổ sung\s+(.*?)vào sau\s+.*?Điều\s+(\d+\w*)\s+như sau"
)

# "Bổ sung Điều 6a vào sau Điều 6 như sau:"
RE_BOSUNG_DIEU = re.compile(
    r"[Bb]ổ sung\s+Điều\s+(\d+\w*)\s+vào sau\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Bổ sung điểm đ vào sau điểm d khoản 4 Điều 10 như sau:"
RE_BOSUNG_DIEM = re.compile(
    r"[Bb]ổ sung\s+điểm\s+(\w+)\s+vào sau\s+điểm\s+\w+\s+khoản\s+(\d+\w*)\s+Điều\s+(\d+\w*)\s+như sau"
)

# "Sửa đổi, bổ sung tên của Điều 52 như sau:"
RE_SUA_TEN_DIEU = re.compile(
    r"Sửa đổi,?\s+bổ sung\s+tên của\s+Điều\s+(\d+\w*)\s+như sau"
)

# Thay thế cụm từ: Thay thế cụm từ "A" bằng cụm từ "B" tại ...
RE_THAY_THE = re.compile(
    r'[Tt]hay thế\s+(?:từ|cụm từ)\s+["\u201c](.+?)["\u201d]\s+bằng\s+(?:từ|cụm từ)\s+["\u201c](.+?)["\u201d]\s+tại\s+(.*)'
)

# Bỏ cụm từ: Bỏ cụm từ "X" tại ...
RE_BO_CUM_TU = re.compile(
    r'[Bb]ỏ\s+cụm từ\s+["\u201c](.+?)["\u201d]\s+tại\s+(.*)'
)

# Bãi bỏ: Bãi bỏ khoản X Điều Y, Điều Z.
RE_BAI_BO = re.compile(
    r'[Bb]ãi bỏ\s+(.*)'
)

# Thay thế từ "X" bằng từ "Y" tại ... (trong dạng điểm con)
RE_THAY_THE_DIEM = re.compile(
    r'[Tt]hay thế\s+(?:từ|cụm từ)\s+["\u201c](.+?)["\u201d]\s+bằng\s+(?:từ|cụm từ)\s+["\u201c](.+?)["\u201d]\s+tại\s+(.*)'
)


# ── Helper: trích nội dung trong ngoặc kép ──────────────────────────────────

OPEN_Q = "\u201c"   # "
CLOSE_Q = "\u201d"  # "


def _extract_quoted_content(paragraphs: list[str], start_idx: int) -> tuple[str, int]:
    """
    Từ vị trí start_idx, tìm và ghép nội dung trong ngoặc kép "...".
    Trả về (nội dung, index dòng cuối cùng đã đọc).

    Nội dung có thể kéo dài nhiều dòng:
        "Điều 8. Phân loại...
        1. Đường bộ theo cấp quản lý...
        ...
        6. Chính phủ quy định chi tiết Điều này.".
    """
    lines = []
    idx = start_idx
    found_open = False

    while idx < len(paragraphs):
        line = paragraphs[idx]

        if not found_open:
            # Tìm dấu mở ngoặc
            if OPEN_Q in line or (line.startswith('"') and '"' != CLOSE_Q):
                found_open = True
                # Bỏ dấu mở ngoặc ở đầu
                content = line.lstrip(OPEN_Q).lstrip('"')
                # Kiểm tra nếu đóng ngoặc cùng dòng
                if CLOSE_Q in content:
                    # Cắt phần sau dấu đóng
                    close_pos = content.rfind(CLOSE_Q)
                    content = content[:close_pos]
                    lines.append(content)
                    return "\n".join(lines), idx
                lines.append(content)
            idx += 1
            continue

        # Đang đọc nội dung, kiểm tra dấu đóng ngoặc
        if CLOSE_Q in line:
            close_pos = line.rfind(CLOSE_Q)
            content = line[:close_pos]
            lines.append(content)
            return "\n".join(lines), idx

        lines.append(line)
        idx += 1

    # Không tìm thấy dấu đóng
    return "\n".join(lines), idx - 1


# ── Helper: parse vị trí từ chuỗi text ─────────────────────────────────────

def _parse_vi_tri_list(text: str, default_dieu: int | None = None) -> list[dict]:
    """
    Parse chuỗi vị trí phức tạp thành list dict.

    Chiến lược: tách text thành các segment theo Điều (anchor).
    Mỗi segment chứa tất cả khoản/điểm thuộc Điều đó.

    Ví dụ:
        'điểm b khoản 4 và khoản 5 Điều 30, điểm b khoản 3 và khoản 7 Điều 32'
        → segment 'điểm b khoản 4 và khoản 5' → Điều 30
        → segment 'điểm b khoản 3 và khoản 7' → Điều 32

        'các khoản 1, 4 và 5 Điều 39'
        → Điều 39: khoản 1, 4, 5
    """
    results = []
    text = text.strip().rstrip('.')

    # Bước 1: Tách thành segments theo "Điều X" (mỗi Điều là anchor cuối segment)
    # Tìm tất cả vị trí "Điều X" trong text
    dieu_positions = list(re.finditer(r'Điều\s+(\d+\w*)', text))

    if not dieu_positions:
        # Không có Điều → dùng default_dieu
        if default_dieu:
            return [{"dieu": default_dieu}]
        return []

    segments = []
    prev_end = 0
    for m in dieu_positions:
        # Segment = text trước "Điều X" + Điều X
        segment_text = text[prev_end:m.end()].strip().strip(',').strip()
        dieu = m.group(1)
        segments.append((dieu, segment_text))
        prev_end = m.end()

    # Bước 2: Parse từng segment
    for dieu, seg in segments:
        # Loại bỏ phần "Điều X" khỏi text để chỉ còn khoản/điểm
        seg_clean = re.sub(r'Điều\s+\d+\w*', '', seg).strip().strip(',').strip()

        if not seg_clean:
            # Chỉ có "Điều X" (vd: "Điều 49")
            results.append({"dieu": dieu})
            continue

        # Xử lý "các khoản 1, 4 và 5"
        cac_khoan = re.search(r'các khoản\s+([\d,\svà]+)', seg_clean)
        if cac_khoan:
            nums = re.findall(r'(\d+)', cac_khoan.group(1))
            for n in nums:
                results.append({"dieu": dieu, "khoan": n})
            continue

        # Tách segment thành các nhóm bởi "và" hoặc ","
        # Mỗi nhóm có thể là: "điểm X khoản Y", "khoản Y", "điểm X"
        # Ví dụ: "điểm b khoản 4 và khoản 5" → ["điểm b khoản 4", "khoản 5"]
        sub_parts = re.split(r'\s+và\s+|,\s*', seg_clean)

        # Parse từng sub_part, dùng khoản gần nhất làm context
        last_khoan = None
        for sp in sub_parts:
            sp = sp.strip()
            if not sp:
                continue

            khoan_m = re.search(r'khoản\s+(\d+\w*)', sp)
            diem_m = re.search(r'điểm\s+([a-zđ]\d*)', sp)

            if khoan_m:
                last_khoan = khoan_m.group(1)

            if diem_m and khoan_m:
                results.append({"dieu": dieu, "khoan": khoan_m.group(1), "diem": diem_m.group(1)})
            elif diem_m and last_khoan:
                results.append({"dieu": dieu, "khoan": last_khoan, "diem": diem_m.group(1)})
            elif khoan_m:
                results.append({"dieu": dieu, "khoan": khoan_m.group(1)})
            elif diem_m:
                results.append({"dieu": dieu, "diem": diem_m.group(1)})

    return results


def _parse_bai_bo(text: str) -> list[dict]:
    """Parse vị trí bãi bỏ: 'khoản 4 Điều 10, Điều 83.' → list vị trí."""
    results = []
    # Tách theo dấu phẩy
    parts = re.split(r'[,]\s*', text.rstrip('.'))
    for part in parts:
        part = part.strip()
        dieu_m = re.search(r'Điều\s+(\d+\w*)', part)
        khoan_m = re.search(r'khoản\s+(\d+\w*)', part)
        diem_m = re.search(r'điểm\s+([a-zđ])', part)

        if dieu_m:
            vi_tri = {"dieu": dieu_m.group(1)}
            if khoan_m:
                vi_tri["khoan"] = khoan_m.group(1)
            if diem_m:
                vi_tri["diem"] = diem_m.group(1)
            results.append(vi_tri)
    return results


# ── Main parser ─────────────────────────────────────────────────────────────

def parse_amendment_docx(file_path: str) -> list[AmendmentCommand]:
    """
    Parse file .docx luật sửa đổi → list AmendmentCommand.
    """
    doc = Document(file_path)
    paragraphs = [t for p in doc.paragraphs if (t := p.text.strip())]

    commands: list[AmendmentCommand] = []
    current_luat = None       # số hiệu luật đang bị sửa
    current_dieu_sd = None    # số Điều trong luật sửa đổi (Điều 7, 8, ...)
    current_khoan_sd = None   # số khoản cấp 1
    target_dieu = None        # Điều đích trong luật bị sửa (context cho sub-items)
    target_khoan = None       # Khoản đích (context cho sub-items cấp điểm)

    i = 0
    while i < len(paragraphs):
        line = paragraphs[i]

        # ── Điều cấp cao: xác định luật bị sửa ─────────────────────────
        m = RE_DIEU_SUA_DOI.match(line)
        if m:
            current_dieu_sd = m.group(1)
            ten_luat = m.group(2).strip()
            current_luat = _match_luat(ten_luat)
            target_dieu = None
            target_khoan = None
            current_khoan_sd = None
            i += 1
            continue

        # Bỏ qua nếu chưa xác định luật
        if not current_luat:
            i += 1
            continue

        # ── Khoản cấp 1 ────────────────────────────────────────────────
        m_khoan = RE_KHOAN_CAP1.match(line)
        m_diem = RE_DIEM_CON.match(line)

        if m_khoan:
            khoan_so = m_khoan.group(1)
            noi_dung = m_khoan.group(2)
            current_khoan_sd = khoan_so
            ghi_chu = f"Điều {current_dieu_sd} khoản {khoan_so}, Luật 118/2025/QH15"

            cmd = _parse_instruction(
                noi_dung, paragraphs, i, current_luat, ghi_chu, target_dieu, target_khoan
            )
            if cmd:
                if isinstance(cmd, list):
                    commands.extend(cmd)
                else:
                    commands.append(cmd)
                    # Cập nhật target_dieu và target_khoan cho sub-items
                    if cmd.vi_tri:
                        target_dieu = cmd.vi_tri[0].get("dieu", target_dieu)
                        target_khoan = cmd.vi_tri[0].get("khoan", None)

            i += 1
            continue

        # ── Điểm con (a, b, c...) ──────────────────────────────────────
        if m_diem and current_luat:
            diem_ky = m_diem.group(1)
            noi_dung = m_diem.group(2)
            ghi_chu = f"Điều {current_dieu_sd} khoản {current_khoan_sd} điểm {diem_ky}, Luật 118/2025/QH15"

            cmd = _parse_instruction(
                noi_dung, paragraphs, i, current_luat, ghi_chu, target_dieu, target_khoan
            )
            if cmd:
                if isinstance(cmd, list):
                    commands.extend(cmd)
                else:
                    commands.append(cmd)

            i += 1
            continue

        i += 1

    # Lọc bỏ các marker _context (chỉ dùng nội bộ để track target_dieu)
    return [cmd for cmd in commands if cmd.loai != "_context"]


def _match_luat(ten_luat: str) -> str | None:
    """Tìm số hiệu từ tên luật."""
    for key, so_hieu in LUAT_MAPPING.items():
        if key in ten_luat:
            return so_hieu
    return None


def _parse_instruction(
    text: str,
    paragraphs: list[str],
    line_idx: int,
    luat_bi_sua: str,
    ghi_chu: str,
    context_dieu: int | None = None,
    context_khoan: int | None = None,
) -> AmendmentCommand | list[AmendmentCommand] | None:
    """
    Phân loại và parse 1 lệnh sửa đổi từ text.
    """

    # ── Thay thế cụm từ ────────────────────────────────────────────────
    m = RE_THAY_THE.match(text)
    if m:
        tu_cu, tu_moi, vi_tri_text = m.group(1), m.group(2), m.group(3)
        vi_tri = _parse_vi_tri_list(vi_tri_text)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="thay_the_tu",
            vi_tri=vi_tri,
            tu_cu=tu_cu,
            tu_moi=tu_moi,
            ghi_chu=ghi_chu,
        )

    # ── Bỏ cụm từ ──────────────────────────────────────────────────────
    m = RE_BO_CUM_TU.match(text)
    if m:
        tu_cu, vi_tri_text = m.group(1), m.group(2)
        vi_tri = _parse_vi_tri_list(vi_tri_text)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bo_cum_tu",
            vi_tri=vi_tri,
            tu_cu=tu_cu,
            ghi_chu=ghi_chu,
        )

    # ── Bãi bỏ ──────────────────────────────────────────────────────────
    m = RE_BAI_BO.match(text)
    if m and "như sau" not in text:
        vi_tri = _parse_bai_bo(m.group(1))
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bai_bo",
            vi_tri=vi_tri,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi nhiều điểm khoản (có sub-items) ───────────────────────
    m = RE_SUA_NHIEU.match(text) or RE_SUA_NHIEU_KHOAN.match(text)
    if m:
        target_d = m.group(1)
        # Parse khoản context từ text (vd "một số điểm của khoản 1 Điều 7")
        khoan_ctx = re.search(r'khoản\s+(\d+\w*)', text)
        vi_tri = {"dieu": target_d}
        if khoan_ctx:
            vi_tri["khoan"] = khoan_ctx.group(1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="_context",
            vi_tri=[vi_tri],
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi nhiều điểm cùng lúc: "điểm a và điểm b khoản 1 Điều 39"
    m = RE_SUA_NHIEU_DIEM_DIEU.match(text)
    if m:
        diem1, diem2, khoan, dieu = m.group(1), m.group(2), m.group(3), m.group(4)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[
                {"dieu": dieu, "khoan": khoan, "diem": diem1},
                {"dieu": dieu, "khoan": khoan, "diem": diem2},
            ],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi nhiều điểm (sub-item): "điểm c và điểm d như sau:" ────
    m = RE_SUA_NHIEU_DIEM_SUB.match(text)
    if m:
        diem1, diem2 = m.group(1), m.group(2)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = [{"diem": diem1}, {"diem": diem2}]
        for vt in vi_tri:
            if context_dieu:
                vt["dieu"] = context_dieu
            if context_khoan:
                vt["khoan"] = context_khoan
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=vi_tri,
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi điểm với Điều: "điểm c khoản 4 Điều 75 như sau:" ──────
    m = RE_SUA_DIEM_DIEU.match(text)
    if m:
        diem, khoan, dieu = m.group(1), m.group(2), m.group(3)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[{"dieu": dieu, "khoan": khoan, "diem": diem}],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi + bổ sung khoản cùng Điều: "khoản 18 và bổ sung khoản 18a ... Điều 9"
    m = RE_SUA_VA_BOSUNG_DIEU.match(text)
    if m:
        khoan_sua, khoan_moi, dieu = m.group(1), m.group(2), m.group(3)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[
                {"dieu": dieu, "khoan": khoan_sua},
                {"dieu": dieu, "khoan": khoan_moi},
            ],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi nhiều khoản cùng Điều: "khoản 2 và khoản 3 Điều 35 như sau:"
    m = RE_SUA_NHIEU_KHOAN_DIEU.match(text)
    if m:
        khoan1, khoan2, dieu = m.group(1), m.group(2), m.group(3)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = [{"dieu": dieu, "khoan": khoan1}]
        if khoan2:
            vi_tri.append({"dieu": dieu, "khoan": khoan2})
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=vi_tri,
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi khoản cụ thể ───────────────────────────────────────────
    m = RE_SUA_KHOAN.match(text)
    if m:
        khoan, dieu = m.group(1), m.group(2)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[{"dieu": dieu, "khoan": khoan}],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi cả Điều ────────────────────────────────────────────────
    m = RE_SUA_DIEU.match(text)
    if m:
        dieu1 = m.group(1)
        dieu2 = m.group(2) if m.group(2) else None
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = [{"dieu": dieu1}]
        if dieu2:
            vi_tri.append({"dieu": dieu2})
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=vi_tri,
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi tên Điều ───────────────────────────────────────────────
    m = RE_SUA_TEN_DIEU.match(text)
    if m:
        dieu = m.group(1)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[{"dieu": dieu, "chi_sua_ten": True}],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Bổ sung Điều mới ───────────────────────────────────────────────
    m = RE_BOSUNG_DIEU.match(text)
    if m:
        dieu_moi = m.group(1)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bo_sung",
            vi_tri=[{"dieu": dieu_moi}],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Bổ sung điểm ───────────────────────────────────────────────────
    m = RE_BOSUNG_DIEM.match(text)
    if m:
        diem, khoan, dieu = m.group(1), m.group(2), m.group(3)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bo_sung",
            vi_tri=[{"dieu": dieu, "khoan": khoan, "diem": diem}],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Bổ sung khoản ──────────────────────────────────────────────────
    m = RE_BOSUNG_KHOAN.match(text)
    if m:
        dieu = m.group(2)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        # Parse khoản mới từ tên
        khoan_matches = re.findall(r'khoản\s+(\d+\w*)', m.group(1))
        vi_tri = [{"dieu": dieu, "khoan": k} for k in khoan_matches]
        if not vi_tri:
            vi_tri = [{"dieu": dieu}]
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bo_sung",
            vi_tri=vi_tri,
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi điểm (sub-item có khoản) ────────────────────────────────
    m = RE_SUA_DIEM.match(text)
    if m:
        diem, khoan = m.group(1), m.group(2)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = {"khoan": khoan, "diem": diem}
        if context_dieu:
            vi_tri["dieu"] = context_dieu
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[vi_tri],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi điểm (sub-item không có khoản): "Sửa đổi, bổ sung điểm h như sau:"
    m_diem_only = re.match(r'Sửa đổi,?\s+bổ sung\s+điểm\s+([a-zđ])\s+như sau', text)
    if m_diem_only:
        diem = m_diem_only.group(1)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = {"diem": diem}
        if context_dieu:
            vi_tri["dieu"] = context_dieu
        if context_khoan:
            vi_tri["khoan"] = context_khoan
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[vi_tri],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi + bổ sung nhiều khoản (sub-item): "khoản 7, khoản 8 và bổ sung khoản 9 vào sau khoản 8 như sau:"
    m = RE_SUA_VA_BOSUNG_SUB.match(text)
    if m:
        # Parse tất cả khoản từ text
        all_khoans = re.findall(r'khoản\s+(\d+\w*)', text)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = []
        for k in all_khoans:
            vt = {"khoan": k}
            if context_dieu:
                vt["dieu"] = context_dieu
            vi_tri.append(vt)
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=vi_tri,
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Sửa đổi khoản (sub-item, không có Điều) ────────────────────────
    m_khoan_sub = re.match(r'Sửa đổi,?\s+bổ sung\s+khoản\s+(\d+\w*)\s+như sau', text)
    if m_khoan_sub:
        khoan = m_khoan_sub.group(1)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = {"khoan": khoan}
        if context_dieu:
            vi_tri["dieu"] = context_dieu
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="sua_doi",
            vi_tri=[vi_tri],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    # ── Bổ sung khoản (sub-item, không có Điều) ────────────────────────
    m_bs_sub = re.match(r'[Bb]ổ sung\s+khoản\s+(\d+\w*)\s+vào sau\s+khoản\s+\d+\w*\s+như sau', text)
    if m_bs_sub:
        khoan = m_bs_sub.group(1)
        noi_dung, _ = _extract_quoted_content(paragraphs, line_idx + 1)
        vi_tri = {"khoan": khoan}
        if context_dieu:
            vi_tri["dieu"] = context_dieu
        return AmendmentCommand(
            luat_bi_sua=luat_bi_sua,
            loai="bo_sung",
            vi_tri=[vi_tri],
            noi_dung_moi=noi_dung,
            ghi_chu=ghi_chu,
        )

    return None


# ── Tách command đến mức sâu nhất ──────────────────────────────────────────

def _split_noi_dung_by_khoan(noi_dung: str, khoans: list[str]) -> dict[str, str]:
    """
    Tách nội dung thành từng phần theo khoản.
    '18. Làm gián đoạn...\n18a. Sử dụng...' + khoans=['18','18a']
    → {'18': '18. Làm gián đoạn...', '18a': '18a. Sử dụng...'}
    """
    result = {}
    lines = noi_dung.split("\n")

    for khoan in khoans:
        # Tìm dòng bắt đầu bằng "khoan. " hoặc "khoan " (cho khoản dạng 18a)
        prefix = f"{khoan}. "
        matched_lines = []
        found = False
        for line in lines:
            if line.startswith(prefix):
                found = True
                matched_lines.append(line)
            elif found:
                # Kiểm tra có phải bắt đầu khoản khác không
                is_other = False
                for other_k in khoans:
                    if other_k != khoan and line.startswith(f"{other_k}. "):
                        is_other = True
                        break
                if is_other:
                    break
                matched_lines.append(line)
        if matched_lines:
            result[khoan] = "\n".join(matched_lines)

    return result


def _split_noi_dung_by_diem(noi_dung: str, diems: list[str]) -> dict[str, str]:
    """
    Tách nội dung thành từng phần theo điểm.
    'a) Xe chữa cháy...\nb) Xe của lực lượng...' + diems=['a','b']
    → {'a': 'a) Xe chữa cháy...', 'b': 'b) Xe của lực lượng...'}
    """
    result = {}
    lines = noi_dung.split("\n")

    for diem in diems:
        prefix = f"{diem}) "
        matched_lines = []
        found = False
        for line in lines:
            if line.startswith(prefix):
                found = True
                matched_lines.append(line)
            elif found:
                is_other = False
                for other_d in diems:
                    if other_d != diem and line.startswith(f"{other_d}) "):
                        is_other = True
                        break
                if is_other:
                    break
                matched_lines.append(line)
        if matched_lines:
            result[diem] = "\n".join(matched_lines)

    return result


def split_commands(commands: list[AmendmentCommand]) -> list[AmendmentCommand]:
    """
    Tách mỗi command có nhiều vi_tri thành nhiều command riêng biệt,
    mỗi command chỉ có 1 vi_tri duy nhất.
    """
    result = []

    for cmd in commands:
        # Loại bỏ vi_tri trùng lặp
        seen = []
        unique_vi_tri = []
        for vt in cmd.vi_tri:
            key = tuple(sorted(vt.items()))
            if key not in seen:
                seen.append(key)
                unique_vi_tri.append(vt)
        cmd.vi_tri = unique_vi_tri

        # Nếu chỉ 1 vi_tri → giữ nguyên
        if len(cmd.vi_tri) <= 1:
            result.append(cmd)
            continue

        # thay_the_tu, bo_cum_tu, bai_bo → mỗi vi_tri 1 command, cùng tu_cu/tu_moi
        if cmd.loai in ("thay_the_tu", "bo_cum_tu", "bai_bo"):
            for vt in cmd.vi_tri:
                result.append(AmendmentCommand(
                    luat_bi_sua=cmd.luat_bi_sua,
                    loai=cmd.loai,
                    vi_tri=[vt],
                    noi_dung_moi=cmd.noi_dung_moi,
                    tu_cu=cmd.tu_cu,
                    tu_moi=cmd.tu_moi,
                    ghi_chu=cmd.ghi_chu,
                ))
            continue

        # sua_doi / bo_sung: cần chia noi_dung_moi
        if not cmd.noi_dung_moi:
            result.append(cmd)
            continue

        # Xác định mức: khoan hay diem?
        has_diem = all("diem" in vt for vt in cmd.vi_tri)
        has_khoan = all("khoan" in vt for vt in cmd.vi_tri)

        if has_diem:
            diems = [vt["diem"] for vt in cmd.vi_tri]
            parts = _split_noi_dung_by_diem(cmd.noi_dung_moi, diems)
            for vt in cmd.vi_tri:
                d = vt["diem"]
                result.append(AmendmentCommand(
                    luat_bi_sua=cmd.luat_bi_sua,
                    loai=cmd.loai,
                    vi_tri=[vt],
                    noi_dung_moi=parts.get(d, cmd.noi_dung_moi),
                    tu_cu=cmd.tu_cu,
                    tu_moi=cmd.tu_moi,
                    ghi_chu=cmd.ghi_chu,
                ))
        elif has_khoan:
            khoans = [vt["khoan"] for vt in cmd.vi_tri]
            parts = _split_noi_dung_by_khoan(cmd.noi_dung_moi, khoans)
            for vt in cmd.vi_tri:
                k = vt["khoan"]
                result.append(AmendmentCommand(
                    luat_bi_sua=cmd.luat_bi_sua,
                    loai=cmd.loai,
                    vi_tri=[vt],
                    noi_dung_moi=parts.get(k, cmd.noi_dung_moi),
                    tu_cu=cmd.tu_cu,
                    tu_moi=cmd.tu_moi,
                    ghi_chu=cmd.ghi_chu,
                ))
        else:
            # Fallback: giữ nguyên
            result.append(cmd)

    return result


# ── Hiển thị kết quả ───────────────────────────────────────────────────────

def print_commands(commands: list[AmendmentCommand], luat_filter: str | None = None) -> None:
    """In danh sách lệnh sửa đổi, có thể lọc theo luật."""
    for cmd in commands:
        if luat_filter and cmd.luat_bi_sua != luat_filter:
            continue

        print(f"[{cmd.loai.upper():12s}] Luật {cmd.luat_bi_sua}")
        for vt in cmd.vi_tri:
            parts = []
            if "dieu" in vt:
                parts.append(f"Điều {vt['dieu']}")
            if "khoan" in vt:
                parts.append(f"Khoản {vt['khoan']}")
            if "diem" in vt:
                parts.append(f"Điểm {vt['diem']}")
            print(f"  → {' '.join(parts)}")

        if cmd.tu_cu:
            print(f"  cũ: \"{cmd.tu_cu}\"")
        if cmd.tu_moi:
            print(f"  mới: \"{cmd.tu_moi}\"")
        if cmd.noi_dung_moi:
            preview = cmd.noi_dung_moi[:100].replace('\n', ' ↵ ')
            print(f"  nội dung: \"{preview}...\"")

        print(f"  ({cmd.ghi_chu})")
        print()


def export_commands_to_json(
    commands: list[AmendmentCommand],
    output_path: str,
    luat_filter: str | None = None,
) -> None:
    """
    Export danh sách lệnh sửa đổi ra file JSON.

    Args:
        commands: list AmendmentCommand từ parse_amendment_docx()
        output_path: đường dẫn file JSON output
        luat_filter: nếu có, chỉ export lệnh cho luật này
    """
    filtered = commands
    if luat_filter:
        filtered = [c for c in commands if c.luat_bi_sua == luat_filter]

    data = [asdict(cmd) for cmd in filtered]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Đã lưu {len(data)} lệnh → {output_path}")


if __name__ == "__main__":
    from collections import Counter

    commands = parse_amendment_docx("../data/raw/Luật-118-2025-QH15.docx")
    commands = split_commands(commands)
    print(f"Tổng: {len(commands)} lệnh sửa đổi (đã tách)\n")

    # Đếm theo luật
    by_luat = Counter(c.luat_bi_sua for c in commands)
    for luat, count in by_luat.most_common():
        print(f"  {luat}: {count} lệnh")
    print()

    # Export toàn bộ
    export_commands_to_json(commands, "../data/processed/amendment_commands.json")

    # Export riêng cho từng luật trong repo
    for so_hieu in ["35/2024/QH15", "36/2024/QH15"]:
        slug = so_hieu.replace("/", "-")
        export_commands_to_json(
            commands,
            f"../data/processed/amendments_{slug}.json",
            luat_filter=so_hieu,
        )

    # In chi tiết cho Luật Đường bộ
    print()
    print("=" * 70)
    print("CHI TIẾT: Luật Đường bộ 35/2024/QH15")
    print("=" * 70)
    print_commands(commands, luat_filter="35/2024/QH15")
