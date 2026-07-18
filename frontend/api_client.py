import json
from typing import Any, Iterator
from urllib.request import Request, urlopen

from .config import CHAT_URL, STREAM_URL


class FrontendAPIError(RuntimeError):
    """Raised when the frontend cannot communicate with the backend."""


def call_chat_api(message: str, session_id: str) -> dict[str, Any]:
    payload = json.dumps(
        {
            "message": message,
            "session_id": session_id,
        }
    ).encode("utf-8")

    request = Request(
        CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise FrontendAPIError("Normal chat API request failed.") from exc


def stream_chat_api(
    message: str,
    session_id: str,
) -> Iterator[dict[str, Any]]:
    payload = json.dumps(
        {
            "message": message,
            "session_id": session_id,
        }
    ).encode("utf-8")

    request = Request(
        STREAM_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(request, timeout=60) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()

                if not line:
                    continue

                yield json.loads(line)
    except Exception as exc:
        raise FrontendAPIError("Streaming chat API request failed.") from exc