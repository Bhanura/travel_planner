import json
import re
from collections.abc import Iterator


def encode_stream_event(event: dict) -> str:
    """Encode one event as a single NDJSON record."""
    return json.dumps(
        event,
        ensure_ascii=False,
    ) + "\n"


def iter_text_chunks(
    text: str,
    max_chars: int = 48,
) -> Iterator[str]:
    """
    Split text into readable chunks while preserving
    the original text exactly when chunks are joined.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    pieces = re.findall(r"\S+\s*|\s+", text)
    buffer = ""

    for piece in pieces:
        if buffer and len(buffer) + len(piece) > max_chars:
            yield buffer
            buffer = piece
        else:
            buffer += piece

    if buffer:
        yield buffer