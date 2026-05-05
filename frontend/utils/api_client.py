import requests
import json
import os
from typing import Generator

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def send_message(question: str, session_id: str) -> dict:
    """Gửi câu hỏi và nhận toàn bộ response."""
    response = requests.post(
        f"{BACKEND_URL}/api/chat",
        json={"question": question, "session_id": session_id},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def stream_message(question: str, session_id: str) -> Generator[str, None, None]:
    """Generator stream từng token từ backend."""
    with requests.post(
        f"{BACKEND_URL}/api/chat/stream",
        json={"question": question, "session_id": session_id},
        stream=True,
        timeout=60,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data_str = line[6:]  # bỏ "data: "
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                if "token" in data:
                    yield data["token"]
                elif "error" in data:
                    yield f"\n\n[Lỗi: {data['error']}]"
            except json.JSONDecodeError:
                continue


def clear_history(session_id: str) -> None:
    """Xóa lịch sử hội thoại."""
    try:
        requests.delete(f"{BACKEND_URL}/api/chat/{session_id}", timeout=10)
    except Exception:
        pass


def check_health() -> dict:
    """Kiểm tra trạng thái backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "detail": str(e)}
