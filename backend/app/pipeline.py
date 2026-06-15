# -*- coding: utf-8 -*-
"""
pipeline.py — Orchestration layer trên rag_core
================================================
Flow:
  query + chat_history
      → AnalyzerNode  (phân loại + chuẩn hoá + mở rộng query)
      → route_by_category
          ├─ legal_rag    → LegalRagNode  (HybridRetriever + LegalAnswerGenerator)
          └─ out_of_scope → out_of_scope_node (từ chối cố định)

Sử dụng:
    pipeline = RAGPipeline(retriever, generator, llm)
    result   = pipeline.run("vượt đèn đỏ bị phạt bao nhiêu?", chat_history=[...])
"""

from __future__ import annotations

import logging
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State & types
# ---------------------------------------------------------------------------

Category = Literal["legal_rag", "out_of_scope"]

class AnalyzerOutput(BaseModel):
    category:        Category = Field(description="Intent category")
    standalone_query: str     = Field(description="Self-contained rewrite using history.")
    retrieval_query:   str     = Field(description="Formal legal terminology for retrieval.")

class State(TypedDict, total=False):
    query: str
    raw_query: str
    retrieval_query: str
    category: str
    chat_history: list[dict]
    chunks: list[dict]
    answer: str
    sources: list[dict]
    refused: bool
    model_info: str
    error: str


# ---------------------------------------------------------------------------
# Prompts & constants
# ---------------------------------------------------------------------------

CONTEXTUALIZE_HISTORY_TURNS = 6

OUT_OF_SCOPE_MESSAGE = """
    Xin lỗi, tôi chỉ tư vấn về Luật Giao thông Việt Nam và không giải quyết các 
    vấn đề ngoài phạm vi này. Bạn có thể hỏi tôi về mức phạt vi phạm, quy định 
    đăng ký xe, đăng kiểm, cấp giấy phép lái xe, v.v.
"""

ANALYZER_SYSTEM_PROMPT = """
Bạn đóng vai trò là bộ phân tích truy vấn cho hệ thống hỏi đáp về pháp luật giao thông đường bộ Việt Nam.
Nhiệm vụ của bạn là đọc:
  1. Lịch sử hội thoại trước đó nếu có.
  2. Câu hỏi hiện tại của người dùng.

Sau đó xử lý những công việc sau:

============================================================
I. PHÂN LOẠI CATEGORY
============================================================
Phân loại câu hỏi của người dùng vào một trong hai category sau:

1. "legal_rag": câu hỏi liên quan đến pháp luật giao thông đường bộ Việt Nam (xử phạt, quy tắc, giấy tờ/thủ tục, tai nạn/phân định lỗi,...).
   → Ưu tiên tuyệt đối: chỉ cần có yếu tố giao thông đường bộ, dù xen lẫn chủ đề khác, vẫn chọn "legal_rag".

2. "out_of_scope": tất cả còn lại — chào hỏi xã giao, chủ đề ngoài giao thông (thể thao, công nghệ, du lịch,...), pháp luật không liên quan (dân sự, hình sự, lao động,...).

============================================================
II. CHUẨN HÓA CÂU HỎI
============================================================
- Tạo standalone_query bằng cách viết lại câu hỏi hiện tại thành một câu đầy đủ, độc lập, có thể hiểu được mà không cần đọc lại lịch sử hội thoại.
- Yêu cầu standalone_query phải:
  + Giải quyết các đại từ hoặc tham chiếu mơ hồ dựa trên ngữ cảnh trước đó. Ví dụ nếu câu hỏi hiện tại dùng các cụm như: "vậy thì sao",
    "trường hợp này", "xe đó", "người kia", "như vậy",... thì phải dựa vào lịch sử hội thoại để viết lại thành câu đầy đủ.
  + Giữ nguyên thông tin quan trọng như loại phương tiện (ô tô, xe máy, xe tải,...), mức phạt, lỗi vi phạm, tình huống cụ thể,... trước đó
  + Không tự thêm tình tiết mới ngoài những gì người dùng cung cấp
  + Với câu hỏi thuộc category "out_of_scope", có thể giữ gần như nguyên văn câu hỏi gốc

============================================================
IV. TẠO TRUY VẤN MỞ RỘNG CHO RETRIEVER
============================================================
- Tạo retrieval_query để phục vụ truy hồi tài liệu pháp luật. Đây không cần là câu tự nhiên, mà là chuỗi từ khóa giàu ngữ nghĩa pháp lý.
- **QUY TẮC THUẬT NGỮ BẮT BUỘC**: Trong retrieval_query, LUÔN dùng "mô tô" thay cho "xe máy" vì văn bản pháp luật dùng thuật ngữ "mô tô". Ví dụ: "xe máy" → "mô tô", "xe máy 50cc" → "mô tô 50cc".
- Chiến lược mở rộng như sau:
    1. Với câu hỏi dạng yes/no:
        ** LUÔN LUÔN giữ lại đầy đủ các yếu tố quan trọng: hành vi, phương tiện, đối tượng, điều kiện,
        ngoại lệ, hạng giấy phép, thời hạn, mức phạt, trừ điểm, tước giấy phép lái xe.**

        a) Nếu câu hỏi hỏi về việc có bị xử phạt không:
            - Tập trung vào quy định gốc cần tìm trong văn bản pháp luật.
            - Loại bỏ các từ nghi vấn ít giá trị tìm kiếm như: "có không", "đúng không", "phải không", "được không", "bị không", "nhỉ", "ạ", "cho hỏi".
            - Biến câu hỏi thành truy vấn dạng mệnh đề: {hành vi chính} {đối tượng/phương tiện} {điều kiện} quy định xử phạt mức phạt (trừ trường hợp ngoại lệ)
        
        b) Nếu câu hỏi hỏi về việc một mệnh đề có đúng không:
            - Viết lại thành truy vấn dạng mệnh đề kiểm tra quy định liên quan đến mệnh đề đó.
            - Giữ nguyên các số liệu, thời hạn, hạng xe, hạng giấy phép hoặc điều kiện cụ thể.
    2. Với câu hỏi tai nạn / phân định lỗi (BẮT BUỘC PHÂN TÍCH):
        - Tách câu hỏi thành DANH SÁCH CÁC HÀNH VI VI PHẠM ĐỘC LẬP của TỪNG bên.
        - Mỗi hành vi viết thành 1 cụm tra cứu kiểu "mức phạt + {hành vi}".
        - Nối các cụm bằng dấu " | " trong cùng một chuỗi retrieval_query.
    3. Với câu hỏi pháp lý đơn lẻ (mức phạt, thủ tục, quy tắc,...):
        - Mở rộng thuật ngữ pháp lý 
        - 'Mức phạt/Bị gì': "{Hành vi} + mức xử phạt".
        - 'Khi nào/Trường hợp nào': "{Chủ đề} + các hành vi vi phạm + hình thức xử
        phạt bổ sung + biện pháp khắc phục hậu quả".
        - 'Thủ tục/Đâu': "{Thủ tục} + trình tự + thẩm quyền + hồ sơ".

        VD: "vượt đèn đỏ ô tô bị phạt bao nhiêu" → "mức phạt vượt đèn đỏ xe ô tô không
          chấp hành hiệu lệnh đèn tín hiệu"
    4. Với câu hỏi pháp lý nhiều ý
        - retrieval_query PHẢI gồm thuật ngữ cho TẤT CẢ các ý, không gộp/lược bỏ.


FEW-SHOT (HỌC THEO CÁC VÍ DỤ NÀY):

Ví dụ 1 — CÂU HỎI YES/NO:
  Question: "Chở người khuyết tật bằng xe máy cùng thêm một người khác có bị xử phạt không?"
    --> category: legal_rag
    --> standalone_query: "Chở người khuyết tật bằng xe máy cùng thêm một người khác có bị xử phạt không?"
    --> retrieval_query: "Chở 2 người là người khuyết tật và người khác bằng mô tô xử phạt mức phạt"

Ví dụ 2 — CÂU HỎI YES/NO:
  Question: "Tôi năm nay 15 tuổi thì có được phép lái xe máy 50cc không?"
    --> category: legal_rag
    --> standalone_query: "Năm nay tôi 15 tuổi có đủ điều kiện điều khiển xe máy 50cc không?"
    --> retrieval_query: "15 tuổi có đủ điều kiện lái mô tô 50cc quy định xử phạt mức phạt"

Ví dụ 3 — TÌNH HUỐNG TAI NẠN, 2 HÀNH VI:
  Question: "Tôi chạy ngược chiều va chạm với người chạy quá tốc độ thì lỗi do ai"
    --> category: legal_rag
    --> standalone_query: "Khi va chạm giữa người đi ngược chiều và người chạy quá tốc độ thì ai có lỗi?"
    --> retrieval_query: "mức phạt đi ngược chiều xe ô tô mô tô đường một chiều
        | mức phạt chạy quá tốc độ vượt quá tốc độ quy định


Ví dụ 4 — TÌNH HUỐNG TAI NẠN, 1 BÊN VI PHẠM RÕ:
  Question: "tôi đang đi đúng làn, một người từ làn ngược hướng sang đường không xi nhan 
            thì tôi va chạm phải họ, lỗi do ai?"
    --> category: legal_rag
    --> standalone_query: "Tôi đi đúng làn, va chạm với người chuyển hướng sang đường
        không bật xi nhan – lỗi thuộc về ai?"
    --> retrieval_query: "mức phạt chuyển hướng không bật đèn tín hiệu xi nhan
        | quy tắc chuyển làn chuyển hướng nhường đường 
        | đi đúng phần đường làn đường quy định

Ví dụ 5 — CÂU HỎI PHÁP LÝ ĐƠN LẺ
 Question: "đi ngược chiều thì bị phạt bao nhiêu?"
  --> category: legal_rag
  --> standalone_query: "Đi ngược chiều bị phạt bao nhiêu tiền?"
  --> retrieval_query: "đi ngược chiều xe ô tô mô tô chiều đường một chiều đường có biển báo cấm mức phạt"


QUY TẮC CHUNG:
- Trả về JSON đúng schema yêu cầu.
- Trong standalone_query: giữ nguyên ngôn ngữ tự nhiên của người dùng (ô tô / xe máy / xe tải / xe đạp).
- Trong retrieval_query: LUÔN dùng "mô tô" thay cho "xe máy" (thuật ngữ pháp lý chính xác).
"""



# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _format_history_for_prompt(history: list[dict]) -> str:
    lines = []
    for msg in history[-CONTEXTUALIZE_HISTORY_TURNS:]:
        role    = msg.get("role", "?")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        label = "user" if role == "user" else "assistant"
        lines.append(f"  {label}: {content}")

        sources = msg.get("sources") or []
        if role == "assistant" and sources:
            source_labels = []
            for i, s in enumerate(sources, 1):
                parts = []
                if s.get("dieu_so"):   parts.append(f"Điều {s['dieu_so']}")
                if s.get("khoan_so"):  parts.append(f"Khoản {s['khoan_so']}")
                if s.get("ten_van_ban"): parts.append(s["ten_van_ban"])
                source_labels.append(f"[{i}] {' · '.join(parts) or s.get('so_hieu', 'Nguồn')}")
            lines.append(f"    (Nguồn đã trích dẫn: {', '.join(source_labels)})")
    return "\n".join(lines) if lines else "(chưa có)"


# ---------------------------------------------------------------------------
# RAGPipeline — entry point duy nhất
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    Orchestrates analyzer → router → (legal_rag | out_of_scope).

    Ví dụ:
        from langchain_openai import ChatOpenAI
        from rag_core import HybridRetriever, LegalAnswerGenerator
        from app.pipeline import RAGPipeline

        llm       = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        retriever = HybridRetriever(...)
        generator = LegalAnswerGenerator(...)

        pipeline = RAGPipeline(retriever, generator, llm)
        result   = pipeline.run("vượt đèn đỏ bị phạt bao nhiêu?")
        print(result["answer"])
    """

    def __init__(self, retriever, generator, llm):
        self._retriever     = retriever
        self._generator     = generator
        self._llm           = llm
        self._structured_llm = llm.with_structured_output(AnalyzerOutput)

    # ------------------------------------------------------------------ nodes

    def _analyze(self, state: State) -> dict:
        raw          = state.get("query", "")
        history      = state.get("chat_history") or []
        history_text = _format_history_for_prompt(history)

        try:
            result = self._structured_llm.invoke([
                SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
                HumanMessage(content=(
                    f"Lịch sử hội thoại:\n{history_text}\n\n"
                    f"Câu hỏi mới nhất: {raw}"
                )),
            ])
            if not result or not hasattr(result, "category"):
                logger.warning("Analyzer trả về kết quả rỗng, dùng defaults")
                return {
                    "category": "legal_rag", 
                    "query": raw,
                    "retrieval_query": raw,
                    "raw_query": raw
                }
            
            return {
                "category":       getattr(result, "category", "legal_rag"),
                "query":          raw if not history else getattr(result, "standalone_query", raw),
                "retrieval_query": getattr(result, "retrieval_query", raw),
                "raw_query":      raw,
            }
        
        except Exception as exc:
            logger.error("Analyzer thất bại (%s); fallback defaults", exc)
            return {
                "category": "legal_rag", 
                "query": raw,
                "retrieval_query": raw, 
                "raw_query": raw
            }

    def _legal_rag(self, state: State) -> dict:
        query           = state["query"]
        retrieval_query = state.get("retrieval_query") or query
        top_k = 15

        try:
            chunks = []

            if hasattr(self._retriever, "get_chunks_by_explicit_reference"):
                chunks = self._retriever.get_chunks_by_explicit_reference(
                    query, include_siblings=True
                )

            if not chunks:
                chunks = self._retriever.get_relevant_chunks(retrieval_query, top_k=top_k)

        except Exception as exc:
            logger.exception("Retriever thất bại: %s", exc)
            return {
                "chunks": [],
                "answer": "",
                "sources": [],
                "refused": False,
                "model_info": "",
                "error": str(exc),
            }

        

        chunk_dicts = [c.to_dict() for c in chunks]
        if not chunk_dicts:
            return {
                "chunks": [], 
                "answer": "", 
                "sources": [],
                "refused": True, 
                "model_info": ""
            }

        try:
            result = self._generator.generate(query, chunk_dicts)
        except Exception as exc:
            logger.exception("Generator thất bại: %s", exc)
            return {
                "chunks": chunk_dicts, 
                "answer": "", 
                "sources": [],
                "refused": False, 
                "model_info": "", 
                "error": str(exc)
            }

        return {
            "chunks":     chunk_dicts,
            "answer":     result["answer"],
            "sources":    result["sources"],
            "refused":    bool(result.get("refused")),
            "model_info": result.get("model", ""),
        }

    
    def _out_of_scope(self, state: State) -> dict:
        return {
            "answer": OUT_OF_SCOPE_MESSAGE, 
            "sources": [], 
            "refused": False
        }

    # --------------------------------------------------------------- run

    def run(
        self,
        query: str,
        chat_history: list[dict] | None = None,
    ) -> State:
        """
        Chạy pipeline và trả về State đầy đủ.

        Keys quan trọng trong kết quả:
          - answer     : str
          - sources    : list[dict]
          - refused    : bool
          - category   : "legal_rag" | "out_of_scope"
          - model_info : str
        """
        state: State = {
            "query":        query,
            "chat_history": chat_history or [],
        }

        # Bước 1: Phân tích
        state.update(self._analyze(state))
        category = state.get("category", "out_of_scope")
        logger.info("category=%s | query='%s'", category, state.get("query"))

        # Bước 2: Route & thực thi
        if category == "legal_rag":
            state.update(self._legal_rag(state))
        else:
            state.update(self._out_of_scope(state))

        return state
