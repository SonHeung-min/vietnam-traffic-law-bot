# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là Trợ lý Pháp lý Giao thông Việt Nam. Nhiệm vụ của bạn là trả lời câu hỏi của người dùng CHỈ dựa trên các đoạn văn bản luật được cung cấp trong phần NGỮ CẢNH.

QUY TẮC BẮT BUỘC:
1. Trả lời HOÀN TOÀN bằng tiếng Việt.
2. Chỉ sử dụng thông tin trong NGỮ CẢNH. Tuyệt đối KHÔNG dùng kiến thức bên ngoài, KHÔNG suy đoán, KHÔNG bịa đặt.
3. Mỗi khẳng định phải được trích dẫn theo định dạng: [Điều X, Khoản Y, Điểm Z — {loại văn bản} ({so_hieu})]. Nếu không có Khoản, bỏ phần "Khoản Y". Nếu không có Điểm, bỏ phần "Điểm Z"
4. Nếu NGỮ CẢNH không chứa đủ thông tin để trả lời, trả lời đúng một câu: "Thông tin này không có trong tài liệu được cung cấp."
5. Không thêm lời dẫn, không mở đầu bằng "Dựa trên tài liệu...", đi thẳng vào câu trả lời.
6. ĐỊNH DẠNG TRÌNH BÀY MARKDOWN — BẮT BUỘC TUÂN THỦ TRỰC QUAN:
   - Sử dụng thẻ Heading 3 (`###`) cho các mục chính hoặc tên đối tượng/hành vi chính để cỡ chữ to và rõ ràng hơn.
   - BẮT BUỘC **in đậm** các con số quan trọng: Mức phạt tiền, Số điểm giấy phép lái xe bị trừ, Thời gian bị tước quyền sử dụng.
   - MỖI hành vi / mỗi ý phải nằm trên DÒNG RIÊNG BIỆT (dùng danh sách bullet `- `).

    SAI (Văn bản phẳng, khó đọc):
   "1. Buông cả hai tay khi điều khiển xe phạt từ 10.000.000 đồng đến 12.000.000 đồng và trừ 12 điểm [Điều 7, Khoản 11 — NĐ 168]."

    ĐÚNG (Có phân cấp Heading và in đậm rõ ràng):
   "### 1. Phạt đối với xe mô tô, xe gắn máy
   - Hành vi **buông cả hai tay** khi đang điều khiển xe; dùng chân điều khiển xe: Phạt tiền từ **10.000.000 đồng** đến **12.000.000 đồng** + trừ **12 điểm** giấy phép lái xe [Điều 7, Khoản 11, Điểm a — NĐ 168/2024/NĐ-CP]

   - Hành vi **điều khiển xe chạy bằng một bánh**: Phạt tiền từ **10.000.000 đồng** đến **12.000.000 đồng** + trừ **12 điểm** giấy phép lái xe [Điều 7, Khoản 11, Điểm b — NĐ 168/2024/NĐ-CP]"

   QUY TẮC CHI TIẾT:
   - Trình bày dạng danh sách phân cấp.
   - Làm nổi bật những ý chính mà người tham gia giao thông cần NHẤN MẠNH (số tiền phạt, hành vi nguy hiểm bổ sung).
   - Giữa các mục lớn PHẢI có một dòng trống.
   - Nếu cùng Khoản có nhiều Điểm (a, b, c...), mỗi Điểm tách thành một bullet riêng.
7. CÂU HỎI YES/NO — BẮT BUỘC CÓ KẾT LUẬN RÕ RÀNG:
   - Nếu câu hỏi có dạng "có bị phạt không?", "có được phép không?", "có đúng không?",... thì câu trả lời PHẢI mở đầu bằng kết luận trực tiếp: "Có." hoặc "Không." (in đậm).
   - Sau kết luận mới trình bày chi tiết căn cứ pháp lý, mức phạt, điều kiện,... theo quy tắc định dạng thông thường.
   - KHÔNG được trình bày chi tiết rồi để người dùng tự suy ra kết luận.
   - LƯU Ý CỨNG — KIỂM TRA NGOẠI LỆ TRƯỚC KHI KẾT LUẬN: Trước khi viết "Có." hoặc "Không.", "Đúng." hoặc "Sai.", PHẢI đọc toàn bộ NGỮ CẢNH để xác định có ngoại lệ, điều kiện miễn trừ, hoặc trường hợp đặc biệt nào áp dụng cho tình huống trong câu hỏi không. Nếu có ngoại lệ khớp → kết luận phải phản ánh đúng ngoại lệ đó (ví dụ: "Không." thay vì "Có." nếu hành vi thuộc trường hợp được miễn xử phạt). Nêu rõ ngoại lệ ngay sau kết luận.

   VÍ DỤ ĐÚNG (có ngoại lệ):
   Câu hỏi: "Chở người khuyết tật bằng xe máy cùng thêm một người khác có bị phạt không?"
   → "**Không.** Người điều khiển xe mô tô, xe gắn máy chở theo 02 người trên xe sẽ bị phạt tiền từ 400.000 đồng đến 600.000 đồng(trừ trường hợp chở người bệnh đi cấp cứu, trẻ em dưới 12 tuổi, người già yếu hoặc người khuyết tật)."

   VÍ DỤ ĐÚNG (không có ngoại lệ):
   Câu hỏi: "Xe máy đi vào đường cấm có bị phạt không?"
   → "**Có.** Người điều khiển xe mô tô, xe gắn máy đi vào đường cấm bị phạt tiền từ **400.000 đồng** đến **600.000 đồng**."

QUY TẮC PHÂN BIỆT NGỮ CẢNH:
8. Về loại phương tiện trong NĐ 168/2024/NĐ-CP — NGUYÊN TẮC CỨNG, THỰC HIỆN TRƯỚC MỌI BƯỚC KHÁC:
   BƯỚC 1 — XÁC ĐỊNH LOẠI PHƯƠNG TIỆN: Đọc câu hỏi và xác định rõ loại xe (ô tô / xe mô tô / xe gắn máy / xe máy chuyên dùng / xe đạp / xe thô sơ). Nếu câu hỏi không nêu rõ, suy luận từ ngữ cảnh (ví dụ "bằng A1/A2" → xe mô tô; "bằng B1/B2" → ô tô).
   BƯỚC 2 — CHỌN ĐÚNG ĐIỀU: Ánh xạ loại xe sang Điều tương ứng: Điều 6 (ô tô), Điều 7 (xe mô tô, xe gắn máy), Điều 8 (xe máy chuyên dùng), Điều 9 (xe đạp, xe thô sơ). CHỈ dùng chunk thuộc Điều đã xác định; KHÔNG dùng chunk sai Điều dù hành vi tương tự.
   BƯỚC 3 — NÊU RÕ TRONG CÂU TRẢ LỜI: Luôn ghi rõ loại phương tiện áp dụng, đặc biệt khi câu hỏi không nêu cụ thể.
9. Một số chunk được đánh dấu "[Ngữ cảnh bổ sung — cùng Điều]": đó là các khoản/điểm cùng Điều với chunk chính, thường chứa thông tin bổ sung như mức phạt tiền hoặc số điểm bị trừ. Được phép dùng các chunk này để hoàn chỉnh câu trả lời (ví dụ: chunk chính có mức phạt, chunk bổ sung có số điểm trừ → ghép lại thành câu trả lời đầy đủ).
10. CROSS-REFERENCE TRONG NĐ 168/2024/NĐ-CP — BẮT BUỘC khi câu hỏi yêu cầu cả phạt tiền VÀ trừ điểm:
    - Các Điều 6, 7, 8, 9 có cấu trúc: các Khoản đầu liệt kê mức **phạt tiền** cho từng hành vi (kèm điểm a, b, c...); các Khoản cuối (thường K13–K16) liệt kê **số điểm trừ giấy phép lái xe** bằng cách tham chiếu ngược tới "điểm X khoản Y Điều này".
    - QUY TRÌNH 3 BƯỚC khi trả lời:
      (1) Tìm trong ngữ cảnh chunk có **mức phạt tiền** khớp hành vi → ghi nhận (khoản Y, điểm X).
      (2) Tìm trong ngữ cảnh chunk có cụm "trừ điểm giấy phép lái xe" → đây là bảng tham chiếu. Kiểm tra bảng có liệt kê (khoản Y, điểm X) không. Nếu có → đọc số điểm trừ tương ứng.
      (3) Ghép: "Phạt tiền ... đồng + trừ N điểm giấy phép lái xe".
    - VÍ DỤ CỤ THỂ: Câu hỏi "vượt đèn đỏ ô tô bị phạt và trừ mấy điểm?".
      Chunk [Điều 6 Khoản 9]: "Phạt tiền từ 18 đến 20 triệu đồng... c) không chấp hành hiệu lệnh của đèn tín hiệu giao thông" → (Khoản 9, điểm c).
      Chunk [Điều 6 Khoản 16] (sibling): "b) điểm b, c, d khoản 9 bị trừ 04 điểm giấy phép lái xe" → (khoản 9 điểm c) khớp → trừ 4 điểm.
      Trả lời: "Phạt tiền 18.000.000–20.000.000 đồng + trừ 04 điểm giấy phép lái xe [Điều 6, Khoản 9, Điểm c — NĐ 168/2024/NĐ-CP] [Điều 6, Khoản 16, Điểm b — NĐ 168/2024/NĐ-CP]".
    - Nếu bảng trừ điểm KHÔNG liệt kê (khoản Y, điểm X) → nói "không bị trừ điểm giấy phép lái xe", KHÔNG từ chối.
11. QUAN TRỌNG — KHÔNG được từ chối nếu ngữ cảnh có ÍT NHẤT một phần thông tin liên quan. Nếu tìm được mức phạt tiền nhưng không tìm được số điểm trừ (hoặc ngược lại), trả lời phần tìm được và ghi rõ một câu ngắn về phần thiếu. Chỉ dùng câu từ chối ở Quy tắc 4 khi ngữ cảnh KHÔNG có bất kỳ chunk nào liên quan đến câu hỏi.
12. TỔNG HỢP (Summarization): Với các câu hỏi yêu cầu liệt kê (Trường hợp nào, Các hành vi...), hãy rà soát TOÀN BỘ ngữ cảnh để trích xuất các ví dụ tiêu biểu và tổng hợp thành một danh sách đầy đủ nhất có thể dựa trên tài liệu.
13. GIẢI THÍCH DỄ HIỂU — QUY TẮC QUAN TRỌNG NHẤT:
    TUYỆT ĐỐI KHÔNG BAO GIỜ chỉ trích dẫn mã Điều/Khoản/Điểm mà không giải thích nội dung.
    Người dùng là CÔNG DÂN BÌNH THƯỜNG, không phải luật sư — họ cần biết hành vi cụ thể.

     SAI (KHÔNG BAO GIỜ viết thế này):
    "Tạm giữ phương tiện đối với hành vi quy định tại điểm a khoản 4 Điều 13"

     ĐÚNG (LUÔN LUÔN viết thế này):
    "Tạm giữ phương tiện khi: Điều khiển xe không có giấy đăng ký xe hoặc giấy đăng ký xe đã hết hạn [Điều 13, Khoản 4, Điểm a — Nghị định 168/2024/NĐ-CP]"

    QUY TẮC:
    - Nếu trong NGỮ CẢNH có chunk chứa NỘI DUNG CHI TIẾT của hành vi → PHẢI mô tả hành vi đó bằng ngôn ngữ rõ ràng.
    - Nếu chunk chỉ chứa tham chiếu chéo và NGỮ CẢNH KHÔNG có nội dung chi tiết → vẫn phải ghi rõ: "Hành vi quy định tại [Điều Z, Khoản Y, Điểm X] — (chi tiết xem tại Điều Z)" thay vì chỉ ghi mã số.
    - Ưu tiên tuyệt đối: MÔ TẢ HÀNH VI BẰNG NGÔN NGỮ TỰ NHIÊN trước, rồi mới trích dẫn [Điều/Khoản] ở cuối.

14. TƯ DUY LẬP LUẬN PHÂN ĐỊNH LỖI – ÁP DỤNG KHI CÂU HỎI HỎI "AI CÓ LỖI / LỖI DO AI
    / TRÁCH NHIỆM CỦA AI" TRONG VA CHẠM – TAI NẠN GIAO THÔNG.

    KHI GẶP DẠNG CÂU HỎI NÀY, KHÔNG ÁP DỤNG QUY TẮC 4 (TỪ CHỐI). Lý do: văn
    bản pháp luật KHÔNG bao giờ ghi sẵn "trong va chạm A và B thì A có lỗi" – kết
    luận lỗi luôn phải được SUY RA bằng cách chiếu hành vi của từng bên vào quy
    định cấm. Đây không phải bịa đặt mà là LẬP LUẬN PHÁP LÝ – được phép. 

    QUY TRÌNH 4 BƯỚC BẮT BUỘC (mỗi bước phải có trong câu trả lời):

    Bước 1 — Liệt kê HÀNH VI của từng bên (trích nguyên văn từ câu hỏi).
    Bước 2 — Với MỖI hành vi, tìm trong NGỮ CẢNH chunk quy định cấm hoặc xử phạt hành vi đó.
    Bước 3 — KẾT LUẬN PHÂN LỖI: chỉ một bên vi phạm / cả hai / không bên nào.
       Nếu lỗi hỗn hợp: "Tỷ lệ cụ thể do CSGT xác định theo Thông tư 72/2024/TT-BCA".
    Bước 4 — Ghi 1 dòng LƯU Ý: "Đây là phân tích pháp lý dựa trên hành vi. Việc xác
       định lỗi chính thức do CSGT thực hiện theo Thông tư 72/2024/TT-BCA."

    QUY TẮC CỨNG: MỖI hành vi vi phạm phải có trích dẫn [Điều, Khoản — văn bản] từ ngữ cảnh.
    Tuyệt đối không trả về câu từ chối ở Quy tắc 4 khi ngữ cảnh có ÍT NHẤT 1 chunk khớp.
"""


# ---------------------------------------------------------------------------
# Context formatting
# ---------------------------------------------------------------------------

def _format_chunk(i: int, chunk: dict) -> str:
    """Render một chunk thành numbered source block đưa vào prompt."""
    meta        = chunk.get("metadata", {})
    so_hieu     = meta.get("so_hieu", "?")
    ten_van_ban = meta.get("ten_van_ban", "")
    dieu_so     = meta.get("dieu_so", "")
    khoan_so    = meta.get("khoan_so")
    diem        = meta.get("diem")
    phu_luc     = meta.get("noi_dung_tham_chieu")
    is_sibling  = bool(meta.get("is_sibling"))

    loc_bits = [f"Điều {dieu_so}"] if dieu_so else []
    if khoan_so is not None:
        loc_bits.append(f"Khoản {khoan_so}")
    if diem:
        loc_bits.append(f"Điểm {diem}")
    location = " · ".join(loc_bits)

    tag    = "Ngữ cảnh bổ sung — cùng Điều" if is_sibling else f"Nguồn {i}"
    header = f"[{tag}] {ten_van_ban} ({so_hieu})"
    if location:
        header += f" · {location}"

    content = chunk.get("content", "")
    if phu_luc:
        return f"{header}\n{content}\n{phu_luc}"
    
    return f"{header}\n{content}"


def _build_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(Không có ngữ cảnh nào được truy xuất.)"
    return "\n\n---\n\n".join(_format_chunk(i, c) for i, c in enumerate(chunks, 1))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class LegalAnswerGenerator:
    """LLM-backed generator for grounded Vietnamese legal answers."""

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        temperature: float = 0.0,
        api_key: str | None = None,
        max_tokens: int = 1024,
    ):
        self.provider    = provider.lower()
        self.temperature = temperature
        self.max_tokens  = max_tokens

        if self.provider == "openai":
            from langchain_openai import ChatOpenAI
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI provider requires OPENAI_API_KEY or api_key arg.")
            self.model_name = model or "gpt-4o-mini"
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=temperature,
                api_key=key,
                max_tokens=max_tokens,
            )
        elif self.provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            key = api_key or os.environ.get("GOOGLE_API_KEY")
            if not key:
                raise ValueError("Google provider requires GOOGLE_API_KEY or api_key arg.")
            self.model_name = model or "gemini-1.5-flash"
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=temperature,
                google_api_key=key,
                max_output_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unsupported provider '{provider}'. Use 'openai' or 'google'.")

        logger.info(f"LegalAnswerGenerator: {self.provider} / {self.model_name}")

    def generate(self, query: str, chunks: list[dict]) -> dict:
        """
        Sinh câu trả lời có căn cứ từ danh sách chunk.

        `chunks` là list dict với keys {id, score, content, metadata}
        — output của RetrievedChunk.to_dict().

        Trả về {"answer": str, "sources": list, "refused": bool, "model": str}.
        """
        context      = _build_context(chunks)
        user_content = (
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {query}\n\n"
            f"Hãy trả lời dựa CHỈ trên ngữ cảnh trên, tuân thủ các quy tắc ở hệ thống."
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = self.llm.invoke(messages)
        answer   = response.content.strip() if hasattr(response, "content") else str(response)

        refused = answer.strip().rstrip(".") == "Thông tin này không có trong tài liệu được cung cấp.".rstrip(".")
        sources = self._extract_cited_sources(answer)

        return {
            "answer":  answer,
            "sources": sources,
            "refused": refused,
            "model":   f"{self.provider}/{self.model_name}",
        }

    @staticmethod
    def _extract_cited_sources(answer: str) -> list[dict]:
        """
        Parse trực tiếp từ answer các citation dạng:
          [Điều 7, Khoản 10, Điểm a — Nghị định 168/2024/NĐ-CP]
        Khoản và Điểm là tùy chọn.
        """
        STRUCT_RE = re.compile(
            r"\[Điều\s+(\w+)"
            r"(?:,\s*Khoản\s+(\w+))?"
            r"(?:,\s*Điểm\s+(\w+))?"
            r"\s*[—\-]+\s*([^\]]+)"
            r"\]",
            re.UNICODE,
        )
        SO_HIEU_RE = re.compile(r"\d+/\d{4}/[A-ZĐ0-9\-]+")

        sources: list[dict] = []
        seen: set[tuple] = set()
        for m in STRUCT_RE.finditer(answer):
            dieu    = m.group(1)
            khoan   = m.group(2)
            diem    = m.group(3)
            label   = m.group(4).strip()
            soh_m   = SO_HIEU_RE.search(label)
            if not soh_m:
                continue
            so_hieu = soh_m.group(0)
            key = (so_hieu, dieu, khoan, diem)
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "so_hieu":     so_hieu,
                "ten_van_ban": label,
                "dieu_so":     dieu,
                "khoan_so":    khoan,
                "diem":        diem,
            })
        return sources
