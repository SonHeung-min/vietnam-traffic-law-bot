"""
Registry khai báo thông tin các văn bản pháp luật.
Tên file .docx phải khớp với key trong DOCUMENTS.
"""

DOCUMENTS = {
    
    # --- Văn bản luật do Quốc hội ban hành ---
    "Luật-36-2024-QH15-dasua": {
        "so_hieu": "36/2024/QH15",
        "ten_van_ban": "Luật Trật tự, an toàn giao thông đường bộ",
        "loai_van_ban": "luat",
        "co_quan_ban_hanh": "Quốc hội",
        "ngay_ban_hanh": "2024-06-27",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Luật-35-2024-QH15-dasua": {
        "so_hieu": "35/2024/QH15",
        "ten_van_ban": "Luật Đường bộ",
        "loai_van_ban": "luat",
        "co_quan_ban_hanh": "Quốc hội",
        "ngay_ban_hanh": "2024-06-27",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },



    # --- Văn bản nghị định do Chính phủ ban hành ---
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

    "Nghị-định-151-2024-NĐ-CP-dasua": {
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


    # --- Văn bản thông tư do Bộ Y tế ban hành ---
    "Thông-tư-36-2024-TT-BYT": {
        "so_hieu": "36/2024/TT-BYT",
        "ten_van_ban": "Thông tư quy định về tiêu chuẩn sức khỏe, việc khám sức khỏe đối với người lái xe, người điều khiển xe máy chuyên dùng; việc khám sức khỏe định kỳ đối với người hành nghề lái xe ô tô; cơ sở dữ liệu về sức khỏe của người lái xe, người điều khiển xe máy chuyên dùng",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Y tế",
        "ngay_ban_hanh": "2024-11-16",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },



    # --- Văn bản thông tư do Bộ Công an ban hành ---
    "Thông-tư-65-2024-TT-BCA-dasua": {
        "so_hieu": "65/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định kiểm tra kiến thức pháp luật về trật tự, an toàn giao thông đường bộ để được phục hồi điểm giấy phép lái xe",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-12",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-69-2024-TT-BCA-dasua": {
        "so_hieu": "69/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định về chỉ huy, điều khiển giao thông đường bộ của Cảnh sát giao thông",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-12",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-71-2024-TT-BCA": {
        "so_hieu": "71/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định quản lý, vận hành, sử dụng hệ thống quản lý dữ liệu thiết bị giám sát hành trình và thiết bị ghi nhận hình ảnh người lái xe",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-12",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-72-2024-TT-BCA-dasua": {
        "so_hieu": "72/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định quy trình điều tra, giải quyết tai nạn giao thông đường bộ của Cảnh sát giao thông",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-13",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-73-2024-TT-BCA-dasua": {
        "so_hieu": "73/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định công tác tuần tra, kiểm soát, xử lý vi phạm pháp luật về trật tự, an toàn giao thông đường bộ của Cảnh sát giao thông",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-79-2024-TT-BCA-dasua": {
        "so_hieu": "79/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định về cấp, thu hồi chứng nhận đăng ký xe, biển số xe cơ giới, xe máy chuyên dùng",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },  

    "Thông-tư-82-2024-TT-BCA": {
        "so_hieu": "82/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định về chứng nhận chất lượng an toàn kỹ thuật và bảo vệ môi trường của xe cơ giới, xe máy chuyên dùng, phụ tùng xe cơ giới trong nhập khẩu, sản xuất, lắp ráp, cải tạo và kiểm định xe cơ giới, xe máy chuyên dùng thuộc phạm vi quản lý của Bộ Công an",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    }, 

    "Thông-tư-83-2024-TT-BCA": {
        "so_hieu": "83/2024/TT-BCA",
        "ten_van_ban": "Thông tư quy định về xây dựng, quản lý, vận hành, khai thác và sử dụng hệ thống giám sát bảo đảm an ninh, trật tự, an toàn giao thông đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    }, 

    "Thông-tư-12-2025-TT-BCA": {
        "so_hieu": "12/2025/TT-BCA",
        "ten_van_ban": "Thông tư quy định về sát hạch, cấp giấy phép lái xe; cấp, sử dụng giấy phép lái xe quốc tế",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2025-02-28",
        "ngay_hieu_luc": "2025-03-01",
        "con_hieu_luc": True,   
    },



    # --- Văn bản thông tư do Bộ Giao thông vận tải/ Bộ Xây dựng ban hành ---
    "Thông-tư-34-2024-TT-BGTVT": {
        "so_hieu": "34/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về hoạt động trạm thu phí đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-14",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    # Thông tư 35-2024-TT-BGTVT bị bãi bỏ bởi thông tư 14-2025-TT-BXD
    # "Thông-tư-35-2024-TT-BGTVT": {
    #     "so_hieu": "35/2024/TT-BGTVT",
    #     "ten_van_ban": "Thông tư quy định về đào tạo, sát hạch, cấp giấy phép lái xe; cấp, sử dụng giấy phép lái xe quốc tế; đào tạo, kiểm tra, cấp chứng chỉ bồi dưỡng kiến thức pháp luật về giao thông đường bộ",
    #     "loai_van_ban": "thong_tu",
    #     "co_quan_ban_hanh": "Bộ Giao thông vận tải",
    #     "ngay_ban_hanh": "2024-11-15",
    #     "ngay_hieu_luc": "2025-01-01",
    #     "con_hieu_luc": True,   
    # },    

    "Thông-tư-36-2024-TT-BGTVT-dasua": {
        "so_hieu": "36/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về tổ chức, quản lý hoạt động vận tải bằng xe ô tô và hoạt động của bến xe, bãi đỗ xe, trạm dừng nghỉ, điểm dừng xe trên đường bộ; quy định trình tự, thủ tục đưa bến xe, trạm dừng nghỉ vào khai thác",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    }, 

    "Thông-tư-38-2024-TT-BGTVT-dasua": {
        "so_hieu": "38/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về tốc độ và khoảng cách an toàn của xe cơ giới, xe máy chuyên dùng tham gia giao thông trên đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    }, 

    # Thông tư 39-2024-TT-BGTVT bị bãi bỏ bởi thông tư 12-2025-TT-BXD
    # "Thông-tư-39-2024-TT-BGTVT": {
    #     "so_hieu": "39/2024/TT-BGTVT",
    #     "ten_van_ban": "Thông tư Quy định về tải trọng, khổ giới hạn của đường bộ; lưu hành xe quá khổ giới hạn, xe quá tải trọng, xe bánh xích trên đường bộ; hàng siêu trường, siêu trọng, vận chuyển hàng siêu trường, siêu trọng; xếp hàng hóa trên phương tiện giao thông đường bộ; cấp giấy phép lưu hành cho xe quá tải trọng, xe quá khổ giới hạn, xe bánh xích, xe vận chuyển hàng siêu trường, siêu trọng trên đường bộ",
    #     "loai_van_ban": "thong_tu",
    #     "co_quan_ban_hanh": "Bộ Giao thông vận tải",
    #     "ngay_ban_hanh": "2024-11-15",
    #     "ngay_hieu_luc": "2025-01-01",
    #     "con_hieu_luc": True,   
    # }, 

    "Thông-tư-40-2024-TT-BGTVT-dasua": {
        "so_hieu": "40/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về công tác phòng, chống, khắc phục hậu quả thiên tai trong lĩnh vực đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-41-2024-TT-BGTVT-dasua": {
        "so_hieu": "41/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về quản lý, vận hành, khai thác và bảo trì kết cấu hạ tầng đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-45-2024-TT-BGTVT-dasua": {
        "so_hieu": "45/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về cấp mới, cấp lại, tạm đình chỉ, thu hồi chứng chỉ đăng kiểm viên phương tiện giao thông đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,   
    },

    "Thông-tư-46-2024-TT-BGTVT-dasua": {
        "so_hieu": "46/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định trình tự, thủ tục cấp mới, cấp lại, tạm đình chỉ hoạt động, thu hồi giấy chứng nhận đủ điều kiện hoạt động kiểm định xe cơ giới của cơ sở đăng kiểm xe cơ giới, cơ sở kiểm định khí thải xe mô tô, xe gắn máy",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-47-2024-TT-BGTVT-dasua": {
        "so_hieu": "47/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định trình tự, thủ tục kiểm định, miễn kiểm định lần đầu cho xe cơ giới, xe máy chuyên dùng; trình tự, thủ tục chứng nhận an toàn kỹ thuật và bảo vệ môi trường đối với xe cơ giới cải tạo, xe máy chuyên dùng cải tạo; trình tự, thủ tục kiểm định khí thải xe mô tô, xe gắn máy",
        "loai_van_ban": "thong_tu", 
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-52-2024-TT-BGTVT": {
        "so_hieu": "52/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về yêu cầu kỹ thuật đối với xe cơ giới, xe máy chuyên dùng thuộc đối tượng nghiên cứu phát triển có nhu cầu tham gia giao thông đường bộ",
        "loai_van_ban": "thong_tu", 
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-53-2024-TT-BGTVT": {
        "so_hieu": "53/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về phân loại phương tiện giao thông đường bộ và dấu hiệu nhận biết xe cơ giới sử dụng năng lượng sạch, năng lượng xanh, thân thiện môi trường",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-54-2024-TT-BGTVT-dasua": {
        "so_hieu": "54/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về trình tự, thủ tục chứng nhận chất lượng an toàn kỹ thuật và bảo vệ môi trường xe cơ giới, xe máy chuyên dùng, phụ tùng xe cơ giới trong nhập khẩu",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-55-2024-TT-BGTVT-dasua": {
        "so_hieu": "55/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư quy định về trình tự, thủ tục chứng nhận chất lượng an toàn kỹ thuật và bảo vệ môi trường của xe cơ giới, xe máy chuyên dùng, phụ tùng xe cơ giới trong sản xuất, lắp ráp",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-58-2024-TT-BGTVT": {
        "so_hieu": "58/2024/TT-BGTVT",
        "ten_van_ban": "Thông tư Quy định về đầu tư điểm dừng xe, đỗ xe và vị trí, quy mô trạm dừng nghỉ, điểm dừng xe, đỗ xe trên đường cao tốc",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Giao thông vận tải",
        "ngay_ban_hanh": "2024-11-15",
        "ngay_hieu_luc": "2025-01-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-12-2025-TT-BXD": {
        "so_hieu": "12/2025/TT-BXD",
        "ten_van_ban": "Thông tư quy định về đầu tư, quản lý, khai thác trạm dừng nghỉ trên đường cao tốc",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-06-30",
        "ngay_hieu_luc": "2025-07-01",
        "con_hieu_luc": True,
    },

    "Thông-tư-14-2025-TT-BXD": {
        "so_hieu": "14/2025/TT-BXD",
        "ten_van_ban": "Thông tư quy định về đào tạo lái xe; bồi dưỡng, kiểm tra, cấp chứng chỉ bồi dưỡng kiến thức pháp luật về giao thông đường bộ",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-06-30",
        "ngay_hieu_luc": "2025-09-01",
        "con_hieu_luc": True,
    }, 

    "Thông-tư-69-2025-TT-BXD": {
        "so_hieu": "69/2025/TT-BXD",
        "ten_van_ban": "Thông tư quy định dán nhãn năng lượng đối với các phương tiện sử dụng năng lượng thuộc phạm vi quản lý của Bộ Xây dựng",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-12-31",
        "ngay_hieu_luc": "2026-01-01",
        "con_hieu_luc": True,
    },



    # -------------------- Văn bản liên quan đến sửa đổi bổ sung luật, nghị định, thông tư --------------------

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

    # Điều 27: Sửa đổi, bổ sung Nghị định số 151/2024/NĐ-CP
    "Nghị-định-184-2025-NĐ-CP": {
        "so_hieu": "184/2025/NĐ-CP",
        "ten_van_ban": "Nghị định quy định phân định thẩm quyền khi tổ chức chính quyền địa phương 02 cấp và sửa đổi, bổ sung một số điều của các Nghị định của Chính phủ trong lĩnh vực an ninh, trật tự",
        "loai_van_ban": "nghi_dinh",
        "co_quan_ban_hanh": "Chính phủ",
        "ngay_ban_hanh": "2025-07-01",
        "ngay_hieu_luc": "2025-07-01",
        "con_hieu_luc": True,
    },

    # Điều 6: Sửa đổi, bổ sung Thông-tư-65-2024-TT-BCA
    # Điều 9: Sửa đổi, bổ sung Thông-tư-69-2024-TT-BCA
    # Điều 10: Sửa đổi, bổ sung Thông-tư-72-2024-TT-BCA
    # Điều 11: Sửa đổi, bổ sung Thông-tư-73-2024-TT-BCA
    # Điều 12: Sửa đổi, bổ sung Thông-tư-79-2024-TT-BCA
    "Thông-tư-13-2025-TT-BCA": {
        "so_hieu": "13/2025/TT-BCA",
        "ten_van_ban": "Thông tư sửa đổi, bổ sung một số điều của các thông tư quy định về trật tự, an toàn giao thông đường bộ, đường sắt và đường thủy nội địa",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2025-02-28",
        "ngay_hieu_luc": "2025-03-01",
        "con_hieu_luc": True,
    },  

    # Điều 1: Sửa đổi, bổ sung Thông-tư-79-2024-TT-BCA 
    "Thông-tư-51-2025-TT-BCA": {
        "so_hieu": "51/2025/TT-BCA",
        "ten_van_ban": "Thông tư sửa đổi, bổ sung một số điều của Thông tư số 79/2024/TT-BCA ngày 15 tháng 11 năm 2024 của Bộ trưởng Bộ Công an quy định về cấp, thu hồi chứng nhận đăng ký xe, biển số xe cơ giới, xe máy chuyên dùng đã được sửa đổi, bổ sung tại Thông tư số 13/2025/TT-BCA ngày 28 ngày 02 năm 2025 của Bộ trưởng Bộ Công an",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Công an",
        "ngay_ban_hanh": "2025-06-30",
        "ngay_hieu_luc": "2025-07-01",
        "con_hieu_luc": True,
    },  

    # Điều 26: Sửa đổi, bổ sung Thông-tư-38-2024-TT-BGTVT
    # Điều 27: Sửa đổi, bổ sung Thông-tư-40-2024-TT-BGTVT  (bị bãi bỏ bởi thông tư 72-2025-TT-BXD)
    # Điều 28: Sửa đổi, bổ sung Thông-tư-41-2024-TT-BGTVT  (bị bãi bỏ bởi thông tư 72-2025-TT-BXD)
    "Thông-tư-09-2025-TT-BXD": {
        "so_hieu": "09/2025/TT-BXD",
        "ten_van_ban": "Thông tư sửa đổi, bổ sung một số điều của các Thông tư thuộc lĩnh vực quản lý nhà nước của Bộ Xây dựng liên quan đến sắp xếp tổ chức bộ máy, thực hiện chính quyền địa phương 02 cấp và phân cấp cho chính quyền địa phương",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-06-13",
        "ngay_hieu_luc": "2025-07-01",
        "con_hieu_luc": True,
    },

    # Chương V: Sửa đổi, bổ sung Thông-tư-45-2024-TT-BGTVT
    # Chương VI: Sửa đổi, bổ sung Thông-tư-46-2024-TT-BGTVT
    # Chương VII: Sửa đổi, bổ sung Thông-tư-47-2024-TT-BGTVT
    # Chương VIII: Sửa đổi, bổ sung Thông-tư-54-2024-TT-BGTVT
    # Chương IX: Sửa đổi, bổ sung Thông-tư-55-2024-TT-BGTVT
    "Thông-tư-71-2025-TT-BXD": {
        "so_hieu": "71/2025/TT-BXD",
        "ten_van_ban": "Thông tư sửa đổi, bổ sung một số điều của các Thông tư để cắt giảm, đơn giản hóa thủ tục hành chính trong lĩnh vực đăng kiểm, hàng không dân dụng và thanh tra thuộc phạm vi quản lý của Bộ Xây dựng",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-12-31",
        "ngay_hieu_luc": "2025-12-31",
        "con_hieu_luc": True,
    },

    # Bãi bỏ Điều 27 và Điều 28 Thông tư số 09/2025/TT-BXD ngày 13 tháng 6 năm 2025 của Bộ trưởng Bộ Xây dựng 
    # về sửa đổi, bổ sung một số điều của các Thông tư thuộc lĩnh vực quản lý nhà nước của Bộ Xây dựng liên quan 
    # đến sắp xếp tổ chức bộ máy, thực hiện chính quyền địa phương hai cấp và phân cấp cho chính quyền địa phương.
    # Chương I: Sửa đổi, bổ sung Thông-tư-36-2024-TT-BGTVT
    # Chương II: Sửa đổi, bổ sung Thông-tư-40-2024-TT-BGTVT
    # Chương III: Sửa đổi, bổ sung Thông-tư-41-2024-TT-BGTVT
    "Thông-tư-72-2025-TT-BXD": {
        "so_hieu": "72/2025/TT-BXD",
        "ten_van_ban": "Thông tư sửa đổi, bổ sung một số điều của Thông tư số 36/2024/TT-BGTVT ngày 15 tháng 11 năm 2024 của Bộ trưởng Bộ Giao thông vận tải quy định về tổ chức, quản lý hoạt động vận tải bằng xe ô tô và hoạt động của bến xe, bãi đỗ xe, trạm dừng nghỉ, điểm dừng xe trên đường bộ; quy định trình tự, thủ tục đưa bến xe, trạm dừng nghỉ vào khai thác, Thông tư số 40/2024/TT-BGTVT ngày 15 tháng 11 năm 2024 của Bộ trưởng Bộ Giao thông vận tải quy định về công tác phòng, chống, khắc phục hậu quả thiên tai trong lĩnh vực đường bộ; Thông tư số 41/2024/TT-BGTVT ngày 15 tháng 11 năm 2024 của Bộ trưởng Bộ Giao thông vận tải quy định về quản lý, vận hành, khai thác và bảo trì kết cấu hạ tầng đường bộ, Thông tư số 22/2014/TT-BGTVT ngày 06 tháng 6 năm 2014 của Bộ trưởng Bộ Giao thông vận tải hướng dẫn xây dựng quy trình vận hành, khai thác bến phà, bến khách ngang sông sử dụng phà một lưỡi chở hành khách và xe ô tô",
        "loai_van_ban": "thong_tu",
        "co_quan_ban_hanh": "Bộ Xây dựng",
        "ngay_ban_hanh": "2025-12-31",
        "ngay_hieu_luc": "2025-12-31",
        "con_hieu_luc": True,
    },

}
