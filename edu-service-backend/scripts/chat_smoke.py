import json
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atguigu_edu.conf.config import settings


def _print(title: str, payload) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    base = f"http://{settings.app_host}:{settings.app_port}"
    if len(sys.argv) >= 2 and str(sys.argv[1]).strip():
        base = str(sys.argv[1]).strip().rstrip("/")

    with httpx.Client(timeout=10.0) as client:
        chat = client.post(
            f"{base}/api/chat",
            json={"sender_id": "student_001", "text": "你好"},
        )
        _print("chat_status", {"status_code": chat.status_code, "text": chat.text})
        if chat.headers.get("content-type", "").startswith("application/json"):
            _print("chat_json", chat.json())
        if chat.status_code >= 400:
            return

        hist = client.get(f"{base}/api/chat/history", params={"sender_id": "student_001"})
        _print("history_status", {"status_code": hist.status_code, "text": hist.text})
        if hist.headers.get("content-type", "").startswith("application/json"):
            _print("history_json", hist.json())
        if hist.status_code >= 400:
            return

    print("\nchat_ok")


if __name__ == "__main__":
    main()

