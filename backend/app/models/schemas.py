from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default="default")


class SourceDocument(BaseModel):
    """Một nguồn trích dẫn trả về cho frontend hiển thị."""

    chunk_id: str
    citation: str                       # vd "Điều 8 Khoản 3, Luật 35/2024/QH15"
    content_preview: str                # nội dung rút gọn để show

    # Định danh văn bản
    so_hieu: str                        # vd "35/2024/QH15"
    loai_van_ban: str                   # "luat" | "nghi_dinh"

    # Vị trí trong văn bản (phần chính)
    dieu_so: int | None = None
    dieu_ten: str | None = None
    khoan_so: int | None = None
    diem: str | None = None

    # Vị trí trong phụ lục (nếu là chunk phụ lục/mẫu)
    phu_luc_so: int | None = None
    mau_so: str | None = None

    # Hiệu lực + cảnh báo sửa đổi
    con_hieu_luc: bool = True
    ngay_het_hieu_luc: str | None = None
    loai_thay_doi: str | None = None    # "sua_doi" | "bai_bo" | "thay_the" | None
    bi_sua_doi_boi: str | None = None   # chunk_id của điều/khoản đã sửa


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    llm: str