"""
Registry khai báo thông tin các văn bản pháp luật.
Tên file .docx phải khớp với key trong DOCUMENTS.
"""

DOCUMENTS = {
    "Luật-36-2024-QH15": {
        "so_hieu": "36/2024/QH15",
        "ten_van_ban": "Luật Trật tự, an toàn giao thông đường bộ",
        "loai_van_ban": "luat",
        "co_quan_ban_hanh": "Quốc hội",
        "ngay_ban_hanh": "2024-06-27",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Luật-35-2024-QH15": {
        "so_hieu": "35/2024/QH15",
        "ten_van_ban": "Luật Đường bộ",
        "loai_van_ban": "luat",
        "co_quan_ban_hanh": "Quốc hội",
        "ngay_ban_hanh": "2024-06-27",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-119-2024-NĐ-CP": {
        "so_hieu": "119/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về thanh toán điện tử giao thông đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-09-30",
        "ngay_hieu_luc": "2024-10-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-130-2024-NĐ-CP": {
        "so_hieu": "130/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về thu phí sử dụng đường bộ cao tốc đối với phương tiện lưu thông trên tuyến đường bộ cao tốc thuộc sở hữu toàn dân do Nhà nước đại diện chủ sở hữu và trực tiếp quản lý, khai thác",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-10-10",
        "ngay_hieu_luc": "2024-10-10",
        "con_hieu_luc": True,
    },
    "Nghị-định-151-2024-NĐ-CP": {
        "so_hieu": "151/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định chi tiết một số điều và biện pháp thi hành Luật trật tự, an toàn giao thông đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-156-2024-NĐ-CP": {
        "so_hieu": "156/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về đấu giá biển số xe",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-10",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-158-2024-NĐ-CP": {
        "so_hieu": "158/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về hoạt động vận tải đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-18",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-160-2024-NĐ-CP": {
        "so_hieu": "160/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về hoạt động đào tạo và sát hạch lái xe",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-18",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-165-2024-NĐ-CP": {
        "so_hieu": "165/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định chi tiết, hướng dẫn thi hành một số điều của Luật Đường bộ và Điều 77 Luật Trật tự, an toàn giao thông đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-26",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-168-2024-NĐ-CP": {
        "so_hieu": "168/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định xử phạt vi phạm hành chính về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ; trừ điểm, phục hồi điểm giấy phép lái xe",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-26",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-176-2024-NĐ-CP": {
        "so_hieu": "176/2024/NĐ-CP",
        "ten_van_ban": "Nghị định quy định quản lý, sử dụng kinh phí thu từ xử phạt vi phạm hành chính về trật tự, an toàn giao thông đường bộ và đấu giá biển số xe sau khi nộp vào ngân sách nhà nước",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2024-12-30",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-279-2025-NĐ-CP": {
        "so_hieu": "279/2025/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về thành lập, nguồn tài chính hình thành, quản lý, hoạt động chi, sử dụng Quỹ giảm thiểu thiệt hại tai nạn giao thông đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2025-10-23",
        "ngay_hieu_luc": "2025-12-15",
        "con_hieu_luc": True,
    },
    "Nghị-định-336-2025-NĐ-CP": {
        "so_hieu": "336/2025/NĐ-CP",
        "ten_van_ban": "Nghị định quy định xử phạt vi phạm hành chính trong hoạt động đường bộ",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2025-12-22",
        "ngay_hieu_luc": "2026-03-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-364-2025-NĐ-CP": {
        "so_hieu": "364/2025/NĐ-CP",
        "ten_van_ban": "Nghị định quy định mức thu, chế độ thu, nộp, miễn, quản lý và sử dụng phí sử dụng đường bộ thu qua đầu phương tiện đối với xe ô tô",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2025-12-31",
        "ngay_hieu_luc": "2026-01-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-61-2026-NĐ-CP": {
        "so_hieu": "61/2026/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về danh mục, việc quản lý, sử dụng phương tiện, thiết bị kỹ thuật nghiệp vụ và quy trình thu thập, sử dụng dữ liệu thu được từ phương tiện, thiết bị kỹ thuật do cá nhân, tổ chức cung cấp để phát hiện vi phạm hành chính",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2026-02-13",
        "ngay_hieu_luc": "2026-04-01",
        "con_hieu_luc": True,
    },
    "Nghị-định-89-2026-NĐ-CP": {
        "so_hieu": "89/2026/NĐ-CP",
        "ten_van_ban": "Nghị định quy định về điều kiện kinh doanh dịch vụ kiểm định xe cơ giới; tổ chức, hoạt động của cơ sở đăng kiểm; niên hạn sử dụng của xe cơ giới",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2026-03-30",
        "ngay_hieu_luc": "2026-07-01",
        "con_hieu_luc": True,
    },




    # --- Văn bản liên quan đến sửa đổi bổ sung luật, nghị định ---

    # Điều 7: Sửa đổi, bổ sung Luật Trật tự, an toàn giao thông đường bộ
    # Điều 8: Sửa đổi, bổ sung Luật Đường bộ
    "Luật-118-2025-QH15": {
        "so_hieu": "118/2025/QH15",
        "ten_van_ban": "Luật sửa đổi bổ sung một số điều của 10 luật có liên quan đến an ninh, trật tự",
        "loai_van_ban": "luat",
        "co_quan_ban_hanh": "Quốc hội",
        "ngay_ban_hanh": "2025-12-10",
        "ngay_hieu_luc": "2026-07-01",
        "con_hieu_luc": True,
    },

    # Chỉ xử lý Điều 27 liên quan đến Nghị định số 151/2024/NĐ-CP 
    "Nghị-định-184-2025-NĐ-CP": {
        "so_hieu": "184/2025/NĐ-CP",
        "ten_van_ban": "Nghị định quy định phân định thẩm quyền khi tổ chức chính quyền địa phương 02 cấp và sửa đổi, bổ sung một số điều của các Nghị định của Chính phủ trong lĩnh vực an ninh, trật tự",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2025-07-01",
        "ngay_hieu_luc": "2025-07-01",
        "con_hieu_luc": True,
    },
}

def get_doc_info(file_key: str) -> dict | None:
    """Lấy thông tin văn bản từ tên file (không có đuôi .docx)."""
    # Thử key trực tiếp trước
    info = DOCUMENTS.get(file_key)
    if info:
        return info

    return None


def make_so_hieu_slug(so_hieu: str) -> str:
    """
    Chuyển số hiệu thành slug dùng cho chunk_id.
    '168/2024/NĐ-CP' → '168-2024-ND-CP'
    '36/2024/QH15'    → '36-2024-QH15'
    """
    return (
        so_hieu
        .replace("/", "-")
        .replace("NĐ", "ND")
    )
