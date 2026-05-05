import streamlit as st
from utils.api_client import clear_history, check_health


SUGGESTED_QUESTIONS = [
    "Vượt đèn đỏ bị phạt bao nhiêu tiền?",
    "Nồng độ cồn tối đa được phép khi lái xe ô tô?",
    "Tốc độ tối đa trong khu dân cư là bao nhiêu?",
    "Không đội mũ bảo hiểm phạt bao nhiêu?",
    "Xe máy đi vào làn ô tô bị phạt không?",
    "Sử dụng điện thoại khi lái xe bị phạt gì?",
    "Giấy phép lái xe hạng B2 được phép lái xe gì?",
]


def render_sidebar(session_id: str) -> str | None:
    """
    Render sidebar và trả về câu hỏi gợi ý nếu được chọn.
    """
    selected_question = None

    with st.sidebar:
        st.title("🚦 Luật GTĐB")
        st.caption("Chatbot hỏi đáp Luật Giao thông Đường bộ Việt Nam")

        # Status indicator
        st.divider()
        health = check_health()
        if health.get("status") == "ok":
            st.success("Hệ thống hoạt động bình thường", icon="✅")
        else:
            st.error("Hệ thống đang có sự cố", icon="❌")

        # Câu hỏi gợi ý
        st.divider()
        st.subheader("Câu hỏi thường gặp")
        for q in SUGGESTED_QUESTIONS:
            if st.button(q, use_container_width=True, key=f"btn_{q[:20]}"):
                selected_question = q

        # Xóa lịch sử
        st.divider()
        if st.button("🗑️ Xóa lịch sử hội thoại", use_container_width=True, type="secondary"):
            st.session_state.confirm_delete = True

        if st.session_state.get("confirm_delete"):
            if st.button("✅ Xác nhận xóa", type="primary"):
                clear_history(session_id)
                st.session_state.messages = []
                st.session_state.confirm_delete = False
                st.rerun()

        # Thông tin
        st.divider()
        st.caption("**Nguồn tài liệu:**")
        st.caption("• Luật Đường bộ 35/2024/QH15")
        st.caption("• Luật Trật tự, ATGT Đường bộ 36/2024/QH15")
        st.caption("• Luật sửa đổi 118/2025/QH15")
        st.caption("• Nghị định 168/2024/NĐ-CP (xử phạt VPHC)")
        st.caption("• & các Nghị định hướng dẫn 2024–2026")

    return selected_question
