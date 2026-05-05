import streamlit as st
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import send_message
from components.sidebar import render_sidebar
from components.chat_ui import render_chat_history, render_sources

# ── Cấu hình trang ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chatbot Luật Giao thông",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS tùy chỉnh ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f4e79;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .stChatMessage { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── Sidebar ──────────────────────────────────────────────────────────────────
suggested_question = render_sidebar(st.session_state.session_id)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🚦 Chatbot Luật Giao thông Đường bộ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hỏi đáp dựa trên Luật & Nghị định hiện hành về giao thông đường bộ Việt Nam</div>', unsafe_allow_html=True)

# ── Hiển thị lịch sử chat ────────────────────────────────────────────────────
if not st.session_state.messages:
    st.info(
        "👋 Xin chào! Hãy đặt câu hỏi về Luật Giao thông Đường bộ. "
        "Bạn có thể dùng các câu hỏi gợi ý ở thanh bên trái."
    )
else:
    render_chat_history(st.session_state.messages)

# ── Lấy input ────────────────────────────────────────────────────────────────
# Luôn render chat_input để đảm bảo input box hiện ở mọi rerun
typed_question = st.chat_input("Nhập câu hỏi về luật giao thông...")

# Ưu tiên sidebar suggestion, sau đó câu user gõ
question = suggested_question or typed_question

# ── Xử lý câu hỏi ────────────────────────────────────────────────────────────
if question:
    # Append user message vào history rồi rerun để render thống nhất qua render_chat_history
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.pending_question = question
    st.rerun()

# Sau rerun, nếu có pending_question thì gọi API
if st.session_state.pending_question:
    pending = st.session_state.pending_question
    st.session_state.pending_question = None  # consume

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm trong văn bản luật..."):
            try:
                result = send_message(pending, st.session_state.session_id)
                answer = result["answer"]
                sources = result.get("sources", [])

                st.markdown(answer)
                render_sources(sources)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
            except Exception as e:
                error_msg = (
                    f"Xin lỗi, đã có lỗi xảy ra: {e}\n\n"
                    "Hãy kiểm tra backend đang chạy không."
                )
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })