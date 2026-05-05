import streamlit as st


_LOAI_THAY_DOI_LABEL = {
    "sua_doi":  "đã được sửa đổi",
    "bai_bo":   "đã bị bãi bỏ",
    "thay_the": "đã bị thay thế toàn bộ",
}


def _render_source(idx: int, src: dict) -> None:
    """Render 1 nguồn trích dẫn theo schema mới."""
    col1, col2 = st.columns([3, 1])

    with col1:
        # Cảnh báo hiệu lực
        if not src.get("con_hieu_luc", True):
            ngay_het = src.get("ngay_het_hieu_luc")
            msg = "⚠️ Điều này đã hết hiệu lực"
            if ngay_het:
                msg += f" từ {ngay_het}"
            st.warning(msg)

        # Cảnh báo bị sửa đổi
        loai = src.get("loai_thay_doi")
        if loai:
            label = _LOAI_THAY_DOI_LABEL.get(loai, f"có thay đổi ({loai})")
            bi_sua = src.get("bi_sua_doi_boi")
            msg = f"⚠️ Điều này {label}"
            if bi_sua:
                msg += f" bởi `{bi_sua}`"
            st.warning(msg)

        st.markdown(f"**{idx}. {src.get('citation', 'Không rõ nguồn')}**")
        if dieu_ten := src.get("dieu_ten"):
            st.caption(f"_{dieu_ten}_")
        st.caption(src.get("content_preview", ""))

    with col2:
        if src.get("dieu_so") is not None:
            st.metric("Điều", src["dieu_so"])
        elif src.get("phu_luc_so") is not None:
            st.metric("Phụ lục", src["phu_luc_so"])


def render_sources(sources: list[dict]) -> None:
    """Hiển thị danh sách nguồn trong expander."""
    if not sources:
        return
    with st.expander(f"📚 Nguồn tham khảo ({len(sources)})", expanded=False):
        for i, src in enumerate(sources, 1):
            _render_source(i, src)
            if i < len(sources):
                st.divider()


def render_message(role: str, content: str, sources: list | None = None):
    """Render 1 tin nhắn trong chat."""
    with st.chat_message(role):
        st.markdown(content)
        if sources:
            render_sources(sources)


def render_chat_history(messages: list):
    """Render toàn bộ lịch sử hội thoại."""
    for msg in messages:
        render_message(
            role=msg["role"],
            content=msg["content"],
            sources=msg.get("sources"),
        )